# create_db.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash
from backend.models import Base, User

DB_FILENAME = 'parking_lot_app.db'

if os.path.exists(DB_FILENAME):
    os.remove(DB_FILENAME)
    print("Old database removed.")

engine = create_engine(f'sqlite:///{DB_FILENAME}')
Base.metadata.create_all(engine)
print("Tables created successfully.")

Session = sessionmaker(bind=engine)
session = Session()

default_admin_username = 'admin@example.com'
default_admin_password = 'adminpass123'

existing_admin = session.query(User).filter_by(is_admin=True).first()

if not existing_admin:
    hashed_pw = generate_password_hash(default_admin_password)
    admin_user = User(
        username=default_admin_username,
        password=hashed_pw,
        full_name='Admin',
        is_admin=True
    )
    session.add(admin_user)
    session.commit()
    print(f"Admin user created: {default_admin_username} / {default_admin_password}")
else:
    print("Admin user already exists.")

session.close()
print("Database setup complete.")
