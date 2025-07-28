# Vehicle Parking Management System

This is a web-based Vehicle Parking Management System developed as a project. It allows admin users to manage parking lots, spots, users, reservations, and view analytics, while regular users can reserve and manage parking spots.

## Features

- User registration and login with role-based access (admin vs user).
- Admin dashboard: manage parking lots, users, reservations, and view visual reports.
- Automated creation of parking spots based on lot capacity.
- Spot reservation and release with real-time status updates.
- Reservation history and cost calculation.
- Interactive charts for reservations and revenues using Chart.js.
- Responsive UI styled with Bootstrap 5.
- REST API endpoint(s) for parking lot information (admin only).


## Prerequisites

- Python 3.7+ installed on your system.
- Optional but recommended: virtual environment for Python dependencies.
- SQLite (comes bundled with Python standard library).


## Setup & Installation

1. **Clone the repository** (or download the project folder):
git clone <repository-url>
cd vehicle-parking-app

2. **Create and activate a virtual environment** (optional but recommended):
python3 -m venv venv
source venv/bin/activate # Linux/Mac
venv\Scripts\activate # Windows

3. **Install Python dependencies:**
pip install -r requirements.txt

4. **Initialize the database:**

Run the database creation script to create database tables and an initial admin user:
python create_db.py

This will create `parking_lot_app.db` SQLite database and a default admin user:

- Username: `admin@example.com`
- Password: `adminpass123`

5. **Run the Flask app:**

Start the Flask development server by running:
python app.py

By default, the app runs on [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Usage

- Open your browser and go to [http://127.0.0.1:5000](http://127.0.0.1:5000)
- Log in using the default admin credentials or register a new user.
- Admin users will be directed to the Admin Dashboard with options to manage lots, users, reservations, and view analytics.
- Regular users will see a simplified dashboard with options to view available lots and manage their reservations.

## Code Structure

- `app.py`: Main Flask application setup and blueprint registration.
- `create_db.py`: Script to initialize the SQLite database and create default admin.
- `backend/`
- `models.py`: SQLAlchemy ORM models defining database schema.
- `routes.py`: Flask routes for all app functionality with authentication and authorization logic.
- `templates/`: Jinja2 HTML templates styled with Bootstrap.
- `static/`: Static assets (CSS, JavaScript including Chart.js).
- `requirements.txt`: List of Python packages required.

## Additional Notes

- Database used is SQLite for easy local development; can be extended to other DBs.
- The API endpoint `/api/lots` is available (admin only) for fetching parking lot data in JSON format.
- For charts, Chart.js with plugins is used to provide interactive visualizations.
- All admin routes are protected, and user roles are enforced.


## Troubleshooting

- If you face issues with missing packages, ensure your virtual environment is activated and all requirements are installed.
- For database errors, try deleting the existing `parking_lot_app.db` file and re-running `create_db.py`.
- The default admin login credentials are printed when you run `create_db.py`.
- Flask debug mode is enabled by default in `app.py`; useful during development.


## Future Improvements

- Add password reset functionality.
- Use environment variables for secret keys and sensitive settings.
- Extend API with more endpoints (spots, reservations).
- Implement email notifications.
- Add JWT token-based API authentication.


## Contact

For any queries or issues, please contact:  
Aditya Raj Sahu  
Email: 22f3000774@ds.study.iitm.ac.in


**This project is developed for academic purposes only.**





