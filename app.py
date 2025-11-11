from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import pymysql
from pymysql.cursors import DictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re
from dotenv import load_dotenv

# Load environment variables (for local testing)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "secretkey123")
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

# ==================== DATABASE CONNECTION ====================

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = int(os.getenv("DB_PORT", "3306"))


def get_db():
    """Return a MySQL connection"""
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        port=DB_PORT,
        cursorclass=DictCursor,
        autocommit=False
    )
    return conn


def init_db():
    """Initialize MySQL database (create tables and admin user if not exist)"""
    conn = get_db()
    c = conn.cursor()

    # USERS TABLE
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        first_name VARCHAR(255) NOT NULL,
        last_name VARCHAR(255) NOT NULL,
        fullname VARCHAR(511) NOT NULL,
        email VARCHAR(255) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        contact VARCHAR(50),
        birthdate VARCHAR(50),
        civil_status VARCHAR(50),
        address TEXT,
        fathers_name VARCHAR(255),
        mothers_name VARCHAR(255),
        birthplace VARCHAR(255),
        role VARCHAR(50) DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    ''')

    # REQUESTS TABLE
    c.execute('''
    CREATE TABLE IF NOT EXISTS requests (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        document_type VARCHAR(255) NOT NULL,
        full_name VARCHAR(511) NOT NULL,
        address TEXT NOT NULL,
        contact VARCHAR(50) NOT NULL,
        purpose TEXT NOT NULL,
        status VARCHAR(50) DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    ) ENGINE=InnoDB;
    ''')

    # INSERT ADMIN IF NOT EXISTS
    admin_email = 'adminsislc@domain.com'
    c.execute('SELECT id FROM users WHERE email = %s', (admin_email,))
    admin = c.fetchone()
    if not admin:
        hashed = generate_password_hash('S3cr#t@dm1n')
        c.execute('''
            INSERT INTO users (first_name, last_name, fullname, email, password, contact, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', ('Admin', 'User', 'Admin User', admin_email, hashed, '09123456789', 'admin'))

    conn.commit()
    c.close()
    conn.close()
    print(" MySQL database initialized successfully!")


# ==================== VALIDATION ====================

def validate_contact(contact):
    return re.match(r'^09\d{9}$', contact) is not None


# ==================== ROUTES ====================

@app.route('/')
def home():
    lang = session.get('lang', 'en')
    if lang == 'tl':
        return render_template('index_tl.html')
    return render_template('index_en.html')


@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['en', 'tl']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('home'))


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user is None:
            flash("You do not have an account.", "error")
        elif check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['fullname'] = user['fullname']
            session['email'] = user['email']

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash("Invalid password", "error")

    lang = session.get('lang', 'en')
    return render_template('login_tl.html' if lang == 'tl' else 'login.html')


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for('register_page'))

        fullname = f"{first_name} {last_name}"
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute('''INSERT INTO users (first_name, last_name, fullname, email, password)
                           VALUES (%s, %s, %s, %s, %s)''',
                        (first_name, last_name, fullname, email, generate_password_hash(password)))
            conn.commit()

            cur.execute('SELECT id FROM users WHERE email = %s', (email,))
            user = cur.fetchone()
            session['user_id'] = user['id']
            session['role'] = 'user'
            session['fullname'] = fullname
            session['email'] = email

            flash("Registration successful! Please complete your profile.", "info")
            return redirect(url_for('edit_account'))

        except pymysql.err.IntegrityError:
            flash("Email already exists", "error")
        finally:
            cur.close()
            conn.close()

    lang = session.get('lang', 'en')
    return render_template('register_tl.html' if lang == 'tl' else 'register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/edit_account', methods=['GET', 'POST'])
def edit_account():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        contact = request.form['contact']
        email = request.form['email']
        password = request.form.get('password', '')
        birthdate = request.form['birthdate']
        civil_status = request.form['civil_status']
        address = request.form['address']
        fathers_name = request.form.get('fathers_name', '')
        mothers_name = request.form.get('mothers_name', '')
        birthplace = request.form.get('birthplace', '')

        fullname = f"{first_name} {last_name}"

        if not validate_contact(contact):
            flash("Contact number must be 11 digits and start with 09", "error")
            cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            user = cur.fetchone()
            cur.close()
            conn.close()
            lang = session.get('lang', 'en')
            return render_template('edit_account_tl.html' if lang == 'tl' else 'edit_account.html', user=user)

        if password:
            cur.execute('''UPDATE users 
                           SET first_name=%s, last_name=%s, fullname=%s, contact=%s, email=%s, password=%s, 
                               birthdate=%s, civil_status=%s, address=%s, fathers_name=%s, mothers_name=%s, birthplace=%s 
                           WHERE id=%s''',
                        (first_name, last_name, fullname, contact, email, generate_password_hash(password),
                         birthdate, civil_status, address, fathers_name, mothers_name, birthplace, user_id))
        else:
            cur.execute('''UPDATE users 
                           SET first_name=%s, last_name=%s, fullname=%s, contact=%s, email=%s, 
                               birthdate=%s, civil_status=%s, address=%s, fathers_name=%s, mothers_name=%s, birthplace=%s 
                           WHERE id=%s''',
                        (first_name, last_name, fullname, contact, email,
                         birthdate, civil_status, address, fathers_name, mothers_name, birthplace, user_id))

        conn.commit()
        session['fullname'] = fullname
        flash("Account updated successfully!", "success")
        cur.close()
        conn.close()
        return redirect(url_for('user_dashboard'))

    cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    lang = session.get('lang', 'en')
    return render_template('edit_account_tl.html' if lang == 'tl' else 'edit_account.html', user=user)


@app.route('/user/dashboard', methods=['GET', 'POST'])
def user_dashboard():
    if 'user_id' not in session or session.get('role') != 'user':
        return redirect(url_for('login_page'))

    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cur.fetchone()

    if not user['birthdate'] or not user['civil_status'] or not user['address']:
        cur.close()
        conn.close()
        flash("Please complete your profile information.", "error")
        return redirect(url_for('edit_account'))

    if request.method == 'POST':
        doc_type = request.form.get('document_type', '').strip()
        full_name = request.form.get('full_name', '').strip()
        address_form = request.form.get('address', '').strip()
        contact = request.form.get('contact', '').strip()
        purpose = request.form.get('purpose', '').strip()

        if not (doc_type and full_name and address_form and contact and purpose):
            flash("All fields are required.", "error")
        else:
            cur.execute('''INSERT INTO requests (user_id, full_name, email, document_type, address, contact, purpose, status)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                        (user_id, full_name, session['email'], doc_type, address_form, contact, purpose, 'Pending'))
            conn.commit()
            flash("Request submitted successfully!", "success")

        cur.close()
        conn.close()
        return redirect(url_for('user_dashboard'))

    cur.execute('SELECT COUNT(*) AS total FROM requests WHERE user_id = %s', (user_id,))
    total = cur.fetchone()['total']
    cur.execute('SELECT COUNT(*) AS pending FROM requests WHERE user_id = %s AND status = "Pending"', (user_id,))
    pending = cur.fetchone()['pending']
    cur.execute('SELECT COUNT(*) AS completed FROM requests WHERE user_id = %s AND status = "Completed"', (user_id,))
    completed = cur.fetchone()['completed']

    cur.execute('SELECT id, document_type, status, created_at FROM requests WHERE user_id = %s ORDER BY created_at DESC', (user_id,))
    user_requests = cur.fetchall()

    cur.close()
    conn.close()

    lang = session.get('lang', 'en')
    return render_template('user_dashboard_tl.html' if lang == 'tl' else 'user_dashboard.html',
                           fullname=session.get('fullname'),
                           total=total, pending=pending, completed=completed,
                           user_contact=user['contact'] or '', user_requests=user_requests)


@app.route('/status')
def status_page():
    if 'user_id' not in session or session.get('role') != 'user':
        return redirect(url_for('login_page'))

    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, document_type, status FROM requests WHERE user_id = %s ORDER BY created_at DESC', (user_id,))
    requests_list = cur.fetchall()
    cur.close()
    conn.close()

    lang = session.get('lang', 'en')
    return render_template('status_tl.html' if lang == 'tl' else 'status.html', requests=requests_list)


@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login_page'))

    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    conn = get_db()
    cur = conn.cursor()

    user_info = None
    if request.method == 'POST' and 'view_user' in request.form:
        user_id_to_view = request.form['user_id']
        cur.execute('SELECT * FROM users WHERE id = %s', (user_id_to_view,))
        user_info = cur.fetchone()

    # Request list (for documents)
    if status_filter:
         cur.execute('''SELECT r.id, u.fullname, u.email, r.document_type, r.purpose, r.status, r.date_submitted
                   FROM requests r JOIN users u ON r.user_id = u.id
                   WHERE r.status = %s ORDER BY r.date_submitted DESC''', (status_filter,))
    else:
        cur.execute('''SELECT r.id, u.fullname, u.email, r.document_type, r.purpose, r.status, r.date_submitted
                    FROM requests r JOIN users u ON r.user_id = u.id ORDER BY r.date_submitted DESC''')

    requests_list = cur.fetchall()

    # Stats
    cur.execute('SELECT COUNT(*) AS cnt FROM users WHERE role = "user"')
    total_users = cur.fetchone()['cnt']
    cur.execute('SELECT COUNT(*) AS cnt FROM requests')
    total_requests = cur.fetchone()['cnt']

    # Fix: always define users_list regardless of search_query
    if search_query:
        cur.execute('''SELECT id, first_name, last_name, fullname, email 
                       FROM users
                       WHERE role = "user" 
                       AND (first_name LIKE %s OR last_name LIKE %s OR fullname LIKE %s)''',
                    (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
        users_list = cur.fetchall()
    else:
        cur.execute('SELECT id, first_name, last_name, fullname, email FROM users WHERE role = "user"')
        users_list = cur.fetchall()

    cur.close()
    conn.close()

    lang = session.get('lang', 'en')
    return render_template(
        'admin_dashboard_tl.html' if lang == 'tl' else 'admin_dashboard.html',
        requests=requests_list,
        total_users=total_users,
        total_requests=total_requests,
        users=users_list,
        user_info=user_info,
        search_query=search_query,
        status_filter=status_filter
    )

# -------------------------------
# ADMIN: View All Records
# -------------------------------
@app.route('/admin/all-records', methods=['GET', 'POST'])
def all_records():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login_page'))

    status_filter = request.args.get('status', '').strip()
    conn = get_db()
    cur = conn.cursor()

    if status_filter:
        cur.execute("SELECT * FROM all_records WHERE status = %s ORDER BY archived_at DESC", (status_filter,))
    else:
        cur.execute("SELECT * FROM all_records ORDER BY archived_at DESC")

    requests_list = cur.fetchall()
    cur.close()
    conn.close()

    lang = session.get('lang', 'en')
    return render_template(
        'all_records_tl.html' if lang == 'tl' else 'all_records.html',
        requests=requests_list
    )

@app.route('/admin/delete_selected_requests', methods=['POST'])
def delete_selected_requests():
    """Delete multiple selected requests permanently"""
    selected_ids = request.form.getlist('request_ids')

    if not selected_ids:
        flash("No requests selected for deletion.", "warning")
        return redirect(url_for('all_records'))

    conn = get_db()
    cur = conn.cursor()
    try:
        format_strings = ','.join(['%s'] * len(selected_ids))
        query = f"DELETE FROM requests WHERE id IN ({format_strings})"
        cur.execute(query, tuple(selected_ids))
        conn.commit()
        flash(f"Successfully deleted {len(selected_ids)} request(s).", "success")
    except Exception as e:
        flash(f"Error deleting requests: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('all_records'))

@app.route('/delete_selected_records', methods=['POST'])
def delete_selected_records():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login_page'))

    selected_ids = request.form.getlist('record_ids')

    if not selected_ids:
        flash('No records selected for deletion.', 'warning')
        return redirect(url_for('all_records'))

    conn = get_db()
    cur = conn.cursor()

    format_strings = ','.join(['%s'] * len(selected_ids))
    cur.execute(f"DELETE FROM all_records WHERE id IN ({format_strings})", tuple(selected_ids))
    conn.commit()

    cur.close()
    conn.close()
    flash('Selected records deleted successfully.', 'success')
    return redirect(url_for('all_records'))

@app.route('/update_status/<int:req_id>/<status>')
def update_status(req_id, status):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login_page'))

    valid_statuses = ['Pending', 'Processing', 'Verifying', 'Ready to be Claim', 'Completed', 'Rejected']
    if status not in valid_statuses:
        flash("Invalid status", "error")
        return redirect(url_for('admin_dashboard'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE requests SET status=%s WHERE id=%s', (status, req_id))
    conn.commit()
    cur.close()
    conn.close()

    flash(f"Request status updated to {status}!", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/delete_request/<int:req_id>')
def delete_request(req_id):
    conn = get_db()
    cur = conn.cursor()

    # Kunin muna ang request bago burahin
    cur.execute("SELECT * FROM requests WHERE id = %s", (req_id,))
    req = cur.fetchone()

    if req:
        # Insert muna sa all_records table (backup log)
        cur.execute("""
            INSERT INTO all_records (request_id, user_id, fullname, document_type, status, date_submitted, archived_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, (req['id'], req['user_id'], req['full_name'], req['document_type'], req['status'], req['date_submitted']))

        # Burahin sa main requests table
        cur.execute("DELETE FROM requests WHERE id = %s", (req_id,))
        conn.commit()
        flash("Request has been moved to All Records.", "success")
    else:
        flash("Request not found.", "warning")

    cur.close()
    conn.close()
    return redirect(url_for('admin_dashboard'))



@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login_page'))

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute('DELETE FROM users WHERE id = %s', (user_id,))
        conn.commit()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'danger')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('admin_dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
