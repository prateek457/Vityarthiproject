## 🚀 **SQLite Order Management System — Command-Line (CLI) Project Overview**

This document outlines the current state, testing procedures, next steps for development, and common questions for an **Order Management System** built with **SQLite** and accessible via a **Command-Line Interface (CLI)**.

---

### 📦 **Current Features & Persistence**

The system uses SQLite for persistence, ensuring it's lightweight and easy to set up.

* **Idempotent Demo Data:** The system is pre-loaded with sample data that can be inserted reliably without duplication:
    * **Customers:** Alice (ID: 1), Bob (ID: 2)
    * **Products:** SKU-001 (ID: 1, Price: $9.99), SKU-002 (ID: 2, Price: $19.99)
* **Core Order Functionality:** Includes schema for customers, products, orders, and order items. 

---

### 🧪 **Testing & Quality Assurance**

Testing is crucial for reliable business logic. The current setup focuses on speed and isolation.

* **In-Memory Testing:** Tests run using the special `sqlite :memory:` database, making them **fast** and ensuring complete **isolation** between test runs.
* **Test Coverage Examples:**
    * Database schema creation and integrity.
    * **Transactional** order creation (ensuring atomicity).
    * **Snapshot Pricing** verification (checking that `unit_price` is stored correctly).
    * Status transition logic (e.g., pending $\rightarrow$ confirmed).
    * Deletion cascade logic.
* **How to Run Tests:**
    ```bash
    python -m unittest discover -v
    ```

---

### 🎯 **Development Recommendations (Next Steps)**

The following steps are recommended to improve the project's architecture, functionality, and maintainability.

#### **Architecture & Modularity**

* **Refactor into Modules:** Organize the codebase into clear layers:
    * `db.py`: Handles **database connection** and raw **SQL** execution.
    * `models.py`: Contains simple **data classes** (e.g., `Product`, `Order`). *(Optional, but recommended)*
    * `services.py`: Implements **business logic** (e.g., order creation, validation, pricing).
    * `cli.py / main.py`: The **command-line interface** entry point.

#### **Features & Operations**

* Add an **"Export"** feature to output data to formats like **CSV/JSON**, along with corresponding tests.
* Implement **logging** to record critical operations, warnings, and errors for easier debugging and auditing.

#### **Process & DevOps**

* Set up a **Continuous Integration (CI) workflow** (e.g., **GitHub Actions**) to automatically run tests on every push or pull request.
* Consider **packaging** the application and providing **example scripts** for users who want to interact with the system programmatically (e.g., integrate it into a larger Python application).

---

### 🤝 **Contributing Guidelines**

We welcome contributions to the project!

* Create a **`CONTRIBUTING.md`** file detailing:
    * How to **run tests**.
    * Expected **code style** (e.g., using `black`, `flake8`).
    * **Branch strategy** (e.g., feature branches).
* Use **small Pull Requests (PRs)**, focusing on one feature or fix per branch.
* All new behavior **must** be accompanied by **unit tests**.

---

### ❓ **Frequently Asked Questions (FAQ)**

| Question | Answer |
| :--- | :--- |
| **Why store `unit_price` in `order_items`?** | This practice (often called **snapshot pricing**) ensures historical orders remain **accurate** even if the product's price changes later. |
| **Can I delete a product?** | **No.** Product deletion is currently **restricted** to maintain order history integrity. Modify the schema's foreign key constraints if a different policy is desired (e.g., soft deletes). |
| **How to add an inventory/stock feature?** | Add a **`quantity`** column to the `products` table. During order confirmation, **transactionally decrement** the stock using a **reservation pattern** to ensure consistency.  |

---

MADE BY - PRATEEK KUMAR 


REG NO. - 25BCY10192


VIT BHOPAL 

* **License:** MIT (Please replace the generic author/contact information).
* **Author:** Replace **`[Your Name]`** with the real author's name, and add a contact or repository link.

---

### 📜 **Changelog (Suggested Format)**

* **v1.0** — Initial launch: CLI functionality, SQLite persistence, and foundational tests.
* **v1.1** — Improved `README.md`, added a test for cascade deletion, and suggested CSV export as the next feature.
