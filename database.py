import sqlite3

def create_database():
    connection = sqlite3.connect("cafe.db")
    cursor = connection.cursor()

    # Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            tea INTEGER DEFAULT 0,
            coffee INTEGER DEFAULT 0,
            sandwich INTEGER DEFAULT 0,
            burger INTEGER DEFAULT 0,
            total INTEGER NOT NULL
        )
    """)

    # Employees table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    """)

    # Attendance table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            meal_choice TEXT DEFAULT '',
            special_request TEXT DEFAULT ''
        )
    """)

    # Menu table — one row per day, storing breakfast/lunch/dinner
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            day TEXT PRIMARY KEY,
            breakfast TEXT NOT NULL,
            lunch TEXT NOT NULL,
            dinner TEXT NOT NULL
        )
    """)

    # Employees
    employees = [
        ("eshalfatima", "2007", "Eshal Fatima", 1),
        ("sara", "1234", "Sara Ahmed", 0),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO employees (username, password, full_name, is_admin) VALUES (?, ?, ?, ?)",
        employees
    )

    # Default weekly menu (only added if not already there)
    default_menu = [
        ("Monday",    "Paratha & Omelette", "Chicken Biryani",       "Daal & Rice"),
        ("Tuesday",   "Halwa Puri",         "Beef Pulao",            "Vegetable Curry & Roti"),
        ("Wednesday", "Bread & Eggs",       "Chicken Karahi & Roti", "Chana Chawal"),
        ("Thursday",  "Aloo Paratha",       "Daal Chawal",           "Chicken Handi & Naan"),
        ("Friday",    "Nihari & Naan",      "Chicken Qorma & Naan",  "Fried Rice"),
        ("Saturday",  "French Toast",       "Vegetable Rice",        "Chicken Pulao"),
        ("Sunday",    "Chana & Puri",       "Chapli Kabab & Naan",   "Qeema & Roti"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO menu (day, breakfast, lunch, dinner) VALUES (?, ?, ?, ?)",
        default_menu
    )

    connection.commit()
    connection.close()


if __name__ == "__main__":
    create_database()
    print("Database created successfully!")