import os
import boto3
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from botocore.exceptions import ClientError
from datetime import datetime
import secrets
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(16))
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
S3_BUCKET = os.environ.get('S3_BUCKET_NAME')

s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=AWS_REGION)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar'}
LOCAL_UPLOAD_FOLDER = 'uploads'
if not os.path.exists(LOCAL_UPLOAD_FOLDER):
    os.makedirs(LOCAL_UPLOAD_FOLDER)

class AppConfig:
    aws_available = False

def check_aws_connection():
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET)
        return True
    except:
        return False

AppConfig.aws_available = check_aws_connection()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size_mb(size_bytes):
    return round(size_bytes / (1024 * 1024), 2)

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        user = User(username=username, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            try:
                if AppConfig.aws_available:
                    s3_client.upload_fileobj(file, S3_BUCKET, unique_filename, ExtraArgs={'ContentType': file.content_type})
                else:
                    file.save(os.path.join(LOCAL_UPLOAD_FOLDER, unique_filename))
                flash(f'File "{filename}" uploaded successfully!', 'success')
                return redirect(url_for('list_files'))
            except Exception as e:
                flash(f'Error uploading file: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('File type not allowed. Allowed types: ' + ', '.join(ALLOWED_EXTENSIONS), 'error')
            return redirect(request.url)
    return render_template('upload.html')

@app.route('/files')
@login_required
def list_files():
    try:
        files = []
        if AppConfig.aws_available:
            response = s3_client.list_objects_v2(Bucket=S3_BUCKET)
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': get_file_size_mb(obj['Size']),
                        'last_modified': obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S'),
                        'original_name': obj['Key'].split('_', 1)[1] if '_' in obj['Key'] else obj['Key']
                    })
        else:
            if os.path.exists(LOCAL_UPLOAD_FOLDER):
                for filename in os.listdir(LOCAL_UPLOAD_FOLDER):
                    file_path = os.path.join(LOCAL_UPLOAD_FOLDER, filename)
                    if os.path.isfile(file_path):
                        stat = os.stat(file_path)
                        files.append({
                            'key': filename,
                            'size': get_file_size_mb(stat.st_size),
                            'last_modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                            'original_name': filename.split('_', 1)[1] if '_' in filename else filename
                        })
        return render_template('files.html', files=files)
    except Exception as e:
        flash(f'Error listing files: {str(e)}', 'error')
        return render_template('files.html', files=[])

@app.route('/download/<path:filename>')
@login_required
def download_file(filename):
    try:
        if AppConfig.aws_available:
            url = s3_client.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': filename}, ExpiresIn=3600)
            return redirect(url)
        else:
            return send_from_directory(LOCAL_UPLOAD_FOLDER, filename, as_attachment=True)
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('list_files'))

@app.route('/delete/<path:filename>', methods=['POST'])
@login_required
def delete_file(filename):
    try:
        if AppConfig.aws_available:
            s3_client.delete_object(Bucket=S3_BUCKET, Key=filename)
        else:
            file_path = os.path.join(LOCAL_UPLOAD_FOLDER, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        flash(f'File "{filename}" deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'error')
    return redirect(url_for('list_files'))

@app.route('/share/<path:filename>')
@login_required
def share_file(filename):
    try:
        if AppConfig.aws_available:
            url = s3_client.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': filename}, ExpiresIn=604800)
            return render_template('share.html', share_url=url, filename=filename)
        else:
            flash('Sharing only available with S3', 'error')
            return redirect(url_for('list_files'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('list_files'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print(f"Mode: {'AWS S3' if AppConfig.aws_available else 'LOCAL STORAGE'}")
    print(f"Bucket: {S3_BUCKET if AppConfig.aws_available else 'uploads/'}")
    app.run(debug=True)
