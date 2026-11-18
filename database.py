import sqlite3

def get_connection():
    conn = sqlite3.connect('bike_repair.db')
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES ('S.PIRIYAN', 'BII2832')")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            nic TEXT NOT NULL,
            email TEXT,
            address TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bikes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            bike_model TEXT NOT NULL,
            bike_number TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bike_id INTEGER,
            issue TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            date TEXT NOT NULL,
            FOREIGN KEY (bike_id) REFERENCES bikes(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS billing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_id INTEGER,
            total_amount REAL NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (service_id) REFERENCES services(id)
        )
    ''')

    conn.commit()
    conn.close()

create_tables()