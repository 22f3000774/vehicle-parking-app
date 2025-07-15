from flask import Flask
from backend.routes import auth_bp

app = Flask(__name__)
app.secret_key = 'secret123'  # Required for sessions

app.register_blueprint(auth_bp)

if __name__ == "__main__":
    app.run(debug=True)
