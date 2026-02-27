from flask import Blueprint, request, jsonify
import sqlite3
import os

patient_bp = Blueprint('patient', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'hospital.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# === 1️⃣ Patient Profile ===
@patient_bp.route('/profile/<int:patient_id>', methods=['GET'])
def get_patient_profile(patient_id):
    conn = get_db_connection()
    patient = conn.execute('SELECT * FROM Patient WHERE PatientID = ?', (patient_id,)).fetchone()
    conn.close()

    if not patient:
        return jsonify({'error': 'Patient not found'}), 404

    return jsonify(dict(patient)), 200


@patient_bp.route('/profile/<int:patient_id>', methods=['PUT'])
def update_patient_profile(patient_id):
    data = request.get_json()
    
    # Validate required fields
    name = data.get('name')
    age = data.get('age')
    gender = data.get('gender')
    contact = data.get('contact')
    address = data.get('address', '')
    
    if not all([name, age, gender, contact]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate age
    try:
        age = int(age)
        if age < 0 or age > 150:
            return jsonify({'error': 'Invalid age'}), 400
    except ValueError:
        return jsonify({'error': 'Age must be a number'}), 400
    
    # Validate gender
    if gender not in ['Male', 'Female', 'Other']:
        return jsonify({'error': 'Gender must be Male, Female, or Other'}), 400
    
    conn = get_db_connection()
    
    # Check if patient exists
    patient = conn.execute('SELECT PatientID FROM Patient WHERE PatientID = ?', (patient_id,)).fetchone()
    if not patient:
        conn.close()
        return jsonify({'error': 'Patient not found'}), 404
    
    # Update profile
    conn.execute('''
        UPDATE Patient 
        SET Name = ?, Age = ?, Gender = ?, Contact = ?, Address = ?
        WHERE PatientID = ?
    ''', (name, age, gender, contact, address, patient_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Profile updated successfully'}), 200


# === 2️⃣ View Patient Appointments ===
@patient_bp.route('/appointments/<int:patient_id>', methods=['GET'])
def get_patient_appointments(patient_id):
    conn = get_db_connection()
    appointments = conn.execute('''
        SELECT 
            a.AppointmentID, a.AppointmentDate, a.Status,
            d.DoctorID, d.Name AS DoctorName, d.Specialization
        FROM Appointment a
        JOIN Doctor d ON a.DoctorID = d.DoctorID
        WHERE a.PatientID = ?
        ORDER BY a.AppointmentDate DESC
    ''', (patient_id,)).fetchall()
    conn.close()

    return jsonify([dict(row) for row in appointments]), 200


# === 3️⃣ Book Appointment ===
@patient_bp.route('/appointments/book', methods=['POST'])
def book_appointment():
    import datetime

    data = request.get_json()
    patient_id = data.get('patient_id')
    doctor_id = data.get('doctor_id')
    date_str = data.get('date')   # Example: "2025-02-20 10:30"

    if not all([patient_id, doctor_id, date_str]):
        return jsonify({'error': 'Missing fields'}), 400

    # Parse date/time
    try:
        appointment_dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    except:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD HH:MM'}), 400

    # Extract weekday
    day_name = appointment_dt.strftime("%A")   # Monday, Tuesday, ...

    # Extract time as string
    time_str = appointment_dt.strftime("%H:%M")

    conn = get_db_connection()

    # Block blacklisted patients
    blk = conn.execute(
        'SELECT IsBlacklisted FROM Patient WHERE PatientID = ?', (patient_id,)
    ).fetchone()

    if blk and blk["IsBlacklisted"] == 1:
        conn.close()
        return jsonify({'error': 'Patient account is blacklisted'}), 403

    # Fetch doctor availability for that day
    slots = conn.execute('''
        SELECT StartTime, EndTime 
        FROM DoctorAvailability
        WHERE DoctorID = ? AND Day = ?
    ''', (doctor_id, day_name)).fetchall()

    if not slots:
        conn.close()
        return jsonify({'error': f'Doctor is not available on {day_name}'}), 400

    # Check if requested time falls in ANY availability slot
    time_valid = False
    for s in slots:
        if s["StartTime"] <= time_str <= s["EndTime"]:
            time_valid = True
            break

    if not time_valid:
        conn.close()
        return jsonify({
            'error': f'Doctor available on {day_name} only during these times',
            'available_slots': [dict(slot) for slot in slots]
        }), 400

    # Create appointment
    conn.execute('''
        INSERT INTO Appointment (AppointmentDate, PatientID, DoctorID, Status)
        VALUES (?, ?, ?, 'Scheduled')
    ''', (date_str, patient_id, doctor_id))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Appointment booked successfully'}), 201


# === 4️⃣ Cancel Appointment (Patient side) ===
@patient_bp.route('/appointments/<int:appointment_id>/cancel', methods=['PUT'])
def cancel_appointment(appointment_id):
    conn = get_db_connection()

    conn.execute('UPDATE Appointment SET Status = "Cancelled" WHERE AppointmentID = ?', (appointment_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Appointment cancelled successfully'}), 200


# === 5️⃣ View Patient History ===
@patient_bp.route('/history/<int:patient_id>', methods=['GET'])
def get_history(patient_id):
    conn = get_db_connection()
    history = conn.execute('''
        SELECT 
            h.HistoryID, h.Tests, h.MedicineName, h.Instructions,
            a.AppointmentDate, a.Status,
            d.DoctorID, d.Name AS DoctorName, d.Specialization
        FROM History h
        JOIN Appointment a ON h.AppointmentID = a.AppointmentID
        JOIN Doctor d ON a.DoctorID = d.DoctorID
        WHERE h.PatientID = ?
        ORDER BY a.AppointmentDate DESC
    ''', (patient_id,)).fetchall()
    conn.close()

    return jsonify([dict(row) for row in history]), 200


# === 6️⃣ Dashboard Summary ===
@patient_bp.route('/dashboard/<int:patient_id>/summary', methods=['GET'])
def patient_summary(patient_id):
    conn = get_db_connection()

    total = conn.execute(
        'SELECT COUNT(*) AS Total FROM Appointment WHERE PatientID = ?', (patient_id,)
    ).fetchone()['Total']

    upcoming = conn.execute(
        'SELECT COUNT(*) AS Upcoming FROM Appointment WHERE PatientID = ? AND Status = "Scheduled"',
        (patient_id,)
    ).fetchone()['Upcoming']

    completed = conn.execute(
        'SELECT COUNT(*) AS Completed FROM Appointment WHERE PatientID = ? AND Status = "Completed"',
        (patient_id,)
    ).fetchone()['Completed']

    conn.close()

    return jsonify({
        'total_appointments': total,
        'upcoming_appointments': upcoming,
        'completed_appointments': completed
    }), 200

@patient_bp.route('/doctor/<int:doctor_id>', methods=['GET'])
def get_doctor_details(doctor_id):
    conn = get_db_connection()

    # fetch doctor info
    doctor = conn.execute('''
        SELECT 
            d.DoctorID,
            d.Name,
            d.Specialization,
            dep.Name AS DepartmentName
        FROM Doctor d
        LEFT JOIN Department dep ON d.DepartmentID = dep.DepartmentID
        WHERE d.DoctorID = ? AND d.IsBlacklisted = 0
    ''', (doctor_id,)).fetchone()

    if not doctor:
        conn.close()
        return jsonify({'error': 'Doctor not found'}), 404

    # fetch availability slots
    availability = conn.execute('''
        SELECT AvailabilityID, Day, StartTime, EndTime
        FROM DoctorAvailability
        WHERE DoctorID = ?
        ORDER BY 
            CASE 
                WHEN Day = 'Monday' THEN 1
                WHEN Day = 'Tuesday' THEN 2
                WHEN Day = 'Wednesday' THEN 3
                WHEN Day = 'Thursday' THEN 4
                WHEN Day = 'Friday' THEN 5
                WHEN Day = 'Saturday' THEN 6
                WHEN Day = 'Sunday' THEN 7
            END,
            StartTime
    ''', (doctor_id,)).fetchall()

    conn.close()

    return jsonify({
        "DoctorID": doctor["DoctorID"],
        "Name": doctor["Name"],
        "Specialization": doctor["Specialization"],
        "DepartmentName": doctor["DepartmentName"],
        "Availability": [dict(a) for a in availability]
    }), 200
