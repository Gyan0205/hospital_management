import sqlite3

def init_db():
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()

    # === TABLE CREATION ===

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Department (
        DepartmentID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Location TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Patient (
    PatientID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Age INTEGER,
    Gender TEXT CHECK(Gender IN ('Male','Female','Other')),
    Contact TEXT,
    Address TEXT,
    IsBlacklisted INTEGER DEFAULT 0 CHECK(IsBlacklisted IN (0,1))
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Doctor (
    DoctorID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Specialization TEXT,
    DepartmentID INTEGER,
    Contact TEXT,
    Email TEXT,
    IsBlacklisted INTEGER DEFAULT 0 CHECK(IsBlacklisted IN (0,1)),
    FOREIGN KEY (DepartmentID) REFERENCES Department(DepartmentID)
    )
    ''')


    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Appointment (
        AppointmentID INTEGER PRIMARY KEY AUTOINCREMENT,
        AppointmentDate TEXT NOT NULL,
        PatientID INTEGER,
        DoctorID INTEGER,
        Status TEXT DEFAULT 'Scheduled' CHECK(Status IN ('Scheduled','Completed','Cancelled')),
        FOREIGN KEY (PatientID) REFERENCES Patient(PatientID),
        FOREIGN KEY (DoctorID) REFERENCES Doctor(DoctorID)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS History (
        HistoryID INTEGER PRIMARY KEY AUTOINCREMENT,
        AppointmentID INTEGER,
        PatientID INTEGER,
        Tests TEXT,
        MedicineName TEXT,
        Instructions TEXT,
        FOREIGN KEY (AppointmentID) REFERENCES Appointment(AppointmentID),
        FOREIGN KEY (PatientID) REFERENCES Patient(PatientID)
    )
''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS User (
        UserID INTEGER PRIMARY KEY AUTOINCREMENT,
        Username TEXT UNIQUE NOT NULL,
        Password TEXT NOT NULL,
        Role TEXT CHECK(Role IN ('Admin','Doctor','Patient')) NOT NULL,
        ReferenceID INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS DoctorAvailability (
    AvailabilityID INTEGER PRIMARY KEY AUTOINCREMENT,
    DoctorID INTEGER,
    Day TEXT NOT NULL,
    StartTime TEXT NOT NULL,
    EndTime TEXT NOT NULL,
    FOREIGN KEY (DoctorID) REFERENCES Doctor(DoctorID)
    )
    ''')


    conn.commit()

    # === SAMPLE DATA INSERTION ===

    # Insert Departments
    cursor.executemany('''
        INSERT OR IGNORE INTO Department (Name, Location)
        VALUES (?, ?)
    ''', [
        ('Cardiology', 'Block A'),
        ('Neurology', 'Block B'),
        ('Orthopedics', 'Block C')
    ])

    # Insert Doctors
    cursor.executemany('''
        INSERT OR IGNORE INTO Doctor (Name, Specialization, DepartmentID, Contact, Email)
        VALUES (?, ?, ?, ?, ?)
    ''', [
        ('Dr. Ravi Kumar', 'Cardiologist', 1, '9876543210', 'ravi.kumar@hospital.com'),
        ('Dr. Neha Sharma', 'Neurologist', 2, '9988776655', 'neha.sharma@hospital.com')
    ])

    # Insert Patients
    cursor.executemany('''
        INSERT OR IGNORE INTO Patient (Name, Age, Gender, Contact, Address)
        VALUES (?, ?, ?, ?, ?)
    ''', [
        ('Arjun Mehta', 28, 'Male', '9998887776', 'Hyderabad'),
        ('Priya Verma', 34, 'Female', '8887776665', 'Chennai')
    ])

    # Insert Users (sample login accounts)
    cursor.executemany('''
        INSERT OR IGNORE INTO User (Username, Password, Role, ReferenceID)
        VALUES (?, ?, ?, ?)
    ''', [
        ('admin', 'admin123', 'Admin', None),
        ('aksheth', 'doctor123', 'Doctor', 1),
        ('neha', 'doctor123', 'Doctor', 2),
        ('arjun', 'patient123', 'Patient', 1),
        ('priya', 'patient123', 'Patient', 2)
    ])

    conn.commit()
    conn.close()
    print("Database initialized successfully with sample data: hospital.db")

if __name__ == "__main__":
    init_db()
