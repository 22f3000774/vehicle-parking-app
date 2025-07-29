from flask import Blueprint, render_template, request, redirect, flash, url_for, jsonify
from backend.models import ParkingLot, ParkingSpot, User, Reservation
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy import create_engine, func, desc
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
import re

# DB setup
engine = create_engine('sqlite:///parking_lot_app.db')
Session = sessionmaker(bind=engine)

# Blueprint
auth_bp = Blueprint('auth', __name__)

# Home route
@auth_bp.route('/')
def home():
    return redirect(url_for('auth.login'))

# ----------------- AUTH ------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session_db = Session()
        username = request.form['username']
        password = request.form['password']
        user = session_db.query(User).filter_by(username=username).first()
        session_db.close()

        if user and user.password == password:
            login_user(user)
            flash('Login successful.', 'success')
            return redirect(url_for('auth.admin_dashboard' if user.is_admin else 'auth.user_dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        full_name = request.form['full_name'].strip()
        password = request.form['password'].strip()

        if not username or not full_name or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('auth.register'))

        if not re.match(r'^[a-zA-Z0-9_]{3,}$', username):
            flash('Username should be valid (min 3 chars, letters/numbers/underscores).', 'danger')
            return redirect(url_for('auth.register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return redirect(url_for('auth.register'))

        session_db = Session()
        if session_db.query(User).filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            session_db.close()
            return redirect(url_for('auth.register'))

        new_user = User(username=username, full_name=full_name, password=password, is_admin=False)
        session_db.add(new_user)
        session_db.commit()
        session_db.close()

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

# ----------------- DASHBOARDS ------------------
@auth_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('admin_dashboard.html')

@auth_bp.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.is_admin:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('user_dashboard.html', full_name=current_user.full_name)

# ----------------- LOTS / SPOTS ------------------
@auth_bp.route('/admin/lots')
@login_required
def admin_lots():
    if not current_user.is_admin:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.login'))
    session_db = Session()
    lots = session_db.query(ParkingLot).all()
    session_db.close()
    return render_template('admin_lots.html', lots=lots)

@auth_bp.route('/admin/lots/create', methods=['GET', 'POST'])
@login_required
def admin_create_lot():
    if not current_user.is_admin:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        capacity = int(request.form['capacity'])
        amenities = request.form['amenities']
        pricing = int(request.form['pricing'])

        session_db = Session()
        lot = ParkingLot(name=name, location=location, capacity=capacity, amenities=amenities, pricing=pricing)
        session_db.add(lot)
        session_db.commit()

        for i in range(1, capacity + 1):
            spot = ParkingSpot(spot_number=str(i), spot_type='Regular', status='available', lot_id=lot.id)
            session_db.add(spot)

        session_db.commit()
        session_db.close()
        flash('Lot and spots created.', 'success')
        return redirect(url_for('auth.admin_lots'))

    return render_template('admin_create_lot.html')

@auth_bp.route('/admin/lots/edit/<int:lot_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_lot(lot_id):
    if not current_user.is_admin:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.login'))

    session_db = Session()
    lot = session_db.query(ParkingLot).get(lot_id)

    if request.method == 'POST':
        lot.name = request.form['name']
        lot.location = request.form['location']
        lot.capacity = int(request.form['capacity'])
        lot.amenities = request.form['amenities']
        lot.pricing = int(request.form['pricing'])
        session_db.commit()
        session_db.close()
        flash('Lot updated.', 'success')
        return redirect(url_for('auth.admin_lots'))

    session_db.close()
    return render_template('admin_edit_lot.html', lot=lot)

@auth_bp.route('/admin/lots/delete/<int:lot_id>', methods=['POST'])
@login_required
def admin_delete_lot(lot_id):
    if not current_user.is_admin:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.login'))

    session_db = Session()
    lot = session_db.query(ParkingLot).get(lot_id)
    spots = session_db.query(ParkingSpot).filter_by(lot_id=lot_id).all()

    # Check if all spots are available (i.e., no spot is reserved or occupied)
    not_available_spots = [spot for spot in spots if spot.status != 'available']
    if not_available_spots:
        session_db.close()
        flash(
            "Cannot delete the lot: Some parking spots are not available (reserved/occupied). "
            "Please ensure all spots are released before deleting.",
            "danger"
        )
        return redirect(url_for('auth.admin_lots'))

    # All spots are available, safe to delete
    session_db.query(ParkingSpot).filter_by(lot_id=lot.id).delete()
    session_db.delete(lot)
    session_db.commit()
    session_db.close()
    flash('Lot deleted.', 'info')
    return redirect(url_for('auth.admin_lots'))

@auth_bp.route('/admin/lots/<int:lot_id>')
@login_required
def admin_lot_details(lot_id):
    if not current_user.is_admin:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.login'))

    session_db = Session()
    lot = session_db.query(ParkingLot).get(lot_id)
    spots = session_db.query(ParkingSpot).filter_by(lot_id=lot_id).all()
    session_db.close()
    return render_template('admin_lot_details.html', lot=lot, spots=spots)

@auth_bp.route('/lots')
@login_required
def user_view_lots():
    if current_user.is_admin:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.login'))

    session_db = Session()
    lots = session_db.query(ParkingLot).all()
    session_db.close()
    return render_template('user_lots.html', lots=lots)

@auth_bp.route('/reserve/<int:lot_id>', methods=['POST'])
@login_required
def reserve_spot(lot_id):
    if current_user.is_admin:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.login'))

    session_db = Session()
    spot = session_db.query(ParkingSpot).filter_by(lot_id=lot_id, status='available').first()

    if spot:
        spot.status = 'reserved'
        reservation = Reservation(
            user_id=current_user.id,
            spot_id=spot.id,
            start_time=datetime.now(),
            status='active'
        )
        session_db.add(reservation)
        session_db.commit()

        # Extract details before closing session
        spot_number = spot.spot_number
        lot_name = spot.lot.name
        session_db.close()

        flash(f'Success! Spot {spot_number} in Lot {lot_name} has been reserved.', 'success')
    else:
        session_db.close()
        flash('No available spots.', 'warning')

    return redirect(url_for('auth.user_view_lots'))

# ----------------- RESERVATIONS / HISTORY ------------------
@auth_bp.route('/reservations/history')
@login_required
def reservation_history():
    if current_user.is_admin:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.login'))

    session_db = Session()
    reservations = (
        session_db.query(Reservation)
        .options(
            joinedload(Reservation.user),
            joinedload(Reservation.spot).joinedload(ParkingSpot.lot)
        )
        .filter_by(user_id=current_user.id)
        .order_by(Reservation.start_time.desc())
        .all()
    )
    session_db.close()
    return render_template('reservation_history.html', reservations=reservations)

@auth_bp.route('/release/<int:reservation_id>', methods=['POST'])
@login_required
def release_spot(reservation_id):
    if current_user.is_admin:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.login'))

    session_db = Session()
    reservation = (
        session_db.query(Reservation)
        .filter_by(id=reservation_id, user_id=current_user.id)
        .join(Reservation.spot)
        .join(ParkingSpot.lot)
        .first()
    )

    if reservation and reservation.status in ('active', 'occupied'):
        reservation.spot.status = 'available'
        reservation.status = 'completed'
        reservation.end_time = datetime.now()

        duration = (reservation.end_time - reservation.start_time).total_seconds() / 3600
        rate = reservation.spot.lot.pricing or 10
        reservation.cost = int(duration * rate)

        session_db.commit()
        flash(f'Spot released. Total cost: ₹{reservation.cost}', 'success')
    else:
        flash("Error releasing reservation.", 'danger')

    session_db.close()
    return redirect(url_for('auth.reservation_history'))

# ----------------- ADMIN USERS ------------------
@auth_bp.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.login'))

    session_db = Session()
    users = session_db.query(User).filter(User.is_admin == False).all()
    session_db.close()
    return render_template('admin_users.html', users=users)

# ----------------- ADMIN PARKING RECORDS ------------------
@auth_bp.route('/admin/parking_records')
@login_required
def admin_parking_records():
    if not current_user.is_admin:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.login'))

    session_db = Session()
    reservations = (
        session_db.query(Reservation)
        .options(
            joinedload(Reservation.user),
            joinedload(Reservation.spot).joinedload(ParkingSpot.lot)
        )
        .order_by(Reservation.start_time.desc())
        .all()
    )
    session_db.close()
    return render_template('admin_parking_records.html', reservations=reservations)

# ----------------- ADMIN SEARCH ------------------
@auth_bp.route('/admin/search', methods=['GET', 'POST'])
@login_required
def admin_search():
    if not current_user.is_admin:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.login'))

    results = []
    query = ''
    search_type = ''

    if request.method == 'POST':
        query = request.form['query'].strip()
        search_type = request.form['search_type']
        session_db = Session()

        if search_type == 'user':
            results = session_db.query(User).filter(User.username.ilike(f'%{query}%')).all()
        elif search_type == 'spot':
            results = session_db.query(ParkingSpot).filter(ParkingSpot.spot_number.ilike(f'%{query}%')).all()
        elif search_type == 'vacancy':
            results = session_db.query(ParkingSpot).filter(ParkingSpot.status.ilike(f'%{query}%')).all()

        session_db.close()

    return render_template('admin_search.html', results=results, query=query, search_type=search_type)

# ----------------- ADMIN PARKING STATS with revenue ------------------
@auth_bp.route('/admin/parking_stats')
@login_required
def admin_parking_stats():
    if not current_user.is_admin:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.login'))

    session_db = Session()
    data = (
        session_db.query(
            User.full_name,
            func.count(Reservation.id).label('reservations_count'),
            func.coalesce(func.sum(Reservation.cost), 0).label('revenue')
        )
        .join(Reservation, Reservation.user_id == User.id)
        .group_by(User.id)
        .all()
    )
    session_db.close()

    labels = [row.full_name for row in data]
    counts = [row.reservations_count for row in data]
    revenue_labels = labels
    revenue_counts = [float(row.revenue) for row in data]

    return render_template(
        'admin_parking_stats.html',
        labels=labels,
        counts=counts,
        revenue_labels=revenue_labels,
        revenue_counts=revenue_counts
    )

# ----------------- API ROUTES ------------------
@auth_bp.route('/api/lots', methods=['GET'])
@login_required
def api_lots():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    session_db = Session()
    lots = session_db.query(ParkingLot).all()
    session_db.close()
    # Return a JSON representation of lots (customize as needed)
    lots_json = [{
        'id': lot.id,
        'name': lot.name,
        'location': lot.location,
        'capacity': lot.capacity,
        'amenities': lot.amenities,
        'pricing': lot.pricing
    } for lot in lots]
    return jsonify(lots_json)
