import re
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

class PriorityTagger:
    """Enhanced priority tagging system with reasoning and confidence scoring."""
    
    def __init__(self, feedback_file='tagging_feedback.json', confidence_file='tag_confidence.json'):
        self.feedback_file = feedback_file
        self.confidence_file = confidence_file
        
        # Load feedback and confidence data
        self.feedback_data = self.load_feedback()
        self.confidence_scores = self.load_confidence_scores()
        
        # Define tag patterns with weights
        self.tag_patterns = {
            'URGENT': {
                'keywords': ['urgent', 'asap', 'immediately', 'emergency', 'critical', 'deadline today', 'overdue'],
                'subject_patterns': [r'urgent:?', r'asap:?', r'emergency:?', r'critical:?'],
                'sender_patterns': ['boss', 'manager', 'ceo', 'director', 'emergency'],
                'weight': 5.0
            },
            'MEETING': {
                'keywords': ['meeting', 'appointment', 'schedule', 'calendar', 'conference call', 'zoom', 'teams'],
                'subject_patterns': [r'meeting', r'appointment', r'schedule', r'call', r'conference'],
                'sender_patterns': ['calendar', 'scheduler', 'meeting'],
                'weight': 4.0
            },
            'FINANCIAL': {
                'keywords': ['invoice', 'payment', 'bill', 'receipt', 'transaction', 'refund', 'purchase', 'order'],
                'subject_patterns': [r'invoice', r'payment', r'bill', r'receipt', r'order #\d+'],
                'sender_patterns': ['billing', 'payments', 'finance', 'accounting', 'paypal', 'stripe'],
                'weight': 4.5
            },
            'IMPORTANT': {
                'keywords': ['important', 'priority', 'attention required', 'action needed', 'follow up'],
                'subject_patterns': [r'important:?', r'priority:?', r'action required'],
                'sender_patterns': ['hr', 'admin', 'support'],
                'weight': 4.0
            },
            'PROMOTIONAL': {
                'keywords': ['sale', 'offer', 'discount', 'deal', 'promotion', 'coupon', 'limited time'],
                'subject_patterns': [r'\d+% off', r'sale', r'deal', r'offer', r'discount'],
                'sender_patterns': ['marketing', 'promo', 'deals', 'offers', 'newsletter'],
                'weight': 1.0
            },
            'NEWSLETTER': {
                'keywords': ['newsletter', 'weekly update', 'monthly digest', 'blog', 'news'],
                'subject_patterns': [r'newsletter', r'weekly', r'monthly', r'digest'],
                'sender_patterns': ['newsletter', 'news', 'blog', 'updates'],
                'weight': 2.0
            },
            'SECURITY': {
                'keywords': ['security', 'password', 'login', 'suspicious', 'verify', 'authentication'],
                'subject_patterns': [r'security', r'password', r'verify', r'suspicious'],
                'sender_patterns': ['security', 'noreply', 'alerts'],
                'weight': 4.5
            }
        }
        
        # Default tag for emails that don't match any pattern
        self.default_tag = 'GENERAL'
        
    def load_feedback(self) -> Dict:
        """Load user feedback data."""
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading feedback: {e}")
        return {
            'tag_corrections': {},  # email_id -> correct_tag
            'sender_preferences': {},  # sender -> preferred_tag
            'keyword_feedback': {}  # keyword -> tag_accuracy
        }
    
    def save_feedback(self):
        """Save feedback data."""
        try:
            with open(self.feedback_file, 'w') as f:
                json.dump(self.feedback_data, f, indent=2)
        except Exception as e:
            print(f"Error saving feedback: {e}")
    
    def load_confidence_scores(self) -> Dict:
        """Load confidence scores for tags."""
        if os.path.exists(self.confidence_file):
            try:
                with open(self.confidence_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading confidence scores: {e}")
        return {}
    
    def save_confidence_scores(self):
        """Save confidence scores."""
        try:
            with open(self.confidence_file, 'w') as f:
                json.dump(self.confidence_scores, f, indent=2)
        except Exception as e:
            print(f"Error saving confidence scores: {e}")
    
    def extract_features(self, email: Dict) -> Dict:
        """Extract features from email for tagging."""
        subject = email.get('subject', '').lower()
        body = email.get('body', '').lower()
        sender = email.get('sender', '').lower()
        
        # Extract sender domain
        sender_domain = ''
        if '@' in sender:
            sender_domain = sender.split('@')[1] if '@' in sender else sender
        
        # Extract time-based urgency
        text = f"{subject} {body}"
        time_urgency = self._detect_time_urgency(text)
        
        return {
            'subject': subject,
            'body': body,
            'sender': sender,
            'sender_domain': sender_domain,
            'text': text,
            'time_urgency': time_urgency,
            'word_count': len(text.split()),
            'has_attachments': 'attachment' in body or 'attached' in body or email.get('has_image_attachments', False),
            'has_image_attachments': email.get('has_image_attachments', False)
        }
    
    def _detect_time_urgency(self, text: str) -> float:
        """Detect time-based urgency indicators."""
        urgency_score = 0.0
        
        # High urgency time indicators
        high_urgency = ['today', 'now', 'asap', 'immediately', 'urgent']
        for word in high_urgency:
            if word in text:
                urgency_score += 2.0
        
        # Medium urgency time indicators
        medium_urgency = ['tomorrow', 'this week', 'soon', 'deadline']
        for word in medium_urgency:
            if word in text:
                urgency_score += 1.0
        
        # Time patterns (e.g., "by 5 PM", "in 2 hours")
        time_patterns = [
            r'by \d+:\d+',
            r'in \d+ (hour|minute|day)s?',
            r'before \d+',
            r'end of (day|week|month)'
        ]
        
        for pattern in time_patterns:
            if re.search(pattern, text):
                urgency_score += 1.5
        
        return min(urgency_score, 5.0)  # Cap at 5.0
    
    def calculate_tag_score(self, features: Dict, tag: str) -> Tuple[float, List[str]]:
        """Calculate score for a specific tag and return reasoning."""
        if tag not in self.tag_patterns:
            return 0.0, []
        
        pattern = self.tag_patterns[tag]
        score = 0.0
        reasoning = []
        
        # Keyword matching
        keyword_matches = 0
        for keyword in pattern['keywords']:
            if keyword in features['text']:
                keyword_matches += 1
                reasoning.append(f"Keyword '{keyword}' found")
        
        if keyword_matches > 0:
            score += (keyword_matches / len(pattern['keywords'])) * 2.0
        
        # Subject pattern matching
        subject_matches = 0
        for pattern_regex in pattern['subject_patterns']:
            if re.search(pattern_regex, features['subject']):
                subject_matches += 1
                reasoning.append(f"Subject pattern '{pattern_regex}' matched")
        
        if subject_matches > 0:
            score += (subject_matches / len(pattern['subject_patterns'])) * 1.5
        
        # Sender pattern matching
        sender_matches = 0
        for sender_pattern in pattern['sender_patterns']:
            if sender_pattern in features['sender'] or sender_pattern in features['sender_domain']:
                sender_matches += 1
                reasoning.append(f"Sender pattern '{sender_pattern}' matched")
        
        if sender_matches > 0:
            score += (sender_matches / len(pattern['sender_patterns'])) * 1.0
        
        # Apply base weight
        score *= pattern['weight']
        
        # Add time urgency for urgent tags
        if tag == 'URGENT' and features['time_urgency'] > 0:
            score += features['time_urgency']
            reasoning.append(f"Time urgency detected: {features['time_urgency']}")
        
        # Apply learned adjustments from feedback
        sender = features['sender']
        if sender in self.feedback_data.get('sender_preferences', {}):
            preferred_tag = self.feedback_data['sender_preferences'][sender]
            if preferred_tag == tag:
                score *= 1.2  # Boost preferred tags
                reasoning.append(f"User preference: {sender} usually tagged as {tag}")
            else:
                score *= 0.8  # Reduce non-preferred tags
        
        return score, reasoning
    
    def tag_email(self, email: Dict) -> Dict:
        """Tag an email and provide reasoning."""
        features = self.extract_features(email)
        
        # Calculate scores for all tags
        tag_scores = {}
        all_reasoning = {}
        
        for tag in self.tag_patterns.keys():
            score, reasoning = self.calculate_tag_score(features, tag)
            tag_scores[tag] = score
            all_reasoning[tag] = reasoning
        
        # Find best tag
        if max(tag_scores.values()) > 0.5:  # Minimum threshold
            best_tag = max(tag_scores, key=tag_scores.get)
            confidence = min(tag_scores[best_tag] / 10.0, 1.0)  # Normalize to 0-1
        else:
            best_tag = self.default_tag
            confidence = 0.3  # Low confidence for default
            all_reasoning[best_tag] = ["No strong patterns detected"]
        
        # Update confidence tracking
        email_id = email.get('id', 'unknown')
        self.confidence_scores[email_id] = {
            'tag': best_tag,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        }
        
        return {
            'tag': best_tag,
            'confidence': confidence,
            'reasoning': all_reasoning[best_tag],
            'all_scores': tag_scores,
            'features_detected': {
                'time_urgency': features['time_urgency'],
                'word_count': features['word_count'],
                'has_attachments': features['has_attachments']
            }
        }
    
    def process_feedback(self, email_id: str, correct_tag: str, original_tag: str, sender: str, feedback_quality: int = 0):
        """Process user feedback for tag correction.
        
        Args:
            email_id: Unique identifier for the email
            correct_tag: The correct tag for the email
            original_tag: The original tag assigned by the system
            sender: The email sender
            feedback_quality: User rating of the tagging quality (1=helpful, -1=not helpful, 0=neutral)
        """
        # Store tag correction with quality feedback
        self.feedback_data['tag_corrections'][email_id] = {
            'original_tag': original_tag,
            'correct_tag': correct_tag,
            'timestamp': datetime.now().isoformat(),
            'feedback_quality': feedback_quality
        }
        
        # Update sender preferences with weighted learning
        if sender not in self.feedback_data['sender_preferences']:
            self.feedback_data['sender_preferences'][sender] = {}
        
        sender_prefs = self.feedback_data['sender_preferences'][sender]
        # Ensure sender_prefs is a dictionary
        if not isinstance(sender_prefs, dict):
            sender_prefs = {}
            self.feedback_data['sender_preferences'][sender] = sender_prefs
        
        # Ensure correct_tag is a key in the dictionary
        if correct_tag not in sender_prefs:
            sender_prefs[correct_tag] = 0
            
        # Apply weighted learning based on feedback quality
        weight = 1.0
        if feedback_quality > 0:
            weight = 1.5  # Boost learning for positive feedback
        elif feedback_quality < 0:
            weight = 0.5  # Reduce impact for negative feedback
            
        sender_prefs[correct_tag] += weight
        
        # Find most common tag for this sender
        if sender_prefs:
            most_common_tag = max(sender_prefs, key=sender_prefs.get)
            self.feedback_data['sender_preferences'][sender] = most_common_tag
        else:
            self.feedback_data['sender_preferences'][sender] = 'GENERAL'  # Default tag
        
        # Update confidence with feedback quality consideration
        if email_id in self.confidence_scores:
            old_confidence = self.confidence_scores[email_id]['confidence']
            
            # Adjust confidence based on correction and feedback quality
            if original_tag != correct_tag:
                # Larger reduction for negative feedback
                reduction_factor = 0.6 if feedback_quality < 0 else 0.7
                new_confidence = max(0.1, old_confidence * reduction_factor)
            else:
                # Larger boost for positive feedback
                boost_factor = 1.2 if feedback_quality > 0 else 1.1
                new_confidence = min(1.0, old_confidence * boost_factor)
            
            self.confidence_scores[email_id]['confidence'] = new_confidence
            self.confidence_scores[email_id]['corrected'] = True
            self.confidence_scores[email_id]['feedback_quality'] = feedback_quality
        
        # Save feedback
        self.save_feedback()
        self.save_confidence_scores()        
        print(f"✅ Feedback processed: {email_id} corrected from {original_tag} to {correct_tag} with quality {feedback_quality}")
    
    def get_sender_insights(self) -> Dict:
        """Get insights about sender patterns and feedback quality."""
        insights = {
            'sender_preferences': self.feedback_data.get('sender_preferences', {}),
            'most_corrected_tags': {},
            'confidence_by_tag': {},
            'feedback_quality_by_tag': {},
            'total_corrections': len(self.feedback_data.get('tag_corrections', {})),
            'positive_feedback_count': 0,
            'negative_feedback_count': 0,
            'neutral_feedback_count': 0
        }
        
        # Analyze corrections by tag and feedback quality
        corrections = self.feedback_data.get('tag_corrections', {})
        for email_id, correction in corrections.items():
            original = correction['original_tag']
            feedback_quality = correction.get('feedback_quality', 0)
            
            # Count by tag
            if original not in insights['most_corrected_tags']:
                insights['most_corrected_tags'][original] = 0
            insights['most_corrected_tags'][original] += 1
            
            # Count by feedback quality
            if feedback_quality > 0:
                insights['positive_feedback_count'] += 1
            elif feedback_quality < 0:
                insights['negative_feedback_count'] += 1
            else:
                insights['neutral_feedback_count'] += 1
                
            # Track feedback quality by tag
            if original not in insights['feedback_quality_by_tag']:
                insights['feedback_quality_by_tag'][original] = []
            insights['feedback_quality_by_tag'][original].append(feedback_quality)
        
        # Analyze confidence by tag
        for email_id, conf_data in self.confidence_scores.items():
            tag = conf_data['tag']
            confidence = conf_data['confidence']
            
            if tag not in insights['confidence_by_tag']:
                insights['confidence_by_tag'][tag] = []
            insights['confidence_by_tag'][tag].append(confidence)
        
        # Calculate average confidence per tag
        for tag, confidences in insights['confidence_by_tag'].items():
            insights['confidence_by_tag'][tag] = sum(confidences) / len(confidences)
            
        # Calculate average feedback quality per tag
        for tag, qualities in insights['feedback_quality_by_tag'].items():
            if qualities:
                insights['feedback_quality_by_tag'][tag] = sum(qualities) / len(qualities)
            else:
                insights['feedback_quality_by_tag'][tag] = 0
                
        # Calculate overall feedback quality
        total_feedback = insights['positive_feedback_count'] + insights['negative_feedback_count'] + insights['neutral_feedback_count']
        insights['overall_feedback_quality'] = insights['positive_feedback_count'] / total_feedback if total_feedback > 0 else 0
        
        return insights
    
    def suggest_tag_improvements(self) -> List[str]:
        """Suggest improvements to tagging based on feedback and quality metrics."""
        suggestions = []
        insights = self.get_sender_insights()
        
        # Suggest based on most corrected tags with feedback quality consideration
        if insights['most_corrected_tags']:
            most_corrected = max(insights['most_corrected_tags'], 
                               key=insights['most_corrected_tags'].get)
            
            # Check feedback quality for this tag
            tag_feedback_quality = insights['feedback_quality_by_tag'].get(most_corrected, 0)
            if tag_feedback_quality < 0:
                # Negative feedback suggests urgent attention needed
                suggestions.append(f"⚠️ URGENT: Review '{most_corrected}' tag rules - frequently corrected with negative feedback")
            else:
                suggestions.append(f"Consider reviewing '{most_corrected}' tag rules - most frequently corrected")
        
        # Suggest based on low confidence tags
        low_confidence_tags = {tag: conf for tag, conf in insights['confidence_by_tag'].items() 
                              if conf < 0.6}
        if low_confidence_tags:
            for tag in low_confidence_tags:
                # Check if this tag also has negative feedback
                tag_feedback = insights['feedback_quality_by_tag'].get(tag, 0)
                if tag_feedback < 0:
                    suggestions.append(f"⚠️ '{tag}' tag has low confidence AND negative feedback - priority for improvement")
                else:
                    suggestions.append(f"'{tag}' tag has low confidence - consider adding more keywords")
        
        # Suggest sender-based rules
        frequent_senders = {sender for sender, tag in insights['sender_preferences'].items()}
        if len(frequent_senders) > 5:
            suggestions.append("Consider creating sender-specific rules for frequent contacts")
            
        # Suggest improvements based on overall feedback quality
        overall_quality = insights.get('overall_feedback_quality', 0)
        if overall_quality < 0.5 and insights['total_corrections'] > 10:
            suggestions.append("⚠️ Overall tagging system needs improvement - less than 50% positive feedback")
        elif overall_quality > 0.8 and insights['total_corrections'] > 10:
            suggestions.append("✅ Tagging system performing well - over 80% positive feedback")
            
        # Suggest specific tag pattern improvements based on feedback
        negative_feedback_tags = {tag: quality for tag, quality in insights['feedback_quality_by_tag'].items() 
                                if quality < 0}
        if negative_feedback_tags:
            worst_tag = min(negative_feedback_tags, key=negative_feedback_tags.get)
            pattern = self.tag_patterns.get(worst_tag, {})
            if pattern:
                suggestions.append(f"📝 For '{worst_tag}' tag, consider updating these keywords: {', '.join(pattern.get('keywords', [])[:3])}...")
        
        return suggestions
    
    def get_tagging_stats(self) -> Dict:
        """Get comprehensive tagging statistics."""
        stats = {
            'total_emails_tagged': len(self.confidence_scores),
            'total_corrections': len(self.feedback_data.get('tag_corrections', {})),
            'average_confidence': 0.0,
            'tag_distribution': {},
            'correction_rate': 0.0,
            'learned_senders': len(self.feedback_data.get('sender_preferences', {}))
        }
        
        # Calculate average confidence
        if self.confidence_scores:
            confidences = [data['confidence'] for data in self.confidence_scores.values()]
            stats['average_confidence'] = sum(confidences) / len(confidences)
        
        # Calculate tag distribution
        for data in self.confidence_scores.values():
            tag = data['tag']
            stats['tag_distribution'][tag] = stats['tag_distribution'].get(tag, 0) + 1
        
        # Calculate correction rate
        if stats['total_emails_tagged'] > 0:
            stats['correction_rate'] = stats['total_corrections'] / stats['total_emails_tagged']
        
        return stats
<<<<<<< HEAD
=======


# Usage example and testing
if __name__ == "__main__":
    # Test the priority tagger
    tagger = PriorityTagger()
    
    # Test emails
    test_emails = [
        {
            'id': 'test_001',
            'subject': 'URGENT: Server maintenance tonight',
            'body': 'We need to perform emergency server maintenance tonight. Please complete all work by 6 PM.',
            'sender': 'ops-team@company.com'
        },
        {
            'id': 'test_002', 
            'subject': 'Weekly team meeting - Tomorrow 2 PM',
            'body': 'Don\'t forget about our weekly team meeting tomorrow at 2 PM in conference room B.',
            'sender': 'manager@company.com'
        },
        {
            'id': 'test_003',
            'subject': '🎉 50% OFF Everything - Limited Time!',
            'body': 'Get 50% off everything in our store this weekend only! Use code SAVE50.',
            'sender': 'deals@store.com'
        }
    ]
    
    print("Testing Priority Tagging System")
    print("=" * 50)
    
    for email in test_emails:
        result = tagger.tag_email(email)
        print(f"\nEmail: {email['subject']}")
        print(f"Tag: {result['tag']} (Confidence: {result['confidence']:.2f})")
        print(f"Reasoning: {', '.join(result['reasoning'])}")
        print(f"All scores: {result['all_scores']}")
    
    # Test feedback
    print("\n" + "=" * 50)
    print("Testing Feedback System")
    tagger.process_feedback('test_001', 'URGENT', 'URGENT', 'ops-team@company.com')
    tagger.process_feedback('test_002', 'MEETING', 'IMPORTANT', 'manager@company.com')
    
    # Get insights
    insights = tagger.get_sender_insights()
    print(f"Sender insights: {insights}")
    
    # Get stats
    stats = tagger.get_tagging_stats()
    print(f"Tagging stats: {stats}")
>>>>>>> 9feb104c2eb5dd41ae26edcdb0da84c87c09344e
