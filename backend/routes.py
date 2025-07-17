from flask import Blueprint, render_template, request, redirect, flash, url_for, session
from backend.models import ParkingLot, ParkingSpot, User
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import desc
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


engine = create_engine('sqlite:///parking_lot_app.db')
Session = sessionmaker(bind=engine)
auth_bp = Blueprint('auth', __name__)

# Home route: redirect root to login for convenience
@auth_bp.route('/')
def home():
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        session_db = Session()
        username = request.form['username']
        full_name = request.form['full_name']
        password = generate_password_hash(request.form['password'])

        if session_db.query(User).filter_by(username=username).first():
            flash('Username already exists.')
            session_db.close()
            return redirect(url_for('auth.register'))

        new_user = User(username=username, full_name=full_name, password=password, is_admin=False)
        session_db.add(new_user)
        session_db.commit()
        session_db.close()
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
        session_db.close()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            flash('Login successful.', 'success')
            if user.is_admin:
                return redirect(url_for('auth.admin_dashboard'))
            else:
                return redirect(url_for('auth.user_dashboard'))
        flash('Invalid credentials.')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('auth.login'))

@auth_bp.route('/user/dashboard')
def user_dashboard():
    if not session.get('user_id') or session.get('is_admin'):
        flash('Unauthorized access.')
        return redirect(url_for('auth.login'))   # Make sure this line has a return!
    return render_template("user_dashboard.html")  # Also return in the main case


# View all parking lots
@auth_bp.route('/admin/lots')
def admin_lots():
    if not session.get('user_id') or not session.get('is_admin'):
        flash('Unauthorized access.')
        return redirect(url_for('auth.login'))
    session_db = Session()
    lots = session_db.query(ParkingLot).all()
    session_db.close()
    return render_template('admin_lots.html', lots=lots)

# Create a new lot
@auth_bp.route('/admin/lots/create', methods=['GET', 'POST'])
def admin_create_lot():
    if not session.get('user_id') or not session.get('is_admin'):
        flash('Unauthorized access.')
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        capacity = int(request.form['capacity'])
        amenities = request.form['amenities']
        pricing = request.form['pricing']
        session_db = Session()
        lot = ParkingLot(name=name, location=location, capacity=capacity, amenities=amenities, pricing=pricing)
        session_db.add(lot)
        session_db.commit()
        # Automatically add spots up to lot capacity
        for i in range(1, capacity + 1):
            spot = ParkingSpot(spot_number=str(i), spot_type='Regular', status='available', lot_id=lot.id)
            session_db.add(spot)
        session_db.commit()
        session_db.close()
        flash('Parking lot and spots created.')
        return redirect(url_for('auth.admin_lots'))
    return render_template('admin_create_lot.html')

# Edit lot
@auth_bp.route('/admin/lots/edit/<int:lot_id>', methods=['GET', 'POST'])
def admin_edit_lot(lot_id):
    if not session.get('user_id') or not session.get('is_admin'):
        flash('Unauthorized access.')
        return redirect(url_for('auth.login'))
    session_db = Session()
    lot = session_db.query(ParkingLot).get(lot_id)
    if request.method == 'POST':
        lot.name = request.form['name']
        lot.location = request.form['location']
        lot.capacity = int(request.form['capacity'])
        lot.amenities = request.form['amenities']
        lot.pricing = request.form['pricing']
        session_db.commit()
        session_db.close()
        flash('Parking lot updated.')
        return redirect(url_for('auth.admin_lots'))
    session_db.close()
    return render_template('admin_edit_lot.html', lot=lot)

# Delete lot
@auth_bp.route('/admin/lots/delete/<int:lot_id>', methods=['POST'])
def admin_delete_lot(lot_id):
    if not session.get('user_id') or not session.get('is_admin'):
        flash('Unauthorized access.')
        return redirect(url_for('auth.login'))
    session_db = Session()
    lot = session_db.query(ParkingLot).get(lot_id)
    # Delete all spots in this lot
    session_db.query(ParkingSpot).filter_by(lot_id=lot.id).delete()
    session_db.delete(lot)
    session_db.commit()
    session_db.close()
    flash('Lot and its spots deleted.')
    return redirect(url_for('auth.admin_lots'))

# View lot details and spots
@auth_bp.route('/admin/lots/<int:lot_id>')
def admin_lot_details(lot_id):
    if not session.get('user_id') or not session.get('is_admin'):
        flash('Unauthorized access.')
        return redirect(url_for('auth.login'))
    session_db = Session()
    lot = session_db.query(ParkingLot).get(lot_id)
    spots = session_db.query(ParkingSpot).filter_by(lot_id=lot_id).all()
    session_db.close()
    return render_template('admin_lot_details.html', lot=lot, spots=spots)

@auth_bp.route('/admin/users')
def admin_users():
    if not session.get('user_id') or not session.get('is_admin'):
        flash('Unauthorized access.')
        return redirect(url_for('auth.login'))
    session_db = Session()
    users = session_db.query(User).filter(User.is_admin == False).all()
    session_db.close()
    return render_template('admin_users.html', users=users)

# Show all reservations for the current user
@auth_bp.route('/reservations/history')
def reservation_history():
    if 'user_id' not in session or session.get('is_admin'):
        flash('Unauthorized access.')
        return redirect(url_for('auth.login'))
    session_db = Session()
    reservations = session_db.query(Reservation).filter_by(user_id=session['user_id']).order_by(Reservation.start_time.desc()).all()
    session_db.close()
    return render_template('reservation_history.html', reservations=reservations)

# Admin view: All parking/reservation records
@auth_bp.route('/admin/parking_records')
def admin_parking_records():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access.')
        return redirect(url_for('auth.login'))
    session_db = Session()
    reservations = session_db.query(Reservation).order_by(Reservation.start_time.desc()).all()
    session_db.close()
    return render_template('admin_parking_records.html', reservations=reservations)

@auth_bp.route('/release/<int:reservation_id>', methods=['POST'])
def release_spot(reservation_id):
    if not session.get('user_id') or session.get('is_admin'):
        flash('Unauthorized access.')
        return redirect(url_for('auth.login'))
    session_db = Session()
    reservation = session_db.query(Reservation).get(reservation_id)
    if reservation and reservation.status in ('active', 'occupied'):
        reservation.spot.status = 'available'
        reservation.status = 'completed'
        reservation.end_time = datetime.now()
        # Calculate cost
        lot = reservation.spot.lot
        duration = (reservation.end_time - reservation.start_time).total_seconds() / 3600  # hours
        price_per_hour = lot.pricing if lot.pricing else 10  # default to 10 if missing
        reservation.cost = int(duration * price_per_hour)
        session_db.commit()
        flash(f'Spot released. Total cost: ₹{reservation.cost}')
    session_db.close()
    return redirect(url_for('auth.user_reservations'))
