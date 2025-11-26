"""Quick test script to verify authentication setup"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Authentication Setup Check")
print("=" * 60)

# Check environment variables
print("\n1. Environment Variables:")
required_vars = ['SECRET_KEY', 'ENCRYPTION_KEY', 'AWS_REGION', 'DYNAMODB_TABLE_NAME']
all_ok = True

for var in required_vars:
    value = os.getenv(var)
    if not value:
        print(f"   ✗ {var}: NOT SET")
        all_ok = False
    elif value.startswith('your-') or value.startswith('change-this'):
        print(f"   ✗ {var}: PLACEHOLDER VALUE")
        all_ok = False
    else:
        print(f"   ✓ {var}: Set")

# Check AWS credentials
aws_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')

if not aws_key or aws_key == 'your-access-key-here':
    print(f"   ✗ AWS_ACCESS_KEY_ID: NOT SET OR PLACEHOLDER")
    all_ok = False
else:
    print(f"   ✓ AWS_ACCESS_KEY_ID: Set")

if not aws_secret or aws_secret == 'your-secret-key-here':
    print(f"   ✗ AWS_SECRET_ACCESS_KEY: NOT SET OR PLACEHOLDER")
    all_ok = False
else:
    print(f"   ✓ AWS_SECRET_ACCESS_KEY: Set")

# Test DynamoDB connection
print("\n2. DynamoDB Connection:")
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    
    dynamodb = boto3.client('dynamodb', region_name=os.getenv('AWS_REGION'))
    table_name = os.getenv('DYNAMODB_TABLE_NAME')
    
    response = dynamodb.describe_table(TableName=table_name)
    print(f"   ✓ Table '{table_name}' exists")
    print(f"   ✓ Status: {response['Table']['TableStatus']}")
    print(f"   ✓ Region: {os.getenv('AWS_REGION')}")
except NoCredentialsError:
    print("   ✗ AWS credentials not configured")
    all_ok = False
except ClientError as e:
    if e.response['Error']['Code'] == 'ResourceNotFoundException':
        print(f"   ✗ Table '{table_name}' not found")
    else:
        print(f"   ✗ Error: {e}")
    all_ok = False
except Exception as e:
    print(f"   ✗ Error: {e}")
    all_ok = False

# Test imports
print("\n3. Python Dependencies:")
try:
    from fastapi import FastAPI
    from jose import jwt
    from passlib.context import CryptContext
    from cryptography.fernet import Fernet
    print("   ✓ All required packages installed")
except ImportError as e:
    print(f"   ✗ Missing package: {e}")
    all_ok = False

print("\n" + "=" * 60)
if all_ok:
    print("✓ ALL CHECKS PASSED - Ready to start backend!")
    print("\nStart with: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
else:
    print("✗ SOME CHECKS FAILED - Fix issues above")
    print("\nMake sure to:")
    print("1. Add your AWS credentials to .env")
    print("2. Verify DynamoDB table exists in ap-southeast-1")
print("=" * 60)
