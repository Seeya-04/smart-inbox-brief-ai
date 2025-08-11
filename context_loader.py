"""
Context Loader Module for SmartBrief v3
Handles historical message context loading and management.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import pandas as pd

logger = logging.getLogger(__name__)

class ContextLoader:
    """
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
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading JSON context: {e}")
        
        return {
            'conversations': {},
            'user_profiles': {},
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
        if platform not in profile['platforms']:
            profile['platforms'][platform] = 0
        profile['platforms'][platform] += 1
        
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
        """
        Get conversation context for a user-platform combination.
        
        Args:
            user_id: User identifier
            platform: Platform name
            limit: Maximum number of messages to return
            
        Returns:
            List of context messages
        """
        context_key = f"{user_id}_{platform}"
        conversations = self.context_data.get('conversations', {})
        
        if context_key in conversations:
            messages = conversations[context_key]
            return messages[-limit:] if messages else []
        
        return []
    
    def search_similar_messages(self, query_text: str, user_id: str = None, 
                              platform: str = None, limit: int = 5) -> List[Dict]:
        """
        Search for messages similar to the query text.
        
        Args:
            query_text: Text to search for
            user_id: Optional user filter
            platform: Optional platform filter
            limit: Maximum results to return
            
        Returns:
            List of similar messages with similarity scores
        """
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
        
        Args:
            output_file: Output file path
            format: Export format ('json' or 'csv')
            user_id: Optional user filter
            platform: Optional platform filter
            
        Returns:
            Success status
        """
        try:
            if format.lower() == 'json':
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
            return True
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return False
    
    def import_data(self, input_file: str, format: str = 'json') -> bool:
        """
        Import context data from file.
        
        Args:
            input_file: Input file path
            format: Import format ('json' or 'csv')
            
        Returns:
            Success status
        """
        try:
            if format.lower() == 'json':
                with open(input_file, 'r', encoding='utf-8') as f:
                    imported_data = json.load(f)
                
                # Merge with existing data
                if 'conversations' in imported_data:
                    existing_conversations = self.context_data.get('conversations', {})
                    for key, messages in imported_data['conversations'].items():
                        if key in existing_conversations:
                            # Merge messages, avoiding duplicates
                            existing_ids = {msg.get('message_id') for msg in existing_conversations[key]}
                            new_messages = [msg for msg in messages if msg.get('message_id') not in existing_ids]
                            existing_conversations[key].extend(new_messages)
                        else:
                            existing_conversations[key] = messages
                    
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
            
            logger.info(f"Data imported from {input_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing data: {e}")
            return False
    
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
    
    print("✅ Context Loader tests completed!")
