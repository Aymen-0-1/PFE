from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json
import re

from backend.database import Notification, db, Doctor, Patient, MedicalReport, Prescription, PrescriptionItem, Medicine, Specialty
from backend.extensions import mail

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')

def validate_phone(phone):
    if not phone:
        return True
    pattern = r'^[0-9+\-\s]{8,20}$'
    return re.match(pattern, phone) is not None

@doctor_bp.route('/dashboard')
@login_required
def doctor_dashboard():
    if session.get('user_role') != 'doctor':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))
    
    search_name = request.args.get('name', '')
    search_ssn = request.args.get('ssn', '')
    search_phone = request.args.get('phone', '')
    search_email = request.args.get('email', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    verified_status = request.args.get('verified', '')
    sort_by = request.args.get('sort', '')
    
    patients = current_user.patients.all() if hasattr(current_user.patients, 'all') else list(current_user.patients)
    
    filtered_patients = []
    
    for patient in patients:
        match = True
    
        if search_name and search_name.lower() not in patient.name.lower():
            match = False
        
        if match and search_ssn and search_ssn != patient.ssn:
            match = False
        
        if match and search_phone and search_phone not in str(patient.phone or ''):
            match = False
        
        if match and search_email and search_email.lower() not in (patient.email or '').lower():
            match = False
        
        if match and date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                if patient.created_at.date() < from_date.date():
                    match = False
            except:
                pass
        
        if match and date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d')
                if patient.created_at.date() > to_date.date():
                    match = False
            except:
                pass
        
        if match and verified_status:
            if verified_status == 'verified' and not patient.is_verified:
                match = False
            if verified_status == 'pending' and patient.is_verified:
                match = False
        
        if match:
            reports_count = MedicalReport.query.filter_by(patient_id=patient.id).count()
            latest_report = MedicalReport.query.filter_by(patient_id=patient.id)\
                              .order_by(MedicalReport.report_date.desc()).first()
            
            # حساب عدد الوصفات الطبية
            prescriptions_count = Prescription.query.filter_by(patient_id=patient.id).count()
            
            filtered_patients.append({
                'patient': patient,
                'reports_count': reports_count,
                'prescriptions_count': prescriptions_count,
                'latest_report': latest_report
            })
    
    if sort_by == 'name_asc':
        filtered_patients.sort(key=lambda x: x['patient'].name)
    elif sort_by == 'name_desc':
        filtered_patients.sort(key=lambda x: x['patient'].name, reverse=True)
    elif sort_by == 'age_asc':
        filtered_patients.sort(key=lambda x: x['patient'].age or 0)
    elif sort_by == 'age_desc':
        filtered_patients.sort(key=lambda x: x['patient'].age or 0, reverse=True)
    elif sort_by == 'date_desc':
        filtered_patients.sort(key=lambda x: x['patient'].created_at, reverse=True)
    elif sort_by == 'date_asc':
        filtered_patients.sort(key=lambda x: x['patient'].created_at)
    elif sort_by == 'reports_desc':
        filtered_patients.sort(key=lambda x: x['reports_count'], reverse=True)
    
    total_patients = len(filtered_patients)
    total_reports = sum(p['reports_count'] for p in filtered_patients)
    total_prescriptions = sum(p['prescriptions_count'] for p in filtered_patients)
    
    return render_template('doctor/doctor_dashboard.html',
                         show_header=True,
                         patients=filtered_patients,
                         total_patients=total_patients,
                         total_reports=total_reports,
                         total_prescriptions=total_prescriptions)

@doctor_bp.route('/patient/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        from backend.auth import generate_verification_code, send_verification_email
        from werkzeug.security import generate_password_hash
        
        name = request.form.get('name', '').strip()
        age = request.form.get('age')
        gender = request.form.get('gender')
        phone = request.form.get('phone', '').strip()
        ssn = request.form.get('ssn', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        create_account = request.form.get('create_account') == 'yes'
        
        if not name:
            flash('Patient name is required', 'danger')
            return redirect(url_for('doctor.add_patient'))
        
        if create_account:
            if not ssn:
                flash('SSN is required to create an account', 'danger')
                return redirect(url_for('doctor.add_patient'))
            
            if not password or len(password) < 6:
                flash('Password must be at least 6 characters', 'danger')
                return redirect(url_for('doctor.add_patient'))
            
            if email and Patient.query.filter_by(email=email).first():
                flash(f'Patient with email {email} already exists', 'danger')
                return redirect(url_for('doctor.add_patient'))
            
            if Patient.query.filter_by(ssn=ssn).first():
                flash(f'Patient with SSN {ssn} already exists', 'danger')
                return redirect(url_for('doctor.add_patient'))
            
            verification_code = generate_verification_code()
            code_expiry = datetime.utcnow() + timedelta(minutes=10)
            
            patient = Patient(
                name=name, age=age if age else None, phone=phone, gender=gender,
                email=email if email else None, ssn=ssn,
                password=generate_password_hash(password), is_verified=False,
                verification_code=verification_code, code_expiry=code_expiry
            )
            db.session.add(patient)
            db.session.flush()
            patient.doctors.append(current_user)
            db.session.commit()
            
            send_verification_email(email, verification_code, name)
            flash(f'Account created for {name}. Verification code sent to {email}', 'success')
        else:
            patient = Patient(
                name=name, age=age if age else None, phone=phone, gender=gender,
                ssn=ssn if ssn else None, email=None, password=None
            )
            db.session.add(patient)
            db.session.flush()
            patient.doctors.append(current_user)
            db.session.commit()
            flash(f'Patient {name} added to your list (no login account)', 'info')
        
        return redirect(url_for('doctor.doctor_dashboard'))
    
    return render_template('doctor/add_patient.html', show_header=True)


@doctor_bp.route('/patient/<int:patient_id>/reports')
@login_required
def patient_reports(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    if current_user not in patient.doctors:
        flash('You don\'t have access to this patient\'s reports', 'danger')
        return redirect(url_for('doctor.doctor_dashboard'))
    
    reports = MedicalReport.query.filter_by(patient_id=patient_id)\
                .order_by(MedicalReport.report_date.desc()).all()
    prescriptions = Prescription.query.filter_by(patient_id=patient_id)\
                    .order_by(Prescription.created_at.desc()).all()
    
    return render_template('patient/patient_report.html',
                         show_header=True, 
                         patient=patient, 
                         reports=reports,
                         prescriptions=prescriptions)


@doctor_bp.route('/patient/<int:patient_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    if current_user not in patient.doctors:
        flash('You don\'t have permission to edit this patient', 'danger')
        return redirect(url_for('doctor.doctor_dashboard'))
    
    if request.method == 'POST':
        try:
            patient.name = request.form.get('name', '').strip()
            patient.age = request.form.get('age', type=int) if request.form.get('age') else None
            patient.gender = request.form.get('gender') or None  
            patient.phone = request.form.get('phone', '').strip()
            patient.email = request.form.get('email', '').strip().lower() or None
            
            if request.form.get('blood_type'):
                patient.blood_type = request.form.get('blood_type')
            if request.form.get('allergies'):
                patient.allergies = request.form.get('allergies')
            if request.form.get('chronic_conditions'):
                patient.chronic_conditions = request.form.get('chronic_conditions')
            if request.form.get('emergency_contact'):
                patient.emergency_contact_name = request.form.get('emergency_contact')
            if request.form.get('emergency_phone'):
                patient.emergency_contact_phone = request.form.get('emergency_phone')
            
            db.session.commit()
            flash(f'Patient {patient.name} updated successfully', 'success')
            return redirect(url_for('doctor.patient_reports', patient_id=patient.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating patient: {str(e)}', 'danger')
    
    return render_template('doctor/edit_patient.html', patient=patient, show_header=True)


@doctor_bp.route('/patient/<int:patient_id>/analyze')
@login_required
def analyze_patient_report(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    if current_user not in patient.doctors:
        flash('You don\'t have access to this patient', 'danger')
        return redirect(url_for('doctor.doctor_dashboard'))
    
    return render_template('doctor/doctor_analyze.html', patient=patient)


@doctor_bp.route('/patient/<int:patient_id>/remove', methods=['POST'])
@login_required
def remove_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    if current_user in patient.doctors:
        patient.doctors.remove(current_user)
        db.session.commit()
        flash(f'Patient {patient.name} removed from your list', 'success')
    else:
        flash('This patient is not in your list', 'danger')
    
    return redirect(url_for('doctor.doctor_dashboard'))


@doctor_bp.route('/patient/<int:patient_id>/add-prescription', methods=['GET', 'POST'])
@login_required
def add_prescription(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    if current_user not in patient.doctors:
        flash('You don\'t have permission to prescribe for this patient', 'danger')
        return redirect(url_for('doctor.doctor_dashboard'))
    
    if request.method == 'POST':
        try:
            diagnosis = request.form.get('diagnosis', '').strip()
            notes = request.form.get('notes', '').strip()
            medicine_ids = request.form.getlist('medicine_id[]')
            dosages = request.form.getlist('dosage[]')
            frequencies = request.form.getlist('frequency[]')
            durations = request.form.getlist('duration[]')
            instructions = request.form.getlist('instructions[]')
            
            has_medicine = any(mid and mid.strip() for mid in medicine_ids)
            if not has_medicine:
                flash('Please add at least one medication', 'danger')
                return redirect(url_for('doctor.add_prescription', patient_id=patient.id))
            
            prescription = Prescription(
                patient_id=patient.id,
                doctor_id=current_user.id,
                diagnosis=diagnosis,
                notes=notes
            )
            db.session.add(prescription)
            db.session.flush()
            
            items_added = 0
            for i in range(len(medicine_ids)):
                if medicine_ids[i] and medicine_ids[i].strip() and dosages[i] and dosages[i].strip():
                    try:
                        item = PrescriptionItem(
                            prescription_id=prescription.id,
                            medicine_id=int(medicine_ids[i]),
                            dosage=dosages[i],
                            frequency=frequencies[i] if i < len(frequencies) else None,
                            duration=durations[i] if i < len(durations) else None,
                            instructions=instructions[i] if i < len(instructions) else None
                        )
                        db.session.add(item)
                        items_added += 1
                    except (ValueError, IndexError):
                        continue
            
            if items_added == 0:
                db.session.rollback()
                flash('No valid medications added', 'danger')
                return redirect(url_for('doctor.add_prescription', patient_id=patient.id))
            
            db.session.commit()
            flash(f'Prescription created successfully with {items_added} medication(s)', 'success')
            return redirect(url_for('doctor.patient_reports', patient_id=patient.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating prescription: {e}")
            flash(f'Error creating prescription: {str(e)}', 'danger')
            return redirect(url_for('doctor.add_prescription', patient_id=patient.id))
    
    medicines = Medicine.query.all()
    medicines_json = [{
        'id': m.id,
        'scientific_name': m.scientific_name,
        'commercial_name': m.commercial_name,
        'category': m.category,
        'common_dosages': json.loads(m.common_dosages) if m.common_dosages else []
    } for m in medicines]
    
    patient_reports = MedicalReport.query.filter_by(patient_id=patient.id)\
                        .order_by(MedicalReport.report_date.desc()).all()
    
    return render_template('doctor/add_prescription.html',
                         show_header=True,
                         patient=patient,
                         medicines=medicines,
                         medicines_json=medicines_json,
                         patient_reports=patient_reports,
                         datetime=datetime)



@doctor_bp.route('/api/patients')
@login_required
def api_get_patients():
    if session.get('user_role') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    patients = current_user.patients.all() if hasattr(current_user.patients, 'all') else list(current_user.patients)
    
    patients_list = [{
        'id': p.id,
        'name': p.name,
        'age': p.age,
        'phone': p.phone,
        'ssn': p.ssn,
        'email': p.email,
        'has_account': p.has_account() if hasattr(p, 'has_account') else bool(p.email)
    } for p in patients]
    
    return jsonify({'patients': patients_list})


@doctor_bp.route('/api/stats')
@login_required
def api_get_stats():
    if session.get('user_role') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    patients = current_user.patients.all() if hasattr(current_user.patients, 'all') else list(current_user.patients)
    total_patients = len(patients)
    
    total_reports = MedicalReport.query.filter(
        MedicalReport.patient_id.in_([p.id for p in patients])
    ).count()
    
    total_prescriptions = Prescription.query.filter_by(doctor_id=current_user.id).count()
    
    # عدد المرضى النشطين (لديهم تقارير)
    active_patients = 0
    for patient in patients:
        if MedicalReport.query.filter_by(patient_id=patient.id).first():
            active_patients += 1
    
    return jsonify({
        'total_patients': total_patients,
        'total_reports': total_reports,
        'total_prescriptions': total_prescriptions,
        'active_patients': active_patients
    })


@doctor_bp.route('/api/patient/<int:patient_id>/summary')
@login_required
def api_patient_summary(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    if current_user not in patient.doctors:
        return jsonify({'error': 'Unauthorized'}), 403
    
    reports = MedicalReport.query.filter_by(patient_id=patient_id).all()
    prescriptions = Prescription.query.filter_by(patient_id=patient_id).all()
    
    all_conditions = set()
    for report in reports:
        for condition in report.get_conditions():
            if isinstance(condition, dict):
                all_conditions.add(condition.get('name', str(condition)))
            else:
                all_conditions.add(str(condition))
    
    return jsonify({
        'patient': {
            'id': patient.id,
            'name': patient.name,
            'age': patient.age,
            'phone': patient.phone,
            'blood_type': patient.blood_type
        },
        'total_reports': len(reports),
        'total_prescriptions': len(prescriptions),
        'conditions': list(all_conditions),
        'last_visit': reports[0].report_date.isoformat() if reports else None
    })

@doctor_bp.route('/stats')
@login_required
def doctor_stats():
    if session.get('user_role') != 'doctor':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))
    
    patients = current_user.patients.all() if hasattr(current_user.patients, 'all') else list(current_user.patients)
    
    total_patients = len(patients)
    total_reports = 0
    total_prescriptions = 0
    active_patients = 0
    
    from collections import defaultdict
    reports_by_month = defaultdict(int)
    conditions_count = defaultdict(int)
    
    for patient in patients:
        reports = MedicalReport.query.filter_by(patient_id=patient.id).all()
        prescriptions = Prescription.query.filter_by(patient_id=patient.id).all()
        
        total_reports += len(reports)
        total_prescriptions += len(prescriptions)
        
        if len(reports) > 0:
            active_patients += 1
        
        for report in reports:
            month_key = report.report_date.strftime('%b %Y')
            reports_by_month[month_key] += 1
            
            for condition in report.get_conditions():
                if isinstance(condition, dict):
                    cond_name = condition.get('name', str(condition))
                else:
                    cond_name = str(condition)
                if cond_name and cond_name != 'No specific conditions identified':
                    conditions_count[cond_name] += 1
    
    months = list(reports_by_month.keys())
    reports_per_month = list(reports_by_month.values())
    
    top_conditions = [{'name': k, 'count': v} for k, v in sorted(conditions_count.items(), key=lambda x: x[1], reverse=True)[:5]]
    
    patients_data = []
    for patient in patients:
        reports_count = MedicalReport.query.filter_by(patient_id=patient.id).count()
        prescriptions_count = Prescription.query.filter_by(patient_id=patient.id).count()
        latest_report = MedicalReport.query.filter_by(patient_id=patient.id).order_by(MedicalReport.report_date.desc()).first()
        
        patients_data.append({
            'patient': patient,
            'reports_count': reports_count,
            'prescriptions_count': prescriptions_count,
            'latest_report': latest_report
        })
    
    return render_template('doctor/doctor_stats.html',
                         show_header=True,
                         patients=patients_data,
                         total_patients=total_patients,
                         total_reports=total_reports,
                         total_prescriptions=total_prescriptions,
                         active_patients=active_patients,
                         months=months,
                         reports_per_month=reports_per_month,
                         top_conditions=top_conditions)


@doctor_bp.route('/stats/export')
@login_required
def export_stats():
    if session.get('user_role') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    patients = current_user.patients.all() if hasattr(current_user.patients, 'all') else list(current_user.patients)
    
    export_data = []
    for patient in patients:
        reports = MedicalReport.query.filter_by(patient_id=patient.id).all()
        prescriptions = Prescription.query.filter_by(patient_id=patient.id).all()
        
        export_data.append({
            'patient_id': patient.id,
            'patient_name': patient.name,
            'patient_age': patient.age,
            'patient_phone': patient.phone,
            'patient_ssn': patient.ssn,
            'reports_count': len(reports),
            'prescriptions_count': len(prescriptions),
            'reports': [{
                'date': r.report_date.isoformat(),
                'conditions': r.get_conditions(),
                'medications': r.get_medications(),
                'alerts': r.get_alerts(),
                'summary': r.summary
            } for r in reports],
            'prescriptions': [{
                'date': p.created_at.isoformat(),
                'diagnosis': p.diagnosis,
                'medications': [{
                    'name': item.medicine.commercial_name if item.medicine else 'Unknown',
                    'dosage': item.dosage,
                    'frequency': item.frequency
                } for item in p.items]
            } for p in prescriptions]
        })
    
    response = jsonify({
        'export_date': datetime.now().isoformat(),
        'doctor_name': current_user.name,
        'doctor_email': current_user.email,
        'total_patients': len(patients),
        'data': export_data
    })
    
    response.headers['Content-Disposition'] = 'attachment; filename=statistics_export.json'
    return response

@doctor_bp.route('/api/notifications')
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(
        doctor_id=current_user.id, 
        status='pending'
    ).order_by(Notification.created_at.desc()).all()
    
    notifications_data = [{
        'id': n.id,
        'patient_id': n.patient_id,
        'patient_name': n.patient.name,
        'message': n.message,
        'created_at': n.created_at.strftime('%d/%m/%Y %H:%M'),
        'status': n.status
    } for n in notifications]
    
    unread_count = Notification.query.filter_by(
        doctor_id=current_user.id, 
        is_read=False,
        status='pending'
    ).count()
    
    return jsonify({
        'notifications': notifications_data,
        'unread_count': unread_count
    })


@doctor_bp.route('/api/notifications/<int:notification_id>/respond', methods=['POST'])
@login_required
def respond_to_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.doctor_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    action = data.get('action')  
    
    if action == 'accept':
        patient = Patient.query.get(notification.patient_id)
        if patient not in current_user.patients:
            current_user.patients.append(patient)
        
        notification.status = 'accepted'
        
        patient.is_verified = True
        
        patient_notification = Notification(
            doctor_id=current_user.id,
            patient_id=patient.id,
            type='request_accepted',
            message=f"Dr. {current_user.name} has accepted your request",
            status='accepted',
            is_read=False
        )
        db.session.add(patient_notification)
        
    elif action == 'reject':
        notification.status = 'rejected'
        
        patient_notification = Notification(
            doctor_id=current_user.id,
            patient_id=notification.patient_id,
            type='request_rejected',
            message=f"Dr. {current_user.name} has declined your request",
            status='rejected',
            is_read=False
        )
        db.session.add(patient_notification)
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Request {action}ed'})