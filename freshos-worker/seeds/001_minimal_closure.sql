INSERT INTO stores (
    id,
    store_code,
    store_name,
    store_status,
    is_active
)
VALUES (
    '00000000-0000-0000-0000-000000000101',
    '10008',
    '宝信润山店',
    '正常',
    true
)
ON CONFLICT (store_code)
DO UPDATE SET
    store_name = EXCLUDED.store_name,
    store_status = EXCLUDED.store_status,
    is_active = EXCLUDED.is_active,
    updated_at = now();

INSERT INTO products (
    id,
    product_code,
    product_name,
    barcode,
    cat_id_01,
    cat_name_01,
    cat_id_02,
    cat_name_02,
    sale_unit,
    fresh_attribute,
    shelf_life_days,
    sellable_days,
    sellable_days_source,
    sellable_days_review_status,
    is_active
)
VALUES (
    '00000000-0000-0000-0000-000000000201',
    '2014691',
    '海南香蕉',
    'barcode-1',
    '42',
    '日配生鲜',
    '4201',
    '水果',
    'kg',
    '普通水果',
    3,
    3,
    'seed',
    'pending',
    true
)
ON CONFLICT (product_code)
DO UPDATE SET
    product_name = EXCLUDED.product_name,
    barcode = EXCLUDED.barcode,
    cat_id_01 = EXCLUDED.cat_id_01,
    cat_name_01 = EXCLUDED.cat_name_01,
    cat_id_02 = EXCLUDED.cat_id_02,
    cat_name_02 = EXCLUDED.cat_name_02,
    sale_unit = EXCLUDED.sale_unit,
    fresh_attribute = EXCLUDED.fresh_attribute,
    shelf_life_days = EXCLUDED.shelf_life_days,
    sellable_days = EXCLUDED.sellable_days,
    sellable_days_source = EXCLUDED.sellable_days_source,
    sellable_days_review_status = EXCLUDED.sellable_days_review_status,
    is_active = EXCLUDED.is_active,
    updated_at = now();

INSERT INTO store_products (
    store_id,
    product_id,
    store_order_status,
    store_sale_status,
    is_orderable,
    is_sellable,
    package_size,
    order_batch_qty,
    min_order_qty,
    safety_stock_days,
    recent_daily_sales,
    store_stock_qty_yesterday,
    is_active
)
VALUES (
    '00000000-0000-0000-0000-000000000101',
    '00000000-0000-0000-0000-000000000201',
    '门店可订',
    '门店可销售',
    true,
    true,
    1,
    5,
    5,
    1,
    9,
    6,
    true
)
ON CONFLICT (store_id, product_id)
DO UPDATE SET
    store_order_status = EXCLUDED.store_order_status,
    store_sale_status = EXCLUDED.store_sale_status,
    is_orderable = EXCLUDED.is_orderable,
    is_sellable = EXCLUDED.is_sellable,
    package_size = EXCLUDED.package_size,
    order_batch_qty = EXCLUDED.order_batch_qty,
    min_order_qty = EXCLUDED.min_order_qty,
    safety_stock_days = EXCLUDED.safety_stock_days,
    recent_daily_sales = EXCLUDED.recent_daily_sales,
    store_stock_qty_yesterday = EXCLUDED.store_stock_qty_yesterday,
    is_active = EXCLUDED.is_active,
    updated_at = now();

INSERT INTO sales_daily (
    store_id,
    product_id,
    business_date,
    sales_quantity,
    sales_amount,
    unit,
    source_file
)
VALUES
    ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000201', '2026-05-12', 9, 63, 'kg', 'seed'),
    ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000201', '2026-05-13', 10, 70, 'kg', 'seed'),
    ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000201', '2026-05-14', 8, 56, 'kg', 'seed'),
    ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000201', '2026-05-15', 11, 77, 'kg', 'seed'),
    ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000201', '2026-05-16', 9, 63, 'kg', 'seed'),
    ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000201', '2026-05-17', 10, 70, 'kg', 'seed'),
    ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000201', '2026-05-18', 12, 84, 'kg', 'seed'),
    ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000201', '2026-05-19', 9, 63, 'kg', 'seed'),
    ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000201', '2026-05-20', 10, 70, 'kg', 'seed'),
    ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000201', '2026-05-21', 11, 77, 'kg', 'seed'),
    ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000201', '2026-05-22', 8, 56, 'kg', 'seed'),
    ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000201', '2026-05-23', 10, 70, 'kg', 'seed'),
    ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000201', '2026-05-24', 11, 77, 'kg', 'seed'),
    ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000201', '2026-05-25', 9, 63, 'kg', 'seed')
ON CONFLICT (store_id, product_id, business_date)
DO UPDATE SET
    sales_quantity = EXCLUDED.sales_quantity,
    sales_amount = EXCLUDED.sales_amount,
    unit = EXCLUDED.unit,
    source_file = EXCLUDED.source_file,
    imported_at = now();

INSERT INTO inventory_snapshots (
    store_id,
    product_id,
    snapshot_time,
    business_date,
    inventory_quantity,
    inventory_source,
    unit,
    source_file
)
VALUES (
    '00000000-0000-0000-0000-000000000101',
    '00000000-0000-0000-0000-000000000201',
    '2026-05-26 06:00:00+08',
    '2026-05-26',
    3,
    'realtime',
    'kg',
    'seed'
)
ON CONFLICT (store_id, product_id, snapshot_time, inventory_source)
DO UPDATE SET
    inventory_quantity = EXCLUDED.inventory_quantity,
    unit = EXCLUDED.unit,
    source_file = EXCLUDED.source_file,
    imported_at = now();

INSERT INTO inventory_loss_daily (
    store_id,
    product_id,
    business_date,
    closing_stock_qty,
    loss_quantity,
    loss_amount,
    inventory_difference_qty,
    unit,
    source_file
)
VALUES (
    '00000000-0000-0000-0000-000000000101',
    '00000000-0000-0000-0000-000000000201',
    '2026-05-26',
    4,
    12,
    84,
    0,
    'kg',
    'seed'
)
ON CONFLICT (store_id, product_id, business_date)
DO UPDATE SET
    closing_stock_qty = EXCLUDED.closing_stock_qty,
    loss_quantity = EXCLUDED.loss_quantity,
    loss_amount = EXCLUDED.loss_amount,
    inventory_difference_qty = EXCLUDED.inventory_difference_qty,
    unit = EXCLUDED.unit,
    source_file = EXCLUDED.source_file,
    imported_at = now();

INSERT INTO fresh_order_imports (
    source_file_name,
    source_sheet_name,
    source_format,
    supplier_name,
    store_id,
    store_name_raw,
    product_id,
    product_name_raw,
    order_date,
    arrival_date,
    ordered_quantity,
    arrival_quantity,
    unit,
    match_status,
    raw_row_number
)
VALUES (
    'seed_order.xlsx',
    'Sheet1',
    'seed',
    '测试供应商',
    '00000000-0000-0000-0000-000000000101',
    '宝信润山店',
    '00000000-0000-0000-0000-000000000201',
    '海南香蕉',
    '2026-05-26',
    '2026-05-27',
    5,
    5,
    'kg',
    'matched',
    1
)
ON CONFLICT (source_file_name, source_sheet_name, raw_row_number)
DO UPDATE SET
    supplier_name = EXCLUDED.supplier_name,
    store_id = EXCLUDED.store_id,
    store_name_raw = EXCLUDED.store_name_raw,
    product_id = EXCLUDED.product_id,
    product_name_raw = EXCLUDED.product_name_raw,
    order_date = EXCLUDED.order_date,
    arrival_date = EXCLUDED.arrival_date,
    ordered_quantity = EXCLUDED.ordered_quantity,
    arrival_quantity = EXCLUDED.arrival_quantity,
    unit = EXCLUDED.unit,
    match_status = EXCLUDED.match_status,
    imported_at = now();
