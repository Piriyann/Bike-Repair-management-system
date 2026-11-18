from flask import Flask, render_template, request, redirect, url_for, session
import database
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'bikerepair2026'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = 'Invalid username or password!'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM customers')
    customer_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM services WHERE status != 'Done'")
    active_services = cursor.fetchone()[0]
    cursor.execute('SELECT * FROM inventory')
    inv = cursor.fetchall()
    low_stock_count = len([item for item in inv if item[2] < 5])
    cursor.execute('SELECT SUM(total_amount) FROM billing')
    revenue = cursor.fetchone()[0] or 0
    conn.close()
    stats = {
        'customers': customer_count,
        'active_services': active_services,
        'low_stock': low_stock_count,
        'revenue': revenue
    }
    return render_template('index.html', stats=stats)

@app.route('/customers')
@login_required
def customers():
    search = request.args.get('search', '')
    error = request.args.get('error', '')
    conn = database.get_connection()
    cursor = conn.cursor()
    if search:
        cursor.execute('SELECT * FROM customers WHERE name LIKE ?', ('%' + search + '%',))
    else:
        cursor.execute('SELECT * FROM customers')
    data = cursor.fetchall()
    conn.close()
    return render_template('customers.html', customers=data, search=search, error=error)

@app.route('/add_customer', methods=['POST'])
@login_required
def add_customer():
    name = request.form['name']
    phone = request.form['phone']
    nic = request.form['nic']
    email = request.form['email']
    address = request.form['address']
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM customers WHERE nic=?', (nic,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return redirect(url_for('customers', error='duplicate'))
    cursor.execute('INSERT INTO customers (name, phone, nic, email, address) VALUES (?, ?, ?, ?, ?)',
                   (name, phone, nic, email, address))
    conn.commit()
    conn.close()
    return redirect(url_for('customers'))

@app.route('/delete_customer/<int:id>')
@login_required
def delete_customer(id):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM customers WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('customers'))

@app.route('/services')
@login_required
def services():
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT services.id, customers.name, bikes.bike_model, bikes.bike_number, services.issue, services.status, services.date FROM services JOIN bikes ON services.bike_id = bikes.id JOIN customers ON bikes.customer_id = customers.id')
    data = cursor.fetchall()
    cursor.execute('SELECT id, name, nic FROM customers')
    customers_list = cursor.fetchall()
    conn.close()
    return render_template('services.html', services=data, customers=customers_list)

@app.route('/add_service', methods=['POST'])
@login_required
def add_service():
    customer_id = request.form['customer_id']
    bike_model = request.form['bike_model']
    bike_number = request.form['bike_number']
    issue = request.form['issue']
    date = datetime.now().strftime('%Y-%m-%d')
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO bikes (customer_id, bike_model, bike_number) VALUES (?, ?, ?)',
                   (customer_id, bike_model, bike_number))
    bike_id = cursor.lastrowid
    cursor.execute('INSERT INTO services (bike_id, issue, date) VALUES (?, ?, ?)',
                   (bike_id, issue, date))
    conn.commit()
    conn.close()
    return redirect(url_for('services'))

@app.route('/update_status/<int:id>', methods=['POST'])
@login_required
def update_status(id):
    status = request.form['status']
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE services SET status=? WHERE id=?', (status, id))
    conn.commit()
    conn.close()
    return redirect(url_for('services'))

@app.route('/delete_service/<int:id>')
@login_required
def delete_service(id):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM services WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('services'))

@app.route('/service_history/<int:customer_id>')
@login_required
def service_history(customer_id):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM customers WHERE id=?', (customer_id,))
    customer = cursor.fetchone()
    cursor.execute('SELECT services.id, bikes.bike_model, bikes.bike_number, services.issue, services.status, services.date FROM services JOIN bikes ON services.bike_id = bikes.id WHERE bikes.customer_id=?', (customer_id,))
    history = cursor.fetchall()
    conn.close()
    return render_template('service_history.html', customer=customer, history=history)

@app.route('/inventory')
@login_required
def inventory():
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory')
    data = cursor.fetchall()
    conn.close()
    low_stock = [item for item in data if item[2] < 5]
    return render_template('inventory.html', items=data, low_stock=low_stock)

@app.route('/add_inventory', methods=['POST'])
@login_required
def add_inventory():
    part_name = request.form['part_name']
    quantity = request.form['quantity']
    price = request.form['price']
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO inventory (part_name, quantity, price) VALUES (?, ?, ?)',
                   (part_name, quantity, price))
    conn.commit()
    conn.close()
    return redirect(url_for('inventory'))

@app.route('/delete_inventory/<int:id>')
@login_required
def delete_inventory(id):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM inventory WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('inventory'))

@app.route('/billing')
@login_required
def billing():
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT billing.id, customers.name, bikes.bike_model, billing.total_amount, billing.date FROM billing JOIN services ON billing.service_id = services.id JOIN bikes ON services.bike_id = bikes.id JOIN customers ON bikes.customer_id = customers.id')
    data = cursor.fetchall()
    cursor.execute('SELECT services.id, customers.name, bikes.bike_model, bikes.bike_number, services.issue, services.status FROM services JOIN bikes ON services.bike_id = bikes.id JOIN customers ON bikes.customer_id = customers.id WHERE services.id NOT IN (SELECT service_id FROM billing)')
    unbilled_services = cursor.fetchall()
    conn.close()
    return render_template('billing.html', bills=data, services=unbilled_services)

@app.route('/add_billing', methods=['POST'])
@login_required
def add_billing():
    service_id = request.form['service_id']
    total_amount = request.form['total_amount']
    date = datetime.now().strftime('%Y-%m-%d')
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO billing (service_id, total_amount, date) VALUES (?, ?, ?)',
                   (service_id, total_amount, date))
    conn.commit()
    conn.close()
    return redirect(url_for('billing'))

@app.route('/invoice/<int:id>')
@login_required
def invoice(id):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT billing.id, customers.name, customers.phone, customers.address, bikes.bike_model, bikes.bike_number, services.issue, billing.total_amount, billing.date FROM billing JOIN services ON billing.service_id = services.id JOIN bikes ON services.bike_id = bikes.id JOIN customers ON bikes.customer_id = customers.id WHERE billing.id=?', (id,))
    bill = cursor.fetchone()
    conn.close()
    return render_template('invoice.html', bill=bill)

@app.route('/analytics')
@login_required
def analytics():
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(total_amount) FROM billing')
    total_revenue = cursor.fetchone()[0] or 0
    cursor.execute('SELECT issue, COUNT(*) as count FROM services GROUP BY issue ORDER BY count DESC LIMIT 5')
    common_issues = cursor.fetchall()
    cursor.execute('SELECT date, SUM(total_amount) FROM billing GROUP BY date ORDER BY date DESC LIMIT 7')
    daily_revenue = cursor.fetchall()
    conn.close()
    return render_template('analytics.html', total_revenue=total_revenue, common_issues=common_issues, daily_revenue=daily_revenue)

if __name__ == '__main__':
    app.run(debug=True)