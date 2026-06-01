CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS job_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_name varchar NOT NULL,
    business_date date,
    status varchar NOT NULL DEFAULT 'running',
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    error_message text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS stores (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    store_code varchar NOT NULL UNIQUE,
    store_name varchar NOT NULL,
    store_status varchar,
    store_type varchar,
    delivery_cycle_days numeric NOT NULL DEFAULT 1,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS products (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    product_code varchar NOT NULL UNIQUE,
    product_name varchar NOT NULL,
    barcode varchar,
    cat_id_01 varchar NOT NULL,
    cat_name_01 varchar NOT NULL,
    cat_id_02 varchar,
    cat_name_02 varchar,
    sale_unit varchar NOT NULL,
    fresh_attribute varchar,
    storage_condition varchar,
    shelf_life_days numeric,
    sellable_days numeric,
    sellable_days_source varchar,
    sellable_days_reference text,
    sellable_days_review_status varchar NOT NULL DEFAULT 'pending',
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS store_products (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id uuid NOT NULL REFERENCES stores(id),
    product_id uuid NOT NULL REFERENCES products(id),
    store_order_status varchar,
    store_sale_status varchar,
    is_orderable boolean NOT NULL DEFAULT true,
    is_sellable boolean NOT NULL DEFAULT true,
    package_size numeric,
    order_batch_qty numeric,
    min_order_qty numeric,
    safety_stock_days numeric NOT NULL DEFAULT 1,
    sellable_days_override numeric,
    recent_daily_sales numeric,
    store_stock_qty_yesterday numeric,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (store_id, product_id)
);

CREATE TABLE IF NOT EXISTS sales_daily (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id uuid NOT NULL REFERENCES stores(id),
    product_id uuid NOT NULL REFERENCES products(id),
    business_date date NOT NULL,
    sales_quantity numeric NOT NULL DEFAULT 0,
    sales_amount numeric NOT NULL DEFAULT 0,
    unit varchar NOT NULL,
    source_file varchar,
    imported_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (store_id, product_id, business_date)
);

CREATE TABLE IF NOT EXISTS sales_cutoff_snapshots (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id uuid NOT NULL REFERENCES stores(id),
    product_id uuid NOT NULL REFERENCES products(id),
    business_date date NOT NULL,
    cutoff_time time NOT NULL,
    cutoff_sales_quantity numeric NOT NULL DEFAULT 0,
    current_inventory_qty numeric,
    in_transit_qty numeric,
    unit varchar NOT NULL,
    source_file varchar,
    imported_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (store_id, product_id, business_date, cutoff_time)
);

CREATE TABLE IF NOT EXISTS inventory_snapshots (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id uuid NOT NULL REFERENCES stores(id),
    product_id uuid NOT NULL REFERENCES products(id),
    snapshot_time timestamptz NOT NULL,
    business_date date NOT NULL,
    inventory_quantity numeric NOT NULL,
    inventory_source varchar NOT NULL,
    unit varchar NOT NULL,
    source_file varchar,
    imported_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (store_id, product_id, snapshot_time, inventory_source)
);

CREATE INDEX IF NOT EXISTS idx_inventory_snapshots_product_time
    ON inventory_snapshots(store_id, product_id, snapshot_time);

CREATE TABLE IF NOT EXISTS inventory_loss_daily (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id uuid NOT NULL REFERENCES stores(id),
    product_id uuid NOT NULL REFERENCES products(id),
    business_date date NOT NULL,
    closing_stock_qty numeric,
    loss_quantity numeric,
    loss_amount numeric,
    inventory_difference_qty numeric,
    unit varchar NOT NULL,
    source_file varchar,
    imported_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (store_id, product_id, business_date)
);

CREATE TABLE IF NOT EXISTS purchase_receipts_daily (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id uuid NOT NULL REFERENCES stores(id),
    product_id uuid NOT NULL REFERENCES products(id),
    business_date date NOT NULL,
    order_quantity numeric,
    receive_quantity numeric,
    total_receive_quantity numeric,
    total_return_quantity numeric,
    unit varchar NOT NULL,
    source_file varchar,
    imported_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (store_id, product_id, business_date)
);

CREATE TABLE IF NOT EXISTS fresh_order_imports (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_file_name varchar NOT NULL,
    source_sheet_name varchar NOT NULL,
    source_format varchar NOT NULL,
    supplier_code varchar,
    supplier_name varchar,
    store_id uuid REFERENCES stores(id),
    store_name_raw varchar NOT NULL,
    product_id uuid REFERENCES products(id),
    product_name_raw varchar NOT NULL,
    order_date date,
    arrival_date date NOT NULL,
    ordered_quantity numeric,
    arrival_quantity numeric NOT NULL,
    gross_quantity numeric,
    tare_quantity numeric,
    received_quantity numeric,
    unit varchar NOT NULL,
    match_status varchar NOT NULL DEFAULT 'pending',
    remark text,
    raw_row_number integer NOT NULL,
    imported_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source_file_name, source_sheet_name, raw_row_number)
);

CREATE INDEX IF NOT EXISTS idx_fresh_order_imports_arrival
    ON fresh_order_imports(arrival_date);

CREATE INDEX IF NOT EXISTS idx_fresh_order_imports_product_arrival
    ON fresh_order_imports(store_id, product_id, arrival_date);

CREATE TABLE IF NOT EXISTS stock_count_adjustments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id uuid NOT NULL REFERENCES stores(id),
    product_id uuid NOT NULL REFERENCES products(id),
    count_time timestamptz NOT NULL,
    business_date date NOT NULL,
    adjusted_quantity numeric NOT NULL,
    unit varchar NOT NULL,
    count_type varchar,
    remark text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_stock_count_adjustments_unique
    ON stock_count_adjustments(store_id, product_id, count_time);

CREATE TABLE IF NOT EXISTS import_exceptions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_file_name varchar NOT NULL,
    source_table varchar NOT NULL,
    raw_row_number integer,
    exception_type varchar NOT NULL,
    exception_message text NOT NULL,
    raw_payload jsonb,
    status varchar NOT NULL DEFAULT 'open',
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source_file_name, source_table, raw_row_number, exception_type)
);

CREATE TABLE IF NOT EXISTS inventory_positions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id uuid NOT NULL REFERENCES stores(id),
    product_id uuid NOT NULL REFERENCES products(id),
    business_date date NOT NULL,
    realtime_inventory_qty numeric,
    closing_inventory_qty numeric,
    theoretical_inventory_qty numeric,
    manual_adjustment_qty numeric,
    corrected_inventory_qty numeric NOT NULL,
    inventory_confidence varchar NOT NULL,
    inventory_source varchar NOT NULL,
    unit varchar NOT NULL,
    calculated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (store_id, product_id, business_date)
);

CREATE TABLE IF NOT EXISTS inventory_age_batches (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id uuid NOT NULL REFERENCES stores(id),
    product_id uuid NOT NULL REFERENCES products(id),
    arrival_date date NOT NULL,
    batch_quantity numeric NOT NULL,
    consumed_quantity numeric NOT NULL DEFAULT 0,
    remaining_quantity numeric NOT NULL DEFAULT 0,
    sellable_days numeric NOT NULL,
    expiry_date date NOT NULL,
    remaining_sellable_days numeric NOT NULL,
    batch_status varchar NOT NULL,
    unit varchar NOT NULL,
    calculated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (store_id, product_id, arrival_date)
);

CREATE TABLE IF NOT EXISTS sales_forecasts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id uuid NOT NULL REFERENCES stores(id),
    product_id uuid NOT NULL REFERENCES products(id),
    forecast_date date NOT NULL,
    forecast_quantity numeric NOT NULL,
    forecast_method varchar NOT NULL,
    sales_days_used integer NOT NULL,
    recent_daily_sales numeric,
    sales_stddev numeric NOT NULL DEFAULT 0,
    base_forecast_quantity numeric NOT NULL DEFAULT 0,
    historical_noon_ratio numeric,
    projected_today_sales_qty numeric,
    today_trend_factor numeric NOT NULL DEFAULT 1,
    forecast_adjustment_factor numeric NOT NULL DEFAULT 1,
    unit varchar NOT NULL,
    calculated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (store_id, product_id, forecast_date)
);

CREATE TABLE IF NOT EXISTS order_suggestions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id uuid NOT NULL REFERENCES stores(id),
    product_id uuid NOT NULL REFERENCES products(id),
    suggestion_date date NOT NULL,
    arrival_date date NOT NULL,
    forecast_quantity numeric NOT NULL,
    corrected_inventory_qty numeric NOT NULL,
    expected_inventory_at_arrival numeric,
    sellable_inventory_qty numeric,
    overstock_qty numeric,
    safety_stock_qty numeric NOT NULL,
    pending_arrival_qty numeric NOT NULL DEFAULT 0,
    raw_suggested_qty numeric NOT NULL,
    suggested_order_qty numeric NOT NULL,
    order_batch_qty numeric,
    min_order_qty numeric,
    suggestion_reason text,
    status varchar NOT NULL DEFAULT 'draft',
    unit varchar NOT NULL,
    calculated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (store_id, product_id, suggestion_date, arrival_date)
);

CREATE TABLE IF NOT EXISTS inventory_risks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id uuid NOT NULL REFERENCES stores(id),
    product_id uuid NOT NULL REFERENCES products(id),
    business_date date NOT NULL,
    risk_type varchar NOT NULL,
    risk_level varchar NOT NULL,
    risk_message text NOT NULL,
    related_quantity numeric,
    status varchar NOT NULL DEFAULT 'open',
    calculated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_inventory_risks_product_date
    ON inventory_risks(store_id, product_id, business_date);

CREATE INDEX IF NOT EXISTS idx_inventory_risks_type_level
    ON inventory_risks(risk_type, risk_level);
