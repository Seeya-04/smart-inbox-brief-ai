import json
import os
import numpy as np
<<<<<<< HEAD
from datetime import datetime
from typing import List, Dict, Tuple, Any

class Prioritizer:
    """
    Email prioritization system using reinforcement learning.
    Learns from user feedback to improve email priority scoring.
    """
    
    def __init__(self, q_table_file='q_table.json', reward_history_file='reward_history.json'):
        self.q_table_file = q_table_file
        self.reward_history_file = reward_history_file
        self.q_table = self._load_q_table()
        self.reward_history = self._load_reward_history()
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.exploration_rate = 0.1
        
    def _load_q_table(self) -> Dict:
        """Load Q-table from file or initialize empty one."""
        if os.path.exists(self.q_table_file):
            try:
                with open(self.q_table_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {}
    
    def _save_q_table(self):
        """Save Q-table to file."""
        try:
            with open(self.q_table_file, 'w') as f:
                json.dump(self.q_table, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save Q-table: {e}")
    
    def _load_reward_history(self) -> List:
        """Load reward history from file."""
        if os.path.exists(self.reward_history_file):
            try:
                with open(self.reward_history_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return []
    
    def _save_reward_history(self):
        """Save reward history to file."""
        try:
            with open(self.reward_history_file, 'w') as f:
                json.dump(self.reward_history, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save reward history: {e}")
    
    def _extract_features(self, email: Dict) -> str:
        """Extract features from email for Q-table state representation."""
        features = []
        
        # Tag-based features
        tag = email.get('tag', 'GENERAL')
        features.append(f"tag_{tag}")
        
        # Confidence level
        confidence = email.get('tag_confidence', 0)
        if confidence > 0.7:
            features.append("high_confidence")
        elif confidence > 0.4:
            features.append("medium_confidence")
        else:
            features.append("low_confidence")
        
        # Sentiment
        sentiment = email.get('sentiment_score', 0)
        if sentiment > 0.1:
            features.append("positive_sentiment")
        elif sentiment < -0.1:
            features.append("negative_sentiment")
        else:
            features.append("neutral_sentiment")
        
        # Metrics-based features
        metrics = email.get('metrics', {})
        urgency = metrics.get('urgency', 'low')
        features.append(f"urgency_{urgency}")
        
        if metrics.get('has_deadline', False):
            features.append("has_deadline")
        
        intent = metrics.get('intent', 'general')
        features.append(f"intent_{intent}")
        
        # Create state key
        return "_".join(sorted(features))
    
    def _calculate_base_score(self, email: Dict) -> float:
        """Calculate base priority score using heuristics."""
        score = 0.0
        
        # Tag-based scoring
        tag_scores = {
            'URGENT': 10.0,
            'SECURITY': 9.0,
            'MEETING': 8.0,
            'FINANCIAL': 7.0,
            'IMPORTANT': 6.0,
            'GENERAL': 3.0,
            'PROMOTIONAL': 2.0,
            'NEWSLETTER': 1.0
        }
        
        tag = email.get('tag', 'GENERAL')
        score += tag_scores.get(tag, 3.0)
        
        # Confidence boost
        confidence = email.get('tag_confidence', 0)
        score += confidence * 2.0
        
        # Sentiment adjustment
        sentiment = email.get('sentiment_score', 0)
        if sentiment < -0.3:  # Very negative sentiment
            score += 2.0
        elif sentiment < -0.1:  # Negative sentiment
            score += 1.0
        
        # Metrics-based adjustments
        metrics = email.get('metrics', {})
        
        urgency_scores = {'high': 3.0, 'medium': 1.5, 'low': 0.0}
        urgency = metrics.get('urgency', 'low')
        score += urgency_scores.get(urgency, 0.0)
        
        if metrics.get('has_deadline', False):
            score += 2.0
        
        # Intent-based scoring
        intent_scores = {
            'request': 2.0,
            'question': 1.5,
            'complaint': 2.5,
            'urgent': 3.0,
            'meeting': 2.0,
            'general': 0.0
        }
        intent = metrics.get('intent', 'general')
        score += intent_scores.get(intent, 0.0)
        
        return max(score, 0.1)  # Ensure minimum score
    
    def prioritize_emails(self, emails: List[Dict]) -> List[Tuple[float, Dict]]:
        """
        Prioritize emails using reinforcement learning enhanced scoring.
        Returns list of (score, email) tuples sorted by priority.
        """
        scored_emails = []
        
        for email in emails:
            # Calculate base score
            base_score = self._calculate_base_score(email)
            
            # Get Q-learning adjustment
            state = self._extract_features(email)
            q_adjustment = self.q_table.get(state, 0.0)
            
            # Combine scores
            final_score = base_score + q_adjustment
            
            scored_emails.append((final_score, email))
        
        # Sort by score (descending)
        scored_emails.sort(key=lambda x: x[0], reverse=True)
        
        return scored_emails
    
    def update_priority(self, email: Dict, user_feedback: float):
        """
        Update Q-table based on user feedback.
        
        Args:
            email: Email that was prioritized
            user_feedback: Feedback score (-1 to 1, where 1 is perfect priority)
        """
        state = self._extract_features(email)
        current_q = self.q_table.get(state, 0.0)
        
        # Q-learning update
        reward = user_feedback
        new_q = current_q + self.learning_rate * (reward - current_q)
        
        self.q_table[state] = new_q
        
        # Record reward
        self.reward_history.append({
            'timestamp': datetime.now().isoformat(),
            'state': state,
            'reward': reward,
            'old_q': current_q,
            'new_q': new_q
        })
        
        # Save updates
        self._save_q_table()
        self._save_reward_history()
    
    def get_learning_stats(self) -> Dict:
        """Get learning statistics."""
        stats = {
            'total_states': len(self.q_table),
            'total_updates': len(self.reward_history),
            'learning_rate': self.learning_rate,
            'discount_factor': self.discount_factor
        }
        
        if self.reward_history:
            recent_rewards = [r['reward'] for r in self.reward_history[-100:]]
            stats.update({
                'average_recent_reward': np.mean(recent_rewards),
                'reward_trend': 'improving' if len(recent_rewards) > 10 and 
                               np.mean(recent_rewards[-10:]) > np.mean(recent_rewards[-20:-10]) 
                               else 'stable'
            })
            
            # Q-value statistics
            if self.q_table:
                q_values = list(self.q_table.values())
                stats.update({
                    'average_q_value': np.mean(q_values),
                    'max_q_value': max(q_values),
                    'min_q_value': min(q_values)
                })
        
        return stats
    
    def get_top_learned_patterns(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Get top learned patterns from Q-table."""
        if not self.q_table:
            return []
        
        # Sort by Q-value
        sorted_patterns = sorted(self.q_table.items(), key=lambda x: x[1], reverse=True)
        return sorted_patterns[:limit]
    
    def reset_learning(self):
        """Reset Q-table and reward history."""
        self.q_table = {}
        self.reward_history = []
        self._save_q_table()
        self._save_reward_history()
        print("Learning data reset successfully.")
=======
import pandas as pd
from collections import defaultdict

class Prioritizer:
    def __init__(self, q_table_file='q_table.json', feedback_file='feedback_log.csv',
                 reward_log_file='reward_history.json', alpha=0.1, gamma=0.9):
        self.alpha = alpha
        self.gamma = gamma
        self.q_table_file = q_table_file
        self.feedback_file = feedback_file
        self.reward_log_file = reward_log_file

        self.q_table = self.load_q_table()
        self.feedback = self.load_feedback()
        self.reward_history = self.load_reward_history()

    def load_q_table(self):
        """Load Q-table from file or create new one."""
        if os.path.exists(self.q_table_file):
            try:
                with open(self.q_table_file, 'r') as f:
                    data = json.load(f)
                # Convert to defaultdict for easier access
                q_table = defaultdict(lambda: defaultdict(float))
                for state, actions in data.items():
                    for action, value in actions.items():
                        q_table[state][action] = value
                return q_table
            except Exception as e:
                print(f"Error loading Q-table: {e}")
                return defaultdict(lambda: defaultdict(float))
        return defaultdict(lambda: defaultdict(float))

    def save_q_table(self):
        """Save Q-table to file."""
        try:
            # Convert defaultdict to regular dict for JSON serialization
            regular_dict = {}
            for state, actions in self.q_table.items():
                regular_dict[state] = dict(actions)
            
            with open(self.q_table_file, 'w') as f:
                json.dump(regular_dict, f, indent=2)
        except Exception as e:
            print(f"Error saving Q-table: {e}")

    def load_feedback(self):
        """Load feedback from CSV file."""
        if os.path.exists(self.feedback_file):
            try:
                df = pd.read_csv(self.feedback_file)
                return df.groupby("email_id")["feedback"].sum().to_dict()
            except Exception as e:
                print(f"Error loading feedback: {e}")
                return {}
        return {}

    def load_reward_history(self):
        """Load reward history from file."""
        if os.path.exists(self.reward_log_file):
            try:
                with open(self.reward_log_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading reward history: {e}")
                return []
        return []

    def save_reward_history(self):
        """Save reward history to file."""
        try:
            with open(self.reward_log_file, 'w') as f:
                json.dump(self.reward_history, f)
        except Exception as e:
            print(f"Error saving reward history: {e}")

    def extract_features(self, email):
        """Extract features from email for state representation."""
        body = email.get('body', '').lower()
        subject = email.get('subject', '').lower()
        sender = email.get('sender', '')
        
        # Extract sender domain/name
        sender_key = 'unknown'
        if sender:
            if '@' in sender:
                sender_key = sender.split('@')[0]
            else:
                sender_key = sender[:10]  # Limit length
        
        features = {
            'sender': sender_key,
            'has_deadline': any(kw in body + subject for kw in [
                'tomorrow', 'today', 'asap', 'urgent', 'deadline', 
                'immediately', 'priority', 'important'
            ]),
            'has_emoji': any(char in body + subject for char in "😊😃📬⏰📅🔥💼📞"),
            'is_work_related': any(kw in body + subject for kw in [
                'meeting', 'project', 'deadline', 'work', 'client', 
                'schedule', 'task', 'report'
            ]),
            'is_promotional': any(kw in body + subject for kw in [
                'offer', 'discount', 'sale', 'promo', 'deal', 'special'
            ])
        }
        return features

    def _state_key(self, features):
        """Create a string key for the state based on features."""
        return f"{features['sender']}_{features['has_deadline']}_{features['has_emoji']}_{features['is_work_related']}"

    def get_priority_score(self, email):
        """Calculate priority score for an email."""
        features = self.extract_features(email)
        state = self._state_key(features)
        
        # Base score from Q-table
        q_values = self.q_table.get(state, {'default': 0.0})
        base_score = sum(q_values.values()) / max(1, len(q_values))
        
        # Feature-based scoring
        feature_score = 0.0
        
        # High priority for work-related emails
        if features['is_work_related']:
            feature_score += 2.0
            
        # High priority for deadline-related emails
        if features['has_deadline']:
            feature_score += 3.0
            
        # Lower priority for promotional emails
        if features['is_promotional']:
            feature_score -= 1.0
            
        # Slight bonus for emails with emojis (might indicate personal/important)
        if features['has_emoji']:
            feature_score += 0.5
            
        # Sender-based scoring
        sender = features['sender']
        if any(term in sender for term in ['support', 'noreply', 'no-reply']):
            feature_score -= 0.5
        elif any(term in sender for term in ['manager', 'hr', 'admin']):
            feature_score += 1.0
            
        return base_score + feature_score

    def update(self, email, reward):
        """Update Q-table based on feedback."""
        features = self.extract_features(email)
        state = self._state_key(features)
        
        # Ensure state exists in Q-table
        if state not in self.q_table:
            self.q_table[state] = defaultdict(float)
        
        # Q-learning update
        current_q = self.q_table[state]['default']
        self.q_table[state]['default'] = current_q + self.alpha * (reward - current_q)
        
        # Save updated Q-table
        self.save_q_table()
        
        return reward

    def prioritize_emails(self, emails):
        """Prioritize list of emails and update model based on feedback."""
        scored_emails = []
        episode_reward = 0
        
        # Reload feedback to get latest
        self.feedback = self.load_feedback()
        
        for email in emails:
            score = self.get_priority_score(email)
            scored_emails.append((score, email))
            
            # Update model if feedback exists for this email
            email_id = email.get('id')
            if email_id and email_id in self.feedback:
                reward = self.feedback[email_id]
                episode_reward += self.update(email, reward)
        
        # Log episode reward
        if episode_reward != 0:  # Only log if there was feedback
            self.reward_history.append(episode_reward)
            self.save_reward_history()
        
        # Sort by score (highest first)
        scored_emails.sort(reverse=True, key=lambda x: x[0])
        return scored_emails

    def get_learning_stats(self):
        """Get statistics about the learning process."""
        stats = {
            'total_states': len(self.q_table),
            'total_feedback': len(self.feedback),
            'total_episodes': len(self.reward_history),
            'avg_reward': np.mean(self.reward_history) if self.reward_history else 0,
            'recent_performance': self.reward_history[-5:] if len(self.reward_history) >= 5 else self.reward_history
        }
        return stats
>>>>>>> 9feb104c2eb5dd41ae26edcdb0da84c87c09344e
