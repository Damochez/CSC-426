from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime, timedelta
import secrets
import re

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

DB_NAME = 'auth.db'

def init_db():
    """Initialize database with tables"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            last_login TIMESTAMP
        )
    ''')
    
    # Audit logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            ip_address TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    
    create_demo_user()

def create_demo_user():
    """Create demo user for testing"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        c.execute('SELECT * FROM users WHERE username = ?', ('demo@test.com',))
        if not c.fetchone():
            hashed_password = generate_password_hash('Demo@1234')
            c.execute('''
                INSERT INTO users (username, email, password, first_name, last_name)
                VALUES (?, ?, ?, ?, ?)
            ''', ('demo@test.com', 'demo@test.com', hashed_password, 'Demo', 'User'))
            conn.commit()
            print("✓ Demo user created: demo@test.com / Demo@1234")
        
        conn.close()
    except Exception as e:
        print(f"Error creating demo user: {e}")

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def log_audit(user_id, action, details=""):
    """Log audit event"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        ip_address = request.remote_addr
        
        c.execute('''
            INSERT INTO audit_logs (user_id, action, ip_address, details)
            VALUES (?, ?, ?, ?)
        ''', (user_id, action, ip_address, details))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Audit log error: {e}")

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(pattern, email) is not None

def is_valid_username(username):
    """Validate username format"""
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None

def is_valid_password(password):
    """Validate password strength"""
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    return re.match(pattern, password) is not None

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Login page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    """Signup page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    
    if not user:
        session.clear()
        return redirect(url_for('index'))
    
    return render_template('dashboard.html', user=dict(user))

@app.route('/forgot-password')
def forgot_password_page():
    """Forgot password page"""
    return render_template('forgot-password.html')

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Login API endpoint"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        remember_me = data.get('rememberMe', False)
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password are required'}), 400
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE (username = ? OR email = ?) AND is_active = 1',
            (username, username)
        ).fetchone()
        conn.close()
        
        if not user:
            log_audit(None, 'LOGIN_FAILED', f'User not found: {username}')
            return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
        
        if not check_password_hash(user['password'], password):
            log_audit(user['id'], 'LOGIN_FAILED', 'Invalid password')
            return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
        
        conn = get_db_connection()
        conn.execute(
            'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
            (user['id'],)
        )
        conn.commit()
        conn.close()
        
        session.permanent = remember_me
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['email'] = user['email']
        
        log_audit(user['id'], 'LOGIN_SUCCESS', 'Successful login')
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'firstName': user['first_name'],
                'lastName': user['last_name']
            }
        }), 200
    
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred during login'}), 500

@app.route('/api/auth/signup', methods=['POST'])
def api_signup():
    """Signup API endpoint"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirmPassword', '')
        first_name = data.get('firstName', '').strip()
        last_name = data.get('lastName', '').strip()
        
        if not all([username, email, password, confirm_password]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        if not is_valid_username(username):
            return jsonify({
                'success': False,
                'message': 'Username must be 3-20 characters (alphanumeric and underscore)'
            }), 400
        
        if not is_valid_email(email):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
        
        if password != confirm_password:
            return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
        
        if not is_valid_password(password):
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters with uppercase, lowercase, number, and special character (@$!%*?&)'
            }), 400
        
        conn = get_db_connection()
        existing_user = conn.execute(
            'SELECT id FROM users WHERE username = ? OR email = ?',
            (username, email)
        ).fetchone()
        
        if existing_user:
            conn.close()
            log_audit(None, 'SIGNUP_FAILED', f'User already exists: {username}')
            return jsonify({'success': False, 'message': 'Username or email already exists'}), 400
        
        hashed_password = generate_password_hash(password)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, email, password, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, email, hashed_password, first_name, last_name))
        conn.commit()
        
        new_user_id = cursor.lastrowid
        conn.close()
        
        log_audit(new_user_id, 'SIGNUP_SUCCESS', 'New account created')
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully. Please login.'
        }), 201
    
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred during signup'}), 500

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """Logout API endpoint"""
    try:
        user_id = session.get('user_id')
        if user_id:
            log_audit(user_id, 'LOGOUT', 'User logged out')
        
        session.clear()
        return jsonify({'success': True, 'message': 'Logged out successfully'}), 200
    except Exception as e:
        print(f"Logout error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred during logout'}), 500

@app.route('/api/auth/profile', methods=['GET'])
def api_profile():
    """Get user profile"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT id, username, email, first_name, last_name, created_at, last_login FROM users WHERE id = ? AND is_active = 1',
            (session['user_id'],)
        ).fetchone()
        conn.close()
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'firstName': user['first_name'],
                'lastName': user['last_name'],
                'createdAt': user['created_at'],
                'lastLogin': user['last_login']
            }
        }), 200
    except Exception as e:
        print(f"Profile error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500

@app.route('/api/auth/change-password', methods=['POST'])
def api_change_password():
    """Change password API endpoint"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        data = request.get_json()
        current_password = data.get('currentPassword', '')
        new_password = data.get('newPassword', '')
        confirm_password = data.get('confirmPassword', '')
        
        if not all([current_password, new_password, confirm_password]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
        
        if not is_valid_password(new_password):
            return jsonify({
                'success': False,
                'message': 'New password must be at least 8 characters with uppercase, lowercase, number, and special character'
            }), 400
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT password FROM users WHERE id = ?',
            (session['user_id'],)
        ).fetchone()
        
        if not user:
            conn.close()
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        if not check_password_hash(user['password'], current_password):
            conn.close()
            log_audit(session['user_id'], 'CHANGE_PASSWORD_FAILED', 'Invalid current password')
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401
        
        hashed_password = generate_password_hash(new_password)
        conn.execute(
            'UPDATE users SET password = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (hashed_password, session['user_id'])
        )
        conn.commit()
        conn.close()
        
        log_audit(session['user_id'], 'CHANGE_PASSWORD_SUCCESS', 'Password changed')
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200
    
    except Exception as e:
        print(f"Change password error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Page not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    init_db()
    
    print("\n╔════════════════════════════════════════╗")
    print("║   🚀 Web Login Application Started    ║")
    print("║   Server: http://localhost:5000       ║")
    print("║   Demo: demo@test.com / Demo@1234     ║")
    print("╚════════════════════════════════════════╝\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
