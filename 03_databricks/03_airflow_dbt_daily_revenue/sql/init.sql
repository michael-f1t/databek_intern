CREATE TABLE IF NOT EXISTS public.customers (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS public.orders (
    id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES public.customers(id),
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS public.products (
    id BIGINT PRIMARY KEY,
    product_name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS public.order_items (
    id BIGINT PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES public.orders(id),
    product_id BIGINT NOT NULL REFERENCES public.products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0)
);
INSERT INTO customers (id, name) VALUES (1, 'Sample Customer')
ON CONFLICT DO NOTHING;
INSERT INTO products (id, product_name) VALUES (1, 'Sample Product')
ON CONFLICT DO NOTHING;
INSERT INTO orders (id, customer_id, created_at)
VALUES (1001, 1, date_trunc('day', now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'
        - INTERVAL '1 day' + INTERVAL '10 hours')
ON CONFLICT DO NOTHING;
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price)
VALUES (5001, 1001, 1, 2, 19.99)
ON CONFLICT DO NOTHING;
