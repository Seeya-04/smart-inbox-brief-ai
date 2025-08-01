import pandas as pd
import json
import os
from datetime import datetime, timedelta
import email
from email.header import decode_header
import imaplib
import ssl
from typing import List, Dict, Optional
import re

class EmailReader:
    """Enhanced email reader with IMAP integration and mock capabilities."""
    
    def __init__(self, use_mock=True):
        self.use_mock = use_mock
        self.imap_server = None
        self.connection = None
    
    def connect_imap(self, email_address: str, password: str, imap_server: str = None) -> bool:
        """Connect to IMAP server for live email reading."""
        try:
            # Auto-detect IMAP server if not provided
            if not imap_server:
                domain = email_address.split('@')[1].lower()
                if 'gmail' in domain:
                    imap_server = 'imap.gmail.com'
                elif 'outlook' in domain or 'hotmail' in domain:
                    imap_server = 'outlook.office365.com'
                elif 'yahoo' in domain:
                    imap_server = 'imap.mail.yahoo.com'
                else:
                    print(f"⚠️ Unknown email provider. Please specify IMAP server.")
                    return False
            
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect to server
            self.connection = imaplib.IMAP4_SSL(imap_server, 993, ssl_context=context)
            self.connection.login(email_address, password)
            
            print(f"✅ Successfully connected to {imap_server}")
            return True
            
        except Exception as e:
            print(f"❌ IMAP connection failed: {e}")
            return False
    
    def fetch_live_emails(self, folder='INBOX', limit=10) -> List[Dict]:
        """Fetch emails from live IMAP connection."""
        if not self.connection:
            print("❌ No IMAP connection established")
            return []
        
        try:
            # Select folder
            self.connection.select(folder)
            
            # Search for recent emails
            status, messages = self.connection.search(None, 'ALL')
            email_ids = messages[0].split()
            
            # Get recent emails (limit)
            recent_emails = email_ids[-limit:] if len(email_ids) > limit else email_ids
            
            emails = []
            for email_id in recent_emails:
                try:
                    # Fetch email
                    status, msg_data = self.connection.fetch(email_id, '(RFC822)')
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Parse email
                    parsed_email = self._parse_email_message(email_message, email_id.decode())
                    if parsed_email:
                        emails.append(parsed_email)
                        
                except Exception as e:
                    print(f"⚠️ Error parsing email {email_id}: {e}")
                    continue
            
            print(f"✅ Fetched {len(emails)} emails from {folder}")
            return emails
            
        except Exception as e:
            print(f"❌ Error fetching emails: {e}")
            return []
    
    def _parse_email_message(self, email_message, email_id: str) -> Dict:
        """Parse email message object into structured data."""
        try:
            # Get subject
            subject = self._decode_header(email_message.get("Subject", "No Subject"))
            
            # Get sender
            sender = self._decode_header(email_message.get("From", "Unknown"))
            
            # Get date
            date_str = email_message.get("Date", "")
            received_date = self._parse_date(date_str)
            
            # Get body
            body = self._extract_email_body(email_message)
            
            # Check for image attachments
            has_image_attachments = self._check_image_attachments(email_message)
            
            return {
                'id': f"email_{email_id}",
                'subject': subject,
                'sender': sender,
                'body': body,
                'date': received_date,
                'raw_date': date_str,
                'label': 'inbox',  # Default label
                'has_image_attachments': has_image_attachments
            }
            
        except Exception as e:
            print(f"⚠️ Error parsing email message: {e}")
            return None
            
    def _check_image_attachments(self, email_message) -> bool:
        """Check if email has image attachments."""
        if not email_message.is_multipart():
            return False
            
        for part in email_message.walk():
            content_type = part.get_content_type()
            if content_type.startswith('image/'):
                return True
                
        return False
    
    def _decode_header(self, header) -> str:
        """Decode email header."""
        if not header:
            return ""
        
        try:
            decoded_header = decode_header(header)[0]
            if isinstance(decoded_header[0], bytes):
                return decoded_header[0].decode(decoded_header[1] or 'utf-8')
            return str(decoded_header[0])
        except:
            return str(header)
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse email date string."""
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except:
            return datetime.now()
    
    def _extract_email_body(self, email_message) -> str:
        """Extract text body from email message."""
        body = ""
        
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    elif part.get_content_type() == "text/html" and not body:
                        # Fallback to HTML if no plain text
                        html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        body = self._strip_html(html_body)
            else:
                body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            
            # Clean up body
            body = self._clean_email_body(body)
            
        except Exception as e:
            print(f"⚠️ Error extracting email body: {e}")
            body = "Could not extract email body"
        
        return body
    
    def _strip_html(self, html_text: str) -> str:
        """Basic HTML tag removal."""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', html_text)
    
    def _clean_email_body(self, body: str) -> str:
        """Clean email body text."""
        if not body:
            return ""
        
        # Remove excessive whitespace
        body = re.sub(r'\n\s*\n', '\n\n', body)
        body = re.sub(r' +', ' ', body)
        
        # Limit length for processing
        if len(body) > 2000:
            body = body[:2000] + "... [truncated]"
        
        return body.strip()
    
    def create_enhanced_mock_emails(self) -> List[Dict]:
        """Create enhanced mock emails with realistic content."""
        mock_emails = [
            {
                'id': 'email_001',
                'subject': 'URGENT: Server Downtime Scheduled for Tonight',
                'sender': 'ops-team@company.com',
                'body': '''Hi Team,

We have scheduled emergency server maintenance tonight from 11 PM to 3 AM EST. 
Please complete all critical tasks by 10 PM. 

The following services will be affected:
- Email server
- File sharing system
- Development environment

Please plan accordingly. Contact me immediately if you have concerns.

Best regards,
Operations Team''',
                'date': datetime.now() - timedelta(hours=2),
                'label': 'work',
                'has_image_attachments': False
            },
            {
                'id': 'email_002',
                'subject': 'Weekly Team Meeting - Tomorrow 2 PM',
                'sender': 'sarah.manager@company.com',
                'body': '''Hello everyone,

Reminder about our weekly team meeting tomorrow at 2 PM in Conference Room B.

Agenda:
1. Project status updates
2. Q4 planning discussion
3. New team member introduction

Please bring your project reports. 

Thanks,
Sarah''',
                'date': datetime.now() - timedelta(hours=5),
                'label': 'meeting',
                'has_image_attachments': False
            },
            {
                'id': 'email_003',
                'subject': 'Invoice #12345 - Payment Due in 3 Days',
                'sender': 'billing@vendor.com',
                'body': '''Dear Customer,

This is a friendly reminder that Invoice #12345 for $2,450.00 is due in 3 days (March 15th).

Invoice Details:
- Amount: $2,450.00
- Due Date: March 15, 2024
- Payment Method: Bank transfer or credit card

Please process payment to avoid late fees.

Customer Service Team''',
                'date': datetime.now() - timedelta(hours=8),
                'label': 'financial',
                'has_image_attachments': False
            },
            {
                'id': 'email_004',
                'subject': '🎉 50% OFF Everything - Limited Time!',
                'sender': 'deals@onlinestore.com',
                'body': '''🛍️ MEGA SALE ALERT! 🛍️

Get 50% OFF everything in our store this weekend only!

✅ Free shipping on orders over $50
✅ Extended return policy
✅ Exclusive member prices

Use code: SAVE50

Shop now before items sell out!

Happy Shopping!''',
                'date': datetime.now() - timedelta(hours=12),
                'label': 'promotional',
                'has_image_attachments': True
            },
            {
                'id': 'email_005',
                'subject': 'Re: Project Alpha - Need Your Input ASAP',
                'sender': 'john.colleague@company.com',
                'body': '''Hi,

Thanks for the project update. I reviewed the documents and have a few questions:

1. Can we move the deadline to next Friday?
2. Do we have budget for additional resources?
3. Who will handle the client presentation?

This is quite urgent as the client meeting is tomorrow. Please get back to me ASAP.

Thanks,
John''',
                'date': datetime.now() - timedelta(hours=1),
                'label': 'urgent',
                'has_image_attachments': False
            },
            {
                'id': 'email_006',
                'subject': 'Your Monthly Newsletter - Tech Trends',
                'sender': 'newsletter@techblog.com',
                'body': '''📱 This Month in Technology

Top stories this month:
• AI developments in healthcare
• New smartphone releases
• Cybersecurity best practices

Read full articles on our website.

Tech Blog Team''',
                'date': datetime.now() - timedelta(days=1),
                'label': 'newsletter',
                'has_image_attachments': False
            },
            {
                'id': 'email_007',
                'subject': 'Lunch meeting today - 12:30 PM',
                'sender': 'client@importantcorp.com',
                'body': '''Hi,

Looking forward to our lunch meeting today at 12:30 PM at The Blue Restaurant.

I'll bring the contract documents for review. Please confirm if you're still available.

Best regards,
Michael Chen
Important Corp''',
                'date': datetime.now() - timedelta(minutes=30),
                'label': 'meeting',
                'has_image_attachments': False
            },
            {
                'id': 'email_008',
                'subject': 'Password Reset Required',
                'sender': 'security@company.com',
                'body': '''Security Alert,

We detected unusual login activity on your account. As a precaution, please reset your password immediately.

Click here to reset: [SECURE LINK]

If you did not request this, contact IT support immediately.

Security Team''',
                'date': datetime.now() - timedelta(minutes=45),
                'label': 'security',
                'has_image_attachments': False
            },
            {
                'id': 'email_009',
                'subject': 'Project Screenshots for Review',
                'sender': 'design-team@company.com',
                'body': '''Hi Team,

I've attached the latest screenshots of our UI design for the new project. Please review them and provide feedback by tomorrow.

The images show the new dashboard layout and mobile responsive views.

Let me know what you think!

Best regards,
Design Team''',
                'date': datetime.now() - timedelta(hours=1),
                'label': 'work',
                'has_image_attachments': True
            }
        ]
        
        return mock_emails
    
    def load_emails(self, email_address=None, password=None, limit=10) -> pd.DataFrame:
        """Main method to load emails (mock or live)."""
        if self.use_mock:
            print("📂 Loading mock emails...")
            emails = self.create_enhanced_mock_emails()
        else:
            if not email_address or not password:
                print("❌ Email credentials required for live connection")
                return pd.DataFrame()
            
            print("📡 Connecting to live email...")
            if self.connect_imap(email_address, password):
                emails = self.fetch_live_emails(limit=limit)
            else:
                print("⚠️ Falling back to mock emails")
                emails = self.create_enhanced_mock_emails()
        
        # Convert to DataFrame
        df = pd.DataFrame(emails)
        
        # Ensure all required columns exist
        required_columns = ['id', 'subject', 'sender', 'body', 'date', 'label']
        for col in required_columns:
            if col not in df.columns:
                if col == 'date':
                    df[col] = datetime.now()
                elif col == 'label':
                    df[col] = 'general'
                else:
                    df[col] = f'Unknown {col}'
        
        print(f"✅ Loaded {len(df)} emails successfully")
        return df
    
    def close_connection(self):
        """Close IMAP connection."""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
                print("✅ IMAP connection closed")
            except:
                pass

# Usage examples
if __name__ == "__main__":
    # Mock usage
    reader = EmailReader(use_mock=True)
    mock_emails = reader.load_emails()
    print(f"Mock emails loaded: {len(mock_emails)}")
    
    # Live usage example (commented out)
    """
    reader = EmailReader(use_mock=False)
    live_emails = reader.load_emails(
        email_address="your-email@gmail.com",
        password="your-app-password",
        limit=5
    )
    reader.close_connection()
    """