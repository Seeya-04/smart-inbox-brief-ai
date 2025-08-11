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
