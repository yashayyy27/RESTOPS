-- RESTOPS source tables; each fact has a documented grain.
-- Dates are ISO text for SQLite. Monetary values are AUD excluding GST.
CREATE TABLE restaurants (
    restaurant_id INTEGER PRIMARY KEY, restaurant_name TEXT NOT NULL,
    state TEXT NOT NULL, location_type TEXT, area TEXT, timezone TEXT,
    seats INTEGER, opening_date TEXT, open_hour INTEGER, close_hour INTEGER
);
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY, product_name TEXT NOT NULL, category TEXT,
    menu_price_ex_gst REAL, standard_ingredient_cost REAL
);
CREATE TABLE calendar (
    business_date TEXT NOT NULL, state TEXT NOT NULL, holiday_name TEXT,
    is_public_holiday INTEGER, weekday INTEGER, is_weekend INTEGER,
    month INTEGER, season TEXT, school_holiday_proxy INTEGER,
    PRIMARY KEY (business_date, state)
);
CREATE TABLE manager_assignments (
    restaurant_id INTEGER REFERENCES restaurants, manager_id TEXT,
    start_date TEXT, end_date TEXT, PRIMARY KEY (restaurant_id, start_date)
);
CREATE TABLE promotions (
    promotion_id TEXT PRIMARY KEY, restaurant_id INTEGER REFERENCES restaurants,
    campaign_name TEXT, start_date TEXT, end_date TEXT, discount_rate REAL,
    eligible_category TEXT, campaign_cost REAL
);
CREATE TABLE targets (
    restaurant_id INTEGER REFERENCES restaurants, month TEXT,
    revenue_target REAL, operating_margin_target REAL, labour_pct_target REAL,
    waste_pct_target REAL, satisfaction_target REAL,
    PRIMARY KEY (restaurant_id, month)
);
CREATE TABLE operating_costs (
    cost_id INTEGER PRIMARY KEY, restaurant_id INTEGER REFERENCES restaurants,
    month TEXT, cost_category TEXT, amount REAL
);
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY, restaurant_id INTEGER REFERENCES restaurants,
    business_date TEXT, timestamp_local TEXT, hour INTEGER, daypart TEXT,
    channel TEXT, customer_id INTEGER, promotion_id TEXT REFERENCES promotions,
    revenue REAL, ingredient_cost REAL, discount_amount REAL, units INTEGER
);
CREATE TABLE transactions (
    transaction_line_id INTEGER PRIMARY KEY, order_id INTEGER REFERENCES orders,
    restaurant_id INTEGER REFERENCES restaurants, restaurant_name TEXT,
    timestamp_local TEXT, product_id INTEGER REFERENCES products, quantity INTEGER,
    channel TEXT, customer_id INTEGER, promotion_id TEXT REFERENCES promotions,
    list_revenue REAL, discount_amount REAL, net_revenue REAL, gst_amount REAL,
    ingredient_cost REAL, business_date TEXT, month TEXT, hour INTEGER, daypart TEXT
);
CREATE TABLE labour (
    shift_id INTEGER PRIMARY KEY, restaurant_id INTEGER REFERENCES restaurants,
    employee_id TEXT, role TEXT, business_date TEXT, daypart TEXT,
    scheduled_start TEXT, scheduled_end TEXT, actual_start TEXT, actual_end TEXT,
    break_hours REAL, paid_hours REAL CHECK (paid_hours BETWEEN 0 AND 16),
    hourly_cost REAL, rate_imputed INTEGER, labour_cost REAL
);
CREATE TABLE customer_feedback (
    feedback_id INTEGER PRIMARY KEY, order_id INTEGER REFERENCES orders,
    restaurant_id INTEGER REFERENCES restaurants, business_date TEXT,
    overall_score REAL CHECK (overall_score BETWEEN 1 AND 5 OR overall_score IS NULL),
    food_score REAL, service_score REAL
);
CREATE TABLE loyalty (
    loyalty_event_id INTEGER PRIMARY KEY, customer_id INTEGER,
    restaurant_id INTEGER REFERENCES restaurants, order_id INTEGER REFERENCES orders,
    event_date TEXT, event_type TEXT, points INTEGER
);
CREATE TABLE waste (
    waste_id INTEGER PRIMARY KEY, restaurant_id INTEGER REFERENCES restaurants,
    product_id INTEGER REFERENCES products, business_date TEXT,
    waste_units INTEGER CHECK (waste_units >= 0), waste_cost REAL, reason TEXT
);
CREATE TABLE delivery (
    order_id INTEGER PRIMARY KEY REFERENCES orders,
    restaurant_id INTEGER REFERENCES restaurants, promised_minutes REAL,
    actual_minutes REAL, commission_cost REAL, delivery_fee REAL, status TEXT
);
-- Materialised monthly mart: consistent Python KPIs for SQL consumers.
CREATE TABLE store_month_kpis (
    restaurant_id INTEGER REFERENCES restaurants, month TEXT,
    revenue REAL, ingredient_cost REAL, transactions INTEGER, discounts REAL,
    identified_orders INTEGER, labour_cost REAL, paid_hours REAL, service_hours REAL,
    waste_cost REAL, score_sum REAL, survey_responses INTEGER, commission_cost REAL,
    deliveries INTEGER, late_deliveries INTEGER, overhead_cost REAL, campaign_cost REAL,
    operating_profit REAL, gross_contribution REAL, average_transaction_value REAL,
    gross_margin_pct REAL, operating_margin_pct REAL, labour_cost_pct REAL,
    sales_per_labour_hour REAL, transactions_per_labour_hour REAL, waste_pct REAL,
    satisfaction_score REAL, identified_order_share REAL, late_delivery_pct REAL,
    revenue_target REAL, operating_margin_target REAL, labour_pct_target REAL,
    waste_pct_target REAL, satisfaction_target REAL, restaurant_name TEXT,
    state TEXT, location_type TEXT, area TEXT, timezone TEXT, seats INTEGER,
    opening_date TEXT, open_hour INTEGER, close_hour INTEGER,
    revenue_growth_mom REAL, revenue_growth_yoy REAL, target_achievement_pct REAL,
    score_revenue REAL, score_margin REAL, score_labour REAL, score_waste REAL,
    score_satisfaction REAL, index_complete INTEGER, performance_index REAL,
    PRIMARY KEY (restaurant_id, month)
);
