#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
  CREATE DATABASE inventory_db;
  CREATE DATABASE orders_db;
  CREATE ROLE agent_reader WITH LOGIN PASSWORD 'agent_password';
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname inventory_db <<-EOSQL
  CREATE EXTENSION IF NOT EXISTS "pgcrypto";

  CREATE TABLE products (
    sku       VARCHAR(20) PRIMARY KEY,
    name      VARCHAR(255) NOT NULL,
    price     NUMERIC(10,2) NOT NULL,
    stock     INTEGER NOT NULL DEFAULT 0,
    category  VARCHAR(100),
    user_id   UUID NOT NULL
  );

  ALTER TABLE products ENABLE ROW LEVEL SECURITY;
  CREATE POLICY user_isolation ON products FOR SELECT TO agent_reader
    USING (user_id = current_setting('app.current_user_id', TRUE)::UUID);

  GRANT SELECT ON products TO agent_reader;

  INSERT INTO products (sku, name, price, stock, category, user_id) VALUES
    ('SKU001', 'Wireless Mouse',      29.99, 150, 'electronics', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'),
    ('SKU002', 'USB-C Hub',           49.99,  45, 'electronics', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'),
    ('SKU003', 'Webcam HD',           59.99,  22, 'electronics', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'),
    ('SKU004', 'Mechanical Keyboard', 89.99,  75, 'electronics', 'b2c3d4e5-f6a7-8901-bcde-f12345678901'),
    ('SKU005', 'Laptop Stand',        39.99,  73, 'accessories', 'b2c3d4e5-f6a7-8901-bcde-f12345678901'),
    ('SKU006', 'Wireless Earbuds',    44.99, 200, 'electronics', 'c3d4e5f6-a7b8-9012-cdef-123456789012'),
    ('SKU007', 'Monitor Light Bar',   34.99,  60, 'accessories', 'c3d4e5f6-a7b8-9012-cdef-123456789012');
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname orders_db <<-EOSQL
  CREATE EXTENSION IF NOT EXISTS "pgcrypto";

  CREATE TABLE orders (
    order_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL,
    status     VARCHAR(20) NOT NULL DEFAULT 'pending',
    total      NUMERIC(10,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  );

  CREATE TABLE order_items (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id   UUID NOT NULL REFERENCES orders(order_id),
    name       VARCHAR(255) NOT NULL,
    quantity   INTEGER NOT NULL DEFAULT 1,
    price      NUMERIC(10,2) NOT NULL DEFAULT 0
  );

  ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
  ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;

  CREATE POLICY user_isolation ON orders FOR SELECT TO agent_reader
    USING (user_id = current_setting('app.current_user_id', TRUE)::UUID);
  CREATE POLICY user_isolation ON order_items FOR SELECT TO agent_reader
    USING (order_id IN (
      SELECT order_id FROM orders
      WHERE user_id = current_setting('app.current_user_id', TRUE)::UUID
    ));

  GRANT SELECT ON orders TO agent_reader;
  GRANT SELECT ON order_items TO agent_reader;

  INSERT INTO orders (order_id, user_id, status, total, created_at) VALUES
    ('11111111-1111-1111-1111-000000000001', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'delivered', 59.98,  NOW() - INTERVAL '7 days'),
    ('11111111-1111-1111-1111-000000000002', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'pending',   109.98, NOW() - INTERVAL '1 day'),
    ('22222222-2222-2222-2222-000000000003', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 'shipped',   39.99,  NOW() - INTERVAL '3 days'),
    ('33333333-3333-3333-3333-000000000004', 'c3d4e5f6-a7b8-9012-cdef-123456789012', 'pending',   134.97, NOW() - INTERVAL '2 days'),
    ('33333333-3333-3333-3333-000000000005', 'c3d4e5f6-a7b8-9012-cdef-123456789012', 'cancelled', 34.99,  NOW() - INTERVAL '5 days');

  INSERT INTO order_items (order_id, name, quantity, price) VALUES
    ('11111111-1111-1111-1111-000000000001', 'Wireless Mouse',    2, 29.99),
    ('11111111-1111-1111-1111-000000000002', 'USB-C Hub',         1, 49.99),
    ('11111111-1111-1111-1111-000000000002', 'Webcam HD',         1, 59.99),
    ('22222222-2222-2222-2222-000000000003', 'Laptop Stand',      1, 39.99),
    ('33333333-3333-3333-3333-000000000004', 'Wireless Earbuds',  3, 44.99),
    ('33333333-3333-3333-3333-000000000005', 'Monitor Light Bar', 1, 34.99);
EOSQL
