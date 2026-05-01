from werkzeug.utils import secure_filename
import os
os.environ['PILLOW_NO_DEBUG'] = '1'

from flask import Flask, render_template, redirect, url_for, session, request, jsonify, flash, send_from_directory
from flask_login import current_user, login_required
from datetime import datetime

app = Flask(__name__, template_folder='../templates', static_folder='../static')

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'my-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medai.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'AiPoweredMedic@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'cfap wffb pdyo skaw')
app.config['MAIL_DEFAULT_SENDER'] = ('Ai-Powered-Medic', 'AiPoweredMedic@medai.com')

# ===== إعدادات إضافية =====
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

from backend.extensions import db, login_manager, mail

db.init_app(app)
login_manager.init_app(app)
mail.init_app(app)

login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please login to access this page'
login_manager.login_message_category = 'warning'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_current_language():
    return session.get('language', 'en')

def gettext(text):
    try:
        from backend.translate import translations
        lang = get_current_language()
        if isinstance(translations.get(lang, {}), dict):
            return translations.get(lang, translations.get('en', {})).get(text, text)
        return text
    except (ImportError, AttributeError):
        return text

app.jinja_env.globals.update(
    gettext=gettext,
    _=gettext,  
    current_lang=get_current_language
)

@app.route('/set-language/<lang>')
def set_language(lang):
    if lang in ['ar', 'en', 'fr']:
        session['language'] = lang
        session.permanent = True
    return redirect(request.referrer or url_for('home'))

@app.route('/set-language', methods=['POST'])
def set_language_post():
    data = request.get_json()
    lang = data.get('lang', 'en')
    if lang in ['ar', 'en', 'fr']:
        session['language'] = lang
        return jsonify({'success': True, 'language': lang})
    return jsonify({'success': False}), 400

from backend.auth import auth_bp
from backend.doctor import doctor_bp
from backend.patient import patient_bp
from backend.report import report_bp
from backend.prescription import prescription_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(doctor_bp, url_prefix='/doctor')
app.register_blueprint(patient_bp, url_prefix='/patient')
app.register_blueprint(report_bp, url_prefix='/report')
app.register_blueprint(prescription_bp, url_prefix='/prescription')

@app.route('/')
def home():
    if current_user.is_authenticated:
        if session.get('user_role') == 'doctor':
            return redirect(url_for('doctor.doctor_dashboard'))
        elif session.get('user_role') == 'patient':
            return redirect(url_for('patient.patient_dashboard'))
    return render_template('home.html', show_header=True)

@app.route('/about')
def about():
    return render_template('about.html', show_header=True)

@app.route('/contact')
def contact():
    return render_template('contact.html', show_header=True)

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if db.engine else 'error'
    })

@login_manager.user_loader
def load_user(user_id):
    from backend.database import Doctor, Patient
    
    user_role = session.get('user_role')
    try:
        if user_role == 'doctor':
            return Doctor.query.get(int(user_id))
        else:
            return Patient.query.get(int(user_id))
    except (ValueError, TypeError):
        return None

@login_manager.unauthorized_handler
def unauthorized():
    flash('Please login to access this page', 'warning')
    return redirect(url_for('auth.login'))

@app.context_processor
def utility_processor():
    def get_user_role():
        return session.get('user_role', 'guest')
    
    def format_date(date):
        if date:
            return date.strftime('%d/%m/%Y')
        return '-'
    
    return dict(
        get_user_role=get_user_role,
        format_date=format_date,
        now=datetime.now()
    )

def init_data():
    from backend.database import init_data as db_init_data
    db_init_data()

def init_medicines():
    from backend.database import init_medicines as db_init_medicines
    db_init_medicines()
    
@app.route('/ocr', methods=['POST'])
def ocr_public():
    try:
        from backend.report import allowed_file, UPLOAD_FOLDER
        from backend.ocr_engine import extract_text
        from werkzeug.utils import secure_filename
        from datetime import datetime
        import os
        
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400
        
        os.makedirs('uploads', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = secure_filename(f"{timestamp}_{file.filename}")
        file_path = os.path.join('uploads', filename)
        file.save(file_path)
        
        text = extract_text(file_path)
        
        return jsonify({
            "success": True,
            "text": text,
            "image_path": filename
        })
        
    except Exception as e:
        print(f"OCR Error: {e}")
        return jsonify({"error": str(e)}), 500

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload-logo', methods=['POST'])
@login_required
def upload_logo():
    try:
        if 'logo' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['logo']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        logo_folder = os.path.join('static', 'logos')
        os.makedirs(logo_folder, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(f"logo_{current_user.id}_{timestamp}_{file.filename}")
        file_path = os.path.join(logo_folder, filename)
        file.save(file_path)
        
        current_user.clinic_logo = f'logos/{filename}'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'logo_path': current_user.clinic_logo,
            'message': 'Logo uploaded successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/remove-logo', methods=['POST'])
@login_required
def remove_logo():
    try:
        if current_user.clinic_logo:
            logo_path = os.path.join('static', current_user.clinic_logo)
            if os.path.exists(logo_path):
                os.remove(logo_path)
            
            current_user.clinic_logo = None
            db.session.commit()
        
        return jsonify({'success': True, 'message': 'Logo removed successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def create_app():
    return app


with app.app_context():
    db.create_all()
    init_data()
    init_medicines()


if __name__ == '__main__':
    app.run(debug=True)