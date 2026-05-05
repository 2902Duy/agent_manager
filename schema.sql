DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    city TEXT NOT NULL,
    segment TEXT NOT NULL
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price REAL NOT NULL
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

INSERT INTO customers (id, name, email, city, segment) VALUES
    (1, 'An Nguyễn', 'an.nguyen@example.com', 'Hà Nội', 'SMB'),
    (2, 'Bình Trần', 'binh.tran@example.com', 'Đà Nẵng', 'Enterprise'),
    (3, 'Chi Lê', 'chi.le@example.com', 'TP. Hồ Chí Minh', 'SMB'),
    (4, 'Dũng Phạm', 'dung.pham@example.com', 'Cần Thơ', 'Startup');

INSERT INTO products (id, name, category, unit_price) VALUES
    (1, 'CrewAI Workshop', 'Training', 2500000),
    (2, 'RAG Starter Kit', 'Software', 1800000),
    (3, 'Ollama Deployment Support', 'Service', 3200000),
    (4, 'SQL Analytics Pack', 'Software', 1500000);

INSERT INTO orders (id, customer_id, order_date, status) VALUES
    (1, 1, '2026-04-01', 'paid'),
    (2, 2, '2026-04-03', 'paid'),
    (3, 3, '2026-04-10', 'pending'),
    (4, 1, '2026-04-18', 'paid'),
    (5, 4, '2026-04-20', 'cancelled');

INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES
    (1, 1, 1, 1, 2500000),
    (2, 1, 2, 2, 1800000),
    (3, 2, 3, 1, 3200000),
    (4, 2, 4, 3, 1500000),
    (5, 3, 2, 1, 1800000),
    (6, 4, 4, 2, 1500000),
    (7, 5, 1, 1, 2500000);
