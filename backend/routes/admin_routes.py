from flask import Blueprint, request, jsonify
import sqlite3
import os

admin_bp = Blueprint('admin', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'hospital.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ====== DOCTOR CRUD ======

@admin_bp.route('/doctors', methods=['GET'])
def get_doctors():
    conn = get_db_connection()
    doctors = conn.execute('SELECT * FROM Doctor').fetchall()
    conn.close()
    return jsonify([dict(row) for row in doctors])


@admin_bp.route('/doctors', methods=['POST'])
def add_doctor():
    data = request.get_json()
    name = data.get('name')
    specialization = data.get('specialization')
    department_id = data.get('department_id')
    contact = data.get('contact')
    email = data.get('email')
    password = data.get('password', 'doctor123')  # Admin sets password, default to 'doctor123' if not provided

    if not all([name, specialization, department_id, email]):
        return jsonify({'error': 'Missing required fields (name, specialization, department, email)'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if email already exists in User table
    existing_user = cursor.execute('SELECT * FROM User WHERE Username = ?', (email,)).fetchone()
    if existing_user:
        conn.close()
        return jsonify({'error': 'A user with this email already exists'}), 400
    
    cursor.execute(
        'INSERT INTO Doctor (Name, Specialization, DepartmentID, Contact, Email) VALUES (?, ?, ?, ?, ?)',
        (name, specialization, department_id, contact, email)
    )
    doctor_id = cursor.lastrowid

    # Create a linked User entry with admin-provided password
    cursor.execute(
        'INSERT INTO User (Username, Password, Role, ReferenceID) VALUES (?, ?, ?, ?)',
        (email, password, 'Doctor', doctor_id)
    )

    conn.commit()
    conn.close()
    return jsonify({'message': 'Doctor added successfully', 'login_username': email}), 201


@admin_bp.route('/doctors/<int:doctor_id>', methods=['PUT'])
def update_doctor(doctor_id):
    data = request.get_json()
    fields = ['Name', 'Specialization', 'DepartmentID', 'Contact', 'Email']
    updates = {f: data[f.lower()] for f in fields if f.lower() in data}

    if not updates:
        return jsonify({'error': 'No valid fields provided'}), 400

    set_clause = ', '.join([f"{f} = ?" for f in updates])
    values = list(updates.values()) + [doctor_id]

    conn = get_db_connection()
    conn.execute(f'UPDATE Doctor SET {set_clause} WHERE DoctorID = ?', values)
    conn.commit()
    conn.close()

    return jsonify({'message': 'Doctor updated successfully'}), 200


@admin_bp.route('/doctors/<int:doctor_id>/blacklist', methods=['PUT'])
def toggle_doctor_blacklist(doctor_id):
    data = request.get_json()
    status = data.get('status')  # 1 = blacklist, 0 = remove from blacklist
    if status not in [0, 1]:
        return jsonify({'error': 'Invalid status value'}), 400

    conn = get_db_connection()
    conn.execute('UPDATE Doctor SET IsBlacklisted = ? WHERE DoctorID = ?', (status, doctor_id))
    conn.commit()
    conn.close()

    return jsonify({'message': f'Doctor {"blacklisted" if status else "unblacklisted"} successfully'}), 200


@admin_bp.route('/doctors/<int:doctor_id>', methods=['DELETE'])
def delete_doctor(doctor_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM Doctor WHERE DoctorID = ?', (doctor_id,))
    conn.execute('DELETE FROM User WHERE Role = "Doctor" AND ReferenceID = ?', (doctor_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Doctor deleted successfully'}), 200


# ====== PATIENT CRUD ======

@admin_bp.route('/patients', methods=['GET'])
def get_patients():
    conn = get_db_connection()
    patients = conn.execute('SELECT * FROM Patient').fetchall()
    conn.close()
    return jsonify([dict(row) for row in patients])

@admin_bp.route('/patients/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    data = request.get_json()
    fields = ['Name', 'Age', 'Gender', 'Contact', 'Address']
    updates = {f: data[f.lower()] for f in fields if f.lower() in data}

    if not updates:
        return jsonify({'error': 'No valid fields provided'}), 400

    set_clause = ', '.join([f"{f} = ?" for f in updates])
    values = list(updates.values()) + [patient_id]

    conn = get_db_connection()
    conn.execute(f'UPDATE Patient SET {set_clause} WHERE PatientID = ?', values)
    conn.commit()
    conn.close()

    return jsonify({'message': 'Patient updated successfully'}), 200

'''@admin_bp.route('/patients', methods=['POST'])
def add_patient():
    data = request.get_json()
    name = data.get('name')
    age = data.get('age')
    gender = data.get('gender')
    contact = data.get('contact')
    address = data.get('address')

    if not all([name, age, gender]):
        return jsonify({'error': 'Missing required fields'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO Patient (Name, Age, Gender, Contact, Address) VALUES (?, ?, ?, ?, ?)',
        (name, age, gender, contact, address)
    )
    patient_id = cursor.lastrowid

    cursor.execute(
        'INSERT INTO User (Username, Password, Role, ReferenceID) VALUES (?, ?, ?, ?)',
        (contact or name.lower().replace(' ', '_'), 'patient123', 'Patient', patient_id)
    )

    conn.commit()
    conn.close()
    return jsonify({'message': 'Patient added successfully'}), 201'''


@admin_bp.route('/patients/<int:patient_id>/blacklist', methods=['PUT'])
def toggle_patient_blacklist(patient_id):
    data = request.get_json()
    status = data.get('status')  # 1 = blacklist, 0 = unblacklist
    if status not in [0, 1]:
        return jsonify({'error': 'Invalid status value'}), 400

    conn = get_db_connection()
    conn.execute('UPDATE Patient SET IsBlacklisted = ? WHERE PatientID = ?', (status, patient_id))
    conn.commit()
    conn.close()

    return jsonify({'message': f'Patient {"blacklisted" if status else "unblacklisted"} successfully'}), 200


@admin_bp.route('/patients/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM Patient WHERE PatientID = ?', (patient_id,))
    conn.execute('DELETE FROM User WHERE Role = "Patient" AND ReferenceID = ?', (patient_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Patient deleted successfully'}), 200

# Get Prescription / History for a Patient
@admin_bp.route('/patients/<int:patient_id>/history', methods=['GET'])
def get_patient_history(patient_id):
    conn = get_db_connection()
    history = conn.execute('''
        SELECT h.HistoryID, h.AppointmentID, h.Tests, h.MedicineName, h.Instructions,
               a.AppointmentDate, a.Status,
               d.Name AS DoctorName, d.Specialization
        FROM History h
        JOIN Appointment a ON h.AppointmentID = a.AppointmentID
        JOIN Doctor d ON a.DoctorID = d.DoctorID
        WHERE h.PatientID = ?
        ORDER BY a.AppointmentDate DESC
    ''', (patient_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in history]), 200

@admin_bp.route('/doctors/search', methods=['GET'])
def search_doctors():
    q = request.args.get('q', '').lower()

    conn = get_db_connection()
    doctors = conn.execute('''
        SELECT * FROM Doctor
        WHERE 
            lower(Name) LIKE ? OR
            lower(Specialization) LIKE ? OR
            lower(Contact) LIKE ? OR
            lower(Email) LIKE ?
    ''', (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()

    conn.close()
    return jsonify([dict(row) for row in doctors]), 200

@admin_bp.route('/patients/search', methods=['GET'])
def search_patients():
    q = request.args.get('q', '').lower()

    conn = get_db_connection()
    patients = conn.execute('''
        SELECT * FROM Patient
        WHERE 
            lower(Name) LIKE ? OR
            lower(Contact) LIKE ? OR
            lower(Address) LIKE ?
    ''', (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()

    conn.close()
    return jsonify([dict(row) for row in patients]), 200

# ====== DEPARTMENT CRUD ======

@admin_bp.route('/departments', methods=['GET'])
def get_departments():
    conn = get_db_connection()
    departments = conn.execute('SELECT * FROM Department').fetchall()
    conn.close()
    return jsonify([dict(row) for row in departments]), 200

@admin_bp.route('/departments', methods=['POST'])
def add_department():
    data = request.get_json()
    name = data.get('name')
    location = data.get('location')

    if not name:
        return jsonify({'error': 'Department name is required'}), 400

    conn = get_db_connection()
    conn.execute('INSERT INTO Department (Name, Location) VALUES (?, ?)', (name, location))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Department added successfully'}), 201

@admin_bp.route('/departments/<int:department_id>', methods=['PUT'])
def update_department(department_id):
    data = request.get_json()
    fields = ['Name', 'Location']
    updates = {f: data[f.lower()] for f in fields if f.lower() in data}

    if not updates:
        return jsonify({'error': 'No valid fields provided'}), 400

    set_clause = ', '.join([f"{f} = ?" for f in updates])
    values = list(updates.values()) + [department_id]

    conn = get_db_connection()
    conn.execute(f'UPDATE Department SET {set_clause} WHERE DepartmentID = ?', values)
    conn.commit()
    conn.close()

    return jsonify({'message': 'Department updated successfully'}), 200

@admin_bp.route('/departments/<int:department_id>', methods=['DELETE'])
def delete_department(department_id):
    conn = get_db_connection()
    
    # Check if any doctors are assigned to this department
    doctors_count = conn.execute(
        'SELECT COUNT(*) as count FROM Doctor WHERE DepartmentID = ?', 
        (department_id,)
    ).fetchone()['count']
    
    if doctors_count > 0:
        conn.close()
        return jsonify({'error': f'Cannot delete department. {doctors_count} doctor(s) are assigned to it.'}), 400
    
    conn.execute('DELETE FROM Department WHERE DepartmentID = ?', (department_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Department deleted successfully'}), 200

# ====== APPOINTMENTS ======

@admin_bp.route('/appointments', methods=['GET'])
def get_all_appointments():
    conn = get_db_connection()
    appointments = conn.execute('''
        SELECT 
            a.AppointmentID,
            a.AppointmentDate,
            a.Status,
            a.PatientID,
            p.Name as PatientName,
            p.Contact as PatientContact,
            d.Name as DoctorName,
            d.Specialization
        FROM Appointment a
        JOIN Patient p ON a.PatientID = p.PatientID
        JOIN Doctor d ON a.DoctorID = d.DoctorID
        ORDER BY a.AppointmentDate DESC
    ''').fetchall()
    conn.close()
    return jsonify([dict(row) for row in appointments]), 200

@admin_bp.route('/appointments/<int:appointment_id>/status', methods=['PUT'])
def update_appointment_status(appointment_id):
    data = request.get_json()
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({'error': 'Status is required'}), 400
    
    if new_status not in ['Scheduled', 'Completed', 'Cancelled']:
        return jsonify({'error': 'Invalid status'}), 400
    
    conn = get_db_connection()
    conn.execute('UPDATE Appointment SET Status = ? WHERE AppointmentID = ?', (new_status, appointment_id))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Appointment status updated successfully'}), 200

