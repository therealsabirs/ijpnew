from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import os
import io
from werkzeug.utils import secure_filename
import csv
from flask import Response

app = Flask(__name__)
#app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def connect_db():
    return psycopg2.connect(
        dbname="defaultdb",
        user="avnadmin",
        password="AVNS_wcoTLLfY4Czw5rBQnbt",
        host="postgres-beingmenie2898.h.aivencloud.com",
        port="11554",
        sslmode="require"
    )


@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['user_type']
        
        conn = connect_db()
        cur = conn.cursor()

        if user_type == 'HR':
            cur.execute("SELECT id, password FROM hr WHERE username = %s", (username,))
        else:
            cur.execute("SELECT id, password FROM employees WHERE username = %s", (username,))
        
        user = cur.fetchone()
        if user and user[1] == password:
            session['user_id'] = user[0]
            session['user_type'] = user_type
            if user_type == 'HR':
                return redirect(url_for('hr_dashboard'))
            else:
                return redirect(url_for('employee_dashboard'))
        else:
            flash("Invalid credentials, please try again.", "danger")
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/hr_dashboard', methods=['GET', 'POST'])
def hr_dashboard():
    if 'user_type' in session and session['user_type'] == 'HR':
        conn = connect_db()
        cur = conn.cursor()

        # If it's a POST request, add a new job
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            date = request.form['date']
            eligibility_criteria = request.form['eligibility_criteria']
            number_of_positions = request.form['number_of_positions']
            last_date_to_apply = request.form['last_date_to_apply']
            status = 'active'

            cur.execute("""
                INSERT INTO jobs (title, description, date, eligibility_criteria, number_of_positions, last_date_to_apply, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (title, description, date, eligibility_criteria, number_of_positions, last_date_to_apply, status))
            conn.commit()

            flash("Job added successfully!", "success")
        
        # Capture search query from GET request
        search_query = request.args.get('search_query')

        if search_query:
            # Search for jobs by title (case-insensitive)
            cur.execute("SELECT * FROM jobs WHERE title ILIKE %s", ('%' + search_query + '%',))
        else:
            # Display all jobs if no search query is provided
            cur.execute("SELECT * FROM jobs")
        
        jobs = cur.fetchall()
        cur.close()
        conn.close()
        
        return render_template('hr_dashboard.html', jobs=jobs, search_query=search_query)
    else:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('index'))


@app.route('/change_job_status/<int:job_id>/<string:new_status>')
def change_job_status(job_id, new_status):
    if 'user_type' in session and session['user_type'] == 'HR':
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("UPDATE jobs SET status = %s WHERE id = %s", (new_status, job_id))
        conn.commit()
        cur.close()
        conn.close()
        flash(f"Job status updated to {new_status}.", "success")
        return redirect(url_for('hr_dashboard'))
    else:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('index'))

@app.route('/employee_dashboard')
def employee_dashboard():
    if 'user_type' in session and session['user_type'] == 'employee':
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM jobs WHERE status = 'active' AND last_date_to_apply::date >= CURRENT_DATE")
        jobs = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('employee_dashboard.html', jobs=jobs)
    else:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('index'))

@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
def apply_for_job(job_id):
    if 'user_type' in session and session['user_type'] == 'employee':
        if request.method == 'POST':
            employee_code = request.form['employee_code']
            name = request.form['name']
            role_type = request.form['role_type']
            designation = request.form['designation']
            department_name = request.form['department_name']
            supervisor_name = request.form['supervisor_name']
            date_of_joining = request.form['date_of_joining']
            resume = request.files['resume']
            
            if resume:
                resume_filename = secure_filename(resume.filename)
                resume_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_filename)
                resume.save(resume_path)
            else:
                resume_filename = None

            conn = connect_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO applications (employee_id, job_id, employee_code, name, role_type, designation, department_name, supervisor_name, date_of_joining, resume)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (session['user_id'], job_id, employee_code, name, role_type, designation, department_name, supervisor_name, date_of_joining, resume_filename))
            conn.commit()
            cur.close()
            conn.close()
            
            flash("Application submitted successfully!", "success")
            return redirect(url_for('employee_dashboard'))
        
        return render_template('apply_form.html', job_id=job_id)
    else:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('index'))
'''
@app.route('/view_applications/<int:job_id>')
def view_applications(job_id):
    if 'user_type' in session and session['user_type'] == 'HR':
        conn = connect_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT e.id, e.username, a.employee_code, a.name, a.role_type, a.designation, a.department_name, a.supervisor_name, a.date_of_joining, a.resume
            FROM applications a
            JOIN employees e ON a.employee_id = e.id
            WHERE a.job_id = %s
        """, (job_id,))
        applications = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('view_applications.html', applications=applications)
    else:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('index'))
'''
'''
@app.route('/export_applications', methods=['POST'])
def export_applications():
    if 'user_type' in session and session['user_type'] == 'HR':
        conn = connect_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT a.id, j.title, e.username, a.employee_code, a.name, a.role_type, a.designation, a.department_name, a.supervisor_name, a.date_of_joining, a.resume
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN employees e ON a.employee_id = e.id
        """)
        applications = cur.fetchall()

        cur.close()
        conn.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Job Title', 'Employee Username', 'Employee Code', 'Name', 'Role Type', 'Designation', 'Department Name', 'Supervisor Name', 'Date of Joining', 'Resume'])
        for app in applications:
            writer.writerow(app)

        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=applications.csv"}
        )
    else:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('index'))
    '''
@app.route('/edit_job/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    if 'user_type' in session and session['user_type'] == 'HR':
        conn = connect_db()
        cur = conn.cursor()

        # Fetch job details
        cur.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
        job = cur.fetchone()

        if request.method == 'POST':
            # Get updated details from the form
            title = request.form['title']
            description = request.form['description']
            date = request.form['date']
            eligibility_criteria = request.form['eligibility_criteria']
            number_of_positions = request.form['number_of_positions']
            last_date_to_apply = request.form['last_date_to_apply']
            status = request.form['status']

            # Update the job in the database
            cur.execute("""
                UPDATE jobs 
                SET title = %s, description = %s, date = %s, eligibility_criteria = %s, 
                    number_of_positions = %s, last_date_to_apply = %s, status = %s 
                WHERE id = %s
            """, (title, description, date, eligibility_criteria, number_of_positions, last_date_to_apply, status, job_id))
            
            conn.commit()
            cur.close()
            conn.close()

            flash("Job updated successfully!", "success")
            return redirect(url_for('hr_dashboard'))
        else:
            cur.close()
            conn.close()
            return render_template('edit_job.html', job=job)
    else:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('index'))

@app.route('/view_job/<int:job_id>', methods=['GET'])
def view_job(job_id):
    if 'user_type' in session and session['user_type'] == 'employee':
        conn = connect_db()
        cur = conn.cursor()

        # Fetch the job details
        cur.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
        job = cur.fetchone()
        cur.close()
        conn.close()

        # Check if job exists
        if job:
            return render_template('view_job.html', job=job)
        else:
            flash("Job not found!", "danger")
            return redirect(url_for('employee_dashboard'))
    else:
        # If user type is not Employee, redirect to the index (login) page
        flash("Unauthorized access!", "danger")
        return redirect(url_for('index'))

@app.route('/view_applications/<int:job_id>')
def view_applications(job_id):
    if 'user_type' in session and session['user_type'] == 'HR':
        conn = connect_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT e.id, e.username, a.employee_code, a.name, a.role_type, a.designation, a.department_name, a.supervisor_name, a.date_of_joining, a.resume
            FROM applications a
            JOIN employees e ON a.employee_id = e.id
            WHERE a.job_id = %s
        """, (job_id,))
        applications = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Pass job_id to the template
        return render_template('view_applications.html', applications=applications, job_id=job_id)
    else:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('index'))
@app.route('/export_applications/<int:job_id>', methods=['POST'])
def export_applications(job_id):
    if 'user_type' in session and session['user_type'] == 'HR':
        conn = connect_db()
        cur = conn.cursor()

        # Fetch applications for the specific job
        cur.execute("""
            SELECT a.id, j.title, e.username, a.employee_code, a.name, a.role_type, a.designation, a.department_name, a.supervisor_name, a.date_of_joining, a.resume
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN employees e ON a.employee_id = e.id
            WHERE a.job_id = %s
        """, (job_id,))
        applications = cur.fetchall()

        cur.close()
        conn.close()

        # Create CSV file in-memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Job Title', 'Employee Username', 'Employee Code', 'Name', 'Role Type', 'Designation', 'Department Name', 'Supervisor Name', 'Date of Joining', 'Resume'])
        for app in applications:
            writer.writerow(app)

        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=applications_job_{job_id}.csv"}
        )
    else:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('index'))



@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))






from flask import Flask, render_template, request, redirect, url_for, flash
import random
import string
from flask_mail import Mail, Message
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'swag.140408@gmail.com'
app.config['MAIL_PASSWORD'] = 'qfarnksnjzjybzxq' 
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)
# Store OTPs temporarily (you should store them securely in the database in a real-world app)
otp_storage = {}
# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://avnadmin:AVNS_wcoTLLfY4Czw5rBQnbt@postgres-beingmenie2898.h.aivencloud.com:11554/defaultdb?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)


class HR(db.Model):
    __tablename__ = 'hr'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True)


class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True)



@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        # Query the HR and Employee tables
        hr_user = HR.query.filter_by(email=email).first()
        emp_user = Employee.query.filter_by(email=email).first()

        if hr_user or emp_user:
            # Generate OTP
            otp = random.randint(1000, 9999)
            otp_storage[email] = otp
            print(f"OTP for {email}: {otp}")  # For debugging; remove in production

            # Send OTP via email (see Step 3 for email setup)
            msg = Message("Password Reset OTP", sender="your-email@gmail.com", recipients=[email])
            msg.body = f"Your OTP for password reset is: {otp}"
            try:
                mail.send(msg)
                flash('An OTP has been sent to your email.', 'info')
                return redirect(url_for('reset_password', email=email))
            except Exception as e:
                flash(f"Error sending email: {str(e)}", 'danger')
        else:
            flash("Email not found in the system.", "danger")
    
    return render_template('forgot_password.html')





@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    email = request.args.get('email')  # Retrieve email from query parameter

    if request.method == 'POST':
        entered_otp = request.form['otp']
        new_password = request.form['new_password']

        if email:  # Ensure the email is not empty
            # Check if OTP is valid
            if email in otp_storage and otp_storage[email] == int(entered_otp):
                # Update password logic here
                hr_user = HR.query.filter_by(email=email).first()
                emp_user = Employee.query.filter_by(email=email).first()

                if hr_user:
                    hr_user.password = new_password
                    db.session.commit()
                    flash('Password updated successfully!', 'success')
                elif emp_user:
                    emp_user.password = new_password
                    db.session.commit()
                    flash('Password updated successfully!', 'success')
                else:
                    flash('User not found.', 'danger')

                return redirect(url_for('login'))
            else:
                flash('Invalid OTP', 'danger')
        else:
            flash('Email not provided.', 'danger')

    return render_template('reset_password.html', email=email)  # Pass email to the template












if __name__ == '__main__':
    app.run(debug=True)
    