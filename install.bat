@echo off
echo Installing AWS S3 File Storage System...
echo.

echo Step 1: Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Step 2: Checking if .env file exists...
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit .env file with your AWS credentials!
    echo Open .env file and replace the placeholder values with your actual AWS credentials.
) else (
    echo .env file already exists.
)

echo.
echo Installation complete!
echo.
echo Next steps:
echo 1. Edit .env file with your AWS credentials
echo 2. Create an S3 bucket in AWS Console
echo 3. Run: python app.py
echo.
pause