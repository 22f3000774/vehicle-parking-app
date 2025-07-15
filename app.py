from flask import Flask
from backend.routes import auth_bp

app = Flask(__name__)
app.secret_key = 'secret123'  # Required for sessions

app.register_blueprint(auth_bp)
from backend.models import User, ParkingLot, ParkingSpot, Reservation

def create_app():
    app=Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"]  = "sqlite:///Vehicle_db.sqilite3"
    return app

app = create_app()

from backend.routes import *

if __name__=="__main__":
    app.run(debug=True)
