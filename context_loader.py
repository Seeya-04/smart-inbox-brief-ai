"""
<<<<<<< HEAD
Context Loader for SmartBrief v3
Manages conversation history and context for improved summarization.
=======
Context Loader Module for SmartBrief v3
Handles historical message context loading and management.
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
"""

import json
import os
<<<<<<< HEAD
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
=======
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import pandas as pd
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03

logger = logging.getLogger(__name__)

class ContextLoader:
    """
<<<<<<< HEAD
    Manages conversation context and history for the summarization system.
    
    Features:
    - Load past messages from JSON or CSV storage
    - Context-aware message retrieval
    - User analytics and patterns
    - Message similarity search
    - Data export/import functionality
    """
    
    def __init__(self, json_file: str = 'conversation_history.json', 
                 csv_file: str = 'message_history.csv', 
                 max_context_days: int = 30):
        self.json_file = json_file
        self.csv_file = csv_file
        self.max_context_days = max_context_days
        
        # Load existing data
        self.conversation_data = self._load_json_data()
        self.message_history = self._load_csv_data()
        
        # Context cache for performance
        self.context_cache = {}
        self.cache_expiry = {}
    
    def _load_json_data(self) -> Dict:
        """Load conversation data from JSON file."""
=======
    Advanced context loader with multiple storage backends and analytics.
    
    Features:
    - JSON storage options
    - Time-windowed context retrieval
    - User analytics and statistics
    - Automatic cleanup of old messages
    - Context similarity matching
    """
    
    def __init__(self, 
        json_file: str = 'message_context.json',
        csv_file: str = 'message_history.csv',
        max_context_days: int = 30,
        max_messages_per_user: int = 100):
    
        self.json_file = json_file
        self.csv_file = csv_file
        self.max_context_days = max_context_days
        self.max_messages_per_user = max_messages_per_user
    
        # Initialize storage
        self.context_data = self._load_json_context()
        self.csv_data = self._load_csv_context()
    
    # Context statistics — moved above cleanup
        self.stats = {
            'total_messages': 0,
            'unique_users': 0,
            'context_retrievals': 0,
            'context_cleanups': 0
        }
    
    # Perform cleanup on initialization
        self._cleanup_old_data()

    
    def _load_json_context(self) -> Dict:
        """Load context from JSON file."""
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
<<<<<<< HEAD
                logger.error(f"Error loading JSON data: {e}")
=======
                logger.error(f"Error loading JSON context: {e}")
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
        
        return {
            'conversations': {},
            'user_profiles': {},
<<<<<<< HEAD
            'metadata': {
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
        }
    
    def _save_json_data(self):
        """Save conversation data to JSON file."""
        try:
            self.conversation_data['metadata']['last_updated'] = datetime.now().isoformat()
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving JSON data: {e}")
    
    def _load_csv_data(self) -> pd.DataFrame:
        """Load message history from CSV file."""
        if os.path.exists(self.csv_file):
            try:
                return pd.read_csv(self.csv_file)
            except Exception as e:
                logger.error(f"Error loading CSV data: {e}")
        
        # Create empty DataFrame with required columns
        return pd.DataFrame(columns=[
            'message_id', 'user_id', 'platform', 'message_text', 
            'timestamp', 'intent', 'urgency', 'summary', 'context_used'
        ])
    
    def _save_csv_data(self):
        """Save message history to CSV file."""
        try:
            self.message_history.to_csv(self.csv_file, index=False)
        except Exception as e:
            logger.error(f"Error saving CSV data: {e}")
    
    def load_past_messages(self, user_id: str, platform: str, limit: int = 3) -> List[Dict]:
        """
        Load past 3 messages from the same user for context.
        
        Args:
            user_id: User identifier
            platform: Platform name
            limit: Number of past messages to load
            
        Returns:
            List of past messages
        """
        # Try CSV first for recent messages
        if not self.message_history.empty:
            user_messages = self.message_history[
                (self.message_history['user_id'] == user_id) &
                (self.message_history['platform'] == platform)
            ].sort_values('timestamp', ascending=False).head(limit)
            
            if not user_messages.empty:
                return user_messages.to_dict('records')
        
        # Fallback to JSON conversation data
        conversation_key = f"{user_id}_{platform}"
        conversations = self.conversation_data.get('conversations', {})
        
        if conversation_key in conversations:
            messages = conversations[conversation_key]
            # Return most recent messages
            return messages[-limit:] if messages else []
        
        return []
    
    def add_message(self, message: Dict, analysis: Dict = None):
        """
        Add a message to the context storage.
        
        Args:
            message: Message dictionary with user_id, platform, message_text, etc.
            analysis: Optional analysis results (intent, urgency, summary, etc.)
        """
        try:
            user_id = message.get('user_id', 'unknown')
            platform = message.get('platform', 'unknown')
            message_id = message.get('message_id', f"msg_{datetime.now().timestamp()}")
            
            # Add to JSON conversation data
            conversation_key = f"{user_id}_{platform}"
            
            if 'conversations' not in self.conversation_data:
                self.conversation_data['conversations'] = {}
            
            if conversation_key not in self.conversation_data['conversations']:
                self.conversation_data['conversations'][conversation_key] = []
            
            conversation_entry = {
                'message_id': message_id,
                'message_text': message.get('message_text', ''),
                'timestamp': message.get('timestamp', datetime.now().isoformat()),
                'analysis': analysis or {}
            }
            
            self.conversation_data['conversations'][conversation_key].append(conversation_entry)
            
            # Keep only recent messages (within max_context_days)
            cutoff_date = datetime.now() - timedelta(days=self.max_context_days)
            self.conversation_data['conversations'][conversation_key] = [
                entry for entry in self.conversation_data['conversations'][conversation_key]
                if datetime.fromisoformat(entry['timestamp']) > cutoff_date
            ]
            
            # Add to CSV history
            csv_entry = {
                'message_id': message_id,
                'user_id': user_id,
                'platform': platform,
                'message_text': message.get('message_text', ''),
                'timestamp': message.get('timestamp', datetime.now().isoformat()),
                'intent': analysis.get('intent', '') if analysis else '',
                'urgency': analysis.get('urgency', '') if analysis else '',
                'summary': analysis.get('summary', '') if analysis else '',
                'context_used': analysis.get('context_used', False) if analysis else False
            }
            
            # Convert to DataFrame row and append
            new_row = pd.DataFrame([csv_entry])
            self.message_history = pd.concat([self.message_history, new_row], ignore_index=True)
            
            # Update user profile
            self._update_user_profile(user_id, platform, message, analysis)
            
            # Clear cache for this user-platform combination
            cache_key = f"{user_id}_{platform}"
            if cache_key in self.context_cache:
                del self.context_cache[cache_key]
                del self.cache_expiry[cache_key]
            
            # Save data
            self._save_json_data()
            self._save_csv_data()
            
            logger.info(f"Added message {message_id} for {user_id} on {platform}")
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
    
    def _update_user_profile(self, user_id: str, platform: str, message: Dict, analysis: Dict = None):
        """Update user profile with message patterns."""
        if 'user_profiles' not in self.conversation_data:
            self.conversation_data['user_profiles'] = {}
        
        if user_id not in self.conversation_data['user_profiles']:
            self.conversation_data['user_profiles'][user_id] = {
                'platforms': {},
                'message_patterns': {
                    'intents': {},
                    'urgency_levels': {},
                    'common_topics': []
                },
                'activity_stats': {
                    'total_messages': 0,
                    'first_seen': datetime.now().isoformat(),
                    'last_seen': datetime.now().isoformat()
                }
            }
        
        profile = self.conversation_data['user_profiles'][user_id]
        
        # Update platform usage
=======
            'platform_stats': {},
            'metadata': {
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'version': '3.0'
            }
        }
    
    def _save_json_context(self):
        """Save context to JSON file."""
        try:
            self.context_data['metadata']['last_updated'] = datetime.now().isoformat()
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(self.context_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving JSON context: {e}")
    
    def _load_csv_context(self) -> Dict:
        """Load context from CSV file."""
        if os.path.exists(self.csv_file):
            try:
                with open(self.csv_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading CSV context: {e}")
        
        # Create empty DataFrame with required columns
        return {}
    
    def _save_csv_context(self):
        """Save context to CSV file."""
        try:
            with open(self.csv_file, 'w', encoding='utf-8') as f:
                json.dump(self.csv_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving CSV context: {e}")
    
    def _cleanup_old_data(self):
        """Remove messages older than max_context_days."""
        cutoff_date = datetime.now() - timedelta(days=self.max_context_days)
        cutoff_timestamp = cutoff_date.timestamp()
        
        # Cleanup JSON data
        conversations = self.context_data.get('conversations', {})
        cleaned_conversations = {}
        
        for user_platform, messages in conversations.items():
            cleaned_messages = []
            for msg in messages:
                try:
                    msg_timestamp = datetime.fromisoformat(msg.get('timestamp', '1970-01-01T00:00:00')).timestamp()
                    if msg_timestamp > cutoff_timestamp:
                        cleaned_messages.append(msg)
                except:
                    # Keep messages with invalid timestamps for safety
                    cleaned_messages.append(msg)
            
            # Limit messages per user
            if len(cleaned_messages) > self.max_messages_per_user:
                cleaned_messages = cleaned_messages[-self.max_messages_per_user:]
            
            if cleaned_messages:  # Only keep non-empty conversations
                cleaned_conversations[user_platform] = cleaned_messages
        
        self.context_data['conversations'] = cleaned_conversations
        
        # Cleanup CSV data
        if self.csv_data:
            try:
                for key, messages in self.csv_data.items():
                    self.csv_data[key] = [msg for msg in messages if datetime.fromisoformat(msg.get('timestamp', '1970-01-01T00:00:00')) > cutoff_date]
            except Exception as e:
                logger.warning(f"Error cleaning CSV data: {e}")
        
        # Save cleaned data
        self._save_json_context()
        self._save_csv_context()
        
        self.stats['context_cleanups'] += 1
    
    def add_message(self, message_data: Dict, analysis_result: Dict = None):
        """
        Add a message to both JSON and CSV storage.
        
        Args:
            message_data: Original message data
            analysis_result: SmartBrief analysis result (optional)
        """
        user_id = message_data.get('user_id', 'unknown')
        platform = message_data.get('platform', 'unknown')
        message_text = message_data.get('message_text', '')
        timestamp = message_data.get('timestamp', datetime.now().isoformat())
        message_id = message_data.get('message_id', f"msg_{datetime.now().timestamp()}")
        
        # Add to JSON storage
        context_key = f"{user_id}_{platform}"
        
        if 'conversations' not in self.context_data:
            self.context_data['conversations'] = {}
        
        if context_key not in self.context_data['conversations']:
            self.context_data['conversations'][context_key] = []
        
        json_message = {
            'message_id': message_id,
            'message_text': message_text,
            'timestamp': timestamp,
            'analysis': analysis_result
        }
        
        self.context_data['conversations'][context_key].append(json_message)
        
        # Limit messages per conversation
        if len(self.context_data['conversations'][context_key]) > self.max_messages_per_user:
            self.context_data['conversations'][context_key] = \
                self.context_data['conversations'][context_key][-self.max_messages_per_user:]
        
        # Add to CSV storage
        if self.csv_data:
            if context_key not in self.csv_data:
                self.csv_data[context_key] = []
            
            csv_row = {
                'message_id': message_id,
                'user_id': user_id,
                'platform': platform,
                'message_text': message_text,
                'timestamp': timestamp,
                'intent': analysis_result.get('intent', '') if analysis_result else '',
                'urgency': analysis_result.get('urgency', '') if analysis_result else '',
                'summary': analysis_result.get('summary', '') if analysis_result else '',
                'context_used': analysis_result.get('context_used', False) if analysis_result else False
            }
            
            self.csv_data[context_key].append(csv_row)
        
        # Update user profiles
        self._update_user_profile(user_id, platform, message_data, analysis_result)
        
        # Update statistics
        self.stats['total_messages'] += 1
        self.stats['unique_users'] = len(self.context_data['conversations'])
        
        # Save data periodically
        if self.stats['total_messages'] % 10 == 0:
            self._save_json_context()
            self._save_csv_context()
        
        logger.debug(f"Added message to context for user {user_id}")
    
    def _update_user_profile(self, user_id: str, platform: str, 
                           message_data: Dict, analysis_result: Dict = None):
        """Update user profile with message statistics."""
        if 'user_profiles' not in self.context_data:
            self.context_data['user_profiles'] = {}
        
        if user_id not in self.context_data['user_profiles']:
            self.context_data['user_profiles'][user_id] = {
                'total_messages': 0,
                'platforms': {},
                'intents': {},
                'urgency_levels': {},
                'first_seen': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat()
            }
        
        profile = self.context_data['user_profiles'][user_id]
        profile['total_messages'] += 1
        profile['last_seen'] = datetime.now().isoformat()
        
        # Platform stats
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
        if platform not in profile['platforms']:
            profile['platforms'][platform] = 0
        profile['platforms'][platform] += 1
        
<<<<<<< HEAD
        # Update activity stats
        profile['activity_stats']['total_messages'] += 1
        profile['activity_stats']['last_seen'] = datetime.now().isoformat()
        
        # Update patterns if analysis is available
        if analysis:
            intent = analysis.get('intent', '')
            urgency = analysis.get('urgency', '')
            
            if intent:
                if intent not in profile['message_patterns']['intents']:
                    profile['message_patterns']['intents'][intent] = 0
                profile['message_patterns']['intents'][intent] += 1
            
            if urgency:
                if urgency not in profile['message_patterns']['urgency_levels']:
                    profile['message_patterns']['urgency_levels'][urgency] = 0
                profile['message_patterns']['urgency_levels'][urgency] += 1
    
    def get_context(self, user_id: str, platform: str, limit: int = 3) -> List[Dict]:
=======
        # Intent and urgency stats (if analysis available)
        if analysis_result:
            intent = analysis_result.get('intent', 'unknown')
            urgency = analysis_result.get('urgency', 'unknown')
            
            if intent not in profile['intents']:
                profile['intents'][intent] = 0
            profile['intents'][intent] += 1
            
            if urgency not in profile['urgency_levels']:
                profile['urgency_levels'][urgency] = 0
            profile['urgency_levels'][urgency] += 1
    
    def get_context(self, user_id: str, platform: str, limit: int = 5) -> List[Dict]:
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
        """
        Get conversation context for a user-platform combination.
        
        Args:
            user_id: User identifier
            platform: Platform name
<<<<<<< HEAD
            limit: Maximum number of context messages to return
=======
            limit: Maximum number of messages to return
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
            
        Returns:
            List of context messages
        """
<<<<<<< HEAD
        cache_key = f"{user_id}_{platform}"
        
        # Check cache first
        if cache_key in self.context_cache:
            cache_time = self.cache_expiry.get(cache_key, datetime.min)
            if datetime.now() - cache_time < timedelta(minutes=5):  # 5-minute cache
                return self.context_cache[cache_key][:limit]
        
        # Load from storage
        context_messages = self.load_past_messages(user_id, platform, limit)
        
        # Cache the result
        self.context_cache[cache_key] = context_messages
        self.cache_expiry[cache_key] = datetime.now()
        
        return context_messages
    
    def get_user_analytics(self, user_id: str) -> Dict:
        """
        Get analytics for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            User analytics dictionary
        """
        profile = self.conversation_data.get('user_profiles', {}).get(user_id, {})
        
        if not profile:
            return {'error': 'User not found'}
        
        # Get message history for this user
        user_messages = self.message_history[self.message_history['user_id'] == user_id]
        
        analytics = {
            'basic_stats': {
                'total_messages': len(user_messages),
                'platforms': profile.get('platforms', {}),
                'first_seen': profile.get('activity_stats', {}).get('first_seen', ''),
                'last_seen': profile.get('activity_stats', {}).get('last_seen', '')
            },
            'message_patterns': profile.get('message_patterns', {}),
            'recent_activity': self._get_recent_activity(user_id),
            'platform_preferences': self._analyze_platform_preferences(user_messages),
            'communication_style': self._analyze_communication_style(user_messages)
        }
        
        return analytics
    
    def _get_recent_activity(self, user_id: str, days: int = 7) -> Dict:
        """Get recent activity for a user."""
        cutoff_date = datetime.now() - timedelta(days=days)
        user_messages = self.message_history[
            (self.message_history['user_id'] == user_id) &
            (pd.to_datetime(self.message_history['timestamp']) > cutoff_date)
        ]
        
        return {
            'messages_last_7_days': len(user_messages),
            'platforms_used': user_messages['platform'].unique().tolist(),
            'most_common_intent': user_messages['intent'].mode().iloc[0] if not user_messages['intent'].empty else 'unknown',
            'average_urgency': user_messages['urgency'].mode().iloc[0] if not user_messages['urgency'].empty else 'low'
        }
    
    def _analyze_platform_preferences(self, user_messages: pd.DataFrame) -> Dict:
        """Analyze user's platform preferences."""
        if user_messages.empty:
            return {}
        
        platform_counts = user_messages['platform'].value_counts()
        total_messages = len(user_messages)
        
        preferences = {}
        for platform, count in platform_counts.items():
            preferences[platform] = {
                'message_count': int(count),
                'percentage': round((count / total_messages) * 100, 1),
                'most_common_intent': user_messages[user_messages['platform'] == platform]['intent'].mode().iloc[0] if not user_messages[user_messages['platform'] == platform]['intent'].empty else 'unknown'
            }
        
        return preferences
    
    def _analyze_communication_style(self, user_messages: pd.DataFrame) -> Dict:
        """Analyze user's communication style."""
        if user_messages.empty:
            return {}
        
        # Calculate average message length
        message_lengths = user_messages['message_text'].str.len()
        avg_length = message_lengths.mean() if not message_lengths.empty else 0
        
        # Determine communication style
        if avg_length < 50:
            style = 'concise'
        elif avg_length < 150:
            style = 'moderate'
        else:
            style = 'detailed'
        
        # Analyze urgency patterns
        urgency_counts = user_messages['urgency'].value_counts()
        most_common_urgency = urgency_counts.index[0] if not urgency_counts.empty else 'low'
        
        return {
            'average_message_length': round(avg_length, 1),
            'communication_style': style,
            'urgency_tendency': most_common_urgency,
            'context_usage_rate': (user_messages['context_used'].sum() / len(user_messages)) * 100 if len(user_messages) > 0 else 0
        }
    
    def search_similar_messages(self, query_text: str, limit: int = 5) -> List[Dict]:
=======
        context_key = f"{user_id}_{platform}"
        conversations = self.context_data.get('conversations', {})
        
        if context_key in conversations:
            messages = conversations[context_key]
            return messages[-limit:] if messages else []
        
        return []
    
    def search_similar_messages(self, query_text: str, user_id: str = None, 
                              platform: str = None, limit: int = 5) -> List[Dict]:
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
        """
        Search for messages similar to the query text.
        
        Args:
            query_text: Text to search for
<<<<<<< HEAD
            limit: Maximum number of results
=======
            user_id: Optional user filter
            platform: Optional platform filter
            limit: Maximum results to return
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
            
        Returns:
            List of similar messages with similarity scores
        """
<<<<<<< HEAD
        if self.message_history.empty:
            return []
        
        query_words = set(query_text.lower().split())
        similar_messages = []
        
        for _, row in self.message_history.iterrows():
            message_text = str(row['message_text']).lower()
            message_words = set(message_text.split())
            
            # Simple Jaccard similarity
            intersection = len(query_words.intersection(message_words))
            union = len(query_words.union(message_words))
            
            if union > 0:
                similarity = intersection / union
                
                if similarity > 0.1:  # Minimum similarity threshold
                    similar_messages.append({
                        'message_id': row['message_id'],
                        'user_id': row['user_id'],
                        'platform': row['platform'],
                        'message_text': row['message_text'],
                        'timestamp': row['timestamp'],
                        'similarity': similarity,
                        'intent': row['intent'],
                        'urgency': row['urgency']
                    })
        
        # Sort by similarity and return top results
        similar_messages.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_messages[:limit]
    
    def export_data(self, output_file: str, format: str = 'json') -> bool:
        """
        Export conversation data to file.
=======
        if not self.csv_data:
            return []
        
        # Filter data if user_id or platform specified
        search_data = self.csv_data.copy()
        
        if user_id:
            search_data = search_data[search_data['user_id'] == user_id]
        
        if platform:
            search_data = search_data[search_data['platform'] == platform]
        
        if search_data.empty:
            return []
        
        # Simple similarity calculation (word overlap)
        query_words = set(query_text.lower().split())
        similarities = []
        
        for _, row in search_data.iterrows():
            message_text = str(row.get('message_text', ''))
            message_words = set(message_text.lower().split())
            
            if query_words and message_words:
                intersection = query_words.intersection(message_words)
                union = query_words.union(message_words)
                similarity = len(intersection) / len(union) if union else 0
                
                if similarity > 0.1:  # Minimum similarity threshold
                    similarities.append({
                        'message': row.to_dict(),
                        'similarity': similarity
                    })
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:limit]
    
    def get_user_analytics(self, user_id: str) -> Dict:
        """Get comprehensive analytics for a specific user."""
        profile = self.context_data.get('user_profiles', {}).get(user_id, {})
        
        if not profile:
            return {'error': 'User not found'}
        
        # Get messages from CSV for detailed analysis
        user_messages = self.csv_data[user_id] if self.csv_data else []
        
        analytics = {
            'basic_stats': profile,
            'message_frequency': {},
            'platform_preferences': profile.get('platforms', {}),
            'communication_patterns': {},
            'recent_activity': []
        }
        
        if user_messages:
            # Message frequency analysis
            if 'timestamp' in user_messages[0]:
                try:
                    user_messages['timestamp'] = pd.to_datetime(user_messages['timestamp'])
                    user_messages['date'] = user_messages['timestamp'].dt.date
                    
                    # Daily message counts
                    daily_counts = user_messages.groupby('date').size()
                    analytics['message_frequency'] = {
                        'daily_average': daily_counts.mean(),
                        'max_daily': daily_counts.max(),
                        'active_days': len(daily_counts)
                    }
                    
                    # Recent activity (last 7 days)
                    recent_cutoff = datetime.now() - timedelta(days=7)
                    recent_messages = user_messages[user_messages['timestamp'] > recent_cutoff]
                    
                    analytics['recent_activity'] = recent_messages[
                        ['platform', 'intent', 'urgency', 'timestamp']
                    ].to_dict('records')[-10:]  # Last 10 messages
                    
                except Exception as e:
                    logger.warning(f"Error analyzing user timestamps: {e}")
            
            # Communication patterns
            if 'intent' in user_messages[0]:
                intent_counts = pd.Series(user_messages['intent']).value_counts()
                analytics['communication_patterns']['most_common_intent'] = intent_counts.index[0] if not intent_counts.empty else 'unknown'
                analytics['communication_patterns']['intent_distribution'] = intent_counts.to_dict()
            
            if 'urgency' in user_messages[0]:
                urgency_counts = pd.Series(user_messages['urgency']).value_counts()
                analytics['communication_patterns']['urgency_distribution'] = urgency_counts.to_dict()
        
        return analytics
    
    def get_platform_analytics(self, platform: str) -> Dict:
        """Get analytics for a specific platform."""
        if not self.csv_data:
            return {'error': 'No data available'}
        
        platform_data = self.csv_data[platform] if self.csv_data else []
        
        if not platform_data:
            return {'error': 'No data for this platform'}
        
        analytics = {
            'total_messages': len(platform_data),
            'unique_users': len(set(msg['user_id'] for msg in platform_data)),
            'intent_distribution': {},
            'urgency_distribution': {},
            'average_message_length': 0,
            'most_active_users': {},
            'time_patterns': {}
        }
        
        # Intent and urgency distributions
        if 'intent' in platform_data[0]:
            intent_counts = pd.Series([msg['intent'] for msg in platform_data]).value_counts()
            analytics['intent_distribution'] = intent_counts.to_dict()
        
        if 'urgency' in platform_data[0]:
            urgency_counts = pd.Series([msg['urgency'] for msg in platform_data]).value_counts()
            analytics['urgency_distribution'] = urgency_counts.to_dict()
        
        # Message length analysis
        if 'message_text' in platform_data[0]:
            message_lengths = [len(msg['message_text']) for msg in platform_data]
            analytics['average_message_length'] = sum(message_lengths) / len(message_lengths)
        
        # Most active users
        user_counts = {}
        for msg in platform_data:
            user_id = msg['user_id']
            user_counts[user_id] = user_counts.get(user_id, 0) + 1
        
        analytics['most_active_users'] = dict(sorted(user_counts.items(), key=lambda item: item[1], reverse=True)[:10])
        
        # Time patterns
        if 'timestamp' in platform_data[0]:
            try:
                timestamps = [datetime.fromisoformat(msg['timestamp']) for msg in platform_data]
                hours = [ts.hour for ts in timestamps]
                days_of_week = [ts.strftime('%A') for ts in timestamps]
                
                analytics['time_patterns'] = {
                    'hourly_distribution': dict(pd.Series(hours).value_counts().sort_index()),
                    'daily_distribution': dict(pd.Series(days_of_week).value_counts())
                }
            except Exception as e:
                logger.warning(f"Error analyzing time patterns: {e}")
        
        return analytics
    
    def export_data(self, output_file: str, format: str = 'json', 
                   user_id: str = None, platform: str = None) -> bool:
        """
        Export context data to file.
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
        
        Args:
            output_file: Output file path
            format: Export format ('json' or 'csv')
<<<<<<< HEAD
=======
            user_id: Optional user filter
            platform: Optional platform filter
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
            
        Returns:
            Success status
        """
        try:
            if format.lower() == 'json':
<<<<<<< HEAD
                export_data = {
                    'conversations': self.conversation_data,
                    'message_history': self.message_history.to_dict('records'),
                    'export_timestamp': datetime.now().isoformat()
                }
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                    
            elif format.lower() == 'csv':
                self.message_history.to_csv(output_file, index=False)
            else:
                logger.error(f"Unsupported export format: {format}")
                return False
            
            logger.info(f"Data exported to {output_file} in {format} format")
=======
                export_data = self.context_data.copy()
                
                # Apply filters if specified
                if user_id or platform:
                    filtered_conversations = {}
                    for key, messages in export_data.get('conversations', {}).items():
                        key_user, key_platform = key.split('_', 1)
                        
                        if user_id and key_user != user_id:
                            continue
                        if platform and key_platform != platform:
                            continue
                        
                        filtered_conversations[key] = messages
                    
                    export_data['conversations'] = filtered_conversations
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            elif format.lower() == 'csv':
                export_data = self.csv_data.copy()
                
                # Apply filters
                if user_id:
                    export_data = {key: messages for key, messages in export_data.items() if key.startswith(user_id)}
                if platform:
                    export_data = {key: messages for key, messages in export_data.items() if key.endswith(platform)}
                
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'message_id', 'user_id', 'platform', 'message_text', 
                        'timestamp', 'intent', 'urgency', 'summary', 'context_used'
                    ])
                    
                    for messages in export_data.values():
                        for msg in messages:
                            writer.writerow([
                                msg.get('message_id', ''), msg.get('user_id', ''), msg.get('platform', ''), msg.get('message_text', ''),
                                msg.get('timestamp', ''), msg.get('intent', ''), msg.get('urgency', ''), msg.get('summary', ''),
                                msg.get('context_used', False)
                            ])
            
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Data exported to {output_file}")
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
            return True
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return False
    
    def import_data(self, input_file: str, format: str = 'json') -> bool:
        """
<<<<<<< HEAD
        Import conversation data from file.
=======
        Import context data from file.
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
        
        Args:
            input_file: Input file path
            format: Import format ('json' or 'csv')
            
        Returns:
            Success status
        """
        try:
            if format.lower() == 'json':
                with open(input_file, 'r', encoding='utf-8') as f:
<<<<<<< HEAD
                    import_data = json.load(f)
                
                # Merge conversation data
                if 'conversations' in import_data:
                    imported_conversations = import_data['conversations'].get('conversations', {})
                    existing_conversations = self.conversation_data.get('conversations', {})
                    
                    for key, messages in imported_conversations.items():
=======
                    imported_data = json.load(f)
                
                # Merge with existing data
                if 'conversations' in imported_data:
                    existing_conversations = self.context_data.get('conversations', {})
                    for key, messages in imported_data['conversations'].items():
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
                        if key in existing_conversations:
                            # Merge messages, avoiding duplicates
                            existing_ids = {msg.get('message_id') for msg in existing_conversations[key]}
                            new_messages = [msg for msg in messages if msg.get('message_id') not in existing_ids]
                            existing_conversations[key].extend(new_messages)
                        else:
                            existing_conversations[key] = messages
                    
<<<<<<< HEAD
                    self.conversation_data['conversations'] = existing_conversations
                
                # Merge message history
                if 'message_history' in import_data:
                    imported_df = pd.DataFrame(import_data['message_history'])
                    
                    # Avoid duplicates based on message_id
                    existing_ids = set(self.message_history['message_id'].tolist())
                    new_messages = imported_df[~imported_df['message_id'].isin(existing_ids)]
                    
                    self.message_history = pd.concat([self.message_history, new_messages], ignore_index=True)
                    
            elif format.lower() == 'csv':
                imported_df = pd.read_csv(input_file)
                
                # Avoid duplicates
                existing_ids = set(self.message_history['message_id'].tolist())
                new_messages = imported_df[~imported_df['message_id'].isin(existing_ids)]
                
                self.message_history = pd.concat([self.message_history, new_messages], ignore_index=True)
            else:
                logger.error(f"Unsupported import format: {format}")
                return False
            
            # Save merged data
            self._save_json_data()
            self._save_csv_data()
=======
                    self.context_data['conversations'] = existing_conversations
                
                if 'user_profiles' in imported_data:
                    self.context_data['user_profiles'].update(imported_data['user_profiles'])
            
            elif format.lower() == 'csv':
                imported_df = pd.read_csv(input_file)
                
                # Merge with existing CSV data
                if self.csv_data:
                    # Remove duplicates based on message_id
                    combined_df = pd.concat([self.csv_data, imported_df], ignore_index=True)
                    self.csv_data = combined_df.drop_duplicates(subset=['message_id'], keep='last')
                else:
                    self.csv_data = imported_df
            
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Save merged data
            self._save_json_context()
            self._save_csv_context()
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
            
            logger.info(f"Data imported from {input_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing data: {e}")
            return False
    
<<<<<<< HEAD
    def cleanup_old_data(self, days: int = None):
        """
        Clean up old conversation data.
        
        Args:
            days: Number of days to keep (default: max_context_days)
        """
        if days is None:
            days = self.max_context_days
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Clean JSON conversations
        conversations = self.conversation_data.get('conversations', {})
        for key, messages in conversations.items():
            self.conversation_data['conversations'][key] = [
                msg for msg in messages
                if datetime.fromisoformat(msg['timestamp']) > cutoff_date
            ]
        
        # Clean CSV history
        self.message_history = self.message_history[
            pd.to_datetime(self.message_history['timestamp']) > cutoff_date
        ]
        
        # Save cleaned data
        self._save_json_data()
        self._save_csv_data()
        
        logger.info(f"Cleaned up data older than {days} days")
    
    def get_statistics(self) -> Dict:
        """Get overall statistics about the context data."""
        total_conversations = len(self.conversation_data.get('conversations', {}))
        total_messages = len(self.message_history)
        unique_users = len(self.conversation_data.get('user_profiles', {}))
        
        platform_stats = self.message_history['platform'].value_counts().to_dict() if not self.message_history.empty else {}
        intent_stats = self.message_history['intent'].value_counts().to_dict() if not self.message_history.empty else {}
        
        return {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'unique_users': unique_users,
            'platform_distribution': platform_stats,
            'intent_distribution': intent_stats,
            'data_range': {
                'oldest_message': self.message_history['timestamp'].min() if not self.message_history.empty else None,
                'newest_message': self.message_history['timestamp'].max() if not self.message_history.empty else None
            }
        }


# Example usage and testing
if __name__ == "__main__":
    print("🔄 Testing Context Loader...")
    
    # Initialize context loader
    loader = ContextLoader('test_conversations.json', 'test_history.csv')
    
    # Test adding messages with context scenario
    test_messages = [
        {
            'user_id': 'alice_work',
            'platform': 'email',
            'message_text': 'I will send the quarterly report tonight after the meeting.',
            'timestamp': '2025-08-07T09:00:00Z',
            'message_id': 'test_msg_1'
        },
        {
            'user_id': 'alice_work',
            'platform': 'email',
            'message_text': 'Hey, did the report get done?',
            'timestamp': '2025-08-07T16:45:00Z',
            'message_id': 'test_msg_2'
        }
    ]
    
    test_analyses = [
        {
            'intent': 'informational',
            'urgency': 'low',
            'summary': 'User will send report tonight',
            'context_used': False
        },
        {
            'intent': 'check_progress',
            'urgency': 'medium',
            'summary': 'User is following up on report status',
            'context_used': True
        }
    ]
    
    # Add messages
    for message, analysis in zip(test_messages, test_analyses):
        loader.add_message(message, analysis)
    
    print("✅ Messages added successfully")
    
    # Test context retrieval
    context = loader.get_context('alice_work', 'email')
    print(f"📋 Retrieved {len(context)} context messages")
    
    # Test past messages loading
    past_messages = loader.load_past_messages('alice_work', 'email', 3)
    print(f"📚 Loaded {len(past_messages)} past messages")
    
    # Test user analytics
    analytics = loader.get_user_analytics('alice_work')
    print(f"📊 User analytics: {analytics['basic_stats']['total_messages']} total messages")
    
    # Test statistics
    stats = loader.get_statistics()
    print(f"📈 Overall stats: {stats['total_messages']} messages, {stats['unique_users']} users")
=======
    def get_global_stats(self) -> Dict:
        """Get global statistics across all users and platforms."""
        stats = {
            'total_conversations': len(self.context_data.get('conversations', {})),
            'total_users': len(self.context_data.get('user_profiles', {})),
            'total_messages': 0,
            'platform_distribution': {},
            'intent_distribution': {},
            'urgency_distribution': {},
            'context_usage_rate': 0,
            'data_retention_days': self.max_context_days,
            **self.stats
        }
        
        # Calculate totals from user profiles
        for profile in self.context_data.get('user_profiles', {}).values():
            stats['total_messages'] += profile.get('total_messages', 0)
            
            # Platform distribution
            for platform, count in profile.get('platforms', {}).items():
                stats['platform_distribution'][platform] = stats['platform_distribution'].get(platform, 0) + count
            
            # Intent distribution
            for intent, count in profile.get('intents', {}).items():
                stats['intent_distribution'][intent] = stats['intent_distribution'].get(intent, 0) + count
            
            # Urgency distribution
            for urgency, count in profile.get('urgency_levels', {}).items():
                stats['urgency_distribution'][urgency] = stats['urgency_distribution'].get(urgency, 0) + count
        
        # Context usage rate from CSV data
        if self.csv_data and 'context_used' in self.csv_data[0]:
            context_used_count = sum(msg['context_used'] for msg in self.csv_data.values())
            stats['context_usage_rate'] = context_used_count / sum(len(messages) for messages in self.csv_data.values())
        
        return stats

    def get_conversation_summary(self, user_id: str, days_back: int = 7) -> Dict[str, Any]:
        """
        Get a summary of recent conversation with a user.
        
        Args:
            user_id: User identifier
            days_back: Number of days to look back
            
        Returns:
            Conversation summary dictionary
        """
        try:
            if user_id not in self.context_data['conversations']:
                return {'message_count': 0, 'platforms': [], 'intents': [], 'urgency_levels': []}
            
            # Get recent messages
            cutoff_date = datetime.now() - timedelta(days=days_back)
            recent_messages = [
                msg for msg in self.context_data['conversations'][user_id]
                if datetime.fromisoformat(msg.get('timestamp', '1970-01-01T00:00:00')) > cutoff_date
            ]
            
            # Analyze conversation patterns
            platforms = list(set(msg.get('platform', 'unknown') for msg in recent_messages))
            intents = []
            urgency_levels = []
            
            for msg in recent_messages:
                if msg.get('analysis'):
                    intents.append(msg['analysis'].get('intent', 'unknown'))
                    urgency_levels.append(msg['analysis'].get('urgency', 'low'))
            
            # Calculate trends
            intent_counts = {}
            urgency_counts = {}
            
            for intent in intents:
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            for urgency in urgency_levels:
                urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1
            
            summary = {
                'message_count': len(recent_messages),
                'platforms': platforms,
                'dominant_intent': max(intent_counts.keys(), key=intent_counts.get) if intent_counts else 'unknown',
                'dominant_urgency': max(urgency_counts.keys(), key=urgency_counts.get) if urgency_counts else 'low',
                'intent_distribution': intent_counts,
                'urgency_distribution': urgency_counts,
                'avg_relevance_score': sum(msg.get('relevance_score', 0.5) for msg in recent_messages) / len(recent_messages) if recent_messages else 0,
                'first_message_date': min(msg.get('timestamp', '') for msg in recent_messages) if recent_messages else None,
                'last_message_date': max(msg.get('timestamp', '') for msg in recent_messages) if recent_messages else None
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating conversation summary for user {user_id}: {e}")
            return {'message_count': 0, 'platforms': [], 'intents': [], 'urgency_levels': []}

    def find_related_messages(self, message: Dict[str, Any], user_id: str, similarity_threshold: float = 0.3) -> List[Dict]:
        """
        Find messages related to the current message.
        
        Args:
            message: Current message
            user_id: User identifier
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of related context entries
        """
        try:
            if user_id not in self.context_data['conversations']:
                return []
            
            current_text = message.get('message_text', '').lower()
            current_words = set(current_text.split())
            
            related_messages = []
            
            for msg in self.context_data['conversations'][user_id]:
                stored_text = msg.get('message_text', '').lower()
                stored_words = set(stored_text.split())
                
                # Calculate simple word overlap similarity
                if current_words and stored_words:
                    intersection = current_words.intersection(stored_words)
                    union = current_words.union(stored_words)
                    similarity = len(intersection) / len(union) if union else 0
                    
                    if similarity >= similarity_threshold:
                        msg_copy = msg.copy()
                        msg_copy['similarity_score'] = similarity
                        related_messages.append(msg_copy)
            
            # Sort by similarity
            related_messages.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return related_messages[:5]  # Return top 5 related messages
            
        except Exception as e:
            logger.error(f"Error finding related messages: {e}")
            return []

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for a specific user."""
        try:
            if user_id not in self.context_data['conversations']:
                return {'message_count': 0, 'first_message': None, 'last_message': None}
            
            user_context = self.context_data['conversations'][user_id]
            
            timestamps = [msg.get('timestamp', '') for msg in user_context]
            timestamps = [ts for ts in timestamps if ts]  # Filter empty timestamps
            
            stats = {
                'message_count': len(user_context),
                'first_message': min(timestamps) if timestamps else None,
                'last_message': max(timestamps) if timestamps else None,
                'platforms_used': list(set(msg.get('platform', 'unknown') for msg in user_context)),
                'avg_relevance_score': sum(msg.get('relevance_score', 0.5) for msg in user_context) / len(user_context) if user_context else 0
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user stats for {user_id}: {e}")
            return {'message_count': 0, 'first_message': None, 'last_message': None}

    def export_context(self, user_id: Optional[str] = None, output_file: Optional[str] = None) -> bool:
        """
        Export context data to file.
        
        Args:
            user_id: Optional user ID to export specific user's context
            output_file: Optional output file path
            
        Returns:
            Success status
        """
        try:
            if output_file is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f'context_export_{timestamp}.json'
            
            if user_id:
                # Export specific user's context
                export_data = {user_id: self.context_data['conversations'].get(user_id, [])}
            else:
                # Export all context
                export_data = self.context_data['conversations']
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Context exported to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting context: {e}")
            return False

    def _calculate_relevance_score(self, message: Dict[str, Any], analysis_result: Optional[Dict] = None) -> float:
        """Calculate relevance score for a message."""
        score = 0.5  # Base score
        
        # Boost score based on urgency
        if analysis_result:
            urgency = analysis_result.get('urgency', 'low')
            if urgency == 'high':
                score += 0.3
            elif urgency == 'medium':
                score += 0.1
            
            # Boost score based on intent
            intent = analysis_result.get('intent', 'informational')
            if intent in ['question', 'request', 'complaint']:
                score += 0.2
            elif intent in ['urgent', 'follow_up']:
                score += 0.3
        
        # Boost score for longer messages (more content)
        message_length = len(message.get('message_text', ''))
        if message_length > 100:
            score += 0.1
        elif message_length > 200:
            score += 0.2
        
        return min(1.0, score)

    def _trim_context(self, context_list: List[Dict]) -> List[Dict]:
        """Trim context list while preserving high-relevance messages."""
        # Sort by relevance score and timestamp
        context_list.sort(key=lambda x: (x.get('relevance_score', 0.5), x.get('timestamp', '1970-01-01T00:00:00')), reverse=True)
        
        # Keep high-relevance messages and recent messages
        high_relevance = [entry for entry in context_list if entry.get('relevance_score', 0.5) > 0.7]
        recent_messages = context_list[:self.max_messages_per_user // 2]
        
        # Combine and deduplicate
        kept_messages = []
        seen_ids = set()
        
        for entry in high_relevance + recent_messages:
            entry_id = entry.get('message_id', id(entry))
            if entry_id not in seen_ids:
                kept_messages.append(entry)
                seen_ids.add(entry_id)
        
        return kept_messages[:self.max_messages_per_user]

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime object."""
        try:
            if timestamp_str:
                # Handle different timestamp formats
                if timestamp_str.endswith('Z'):
                    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    return datetime.fromisoformat(timestamp_str)
            else:
                return datetime.min
        except:
            return datetime.min


# Example usage
if __name__ == "__main__":
    print("🗃️ Testing Context Loader...")
    
    # Create context loader
    loader = ContextLoader()
    
    # Test adding messages
    test_messages = [
        {
            'user_id': 'alice',
            'platform': 'whatsapp',
            'message_text': 'Hey! How are you doing?',
            'timestamp': '2025-08-07T10:00:00Z',
            'message_id': 'msg_001'
        },
        {
            'user_id': 'alice',
            'platform': 'whatsapp',
            'message_text': 'Can you send me those photos from yesterday?',
            'timestamp': '2025-08-07T10:05:00Z',
            'message_id': 'msg_002'
        }
    ]
    
    # Add messages with mock analysis
    for msg in test_messages:
        analysis = {
            'intent': 'question' if '?' in msg['message_text'] else 'social',
            'urgency': 'low',
            'summary': msg['message_text'][:30] + '...',
            'context_used': True
        }
        loader.add_message(msg, analysis)
    
    # Test context retrieval
    context = loader.get_context('alice', 'whatsapp')
    print(f"📱 Context for Alice (WhatsApp): {len(context)} messages")
    
    # Test user analytics
    analytics = loader.get_user_analytics('alice')
    print(f"📊 Alice's analytics: {analytics['basic_stats']['total_messages']} total messages")
    
    # Test global stats
    global_stats = loader.get_global_stats()
    print(f"🌍 Global stats: {global_stats['total_messages']} total messages across {global_stats['total_users']} users")
>>>>>>> 68a78cdd1bc9e2bb6e6f28be3fc2b1e52df3cc03
    
    print("✅ Context Loader tests completed!")
