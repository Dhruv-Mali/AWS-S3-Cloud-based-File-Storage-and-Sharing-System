import os
import boto3
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import secrets
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(16))
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# AWS S3 Configuration
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
S3_BUCKET = os.environ.get('S3_BUCKET_NAME')

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar'}

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size_mb(size_bytes):
    """Convert bytes to MB"""
    return round(size_bytes / (1024 * 1024), 2)

@app.route('/')
@login_required
def index():
    """Home page"""
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
    """Upload file to S3"""
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
            # Add timestamp to avoid filename conflicts
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            
            try:
                # Upload file to S3
                s3_client.upload_fileobj(
                    file,
                    S3_BUCKET,
                    unique_filename,
                    ExtraArgs={
                        'ContentType': file.content_type,
                        'Metadata': {
                            'original-filename': filename,
                            'upload-date': datetime.now().isoformat()
                        }
                    }
                )
                flash(f'File "{filename}" uploaded successfully!', 'success')
                return redirect(url_for('list_files'))
            
            except ClientError as e:
                flash(f'Error uploading file: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('File type not allowed. Allowed types: ' + ', '.join(ALLOWED_EXTENSIONS), 'error')
            return redirect(request.url)
    
    return render_template('upload.html')

@app.route('/files')
@login_required
def list_files():
    """List all files in S3 bucket"""
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET)
        
        files = []
        if 'Contents' in response:
            for obj in response['Contents']:
                files.append({
                    'key': obj['Key'],
                    'size': get_file_size_mb(obj['Size']),
                    'last_modified': obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S'),
                    'original_name': obj['Key'].split('_', 1)[1] if '_' in obj['Key'] else obj['Key']
                })
        
        return render_template('files.html', files=files)
    
    except ClientError as e:
        flash(f'Error listing files: {str(e)}', 'error')
        return render_template('files.html', files=[])

@app.route('/download/<path:filename>')
@login_required
def download_file(filename):
    """Generate pre-signed URL for file download"""
    try:
        # Generate pre-signed URL valid for 1 hour
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': filename},
            ExpiresIn=3600
        )
        return redirect(url)
    
    except ClientError as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('list_files'))

@app.route('/delete/<path:filename>', methods=['POST'])
@login_required
def delete_file(filename):
    """Delete file from S3"""
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=filename)
        flash(f'File "{filename}" deleted successfully!', 'success')
    
    except ClientError as e:
        flash(f'Error deleting file: {str(e)}', 'error')
    
    return redirect(url_for('list_files'))

@app.route('/share/<path:filename>')
@login_required
def share_file(filename):
    """Generate shareable link for file"""
    try:
        # Generate pre-signed URL valid for 7 days
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': filename},
            ExpiresIn=604800  # 7 days
        )
        return render_template('share.html', filename=filename, share_url=url)
    
    except ClientError as e:
        flash(f'Error generating share link: {str(e)}', 'error')
        return redirect(url_for('list_files'))

@app.route('/api/storage-stats')
@login_required
def storage_stats():
    """Get storage statistics"""
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET)
        
        total_size = 0
        file_count = 0
        
        if 'Contents' in response:
            file_count = len(response['Contents'])
            total_size = sum(obj['Size'] for obj in response['Contents'])
        
        return jsonify({
            'file_count': file_count,
            'total_size_mb': get_file_size_mb(total_size),
            'bucket_name': S3_BUCKET
        })
    
    except ClientError as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def too_large(e):
    flash('File is too large. Maximum size is 100MB.', 'error')
    return redirect(url_for('upload_file'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Verify AWS credentials are set
    if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, S3_BUCKET]):
        print("ERROR: Please set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and S3_BUCKET_NAME environment variables")
        print("\nTo fix this:")
        print("1. Edit .env file with your actual AWS credentials")
        print("2. Create an S3 bucket in AWS Console")
        print("3. Or run 'python app_demo.py' for local testing")
        exit(1)
    
    try:
        # Test AWS connection
        s3_client.list_objects_v2(Bucket=S3_BUCKET, MaxKeys=1)
        print(f"Connected to AWS S3 bucket: {S3_BUCKET}")
    except Exception as e:
        print(f"ERROR: Cannot connect to AWS S3: {e}")
        print("\nTo fix this:")
        print("1. Check your AWS credentials in .env file")
        print("2. Ensure S3 bucket exists and you have permissions")
        print("3. Or run 'python app_demo.py' for local testing")
        exit(1)
    
    app.run(debug=True, host='0.0.0.0', port=5000)