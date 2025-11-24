


import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "orders.db"

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL CHECK(price >= 0),
    sku TEXT UNIQUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    total REAL NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price REAL NOT NULL CHECK(unit_price >= 0),
    FOREIGN KEY(order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY(product_id) REFERENCES products(product_id)
);
"""


def format_currency(amount: float) -> str:
    """Formats a float as a currency string."""
    return f"${amount:,.2f}"


class OrderRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._setup_db()

    def get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _setup_db(self):
        conn = self.get_conn()
        try:
            conn.executescript(SCHEMA)
        finally:
            conn.close()

    
    def create_customer(self, name: str, email: str = None, phone: str = None) -> int:
        with self.get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO customers (name, email, phone) VALUES (?, ?, ?)",
                (name, email, phone)
            )
            return cur.lastrowid

    def get_customer(self, customer_id: int) -> Optional[Dict[str, Any]]:
        conn = self.get_conn()
        try:
            cur = conn.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    
    def create_product(self, name: str, price: float, sku: str = None) -> int:
        with self.get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO products (name, price, sku) VALUES (?, ?, ?)",
                (name, price, sku)
            )
            return cur.lastrowid

    def list_products(self) -> List[Dict[str, Any]]:
        conn = self.get_conn()
        try:
            cur = conn.execute("SELECT * FROM products ORDER BY product_id")
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def get_product_price_map(self, product_ids: List[int]) -> Dict[int, float]:
        """Helper to fetch prices for a list of IDs in one query."""
        if not product_ids:
            return {}
        placeholders = ",".join("?" * len(product_ids))
        conn = self.get_conn()
        try:
            cur = conn.execute(f"SELECT product_id, price FROM products WHERE product_id IN ({placeholders})", product_ids)
            return {row['product_id']: row['price'] for row in cur.fetchall()}
        finally:
            conn.close()

    
    def create_order(self, customer_id: int, items: List[Tuple[int, int]]) -> int:
        """
        Transactional creation of an Order and its OrderItems.
        items: [(product_id, quantity), ...]
        """
        price_map = self.get_product_price_map([pid for pid, _ in items])
        
        
        for pid, _ in items:
            if pid not in price_map:
                raise ValueError(f"Product ID {pid} not found.")

        total_amount = sum(price_map[pid] * qty for pid, qty in items)

        with self.get_conn() as conn:
            
            cur = conn.execute(
                "INSERT INTO orders (customer_id, status, total) VALUES (?, 'pending', ?)",
                (customer_id, total_amount)
            )
            order_id = cur.lastrowid

            
            for pid, qty in items:
                conn.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                    (order_id, pid, qty, price_map[pid])
                )
            return order_id

    def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        conn = self.get_conn()
        try:
            cur = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
            row = cur.fetchone()
            if not row:
                return None
            
            order = dict(row)
            
            item_cur = conn.execute("""
                SELECT oi.product_id, p.name, oi.quantity, oi.unit_price, (oi.quantity * oi.unit_price) as line_total
                FROM order_items oi
                JOIN products p ON oi.product_id = p.product_id
                WHERE oi.order_id = ?
            """, (order_id,))
            order['items'] = [dict(r) for r in item_cur.fetchall()]
            return order
        finally:
            conn.close()

    def list_orders(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self.get_conn()
        try:
           
            query = """
                SELECT o.order_id, o.status, o.total, o.created_at, c.name as customer_name
                FROM orders o
                JOIN customers c ON o.customer_id = c.customer_id
                ORDER BY o.created_at DESC LIMIT ?
            """
            cur = conn.execute(query, (limit,))
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def update_order_status(self, order_id: int, new_status: str) -> bool:
        valid_statuses = {'pending', 'processing', 'shipped', 'cancelled', 'completed'}
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")

        with self.get_conn() as conn:
            cur = conn.execute(
                "UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE order_id = ?",
                (new_status, order_id)
            )
            return cur.rowcount > 0

    def delete_order(self, order_id: int) -> bool:
        with self.get_conn() as conn:
            cur = conn.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
            return cur.rowcount > 0

    def seed_demo_data(self):
        if not self.list_products():
            print("Seeding demo data...")
            self.create_customer("Alice Johnson", "alice@corp.com")
            self.create_customer("Bob Smith", "bob@agency.com")
            self.create_product("Laptop Stand", 29.99, "SKU-LP-100")
            self.create_product("USB-C Hub", 45.50, "SKU-USB-200")
            self.create_product("Monitor 24in", 120.00, "SKU-MON-300")


def prompt_int(msg: str) -> int:
    while True:
        val = input(msg).strip()
        if val.isdigit(): return int(val)
        print(">> Invalid integer. Try again.")

def main():
    repo = OrderRepository(DB_PATH)
    repo.seed_demo_data()

    while True:
        print(f"\n--- Order System ({DB_PATH}) ---")
        print("1. List Products")
        print("2. List Orders")
        print("3. Create Order")
        print("4. View Order Details")
        print("5. Update Order Status")
        print("6. Delete Order")
        print("0. Exit")
        
        choice = input("Select: ").strip()

        try:
            if choice == "1":
                print(f"\n{'ID':<5} {'SKU':<15} {'Price':<10} {'Name'}")
                print("-" * 50)
                for p in repo.list_products():
                    print(f"{p['product_id']:<5} {p['sku']:<15} {format_currency(p['price']):<10} {p['name']}")

            elif choice == "2":
                orders = repo.list_orders()
                print(f"\n{'ID':<5} {'Status':<12} {'Total':<10} {'Customer'}")
                print("-" * 50)
                for o in orders:
                    print(f"{o['order_id']:<5} {o['status']:<12} {format_currency(o['total']):<10} {o['customer_name']}")

            elif choice == "3":
                cust_id = prompt_int("Customer ID: ")
                if not repo.get_customer(cust_id):
                    print(">> Customer not found.")
                    continue
                
                items = []
                print("Enter items (Product ID, Quantity). Empty line to finish.")
                while True:
                    line = input("PID, QTY: ").strip()
                    if not line: break
                    try:
                        pid, qty = map(int, line.split(','))
                        if qty > 0: items.append((pid, qty))
                    except ValueError:
                        print(">> Use format: 1, 5")

                if items:
                    oid = repo.create_order(cust_id, items)
                    print(f">> Order created successfully! ID: {oid}")
                else:
                    print(">> Order cancelled (no items).")

            elif choice == "4":
                oid = prompt_int("Order ID: ")
                order = repo.get_order(oid)
                if order:
                    print(f"\nOrder #{order['order_id']} [{order['status'].upper()}]")
                    print(f"Date: {order['created_at']}")
                    print(f"Total: {format_currency(order['total'])}")
                    print("Line Items:")
                    for item in order['items']:
                        print(f" - {item['name']} x{item['quantity']} @ {format_currency(item['unit_price'])} = {format_currency(item['line_total'])}")
                else:
                    print(">> Order not found.")

            elif choice == "5":
                oid = prompt_int("Order ID: ")
                status = input("New Status (pending/processing/shipped/cancelled/completed): ").strip()
                if repo.update_order_status(oid, status):
                    print(">> Status updated.")
                else:
                    print(">> Update failed (Check ID or spelling).")

            elif choice == "6":
                oid = prompt_int("Order ID: ")
                if repo.delete_order(oid):
                    print(">> Order deleted.")
                else:
                    print(">> Order not found.")

            elif choice == "0":
                print("Goodbye.")
                sys.exit(0)
            else:
                print("Invalid option.")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()