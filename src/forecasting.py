"""Four-week recursive forecasts with rolling validation and a held-out month."""

import json

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .common import REPORTS, TABLEAU, config, read, save
from .generate_data import calendar

MODELS = ("Seasonal naive", "Calendar ridge", "Gradient boosting")


def features(frame, stores, cal):
    """Features known at the forecast origin or generated recursively."""
    frame = frame.merge(
        stores[["restaurant_id", "state"]], on="restaurant_id", validate="many_to_one"
    )
    frame = frame.merge(
        cal[["business_date", "state", "is_public_holiday"]],
        on=["business_date", "state"],
        validate="many_to_one",
    )
    dates = pd.to_datetime(frame.business_date)
    out = pd.DataFrame(index=frame.index)
    for sid in stores.restaurant_id:
        out[f"store_{sid}"] = frame.restaurant_id.eq(sid).astype(float)
    for weekday in range(7):
        out[f"weekday_{weekday}"] = dates.dt.dayofweek.eq(weekday).astype(float)
    # Store/weekday interactions retain location-specific weekly demand patterns.
    for sid in stores.restaurant_id:
        out[f"weekend_store_{sid}"] = frame.restaurant_id.eq(sid).astype(
            float
        ) * dates.dt.dayofweek.ge(5)
    out["annual_sin"] = np.sin(2 * np.pi * dates.dt.dayofyear / 365.25)
    out["annual_cos"] = np.cos(2 * np.pi * dates.dt.dayofyear / 365.25)
    out["trend_years"] = (dates - pd.Timestamp(config()["start_date"])).dt.days / 365.25
    out["holiday"] = frame.is_public_holiday
    out[["lag7", "lag28", "mean28"]] = frame[["lag7", "lag28", "mean28"]].to_numpy()
    return out


def training_rows(history):
    """Lagged values use observations strictly before each target date."""
    frame = history.sort_values(["restaurant_id", "business_date"]).copy()
    group = frame.groupby("restaurant_id").revenue
    frame["lag7"] = group.shift(7)
    frame["lag28"] = group.shift(28)
    frame["mean28"] = group.transform(lambda values: values.shift(1).rolling(28).mean())
    return frame.dropna(subset=["lag7", "lag28", "mean28"])


def predict_from_origin(history, cutoff, model_name, stores, cal, horizon=28):
    """Fit only through cutoff, then recursively predict every future day.

    Slicing inside this function protects callers from accidentally passing
    post-origin actual sales. Real future promotion plans are not assumed.
    """
    history = history[pd.to_datetime(history.business_date).le(cutoff)].copy()
    fitted = None
    if model_name != "Seasonal naive":
        train = training_rows(history)
        x = features(train, stores, cal)
        if model_name == "Calendar ridge":
            fitted = make_pipeline(StandardScaler(), Ridge(alpha=60))
        else:
            fitted = HistGradientBoostingRegressor(
                max_iter=120,
                max_leaf_nodes=15,
                learning_rate=0.06,
                l2_regularization=8,
                random_state=42,
            )
        fitted.fit(x, train.revenue.to_numpy())
    series = {
        sid: history[history.restaurant_id.eq(sid)]
        .sort_values("business_date")
        .revenue.tolist()
        for sid in stores.restaurant_id
    }
    forecasts = []
    for step in range(1, horizon + 1):
        date = (pd.Timestamp(cutoff) + pd.Timedelta(days=step)).strftime("%Y-%m-%d")
        next_rows = pd.DataFrame(
            [
                {
                    "restaurant_id": sid,
                    "business_date": date,
                    "lag7": values[-7],
                    "lag28": values[-28],
                    "mean28": np.mean(values[-28:]),
                }
                for sid, values in series.items()
            ]
        )
        prediction = (
            next_rows.lag7.to_numpy()
            if fitted is None
            else fitted.predict(features(next_rows, stores, cal))
        )
        prediction = np.maximum(prediction, 0)
        for row, value in zip(next_rows.itertuples(), prediction):
            series[row.restaurant_id].append(float(value))
            forecasts.append(
                {
                    "restaurant_id": row.restaurant_id,
                    "business_date": date,
                    "horizon_day": step,
                    "forecast_revenue": float(value),
                    "model": model_name,
                    "origin_date": pd.Timestamp(cutoff).strftime("%Y-%m-%d"),
                }
            )
    return pd.DataFrame(forecasts)


def metrics(actual, predicted):
    """Evaluate dollars and relative errors; exclude zero actuals from MAPE."""
    actual, predicted = np.asarray(actual), np.asarray(predicted)
    errors = actual - predicted
    positive = actual > 0
    return {
        "mae": float(np.abs(errors).mean()),
        "rmse": float(np.sqrt((errors**2).mean())),
        "mape": float((np.abs(errors[positive]) / actual[positive]).mean() * 100),
        "wape": float(np.abs(errors).sum() / actual.sum() * 100),
    }


def run():
    """Compare models on three rolling folds, test once, then refit all data."""
    cfg = config()
    horizon = cfg["forecast_horizon"]
    history = read("store_day")[["restaurant_id", "business_date", "revenue"]]
    stores = read("restaurants")
    dates = sorted(history.business_date.unique())
    calendar_end = pd.Timestamp(dates[-1]) + pd.Timedelta(days=horizon)
    cal = calendar(pd.date_range(dates[0], calendar_end))
    cal["business_date"] = cal.business_date.dt.strftime("%Y-%m-%d")
    origins = [pd.Timestamp(dates[-horizon * factor - 1]) for factor in (4, 3, 2)]
    scores, traces = [], []
    for fold, origin in enumerate(origins, 1):
        for name in MODELS:
            predictions = predict_from_origin(
                history, origin, name, stores, cal, horizon
            )
            joined = predictions.merge(
                history.rename(columns={"revenue": "actual_revenue"}),
                on=["restaurant_id", "business_date"],
                validate="one_to_one",
            )
            joined["evaluation_period"] = "Validation"
            joined["fold"] = fold
            traces.append(joined)
            scores.append(
                {
                    "evaluation_period": "Validation",
                    "fold": fold,
                    "model": name,
                    **metrics(joined.actual_revenue, joined.forecast_revenue),
                }
            )
        print(f"Forecast validation fold {fold}/3 completed.", flush=True)
    score_frame = pd.DataFrame(scores)
    winner = score_frame.groupby("model").mae.mean().idxmin()
    validation = pd.concat(traces, ignore_index=True)
    selected_errors = validation[validation.model.eq(winner)].copy()
    selected_errors["absolute_error"] = (
        selected_errors.actual_revenue - selected_errors.forecast_revenue
    ).abs()
    # 84 validation errors per store: a practical store-specific calibration set.
    error_bands = selected_errors.groupby("restaurant_id").absolute_error.quantile(0.8)
    holdout_origin = pd.Timestamp(dates[-horizon - 1])
    for name in MODELS:
        predictions = predict_from_origin(
            history, holdout_origin, name, stores, cal, horizon
        )
        joined = predictions.merge(
            history.rename(columns={"revenue": "actual_revenue"}),
            on=["restaurant_id", "business_date"],
            validate="one_to_one",
        )
        joined["evaluation_period"] = "Holdout"
        joined["fold"] = 0
        band = joined.restaurant_id.map(error_bands)
        joined["lower_80"] = (
            (joined.forecast_revenue - band).clip(lower=0) if name == winner else np.nan
        )
        joined["upper_80"] = (
            joined.forecast_revenue + band if name == winner else np.nan
        )
        traces.append(joined)
        coverage = (
            joined.actual_revenue.between(joined.lower_80, joined.upper_80).mean()
            if name == winner
            else np.nan
        )
        scores.append(
            {
                "evaluation_period": "Holdout",
                "fold": 0,
                "model": name,
                **metrics(joined.actual_revenue, joined.forecast_revenue),
                "interval_coverage": coverage,
            }
        )
    final = predict_from_origin(
        history, pd.Timestamp(dates[-1]), winner, stores, cal, horizon
    )
    band = final.restaurant_id.map(error_bands)
    final["lower_80"] = (final.forecast_revenue - band).clip(lower=0)
    final["upper_80"] = final.forecast_revenue + band
    final = final.merge(
        stores[["restaurant_id", "restaurant_name", "state", "area"]],
        on="restaurant_id",
    )
    final["forecast_type"] = "Statistical revenue forecast (synthetic data)"
    save(final, TABLEAU / "forecast_daily.csv")
    save(pd.concat(traces, ignore_index=True), TABLEAU / "forecast_backtests.csv")
    store_scores = []
    for (period, name, sid), group in pd.concat(traces).groupby(
        ["evaluation_period", "model", "restaurant_id"]
    ):
        coverage = (
            group.actual_revenue.between(group.lower_80, group.upper_80).mean()
            if name == winner and period == "Holdout"
            else np.nan
        )
        store_scores.append(
            {
                "evaluation_period": period,
                "model": name,
                "restaurant_id": sid,
                **metrics(group.actual_revenue, group.forecast_revenue),
                "interval_coverage": coverage,
                "observations": len(group),
            }
        )
    save(pd.DataFrame(store_scores), TABLEAU / "forecast_store_metrics.csv")
    scores = pd.DataFrame(scores)
    save(scores, REPORTS / "exports/forecast_metrics.csv")
    save(scores, TABLEAU / "forecast_metrics.csv")
    summary = {
        "selected_model": winner,
        "selection_metric": "Mean validation MAE across three rolling 28-day folds",
        "holdout_start": (holdout_origin + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
        "holdout_end": dates[-1],
        "future_start": final.business_date.min(),
        "future_end": final.business_date.max(),
        "forecast_total": round(final.forecast_revenue.sum(), 2),
        "interval_method": "Per-store 80th percentile absolute validation error (84 errors/store); approximate empirical bands",
    }
    (REPORTS / "forecast_summary.json").write_text(json.dumps(summary, indent=2))
    print(
        f"Forecast winner: {winner}; holdout evaluated and next {horizon} days exported.",
        flush=True,
    )
    return scores


if __name__ == "__main__":
    run()
