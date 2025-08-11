import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re

# Import your modules
try:
    from email_reader import EmailReader
    from priority_model import Prioritizer
    from smart_metrics import extract_email_metrics
    from sentiment import analyze_sentiment
    from tts import read_text, stop_speech
    from briefing import generate_daily_brief
    from credentials_manager import get_email_credentials, manage_credentials
    from email_summarizer import format_email_display, generate_email_summary
    from smart_summarizer_v3 import SmartSummarizerV3, summarize_message
    from context_loader import ContextLoader
    from feedback_system import FeedbackCollector, FeedbackEnhancedSummarizer
    
    # Create a wrapper function for load_emails to maintain compatibility
    def load_emails():
        """Load emails using the EmailReader class."""
        email_reader = EmailReader(use_mock=True)
        return email_reader.load_emails()
        
except ImportError as e:
    st.error(f"Missing required modules: {e}")
    st.stop()

# Set page config
st.set_page_config(
    page_title="Smart Inbox Assistant", 
    page_icon="📬", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
.email-card {
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 15px;
    margin: 10px 0;
    background-color: #f9f9f9;
    color: #333333;
}
.urgent { border-left: 5px solid #ff4444; }
.meeting { border-left: 5px solid #4444ff; }
.financial { border-left: 5px solid #44ff44; }
.important { border-left: 5px solid #ffaa44; }
.promotional { border-left: 5px solid #ff44ff; }
.newsletter { border-left: 5px solid #44ffff; }
.security { border-left: 5px solid #ff8844; }
.general { border-left: 5px solid #888888; }

.confidence-high { background-color: #e6ffe6; }
.confidence-medium { background-color: #fff3e6; }
.confidence-low { background-color: #ffe6e6; }

.smartbrief-card {
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 15px;
    margin: 10px 0;
    background-color: #f0f8ff;
    color: #333333;
    border-left: 5px solid #1f77b4;
}

.intent-question { border-left-color: #ff6b6b; }
.intent-request { border-left-color: #4ecdc4; }
.intent-follow_up { border-left-color: #45b7d1; }
.intent-complaint { border-left-color: #f9ca24; }
.intent-appreciation { border-left-color: #6c5ce7; }
.intent-urgent { border-left-color: #fd79a8; }
.intent-social { border-left-color: #00b894; }
.intent-informational { border-left-color: #74b9ff; }

/* Fix for white text on white background */
.stMarkdown, .stText, .stDataFrame {
    color: #333333 !important;
}

/* Ensure all text in white containers is visible */
.css-1kyxreq, .css-12oz5g7 {
    color: #333333 !important;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'emails_processed' not in st.session_state:
    st.session_state.emails_processed = False
if 'processed_emails' not in st.session_state:
    st.session_state.processed_emails = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = 0
if 'filter_tag' not in st.session_state:
    st.session_state.filter_tag = 'ALL'
if 'sort_by' not in st.session_state:
    st.session_state.sort_by = 'Priority Score'
if 'demo_mode' not in st.session_state:
    st.session_state.demo_mode = 'email_processing'
if 'smartbrief_results' not in st.session_state:
    st.session_state.smartbrief_results = []

# Simple Priority Tagger class (inline implementation)
class SimplePriorityTagger:
    def __init__(self):
        self.feedback_file = 'tagging_feedback.json'
        self.load_feedback()
    
    def load_feedback(self):
        """Load feedback data from file."""
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, 'r') as f:
                    self.feedback_data = json.load(f)
            except:
                self.feedback_data = {
                    'tag_corrections': {},
                    'sender_preferences': {},
                    'confidence_scores': {}
                }
        else:
            self.feedback_data = {
                'tag_corrections': {},
                'sender_preferences': {},
                'confidence_scores': {}
            }
    
    def save_feedback(self):
        """Save feedback data to file."""
        try:
            with open(self.feedback_file, 'w') as f:
                json.dump(self.feedback_data, f, indent=2)
        except Exception as e:
            print(f"Error saving feedback: {e}")
    
    def tag_email(self, email):
        """Tag an email with priority category."""
        subject = email.get('subject', '').lower()
        body = email.get('body', '').lower()
        sender = email.get('sender', '').lower()
        
        full_text = f"{subject} {body}"
        
        # Initialize scores
        scores = {
            'URGENT': 0.0,
            'MEETING': 0.0,
            'FINANCIAL': 0.0,
            'IMPORTANT': 0.0,
            'PROMOTIONAL': 0.0,
            'NEWSLETTER': 0.0,
            'SECURITY': 0.0,
            'GENERAL': 0.1
        }
        
        reasoning = []
        features_detected = {}
        
        # Urgent keywords
        urgent_keywords = ['urgent', 'asap', 'immediately', 'emergency', 'critical', 'deadline']
        urgent_score = sum(1 for keyword in urgent_keywords if keyword in full_text)
        if urgent_score > 0:
            scores['URGENT'] += urgent_score * 0.3
            reasoning.append(f"Urgent keywords found ({urgent_score})")
        
        # Meeting keywords
        meeting_keywords = ['meeting', 'schedule', 'appointment', 'conference', 'call', 'zoom']
        meeting_score = sum(1 for keyword in meeting_keywords if keyword in full_text)
        if meeting_score > 0:
            scores['MEETING'] += meeting_score * 0.2
            reasoning.append(f"Meeting keywords found ({meeting_score})")
        
        # Financial keywords
        financial_keywords = ['invoice', 'payment', 'bill', 'transaction', 'account', 'financial']
        financial_score = sum(1 for keyword in financial_keywords if keyword in full_text)
        if financial_score > 0:
            scores['FINANCIAL'] += financial_score * 0.25
            reasoning.append(f"Financial keywords found ({financial_score})")
        
        # Security keywords
        security_keywords = ['security', 'password', 'alert', 'suspicious', 'breach', 'verify']
        security_score = sum(1 for keyword in security_keywords if keyword in full_text)
        if security_score > 0:
            scores['SECURITY'] += security_score * 0.3
            reasoning.append(f"Security keywords found ({security_score})")
        
        # Promotional keywords
        promo_keywords = ['offer', 'sale', 'discount', 'deal', 'promotion', 'limited time']
        promo_score = sum(1 for keyword in promo_keywords if keyword in full_text)
        if promo_score > 0:
            scores['PROMOTIONAL'] += promo_score * 0.15
            reasoning.append(f"Promotional keywords found ({promo_score})")
        
        # Newsletter indicators
        newsletter_keywords = ['newsletter', 'weekly', 'monthly', 'updates', 'news']
        newsletter_score = sum(1 for keyword in newsletter_keywords if keyword in full_text)
        if newsletter_score > 0 or 'unsubscribe' in full_text:
            scores['NEWSLETTER'] += 0.2
            reasoning.append("Newsletter indicators found")
        
        # Sender-based scoring
        if sender:
            if any(term in sender for term in ['ceo', 'manager', 'director', 'admin']):
                scores['IMPORTANT'] += 0.3
                reasoning.append("Important sender detected")
            elif any(term in sender for term in ['noreply', 'no-reply', 'automated']):
                scores['NEWSLETTER'] += 0.2
                reasoning.append("Automated sender detected")
        
        # Apply learned preferences
        sender_prefs = self.feedback_data.get('sender_preferences', {})
        if sender in sender_prefs:
            preferred_tag = sender_prefs[sender]
            scores[preferred_tag] += 0.4
            reasoning.append(f"Learned preference for sender: {preferred_tag}")
        
        # Find the tag with highest score
        best_tag = max(scores.keys(), key=lambda k: scores[k])
        confidence = min(scores[best_tag], 1.0)
        
        # Features for display
        features_detected = {
            'word_count': len(full_text.split()),
            'has_attachments': bool(email.get('attachments')),
            'time_urgency': urgent_score
        }
        
        return {
            'tag': best_tag,
            'confidence': confidence,
            'reasoning': reasoning,
            'all_scores': scores,
            'features_detected': features_detected
        }
    
    def process_feedback(self, email_id, correct_tag, predicted_tag, sender, feedback_quality=1.0):
        """Process user feedback for learning."""
        # Store correction with consistent format
        self.feedback_data['tag_corrections'][email_id] = {
            'correct': correct_tag,
            'predicted': predicted_tag,
            'sender': sender,
            'timestamp': datetime.now().isoformat(),
            'quality': feedback_quality
        }
        
        # Update sender preferences
        if sender and correct_tag != predicted_tag:
            if sender in self.feedback_data['sender_preferences']:
                # If we have multiple corrections for this sender, use most recent
                self.feedback_data['sender_preferences'][sender] = correct_tag
            else:
                self.feedback_data['sender_preferences'][sender] = correct_tag
        
        self.save_feedback()
    
    def suggest_tag_improvements(self):
        """Suggest improvements based on feedback."""
        improvements = []
        corrections = self.feedback_data.get('tag_corrections', {})
        
        if len(corrections) > 5:
            # Analyze common mistakes
            mistake_counts = {}
            for correction in corrections.values():
                # Handle both old and new feedback formats
                if 'predicted' in correction and 'correct' in correction:
                    mistake = f"{correction['predicted']} → {correction['correct']}"
                elif 'original_tag' in correction and 'correct_tag' in correction:
                    mistake = f"{correction['original_tag']} → {correction['correct_tag']}"
                else:
                    continue  # Skip malformed entries
                
                mistake_counts[mistake] = mistake_counts.get(mistake, 0) + 1
            
            for mistake, count in mistake_counts.items():
                if count > 2:
                    improvements.append(f"Consider reviewing {mistake} classifications ({count} corrections)")
        
        return improvements

# Simple Smart Suggestions Module (inline implementation)
class SimpleSmartSuggestionsModule:
    def __init__(self):
        self.usage_stats = {'user_preferences': {}, 'tag_preferences': {}}
    
    def generate_suggestions(self, email, tag, confidence):
        """Generate smart suggestions for an email."""
        suggestions = []
        
        if tag == 'URGENT':
            suggestions.extend([
                {'text': 'Reply immediately', 'action': 'reply_urgent', 'estimated_time': '5 min', 'confidence': 0.9},
                {'text': 'Add to high priority list', 'action': 'high_priority', 'estimated_time': '1 min', 'confidence': 0.8},
                {'text': 'Set reminder in 1 hour', 'action': 'reminder_1h', 'estimated_time': '1 min', 'confidence': 0.7}
            ])
        elif tag == 'MEETING':
            suggestions.extend([
                {'text': 'Add to calendar', 'action': 'add_calendar', 'estimated_time': '2 min', 'confidence': 0.9},
                {'text': 'Accept meeting invite', 'action': 'accept_meeting', 'estimated_time': '1 min', 'confidence': 0.8},
                {'text': 'Request agenda', 'action': 'request_agenda', 'estimated_time': '3 min', 'confidence': 0.6}
            ])
        elif tag == 'FINANCIAL':
            suggestions.extend([
                {'text': 'Review and approve', 'action': 'review_financial', 'estimated_time': '10 min', 'confidence': 0.8},
                {'text': 'Forward to accounting', 'action': 'forward_accounting', 'estimated_time': '2 min', 'confidence': 0.9},
                {'text': 'Add to expenses tracker', 'action': 'track_expense', 'estimated_time': '3 min', 'confidence': 0.7}
            ])
        elif tag == 'PROMOTIONAL':
            suggestions.extend([
                {'text': 'Archive (promotional)', 'action': 'archive_promo', 'estimated_time': '1 min', 'confidence': 0.9},
                {'text': 'Unsubscribe', 'action': 'unsubscribe', 'estimated_time': '2 min', 'confidence': 0.7},
                {'text': 'Save offer for later', 'action': 'save_offer', 'estimated_time': '1 min', 'confidence': 0.5}
            ])
        else:
            suggestions.extend([
                {'text': 'Quick reply', 'action': 'quick_reply', 'estimated_time': '3 min', 'confidence': 0.6},
                {'text': 'Archive', 'action': 'archive', 'estimated_time': '1 min', 'confidence': 0.8},
                {'text': 'Set reminder for tomorrow', 'action': 'reminder_tomorrow', 'estimated_time': '1 min', 'confidence': 0.7}
            ])
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def execute_suggestion(self, email, action):
        """Execute a suggestion action."""
        # Update usage stats
        self.usage_stats['user_preferences'][action] = self.usage_stats['user_preferences'].get(action, 0) + 1
        
        # Simulate action execution
        action_responses = {
            'reply_urgent': {'success': True, 'message': 'Urgent reply template prepared'},
            'high_priority': {'success': True, 'message': 'Added to high priority list'},
            'add_calendar': {'success': True, 'message': 'Calendar event created'},
            'archive_promo': {'success': True, 'message': 'Email archived to promotional folder'},
            'quick_reply': {'success': True, 'message': 'Quick reply template ready'},
            'archive': {'success': True, 'message': 'Email archived'},
        }
        
        return action_responses.get(action, {'success': False, 'message': 'Action not implemented'})

# Initialize components
@st.cache_data
def initialize_components():
    """Initialize all AI components and fetch emails from Gmail."""
    from email_reader import EmailReader  # correct class name

    components = {
        'prioritizer': Prioritizer(),
        'tagger': SimplePriorityTagger(),
        'suggestions': SimpleSmartSuggestionsModule(),
        'smartbrief': SmartSummarizerV3(),
        'context_loader': ContextLoader(),
        'feedback_collector': FeedbackCollector()
    }

    EMAIL = st.secrets["email"]
    APP_PASSWORD = st.secrets["app_password"]

    try:
        reader = EmailReader(use_mock=False)  # disable mock so it uses live Gmail
        if reader.connect_imap(email_address=EMAIL, password=APP_PASSWORD):
            messages = reader.fetch_live_emails(limit=20)
            components['inbox_messages'] = messages
            st.session_state['inbox_messages'] = messages
            st.success(f"Loaded {len(messages)} emails from Gmail.")
        else:
            st.error("Failed to connect to Gmail.")
            components['inbox_messages'] = []
    except Exception as e:
        st.error(f"Error fetching emails: {e}")
        components['inbox_messages'] = []

    return components



components = initialize_components()

# Function to clean text for display and TTS
def clean_text_for_summary(text):
    """Clean HTML and simplify links in text."""
    if not text:
        return ""
    # Replace HTML tags with spaces
    text = re.sub(r'<[^>]+>', ' ', text)
    # Replace links with a placeholder
    text = re.sub(r'https?://\S+', '[Link]', text)
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def display_smartbrief_result(message, result, index):
    """Display a SmartBrief analysis result."""
    with st.container():
        # Create columns for layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Message content with intent-based styling
            intent_class = f"intent-{result['intent']}"
            st.markdown(f"""
            <div class="smartbrief-card {intent_class}">
                <h4>🤖 SmartBrief Analysis - {message['platform'].title()}</h4>
                <p><strong>From:</strong> {message['user_id']}</p>
                <p><strong>Message:</strong> {message['message_text']}</p>
                <p><strong>Summary:</strong> {result['summary']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Analysis results
            urgency_color = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[result['urgency']]
            
            st.markdown(f"""
            <div class="smartbrief-card">
                <p><strong>🎯 Intent:</strong> {result['intent'].title()}</p>
                <p><strong>{urgency_color} Urgency:</strong> {result['urgency'].title()}</p>
                <p><strong>🎲 Confidence:</strong> {result['confidence']:.2f}</p>
                <p><strong>🧠 Context:</strong> {'Yes' if result['context_used'] else 'No'}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Expandable reasoning and feedback
        with st.expander(f"🔍 Analysis Details & Feedback - Message {index + 1}"):
            col_a, col_b = st.columns([2, 1])
            
            with col_a:
                st.write("**Reasoning:**")
                for reason in result['reasoning']:
                    st.write(f"• {reason}")
                
                if result.get('platform_optimized'):
                    st.success("✅ Platform-optimized summary generated")
            
            with col_b:
                st.write("**Provide Feedback:**")
                
                # Feedback buttons
                col_good, col_bad = st.columns(2)
                
                message_id = message.get('message_id', f'msg_{index}')
                safe_msg_id = str(message_id).replace('@', '_at_').replace('.', '_dot_')
                
                with col_good:
                    good_key = f"smartbrief_good_{safe_msg_id}_{index}"
                    if st.button("👍 Good", key=good_key):
                        # Collect positive feedback
                        components['feedback_collector'].collect_feedback(
                            message_id=message_id,
                            user_id=message['user_id'],
                            platform=message['platform'],
                            original_text=message['message_text'],
                            generated_summary=result['summary'],
                            feedback_score=1,
                            feedback_comment="User marked as good",
                            category_ratings={
                                'summary_quality': 1,
                                'intent_detection': 1,
                                'urgency_level': 1,
                                'context_usage': 1 if result['context_used'] else 0
                            }
                        )
                        st.success("✅ Positive feedback recorded!")
                
                with col_bad:
                    bad_key = f"smartbrief_bad_{safe_msg_id}_{index}"
                    if st.button("👎 Needs Work", key=bad_key):
                        # Collect negative feedback
                        components['feedback_collector'].collect_feedback(
                            message_id=message_id,
                            user_id=message['user_id'],
                            platform=message['platform'],
                            original_text=message['message_text'],
                            generated_summary=result['summary'],
                            feedback_score=-1,
                            feedback_comment="User marked as needs improvement",
                            category_ratings={
                                'summary_quality': -1,
                                'intent_detection': 0,
                                'urgency_level': 0,
                                'context_usage': -1 if result['context_used'] else 0
                            }
                        )
                        st.success("❌ Feedback recorded - will improve!")
                
                # Corrected summary input
                corrected_summary = st.text_input(
                    "Better summary:",
                    key=f"corrected_{safe_msg_id}_{index}",
                    placeholder="Provide a better summary..."
                )
                
                if corrected_summary:
                    correct_key = f"submit_correction_{safe_msg_id}_{index}"
                    if st.button("📝 Submit Correction", key=correct_key):
                        components['feedback_collector'].collect_feedback(
                            message_id=message_id,
                            user_id=message['user_id'],
                            platform=message['platform'],
                            original_text=message['message_text'],
                            generated_summary=result['summary'],
                            feedback_score=0,  # Neutral with correction
                            corrected_summary=corrected_summary,
                            feedback_comment="User provided corrected summary"
                        )
                        st.success("📝 Correction submitted - thank you!")

# Sidebar Configuration
st.sidebar.title("🤖 Smart Inbox Settings")

# Demo mode selection
demo_mode = st.sidebar.radio(
    "Select Mode:",
    ["Email Processing", "SmartBrief v3", "Feedback Analytics", "Performance Test"],
    key="demo_mode_radio"
)

st.session_state.demo_mode = demo_mode


def load_mock_emails():
    """Load mock emails from CSV file."""
    mock_file = os.path.join(os.path.dirname(__file__), "mock_emails.csv")
    if os.path.exists(mock_file):
        return pd.read_csv(mock_file).to_dict(orient="records")
    else:
        return []

# Email source selection (for Email Processing mode)
if demo_mode == "Email Processing":
    email_source = st.sidebar.radio(
        "Email Source",
        ["Live Email", "Mock Emails", "CSV File"],
        help="Select your email source"
    )

    if email_source == "Live Email":
        # Use Gmail emails fetched in initialize_components()
        messages = components.get('inbox_messages', [])
        if messages:
            st.sidebar.success(f"📬 {len(messages)} emails loaded from Gmail")
        else:
            st.sidebar.warning("No emails loaded. Check your Gmail credentials in .streamlit/secrets.toml.")

    elif email_source == "Mock Emails":
        # Example: load mock emails from a local CSV or function
        try:
            messages = load_mock_emails()  # replace with your mock loader
            st.sidebar.info(f"📨 {len(messages)} mock emails loaded")
        except Exception as e:
            st.sidebar.error(f"Error loading mock emails: {e}")
            messages = []

    elif email_source == "CSV File":
        uploaded_file = st.sidebar.file_uploader(
            "Upload CSV file with emails",
            type=['csv'],
            help="CSV should have columns: subject, sender, body, date"
        )
        if uploaded_file:
            try:
                messages = pd.read_csv(uploaded_file).to_dict(orient="records")
                st.sidebar.info(f"📂 {len(messages)} emails loaded from CSV")
            except Exception as e:
                st.sidebar.error(f"Error reading CSV: {e}")
                messages = []
        else:
            messages = []


# SmartBrief settings (for SmartBrief mode)
if demo_mode == "SmartBrief v3":
    st.sidebar.subheader("🧠 SmartBrief Settings")
    platforms = ['All', 'whatsapp', 'email', 'slack', 'teams', 'instagram', 'discord']
    selected_platform = st.sidebar.selectbox("Filter by Platform:", platforms)
    
    use_context = st.sidebar.checkbox("Use Context Awareness", value=True)
    max_context = st.sidebar.slider("Max Context Messages", 1, 10, 3)
    
    # Update summarizer settings
    components['smartbrief'].max_context_messages = max_context

# Filters and sorting (for Email Processing mode)
if demo_mode == "Email Processing":
    st.sidebar.subheader("📊 Display Options")
    st.session_state.filter_tag = st.sidebar.selectbox(
        "Filter by Tag",
        ['ALL', 'URGENT', 'MEETING', 'FINANCIAL', 'IMPORTANT', 'PROMOTIONAL', 'NEWSLETTER', 'SECURITY', 'GENERAL']
    )
    
    st.session_state.sort_by = st.sidebar.selectbox(
        "Sort by",
        ['Priority Score', 'Confidence', 'Date', 'Sender']
    )

# Processing options
st.sidebar.subheader("🎛️ Processing Options")
show_reasoning = st.sidebar.checkbox("Show Analysis Reasoning", value=True)
show_suggestions = st.sidebar.checkbox("Show Smart Suggestions", value=True)
auto_play_tts = st.sidebar.checkbox("Auto-play TTS for high priority", value=False)

# Main title
st.title("📬 Smart Inbox Assistant")
st.markdown("*Unified Email Processing & SmartBrief v3 Analysis with Reinforcement Learning*")

# Main content based on selected mode
if demo_mode == "Email Processing":
    # Email loading section
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if st.button("🔄 Load & Process Emails"):
            with st.spinner("Loading and processing emails..."):
                try:
                    # Load emails based on source
                    if email_source == "Live Email":
                        # Try to get saved credentials
                        try:
                            credentials = get_email_credentials()
                            if credentials:
                                email_reader = EmailReader(use_mock=False)
                                if email_reader.connect_imap(credentials['email_address'], credentials['password']):
                                    emails_df = email_reader.load_emails(
                                        email_address=credentials['email_address'],
                                        password=credentials['password'],
                                        limit=10
                                    )
                                    email_reader.close_connection()
                                    st.success(f"✅ Loaded {len(emails_df)} emails from {credentials['email_address']}")
                                else:
                                    st.error("❌ Failed to connect to email server")
                                    emails_df = load_emails()
                            else:
                                st.warning("⚠️ No saved credentials found. Using mock emails.")
                                emails_df = load_emails()
                        except Exception as e:
                            st.error(f"❌ Error connecting to email: {e}")
                            emails_df = load_emails()
                            
                    elif email_source == "CSV File" and uploaded_file is not None:
                        # Load from uploaded CSV
                        emails_df = pd.read_csv(uploaded_file)
                        # Ensure required columns exist
                        required_cols = ['subject', 'sender', 'body', 'date']
                        for col in required_cols:
                            if col not in emails_df.columns:
                                emails_df[col] = f'Unknown {col}'
                        st.success(f"✅ Loaded {len(emails_df)} emails from CSV")
                    else:
                        # Load mock emails
                        emails_df = load_emails()
                        st.success(f"✅ Loaded {len(emails_df)} emails")
                    
                    # Process each email
                    processed_emails = []
                    
                    progress_bar = st.progress(0)
                    for idx, (_, email_row) in enumerate(emails_df.iterrows()):
                        email_dict = email_row.to_dict()
                        
                        # Format email for display (add subject if missing, generate summary)
                        email_dict = format_email_display(email_dict)
                        
                        # Extract metrics
                        body = email_dict.get('body', '')
                        subject = email_dict.get('subject', 'No Subject')
                        full_text = f"{subject} {body}"
                        
                        # AI Analysis
                        metrics = extract_email_metrics(full_text)
                        sentiment_score = analyze_sentiment(body)
                        
                        # Priority tagging
                        tag_result = components['tagger'].tag_email(email_dict)
                        
                        # Priority scoring with feedback learning
                        enriched_email = {
                            **email_dict,
                            'sentiment_score': sentiment_score,
                            'metrics': metrics,
                            'tag': tag_result['tag'],
                            'tag_confidence': tag_result['confidence'],
                            'tag_reasoning': tag_result['reasoning'],
                            'all_scores': tag_result['all_scores'],
                            'features_detected': tag_result['features_detected']
                        }
                        
                        processed_emails.append(enriched_email)
                        progress_bar.progress((idx + 1) / len(emails_df))
                    
                    # Prioritize using the existing system with RL
                    prioritized_emails = components['prioritizer'].prioritize_emails(processed_emails)
                    
                    # Store in session state
                    st.session_state.processed_emails = [(score, email) for score, email in prioritized_emails]
                    st.session_state.emails_processed = True
                    st.session_state.current_page = 0  # Reset to first page
                    
                    st.success(f"✅ Successfully processed {len(processed_emails)} emails!")
                    
                    # Show RL learning stats
                    rl_stats = components['prioritizer'].get_learning_stats()
                    if rl_stats['total_feedback'] > 0:
                        st.info(f"🧠 RL System: {rl_stats['total_feedback']} feedback entries, Avg reward: {rl_stats['avg_reward']:.2f}")
                    
                except Exception as e:
                    st.error(f"Error processing emails: {e}")
                    st.error(f"Error details: {str(e)}")

    with col2:
        if st.button("📄 Generate Brief"):
            if st.session_state.emails_processed:
                top_emails = [email for _, email in st.session_state.processed_emails[:10]]
                
                # Add required fields for briefing
                for i, email in enumerate(top_emails):
                    email['priority_level'] = 'HIGH' if i < 3 else 'MEDIUM' if i < 7 else 'LOW'
                    email['priority_score'] = st.session_state.processed_emails[i][0]
                    email['read_status'] = 'unread'
                    email['message_type'] = email.get('metrics', {}).get('intent', 'general')
                    email['timestamp'] = email.get('date', datetime.now())
                    
                    # Key points
                    key_points = []
                    if email.get('metrics', {}).get('has_deadline'):
                        key_points.append("⏰ Contains deadline")
                    if email.get('metrics', {}).get('urgency') == 'high':
                        key_points.append("🔥 High urgency")
                    if email.get('tag') == 'URGENT':
                        key_points.append("🚨 Tagged as urgent")
                    if email.get('sentiment_score', 0) < -0.1:
                        key_points.append("😟 Negative sentiment")
                    
                    email['key_points'] = key_points if key_points else ["📧 Standard email"]
                
                brief = generate_daily_brief(top_emails)
                
                st.text_area("Daily Brief", brief, height=200)
                
                if st.button("🔊 Read Brief Aloud"):
                    read_text(brief)
            else:
                st.warning("Please process emails first")

    with col3:
        if st.button("🛑 Stop Speech"):
            stop_speech()
            st.success("Speech stopped")

    # Display processed emails if available
    if st.session_state.emails_processed:
        
        # Statistics dashboard
        st.subheader("📊 Email Analytics Dashboard")
        
        # Create metrics
        total_emails = len(st.session_state.processed_emails)
        tag_counts = {}
        confidence_levels = {'High': 0, 'Medium': 0, 'Low': 0}
        
        for score, email in st.session_state.processed_emails:
            tag = email.get('tag', 'GENERAL')
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            confidence = email.get('tag_confidence', 0)
            if confidence > 0.7:
                confidence_levels['High'] += 1
            elif confidence > 0.4:
                confidence_levels['Medium'] += 1
            else:
                confidence_levels['Low'] += 1
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Emails", total_emails)
        col2.metric("Urgent Emails", tag_counts.get('URGENT', 0))
        col3.metric("High Confidence", confidence_levels['High'])
        if total_emails > 0:
            avg_score = sum(score for score, _ in st.session_state.processed_emails) / total_emails
            col4.metric("Avg Priority Score", f"{avg_score:.2f}")
        else:
            col4.metric("Avg Priority Score", "0.00")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            if tag_counts:
                # Tag distribution
                fig_tags = px.pie(
                    values=list(tag_counts.values()),
                    names=list(tag_counts.keys()),
                    title="Email Distribution by Tag"
                )
                st.plotly_chart(fig_tags, use_container_width=True)
        
        with col2:
            # Confidence levels
            fig_conf = px.bar(
                x=list(confidence_levels.keys()),
                y=list(confidence_levels.values()),
                title="Tagging Confidence Levels",
                color=list(confidence_levels.values()),
                color_continuous_scale="RdYlGn"
            )
            st.plotly_chart(fig_conf, use_container_width=True)
        
        # Filter and sort emails
        filtered_emails = st.session_state.processed_emails
        
        if st.session_state.filter_tag != 'ALL':
            filtered_emails = [(score, email) for score, email in filtered_emails 
                              if str(email.get('tag', 'GENERAL')).upper() == st.session_state.filter_tag.upper()]
        
        # Sort emails
        if st.session_state.sort_by == 'Priority Score':
            filtered_emails.sort(key=lambda x: x[0], reverse=True)
        elif st.session_state.sort_by == 'Confidence':
            filtered_emails.sort(key=lambda x: x[1].get('tag_confidence', 0), reverse=True)
        elif st.session_state.sort_by == 'Date':
            filtered_emails.sort(key=lambda x: x[1].get('date', datetime.now()), reverse=True)
        elif st.session_state.sort_by == 'Sender':
            filtered_emails.sort(key=lambda x: x[1].get('sender', ''))
        
        # Pagination
        EMAILS_PER_PAGE = 10
        total_pages = max(1, (len(filtered_emails) + EMAILS_PER_PAGE - 1) // EMAILS_PER_PAGE)
        
        # Ensure current page is valid
        if st.session_state.current_page >= total_pages:
            st.session_state.current_page = max(0, total_pages - 1)

        # Top Pagination Controls
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.session_state.current_page > 0:
                if st.button("⬅️ Previous", key="prev_top_btn"):
                    st.session_state.current_page -= 1
                    st.rerun()
        with col2:
            st.write(f"Page {st.session_state.current_page + 1} of {total_pages} ({len(filtered_emails)} total emails)")
        with col3:
            if st.session_state.current_page < total_pages - 1:
                if st.button("Next ➡️", key="next_top_btn"):
                    st.session_state.current_page += 1
                    st.rerun()

        # Display emails
        start_idx = st.session_state.current_page * EMAILS_PER_PAGE
        end_idx = min(start_idx + EMAILS_PER_PAGE, len(filtered_emails))
        page_emails = filtered_emails[start_idx:end_idx]

        st.subheader(f"📧 Emails ({start_idx + 1}-{end_idx} of {len(filtered_emails)})")

        # Email display loop with RL feedback
        for email_idx, (priority_score, email) in enumerate(page_emails):
            email_id = email.get('id', f'email_{start_idx + email_idx}')
            subject = email.get('subject', 'No Subject')
            sender = email.get('sender', 'Unknown Sender')
            body = email.get('body', 'No body provided.')
            tag = email.get('tag', 'GENERAL')
            confidence = email.get('tag_confidence', 0.0)
            
            # Determine confidence class
            conf_class = 'high' if confidence > 0.7 else 'medium' if confidence > 0.4 else 'low'
            
            # Create email card
            with st.container():
                # Sanitize sender email to prevent InvalidCharacterError
                display_sender = sender.replace('@', ' (at) ') if isinstance(sender, str) else str(sender)
                
                st.markdown(f"""
                <div class="email-card {tag.lower()} confidence-{conf_class}">
                    <h4>📧 {subject}</h4>
                    <p><strong>From:</strong> {display_sender}</p>
                    <p><strong>Priority Score:</strong> {priority_score:.2f} | <strong>Tag:</strong> {tag} | <strong>Confidence:</strong> {confidence:.1%}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Email summary
                summary = email.get('summary', '')
                if not summary:
                    # Generate summary if not available
                    summary = generate_email_summary(email)
                
                st.markdown(f"<div style='color: #333333; font-weight: 500; background-color: #f5f5f5; padding: 10px; border-radius: 5px;'><strong>Summary:</strong> {summary}</div>", unsafe_allow_html=True)
                
                # Show reasoning if enabled
                if show_reasoning:
                    reasoning = email.get('tag_reasoning', [])
                    if reasoning:
                        st.markdown(f"<div style='color: #333333; font-weight: 500; background-color: #fff0f5; padding: 8px; border-radius: 5px; margin-top: 5px;'><strong>Tagging Reasoning:</strong> {', '.join(reasoning)}</div>", unsafe_allow_html=True)
                
                # Features detected
                features = email.get('features_detected', {})
                if features:
                    feature_text = []
                    if features.get('time_urgency', 0) > 0:
                        feature_text.append(f"⏰ Time urgency: {features['time_urgency']:.1f}")
                    if features.get('has_attachments'):
                        feature_text.append("📎 Has attachments")
                    feature_text.append(f"📝 {features.get('word_count', 0)} words")
                    
                    if feature_text:
                        st.markdown(f"<div style='color: #333333; font-weight: 500; background-color: #f0f7ff; padding: 8px; border-radius: 5px; margin-top: 5px;'><strong>Features:</strong> {' | '.join(feature_text)}</div>", unsafe_allow_html=True)
                
                # Action buttons with RL feedback
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    # Sanitize key for button to prevent InvalidCharacterError
                    button_key = f"read_{email_id}_{start_idx + email_idx}".replace('@', '_at_').replace('.', '_dot_')
                    if st.button(f"🔊 Read", key=button_key):
                        tts_body = clean_text_for_summary(body)
                        read_text(f"Email from {display_sender}. Subject: {subject}. {tts_body}")
                
                with col2:
                    # Tag correction with RL feedback
                    safe_email_id = str(email_id).replace('@', '_at_').replace('.', '_dot_')
                    tag_key = f"tag_{safe_email_id}_{start_idx + email_idx}"
                    new_tag = st.selectbox(
                        "Correct Tag",
                        ['URGENT', 'MEETING', 'FINANCIAL', 'IMPORTANT', 'PROMOTIONAL', 'NEWSLETTER', 'SECURITY', 'GENERAL'],
                        index=['URGENT', 'MEETING', 'FINANCIAL', 'IMPORTANT', 'PROMOTIONAL', 'NEWSLETTER', 'SECURITY', 'GENERAL'].index(tag),
                        key=tag_key
                    )
                    
                    if new_tag != tag:
                        update_key = f"update_tag_{safe_email_id}_{start_idx + email_idx}"
                        if st.button(f"✅ Update", key=update_key):
                            # Process feedback for both tagger and RL system
                            components['tagger'].process_feedback(email_id, new_tag, tag, sender)
                            
                            # RL feedback: positive reward for correction, negative for wrong prediction
                            reward = 1.0 if new_tag != tag else -0.5
                            components['prioritizer'].update(email, reward)
                            
                            st.success(f"Tag updated from {tag} to {new_tag}")
                            st.info(f"🧠 RL System learned from feedback (reward: {reward})")
                            
                            # Update the email in session state
                            for i, (score, em) in enumerate(st.session_state.processed_emails):
                                if em.get('id') == email_id:
                                    st.session_state.processed_emails[i] = (score, {**em, 'tag': new_tag})
                                    break
                            st.rerun()
                
                with col3:
                    # Feedback buttons for RL
                    safe_email_id = str(email_id).replace('@', '_at_').replace('.', '_dot_')
                    good_key = f"good_{safe_email_id}_{start_idx + email_idx}"
                    if st.button(f"👍 Good", key=good_key):
                        # Positive feedback for RL
                        reward = 2.0  # High positive reward for good classification
                        components['prioritizer'].update(email, reward)
                        components['tagger'].process_feedback(email_id, tag, tag, sender)
                        
                        st.success("Positive feedback recorded!")
                        st.info(f"🧠 RL System: +{reward} reward")
                
                with col4:
                    # Negative feedback for RL
                    bad_key = f"bad_{safe_email_id}_{start_idx + email_idx}"
                    if st.button(f"👎 Poor", key=bad_key):
                        # Negative feedback for RL
                        reward = -1.0  # Negative reward for poor classification
                        components['prioritizer'].update(email, reward)
                        
                        st.warning("Negative feedback recorded!")
                        st.info(f"🧠 RL System: {reward} reward")
                
                # Smart suggestions
                if show_suggestions:
                    with col5:
                        safe_email_id = str(email_id).replace('@', '_at_').replace('.', '_dot_')
                        suggest_key = f"suggest_{safe_email_id}_{start_idx + email_idx}"
                        if st.button(f"💡 Actions", key=suggest_key):
                            suggestions = components['suggestions'].generate_suggestions(email, tag, confidence)
                            
                            st.write("**Smart Suggestions:**")
                            for i, suggestion in enumerate(suggestions[:3]):
                                suggestion_text = suggestion['text']
                                suggestion_time = suggestion.get('estimated_time', '')
                                suggestion_confidence = suggestion.get('confidence', 0)
                                
                                time_text = f" (⏱️ {suggestion_time})" if suggestion_time else ""
                                confidence_text = f" ({int(suggestion_confidence * 100)}%)" if suggestion_confidence else ""
                                
                                col_a, col_b = st.columns([3, 1])
                                with col_a:
                                    st.write(f"• {suggestion_text}{time_text}{confidence_text}")
                                with col_b:
                                    exec_key = f"exec_{safe_email_id}_{start_idx + email_idx}_{i}"
                                    if st.button(f"Execute", key=exec_key):
                                        result = components['suggestions'].execute_suggestion(email, suggestion['action'])
                                        if result['success']:
                                            st.success(result['message'])
                                            # Positive RL feedback for successful action
                                            components['prioritizer'].update(email, 0.5)
                                        else:
                                            st.error(result['message'])
                
                st.markdown("---")
        
        # Bottom Pagination Controls
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.session_state.current_page > 0:
                if st.button("⬅️ Previous", key="prev_bottom_btn"):
                    st.session_state.current_page -= 1
                    st.rerun()
        
        with col2:
            st.write(f"Page {st.session_state.current_page + 1} of {total_pages}")
        
        with col3:
            if st.session_state.current_page < total_pages - 1:
                if st.button("Next ➡️", key="next_bottom_btn"):
                    st.session_state.current_page += 1
                    st.rerun()
        
        # Analytics section
        st.markdown("---")
        st.subheader("💡 Learning Analytics")
        
        # RL Learning Stats
        rl_stats = components['prioritizer'].get_learning_stats()
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("RL States Learned", rl_stats['total_states'])
        col2.metric("Total Feedback", rl_stats['total_feedback'])
        col3.metric("Learning Episodes", rl_stats['total_episodes'])
        col4.metric("Avg Reward", f"{rl_stats['avg_reward']:.2f}")
        
        # Recent performance trend
        if rl_stats['recent_performance']:
            st.subheader("📈 Recent RL Performance")
            fig_rl = go.Figure()
            fig_rl.add_trace(go.Scatter(
                y=rl_stats['recent_performance'],
                mode='lines+markers',
                name='Episode Reward',
                line=dict(color='green')
            ))
            fig_rl.update_layout(
                title="Recent Learning Episodes",
                xaxis_title="Episode",
                yaxis_title="Total Reward"
            )
            st.plotly_chart(fig_rl, use_container_width=True)
        
        # Load and display feedback stats
        if os.path.exists('tagging_feedback.json'):
            with open('tagging_feedback.json', 'r') as f:
                feedback_data = json.load(f)
            
            col1, col2, col3 = st.columns(3)
            
            corrections = feedback_data.get('tag_corrections', {})
            sender_prefs = feedback_data.get('sender_preferences', {})
            
            col1.metric("Total Corrections", len(corrections))
            col2.metric("Learned Senders", len(sender_prefs))
            
            if corrections:
                recent_corrections = list(corrections.values())[-5:]
                accuracy_scores = [c.get('quality', 0) for c in recent_corrections]
                if accuracy_scores:
                    avg_quality = sum(accuracy_scores) / len(accuracy_scores)
                    col3.metric("Recent Quality", f"{avg_quality:.1f}")
            
            # Show recent improvements
            improvements = components['tagger'].suggest_tag_improvements()
            if improvements:
                st.write("**Suggested Improvements:**")
                for improvement in improvements[:3]:
                    st.write(f"• {improvement}")
        
        # Show smart suggestion usage if available
        suggestion_stats = components['suggestions'].usage_stats
        if suggestion_stats.get('user_preferences'):
            st.subheader("📈 Action Usage Statistics")
            
            action_counts = suggestion_stats['user_preferences']
            if action_counts:
                # Create a simple bar chart of most used actions
                action_data = [{"Action": action.replace('_', ' ').title(), "Count": count} 
                              for action, count in sorted(action_counts.items(), 
                                                        key=lambda x: x[1], 
                                                        reverse=True)]
                if action_data:
                    df_actions = pd.DataFrame(action_data)
                    st.bar_chart(df_actions.set_index("Action"))

elif demo_mode == "SmartBrief v3":
    st.header("🤖 SmartBrief v3 - Context-Aware Message Analysis")
    
    # Demo mode selection
    smartbrief_mode = st.radio(
        "Select SmartBrief Mode:",
        ["Single Message", "Batch Processing", "Upload JSON", "Context Analysis"],
        horizontal=True
    )
    
    if smartbrief_mode == "Single Message":
        st.subheader("📝 Single Message Analysis")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Input form
            with st.form("single_message_form"):
                user_id = st.text_input("User ID:", value="demo_user")
                platform = st.selectbox("Platform:", ['whatsapp', 'email', 'slack', 'teams', 'instagram', 'discord'])
                message_text = st.text_area("Message Text:", 
                    value="Hey! Can you send me those photos from yesterday? Need them for my Instagram story ASAP!")
                
                submitted = st.form_submit_button("🔍 Analyze Message")
                
                if submitted and message_text:
                    message_data = {
                        'user_id': user_id,
                        'platform': platform,
                        'message_text': message_text,
                        'timestamp': datetime.now().isoformat(),
                        'message_id': f"msg_{datetime.now().timestamp()}"
                    }
                    
                    with st.spinner("Analyzing message..."):
                        result = components['smartbrief'].summarize(message_data, use_context=use_context)
                        
                        # Store in context
                        components['context_loader'].add_message(message_data, result)
                    
                    st.success("✅ Analysis Complete!")
                    display_smartbrief_result(message_data, result, 0)
        
        with col2:
            st.subheader("📊 Quick Stats")
            stats = components['smartbrief'].get_stats()
            
            st.metric("Messages Processed", stats['processed'])
            st.metric("Context Usage Rate", f"{stats['context_usage_rate']:.1%}")
            st.metric("Unique Users", stats['unique_users'])
            
            if stats['platforms']:
                st.write("**Platform Distribution:**")
                for platform, count in stats['platforms'].items():
                    st.write(f"• {platform}: {count}")
    
    elif smartbrief_mode == "Batch Processing":
        st.subheader("📦 Batch Message Processing")
        
        # Sample messages for demo
        sample_messages = [
            {
                'user_id': 'alice_work',
                'platform': 'email',
                'message_text': 'Hi team, please review the quarterly budget proposal attached. Need feedback by Friday for the board meeting.',
                'timestamp': '2025-08-07T09:00:00Z',
                'message_id': 'msg_001'
            },
            {
                'user_id': 'bob_friend',
                'platform': 'whatsapp',
                'message_text': 'Hey! What time is the party tonight? Should I bring anything?',
                'timestamp': '2025-08-07T14:30:00Z',
                'message_id': 'msg_002'
            },
            {
                'user_id': 'alice_work',
                'platform': 'email',
                'message_text': 'Following up on the budget proposal - any updates? The board meeting is tomorrow!',
                'timestamp': '2025-08-07T16:45:00Z',
                'message_id': 'msg_003'
            },
            {
                'user_id': 'customer_support',
                'platform': 'slack',
                'message_text': 'The login system is down again. Multiple customers are complaining. This is urgent!',
                'timestamp': '2025-08-07T11:15:00Z',
                'message_id': 'msg_004'
            },
            {
                'user_id': 'mom_family',
                'platform': 'whatsapp',
                'message_text': 'Thanks for helping with the computer setup yesterday! You\'re the best ❤️',
                'timestamp': '2025-08-07T08:20:00Z',
                'message_id': 'msg_005'
            }
        ]
        
        # Filter by platform if selected
        if selected_platform != 'All':
            sample_messages = [msg for msg in sample_messages if msg['platform'] == selected_platform]
        
        st.write(f"**Sample Dataset:** {len(sample_messages)} messages")
        
        if st.button("🚀 Process All Messages"):
            with st.spinner("Processing messages..."):
                results = components['smartbrief'].batch_summarize(sample_messages, use_context=use_context)
                
                # Store in context
                for msg, result in zip(sample_messages, results):
                    components['context_loader'].add_message(msg, result)
            
            st.success(f"✅ Processed {len(results)} messages!")
            
            # Store results for display
            st.session_state.smartbrief_results = list(zip(sample_messages, results))
            
            # Display results
            st.subheader("📋 Processing Results")
            
            for i, (message, result) in enumerate(st.session_state.smartbrief_results):
                display_smartbrief_result(message, result, i)
                st.markdown("---")
            
            # Analytics
            st.subheader("📊 Analytics Dashboard")
            
            # Create analytics charts
            df = pd.DataFrame(results)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Intent distribution
                intent_counts = df['intent'].value_counts()
                fig_intent = px.pie(
                    values=intent_counts.values,
                    names=intent_counts.index,
                    title="Intent Distribution"
                )
                st.plotly_chart(fig_intent, use_container_width=True)
            
            with col2:
                # Urgency distribution
                urgency_counts = df['urgency'].value_counts()
                urgency_colors = {'high': '#ff4444', 'medium': '#ffaa44', 'low': '#44ff44'}
                fig_urgency = px.bar(
                    x=urgency_counts.index,
                    y=urgency_counts.values,
                    title="Urgency Levels",
                    color=urgency_counts.index,
                    color_discrete_map=urgency_colors
                )
                st.plotly_chart(fig_urgency, use_container_width=True)
            
            with col3:
                # Platform distribution
                platform_counts = pd.Series([msg['platform'] for msg in sample_messages]).value_counts()
                fig_platform = px.bar(
                    x=platform_counts.index,
                    y=platform_counts.values,
                    title="Messages by Platform"
                )
                st.plotly_chart(fig_platform, use_container_width=True)
    
    elif smartbrief_mode == "Upload JSON":
        st.subheader("📁 Upload Your Own Messages")
        
        uploaded_file = st.file_uploader(
            "Choose a JSON file with your messages",
            type=['json'],
            help="Upload a JSON file containing an array of message objects"
        )
        
        if uploaded_file is not None:
            try:
                messages = json.load(uploaded_file)
                
                if not isinstance(messages, list):
                    st.error("JSON file must contain an array of message objects")
                else:
                    st.success(f"✅ Loaded {len(messages)} messages from file")
                    
                    # Validate message format
                    required_fields = ['user_id', 'platform', 'message_text']
                    valid_messages = []
                    
                    for i, msg in enumerate(messages):
                        if all(field in msg for field in required_fields):
                            if 'timestamp' not in msg:
                                msg['timestamp'] = datetime.now().isoformat()
                            if 'message_id' not in msg:
                                msg['message_id'] = f"uploaded_msg_{i}"
                            valid_messages.append(msg)
                        else:
                            st.warning(f"Message {i+1} missing required fields: {required_fields}")
                    
                    if valid_messages:
                        st.write(f"**Valid Messages:** {len(valid_messages)}")
                        
                        # Show sample
                        with st.expander("📋 Preview Messages"):
                            st.json(valid_messages[:3])
                        
                        if st.button("🔍 Analyze Uploaded Messages"):
                            with st.spinner("Processing uploaded messages..."):
                                results = components['smartbrief'].batch_summarize(valid_messages, use_context=use_context)
                                
                                # Store in context
                                for msg, result in zip(valid_messages, results):
                                    components['context_loader'].add_message(msg, result)
                            
                            st.success("✅ Analysis Complete!")
                            
                            # Display results
                            for i, (message, result) in enumerate(zip(valid_messages, results)):
                                display_smartbrief_result(message, result, i)
                                if i < len(valid_messages) - 1:
                                    st.markdown("---")
                            
                            # Download results
                            results_json = json.dumps(results, indent=2)
                            st.download_button(
                                label="💾 Download Results (JSON)",
                                data=results_json,
                                file_name=f"smartbrief_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json"
                            )
                
            except json.JSONDecodeError:
                st.error("Invalid JSON file. Please check the format.")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
        
        # Show expected format
        st.subheader("📋 Expected JSON Format")
        st.code("""
[
  {
    "user_id": "user123",
    "platform": "whatsapp",
    "message_text": "Hey! How are you doing?",
    "timestamp": "2025-08-07T10:00:00Z",
    "message_id": "optional_id"
  },
  {
    "user_id": "user456",
    "platform": "email",
    "message_text": "Please review the attached document.",
    "timestamp": "2025-08-07T11:00:00Z"
  }
]
        """, language="json")
    
    elif smartbrief_mode == "Context Analysis":
        st.subheader("🧠 Context Awareness Demo")
        
        st.write("This demo shows how SmartBrief v3 uses conversation context to improve analysis.")
        
        # Predefined conversation flow
        conversation_flow = [
            {
                'user_id': 'demo_user',
                'platform': 'whatsapp',
                'message_text': 'Can you send me those vacation photos?',
                'timestamp': '2025-08-07T10:00:00Z',
                'message_id': 'context_msg_1',
                'step': 1,
                'description': 'Initial request'
            },
            {
                'user_id': 'demo_user',
                'platform': 'whatsapp',
                'message_text': 'I need them for my travel blog post',
                'timestamp': '2025-08-07T10:05:00Z',
                'message_id': 'context_msg_2',
                'step': 2,
                'description': 'Additional context'
            },
            {
                'user_id': 'demo_user',
                'platform': 'whatsapp',
                'message_text': 'Any update on those photos? Publishing the blog tomorrow!',
                'timestamp': '2025-08-07T14:30:00Z',
                'message_id': 'context_msg_3',
                'step': 3,
                'description': 'Follow-up with urgency'
            }
        ]
        
        st.subheader("📱 Conversation Flow")
        
        # Process conversation step by step
        for msg in conversation_flow:
            st.write(f"**Step {msg['step']}: {msg['description']}**")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"💬 Message: *{msg['message_text']}*")
            
            with col2:
                analyze_key = f"analyze_{msg['step']}"
                if st.button(f"Analyze Step {msg['step']}", key=analyze_key):
                    result = components['smartbrief'].summarize(msg, use_context=True)
                    
                    # Store in context for next messages
                    components['context_loader'].add_message(msg, result)
                    
                    st.write(f"**Summary:** {result['summary']}")
                    st.write(f"**Intent:** {result['intent']} | **Urgency:** {result['urgency']}")
                    st.write(f"**Context Used:** {'Yes' if result['context_used'] else 'No'}")
                    
                    if result['context_used']:
                        st.success("🧠 Context awareness active!")
                    
                    with st.expander("Detailed Analysis"):
                        for reason in result['reasoning']:
                            st.write(f"• {reason}")
            
            st.markdown("---")
        
        # Context statistics
        st.subheader("📊 Context Statistics")
        context_stats = components['smartbrief'].get_stats()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Context Entries", context_stats['total_context_entries'])
        with col2:
            st.metric("Context Usage Rate", f"{context_stats['context_usage_rate']:.1%}")
        with col3:
            st.metric("Unique Users", context_stats['unique_users'])

elif demo_mode == "Feedback Analytics":
    st.header("📊 Feedback Analytics Dashboard")
    
    # Get feedback analytics
    feedback_analytics = components['feedback_collector'].get_feedback_analytics()
    
    if feedback_analytics['overall_metrics']['total_feedback'] == 0:
        st.info("No feedback data available yet. Process some messages and provide feedback to see analytics here!")
    else:
        # Overall metrics
        st.subheader("📈 Overall Performance")
        
        col1, col2, col3, col4 = st.columns(4)
        
        overall = feedback_analytics['overall_metrics']
        col1.metric("Total Feedback", overall['total_feedback'])
        col2.metric("Positive Feedback", overall['positive_feedback'])
        col3.metric("Satisfaction Rate", f"{overall['satisfaction_rate']:.1%}")
        col4.metric("Average Score", f"{overall['avg_score']:.2f}")
        
        # Platform performance
        st.subheader("🔧 Platform Performance")
        
        platform_perf = feedback_analytics['platform_performance']
        if platform_perf:
            platform_df = pd.DataFrame([
                {
                    'Platform': platform,
                    'Total Feedback': data['total_feedback'],
                    'Positive': data['positive_feedback'],
                    'Negative': data['negative_feedback'],
                    'Satisfaction Rate': f"{data['positive_feedback']/data['total_feedback']:.1%}" if data['total_feedback'] > 0 else "0%"
                }
                for platform, data in platform_perf.items()
            ])
            
            st.dataframe(platform_df, use_container_width=True)
            
            # Platform satisfaction chart
            fig_platform_sat = px.bar(
                platform_df,
                x='Platform',
                y='Positive',
                title="Positive Feedback by Platform",
                color='Positive',
                color_continuous_scale='Greens'
            )
            st.plotly_chart(fig_platform_sat, use_container_width=True)
        
        # Improvement areas
        st.subheader("🎯 Areas for Improvement")
        
        improvement_areas = feedback_analytics['improvement_areas']
        if improvement_areas:
            improvement_df = pd.DataFrame([
                {'Category': category, 'Issues': count}
                for category, count in improvement_areas.items()
            ])
            
            fig_improvements = px.bar(
                improvement_df,
                x='Category',
                y='Issues',
                title="Categories with Negative Feedback",
                color='Issues',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig_improvements, use_container_width=True)
        else:
            st.success("🎉 No major improvement areas identified!")
        
        # Recent trends
        st.subheader("📅 Recent Trends")
        
        trends = feedback_analytics.get('trends', {})
        if trends:
            col1, col2, col3 = st.columns(3)
            
            col1.metric("Recent Feedback Count", trends['recent_feedback_count'])
            col2.metric("Recent Satisfaction", f"{trends['recent_satisfaction_rate']:.1%}")
            
            trend_direction = trends['trend_direction']
            trend_color = "normal" if trend_direction == "improving" else "inverse"
            col3.metric("Trend", trend_direction.title(), delta_color=trend_color)
        
        # Export feedback data
        st.subheader("💾 Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Export as JSON"):
                success = components['feedback_collector'].export_feedback_data(
                    'feedback_export.json', 'json'
                )
                if success:
                    st.success("✅ Feedback data exported to feedback_export.json")
                else:
                    st.error("❌ Error exporting data")
        
        with col2:
            if st.button("📊 Export as CSV"):
                success = components['feedback_collector'].export_feedback_data(
                    'feedback_export.csv', 'csv'
                )
                if success:
                    st.success("✅ Feedback data exported to feedback_export.csv")
                else:
                    st.error("❌ Error exporting data")

elif demo_mode == "Performance Test":
    st.header("🚀 Performance Testing")
    
    st.write("Test the unified system performance with different message volumes.")
    
    # Performance test settings
    col1, col2 = st.columns(2)
    
    with col1:
        test_size = st.selectbox("Test Size:", [10, 50, 100, 500])
        test_platforms = st.multiselect(
            "Platforms to Test:", 
            ['whatsapp', 'email', 'slack', 'teams'],
            default=['whatsapp', 'email']
        )
    
    with col2:
        include_context = st.checkbox("Include Context Processing", value=True)
        include_rl = st.checkbox("Include RL Learning", value=True)
        show_progress = st.checkbox("Show Progress", value=True)
    
    if st.button("🏃‍♂️ Run Performance Test"):
        # Generate test messages
        import random
        
        test_messages = []
        sample_texts = [
            "Can you help me with this urgent issue?",
            "Thanks for your help yesterday!",
            "Meeting scheduled for tomorrow at 2 PM",
            "The system is not working properly",
            "Please review the attached document",
            "What time should we meet?",
            "FYI - server maintenance tonight",
            "Any updates on the project status?"
        ]
        
        for i in range(test_size):
            platform = random.choice(test_platforms)
            text = random.choice(sample_texts)
            
            test_messages.append({
                'user_id': f'test_user_{i % 20}',  # 20 different users
                'platform': platform,
                'message_text': f"{text} (Test message {i+1})",
                'timestamp': (datetime.now() - timedelta(minutes=i)).isoformat(),
                'message_id': f'perf_test_msg_{i}'
            })
        
        # Run performance test
        import time
        
        start_time = time.time()
        
        if show_progress:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            for i, message in enumerate(test_messages):
                # SmartBrief analysis
                result = components['smartbrief'].summarize(message, use_context=include_context)
                results.append(result)
                
                # RL learning simulation
                if include_rl:
                    # Simulate random feedback for testing
                    reward = random.choice([-1.0, 0.5, 1.0, 2.0])
                    components['prioritizer'].update(message, reward)
                
                # Update progress
                progress = (i + 1) / len(test_messages)
                progress_bar.progress(progress)
                status_text.text(f"Processing message {i+1}/{len(test_messages)}")
        else:
            with st.spinner("Running performance test..."):
                results = components['smartbrief'].batch_summarize(test_messages, use_context=include_context)
                
                if include_rl:
                    for message in test_messages:
                        reward = random.choice([-1.0, 0.5, 1.0, 2.0])
                        components['prioritizer'].update(message, reward)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Display results
        st.success("✅ Performance Test Complete!")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Messages Processed", len(results))
        with col2:
            st.metric("Total Time", f"{processing_time:.2f}s")
        with col3:
            st.metric("Avg per Message", f"{processing_time/len(results)*1000:.1f}ms")
        with col4:
            st.metric("Messages/Second", f"{len(results)/processing_time:.1f}")
        
        # Performance breakdown
        st.subheader("📊 Performance Breakdown")
        
        # Intent distribution
        intent_counts = {}
        urgency_counts = {}
        platform_counts = {}
        
        for result in results:
            intent_counts[result['intent']] = intent_counts.get(result['intent'], 0) + 1
            urgency_counts[result['urgency']] = urgency_counts.get(result['urgency'], 0) + 1
        
        for message in test_messages:
            platform_counts[message['platform']] = platform_counts.get(message['platform'], 0) + 1
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Intent Distribution:**")
            for intent, count in intent_counts.items():
                st.write(f"• {intent}: {count}")
        
        with col2:
            st.write("**Urgency Distribution:**")
            for urgency, count in urgency_counts.items():
                st.write(f"• {urgency}: {count}")
        
        with col3:
            st.write("**Platform Distribution:**")
            for platform, count in platform_counts.items():
                st.write(f"• {platform}: {count}")
        
        # RL Performance (if enabled)
        if include_rl:
            st.subheader("🧠 RL Learning Performance")
            rl_stats = components['prioritizer'].get_learning_stats()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("States Learned", rl_stats['total_states'])
            col2.metric("Total Episodes", rl_stats['total_episodes'])
            col3.metric("Avg Reward", f"{rl_stats['avg_reward']:.2f}")

else:
    # Welcome screen
    st.markdown("""
    ## Welcome to Smart Inbox Assistant! 🎉
    
    This unified intelligent email management system combines traditional email processing with advanced SmartBrief v3 analysis:
    
    ### 📧 **Email Processing Mode**
    - Automatic priority tagging with reinforcement learning
    - Smart suggestions and action recommendations
    - Real-time feedback learning from user corrections
    - Text-to-speech capabilities for accessibility
    
    ### 🤖 **SmartBrief v3 Mode**
    - Context-aware message summarization
    - Platform-optimized summaries (WhatsApp, Email, Slack, etc.)
    - Intent detection and urgency analysis
    - Conversation context tracking
    
    ### 📊 **Feedback Analytics**
    - Comprehensive feedback tracking and analysis
    - Platform performance metrics
    - Improvement suggestions based on user feedback
    - Export capabilities for data analysis
    
    ### 🚀 **Performance Testing**
    - Batch processing capabilities
    - Reinforcement learning performance metrics
    - Context processing benchmarks
    - Scalability testing
    
    ---
    
    **🧠 Reinforcement Learning Features:**
    - System learns from your tag corrections
    - Adapts priority scoring based on feedback
    - Builds user preference profiles over time
    - Continuous improvement through reward-based learning
    
    **🎯 SmartBrief v3 Features:**
    - Context intelligence using conversation history
    - Platform-specific optimization
    - Intent classification (8+ categories)
    - Urgency analysis with confidence scoring
    
    ---
    
    **Getting Started:**
    1. Choose your mode from the sidebar
    2. Configure processing options
    3. Start processing emails or messages
    4. Provide feedback to improve the system
    5. Monitor learning progress in analytics
    
    Ready to revolutionize your inbox management with AI? Let's get started! 🚀
    """)
    
    # Quick stats if available
    if os.path.exists('tagging_feedback.json'):
        try:
            with open('tagging_feedback.json', 'r') as f:
                feedback_data = json.load(f)
            
            st.subheader("📈 System Learning Progress")
            col1, col2, col3 = st.columns(3)
            
            corrections = feedback_data.get('tag_corrections', {})
            sender_prefs = feedback_data.get('sender_preferences', {})
            
            col1.metric("Total Corrections", len(corrections))
            col2.metric("Learned Senders", len(sender_prefs))
            col3.metric("Learning Sessions", len(set(c.get('timestamp', '')[:10] for c in corrections.values())))
        except Exception as e:
            st.info("No learning data available yet. Start processing emails to build your personalized assistant!")
    
    # Show SmartBrief stats if available
    smartbrief_stats = components['smartbrief'].get_stats()
    if smartbrief_stats['processed'] > 0:
        st.subheader("🤖 SmartBrief v3 Progress")
        col1, col2, col3 = st.columns(3)
        
        col1.metric("Messages Analyzed", smartbrief_stats['processed'])
        col2.metric("Context Usage Rate", f"{smartbrief_stats['context_usage_rate']:.1%}")
        col3.metric("Unique Users", smartbrief_stats['unique_users'])
    
    # Show RL stats if available
    rl_stats = components['prioritizer'].get_learning_stats()
    if rl_stats['total_feedback'] > 0:
        st.subheader("🧠 Reinforcement Learning Progress")
        col1, col2, col3 = st.columns(3)
        
        col1.metric("RL States", rl_stats['total_states'])
        col2.metric("Learning Episodes", rl_stats['total_episodes'])
        col3.metric("Average Reward", f"{rl_stats['avg_reward']:.2f}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Smart Inbox Assistant v3.0 | Unified Email Processing & SmartBrief Analysis</p>
    <p>🧠 Powered by Reinforcement Learning • 🤖 Enhanced with Context-Aware AI</p>
    <p>💡 Tip: Regular feedback helps both systems learn your preferences better!</p>
</div>
""", unsafe_allow_html=True)
