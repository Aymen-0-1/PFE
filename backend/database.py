from backend.extensions import db
from flask_login import UserMixin
from datetime import datetime
import json

class Commune(db.Model):
    __tablename__ = 'communes'
    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)


class Specialty(db.Model):
    __tablename__ = 'specialties'
    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)

class Doctor(UserMixin, db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    phone = db.Column(db.String(20))
    commune_id = db.Column(db.Integer, db.ForeignKey('communes.id'))
    specialty_id = db.Column(db.Integer, db.ForeignKey('specialties.id'))
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6), nullable=True)
    code_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    clinic_name = db.Column(db.String(200), nullable=True)      
    clinic_address = db.Column(db.String(300), nullable=True)   
    clinic_phone = db.Column(db.String(20), nullable=True)      
    clinic_email = db.Column(db.String(100), nullable=True)    
    clinic_logo = db.Column(db.String(200), nullable=True)  
    
    commune = db.relationship('Commune', foreign_keys=[commune_id])
    specialty = db.relationship('Specialty', foreign_keys=[specialty_id])

class Patient(UserMixin, db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    password = db.Column(db.String(200), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    phone = db.Column(db.String(20))
    ssn = db.Column(db.String(20), unique=True, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6), nullable=True)
    code_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    gender = db.Column(db.String(10), nullable=True)
    blood_type = db.Column(db.String(5), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    allergies = db.Column(db.Text, nullable=True)
    chronic_conditions = db.Column(db.Text, nullable=True)
    current_medications = db.Column(db.Text, nullable=True)
    emergency_contact_name = db.Column(db.String(100), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)

patient_doctor = db.Table('patient_doctor',
    db.Column('patient_id', db.Integer, db.ForeignKey('patients.id'), primary_key=True),
    db.Column('doctor_id', db.Integer, db.ForeignKey('doctors.id'), primary_key=True),
    db.Column('assigned_at', db.DateTime, default=datetime.utcnow)
)

Doctor.patients = db.relationship('Patient', secondary=patient_doctor, back_populates='doctors', lazy='dynamic')
Patient.doctors = db.relationship('Doctor', secondary=patient_doctor, back_populates='patients', lazy='dynamic')

class MedicalReport(db.Model):
    __tablename__ = 'medical_reports'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)
    image_paths = db.Column(db.Text)
    report_date = db.Column(db.DateTime, default=datetime.utcnow)
    conditions = db.Column(db.Text)
    medications = db.Column(db.Text)
    alerts = db.Column(db.Text)
    summary = db.Column(db.Text)
    
    patient = db.relationship('Patient', backref='reports')
    doctor = db.relationship('Doctor', backref='reports')
    
    def get_conditions(self):
        return json.loads(self.conditions) if self.conditions else []
    
    def get_medications(self):
        return json.loads(self.medications) if self.medications else []
    
    def get_alerts(self):
        return json.loads(self.alerts) if self.alerts else []

    def get_image_paths(self):
        return json.loads(self.image_paths) if self.image_paths else []
    
    def set_image_paths(self, paths):
        self.image_paths = json.dumps(paths)


class Medicine(db.Model):
    __tablename__ = 'medicines'
    id = db.Column(db.Integer, primary_key=True)
    scientific_name = db.Column(db.String(100), nullable=False)
    commercial_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    common_dosages = db.Column(db.Text)

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    diagnosis = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    patient = db.relationship('Patient', backref='prescriptions')
    doctor = db.relationship('Doctor', backref='prescriptions')
    items = db.relationship('PrescriptionItem', backref='prescription', cascade='all, delete-orphan')


class PrescriptionItem(db.Model):
    __tablename__ = 'prescription_items'
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    dosage = db.Column(db.String(50))
    frequency = db.Column(db.String(50))
    duration = db.Column(db.String(50))
    instructions = db.Column(db.Text)
    
    medicine = db.relationship('Medicine')

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    type = db.Column(db.String(50), default='patient_request')  
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='pending')  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    doctor = db.relationship('Doctor', backref='notifications')
    patient = db.relationship('Patient', backref='notifications')
    
def init_data():
    communes = [
        ("الشلف", "Chlef"), ("تنس", "Tenes"), ("المرسى", "El Marsa"),
        ("بوقادير", "Boukadir"), ("وادي الفضة", "Oued Fodda"), ("أولاد فارس", "Ouled Fares"),
        ("الشطية", "Chettia"), ("الزبوجة", "Zeboudja"),
        ("بني بوعتاب", "Beni Bouattab"), ("الصبحة", "Sobha"), ("تاوقريت", "Taougrite"),
        ("الهرانفة", "Heranfa"), ("أبو الحسن", "Abou El Hassan"),
        ("تلعصة", "Talassa"), ("بني حواء", "Beni Haoua"), ("بني راشد", "Beni Rached"),
        ("وادي سلي", "Oued Sly"), ("سنجاس", "Sendjas"), ("الحساسنة", "Harchoun"),
        ("الكريمية", "El Karimia"), ("وادي قوسين", "Oued Goussine"), ("الظهرة", "Dahra"),
        ("بوزغاية", "Bouzeghaia"), ("أولاد بن عبد القادر", "Ouled Ben Abdelkader"),
        ("أولاد محمد", "Ouled Mohamed"),
    ]    
    specialties = [
        ("طب عام", "General Practice"), ("طب القلب", "Cardiology"), ("طب العيون", "Ophthalmology"),
        ("طب الأطفال", "Pediatrics"), ("طب النساء والتوليد", "Gynecology"), ("طب الجلدية", "Dermatology"),
        ("طب العظام", "Orthopedics"), ("طب الأعصاب", "Neurology"), ("طب النفسي", "Psychiatry"),
        ("طب الأسنان", "Dentistry"), ("طب الأنف والأذن والحنجرة", "ENT"), ("طب الجهاز الهضمي", "Gastroenterology"),
        ("طب الكلى", "Nephrology"), ("طب المسالك البولية", "Urology"), ("طب الغدد الصماء", "Endocrinology"),
    ]
    
    unique_communes = []
    seen = set()
    for ar, en in communes:
        if (ar, en) not in seen:
            seen.add((ar, en))
            unique_communes.append((ar, en))
    
    for ar, en in unique_communes:
        if not Commune.query.filter_by(name_en=en).first():
            db.session.add(Commune(name_ar=ar, name_en=en))
    
    for ar, en in specialties:
        if not Specialty.query.filter_by(name_en=en).first():
            db.session.add(Specialty(name_ar=ar, name_en=en))
    
    db.session.commit()

def init_medicines():
    """إضافة الأدوية الشائعة إلى قاعدة البيانات"""
    medicines = [
            # ==================== 1. مسكنات الألم وخافضات الحرارة (15) ====================
            {"scientific_name": "Paracetamol", "commercial_name": "Doliprane", "category": "Analgesic", 
            "common_dosages": '["500mg", "1000mg"]'},
            {"scientific_name": "Paracetamol", "commercial_name": "Panadol", "category": "Analgesic", 
            "common_dosages": '["500mg", "1000mg"]'},
            {"scientific_name": "Paracetamol", "commercial_name": "Efferalgan", "category": "Analgesic", 
            "common_dosages": '["500mg", "1000mg"]'},
            {"scientific_name": "Paracetamol", "commercial_name": "Dafalgan", "category": "Analgesic", 
            "common_dosages": '["500mg", "1000mg"]'},
            {"scientific_name": "Ibuprofen", "commercial_name": "Brufen", "category": "NSAID", 
            "common_dosages": '["200mg", "400mg", "600mg"]'},
            {"scientific_name": "Ibuprofen", "commercial_name": "Advil", "category": "NSAID", 
            "common_dosages": '["200mg", "400mg"]'},
            {"scientific_name": "Ibuprofen", "commercial_name": "Nurofen", "category": "NSAID", 
            "common_dosages": '["200mg", "400mg"]'},
            {"scientific_name": "Ibuprofen", "commercial_name": "Motrin", "category": "NSAID", 
            "common_dosages": '["200mg", "400mg", "600mg"]'},
            {"scientific_name": "Aspirin", "commercial_name": "Aspirin", "category": "NSAID", 
            "common_dosages": '["75mg", "100mg", "300mg", "500mg"]'},
            {"scientific_name": "Aspirin", "commercial_name": "Aspegic", "category": "NSAID", 
            "common_dosages": '["100mg", "250mg", "500mg"]'},
            {"scientific_name": "Aspirin", "commercial_name": "Cardiospirin", "category": "NSAID", 
            "common_dosages": '["75mg", "100mg"]'},
            {"scientific_name": "Diclofenac", "commercial_name": "Voltaren", "category": "NSAID", 
            "common_dosages": '["25mg", "50mg", "75mg"]'},
            {"scientific_name": "Diclofenac", "commercial_name": "Voltarol", "category": "NSAID", 
            "common_dosages": '["25mg", "50mg"]'},
            {"scientific_name": "Naproxen", "commercial_name": "Naproxen", "category": "NSAID", 
            "common_dosages": '["250mg", "500mg"]'},
            {"scientific_name": "Naproxen", "commercial_name": "Aleve", "category": "NSAID", 
            "common_dosages": '["220mg"]'},
            
            # ==================== 2. مضادات حيوية (20) ====================
            {"scientific_name": "Amoxicillin", "commercial_name": "Amoxil", "category": "Antibiotic", 
            "common_dosages": '["250mg", "500mg", "1000mg"]'},
            {"scientific_name": "Amoxicillin", "commercial_name": "Clamoxyl", "category": "Antibiotic", 
            "common_dosages": '["250mg", "500mg", "1000mg"]'},
            {"scientific_name": "Amoxicillin-Clavulanate", "commercial_name": "Augmentin", "category": "Antibiotic", 
            "common_dosages": '["500mg", "875mg", "1000mg"]'},
            {"scientific_name": "Amoxicillin-Clavulanate", "commercial_name": "Clavulin", "category": "Antibiotic", 
            "common_dosages": '["500mg", "875mg"]'},
            {"scientific_name": "Azithromycin", "commercial_name": "Azithromycin", "category": "Macrolide", 
            "common_dosages": '["250mg", "500mg"]'},
            {"scientific_name": "Azithromycin", "commercial_name": "Zithromax", "category": "Macrolide", 
            "common_dosages": '["250mg", "500mg"]'},
            {"scientific_name": "Clarithromycin", "commercial_name": "Clarithromycin", "category": "Macrolide", 
            "common_dosages": '["250mg", "500mg"]'},
            {"scientific_name": "Clarithromycin", "commercial_name": "Klaricid", "category": "Macrolide", 
            "common_dosages": '["250mg", "500mg"]'},
            {"scientific_name": "Ciprofloxacin", "commercial_name": "Ciprofloxacin", "category": "Fluoroquinolone", 
            "common_dosages": '["250mg", "500mg", "750mg"]'},
            {"scientific_name": "Ciprofloxacin", "commercial_name": "Cipro", "category": "Fluoroquinolone", 
            "common_dosages": '["250mg", "500mg", "750mg"]'},
            {"scientific_name": "Levofloxacin", "commercial_name": "Levofloxacin", "category": "Fluoroquinolone", 
            "common_dosages": '["250mg", "500mg", "750mg"]'},
            {"scientific_name": "Moxifloxacin", "commercial_name": "Avelox", "category": "Fluoroquinolone", 
            "common_dosages": '["400mg"]'},
            {"scientific_name": "Doxycycline", "commercial_name": "Doxycycline", "category": "Tetracycline", 
            "common_dosages": '["100mg"]'},
            {"scientific_name": "Doxycycline", "commercial_name": "Vibramycin", "category": "Tetracycline", 
            "common_dosages": '["100mg"]'},
            {"scientific_name": "Metronidazole", "commercial_name": "Flagyl", "category": "Antibiotic", 
            "common_dosages": '["250mg", "500mg"]'},
            {"scientific_name": "Metronidazole", "commercial_name": "Metronidazole", "category": "Antibiotic", 
            "common_dosages": '["250mg", "500mg"]'},
            {"scientific_name": "Clindamycin", "commercial_name": "Clindamycin", "category": "Antibiotic", 
            "common_dosages": '["150mg", "300mg"]'},
            {"scientific_name": "Cefixime", "commercial_name": "Suprax", "category": "Cephalosporin", 
            "common_dosages": '["200mg", "400mg"]'},
            {"scientific_name": "Cefuroxime", "commercial_name": "Zinnat", "category": "Cephalosporin", 
            "common_dosages": '["125mg", "250mg", "500mg"]'},
            {"scientific_name": "Cefalexin", "commercial_name": "Keflex", "category": "Cephalosporin", 
            "common_dosages": '["250mg", "500mg"]'},
            
            # ==================== 3. أدوية الضغط (20) ====================
            {"scientific_name": "Lisinopril", "commercial_name": "Zestril", "category": "ACE Inhibitor", 
            "common_dosages": '["5mg", "10mg", "20mg"]'},
            {"scientific_name": "Lisinopril", "commercial_name": "Lisinopril", "category": "ACE Inhibitor", 
            "common_dosages": '["5mg", "10mg", "20mg"]'},
            {"scientific_name": "Enalapril", "commercial_name": "Renitec", "category": "ACE Inhibitor", 
            "common_dosages": '["5mg", "10mg", "20mg"]'},
            {"scientific_name": "Enalapril", "commercial_name": "Enalapril", "category": "ACE Inhibitor", 
            "common_dosages": '["5mg", "10mg", "20mg"]'},
            {"scientific_name": "Ramipril", "commercial_name": "Ramipril", "category": "ACE Inhibitor", 
            "common_dosages": '["2.5mg", "5mg", "10mg"]'},
            {"scientific_name": "Amlodipine", "commercial_name": "Norvasc", "category": "Calcium Channel Blocker", 
            "common_dosages": '["2.5mg", "5mg", "10mg"]'},
            {"scientific_name": "Amlodipine", "commercial_name": "Amlodipine", "category": "Calcium Channel Blocker", 
            "common_dosages": '["2.5mg", "5mg", "10mg"]'},
            {"scientific_name": "Nifedipine", "commercial_name": "Adalat", "category": "Calcium Channel Blocker", 
            "common_dosages": '["30mg", "60mg"]'},
            {"scientific_name": "Losartan", "commercial_name": "Cozaar", "category": "ARB", 
            "common_dosages": '["25mg", "50mg", "100mg"]'},
            {"scientific_name": "Losartan", "commercial_name": "Losartan", "category": "ARB", 
            "common_dosages": '["25mg", "50mg", "100mg"]'},
            {"scientific_name": "Valsartan", "commercial_name": "Diovan", "category": "ARB", 
            "common_dosages": '["80mg", "160mg"]'},
            {"scientific_name": "Irbesartan", "commercial_name": "Aprovel", "category": "ARB", 
            "common_dosages": '["75mg", "150mg", "300mg"]'},
            {"scientific_name": "Metoprolol", "commercial_name": "Lopressor", "category": "Beta Blocker", 
            "common_dosages": '["25mg", "50mg", "100mg"]'},
            {"scientific_name": "Metoprolol", "commercial_name": "Betaloc", "category": "Beta Blocker", 
            "common_dosages": '["25mg", "50mg", "100mg"]'},
            {"scientific_name": "Atenolol", "commercial_name": "Tenormin", "category": "Beta Blocker", 
            "common_dosages": '["25mg", "50mg", "100mg"]'},
            {"scientific_name": "Bisoprolol", "commercial_name": "Bisoprolol", "category": "Beta Blocker", 
            "common_dosages": '["2.5mg", "5mg", "10mg"]'},
            {"scientific_name": "Carvedilol", "commercial_name": "Carvedilol", "category": "Beta Blocker", 
            "common_dosages": '["6.25mg", "12.5mg", "25mg"]'},
            {"scientific_name": "Hydrochlorothiazide", "commercial_name": "Hydrochlorothiazide", "category": "Diuretic", 
            "common_dosages": '["12.5mg", "25mg", "50mg"]'},
            {"scientific_name": "Furosemide", "commercial_name": "Lasix", "category": "Loop Diuretic", 
            "common_dosages": '["20mg", "40mg", "80mg"]'},
            {"scientific_name": "Spironolactone", "commercial_name": "Aldactone", "category": "Potassium-sparing Diuretic", 
            "common_dosages": '["25mg", "50mg", "100mg"]'},
            
            # ==================== 4. أدوية السكري (15) ====================
            {"scientific_name": "Metformin", "commercial_name": "Glucophage", "category": "Biguanide", 
            "common_dosages": '["500mg", "850mg", "1000mg"]'},
            {"scientific_name": "Metformin", "commercial_name": "Metformin", "category": "Biguanide", 
            "common_dosages": '["500mg", "850mg", "1000mg"]'},
            {"scientific_name": "Gliclazide", "commercial_name": "Diamicron", "category": "Sulfonylurea", 
            "common_dosages": '["30mg", "60mg", "80mg"]'},
            {"scientific_name": "Gliclazide", "commercial_name": "Gliclazide", "category": "Sulfonylurea", 
            "common_dosages": '["30mg", "60mg", "80mg"]'},
            {"scientific_name": "Glimepiride", "commercial_name": "Amaryl", "category": "Sulfonylurea", 
            "common_dosages": '["1mg", "2mg", "4mg"]'},
            {"scientific_name": "Glimepiride", "commercial_name": "Glimepiride", "category": "Sulfonylurea", 
            "common_dosages": '["1mg", "2mg", "4mg"]'},
            {"scientific_name": "Glipizide", "commercial_name": "Glipizide", "category": "Sulfonylurea", 
            "common_dosages": '["5mg", "10mg"]'},
            {"scientific_name": "Sitagliptin", "commercial_name": "Januvia", "category": "DPP-4 Inhibitor", 
            "common_dosages": '["25mg", "50mg", "100mg"]'},
            {"scientific_name": "Sitagliptin", "commercial_name": "Sitagliptin", "category": "DPP-4 Inhibitor", 
            "common_dosages": '["25mg", "50mg", "100mg"]'},
            {"scientific_name": "Saxagliptin", "commercial_name": "Onglyza", "category": "DPP-4 Inhibitor", 
            "common_dosages": '["2.5mg", "5mg"]'},
            {"scientific_name": "Empagliflozin", "commercial_name": "Jardiance", "category": "SGLT2 Inhibitor", 
            "common_dosages": '["10mg", "25mg"]'},
            {"scientific_name": "Empagliflozin", "commercial_name": "Empagliflozin", "category": "SGLT2 Inhibitor", 
            "common_dosages": '["10mg", "25mg"]'},
            {"scientific_name": "Dapagliflozin", "commercial_name": "Forxiga", "category": "SGLT2 Inhibitor", 
            "common_dosages": '["5mg", "10mg"]'},
            {"scientific_name": "Pioglitazone", "commercial_name": "Actos", "category": "Thiazolidinedione", 
            "common_dosages": '["15mg", "30mg", "45mg"]'},
            {"scientific_name": "Liraglutide", "commercial_name": "Victoza", "category": "GLP-1 Agonist", 
            "common_dosages": '["0.6mg", "1.2mg", "1.8mg"]'},
            
            # ==================== 5. أدوية الكوليسترول (10) ====================
            {"scientific_name": "Atorvastatin", "commercial_name": "Lipitor", "category": "Statin", 
            "common_dosages": '["10mg", "20mg", "40mg", "80mg"]'},
            {"scientific_name": "Atorvastatin", "commercial_name": "Atorvastatin", "category": "Statin", 
            "common_dosages": '["10mg", "20mg", "40mg", "80mg"]'},
            {"scientific_name": "Simvastatin", "commercial_name": "Zocor", "category": "Statin", 
            "common_dosages": '["10mg", "20mg", "40mg"]'},
            {"scientific_name": "Simvastatin", "commercial_name": "Simvastatin", "category": "Statin", 
            "common_dosages": '["10mg", "20mg", "40mg"]'},
            {"scientific_name": "Rosuvastatin", "commercial_name": "Crestor", "category": "Statin", 
            "common_dosages": '["5mg", "10mg", "20mg", "40mg"]'},
            {"scientific_name": "Rosuvastatin", "commercial_name": "Rosuvastatin", "category": "Statin", 
            "common_dosages": '["5mg", "10mg", "20mg", "40mg"]'},
            {"scientific_name": "Pravastatin", "commercial_name": "Pravastatin", "category": "Statin", 
            "common_dosages": '["10mg", "20mg", "40mg"]'},
            {"scientific_name": "Fluvastatin", "commercial_name": "Fluvastatin", "category": "Statin", 
            "common_dosages": '["20mg", "40mg", "80mg"]'},
            {"scientific_name": "Ezetimibe", "commercial_name": "Ezetrol", "category": "Cholesterol Absorption Inhibitor", 
            "common_dosages": '["10mg"]'},
            {"scientific_name": "Fenofibrate", "commercial_name": "Fenofibrate", "category": "Fibrate", 
            "common_dosages": '["145mg"]'},
            
            # ==================== 6. أدوية الجهاز التنفسي (10) ====================
            {"scientific_name": "Salbutamol", "commercial_name": "Ventolin", "category": "Bronchodilator", 
            "common_dosages": '["100mcg", "200mcg"]'},
            {"scientific_name": "Salbutamol", "commercial_name": "Salbutamol", "category": "Bronchodilator", 
            "common_dosages": '["100mcg", "200mcg"]'},
            {"scientific_name": "Salmeterol", "commercial_name": "Serevent", "category": "LABA", 
            "common_dosages": '["25mcg", "50mcg"]'},
            {"scientific_name": "Budesonide", "commercial_name": "Pulmicort", "category": "Inhaled Corticosteroid", 
            "common_dosages": '["200mcg", "400mcg"]'},
            {"scientific_name": "Fluticasone", "commercial_name": "Flixotide", "category": "Inhaled Corticosteroid", 
            "common_dosages": '["125mcg", "250mcg"]'},
            {"scientific_name": "Montelukast", "commercial_name": "Singulair", "category": "Leukotriene Antagonist", 
            "common_dosages": '["4mg", "5mg", "10mg"]'},
            {"scientific_name": "Montelukast", "commercial_name": "Montelukast", "category": "Leukotriene Antagonist", 
            "common_dosages": '["4mg", "5mg", "10mg"]'},
            {"scientific_name": "Theophylline", "commercial_name": "Theophylline", "category": "Xanthine", 
            "common_dosages": '["200mg", "300mg"]'},
            {"scientific_name": "Ipratropium", "commercial_name": "Atrovent", "category": "Anticholinergic", 
            "common_dosages": '["20mcg", "40mcg"]'},
            {"scientific_name": "Tiotropium", "commercial_name": "Spiriva", "category": "LAMA", 
            "common_dosages": '["18mcg"]'},
            
            # ==================== 7. أدوية الجهاز الهضمي (10) ====================
            {"scientific_name": "Omeprazole", "commercial_name": "Losec", "category": "PPI", 
            "common_dosages": '["10mg", "20mg", "40mg"]'},
            {"scientific_name": "Omeprazole", "commercial_name": "Omeprazole", "category": "PPI", 
            "common_dosages": '["10mg", "20mg", "40mg"]'},
            {"scientific_name": "Esomeprazole", "commercial_name": "Nexium", "category": "PPI", 
            "common_dosages": '["20mg", "40mg"]'},
            {"scientific_name": "Pantoprazole", "commercial_name": "Protonix", "category": "PPI", 
            "common_dosages": '["20mg", "40mg"]'},
            {"scientific_name": "Pantoprazole", "commercial_name": "Pantoprazole", "category": "PPI", 
            "common_dosages": '["20mg", "40mg"]'},
            {"scientific_name": "Lansoprazole", "commercial_name": "Lansoprazole", "category": "PPI", 
            "common_dosages": '["15mg", "30mg"]'},
            {"scientific_name": "Famotidine", "commercial_name": "Famotidine", "category": "H2 Blocker", 
            "common_dosages": '["20mg", "40mg"]'},
            {"scientific_name": "Metoclopramide", "commercial_name": "Metoclopramide", "category": "Prokinetic", 
            "common_dosages": '["10mg"]'},
            {"scientific_name": "Domperidone", "commercial_name": "Domperidone", "category": "Prokinetic", 
            "common_dosages": '["10mg"]'},
            {"scientific_name": "Ondansetron", "commercial_name": "Zofran", "category": "Antiemetic", 
            "common_dosages": '["4mg", "8mg"]'},
            
            # ==================== 8. أدوية الجهاز العصبي (15) ====================
            {"scientific_name": "Gabapentin", "commercial_name": "Neurontin", "category": "Anticonvulsant", 
            "common_dosages": '["100mg", "300mg", "400mg", "600mg", "800mg"]'},
            {"scientific_name": "Gabapentin", "commercial_name": "Gabapentin", "category": "Anticonvulsant", 
            "common_dosages": '["100mg", "300mg", "400mg", "600mg", "800mg"]'},
            {"scientific_name": "Pregabalin", "commercial_name": "Lyrica", "category": "Anticonvulsant", 
            "common_dosages": '["25mg", "50mg", "75mg", "150mg"]'},
            {"scientific_name": "Pregabalin", "commercial_name": "Pregabalin", "category": "Anticonvulsant", 
            "common_dosages": '["25mg", "50mg", "75mg", "150mg"]'},
            {"scientific_name": "Sertraline", "commercial_name": "Zoloft", "category": "SSRI", 
            "common_dosages": '["25mg", "50mg", "100mg"]'},
            {"scientific_name": "Sertraline", "commercial_name": "Sertraline", "category": "SSRI", 
            "common_dosages": '["25mg", "50mg", "100mg"]'},
            {"scientific_name": "Fluoxetine", "commercial_name": "Prozac", "category": "SSRI", 
            "common_dosages": '["20mg", "40mg"]'},
            {"scientific_name": "Fluoxetine", "commercial_name": "Fluoxetine", "category": "SSRI", 
            "common_dosages": '["20mg", "40mg"]'},
            {"scientific_name": "Escitalopram", "commercial_name": "Cipralex", "category": "SSRI", 
            "common_dosages": '["10mg", "20mg"]'},
            {"scientific_name": "Paroxetine", "commercial_name": "Paroxetine", "category": "SSRI", 
            "common_dosages": '["20mg", "40mg"]'},
            {"scientific_name": "Diazepam", "commercial_name": "Valium", "category": "Benzodiazepine", 
            "common_dosages": '["2mg", "5mg", "10mg"]'},
            {"scientific_name": "Alprazolam", "commercial_name": "Xanax", "category": "Benzodiazepine", 
            "common_dosages": '["0.25mg", "0.5mg", "1mg"]'},
            {"scientific_name": "Lorazepam", "commercial_name": "Ativan", "category": "Benzodiazepine", 
            "common_dosages": '["0.5mg", "1mg", "2mg"]'},
            {"scientific_name": "Clonazepam", "commercial_name": "Rivotril", "category": "Benzodiazepine", 
            "common_dosages": '["0.5mg", "1mg", "2mg"]'},
            {"scientific_name": "Carbamazepine", "commercial_name": "Tegretol", "category": "Anticonvulsant", 
            "common_dosages": '["200mg", "400mg"]'},
            
            # ==================== 9. أدوية القلب (10) ====================
            {"scientific_name": "Digoxin", "commercial_name": "Digoxin", "category": "Cardiac Glycoside", 
            "common_dosages": '["0.125mg", "0.25mg"]'},
            {"scientific_name": "Warfarin", "commercial_name": "Coumadin", "category": "Anticoagulant", 
            "common_dosages": '["1mg", "2mg", "2.5mg", "3mg", "4mg", "5mg"]'},
            {"scientific_name": "Warfarin", "commercial_name": "Warfarin", "category": "Anticoagulant", 
            "common_dosages": '["1mg", "2mg", "2.5mg", "3mg", "4mg", "5mg"]'},
            {"scientific_name": "Clopidogrel", "commercial_name": "Plavix", "category": "Antiplatelet", 
            "common_dosages": '["75mg"]'},
            {"scientific_name": "Clopidogrel", "commercial_name": "Clopidogrel", "category": "Antiplatelet", 
            "common_dosages": '["75mg"]'},
            {"scientific_name": "Apixaban", "commercial_name": "Eliquis", "category": "DOAC", 
            "common_dosages": '["2.5mg", "5mg"]'},
            {"scientific_name": "Rivaroxaban", "commercial_name": "Xarelto", "category": "DOAC", 
            "common_dosages": '["10mg", "15mg", "20mg"]'},
            {"scientific_name": "Dabigatran", "commercial_name": "Pradaxa", "category": "DOAC", 
            "common_dosages": '["75mg", "110mg", "150mg"]'},
            {"scientific_name": "Isosorbide Mononitrate", "commercial_name": "Isosorbide", "category": "Nitrate", 
            "common_dosages": '["10mg", "20mg"]'},
            {"scientific_name": "Nitroglycerin", "commercial_name": "Nitroglycerin", "category": "Nitrate", 
            "common_dosages": '["0.3mg", "0.4mg", "0.6mg"]'},
        ]

    added_count = 0
    for med in medicines:
        existing = Medicine.query.filter_by(commercial_name=med["commercial_name"]).first()
        if not existing:
            medicine = Medicine(**med)
            db.session.add(medicine)
            added_count += 1
    
    db.session.commit()

__all__ = [
    'db',
    'Commune',
    'Specialty', 
    'Doctor',
    'Patient',
    'MedicalReport',
    'Medicine',
    'Prescription',
    'PrescriptionItem',
    'init_data',
    'init_medicines'
]