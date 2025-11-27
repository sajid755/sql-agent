"""
School Management System Database Setup
Creates 10 tables with 100+ records each for testing purposes
"""

import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from faker import Faker
import random
from datetime import datetime, timedelta

load_dotenv()
fake = Faker()

# Database connection
def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def create_tables(conn):
    """Create all school management tables"""
    cursor = conn.cursor()
    
    # Drop existing tables if they exist
    print("Dropping existing tables...")
    tables = ['enrollments', 'grades', 'attendance', 'assignments', 'library_books', 
              'library_transactions', 'staff', 'classes', 'subjects', 'students']
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
    
    print("Creating tables...")
    
    # 1. Students table
    cursor.execute("""
        CREATE TABLE students (
            student_id SERIAL PRIMARY KEY,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            phone VARCHAR(20),
            date_of_birth DATE NOT NULL,
            gender VARCHAR(10),
            address TEXT,
            admission_date DATE NOT NULL,
            grade_level INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'active'
        );
    """)
    
    # 2. Subjects table
    cursor.execute("""
        CREATE TABLE subjects (
            subject_id SERIAL PRIMARY KEY,
            subject_name VARCHAR(100) NOT NULL,
            subject_code VARCHAR(20) UNIQUE NOT NULL,
            description TEXT,
            credits INTEGER DEFAULT 3,
            department VARCHAR(50)
        );
    """)
    
    # 3. Staff table
    cursor.execute("""
        CREATE TABLE staff (
            staff_id SERIAL PRIMARY KEY,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            phone VARCHAR(20),
            role VARCHAR(50) NOT NULL,
            department VARCHAR(50),
            hire_date DATE NOT NULL,
            salary DECIMAL(10, 2),
            status VARCHAR(20) DEFAULT 'active'
        );
    """)
    
    # 4. Classes table
    cursor.execute("""
        CREATE TABLE classes (
            class_id SERIAL PRIMARY KEY,
            class_name VARCHAR(100) NOT NULL,
            subject_id INTEGER REFERENCES subjects(subject_id),
            teacher_id INTEGER REFERENCES staff(staff_id),
            room_number VARCHAR(20),
            schedule VARCHAR(100),
            semester VARCHAR(20),
            year INTEGER,
            max_students INTEGER DEFAULT 30
        );
    """)
    
    # 5. Enrollments table
    cursor.execute("""
        CREATE TABLE enrollments (
            enrollment_id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(student_id),
            class_id INTEGER REFERENCES classes(class_id),
            enrollment_date DATE NOT NULL,
            status VARCHAR(20) DEFAULT 'enrolled'
        );
    """)
    
    # 6. Grades table
    cursor.execute("""
        CREATE TABLE grades (
            grade_id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(student_id),
            class_id INTEGER REFERENCES classes(class_id),
            assignment_name VARCHAR(100),
            grade DECIMAL(5, 2),
            max_grade DECIMAL(5, 2) DEFAULT 100,
            grade_date DATE NOT NULL,
            comments TEXT
        );
    """)
    
    # 7. Attendance table
    cursor.execute("""
        CREATE TABLE attendance (
            attendance_id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(student_id),
            class_id INTEGER REFERENCES classes(class_id),
            attendance_date DATE NOT NULL,
            status VARCHAR(20) NOT NULL,
            remarks TEXT
        );
    """)
    
    # 8. Assignments table
    cursor.execute("""
        CREATE TABLE assignments (
            assignment_id SERIAL PRIMARY KEY,
            class_id INTEGER REFERENCES classes(class_id),
            title VARCHAR(200) NOT NULL,
            description TEXT,
            due_date DATE NOT NULL,
            max_points DECIMAL(5, 2) DEFAULT 100,
            assignment_type VARCHAR(50)
        );
    """)
    
    # 9. Library Books table
    cursor.execute("""
        CREATE TABLE library_books (
            book_id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            author VARCHAR(100),
            isbn VARCHAR(20) UNIQUE,
            publisher VARCHAR(100),
            publication_year INTEGER,
            category VARCHAR(50),
            total_copies INTEGER DEFAULT 1,
            available_copies INTEGER DEFAULT 1,
            shelf_location VARCHAR(50)
        );
    """)
    
    # 10. Library Transactions table
    cursor.execute("""
        CREATE TABLE library_transactions (
            transaction_id SERIAL PRIMARY KEY,
            book_id INTEGER REFERENCES library_books(book_id),
            student_id INTEGER REFERENCES students(student_id),
            checkout_date DATE NOT NULL,
            due_date DATE NOT NULL,
            return_date DATE,
            status VARCHAR(20) DEFAULT 'borrowed',
            fine_amount DECIMAL(10, 2) DEFAULT 0
        );
    """)
    
    conn.commit()
    print("✅ All tables created successfully!")

def populate_students(conn, count=150):
    """Populate students table"""
    cursor = conn.cursor()
    print(f"Inserting {count} students...")
    
    for _ in range(count):
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}@school.edu"
        phone = fake.phone_number()[:20]
        dob = fake.date_of_birth(minimum_age=5, maximum_age=18)
        gender = random.choice(['Male', 'Female', 'Other'])
        address = fake.address()
        admission_date = fake.date_between(start_date='-5y', end_date='today')
        grade_level = random.randint(1, 12)
        status = random.choice(['active'] * 9 + ['inactive'])
        
        cursor.execute("""
            INSERT INTO students (first_name, last_name, email, phone, date_of_birth, 
                                gender, address, admission_date, grade_level, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (first_name, last_name, email, phone, dob, gender, address, 
              admission_date, grade_level, status))
    
    conn.commit()
    print(f"✅ {count} students inserted!")

def populate_subjects(conn, count=120):
    """Populate subjects table"""
    cursor = conn.cursor()
    print(f"Inserting {count} subjects...")
    
    departments = ['Mathematics', 'Science', 'English', 'Social Studies', 'Arts', 
                   'Physical Education', 'Computer Science', 'Languages']
    subject_types = ['Algebra', 'Geometry', 'Calculus', 'Physics', 'Chemistry', 'Biology',
                     'Literature', 'Writing', 'History', 'Geography', 'Music', 'Art',
                     'Programming', 'Spanish', 'French', 'Physical Education']
    
    for i in range(count):
        subject_name = f"{random.choice(subject_types)} {random.choice(['I', 'II', 'III', 'Advanced', 'Honors'])}"
        subject_code = f"{random.choice(['MATH', 'SCI', 'ENG', 'SOC', 'ART', 'PE', 'CS', 'LANG'])}{random.randint(100, 999)}"
        description = fake.sentence()
        credits = random.choice([2, 3, 4, 5])
        department = random.choice(departments)
        
        try:
            cursor.execute("""
                INSERT INTO subjects (subject_name, subject_code, description, credits, department)
                VALUES (%s, %s, %s, %s, %s)
            """, (subject_name, subject_code, description, credits, department))
        except:
            pass  # Skip duplicates
    
    conn.commit()
    print(f"✅ Subjects inserted!")

def populate_staff(conn, count=100):
    """Populate staff table"""
    cursor = conn.cursor()
    print(f"Inserting {count} staff members...")
    
    roles = ['Teacher', 'Administrator', 'Counselor', 'Librarian', 'IT Support', 'Nurse']
    departments = ['Mathematics', 'Science', 'English', 'Social Studies', 'Arts', 
                   'Physical Education', 'Computer Science', 'Administration']
    
    for _ in range(count):
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}@school.edu"
        phone = fake.phone_number()[:20]
        role = random.choice(roles)
        department = random.choice(departments)
        hire_date = fake.date_between(start_date='-20y', end_date='today')
        salary = round(random.uniform(35000, 95000), 2)
        status = random.choice(['active'] * 9 + ['inactive'])
        
        try:
            cursor.execute("""
                INSERT INTO staff (first_name, last_name, email, phone, role, department, 
                                 hire_date, salary, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (first_name, last_name, email, phone, role, department, 
                  hire_date, salary, status))
        except:
            pass
    
    conn.commit()
    print(f"✅ Staff members inserted!")

def populate_classes(conn, count=100):
    """Populate classes table"""
    cursor = conn.cursor()
    print(f"Inserting {count} classes...")
    
    cursor.execute("SELECT subject_id FROM subjects")
    subject_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT staff_id FROM staff WHERE role = 'Teacher'")
    teacher_ids = [row[0] for row in cursor.fetchall()]
    
    if not teacher_ids:
        cursor.execute("SELECT staff_id FROM staff LIMIT 20")
        teacher_ids = [row[0] for row in cursor.fetchall()]
    
    schedules = ['MWF 9:00-10:00', 'TTh 10:00-11:30', 'MWF 13:00-14:00', 
                 'TTh 14:00-15:30', 'Daily 8:00-9:00']
    semesters = ['Fall', 'Spring', 'Summer']
    years = [2023, 2024, 2025]
    
    for i in range(count):
        class_name = f"Class {i+1}"
        subject_id = random.choice(subject_ids)
        teacher_id = random.choice(teacher_ids)
        room_number = f"{random.randint(100, 500)}"
        schedule = random.choice(schedules)
        semester = random.choice(semesters)
        year = random.choice(years)
        max_students = random.randint(20, 35)
        
        cursor.execute("""
            INSERT INTO classes (class_name, subject_id, teacher_id, room_number, 
                               schedule, semester, year, max_students)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (class_name, subject_id, teacher_id, room_number, schedule, 
              semester, year, max_students))
    
    conn.commit()
    print(f"✅ {count} classes inserted!")

def populate_enrollments(conn, count=500):
    """Populate enrollments table"""
    cursor = conn.cursor()
    print(f"Inserting {count} enrollments...")
    
    cursor.execute("SELECT student_id FROM students")
    student_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT class_id FROM classes")
    class_ids = [row[0] for row in cursor.fetchall()]
    
    for _ in range(count):
        student_id = random.choice(student_ids)
        class_id = random.choice(class_ids)
        enrollment_date = fake.date_between(start_date='-1y', end_date='today')
        status = random.choice(['enrolled'] * 8 + ['dropped', 'completed'])
        
        try:
            cursor.execute("""
                INSERT INTO enrollments (student_id, class_id, enrollment_date, status)
                VALUES (%s, %s, %s, %s)
            """, (student_id, class_id, enrollment_date, status))
        except:
            pass
    
    conn.commit()
    print(f"✅ Enrollments inserted!")

def populate_grades(conn, count=1000):
    """Populate grades table"""
    cursor = conn.cursor()
    print(f"Inserting {count} grades...")
    
    cursor.execute("SELECT student_id, class_id FROM enrollments WHERE status = 'enrolled'")
    enrollments = cursor.fetchall()
    
    assignment_types = ['Quiz', 'Test', 'Homework', 'Project', 'Midterm', 'Final']
    
    for _ in range(min(count, len(enrollments) * 5)):
        student_id, class_id = random.choice(enrollments)
        assignment_name = f"{random.choice(assignment_types)} {random.randint(1, 10)}"
        max_grade = 100
        grade = round(random.uniform(60, 100), 2)
        grade_date = fake.date_between(start_date='-6m', end_date='today')
        comments = fake.sentence() if random.random() > 0.7 else None
        
        cursor.execute("""
            INSERT INTO grades (student_id, class_id, assignment_name, grade, 
                              max_grade, grade_date, comments)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (student_id, class_id, assignment_name, grade, max_grade, grade_date, comments))
    
    conn.commit()
    print(f"✅ Grades inserted!")

def populate_attendance(conn, count=2000):
    """Populate attendance table"""
    cursor = conn.cursor()
    print(f"Inserting {count} attendance records...")
    
    cursor.execute("SELECT student_id, class_id FROM enrollments WHERE status = 'enrolled'")
    enrollments = cursor.fetchall()
    
    statuses = ['Present', 'Absent', 'Late', 'Excused']
    
    for _ in range(min(count, len(enrollments) * 10)):
        student_id, class_id = random.choice(enrollments)
        attendance_date = fake.date_between(start_date='-3m', end_date='today')
        status = random.choice(['Present'] * 7 + ['Absent', 'Late', 'Excused'])
        remarks = fake.sentence() if status != 'Present' and random.random() > 0.5 else None
        
        cursor.execute("""
            INSERT INTO attendance (student_id, class_id, attendance_date, status, remarks)
            VALUES (%s, %s, %s, %s, %s)
        """, (student_id, class_id, attendance_date, status, remarks))
    
    conn.commit()
    print(f"✅ Attendance records inserted!")

def populate_assignments(conn, count=200):
    """Populate assignments table"""
    cursor = conn.cursor()
    print(f"Inserting {count} assignments...")
    
    cursor.execute("SELECT class_id FROM classes")
    class_ids = [row[0] for row in cursor.fetchall()]
    
    assignment_types = ['Quiz', 'Test', 'Homework', 'Project', 'Essay', 'Lab Report']
    
    for i in range(count):
        class_id = random.choice(class_ids)
        title = f"{random.choice(assignment_types)}: {fake.catch_phrase()}"
        description = fake.paragraph()
        due_date = fake.date_between(start_date='today', end_date='+3m')
        max_points = random.choice([50, 100, 150, 200])
        assignment_type = random.choice(assignment_types)
        
        cursor.execute("""
            INSERT INTO assignments (class_id, title, description, due_date, 
                                   max_points, assignment_type)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (class_id, title, description, due_date, max_points, assignment_type))
    
    conn.commit()
    print(f"✅ {count} assignments inserted!")

def populate_library_books(conn, count=300):
    """Populate library books table"""
    cursor = conn.cursor()
    print(f"Inserting {count} library books...")
    
    categories = ['Fiction', 'Non-Fiction', 'Science', 'History', 'Biography', 
                  'Reference', 'Technology', 'Arts', 'Literature']
    
    for _ in range(count):
        title = fake.catch_phrase()
        author = fake.name()
        isbn = fake.isbn13()
        publisher = fake.company()
        publication_year = random.randint(1950, 2024)
        category = random.choice(categories)
        total_copies = random.randint(1, 5)
        available_copies = random.randint(0, total_copies)
        shelf_location = f"{random.choice(['A', 'B', 'C', 'D'])}-{random.randint(1, 50)}"
        
        try:
            cursor.execute("""
                INSERT INTO library_books (title, author, isbn, publisher, publication_year,
                                         category, total_copies, available_copies, shelf_location)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (title, author, isbn, publisher, publication_year, category, 
                  total_copies, available_copies, shelf_location))
        except:
            pass
    
    conn.commit()
    print(f"✅ Library books inserted!")

def populate_library_transactions(conn, count=400):
    """Populate library transactions table"""
    cursor = conn.cursor()
    print(f"Inserting {count} library transactions...")
    
    cursor.execute("SELECT book_id FROM library_books")
    book_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT student_id FROM students")
    student_ids = [row[0] for row in cursor.fetchall()]
    
    for _ in range(count):
        book_id = random.choice(book_ids)
        student_id = random.choice(student_ids)
        checkout_date = fake.date_between(start_date='-6m', end_date='today')
        due_date = checkout_date + timedelta(days=14)
        
        # 70% returned, 30% still borrowed
        if random.random() > 0.3:
            return_date = checkout_date + timedelta(days=random.randint(1, 30))
            status = 'returned'
            # Calculate fine if late
            if return_date > due_date:
                days_late = (return_date - due_date).days
                fine_amount = days_late * 0.50
            else:
                fine_amount = 0
        else:
            return_date = None
            status = 'borrowed'
            fine_amount = 0
        
        cursor.execute("""
            INSERT INTO library_transactions (book_id, student_id, checkout_date, 
                                            due_date, return_date, status, fine_amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (book_id, student_id, checkout_date, due_date, return_date, status, fine_amount))
    
    conn.commit()
    print(f"✅ Library transactions inserted!")

def main():
    print("=" * 60)
    print("School Management System Database Setup")
    print("=" * 60)
    
    conn = get_connection()
    
    try:
        # Create tables
        create_tables(conn)
        
        # Populate tables
        populate_students(conn, 150)
        populate_subjects(conn, 120)
        populate_staff(conn, 100)
        populate_classes(conn, 100)
        populate_enrollments(conn, 500)
        populate_grades(conn, 1000)
        populate_attendance(conn, 2000)
        populate_assignments(conn, 200)
        populate_library_books(conn, 300)
        populate_library_transactions(conn, 400)
        
        # Print summary
        cursor = conn.cursor()
        print("\n" + "=" * 60)
        print("DATABASE SUMMARY")
        print("=" * 60)
        
        tables = ['students', 'subjects', 'staff', 'classes', 'enrollments', 
                  'grades', 'attendance', 'assignments', 'library_books', 'library_transactions']
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table.capitalize():25} {count:>6} records")
        
        print("=" * 60)
        print("✅ Database setup complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
