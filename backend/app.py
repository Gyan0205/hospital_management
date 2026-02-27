from flask import Flask, send_from_directory
from flask_cors import CORS
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.doctor_routes import doctor_bp
from routes.patient_routes import patient_bp

app = Flask(__name__, static_folder='../frontend', static_url_path='/')
CORS(app)

# ----------------- FRONTEND ROUTES -----------------

@app.route('/')
def root():
    return send_from_directory('../frontend', 'login.html')

@app.route('/<path:filename>')
def serve_frontend(filename):
    return send_from_directory('../frontend', filename)

# ----------------- API ROUTES -----------------

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(doctor_bp, url_prefix='/api/doctor')
app.register_blueprint(patient_bp, url_prefix='/api/patient')

if __name__ == '__main__':
    app.run(debug=True)
