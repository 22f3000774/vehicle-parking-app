# create_db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

# ✅ Import your SQLAlchemy Base and User model
from backend.models import Base, User

# ✅ Step 1: Create SQLite engine — change URL if using PostgreSQL/MySQL
engine = create_engine('sqlite:///parking_lot_app.db')

# ✅ Step 2: Create all tables
Base.metadata.create_all(engine)

# ✅ Step 3: Setup session
Session = sessionmaker(bind=engine)
session = Session()

# ✅ Step 4: Create default admin user if not already present
existing_admin = session.query(User).filter_by(is_admin=True).first()

if not existing_admin:
    admin_user = User(
        username='admin@example.com',
        password=generate_password_hash('adminpass123'),
        full_name='Admin',
        is_admin=True
    )
    session.add(admin_user)
    session.commit()
    print("✅ Admin user created: admin@example.com / adminpass123")
else:
    print("ℹ️ Admin user already exists.")

# ✅ Step 5: Close session
session.close()
