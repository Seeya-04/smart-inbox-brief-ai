<<<<<<< HEAD
#!/usr/bin/env python3
"""
Smart Inbox Assistant - Main Application
Enhanced with SmartBrief v3 context-aware summarization, feedback system, and multi-platform support.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all modules
from dashboard import create_dashboard
from email_reader import EmailReader
from smart_summarizer_v3 import SmartSummarizerV3, summarize_message
from context_loader import ContextLoader
from feedback_system import FeedbackCollector, FeedbackEnhancedSummarizer
from sentiment import analyze_sentiment_detailed
from priority_model import PriorityModel
from priority_tagging import PriorityTagger
from smart_suggestions import SmartSuggestionsModule
from tts import TextToSpeechEngine
from email_summarizer import EmailSummarizer
from visualizations import create_priority_chart, create_sentiment_chart
from credentials_manager import CredentialsManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_inbox.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SmartInboxAssistant:
    """
    Main Smart Inbox Assistant class with enhanced SmartBrief v3 integration.
    
    Features:
    - Context-aware message summarization
    - Multi-platform support (Email, WhatsApp, Slack, etc.)
    - Intent detection and urgency analysis
    - Feedback learning system
    - Priority tagging and smart suggestions
    - Text-to-speech capabilities
    - Interactive dashboard
    """
    
    def __init__(self, config_file: str = 'config.json'):
        """Initialize the Smart Inbox Assistant."""
        self.config_file = config_file
        self.config = self._load_config()
        
        # Initialize core components
        logger.info("Initializing Smart Inbox Assistant...")
        
        # Credentials manager
        self.credentials_manager = CredentialsManager()
        
        # Email reader
        self.email_reader = EmailReader()
        
        # SmartBrief v3 components
        self.summarizer = SmartSummarizerV3(
            context_file=self.config.get('context_file', 'message_context.json'),
            max_context_messages=self.config.get('max_context_messages', 3)
        )
        
        self.context_loader = ContextLoader(
            json_file=self.config.get('conversation_history_file', 'conversation_history.json'),
            csv_file=self.config.get('message_history_file', 'message_history.csv')
        )
        
        self.feedback_collector = FeedbackCollector(
            feedback_file=self.config.get('feedback_file', 'feedback_data.json')
        )
        
        self.feedback_enhanced_summarizer = FeedbackEnhancedSummarizer(
            context_file=self.config.get('context_file', 'message_context.json'),
            feedback_file=self.config.get('feedback_file', 'feedback_data.json')
        )
        
        # Legacy components (enhanced with new features)
        self.priority_model = PriorityModel()
        self.priority_tagger = PriorityTagger()
        self.smart_suggestions = SmartSuggestionsModule()
        self.tts_engine = TextToSpeechEngine()
        self.email_summarizer = EmailSummarizer()
        
        logger.info("✅ Smart Inbox Assistant initialized successfully!")
    
    def _load_config(self) -> Dict:
        """Load configuration from file."""
        default_config = {
            'context_file': 'message_context.json',
            'conversation_history_file': 'conversation_history.json',
            'message_history_file': 'message_history.csv',
            'feedback_file': 'feedback_data.json',
            'max_context_messages': 3,
            'use_context_awareness': True,
            'enable_feedback_learning': True,
            'supported_platforms': ['email', 'whatsapp', 'slack', 'teams', 'instagram', 'discord'],
            'tts_enabled': True,
            'dashboard_enabled': True
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        return default_config
    
    def _save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def process_message(self, message_data: Dict, platform: str = 'email') -> Dict:
        """
        Process a single message with enhanced SmartBrief v3 analysis.
        
        Args:
            message_data: Message data dictionary
            platform: Platform type (email, whatsapp, slack, etc.)
            
        Returns:
            Comprehensive analysis results
        """
        try:
            # Ensure platform is set
            message_data['platform'] = platform
            
            # Add timestamp if not present
            if 'timestamp' not in message_data:
                message_data['timestamp'] = datetime.now().isoformat()
            
            # SmartBrief v3 analysis
            logger.info(f"Processing message from {message_data.get('user_id', 'unknown')} on {platform}")
            
            smart_analysis = self.feedback_enhanced_summarizer.summarize(
                message_data, 
                use_context=self.config.get('use_context_awareness', True)
            )
            
            # Legacy analysis for compatibility
            message_text = message_data.get('message_text', '')
            
            # Sentiment analysis
            sentiment_analysis = analyze_sentiment_detailed(message_text)
            
            # Priority analysis
            priority_score = self.priority_model.predict_priority(message_text)
            priority_tag = self.priority_tagger.tag_email({
                'subject': message_data.get('subject', ''),
                'body': message_text,
                'sender': message_data.get('sender', message_data.get('user_id', ''))
            })
            
            # Smart suggestions
            suggestions = self.smart_suggestions.generate_suggestions(
                {
                    'subject': message_data.get('subject', ''),
                    'body': message_text,
                    'sender': message_data.get('sender', message_data.get('user_id', '')),
                    'platform': platform,
                    'tag': priority_tag
                },
                priority_tag,
                smart_analysis['confidence']
            )
            
            # Combine all analysis results
            comprehensive_result = {
                # SmartBrief v3 results
                'summary': smart_analysis['summary'],
                'type': smart_analysis['type'],
                'intent': smart_analysis['intent'],
                'urgency': smart_analysis['urgency'],
                'confidence': smart_analysis['confidence'],
                'context_used': smart_analysis['context_used'],
                'platform_optimized': smart_analysis['platform_optimized'],
                'reasoning': smart_analysis['reasoning'],
                
                # Enhanced analysis
                'sentiment': sentiment_analysis,
                'priority_score': priority_score,
                'priority_tag': priority_tag,
                'suggestions': suggestions,
                
                # Metadata
                'platform': platform,
                'processed_at': datetime.now().isoformat(),
                'feedback_ready': smart_analysis.get('feedback_ready', False),
                'message_id': smart_analysis.get('message_id', message_data.get('message_id')),
                
                # Legacy compatibility
                'smart_analysis': smart_analysis,
                'metadata': smart_analysis.get('metadata', {})
            }
            
            # Store in context for future processing
            self.context_loader.add_message(message_data, comprehensive_result)
            
            logger.info(f"✅ Message processed successfully: {comprehensive_result['summary']}")
            return comprehensive_result
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                'summary': 'Error processing message',
                'type': 'error',
                'intent': 'unknown',
                'urgency': 'low',
                'confidence': 0.0,
                'error': str(e),
                'processed_at': datetime.now().isoformat()
            }
    
    def process_emails(self, limit: int = 10) -> List[Dict]:
        """
        Process recent emails with enhanced analysis.
        
        Args:
            limit: Maximum number of emails to process
            
        Returns:
            List of processed email results
        """
        try:
            logger.info(f"Processing {limit} recent emails...")
            
            # Fetch emails
            emails = self.email_reader.fetch_recent_emails(limit)
            
            if not emails:
                logger.warning("No emails found to process")
                return []
            
            results = []
            for email in emails:
                # Convert email to message format
                message_data = {
                    'user_id': email.get('sender', 'unknown'),
                    'platform': 'email',
                    'message_text': email.get('body', ''),
                    'subject': email.get('subject', ''),
                    'sender': email.get('sender', ''),
                    'timestamp': email.get('date', datetime.now().isoformat()),
                    'message_id': email.get('id', f"email_{datetime.now().timestamp()}")
                }
                
                # Process with enhanced analysis
                result = self.process_message(message_data, 'email')
                result['original_email'] = email  # Keep original email data
                
                results.append(result)
            
            logger.info(f"✅ Processed {len(results)} emails successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error processing emails: {e}")
            return []
    
    def collect_feedback(self, message_id: str, user_id: str, platform: str, 
                        original_text: str, generated_summary: str, 
                        feedback_score: int, feedback_comment: str = "",
                        category_ratings: Dict[str, int] = None) -> bool:
        """
        Collect user feedback for continuous improvement.
        
        Args:
            message_id: Unique message identifier
            user_id: User who provided feedback
            platform: Platform where message originated
            original_text: Original message text
            generated_summary: Generated summary
            feedback_score: Overall feedback score (-1, 0, 1)
            feedback_comment: Optional comment
            category_ratings: Category-specific ratings
            
        Returns:
            Success status
        """
        return self.feedback_collector.collect_feedback(
            message_id=message_id,
            user_id=user_id,
            platform=platform,
            original_text=original_text,
            generated_summary=generated_summary,
            feedback_score=feedback_score,
            feedback_comment=feedback_comment,
            category_ratings=category_ratings
        )
    
    def get_analytics(self) -> Dict:
        """Get comprehensive analytics from all components."""
        try:
            # SmartBrief v3 analytics
            summarizer_stats = self.summarizer.get_stats()
            context_stats = self.context_loader.get_statistics()
            feedback_analytics = self.feedback_collector.get_feedback_analytics()
            
            # Smart suggestions analytics
            suggestions_stats = self.smart_suggestions.get_suggestion_stats()
            
            return {
                'summarizer_stats': summarizer_stats,
                'context_stats': context_stats,
                'feedback_analytics': feedback_analytics,
                'suggestions_stats': suggestions_stats,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating analytics: {e}")
            return {'error': str(e)}
    
    def speak_summary(self, text: str) -> bool:
        """Convert text to speech using TTS engine."""
        if self.config.get('tts_enabled', True):
            return self.tts_engine.speak(text)
        return False
    
    def run_dashboard(self):
        """Launch the interactive dashboard."""
        if self.config.get('dashboard_enabled', True):
            logger.info("Launching interactive dashboard...")
            try:
                # Import and run Streamlit dashboard
                import subprocess
                import sys
                
                # Run the Streamlit app
                subprocess.run([
                    sys.executable, '-m', 'streamlit', 'run', 
                    'demo_streamlit_app.py', 
                    '--server.port', '8501',
                    '--server.headless', 'false'
                ])
            except Exception as e:
                logger.error(f"Error launching dashboard: {e}")
                # Fallback to basic dashboard
                create_dashboard()
        else:
            logger.info("Dashboard is disabled in configuration")
    
    def run_cli(self):
        """Run the command-line interface."""
        print("🤖 Smart Inbox Assistant - Enhanced with SmartBrief v3")
        print("=" * 60)
        
        while True:
            print("\nAvailable commands:")
            print("1. Process recent emails")
            print("2. Analyze single message")
            print("3. View analytics")
            print("4. Launch dashboard")
            print("5. Test message (demo)")
            print("6. Export data")
            print("7. Settings")
            print("0. Exit")
            
            try:
                choice = input("\nEnter your choice (0-7): ").strip()
                
                if choice == '0':
                    print("👋 Goodbye!")
                    break
                
                elif choice == '1':
                    limit = int(input("Number of emails to process (default 10): ") or "10")
                    results = self.process_emails(limit)
                    
                    print(f"\n📧 Processed {len(results)} emails:")
                    for i, result in enumerate(results[:5], 1):  # Show first 5
                        print(f"\n{i}. {result['summary']}")
                        print(f"   Type: {result['type']} | Intent: {result['intent']} | Urgency: {result['urgency']}")
                        print(f"   Confidence: {result['confidence']:.2f} | Context: {'Yes' if result['context_used'] else 'No'}")
                        
                        if self.config.get('tts_enabled'):
                            speak = input("   Speak summary? (y/n): ").lower() == 'y'
                            if speak:
                                self.speak_summary(result['summary'])
                
                elif choice == '2':
                    print("\n📝 Analyze Single Message")
                    user_id = input("User ID: ") or "demo_user"
                    platform = input("Platform (email/whatsapp/slack/teams/instagram): ") or "email"
                    message_text = input("Message text: ")
                    
                    if message_text:
                        message_data = {
                            'user_id': user_id,
                            'platform': platform,
                            'message_text': message_text,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        result = self.process_message(message_data, platform)
                        
                        print(f"\n📊 Analysis Results:")
                        print(f"Summary: {result['summary']}")
                        print(f"Type: {result['type']}")
                        print(f"Intent: {result['intent']}")
                        print(f"Urgency: {result['urgency']}")
                        print(f"Confidence: {result['confidence']:.2f}")
                        print(f"Context Used: {'Yes' if result['context_used'] else 'No'}")
                        print(f"Platform Optimized: {'Yes' if result['platform_optimized'] else 'No'}")
                        
                        print(f"\nReasoning:")
                        for reason in result['reasoning']:
                            print(f"  • {reason}")
                        
                        # Feedback collection
                        if result.get('feedback_ready')):
                            collect_feedback = input("\nProvide feedback? (y/n): ").lower() == 'y'
                            if collect_feedback:
                                feedback_score = int(input("Rate summary (1=good, 0=neutral, -1=poor): ") or "0")
                                feedback_comment = input("Optional comment: ")
                                
                                success = self.collect_feedback(
                                    message_id=result['message_id'],
                                    user_id=user_id,
                                    platform=platform,
                                    original_text=message_text,
                                    generated_summary=result['summary'],
                                    feedback_score=feedback_score,
                                    feedback_comment=feedback_comment
                                )
                                
                                if success:
                                    print("✅ Feedback collected successfully!")
                                else:
                                    print("❌ Failed to collect feedback")
                
                elif choice == '3':
                    print("\n📊 Analytics Dashboard")
                    analytics = self.get_analytics()
                    
                    if 'error' not in analytics:
                        print(f"\n📈 Summarizer Stats:")
                        stats = analytics['summarizer_stats']
                        print(f"  Messages Processed: {stats['processed']}")
                        print(f"  Context Usage Rate: {stats['context_usage_rate']:.1%}")
                        print(f"  Unique Users: {stats['unique_users']}")
                        print(f"  Platforms: {list(stats['platforms'].keys())}")
                        
                        print(f"\n🔄 Feedback Analytics:")
                        feedback = analytics['feedback_analytics']['overall_metrics']
                        if feedback.get('total_feedback', 0) > 0:
                            print(f"  Total Feedback: {feedback['total_feedback']}")
                            print(f"  Satisfaction Rate: {feedback.get('satisfaction_rate', 0):.1%}")
                            print(f"  Positive: {feedback['positive_feedback']}")
                            print(f"  Negative: {feedback['negative_feedback']}")
                        else:
                            print("  No feedback data available yet")
                    else:
                        print(f"Error generating analytics: {analytics['error']}")
                
                elif choice == '4':
                    print("\n🚀 Launching Interactive Dashboard...")
                    self.run_dashboard()
                
                elif choice == '5':
                    print("\n🧪 Demo Mode - Testing Sample Messages")
                    
                    demo_messages = [
                        {
                            'user_id': 'alice_work',
                            'platform': 'email',
                            'message_text': 'I will send the quarterly report tonight after the meeting.',
                        },
                        {
                            'user_id': 'alice_work',
                            'platform': 'email',
                            'message_text': 'Hey, did the report get done?',
                        },
                        {
                            'user_id': 'bob_friend',
                            'platform': 'whatsapp',
                            'message_text': 'yo whats up? party tonight at 8pm, u coming?',
                        },
                        {
                            'user_id': 'customer_insta',
                            'platform': 'instagram',
                            'message_text': 'love ur latest post! 😍 where did u get that dress?',
                        }
                    ]
                    
                    for i, message in enumerate(demo_messages, 1):
                        print(f"\n--- Demo Message {i} ({message['platform']}) ---")
                        result = self.process_message(message, message['platform'])
                        
                        print(f"Original: {message['message_text']}")
                        print(f"Summary: {result['summary']}")
                        print(f"Type: {result['type']} | Intent: {result['intent']} | Urgency: {result['urgency']}")
                        print(f"Context Used: {'Yes' if result['context_used'] else 'No'}")
                
                elif choice == '6':
                    print("\n💾 Export Data")
                    export_format = input("Format (json/csv): ").lower() or "json"
                    filename = input(f"Filename (default: export.{export_format}): ") or f"export.{export_format}"
                    
                    try:
                        success = self.context_loader.export_data(filename, export_format)
                        if success:
                            print(f"✅ Data exported to {filename}")
                        else:
                            print("❌ Export failed")
                    except Exception as e:
                        print(f"❌ Export error: {e}")
                
                elif choice == '7':
                    print("\n⚙️ Settings")
                    print(f"Current settings:")
                    print(f"  Context Awareness: {'Enabled' if self.config.get('use_context_awareness') else 'Disabled'}")
                    print(f"  Max Context Messages: {self.config.get('max_context_messages', 3)}")
                    print(f"  TTS Enabled: {'Yes' if self.config.get('tts_enabled') else 'No'}")
                    print(f"  Feedback Learning: {'Enabled' if self.config.get('enable_feedback_learning') else 'Disabled'}")
                    
                    modify = input("\nModify settings? (y/n): ").lower() == 'y'
                    if modify:
                        self.config['use_context_awareness'] = input("Enable context awareness? (y/n): ").lower() == 'y'
                        self.config['max_context_messages'] = int(input("Max context messages (1-10): ") or "3")
                        self.config['tts_enabled'] = input("Enable TTS? (y/n): ").lower() == 'y'
                        self.config['enable_feedback_learning'] = input("Enable feedback learning? (y/n): ").lower() == 'y'
                        
                        self._save_config()
                        print("✅ Settings saved!")
                
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                logger.error(f"CLI error: {e}")

def main():
    """Main entry point for the Smart Inbox Assistant."""
    try:
        # Initialize the assistant
        assistant = SmartInboxAssistant()
        
        # Check command line arguments
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == 'dashboard':
                assistant.run_dashboard()
            elif command == 'process':
                limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
                results = assistant.process_emails(limit)
                print(f"Processed {len(results)} emails")
            elif command == 'analytics':
                analytics = assistant.get_analytics()
                print(json.dumps(analytics, indent=2, default=str))
            elif command == 'demo':
                # Quick demo
                result = summarize_message(
                    "Hey, did the report get done? The board meeting is tomorrow!",
                    platform='email',
                    user_id='demo_user'
                )
                print(f"Demo Summary: {result['summary']}")
                print(f"Type: {result['type']} | Intent: {result['intent']} | Urgency: {result['urgency']}")
            else:
                print(f"Unknown command: {command}")
                print("Available commands: dashboard, process, analytics, demo")
        else:
            # Run CLI interface
            assistant.run_cli()
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
=======
from email_reader import EmailReader
from email_agent import EmailAgent
from sentiment import analyze_sentiment
from priority_model import Prioritizer
from priority_tagging import PriorityTagger
from smart_suggestions import SmartSuggestionsModule
from smart_metrics import extract_email_metrics
from briefing import generate_daily_brief
from tts import read_text
from credentials_manager import get_email_credentials, manage_credentials
import pandas as pd
from datetime import datetime
import json

def main():
    """Enhanced main function with priority tagging and smart suggestions."""
    print("📬 Smart Inbox Brief AI v2.0")
    print("From Summary to Action: Priority Tagging + Feedback Learning Loop")
    print("=" * 70)
    
    # Initialize components
    print("🤖 Initializing AI components...")
    agent = EmailAgent()
    prioritizer = Prioritizer()
    tagger = PriorityTagger()
    suggestions_module = SmartSuggestionsModule()
    
    # Email connection setup
    print("\n📧 Email Connection Setup")
    print("=" * 40)
    
    # Try to get saved credentials first
    credentials = get_email_credentials()
    
    if credentials:
        print(f"\n📡 Connecting to {credentials['email_address']}...")
        email_reader = EmailReader(use_mock=False)
        
        if email_reader.connect_imap(credentials['email_address'], credentials['password']):
            email_limit = int(input("Number of emails to fetch (default 10): ") or "10")
            emails_df = email_reader.load_emails(
                email_address=credentials['email_address'],
                password=credentials['password'],
                limit=email_limit
            )
            email_reader.close_connection()
        else:
            print("⚠️ Live email connection failed. Using mock emails instead.")
            emails_df = EmailReader(use_mock=True).load_emails()
    else:
        print("📂 Using mock emails...")
        email_reader = EmailReader(use_mock=True)
        emails_df = email_reader.load_emails()
    
    print(f"✅ Loaded {len(emails_df)} emails successfully")
    
    # Process emails with enhanced analysis
    print("\n📊 Processing emails with AI analysis...")
    processed_emails = []
    processing_stats = {
        'tags': {},
        'confidence_levels': {'high': 0, 'medium': 0, 'low': 0},
        'sentiments': {'positive': 0, 'neutral': 0, 'negative': 0},
        'urgency_levels': {'high': 0, 'medium': 0, 'low': 0}
    }
    
    for idx, row in emails_df.iterrows():
        email_dict = row.to_dict()
        
        # Extract enhanced metrics
        body = email_dict.get('body', '')
        subject = email_dict.get('subject', '')
        full_text = f"{subject} {body}"
        
        # AI Analysis Pipeline
        print(f"Processing email {idx + 1}/{len(emails_df)}: {subject[:50]}...")
        
        # 1. Basic classification and sentiment
        category = agent.classify(body)
        sentiment_score = analyze_sentiment(body)
        
        # 2. Smart metrics extraction
        metrics = extract_email_metrics(full_text)
        
        # 3. Priority tagging with reasoning
        tag_result = tagger.tag_email(email_dict)
        
        # 4. Generate smart suggestions
        suggestions = suggestions_module.generate_suggestions(
            email_dict, tag_result['tag'], tag_result['confidence']
        )
        
        # Create enriched email object
        enriched_email = {
            **email_dict,
            'category': category,
            'sentiment_score': sentiment_score,
            'metrics': metrics,
            'tag': tag_result['tag'],
            'tag_confidence': tag_result['confidence'],
            'tag_reasoning': tag_result['reasoning'],
            'all_tag_scores': tag_result['all_scores'],
            'features_detected': tag_result['features_detected'],
            'smart_suggestions': suggestions,
            'processing_timestamp': datetime.now()
        }
        
        processed_emails.append(enriched_email)
        
        # Update statistics
        tag = tag_result['tag']
        processing_stats['tags'][tag] = processing_stats['tags'].get(tag, 0) + 1
        
        confidence = tag_result['confidence']
        if confidence > 0.7:
            processing_stats['confidence_levels']['high'] += 1
        elif confidence > 0.4:
            processing_stats['confidence_levels']['medium'] += 1
        else:
            processing_stats['confidence_levels']['low'] += 1
        
        if sentiment_score > 0.1:
            processing_stats['sentiments']['positive'] += 1
        elif sentiment_score < -0.1:
            processing_stats['sentiments']['negative'] += 1
        else:
            processing_stats['sentiments']['neutral'] += 1
        
        urgency = metrics['urgency']
        processing_stats['urgency_levels'][urgency] += 1
    
    print(f"✅ Enhanced processing complete for {len(processed_emails)} emails")
    
    # Prioritize emails using reinforcement learning
    print("\n🏆 Prioritizing emails with reinforcement learning...")
    prioritized_emails = prioritizer.prioritize_emails(processed_emails)
    
    # Display Processing Results
    print("\n" + "="*70)
    print("📋 ENHANCED PROCESSING RESULTS")
    print("="*70)
    
    # Processing Statistics
    print(f"\n📊 PROCESSING STATISTICS:")
    print(f"   • Total emails processed: {len(processed_emails)}")
    print(f"   • Tag distribution: {dict(sorted(processing_stats['tags'].items(), key=lambda x: x[1], reverse=True))}")
    print(f"   • Confidence levels: {processing_stats['confidence_levels']}")
    print(f"   • Sentiment distribution: {processing_stats['sentiments']}")
    print(f"   • Urgency levels: {processing_stats['urgency_levels']}")
    
    # Top prioritized emails with enhanced display
    print(f"\n🔝 TOP 10 PRIORITIZED EMAILS:")
    print("-" * 70)
    
    for i, (score, email) in enumerate(prioritized_emails[:10], 1):
        tag = email.get('tag', 'GENERAL')
        confidence = email.get('tag_confidence', 0)
        suggestions_count = len(email.get('smart_suggestions', []))
        
        # Create priority indicator
        if i <= 3:
            priority_icon = "🔥"
        elif i <= 7:
            priority_icon = "⚡"
        else:
            priority_icon = "📧"
        
        print(f"{priority_icon} {i}. [{score:.2f}] {email.get('subject', 'No Subject')}")
        print(f"     From: {email.get('sender', 'Unknown')}")
        print(f"     Tag: {tag} (Confidence: {confidence:.1%}) | Suggestions: {suggestions_count}")
        
        # Show reasoning if available
        reasoning = email.get('tag_reasoning', [])
        if reasoning:
            print(f"     Reasoning: {', '.join(reasoning[:2])}...")  # Show first 2 reasons
        
        print()
    
    # Interactive section
    print("\n" + "="*70)
    print("🎯 INTERACTIVE FEATURES")
    print("="*70)
    
    while True:
        print("\nWhat would you like to do?")
        print("1. 📄 Generate daily brief")
        print("2. 🔊 Read email aloud")
        print("3. 💡 View smart suggestions")
        print("4. 🏷️ Provide tag feedback")
        print("5. 📊 View learning statistics")
        print("6. 🔍 Search emails")
        print("7. 💬 Quick demo interaction")
        print("8. 🔐 Manage email credentials")
        print("9. 🚪 Exit")
        
        choice = input("\nEnter your choice (1-9): ").strip()
        
        if choice == '1':
            # Generate and display daily brief
            top_emails = []
            for i, (score, email) in enumerate(prioritized_emails[:10]):
                email_copy = email.copy()
                email_copy['priority_level'] = 'HIGH' if i < 3 else 'MEDIUM' if i < 7 else 'LOW'
                email_copy['priority_score'] = score
                email_copy['read_status'] = 'unread'
                email_copy['message_type'] = email_copy.get('metrics', {}).get('intent', 'general')
                email_copy['timestamp'] = email_copy.get('date', datetime.now())
                
                # Generate key points
                key_points = []
                if email_copy.get('metrics', {}).get('has_deadline'):
                    key_points.append("⏰ Contains deadline")
                if email_copy.get('tag') == 'URGENT':
                    key_points.append("🚨 Tagged as urgent")
                if email_copy.get('metrics', {}).get('urgency') == 'high':
                    key_points.append("🔥 High urgency detected")
                if email_copy.get('sentiment_score', 0) < -0.1:
                    key_points.append("😟 Negative sentiment")
                
                email_copy['key_points'] = key_points if key_points else ["📧 Standard email"]
                top_emails.append(email_copy)
            
            brief = generate_daily_brief(top_emails)
            print(brief)
            
            # Offer to read aloud
            if input("\n🔊 Read brief aloud? (y/n): ").lower().strip() == 'y':
                read_text(brief)
        
        elif choice == '2':
            # Read specific email aloud
            try:
                email_num = int(input("Enter email number to read (1-10): ")) - 1
                if 0 <= email_num < min(10, len(prioritized_emails)):
                    email = prioritized_emails[email_num][1]
                    email_text = f"Email from {email.get('sender', 'unknown sender')}. Subject: {email.get('subject', 'no subject')}. {email.get('body', 'no content')}"
                    print(f"🔊 Reading email: {email.get('subject', 'No Subject')[:50]}...")
                    read_text(email_text)
                else:
                    print("❌ Invalid email number")
            except ValueError:
                print("❌ Please enter a valid number")
        
        elif choice == '3':
            # View smart suggestions for an email
            try:
                email_num = int(input("Enter email number for suggestions (1-10): ")) - 1
                if 0 <= email_num < min(10, len(prioritized_emails)):
                    email = prioritized_emails[email_num][1]
                    suggestions = email.get('smart_suggestions', [])
                    
                    print(f"\n💡 Smart Suggestions for: {email.get('subject', 'No Subject')}")
                    print("-" * 50)
                    
                    for i, suggestion in enumerate(suggestions, 1):
                        print(f"{i}. {suggestion['text']}")
                        print(f"   Context: {suggestion.get('context', 'N/A')}")
                        print(f"   Estimated time: {suggestion.get('estimated_time', 'N/A')}")
                        print(f"   Confidence: {suggestion.get('confidence', 0):.1%}")
                        print()
                    
                    # Execute suggestion
                    if suggestions and input("Execute a suggestion? (y/n): ").lower().strip() == 'y':
                        try:
                            suggestion_num = int(input(f"Enter suggestion number (1-{len(suggestions)}): ")) - 1
                            if 0 <= suggestion_num < len(suggestions):
                                suggestion = suggestions[suggestion_num]
                                result = suggestions_module.execute_suggestion(email, suggestion['action'])
                                print(f"✅ {result['message']}")
                            else:
                                print("❌ Invalid suggestion number")
                        except ValueError:
                            print("❌ Please enter a valid number")
                else:
                    print("❌ Invalid email number")
            except ValueError:
                print("❌ Please enter a valid number")
        
        elif choice == '4':
            # Provide tag feedback
            try:
                email_num = int(input("Enter email number for tag feedback (1-10): ")) - 1
                if 0 <= email_num < min(10, len(prioritized_emails)):
                    email = prioritized_emails[email_num][1]
                    current_tag = email.get('tag', 'GENERAL')
                    
                    print(f"\nEmail: {email.get('subject', 'No Subject')}")
                    print(f"Current tag: {current_tag}")
                    print(f"Confidence: {email.get('tag_confidence', 0):.1%}")
                    
                    available_tags = ['URGENT', 'MEETING', 'FINANCIAL', 'IMPORTANT', 'PROMOTIONAL', 'NEWSLETTER', 'SECURITY', 'GENERAL']
                    print(f"Available tags: {', '.join(available_tags)}")
                    
                    new_tag = input("Enter correct tag (or press Enter to keep current): ").strip().upper()
                    
                    if new_tag and new_tag in available_tags:
                        email_id = email.get('id', f'email_{email_num}')
                        sender = email.get('sender', 'unknown')
                        
                        # Ask for feedback quality
                        print("\nHow confident are you about this tag correction?")
                        print("1. Very confident (Helpful)")
                        print("2. Somewhat confident (Neutral)")
                        print("3. Not sure (Not helpful)")
                        
                        try:
                            quality_choice = int(input("Enter your confidence (1-3): ").strip())
                            
                            # Map choice to feedback quality value
                            feedback_quality = 1.0  # Default to helpful
                            if quality_choice == 2:
                                feedback_quality = 0.0  # Neutral
                            elif quality_choice == 3:
                                feedback_quality = -1.0  # Not helpful
                            
                            # Process feedback with quality
                            tagger.process_feedback(email_id, new_tag, current_tag, sender, feedback_quality=feedback_quality)
                            
                            quality_text = "Very confident" if quality_choice == 1 else "Somewhat confident" if quality_choice == 2 else "Not sure"
                            print(f"✅ Feedback recorded: {current_tag} → {new_tag} (Quality: {quality_text})")
<<<<<<< HEAD
                            
                            # Also collect feedback for the summarization system
                            try:
                                from feedback_system import FeedbackCollector
                                feedback_collector = FeedbackCollector()
                                
                                # Convert quality choice to feedback score
                                feedback_score = 1 if quality_choice == 1 else 0 if quality_choice == 2 else -1
                                
                                feedback_collector.collect_feedback(
                                    message_id=email_id,
                                    user_id='main_user',
                                    platform=email.get('platform', 'email'),
                                    original_text=email.get('body', ''),
                                    generated_summary=email.get('summary', ''),
                                    feedback_score=feedback_score,
                                    feedback_comment=f"Tag correction: {current_tag} → {new_tag}",
                                    category_ratings={
                                        'intent_detection': feedback_score,
                                        'summary_quality': feedback_score
                                    }
                                )
                                print("📊 Feedback also recorded for summarization system")
                            except Exception as fb_error:
                                print(f"⚠️ Could not record summarization feedback: {fb_error}")
                                
=======
>>>>>>> 9feb104c2eb5dd41ae26edcdb0da84c87c09344e
                        except ValueError:
                            # If invalid input, use default quality
                            tagger.process_feedback(email_id, new_tag, current_tag, sender, feedback_quality=1.0)
                            print(f"✅ Feedback recorded: {current_tag} → {new_tag} (Quality: Very confident)")
                            print("⚠️ Invalid confidence level, defaulted to 'Very confident'.")
                    elif new_tag:
                        print("❌ Invalid tag. Please use one of the available tags.")
                    else:
                        print("No changes made.")
                else:
                    print("❌ Invalid email number")
            except ValueError:
                print("❌ Please enter a valid number")
        
        elif choice == '5':
            # View learning statistics
            print("\n🧠 LEARNING STATISTICS")
            print("-" * 40)
            
            # Priority model stats
            priority_stats = prioritizer.get_learning_stats()
            print("Priority Learning:")
            for key, value in priority_stats.items():
                print(f"  • {key}: {value}")
            
            print()
            
            # Tagging stats
            tagging_stats = tagger.get_tagging_stats()
            print("Tagging Learning:")
            for key, value in tagging_stats.items():
                print(f"  • {key}: {value}")
            
            print()
            
<<<<<<< HEAD
            # Feedback system stats
            try:
                from feedback_system import FeedbackCollector
                feedback_collector = FeedbackCollector()
                feedback_analytics = feedback_collector.get_feedback_analytics()
                
                print("Feedback System Statistics:")
                overall_metrics = feedback_analytics.get('overall_metrics', {})
                print(f"  • Total feedback: {overall_metrics.get('total_feedback', 0)}")
                print(f"  • Positive feedback: {overall_metrics.get('positive_feedback', 0)}")
                print(f"  • Negative feedback: {overall_metrics.get('negative_feedback', 0)}")
                print(f"  • Satisfaction rate: {overall_metrics.get('satisfaction_rate', 0):.1%}")
                
                # Platform performance
                platform_stats = feedback_analytics.get('platform_performance', {})
                if platform_stats:
                    print("\nPlatform Performance:")
                    for platform, stats in platform_stats.items():
                        satisfaction = stats.get('satisfaction_rate', 0)
                        print(f"  • {platform}: {satisfaction:.1%} satisfaction")
                
                print()
            except Exception as e:
                print(f"⚠️ Could not load feedback statistics: {e}")
                print()
            
=======
>>>>>>> 9feb104c2eb5dd41ae26edcdb0da84c87c09344e
            # Sender insights with feedback quality metrics
            sender_insights = tagger.get_sender_insights()
            print("Sender Insights:")
            print(f"  • Learned senders: {len(sender_insights.get('sender_preferences', {}))}")
            print(f"  • Total corrections: {sender_insights.get('total_corrections', 0)}")
            
            # Display feedback quality metrics if available
            if 'feedback_quality' in sender_insights:
                quality_metrics = sender_insights['feedback_quality']
                print("\nFeedback Quality Metrics:")
                print(f"  • Positive feedback: {quality_metrics.get('positive_count', 0)}")
                print(f"  • Negative feedback: {quality_metrics.get('negative_count', 0)}")
                print(f"  • Neutral feedback: {quality_metrics.get('neutral_count', 0)}")
                print(f"  • Average quality: {quality_metrics.get('average_quality', 0):.2f}")
                
                # Display tag-specific quality if available
                if 'tag_quality' in quality_metrics and quality_metrics['tag_quality']:
                    print("\nTag-Specific Feedback Quality:")
                    for tag, quality in sorted(quality_metrics['tag_quality'].items(), 
                                              key=lambda x: x[1], reverse=True):
                        print(f"  • {tag}: {quality:.2f}")
            
            if sender_insights.get('sender_preferences'):
                print("\nTop Sender Preferences:")
                for sender, prefs in list(sender_insights['sender_preferences'].items())[:5]:
                    # Handle both old and new format
                    if isinstance(prefs, dict):
                        tag = prefs.get('preferred_tag', 'Unknown')
                        quality = prefs.get('feedback_quality', 'N/A')
                        print(f"  • {sender}: {tag} (Quality: {quality if quality == 'N/A' else f'{quality:.2f}'})") 
                    else:
                        print(f"  • {sender}: {prefs}")
        
        elif choice == '6':
            # Search emails
            query = input("Enter search query: ").strip().lower()
            if query:
                print(f"\n🔍 Searching for: '{query}'")
                print("-" * 40)
                
                matches = []
                for score, email in prioritized_emails:
                    text_to_search = f"{email.get('subject', '')} {email.get('body', '')} {email.get('sender', '')}".lower()
                    if query in text_to_search:
                        matches.append((score, email))
                
                if matches:
                    for i, (score, email) in enumerate(matches[:5], 1):
                        print(f"{i}. [{score:.2f}] {email.get('subject', 'No Subject')}")
                        print(f"   From: {email.get('sender', 'Unknown')}")
                        print(f"   Tag: {email.get('tag', 'GENERAL')}")
                        print()
                else:
                    print("No matches found.")
        
        elif choice == '7':
            # Quick demo interaction
            print("\n🎬 QUICK DEMO")
            print("-" * 30)
            print("This demo shows the system's key capabilities:")
            
            # Show top email with full analysis
            if prioritized_emails:
                score, top_email = prioritized_emails[0]
                
                print(f"\n📧 Top Priority Email Analysis:")
                print(f"   Subject: {top_email.get('subject', 'No Subject')}")
                print(f"   Sender: {top_email.get('sender', 'Unknown')}")
                print(f"   Priority Score: {score:.2f}")
                print(f"   Tag: {top_email.get('tag', 'GENERAL')} (Confidence: {top_email.get('tag_confidence', 0):.1%})")
                
                reasoning = top_email.get('tag_reasoning', [])
                if reasoning:
                    print(f"   Reasoning: {', '.join(reasoning)}")
                
                suggestions = top_email.get('smart_suggestions', [])[:3]
                if suggestions:
                    print(f"   Smart Suggestions:")
                    for i, suggestion in enumerate(suggestions, 1):
                        # Check if suggestion is personalized
                        personalized = suggestion.get('personalized', False)
                        personalization_indicator = "🔵" if personalized else ""
                        
                        # Get confidence and time estimate
                        confidence = suggestion.get('confidence', 0)
                        time_estimate = suggestion.get('estimated_time', 'N/A')
                        
                        # Format the suggestion display
                        print(f"     {i}. {personalization_indicator} {suggestion['text']} ")
                        print(f"        Time: {time_estimate} | Confidence: {confidence:.1%}")
                        
                        # Show context if available
                        if 'context' in suggestion and suggestion['context']:
                            print(f"        Context: {suggestion['context']}")
                        
                        # Show personalization source if available
                        if personalized and 'personalization_source' in suggestion:
                            print(f"        Personalized based on: {suggestion['personalization_source']}")
                
                metrics = top_email.get('metrics', {})
                print(f"   Detected Features:")
                print(f"     - Intent: {metrics.get('intent', 'unknown')}")
                print(f"     - Urgency: {metrics.get('urgency', 'unknown')}")
                print(f"     - Has deadline: {metrics.get('has_deadline', False)}")
                print(f"     - Sentiment: {top_email.get('sentiment_score', 0):.2f}")
        
        elif choice == '8':
            # Manage email credentials
            print("\n🔐 Email Credentials Management")
            print("-" * 40)
            
            new_credentials = manage_credentials()
            if new_credentials:
                print(f"✅ Updated credentials for: {new_credentials['email_address']}")
                print("🔄 Please restart the application to use new credentials")
            else:
                print("ℹ️ No changes made to credentials")
        
        elif choice == '9':
            # Exit
            print("\n👋 Thank you for using Smart Inbox Assistant!")
<<<<<<< HEAD
            break

if __name__ == "__main__":
    main()
=======
            break
>>>>>>> 9feb104c2eb5dd41ae26edcdb0da84c87c09344e
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
