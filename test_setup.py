#!/usr/bin/env python3
"""
Test script to verify the AWS S3 File Storage System setup
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import flask
        print("[OK] Flask imported successfully")
    except ImportError as e:
        print(f"[ERROR] Flask import failed: {e}")
        return False
    
    try:
        import boto3
        print("[OK] boto3 imported successfully")
    except ImportError as e:
        print(f"[ERROR] boto3 import failed: {e}")
        return False
    
    try:
        from botocore.exceptions import ClientError
        print("[OK] botocore imported successfully")
    except ImportError as e:
        print(f"[ERROR] botocore import failed: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("[OK] python-dotenv imported successfully")
    except ImportError as e:
        print(f"[ERROR] python-dotenv import failed: {e}")
        return False
    
    return True

def test_env_file():
    """Test if .env file exists and has required variables"""
    print("\nTesting environment configuration...")
    
    if not os.path.exists('.env'):
        print("[ERROR] .env file not found")
        print("  Please copy .env.example to .env and fill in your AWS credentials")
        return False
    
    print("[OK] .env file exists")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY', 
        'S3_BUCKET_NAME'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var)
        if not value or value.startswith('your_'):
            missing_vars.append(var)
        else:
            print(f"[OK] {var} is set")
    
    if missing_vars:
        print(f"[ERROR] Missing or placeholder values for: {', '.join(missing_vars)}")
        print("  Please update your .env file with actual AWS credentials")
        return False
    
    return True

def test_app_syntax():
    """Test if app.py has valid syntax"""
    print("\nTesting app.py syntax...")
    
    try:
        import py_compile
        py_compile.compile('app.py', doraise=True)
        print("[OK] app.py syntax is valid")
        return True
    except py_compile.PyCompileError as e:
        print(f"[ERROR] app.py syntax error: {e}")
        return False

def main():
    """Run all tests"""
    print("AWS S3 File Storage System - Setup Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_env_file,
        test_app_syntax
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("[SUCCESS] All tests passed! Your setup looks good.")
        print("You can now run: python app.py")
    else:
        print("[FAILED] Some tests failed. Please fix the issues above.")
        print("Run this script again after fixing the issues.")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())