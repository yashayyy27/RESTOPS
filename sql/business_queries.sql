-- 1. Which restaurants need support? Latest quarter; weighted rates.
SELECT restaurant_id, restaurant_name, SUM(revenue) AS revenue,
       SUM(operating_profit) / NULLIF(SUM(revenue), 0) AS operating_margin_pct,
       SUM(labour_cost) / NULLIF(SUM(revenue), 0) AS labour_pct,
       SUM(waste_cost) / NULLIF(SUM(ingredient_cost + waste_cost), 0) AS waste_pct,
       SUM(score_sum) / NULLIF(SUM(survey_responses), 0) AS satisfaction,
       AVG(performance_index) AS mean_monthly_index
FROM store_month_kpis WHERE month >= '2025-10'
GROUP BY restaurant_id, restaurant_name ORDER BY operating_margin_pct;

-- 2. Which products contribute most? Product order counts are not additive.
SELECT p.category, p.product_name, SUM(t.quantity) AS units,
       SUM(t.net_revenue) AS revenue,
       SUM(t.net_revenue - t.ingredient_cost) AS gross_contribution
FROM transactions t JOIN products p ON t.product_id = p.product_id
GROUP BY p.category, p.product_name ORDER BY gross_contribution DESC;

-- 3. Which dayparts have low labour productivity? No many-to-many fact join.
WITH demand AS (
    SELECT restaurant_id, business_date, daypart, COUNT(*) AS orders, SUM(revenue) AS revenue
    FROM orders GROUP BY restaurant_id, business_date, daypart
), capacity AS (
    SELECT restaurant_id, business_date, daypart, SUM(paid_hours) AS hours
    FROM labour GROUP BY restaurant_id, business_date, daypart
)
SELECT d.restaurant_id, d.daypart, SUM(d.orders) AS orders,
       SUM(d.revenue) / NULLIF(SUM(c.hours), 0) AS sales_per_hour
FROM demand d JOIN capacity c ON d.restaurant_id = c.restaurant_id
    AND d.business_date = c.business_date AND d.daypart = c.daypart
GROUP BY d.restaurant_id, d.daypart ORDER BY sales_per_hour;

-- 4. Delivery service failures by restaurant.
SELECT restaurant_id, COUNT(*) AS deliveries,
       AVG(CASE WHEN actual_minutes > promised_minutes THEN 1.0 ELSE 0.0 END) AS late_share,
       SUM(commission_cost) AS commission_cost
FROM delivery GROUP BY restaurant_id ORDER BY late_share DESC;

-- 5. Fully observed 90-day repeat cohorts. SQLite uses julianday; in PostgreSQL
-- replace date differences with INTERVAL/date arithmetic.
WITH first_visits AS (
    SELECT customer_id, MIN(business_date) AS first_visit FROM orders
    WHERE customer_id IS NOT NULL GROUP BY customer_id
), eligible AS (
    SELECT * FROM first_visits WHERE julianday(first_visit) <=
        (SELECT julianday(MAX(business_date)) - 90 FROM orders)
), returns AS (
    SELECT DISTINCT o.customer_id FROM orders o JOIN eligible e ON o.customer_id = e.customer_id
    WHERE julianday(o.business_date) - julianday(e.first_visit) BETWEEN 1 AND 90
)
SELECT COUNT(*) AS eligible_customers,
       SUM(CASE WHEN r.customer_id IS NOT NULL THEN 1 ELSE 0 END) AS repeat_customers,
       AVG(CASE WHEN r.customer_id IS NOT NULL THEN 1.0 ELSE 0.0 END) AS repeat_rate
FROM eligible e LEFT JOIN returns r ON e.customer_id = r.customer_id;

-- 6. Revenue growth and targets without mixing store populations.
WITH monthly AS (
    SELECT restaurant_id, month, revenue, revenue_target,
           LAG(revenue, 12) OVER (PARTITION BY restaurant_id ORDER BY month) AS prior_year
    FROM store_month_kpis
)
SELECT *, revenue / NULLIF(revenue_target, 0) AS target_achievement,
       (revenue - prior_year) / NULLIF(prior_year, 0) AS revenue_growth_yoy
FROM monthly ORDER BY restaurant_id, month;
