from flask import Blueprint, render_template, request, redirect, flash, url_for, session
from backend.models import User
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from werkzeug.security import generate_password_hash, check_password_hash

engine = create_engine('sqlite:///parking_lot_app.db')
Session = sessionmaker(bind=engine)
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        session_db = Session()
        username = request.form['username']
        full_name = request.form['full_name']
        password = generate_password_hash(request.form['password'])

        if session_db.query(User).filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('auth.register'))

        new_user = User(username=username, full_name=full_name, password=password, is_admin=False)
        session_db.add(new_user)
        session_db.commit()
        flash('Registration successful.')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session_db = Session()
        username = request.form['username']
        password = request.form['password']

        user = session_db.query(User).filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            flash('Login successful.')
            if user.is_admin:
                return redirect(url_for('dashboard.admin_dashboard'))
            else:
                return redirect(url_for('dashboard.user_dashboard'))
        flash('Invalid credentials.')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('auth.login'))
@auth_bp.route('/user/dashboard')
def user_dashboard():
    # Ensure only users see this
    return render_template("user_dashboard.html")

@auth_bp.route('/admin/dashboard')
def admin_dashboard():
    return render_template("admin_dashboard.html")
