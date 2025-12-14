#!/usr/bin/env python3
"""
Script to create and configure S3 bucket for the file storage system
"""

import boto3
import sys
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
S3_BUCKET = os.environ.get('S3_BUCKET_NAME')

def create_s3_bucket():
    """Create S3 bucket with proper configuration"""
    
    print("AWS S3 Bucket Setup")
    print("=" * 50)
    
    # Validate credentials
    if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, S3_BUCKET]):
        print("ERROR: Missing AWS credentials in .env file")
        print("\nPlease ensure your .env file has:")
        print("- AWS_ACCESS_KEY_ID")
        print("- AWS_SECRET_ACCESS_KEY")
        print("- S3_BUCKET_NAME")
        return False
    
    # Initialize S3 client
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION
        )
        print(f"[OK] AWS credentials validated")
    except Exception as e:
        print(f"ERROR: Failed to initialize AWS client: {e}")
        return False
    
    # Check if bucket already exists
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET)
        print(f"[OK] Bucket '{S3_BUCKET}' already exists")
        print(f"[OK] You can use this bucket")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"Bucket '{S3_BUCKET}' does not exist. Creating...")
        elif error_code == '403':
            print(f"ERROR: Access denied to bucket '{S3_BUCKET}'")
            print("Either the bucket exists and you don't have permission,")
            print("or you need different credentials.")
            return False
        else:
            print(f"ERROR: {e}")
            return False
    
    # Create the bucket
    try:
        if AWS_REGION == 'us-east-1':
            # us-east-1 doesn't need LocationConstraint
            s3_client.create_bucket(Bucket=S3_BUCKET)
        else:
            s3_client.create_bucket(
                Bucket=S3_BUCKET,
                CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
            )
        print(f"[OK] Bucket '{S3_BUCKET}' created successfully")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'BucketAlreadyExists':
            print(f"ERROR: Bucket name '{S3_BUCKET}' is already taken globally")
            print("S3 bucket names must be globally unique.")
            print("Please choose a different name in your .env file")
            return False
        elif error_code == 'BucketAlreadyOwnedByYou':
            print(f"[OK] Bucket '{S3_BUCKET}' already exists and is owned by you")
            return True
        else:
            print(f"ERROR: Failed to create bucket: {e}")
            return False
    
    # Configure bucket CORS (for web access)
    try:
        cors_configuration = {
            'CORSRules': [{
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE'],
                'AllowedOrigins': ['*'],
                'ExposeHeaders': ['ETag'],
                'MaxAgeSeconds': 3000
            }]
        }
        s3_client.put_bucket_cors(
            Bucket=S3_BUCKET,
            CORSConfiguration=cors_configuration
        )
        print(f"[OK] CORS configuration applied")
    except ClientError as e:
        print(f"WARNING: Could not set CORS: {e}")
    
    # Test bucket access
    try:
        s3_client.list_objects_v2(Bucket=S3_BUCKET, MaxKeys=1)
        print(f"[OK] Bucket access verified")
    except ClientError as e:
        print(f"ERROR: Cannot access bucket: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("SUCCESS! Your S3 bucket is ready to use")
    print(f"Bucket Name: {S3_BUCKET}")
    print(f"Region: {AWS_REGION}")
    print("\nYou can now run: python app.py")
    print("=" * 50)
    
    return True

if __name__ == '__main__':
    success = create_s3_bucket()
    sys.exit(0 if success else 1)
