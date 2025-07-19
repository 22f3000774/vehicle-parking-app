from flask import Blueprint, render_template, request, redirect, flash, url_for, session
from backend.models import ParkingLot, ParkingSpot, User, Reservation
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import desc
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.orm import joinedload
from flask import jsonify
from sqlalchemy import func




engine = create_engine('sqlite:///parking_lot_app.db')
Session = sessionmaker(bind=engine)
auth_bp = Blueprint('auth', __name__)

# Home route: redirect root to login for convenience
@auth_bp.route('/')
def home():
    return redirect(url_for('auth.login'))

@auth_bp.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('user_id') or not session.get('is_admin'):
        flash('Unauthorized access.')
        return redirect(url_for('auth.login'))
    return render_template("admin_dashboard.html")

@auth_bp.route('/admin/parking_records')
def admin_parking_records():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access.')
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
        return redirect(url_for('auth.login'))
    session_db = Session()
    user = session_db.query(User).get(session['user_id'])
    session_db.close()
    return render_template("user_dashboard.html", full_name=user.full_name)



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
        pricing = int(request.form['pricing'])
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

@auth_bp.route('/lots')
def user_view_lots():
    if not session.get('user_id') or session.get('is_admin'):
        flash('Unauthorized access.')
        return redirect(url_for('auth.login'))
    session_db = Session()
    lots = session_db.query(ParkingLot).all()
    session_db.close()
    return render_template('user_lots.html', lots=lots)

@auth_bp.route('/reserve/<int:lot_id>', methods=['POST'])
def reserve_spot(lot_id):
    if not session.get('user_id') or session.get('is_admin'):
        flash('Unauthorized access.')
        return redirect(url_for('auth.login'))

    session_db = Session()

    # Find first available spot in the selected lot
    spot = session_db.query(ParkingSpot).filter_by(lot_id=lot_id, status='available').first()

    if spot:
        # Mark spot as reserved
        spot.status = 'reserved'

        # Create reservation record
        reservation = Reservation(
            user_id=session['user_id'],
            spot_id=spot.id,
            start_time=datetime.now(),
            status='active'
        )

        session_db.add(reservation)
        session_db.commit()

        # 👇 Store info BEFORE closing session
        spot_number = spot.spot_number
        lot_name = spot.lot.name

        session_db.close()

        flash(f'Success! Spot {spot_number} in Lot {lot_name} has been reserved.')
    else:
        session_db.close()
        flash('Sorry, no available spots in this lot.')

    return redirect(url_for('auth.user_view_lots'))


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
        lot.pricing = int(request.form['pricing'])
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
from sqlalchemy.orm import joinedload

@auth_bp.route('/reservations/history')
def reservation_history():
    if 'user_id' not in session or session.get('is_admin'):
        flash('Unauthorized access.')
        return redirect(url_for('auth.login'))
    session_db = Session()
    reservations = (
        session_db.query(Reservation)
        .options(
            joinedload(Reservation.user),
            joinedload(Reservation.spot).joinedload(ParkingSpot.lot)
        )
        .filter_by(user_id=session['user_id'])
        .order_by(Reservation.start_time.desc())
        .all()
    )
    session_db.close()
    return render_template('reservation_history.html', reservations=reservations)


# Admin view: All parking/reservation records



@auth_bp.route('/release/<int:reservation_id>', methods=['POST'])
def release_spot(reservation_id):
    if not session.get('user_id') or session.get('is_admin'):
        flash('Unauthorized access.')
        return redirect(url_for('auth.login'))

    session_db = Session()
    # Load the reservation with the spot and lot eagerly
    reservation = (
        session_db.query(Reservation)
        .filter_by(id=reservation_id, user_id=session['user_id'])
        .join(Reservation.spot)
        .join(ParkingSpot.lot)
        .first()
    )

    if reservation and reservation.status in ('active', 'occupied'):
        reservation.spot.status = 'available'
        reservation.status = 'completed'
        reservation.end_time = datetime.now()

        # Cost calculation example: price per hour
        lot = reservation.spot.lot
        duration_hours = (reservation.end_time - reservation.start_time).total_seconds() / 3600
        price_per_hour = getattr(lot, 'pricing', 10) or 10  # Fallback 10 if not set
        reservation.cost = int(duration_hours * price_per_hour)

        session_db.commit()
        flash(f'Spot released. Total cost: ₹{reservation.cost}')
    else:
        flash('Could not release this reservation.')

    session_db.close()
    return redirect(url_for('auth.reservation_history'))

@auth_bp.route('/admin/search', methods=['GET', 'POST'])
def admin_search():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access.')
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
            results = session_db.query(ParkingSpot).filter(ParkingSpot.status == query).all() # e.g. 'available' or 'occupied'
        session_db.close()

    return render_template('admin_search.html', results=results, query=query, search_type=search_type)


# Get all lots
@auth_bp.route('/api/lots', methods=['GET'])
def api_lots():
    session_db = Session()
    lots = session_db.query(ParkingLot).all()
    session_db.close()
    return jsonify([{
        'id': lot.id,
        'name': lot.name,
        'location': lot.location,
        'capacity': lot.capacity,
        'pricing': lot.pricing
    } for lot in lots])

# Get all spots
@auth_bp.route('/api/spots', methods=['GET'])
def api_spots():
    session_db = Session()
    spots = session_db.query(ParkingSpot).all()
    session_db.close()
    return jsonify([{
        'id': spot.id,
        'lot_id': spot.lot_id,
        'spot_number': spot.spot_number,
        'status': spot.status
    } for spot in spots])

# Get all reservations
@auth_bp.route('/api/reservations', methods=['GET'])
def api_reservations():
    session_db = Session()
    reservations = session_db.query(Reservation).all()
    session_db.close()
    return jsonify([{
        'id': r.id,
        'user_id': r.user_id,
        'spot_id': r.spot_id,
        'start_time': r.start_time.isoformat() if r.start_time else None,
        'end_time': r.end_time.isoformat() if r.end_time else None,
        'cost': r.cost,
        'status': r.status
    } for r in reservations])

@auth_bp.route('/admin/parking_stats')
def admin_parking_stats():
    if not session.get('user_id') or not session.get('is_admin'):
        flash('Unauthorized access.')
        return redirect(url_for('auth.login'))
    session_db = Session()
    # Example: Count reservations per user
    data = (
        session_db.query(User.full_name, func.count(Reservation.id))
        .join(Reservation, Reservation.user_id == User.id)
        .group_by(User.full_name)
        .all()
    )
    session_db.close()
    labels = [d[0] for d in data]
    counts = [d[1] for d in data]
    return render_template('admin_parking_stats.html', labels=labels, counts=counts)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        full_name = request.form['full_name'].strip()
        password = request.form['password'].strip()
        
        if not username or not full_name or not password:
            flash('All fields are required.')
            return redirect(url_for('auth.register'))
        
        if not re.match(r'^[a-zA-Z0-9_]{3,}$', username):
            flash('Username should be at least 3 characters and contain only letters, numbers, or underscores.')
            return redirect(url_for('auth.register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long.')
            return redirect(url_for('auth.register'))

        session_db = Session()
        existing_user = session_db.query(User).filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.')
            session_db.close()
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            full_name=full_name,
            password=hashed_password,
            is_admin=False  
        )

        session_db.add(new_user)
        session_db.commit()
        session_db.close()

        flash('Registration successful! You can now log in.')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

