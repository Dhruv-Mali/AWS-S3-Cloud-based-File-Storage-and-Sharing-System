# AWS S3 Setup Guide

## Your Current Issue
Your AWS credentials in the `.env` file are either:
- Invalid/expired
- Don't have proper S3 permissions
- The Access Key ID doesn't exist in AWS

## How to Get Valid AWS Credentials

### Step 1: Sign in to AWS Console
1. Go to https://aws.amazon.com/console/
2. Sign in with your AWS account
3. If you don't have an account, create one (requires credit card)

### Step 2: Create IAM User with S3 Access
1. Go to IAM Console: https://console.aws.amazon.com/iam/
2. Click "Users" in the left sidebar
3. Click "Create user"
4. Enter username (e.g., `s3-file-storage-user`)
5. Click "Next"

### Step 3: Set Permissions
1. Select "Attach policies directly"
2. Search for and select: `AmazonS3FullAccess`
3. Click "Next" then "Create user"

### Step 4: Create Access Keys
1. Click on the newly created user
2. Go to "Security credentials" tab
3. Scroll to "Access keys" section
4. Click "Create access key"
5. Select "Application running outside AWS"
6. Click "Next" then "Create access key"
7. **IMPORTANT**: Copy both:
   - Access key ID
   - Secret access key
   (You won't be able to see the secret key again!)

### Step 5: Create S3 Bucket
1. Go to S3 Console: https://s3.console.aws.amazon.com/s3/
2. Click "Create bucket"
3. Enter a **globally unique** bucket name (e.g., `your-name-file-storage-2024-12345`)
4. Select region: `us-east-1`
5. Keep all default settings
6. Click "Create bucket"

### Step 6: Update .env File
Edit your `.env` file with the new credentials:

```
AWS_ACCESS_KEY_ID=YOUR_NEW_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=YOUR_NEW_SECRET_ACCESS_KEY
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-unique-bucket-name
```

### Step 7: Run the Application
```bash
python app.py
```

## Alternative: Run Without AWS (Local Mode)

If you don't want to use AWS right now, the application will automatically run in LOCAL MODE:

1. Just run: `python app.py`
2. Files will be stored in the `uploads/` folder
3. All features work the same way

## Troubleshooting

### Error: "InvalidAccessKeyId"
- Your Access Key ID is wrong or doesn't exist
- Create new credentials following steps above

### Error: "Access Denied"
- Your IAM user doesn't have S3 permissions
- Attach `AmazonS3FullAccess` policy to your IAM user

### Error: "Bucket name already taken"
- S3 bucket names are globally unique
- Choose a different, more unique name

## Security Best Practices

1. **Never share your credentials** - Keep `.env` file private
2. **Use IAM users** - Don't use root account credentials
3. **Limit permissions** - Only grant S3 access, not full AWS access
4. **Rotate keys regularly** - Create new access keys periodically
5. **Delete unused keys** - Remove old access keys from IAM

## Cost Information

- **S3 Storage**: ~$0.023 per GB/month
- **Data Transfer**: First 100GB/month is free
- **Requests**: Very cheap (fractions of a cent per 1000 requests)

For this small project, costs should be less than $1/month.

## Need Help?

If you're still having issues:
1. Verify your AWS account is active
2. Check IAM user has correct permissions
3. Ensure bucket name is globally unique
4. Try running in LOCAL MODE first to test the application
