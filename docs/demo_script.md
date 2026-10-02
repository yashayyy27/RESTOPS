# Five-minute interview demonstration

Use `python -m streamlit run streamlit_app.py`, Dataset **Demo**, all restaurants,
reporting month **2025-12**. The app demonstrates a fictional Australian chain.
Choose Wollongong for investigation, planning, forecasting and scenarios.

## 0:00–0:40 · Business framing

“My restaurant management experience helped me frame the operational decisions.
RESTOPS connects sales, labour, waste and customer experience to contribution.
The data is entirely synthetic. I used my Business Analytics and Data Science
background to translate those questions into requirements, data contracts and
tested analysis. I am demonstrating proposed decisions, not real business savings.”

Show Executive overview. Explain the difference between revenue and profit,
the selected month and the latest seven-day attention queue. Open one brief entry
to show evidence, a proposed owner and a success measure.

## 0:40–1:40 · Investigate recorded performance

Open Restaurant investigation and select Wollongong. Show the revenue target
gap and December/November profit bridge. Explain that order volume and net basket
value reconcile the revenue movement and six cost changes reconcile profit.
Inspect product/category contribution and waste reasons. State that these are
observed financial drivers, while an operational explanation needs a pilot.

## 1:40–2:35 · Assess an action commercially

Open Profit scenario simulator. Show the zero-change baseline. Set staffing
hours to −5%, order demand to −2% and waste share to 4%. Show net sales, COGS,
labour, contribution, profit and break-even. Explain that demand is an explicit
assumption; fewer labour hours do not automatically guarantee unchanged service.
Show the ±10% demand range and download the assumptions/results.

## 2:35–3:25 · Connect forecasts to staffing

Open Forecasting. Compare the selected model with seasonal naive, including the
store's MAE/RMSE/WAPE and measured band coverage. Explain rolling validation and
the final holdout. Open Labour & demand planning. Raise productivity from 6 to 8
orders per service hour and show the coverage/budget response. State that the
scheduled line is a historical template and suggestions do not construct a
compliant employee roster.

## 3:25–4:10 · Challenge promotional performance

Open Promotion evaluation. Select a campaign and compare estimated sales,
incremental contribution, spend and ROI. Point out discounts already reduce net
sales. Explain control-store contamination, confounding and limited bootstrap
uncertainty. Show that generator truth is isolated and used to assess expected
order-uplift error after estimation, not supplied as a model feature.

## 4:10–5:00 · Demonstrate BA delivery and trust

Open Data quality. Show contract checks, optional missing values and whole-order
quarantine. Explain source IDs and independent SQL reconciliation. Open the
requirements traceability matrix and validation results. Finish with the BA
question: “What result would make us retain or stop this pilot?” Suggest labour
cost and contribution as commercial measures, with satisfaction and stock-outs
as guardrails.

## Design choices to defend

- **Separate grains:** a three-item basket is one transaction; raw fact joins
  multiply costs. Independently aggregate facts before combining them.
- **Transparent scenarios:** named drivers, constant-cost assumptions and a
  ledger identity are easier to challenge than an unexplained optimisation model.
- **Temporal validation:** random splits leak future structure into planning;
  forecasts recursively use predictions for future lags.
- **Appropriate ML:** ridge and boosting challenge a weekly baseline. Selection
  is based on validation error, not complexity or the most flattering holdout.
- **Observed relationships:** staffing, survey and loyalty comparisons do not
  prove causation. A proposed controlled pilot connects evidence to action.
- **Business acceptance:** stories, criteria and developer validation are
  provided. Stakeholder interviews, approvals and real-user UAT are not invented.
- **Honest scope:** the Streamlit app is working; Tableau data/specification are
  delivered, but no native Tableau workbook or published dashboard is claimed.
