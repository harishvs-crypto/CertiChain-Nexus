from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import check_password_hash
from models.schema import db, User, Issuer

auth_bp = Blueprint('auth', __name__)

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return db.session.get(User, user_id)
    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user or user.role not in roles:
                flash("Access denied. Insufficient permissions.", "danger")
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_role'] = user.role
            session['user_name'] = user.full_name
            
            flash(f"Welcome back, {user.full_name}!", "success")
            if user.role == 'ADMIN':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'ISSUER':
                return redirect(url_for('certificate.issuer_dashboard'))
            elif user.role == 'STUDENT':
                return redirect(url_for('certificate.student_portal'))
            return redirect(url_for('verify.landing'))
        
        flash("Invalid email or password.", "danger")
        
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('verify.landing'))
