import json
import os
import getpass
from cryptography.fernet import Fernet
import base64
from typing import Optional, Dict
<<<<<<< HEAD
from datetime import datetime

CREDENTIALS_FILE = 'email_credentials.enc'
=======
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03

class CredentialsManager:
    """Secure credentials manager for storing email credentials."""
    
    def __init__(self, credentials_file='email_credentials.enc'):
        self.credentials_file = credentials_file
        self.key_file = 'encryption_key.key'
        self._load_or_generate_key()
    
    def _load_or_generate_key(self):
        """Load existing encryption key or generate a new one."""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(self.key)
        
        self.cipher = Fernet(self.key)
    
    def save_credentials(self, email_address: str, password: str, provider: str = 'gmail') -> bool:
        """Save encrypted credentials to file."""
        try:
            credentials = {
                'email_address': email_address,
                'password': password,
                'provider': provider,
<<<<<<< HEAD
                'timestamp': str(datetime.now())  # Use current timestamp
=======
                'timestamp': '2024-01-01'  # Placeholder timestamp
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
            }
            
            # Encrypt credentials
            encrypted_data = self.cipher.encrypt(json.dumps(credentials).encode())
            
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted_data)
            
            print(f"✅ Credentials saved for {email_address}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving credentials: {e}")
            return False
    
    def load_credentials(self) -> Optional[Dict]:
        """Load and decrypt credentials from file."""
        try:
            if not os.path.exists(self.credentials_file):
                return None
            
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt credentials
            decrypted_data = self.cipher.decrypt(encrypted_data)
            credentials = json.loads(decrypted_data.decode())
            
            return credentials
            
        except Exception as e:
            print(f"❌ Error loading credentials: {e}")
            return None
    
    def clear_credentials(self) -> bool:
        """Clear stored credentials."""
        try:
            if os.path.exists(self.credentials_file):
                os.remove(self.credentials_file)
                print("✅ Credentials cleared")
                return True
            return False
        except Exception as e:
            print(f"❌ Error clearing credentials: {e}")
            return False
    
    def has_credentials(self) -> bool:
        """Check if credentials are stored."""
        return os.path.exists(self.credentials_file)

def setup_email_credentials():
    """Interactive setup for email credentials."""
    print("🔐 Email Credentials Setup")
    print("=" * 40)
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
    print("📧 For Gmail users:")
    print("   1. Enable 2-Factor Authentication")
    print("   2. Generate an App Password (not your regular password)")
    print("   3. Use the App Password here")
    print("   4. Guide: https://support.google.com/accounts/answer/185833")
    print()
<<<<<<< HEAD
=======
=======
>>>>>>> 9feb104c2eb5dd41ae26edcdb0da84c87c09344e
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
    
    credentials_manager = CredentialsManager()
    
    # Check if credentials already exist
    if credentials_manager.has_credentials():
        print("📧 Found existing credentials!")
        use_existing = input("Use existing credentials? (y/n): ").lower().strip()
        
        if use_existing == 'y':
            credentials = credentials_manager.load_credentials()
            if credentials:
                print(f"✅ Using credentials for: {credentials['email_address']}")
                return credentials
    
    # Get new credentials
    print("\n📧 Enter your email credentials:")
    email_address = input("Email address: ").strip()
<<<<<<< HEAD
    password = getpass.getpass("App password (not regular password): ")
=======
<<<<<<< HEAD
    password = getpass.getpass("App password (not regular password): ")
=======
    password = getpass.getpass("App password: ")
>>>>>>> 9feb104c2eb5dd41ae26edcdb0da84c87c09344e
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
    provider = input("Email provider (gmail/outlook/yahoo): ").strip().lower()
    
    if not provider:
        provider = 'gmail'
    
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
    # Validate email format
    if '@' not in email_address:
        print("❌ Invalid email address format")
        return None
    
    if not password:
        print("❌ Password cannot be empty")
        return None
    
    # Save credentials
    if credentials_manager.save_credentials(email_address, password, provider):
        print("✅ Credentials saved successfully!")
        print("💡 Tip: If connection fails, make sure you're using an App Password, not your regular password")
<<<<<<< HEAD
=======
=======
    # Save credentials
    if credentials_manager.save_credentials(email_address, password, provider):
        print("✅ Credentials saved successfully!")
>>>>>>> 9feb104c2eb5dd41ae26edcdb0da84c87c09344e
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
        return {
            'email_address': email_address,
            'password': password,
            'provider': provider
        }
    else:
        print("❌ Failed to save credentials")
        return None

def get_email_credentials() -> Optional[Dict]:
    """Get email credentials (load from file or prompt user)."""
    credentials_manager = CredentialsManager()
    
    # Try to load existing credentials
    credentials = credentials_manager.load_credentials()
    
    if credentials:
        print(f"📧 Using saved credentials for: {credentials['email_address']}")
        return credentials
    
    # No saved credentials, prompt user
    print("📧 No saved credentials found.")
    setup_choice = input("Would you like to set up email credentials now? (y/n): ").lower().strip()
    
    if setup_choice == 'y':
        return setup_email_credentials()
    else:
        print("⚠️ Using mock emails instead")
        return None

def manage_credentials():
    """Manage stored credentials."""
    credentials_manager = CredentialsManager()
    
    print("🔐 Credentials Management")
    print("=" * 30)
    
    if credentials_manager.has_credentials():
        credentials = credentials_manager.load_credentials()
        if credentials:
            print(f"📧 Current credentials: {credentials['email_address']}")
            print(f"   Provider: {credentials['provider']}")
            
            choice = input("\nOptions:\n1. Use current credentials\n2. Update credentials\n3. Clear credentials\n4. Cancel\n\nChoice: ").strip()
            
            if choice == '1':
                return credentials
            elif choice == '2':
                return setup_email_credentials()
            elif choice == '3':
                credentials_manager.clear_credentials()
                print("✅ Credentials cleared")
                return None
            else:
                print("❌ Cancelled")
                return None
    else:
        print("📧 No saved credentials found")
        setup_choice = input("Set up credentials now? (y/n): ").lower().strip()
        
        if setup_choice == 'y':
            return setup_email_credentials()
        else:
            return None

if __name__ == "__main__":
    # Test the credentials manager
    credentials = get_email_credentials()
    if credentials:
        print(f"✅ Successfully loaded credentials for {credentials['email_address']}")
    else:
<<<<<<< HEAD
        print("❌ No credentials available")
=======
<<<<<<< HEAD
        print("❌ No credentials available")
=======
        print("❌ No credentials available") 
>>>>>>> 9feb104c2eb5dd41ae26edcdb0da84c87c09344e
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
