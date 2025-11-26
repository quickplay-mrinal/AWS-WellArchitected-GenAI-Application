#!/usr/bin/env python3
"""
Generate secure keys for AWS Well-Architected GenAI App
Generates SECRET_KEY and ENCRYPTION_KEY and updates AWS Secrets Manager
"""

import secrets
from cryptography.fernet import Fernet
import sys
import subprocess
import json

def generate_keys():
    """Generate SECRET_KEY and ENCRYPTION_KEY"""
    print("🔐 Generating Secure Keys...")
    print("=" * 70)
    
    # Generate SECRET_KEY (for JWT)
    secret_key = secrets.token_urlsafe(32)
    print(f"✅ SECRET_KEY generated: {secret_key}")
    
    # Generate ENCRYPTION_KEY (for Fernet)
    encryption_key = Fernet.generate_key().decode()
    print(f"✅ ENCRYPTION_KEY generated: {encryption_key}")
    
    print("=" * 70)
    
    return secret_key, encryption_key

def update_secrets_manager(secret_key, encryption_key, region='ap-southeast-1'):
    """Update AWS Secrets Manager with generated keys"""
    
    secret_string = {
        "SECRET_KEY": secret_key,
        "ENCRYPTION_KEY": encryption_key,
        "BEDROCK_INFERENCE_PROFILE_ARN": "arn:aws:bedrock:ap-southeast-1:892345653395:inference-profile/apac.anthropic.claude-sonnet-4-5-20250929-v1:0"
    }
    
    print("\n📤 Updating AWS Secrets Manager...")
    print(f"   Secret ID: wellarchitected/backend/secrets")
    print(f"   Region: {region}")
    
    try:
        # Update secret using AWS CLI
        cmd = [
            'aws', 'secretsmanager', 'update-secret',
            '--secret-id', 'wellarchitected/backend/secrets',
            '--secret-string', json.dumps(secret_string),
            '--region', region
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        print("✅ Secrets Manager updated successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error updating Secrets Manager: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ AWS CLI not found. Please install AWS CLI first.")
        return False

def save_to_env_file(secret_key, encryption_key):
    """Save keys to .env file for local development"""
    
    env_content = f"""# Generated Keys - DO NOT COMMIT TO GIT
SECRET_KEY={secret_key}
ENCRYPTION_KEY={encryption_key}
BEDROCK_INFERENCE_PROFILE_ARN=arn:aws:bedrock:ap-southeast-1:892345653395:inference-profile/apac.anthropic.claude-sonnet-4-5-20250929-v1:0
"""
    
    try:
        with open('backend/.env.generated', 'w') as f:
            f.write(env_content)
        print(f"\n💾 Keys saved to: backend/.env.generated")
        print("   (Copy these to your backend/.env file)")
        return True
    except Exception as e:
        print(f"❌ Error saving to file: {e}")
        return False

def main():
    """Main function"""
    
    print("\n" + "=" * 70)
    print("🔑 AWS Well-Architected GenAI App - Secret Key Generator")
    print("=" * 70 + "\n")
    
    # Generate keys
    secret_key, encryption_key = generate_keys()
    
    # Ask user what to do
    print("\n📋 What would you like to do?")
    print("   1. Update AWS Secrets Manager (recommended)")
    print("   2. Save to local file only")
    print("   3. Both")
    print("   4. Just display (no save)")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        update_secrets_manager(secret_key, encryption_key)
    elif choice == '2':
        save_to_env_file(secret_key, encryption_key)
    elif choice == '3':
        update_secrets_manager(secret_key, encryption_key)
        save_to_env_file(secret_key, encryption_key)
    elif choice == '4':
        print("\n📋 Generated Keys (copy these manually):")
        print("=" * 70)
        print(f"SECRET_KEY={secret_key}")
        print(f"ENCRYPTION_KEY={encryption_key}")
        print("=" * 70)
    else:
        print("❌ Invalid choice")
        sys.exit(1)
    
    # Display AWS CLI command for manual update
    print("\n" + "=" * 70)
    print("📝 Manual AWS CLI Command (if needed):")
    print("=" * 70)
    print(f"""
aws secretsmanager update-secret \\
  --secret-id wellarchitected/backend/secrets \\
  --secret-string '{{
    "SECRET_KEY": "{secret_key}",
    "ENCRYPTION_KEY": "{encryption_key}",
    "BEDROCK_INFERENCE_PROFILE_ARN": "arn:aws:bedrock:ap-southeast-1:892345653395:inference-profile/apac.anthropic.claude-sonnet-4-5-20250929-v1:0"
  }}' \\
  --region ap-southeast-1
""")
    
    print("\n✅ Done! Your secrets are ready to use.")
    print("\n⚠️  IMPORTANT: Keep these keys secure and never commit them to Git!\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
