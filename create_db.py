from sqlalchemy import create_engine
from backend.models import Base, User

# Create an SQLite database (can be switched to PostgreSQL/MySQL as needed)
engine = create_engine('sqlite:///parking_lot_app.db')

# Create all tables
Base.metadata.create_all(engine)

# Seed the admin user if not present
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()

# Check if admin exists
admin = session.query(User).filter_by(is_admin=True).first()
if not admin:
    admin_user = User(username='admin', password='adminpassword', is_admin=True)
    session.add(admin_user)
    session.commit()
    print("Admin user created.")

session.close()
