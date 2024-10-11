from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import bcrypt

app = Flask(__name__)
app.secret_key = 'CHINUVAISH'  # Change this to a random secret key

# Database connection function
def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',  # Replace with your MySQL username
        password='sa123',  # Replace with your MySQL password
        database='blood_bank'
    )
    return connection

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# User registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password, role) VALUES (%s, %s, %s)',
                       (username, hashed, 'user'))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# User authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            # user[2] is password, user[3] is role
            if bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
                session['username'] = username
                session['role'] = user[3]  # Store user role
                return redirect(url_for('home'))
            else:
                flash('Invalid password, please try again.', 'danger')
        else:
            flash('Username not found, please register first.', 'warning')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# Admin dashboard route
@app.route('/dashboard')
def dashboard():
    if 'role' not in session or session['role'] != 'admin':
        flash('Access denied. You are not authorized to view this page.', 'danger')
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM donors')
    donor_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM receivers')
    receiver_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM blood_inventory')
    inventory_count = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    return render_template('dashboard.html', donor_count=donor_count, receiver_count=receiver_count, inventory_count=inventory_count)

# Donor management routes
@app.route('/donors', methods=['GET', 'POST'])
def donors():
    search_query = request.form.get('search') if request.method == 'POST' else None
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if search_query:
        cursor.execute('SELECT * FROM donors WHERE name LIKE %s OR blood_type LIKE %s', (f'%{search_query}%', f'%{search_query}%'))
    else:
        cursor.execute('SELECT * FROM donors')
    
    donor_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('donors.html', donors=donor_list)

@app.route('/add_donor', methods=['GET', 'POST'])
def add_donor():
    if request.method == 'POST':
        name = request.form['name']
        blood_type = request.form['blood_type']
        contact = request.form['contact']
        last_donation = request.form['last_donation']
        age = int(request.form['age'])
        weight = int(request.form['weight'])
        medical_history = request.form['medical_history']

        # Eligibility check
        if age < 18 or weight < 50:  # Example eligibility criteria
            flash("You are not eligible to donate blood.", 'warning')
            return redirect(url_for('add_donor'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO donors (name, blood_type, contact, last_donation, age, weight, medical_history) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                       (name, blood_type, contact, last_donation, age, weight, medical_history))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Donor added successfully.", 'success')
        return redirect(url_for('donors'))

    return render_template('add_donor.html')

@app.route('/delete_donor', methods=['GET', 'POST'])
def delete_donor():
    if request.method == 'POST':
        name = str(request.form['name'])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('delete from donors where name = (%s)',(name,))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Receiver deleted successfully.", 'success')
        return redirect(url_for('donors'))

    return render_template('delete_donor.html')
# Receiver management routes
@app.route('/receivers', methods=['GET', 'POST'])
def receivers():
    search_query = request.form.get('search') if request.method == 'POST' else None
    conn = get_db_connection()
    cursor = conn.cursor()

    if search_query:
        cursor.execute('SELECT * FROM receivers WHERE name LIKE %s OR blood_type LIKE %s', (f'%{search_query}%', f'%{search_query}%'))
    else:
        cursor.execute('SELECT * FROM receivers')

    receiver_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('receivers.html', receivers=receiver_list)

@app.route('/add_receiver', methods=['GET', 'POST'])
def add_receiver():
    if request.method == 'POST':
        name = request.form['name']
        blood_type = request.form['blood_type']
        contact = request.form['contact']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO receivers (name, blood_type, contact) VALUES (%s, %s, %s)',
                       (name, blood_type, contact))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Receiver added successfully.", 'success')
        return redirect(url_for('receivers'))

    return render_template('add_receiver.html')

@app.route('/delete_receiver', methods=['GET', 'POST'])
def delete_receiver():
    if request.method == 'POST':
        name = str(request.form['name'])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('delete from receivers where name = (%s)',(name,))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Receiver deleted successfully.", 'success')
        return redirect(url_for('receivers'))

    return render_template('delete_receiver.html')

# Blood inventory management routes
@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        blood_type = request.form['blood_type']
        quantity = request.form['quantity']
        cursor.execute('INSERT INTO blood_inventory (blood_type, quantity) VALUES (%s, %s)',
                       (blood_type, quantity))
        conn.commit()

    cursor.execute('SELECT * FROM blood_inventory')
    inventory_list = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('inventory.html', inventory=inventory_list)

# Feedback route
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        user_feedback = request.form['feedback']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO feedback (feedback) VALUES (%s)', (user_feedback,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Thank you for your feedback!", 'success')
        return redirect(url_for('home'))

    return render_template('feedback.html')

# User profile route
@app.route('/profile')
def profile():
    if 'username' not in session:
        flash('Please log in to view your profile.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = %s', (session['username'],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('profile.html', user=user)

if __name__ == '__main__':
    app.run(debug=True)
