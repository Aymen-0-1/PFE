from flask import Blueprint, render_template, redirect, url_for, flash, session, request, jsonify, current_app, json
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from backend.database import Notification, db, MedicalReport, Prescription, PrescriptionItem, Doctor, Patient

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

def get_patient_doctors(patient):
    return patient.doctors.all() if hasattr(patient.doctors, 'all') else list(patient.doctors)


def get_patient_stats(patient_id):
    reports_count = MedicalReport.query.filter_by(patient_id=patient_id).count()
    prescriptions_count = Prescription.query.filter_by(patient_id=patient_id).count()
    
    patient = Patient.query.get(patient_id)
    doctors_count = len(get_patient_doctors(patient)) if patient else 0
    
    latest_report = MedicalReport.query.filter_by(patient_id=patient_id)\
                      .order_by(MedicalReport.report_date.desc()).first()
    
    alerts_count = 0
    reports = MedicalReport.query.filter_by(patient_id=patient_id).all()
    for report in reports:
        alerts_count += len(report.get_alerts())
    
    return {
        'reports_count': reports_count,
        'prescriptions_count': prescriptions_count,
        'doctors_count': doctors_count,
        'alerts_count': alerts_count,
        'latest_report_date': latest_report.report_date if latest_report else None
    }


@patient_bp.route('/dashboard')
@login_required
def patient_dashboard():
    if session.get('user_role') != 'patient':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))
    
    reports = MedicalReport.query.filter_by(patient_id=current_user.id)\
                .order_by(MedicalReport.report_date.desc()).all()
    
    prescriptions = Prescription.query.filter_by(patient_id=current_user.id)\
                     .order_by(Prescription.created_at.desc()).all()
    
    doctors = get_patient_doctors(current_user)
    
    stats = get_patient_stats(current_user.id)
    
    all_alerts = []
    for report in reports[:5]:  
        alerts = report.get_alerts()
        for alert in alerts:
            if isinstance(alert, dict):
                all_alerts.append({
                    'message': alert.get('message', str(alert)),
                    'date': report.report_date,
                    'report_id': report.id
                })
            else:
                all_alerts.append({
                    'message': str(alert),
                    'date': report.report_date,
                    'report_id': report.id
                })
    
    recent_reports = reports[:3]
    
    return render_template('patient/patient_dashboard.html',
                         show_header=True,
                         patient=current_user,
                         reports=reports,
                         recent_reports=recent_reports,
                         prescriptions=prescriptions,
                         doctors=doctors,
                         stats=stats,
                         all_alerts=all_alerts,
                         datetime=datetime)

@patient_bp.route('/analyze-report')
@login_required
def analyze_my_report():
    """صفحة تحليل التقرير للمريض"""
    if session.get('user_role') != 'patient':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))
    
    patient = Patient.query.get(current_user.id)
    
    return render_template('patient/patient_analyze.html', patient=patient)


@patient_bp.route('/api/analyze-report', methods=['POST'])
@login_required
def api_analyze_my_report():
    """API لتحليل وحفظ تقرير المريض"""
    if session.get('user_role') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        patient_id = current_user.id
        
        report = MedicalReport(
            patient_id=patient_id,
            doctor_id=None,  # المريض رفعه بنفسه، لا يوجد طبيب
            conditions=json.dumps(data.get('conditions', [])),
            medications=json.dumps(data.get('medications', [])),
            alerts=json.dumps(data.get('alerts', [])),
            summary=data.get('summary', '')
        )
        
        image_paths = data.get('image_paths', [])
        report.set_image_paths(image_paths)
        
        db.session.add(report)
        db.session.commit()
        
        return jsonify({'success': True, 'id': report.id})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@patient_bp.route('/reports')
@login_required
def patient_reports_list():
    if session.get('user_role') != 'patient':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))
    
    query = MedicalReport.query.filter_by(patient_id=current_user.id)
    reports = query.all()
    stats = {
        'total': len(reports),
        'with_conditions': sum(1 for r in reports if r.conditions and r.conditions != '[]'),
        'with_medications': sum(1 for r in reports if r.medications and r.medications != '[]')
    }
    return render_template('patient/patient_report.html',
                         show_header=True,
                         patient=current_user,
                         reports=reports,
                         stats=stats,
                         datetime=datetime)


@patient_bp.route('/report/<int:report_id>')
@login_required
def view_report(report_id):
    report = MedicalReport.query.get_or_404(report_id)
    
    if report.patient_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('patient.patient_dashboard'))
    
    doctor = None
    if report.doctor_id:
        doctor = Doctor.query.get(report.doctor_id)
    
    related_prescriptions = Prescription.query.filter_by(
        patient_id=current_user.id
    ).order_by(Prescription.created_at.desc()).limit(3).all()
    
    return render_template('report/view_report.html',
                         show_header=True,
                         report=report,
                         doctor=doctor,
                         related_prescriptions=related_prescriptions,
                         datetime=datetime)


from datetime import datetime, timedelta

@patient_bp.route('/prescriptions')
@login_required
def patient_prescriptions():
    """عرض جميع وصفات المريض"""
    if session.get('user_role') != 'patient':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))
    
    prescriptions = Prescription.query.filter_by(patient_id=current_user.id)\
                       .order_by(Prescription.created_at.desc()).all()
    
    today = datetime.utcnow()
    active_count = 0
    expired_count = 0
    
    for p in prescriptions:
        if not p.is_active or (p.created_at < today - timedelta(days=30)):
            expired_count += 1
        else:
            active_count += 1
    
    return render_template('patient/patient_prescriptions.html',
                         show_header=True,
                         prescriptions=prescriptions,
                         active_count=active_count,
                         expired_count=expired_count,
                         datetime=datetime,
                         timedelta=timedelta)


@patient_bp.route('/prescription/<int:prescription_id>/view')
@login_required
def view_prescription(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    
    if prescription.patient_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('patient.patient_dashboard'))
    
    doctor = Doctor.query.get(prescription.doctor_id)
    
    return render_template('patient/view_prescription.html',
                         show_header=True,
                         prescription=prescription,
                         doctor=doctor,
                         datetime=datetime)


@patient_bp.route('/doctors')
@login_required
def patient_doctors():
    if session.get('user_role') != 'patient':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))
    
    doctors = get_patient_doctors(current_user)
    
    doctors_data = []
    for doctor in doctors:
        reports_count = MedicalReport.query.filter_by(
            patient_id=current_user.id, 
            doctor_id=doctor.id
        ).count()
        
        prescriptions_count = Prescription.query.filter_by(
            patient_id=current_user.id,
            doctor_id=doctor.id
        ).count()
        
        doctors_data.append({
            'doctor': doctor,
            'reports_count': reports_count,
            'prescriptions_count': prescriptions_count
        })
    
    return render_template('patient/patient_doctors.html',
                         show_header=True,
                         doctors=doctors_data,
                         datetime=datetime)


@patient_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if session.get('user_role') != 'patient':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        try:
            current_user.name = request.form.get('name', current_user.name)
            current_user.phone = request.form.get('phone', current_user.phone)
            current_user.email = request.form.get('email', current_user.email) or None
            
            current_user.blood_type = request.form.get('blood_type', current_user.blood_type)
            current_user.allergies = request.form.get('allergies', current_user.allergies)
            current_user.chronic_conditions = request.form.get('chronic_conditions', current_user.chronic_conditions)
            current_user.current_medications = request.form.get('current_medications', current_user.current_medications)
            
            current_user.emergency_contact_name = request.form.get('emergency_contact_name', current_user.emergency_contact_name)
            current_user.emergency_contact_phone = request.form.get('emergency_contact_phone', current_user.emergency_contact_phone)
            current_user.emergency_contact_relation = request.form.get('emergency_contact_relation', current_user.emergency_contact_relation)
            
            db.session.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for('patient.patient_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating profile: {e}")
            flash(f'Error updating profile: {str(e)}', 'danger')
    
    return render_template('patient/edit_profile.html',
                         show_header=True,
                         patient=current_user)


@patient_bp.route('/api/stats')
@login_required
def api_get_stats():
    if session.get('user_role') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    stats = get_patient_stats(current_user.id)
    
    return jsonify({
        'reports_count': stats['reports_count'],
        'prescriptions_count': stats['prescriptions_count'],
        'doctors_count': stats['doctors_count'],
        'alerts_count': stats['alerts_count'],
        'latest_report_date': stats['latest_report_date'].isoformat() if stats['latest_report_date'] else None
    })


@patient_bp.route('/api/reports')
@login_required
def api_get_reports():
    if session.get('user_role') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    reports = MedicalReport.query.filter_by(patient_id=current_user.id)\
                .order_by(MedicalReport.report_date.desc()).all()
    
    reports_data = [{
        'id': r.id,
        'date': r.report_date.isoformat(),
        'conditions': r.get_conditions(),
        'medications': r.get_medications(),
        'alerts': r.get_alerts(),
        'summary': r.summary[:200] + '...' if r.summary and len(r.summary) > 200 else r.summary
    } for r in reports]
    
    return jsonify({'reports': reports_data})


@patient_bp.route('/api/conditions')
@login_required
def api_get_conditions():
    if session.get('user_role') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    reports = MedicalReport.query.filter_by(patient_id=current_user.id).all()
    
    all_conditions = set()
    for report in reports:
        conditions = report.get_conditions()
        for condition in conditions:
            if isinstance(condition, dict):
                all_conditions.add(condition.get('name', str(condition)))
            else:
                all_conditions.add(str(condition))
    
    return jsonify({'conditions': list(all_conditions)})


@patient_bp.route('/api/prescriptions')
@login_required
def api_get_prescriptions():
    if session.get('user_role') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    prescriptions = Prescription.query.filter_by(patient_id=current_user.id)\
                     .order_by(Prescription.created_at.desc()).all()
    
    prescriptions_data = [{
        'id': p.id,
        'date': p.created_at.isoformat(),
        'diagnosis': p.diagnosis,
        'is_active': p.is_active,
        'items_count': len(p.items),
        'doctor_name': p.doctor.name if p.doctor else None
    } for p in prescriptions]
    
    return jsonify({'prescriptions': prescriptions_data})

@patient_bp.route('/api/search-doctors', methods=['GET'])
@login_required
def search_doctors():
    if session.get('user_role') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify({'doctors': []})
    
    patient = Patient.query.get(current_user.id)
    existing_doctor_ids = [d.id for d in patient.doctors]
    
    doctors = Doctor.query.filter(
        db.or_(
            Doctor.name.ilike(f"%{query}%"),
            Doctor.email.ilike(f"%{query}%"),
            Doctor.clinic_name.ilike(f"%{query}%")
        ),
        Doctor.id.notin_(existing_doctor_ids),
        Doctor.is_verified == True
    ).limit(20).all()
    
    doctors_data = []
    for doctor in doctors:
        specialty_name = None
        if doctor.specialty:
            lang = session.get('language', 'en')
            if lang == 'ar':
                specialty_name = doctor.specialty.name_ar
            elif lang == 'fr':
                specialty_name = getattr(doctor.specialty, 'name_fr', doctor.specialty.name_en)
            else:
                specialty_name = doctor.specialty.name_en
        
        doctors_data.append({
            'id': doctor.id,
            'name': doctor.name,
            'email': doctor.email,
            'specialty': specialty_name,
            'clinic_name': doctor.clinic_name,
            'phone': doctor.phone
        })
    
    return jsonify({'doctors': doctors_data})


@patient_bp.route('/api/request-doctor', methods=['POST'])
@login_required
def request_doctor():
    if session.get('user_role') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    doctor_id = data.get('doctor_id')
    
    if not doctor_id:
        return jsonify({'error': 'Doctor ID required'}), 400
    
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    patient = Patient.query.get(current_user.id)
    
    if doctor in patient.doctors:
        return jsonify({'error': 'You are already under this doctor\'s care'}), 400
    
    existing = Notification.query.filter_by(
        doctor_id=doctor_id,
        patient_id=patient.id,
        status='pending'
    ).first()
    
    if existing:
        return jsonify({'error': 'Request already sent and pending approval'}), 400
    
    notification = Notification(
        doctor_id=doctor_id,
        patient_id=patient.id,
        type='patient_request',
        message=f"Patient {patient.name} has requested to add you as their doctor",
        status='pending',
        is_read=False
    )
    
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Request sent successfully'})