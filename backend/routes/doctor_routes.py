from flask import Blueprint, request, jsonify
import sqlite3
import os

doctor_bp = Blueprint('doctor', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'hospital.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# === 1️⃣ View Appointments for a Doctor ===
@doctor_bp.route('/appointments/<int:doctor_id>', methods=['GET'])
def get_doctor_appointments(doctor_id):
    conn = get_db_connection()
    appointments = conn.execute('''
        SELECT a.AppointmentID, a.AppointmentDate, a.Status,
               p.PatientID, p.Name AS PatientName, p.Age, p.Gender, p.Contact
        FROM Appointment a
        JOIN Patient p ON a.PatientID = p.PatientID
        WHERE a.DoctorID = ?
        ORDER BY a.AppointmentDate ASC
    ''', (doctor_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in appointments]), 200


# === 2️⃣ Update Appointment Status ===
@doctor_bp.route('/appointments/<int:appointment_id>/status', methods=['PUT'])
def update_appointment_status(appointment_id):
    data = request.get_json()
    status = data.get('status')
    if status not in ['Scheduled', 'Completed', 'Cancelled']:
        return jsonify({'error': 'Invalid status'}), 400

    conn = get_db_connection()
    conn.execute('UPDATE Appointment SET Status = ? WHERE AppointmentID = ?', (status, appointment_id))
    conn.commit()
    conn.close()
    return jsonify({'message': f'Appointment marked as {status}'}), 200


# === 3️⃣ Add Prescription / History Record ===
@doctor_bp.route('/appointments/<int:appointment_id>/history', methods=['POST'])
def add_prescription(appointment_id):
    data = request.get_json()
    patient_id = data.get('patient_id')
    tests = data.get('tests')
    medicine = data.get('medicine')
    instructions = data.get('instructions')

    if not patient_id:
        return jsonify({'error': 'Patient ID required'}), 400

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO History (AppointmentID, PatientID, Tests, MedicineName, Instructions)
        VALUES (?, ?, ?, ?, ?)
    ''', (appointment_id, patient_id, tests, medicine, instructions))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Prescription added successfully'}), 201


# === 4️⃣ Get Prescription / History for a Patient ===
@doctor_bp.route('/patients/<int:patient_id>/history', methods=['GET'])
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


# === 5️⃣ Quick Stats (optional for dashboard summary) ===
@doctor_bp.route('/dashboard/<int:doctor_id>/summary', methods=['GET'])
def doctor_dashboard_summary(doctor_id):
    conn = get_db_connection()

    total = conn.execute('SELECT COUNT(*) AS Total FROM Appointment WHERE DoctorID = ?', (doctor_id,)).fetchone()['Total']
    completed = conn.execute('SELECT COUNT(*) AS Completed FROM Appointment WHERE DoctorID = ? AND Status = "Completed"', (doctor_id,)).fetchone()['Completed']
    upcoming = conn.execute('SELECT COUNT(*) AS Upcoming FROM Appointment WHERE DoctorID = ? AND Status = "Scheduled"', (doctor_id,)).fetchone()['Upcoming']

    conn.close()

    return jsonify({
        'total_appointments': total,
        'completed_appointments': completed,
        'upcoming_appointments': upcoming
    }), 200

@doctor_bp.route('/<int:doctor_id>/availability', methods=['POST'])
def add_availability(doctor_id):
    data = request.get_json()
    day = data.get('day')
    start = data.get('start_time')
    end = data.get('end_time')

    if not all([day, start, end]):
        return jsonify({'error': 'Missing required fields'}), 400

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO DoctorAvailability (DoctorID, Day, StartTime, EndTime)
        VALUES (?, ?, ?, ?)
    ''', (doctor_id, day, start, end))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Availability added successfully'}), 201

@doctor_bp.route('/<int:doctor_id>/availability', methods=['GET'])
def get_availability(doctor_id):
    conn = get_db_connection()
    slots = conn.execute('''
        SELECT * FROM DoctorAvailability
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

    return jsonify([dict(row) for row in slots]), 200

@doctor_bp.route('/availability/<int:availability_id>', methods=['DELETE'])
def delete_availability(availability_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM DoctorAvailability WHERE AvailabilityID = ?', 
                 (availability_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Availability deleted successfully'}), 200

@doctor_bp.route('/availability/<int:availability_id>', methods=['PUT'])
def update_availability(availability_id):
    data = request.get_json()
    updates = {}

    if 'day' in data:
        updates['Day'] = data['day']
    if 'start_time' in data:
        updates['StartTime'] = data['start_time']
    if 'end_time' in data:
        updates['EndTime'] = data['end_time']

    if not updates:
        return jsonify({'error': 'No valid fields'}), 400

    set_clause = ', '.join([f"{k} = ?" for k in updates])
    values = list(updates.values()) + [availability_id]

    conn = get_db_connection()
    conn.execute(f'''
        UPDATE DoctorAvailability 
        SET {set_clause}
        WHERE AvailabilityID = ?
    ''', values)
    conn.commit()
    conn.close()

    return jsonify({'message': 'Availability updated successfully'}), 200
