-- Monthly financial KPIs built from source facts. Aggregate separately first.
WITH sales AS (
    SELECT restaurant_id, month, SUM(net_revenue) AS revenue,
           SUM(ingredient_cost) AS ingredient_cost,
           COUNT(DISTINCT order_id) AS transactions
    FROM transactions GROUP BY restaurant_id, month
), roster AS (
    SELECT restaurant_id, SUBSTR(business_date, 1, 7) AS month,
           SUM(labour_cost) AS labour_cost, SUM(paid_hours) AS paid_hours
    FROM labour GROUP BY restaurant_id, SUBSTR(business_date, 1, 7)
), waste_totals AS (
    SELECT restaurant_id, SUBSTR(business_date, 1, 7) AS month,
           SUM(waste_cost) AS waste_cost
    FROM waste GROUP BY restaurant_id, SUBSTR(business_date, 1, 7)
), feedback AS (
    SELECT restaurant_id, SUBSTR(business_date, 1, 7) AS month,
           AVG(overall_score) AS satisfaction_score, COUNT(overall_score) AS responses
    FROM customer_feedback GROUP BY restaurant_id, SUBSTR(business_date, 1, 7)
)
SELECT s.restaurant_id, s.month, s.revenue, s.transactions,
       1.0 * s.revenue / NULLIF(s.transactions, 0) AS average_transaction_value,
       (s.revenue - s.ingredient_cost) / NULLIF(s.revenue, 0) AS gross_margin_pct,
       l.labour_cost / NULLIF(s.revenue, 0) AS labour_cost_pct,
       s.revenue / NULLIF(l.paid_hours, 0) AS sales_per_labour_hour,
       w.waste_cost / NULLIF(s.ingredient_cost + w.waste_cost, 0) AS waste_pct,
       f.satisfaction_score, f.responses,
       s.revenue / NULLIF(t.revenue_target, 0) AS target_achievement_pct
FROM sales s
LEFT JOIN roster l ON s.restaurant_id = l.restaurant_id AND s.month = l.month
LEFT JOIN waste_totals w ON s.restaurant_id = w.restaurant_id AND s.month = w.month
LEFT JOIN feedback f ON s.restaurant_id = f.restaurant_id AND s.month = f.month
LEFT JOIN targets t ON s.restaurant_id = t.restaurant_id AND s.month = t.month
ORDER BY s.restaurant_id, s.month;
