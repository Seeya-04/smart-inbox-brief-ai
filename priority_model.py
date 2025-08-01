import json
import os
import numpy as np
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