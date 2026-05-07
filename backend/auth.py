from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random
import string
import re

from backend.database import MedicalReport, Notification, db, Doctor, Patient, Commune, Specialty
from backend.extensions import mail
from flask_mail import Message

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone):
    if not phone:
        return True
    pattern = r'^[0-9+\-\s]{8,20}$'
    return re.match(pattern, phone) is not None


def send_verification_email(user_email, code, user_name=""):
    try:
        msg = Message(
            subject='🔐 AI-Powered-Medic - Verify Your Email',
            recipients=[user_email],
            html=f'''
            <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 30px; border: 2px solid #007bbd; border-radius: 12px;">
                <h2 style="color: #004d73; text-align: center;">Welcome to AI-Powered-Medic!</h2>
                <p style="color: #0c2a3e; text-align: center;">Hello {user_name},</p>
                <p style="color: #0c2a3e; text-align: center;">Your verification code is:</p>
                <div style="background: linear-gradient(135deg, #f4f8fa, #e6f0f5); padding: 25px; text-align: center; font-size: 40px; letter-spacing: 12px; font-weight: bold; color: #007bbd; border-radius: 10px; margin: 20px 0;">
                {code}
                </div>
                <p style="color: #4c6c80; text-align: center;">This code will expire in <strong>10 minutes</strong>.</p>
                <hr>
                <p style="color: #7f8c8d; font-size: 12px; text-align: center;">AI-Powered-Medic - Your Medical Assistant</p>
            </div>'''
        )
        mail.send(msg)
        current_app.logger.info(f"Verification email sent to {user_email}")
        return True
    except Exception as e:
        current_app.logger.error(f"Email error: {e}")
        return False


def send_reset_email(user_email, code, user_name=""):
    try:
        msg = Message(
            subject='🔐 AI-Powered-Medic - Password Reset Code',
            recipients=[user_email],
            html=f'''
            <div style="font-family: Arial; max-width:500px; margin:auto; padding:30px; border:1px solid #3b82f6; border-radius:10px;">
                <h2 style="color:#2b5e4e;">Password Reset Request</h2>
                <p>Hello {user_name},</p>
                <p>Use the code below to reset your password:</p>
                <div style="background:#f0f0f0; padding:20px; text-align:center; font-size:36px; letter-spacing:10px; font-weight:bold; color:#2b5e4e;">
                    {code}
                </div>
                <p>This code will expire in <strong>10 minutes</strong>.</p>
                <hr>
                <p style="color:#666; font-size:12px;">AI-Powered-Medic - Your Medical Assistant</p>
            </div>'''
        )
        mail.send(msg)
        current_app.logger.info(f"Reset email sent to {user_email}")
        return True
    except Exception as e:
        current_app.logger.error(f"Reset email error: {e}")
        return False

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        communes = Commune.query.all()
        specialties = Specialty.query.all()
        doctors = Doctor.query.all()
        return render_template('auth/register.html', 
                             show_header=True,
                             doctors=doctors, 
                             communes=communes,
                             specialties=specialties)
    
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    plain_password = request.form.get('password', '')
    age = request.form.get('age')
    gender = request.form.get('gender')  
    phone = request.form.get('phone', '').strip()
    ssn = request.form.get('ssn', '').strip()
    role = request.form.get('role')
    commune_id = request.form.get('commune_id')
    specialty_id = request.form.get('specialty_id')
    doctor_ids = request.form.get('doctor_ids')
    clinic_name = request.form.get('clinic_name', '').strip()
    clinic_address = request.form.get('clinic_address', '').strip()
    clinic_phone = request.form.get('clinic_phone', '').strip()
    clinic_email = request.form.get('clinic_email', '').strip().lower()
    clinic_logo = request.form.get('clinic_logo', '').strip()

    if not name:
        flash('Name is required', 'danger')
        return redirect(url_for('auth.register'))
    
    if not validate_email(email):
        flash('Invalid email address', 'danger')
        return redirect(url_for('auth.register'))
    
    if not plain_password or len(plain_password) < 6:
        flash('Password must be at least 6 characters', 'danger')
        return redirect(url_for('auth.register'))
    
    if role == 'doctor':
        if Doctor.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('auth.register'))
    else:
        if Patient.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('auth.register'))
        if ssn and Patient.query.filter_by(ssn=ssn).first():
            flash('SSN already registered', 'danger')
            return redirect(url_for('auth.register'))
    
    password = generate_password_hash(plain_password)
    verification_code = generate_verification_code()
    code_expiry = datetime.utcnow() + timedelta(minutes=10)
    
    if role == 'doctor':
        user = Doctor(
            email=email,
            password=password, 
            name=name, 
            age=age if age else None, 
            phone=phone,
            commune_id=commune_id if commune_id else None, 
            specialty_id=specialty_id if specialty_id else None,
            is_verified=False, 
            verification_code=verification_code, 
            code_expiry=code_expiry,
            clinic_name=clinic_name,
            clinic_address=clinic_address,
            clinic_phone=clinic_phone,
            clinic_email=clinic_email,
            clinic_logo=clinic_logo
        )
        db.session.add(user)
        flash('Doctor account created successfully!', 'success')
        
    else:  
        user = Patient(
            email=email, 
            password=password, 
            name=name, 
            age=age if age else None, 
            gender=gender,
            phone=phone, 
            ssn=ssn,
            is_verified=False, 
            verification_code=verification_code, 
            code_expiry=code_expiry
        )
        db.session.add(user)
        db.session.flush()
        
        if doctor_ids and doctor_ids.strip():
            doctor_list = [int(id) for id in doctor_ids.split(',') if id.strip()]
            if doctor_list:
                doctors = Doctor.query.filter(Doctor.id.in_(doctor_list)).all()
                
                for doctor in doctors:
                    notification = Notification(
                        doctor_id=doctor.id,
                        patient_id=user.id,
                        type='patient_request',
                        message=f"Patient {user.name} has requested to add you as their doctor",
                        status='pending',
                        is_read=False
                    )
                    db.session.add(notification)
                
                current_app.logger.info(f"Patient {user.name} sent requests to {len(doctors)} doctors")
        
        flash('Patient account created successfully! Waiting for doctor approval.', 'success')
    
    db.session.commit()
    
    if send_verification_email(email, verification_code, name):
        flash('Verification code sent to your email! Please check your inbox.', 'info')
    else:
        flash('Account created but failed to send verification email. Please contact support.', 'warning')
    
    session['verify_email'] = email
    session['user_role'] = role
    
    return redirect(url_for('auth.verify'))

@auth_bp.route('/get-doctors')
def get_doctors():
    commune_id = request.args.get('commune_id', type=int)
    specialty_id = request.args.get('specialty_id', type=int)
    
    if not commune_id or not specialty_id:
        return jsonify({'doctors': []})
    
    doctors = Doctor.query.filter_by(
        commune_id=commune_id, 
        specialty_id=specialty_id,
        is_verified=True
    ).all()
    
    doctors_list = [{
        'id': d.id, 
        'name': d.name, 
        'specialty': d.specialty.name_en if d.specialty else 'General',
        'phone': d.phone or 'Not available'
    } for d in doctors]
    
    return jsonify({'doctors': doctors_list})


@auth_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        email = session.get('verify_email')
        
        if not email:
            flash('Session expired. Please register again.', 'danger')
            return redirect(url_for('auth.register'))
        
        user = Doctor.query.filter_by(email=email).first()
        if not user:
            user = Patient.query.filter_by(email=email).first()
        
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('auth.register'))
        
        if user.is_verified:
            flash('Account already verified! You can now login.', 'info')
            return redirect(url_for('auth.login'))
        
        if user.verification_code != code:
            flash('Invalid verification code. Please try again.', 'danger')
            return redirect(url_for('auth.verify'))
        
        if user.code_expiry < datetime.utcnow():
            flash('Code expired. Please request a new one.', 'danger')
            return redirect(url_for('auth.resend_code'))
        
        user.is_verified = True
        user.verification_code = None
        user.code_expiry = None
        db.session.commit()
        
        session.pop('verify_email', None)
        flash('Email verified successfully! You can now login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/verify.html', show_header=True)


@auth_bp.route('/resend-code')
def resend_code():
    email = session.get('verify_email')
    if not email:
        flash('Session expired', 'danger')
        return redirect(url_for('auth.register'))
    
    user = Doctor.query.filter_by(email=email).first()
    if not user:
        user = Patient.query.filter_by(email=email).first()
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('auth.register'))
    
    if user.is_verified:
        flash('Account already verified!', 'info')
        return redirect(url_for('auth.login'))
    
    new_code = generate_verification_code()
    user.verification_code = new_code
    user.code_expiry = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()
    
    if send_verification_email(email, new_code, user.name):
        flash('New verification code sent! Please check your email.', 'info')
    else:
        flash('Failed to send email. Please try again.', 'danger')
    
    return redirect(url_for('auth.verify'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        password = request.form.get('password', '')
        
        if user_type == 'patient':
            ssn = request.form.get('ssn', '').strip()
            if not ssn:
                flash('Please enter your SSN', 'danger')
                return redirect(url_for('auth.login'))
            
            user = Patient.query.filter_by(ssn=ssn).first()
            if not user:
                flash('No patient found with this SSN', 'danger')
                return redirect(url_for('auth.login'))
            
            if not user.password:
                flash('This patient does not have a login account. Please contact your doctor to create an account.', 'warning')
                return redirect(url_for('auth.login'))
            role = 'patient'
        else:
            email = request.form.get('email', '').strip().lower()
            if not email:
                flash('Please enter your email', 'danger')
                return redirect(url_for('auth.login'))
            
            user = Doctor.query.filter_by(email=email).first()
            if not user:
                flash('No doctor found with this email', 'danger')
                return redirect(url_for('auth.login'))
            role = 'doctor'
        
        if not check_password_hash(user.password, password):
            flash('Incorrect password. Please try again.', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_verified:
            flash('Please verify your email first. Check your inbox for the verification code.', 'warning')
            session['verify_email'] = user.email
            session['user_role'] = role
            return redirect(url_for('auth.verify'))
        
        login_user(user)
        session['user_role'] = role
        session.permanent = True
        flash(f'Welcome back, {user.name}!', 'success')
        
        if role == 'doctor':
            return redirect(url_for('doctor.doctor_dashboard'))
        return redirect(url_for('patient.patient_dashboard'))
    
    return render_template('auth/login.html', show_header=True)


@auth_bp.route('/logout')
@login_required
def logout():
    user_name = current_user.name
    logout_user()
    session.clear()
    flash(f'Goodbye, {user_name}! You have been logged out.', 'info')
    return redirect(url_for('home'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email:
            flash('Please enter your email', 'danger')
            return redirect(url_for('auth.forgot_password'))
        
        user = Doctor.query.filter_by(email=email).first()
        role = 'doctor'
        if not user:
            user = Patient.query.filter_by(email=email).first()
            role = 'patient'
        
        if user:
            reset_code = generate_verification_code()
            user.verification_code = reset_code
            user.code_expiry = datetime.utcnow() + timedelta(minutes=10)
            db.session.commit()
            
            if send_reset_email(email, reset_code, user.name):
                flash('Reset code sent to your email! Please check your inbox.', 'info')
                session['reset_email'] = email
                session['reset_role'] = role
                return redirect(url_for('auth.reset_password'))
            else:
                flash('Failed to send email. Please try again.', 'danger')
        else:
            flash('No account found with this email address', 'danger')
    
    return render_template('auth/forgot_password.html', show_header=True)


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    email = session.get('reset_email')
    role = session.get('reset_role')
    
    if not email or not role:
        flash('Session expired. Please start over.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if new_password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.reset_password'))
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return redirect(url_for('auth.reset_password'))
        
        user = Doctor.query.filter_by(email=email).first() if role == 'doctor' else Patient.query.filter_by(email=email).first()
        
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('auth.forgot_password'))
        
        if user.verification_code != code:
            flash('Invalid verification code', 'danger')
            return redirect(url_for('auth.reset_password'))
        
        if user.code_expiry < datetime.utcnow():
            flash('Code expired. Please request a new one.', 'danger')
            return redirect(url_for('auth.forgot_password'))
        
        user.password = generate_password_hash(new_password)
        user.verification_code = None
        user.code_expiry = None
        db.session.commit()
        
        session.pop('reset_email', None)
        session.pop('reset_role', None)
        flash('Password reset successful! You can now login with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', show_header=True, email=email)


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_password':
            old_password = request.form.get('old_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if not check_password_hash(current_user.password, old_password):
                flash('Old password is incorrect', 'danger')
                return redirect(url_for('auth.profile'))
            
            if new_password != confirm_password:
                flash('New passwords do not match', 'danger')
                return redirect(url_for('auth.profile'))
            
            if len(new_password) < 6:
                flash('Password must be at least 6 characters', 'danger')
                return redirect(url_for('auth.profile'))
            
            current_user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Password updated successfully', 'success')
        
        elif action == 'update_info':
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            gender = request.form.get('gender')  
            
            if name:
                current_user.name = name
            if phone:
                current_user.phone = phone
            if gender: 
                current_user.gender = gender
            
            if session.get('user_role') == 'patient':
                age = request.form.get('age')
                blood_type = request.form.get('blood_type')
                allergies = request.form.get('allergies')
                chronic_conditions = request.form.get('chronic_conditions')
                emergency_contact = request.form.get('emergency_contact')
                emergency_phone = request.form.get('emergency_phone')
                
                if age:
                    current_user.age = age
                if blood_type:
                    current_user.blood_type = blood_type
                if allergies:
                    current_user.allergies = allergies
                if chronic_conditions:
                    current_user.chronic_conditions = chronic_conditions
                if emergency_contact:
                    current_user.emergency_contact_name = emergency_contact
                if emergency_phone:
                    current_user.emergency_contact_phone = emergency_phone
            
            elif session.get('user_role') == 'doctor':
                age = request.form.get('age')
                commune_id = request.form.get('commune_id')
                specialty_id = request.form.get('specialty_id')
                clinic_name = request.form.get('clinic_name', '').strip()
                clinic_address = request.form.get('clinic_address', '').strip()
                clinic_phone = request.form.get('clinic_phone', '').strip()
                clinic_email = request.form.get('clinic_email', '').strip()
                
                if age:
                    current_user.age = age
                if commune_id:
                    current_user.commune_id = commune_id
                if specialty_id:
                    current_user.specialty_id = specialty_id
                if clinic_name:
                    current_user.clinic_name = clinic_name
                if clinic_address:
                    current_user.clinic_address = clinic_address
                if clinic_phone:
                    current_user.clinic_phone = clinic_phone
                if clinic_email:
                    current_user.clinic_email = clinic_email
            
            db.session.commit()
            flash('Profile information updated successfully', 'success')
    
    communes = Commune.query.all() if session.get('user_role') == 'doctor' else []
    specialties = Specialty.query.all() if session.get('user_role') == 'doctor' else []

    doctors = []
    if session.get('user_role') == 'patient':
        patient = Patient.query.get(current_user.id)
        if patient:
            print(f"Patient ID: {patient.id}")
            print(f"Doctors count: {patient.doctors.count()}")
            for doctor in patient.doctors:
                print(f"Doctor found: {doctor.name}")
            doctors_data = []
            for doctor in patient.doctors:
                # ✅ حساب كل التقارير (بدون تصفية حسب doctor_id)
                reports_count = MedicalReport.query.filter_by(
                    patient_id=patient.id
                ).count()

                doctors_data.append({
                    'doctor': doctor,
                    'reports_count': reports_count
                })
            doctors = doctors_data
            print(f"Doctors data: {doctors}")

    return render_template('profile.html', 
                         show_header=True, 
                         user=current_user,
                         communes=communes,
                         specialties=specialties,
                         doctors=doctors)

@auth_bp.route('/profile/delete', methods=['POST'])
@login_required
def delete_account():
    password = request.form.get('password', '')
    if not check_password_hash(current_user.password, password):
        flash('Incorrect password', 'danger')
        return redirect(url_for('auth.profile'))
    
    user_name = current_user.name
    db.session.delete(current_user)
    db.session.commit()
    logout_user()
    flash(f'Your account "{user_name}" has been deleted permanently.', 'info')
    return redirect(url_for('home'))

@auth_bp.route('/check-email')
def check_email():
    email = request.args.get('email', '').strip().lower()
    if not email:
        return jsonify({'exists': False})
    
    doctor_exists = Doctor.query.filter_by(email=email).first() is not None
    patient_exists = Patient.query.filter_by(email=email).first() is not None
    
    return jsonify({'exists': doctor_exists or patient_exists})


@auth_bp.route('/check-ssn')
def check_ssn():
    ssn = request.args.get('ssn', '').strip()
    if not ssn:
        return jsonify({'exists': False})
    
    exists = Patient.query.filter_by(ssn=ssn).first() is not None
    return jsonify({'exists': exists})