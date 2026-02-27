from flask import Blueprint, request, jsonify
import sqlite3
import os

auth_bp = Blueprint('auth', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'hospital.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM User WHERE Username = ? AND Password = ?',
        (username, password)
    ).fetchone()

    if not user:
        conn.close()
        return jsonify({'error': 'Invalid credentials'}), 401

    role = user['Role']
    reference_id = user['ReferenceID']
    name = 'Admin'  # Default for admin role

    # === Blacklist checks and name retrieval ===
    if role == 'Doctor':
        doctor = conn.execute('SELECT IsBlacklisted, Name FROM Doctor WHERE DoctorID = ?', (reference_id,)).fetchone()
        if doctor and doctor['IsBlacklisted'] == 1:
            conn.close()
            return jsonify({'error': 'Doctor account is blacklisted. Contact admin.'}), 403
        if doctor:
            name = doctor['Name']

    elif role == 'Patient':
        patient = conn.execute('SELECT IsBlacklisted, Name FROM Patient WHERE PatientID = ?', (reference_id,)).fetchone()
        if patient and patient['IsBlacklisted'] == 1:
            conn.close()
            return jsonify({'error': 'Patient account is blacklisted. Contact admin.'}), 403
        if patient:
            name = patient['Name']

    conn.close()

    return jsonify({
        'message': 'Login successful',
        'role': role,
        'user_id': user['UserID'],
        'reference_id': reference_id,
        'name': name
    }), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    age = data.get('age')
    gender = data.get('gender')
    contact = data.get('contact')
    address = data.get('address')

    # Registration is only for patients
    if not all([username, password, name, age, gender]):
        return jsonify({'error': 'Missing required fields'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Create Patient entry first
        cursor.execute('''
            INSERT INTO Patient (Name, Age, Gender, Contact, Address)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, age, gender, contact, address))
        patient_id = cursor.lastrowid

        # Create linked User entry
        cursor.execute('''
            INSERT INTO User (Username, Password, Role, ReferenceID)
            VALUES (?, ?, 'Patient', ?)
        ''', (username, password, patient_id))

        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Username already exists'}), 409

    conn.close()
    return jsonify({'message': 'Patient registered successfully'}), 201