from flask import Flask
from flask_login import LoginManager
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from backend.models import User
from backend.routes import auth_bp

# Setup Flask app
app = Flask(__name__)
app.secret_key = 'secret123'

# Configure SQLite database
engine = create_engine('sqlite:///parking_lot_app.db')
Session = sessionmaker(bind=engine)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # redirect to this route for @login_required

# Flask-Login: how to load user from user ID in session
@login_manager.user_loader
def load_user(user_id):
    session_db = Session()
    user = session_db.query(User).get(int(user_id))
    session_db.close()
    return user

# Register blueprint
app.register_blueprint(auth_bp)

# Run development server
if __name__ == '__main__':
    app.run(debug=True)
