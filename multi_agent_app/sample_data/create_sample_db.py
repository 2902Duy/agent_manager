"""Script to create a sample SQLite database with demo data."""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "sample.db")


def create_sample_database():
    """Create tables and insert sample data for testing."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # -- Products table --
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # -- Sales table --
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            amount REAL NOT NULL,
            sale_date TEXT NOT NULL,
            region TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # -- Employees table --
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            position TEXT NOT NULL,
            salary REAL NOT NULL,
            hire_date TEXT NOT NULL
        )
    """)

    # -- Insert sample products --
    products = [
        ("Laptop Dell XPS 15", "Electronics", 35000000, 50),
        ("iPhone 15 Pro Max", "Electronics", 32000000, 100),
        ("Samsung Galaxy S24", "Electronics", 25000000, 80),
        ("Tai nghe Sony WH-1000XM5", "Accessories", 8500000, 200),
        ("Bàn phím Logitech MX Keys", "Accessories", 2500000, 150),
        ("Màn hình LG 27UK850", "Electronics", 12000000, 30),
        ("Chuột Logitech MX Master 3", "Accessories", 2200000, 120),
        ("iPad Air M2", "Electronics", 18000000, 60),
        ("Apple Watch Series 9", "Accessories", 12500000, 90),
        ("MacBook Pro M3", "Electronics", 45000000, 40),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)",
        products,
    )

    # -- Insert sample sales (monthly data for 2024) --
    sales_data = []
    import random

    random.seed(42)
    regions = ["Ha Noi", "Ho Chi Minh", "Da Nang", "Can Tho", "Hai Phong"]
    for month in range(1, 13):
        for product_id in range(1, 11):
            for region in regions:
                qty = random.randint(1, 20)
                price = products[product_id - 1][2]
                amount = qty * price
                sale_date = f"2024-{month:02d}-{random.randint(1, 28):02d}"
                sales_data.append((product_id, qty, amount, sale_date, region))

    cursor.executemany(
        "INSERT INTO sales (product_id, quantity, amount, sale_date, region) VALUES (?, ?, ?, ?, ?)",
        sales_data,
    )

    # -- Insert sample employees --
    employees = [
        ("Nguyen Van A", "Sales", "Manager", 25000000, "2020-03-15"),
        ("Tran Thi B", "Sales", "Staff", 12000000, "2021-06-01"),
        ("Le Van C", "Engineering", "Senior Dev", 30000000, "2019-01-10"),
        ("Pham Thi D", "Engineering", "Junior Dev", 15000000, "2023-02-20"),
        ("Hoang Van E", "Marketing", "Manager", 22000000, "2020-08-05"),
        ("Vo Thi F", "HR", "Staff", 13000000, "2022-04-12"),
        ("Dang Van G", "Engineering", "Tech Lead", 35000000, "2018-07-01"),
        ("Bui Thi H", "Sales", "Staff", 11000000, "2023-09-15"),
        ("Nguyen Van I", "Marketing", "Staff", 14000000, "2022-11-20"),
        ("Tran Van K", "Finance", "Manager", 28000000, "2019-05-10"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO employees (name, department, position, salary, hire_date) VALUES (?, ?, ?, ?, ?)",
        employees,
    )

    conn.commit()
    conn.close()
    print(f"Sample database created at: {DB_PATH}")
    print(f"  - products: {len(products)} rows")
    print(f"  - sales: {len(sales_data)} rows")
    print(f"  - employees: {len(employees)} rows")


if __name__ == "__main__":
    create_sample_database()
