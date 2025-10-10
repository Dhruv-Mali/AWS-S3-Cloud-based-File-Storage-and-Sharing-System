# AWS S3 Cloud-based File Storage and Sharing System

A Flask web application for secure file storage and sharing using Amazon S3.

## Features

- **Secure File Upload**: Upload files up to 100MB to AWS S3
- **File Management**: View, download, and delete stored files
- **File Sharing**: Generate temporary shareable links (valid for 7 days)
- **Storage Statistics**: View file count and storage usage
- **Responsive Design**: Bootstrap-based UI that works on all devices
- **Security**: Pre-signed URLs for secure file access

## Prerequisites

- Python 3.7+
- AWS Account with S3 access
- AWS S3 bucket created

## Installation

1. **Clone or download the project**
   ```bash
   cd "AWS S3 Cloud-based File Storage and Sharing System"
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Fill in your AWS credentials and S3 bucket name:
   ```
   AWS_ACCESS_KEY_ID=your_aws_access_key_here
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
   AWS_REGION=us-east-1
   S3_BUCKET_NAME=your-s3-bucket-name
   FLASK_SECRET_KEY=your_secret_key_here
   ```

## AWS Setup

1. **Create an S3 Bucket**
   - Go to AWS S3 Console
   - Create a new bucket with a unique name
   - Note the bucket name for your `.env` file

2. **Create IAM User** (Recommended)
   - Go to AWS IAM Console
   - Create a new user with programmatic access
   - Attach the following policy for S3 access:
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "s3:GetObject",
                   "s3:PutObject",
                   "s3:DeleteObject",
                   "s3:ListBucket"
               ],
               "Resource": [
                   "arn:aws:s3:::your-bucket-name",
                   "arn:aws:s3:::your-bucket-name/*"
               ]
           }
       ]
   }
   ```

## Running the Application

1. **Start the Flask application**
   ```bash
   python app.py
   ```

2. **Access the application**
   - Open your browser and go to `http://localhost:5000`

## Supported File Types

- Documents: txt, pdf, doc, docx, xls, xlsx
- Images: png, jpg, jpeg, gif
- Archives: zip, rar

## File Size Limit

- Maximum file size: 100MB per file

## Security Features

- Pre-signed URLs for secure file access
- Temporary share links (7-day expiration)
- File type validation
- Secure filename handling

## Project Structure

```
AWS S3 Cloud-based File Storage and Sharing System/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── README.md             # This file
└── templates/            # HTML templates
    ├── base.html         # Base template
    ├── index.html        # Home page
    ├── upload.html       # File upload page
    ├── files.html        # File listing page
    └── share.html        # File sharing page
```

## Troubleshooting

1. **AWS Credentials Error**
   - Ensure your `.env` file has correct AWS credentials
   - Verify your IAM user has S3 permissions

2. **Bucket Access Error**
   - Check if the S3 bucket name is correct
   - Verify bucket permissions and region

3. **File Upload Issues**
   - Check file size (max 100MB)
   - Verify file type is supported
   - Ensure stable internet connection

## License

This project is open source and available under the MIT License.