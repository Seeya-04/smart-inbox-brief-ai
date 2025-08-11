"""
SmartBrief v3 - Interactive Streamlit Demo
Comprehensive demo application showcasing all features of the context-aware summarizer.
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import tempfile
import os
from smart_summarizer_v3 import SmartSummarizerV3, summarize_message
from context_loader import ContextLoader

# Page configuration
st.set_page_config(
    page_title="SmartBrief v3 Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
}
.intent-high { border-left-color: #ff4444; }
.intent-medium { border-left-color: #ffaa44; }
.intent-low { border-left-color: #44ff44; }
.platform-whatsapp { background-color: #e8f5e8; }
.platform-email { background-color: #e8e8f5; }
.platform-slack { background-color: #f5e8f5; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'summarizer' not in st.session_state:
    st.session_state.summarizer = SmartSummarizerV3()
if 'processed_messages' not in st.session_state:
    st.session_state.processed_messages = []
if 'demo_mode' not in st.session_state:
    st.session_state.demo_mode = 'single'

def load_sample_messages():
    """Load sample messages for demonstration."""
    return [
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
        },
        {
            'user_id': 'project_manager',
            'platform': 'teams',
            'message_text': 'Can we schedule a quick standup for tomorrow at 10 AM? Need to discuss the sprint planning.',
            'timestamp': '2025-08-07T17:10:00Z',
            'message_id': 'msg_006'
        },
        {
            'user_id': 'newsletter_tech',
            'platform': 'email',
            'message_text': 'Weekly Tech Digest: AI breakthroughs, new frameworks, and industry trends. Unsubscribe anytime.',
            'timestamp': '2025-08-07T07:00:00Z',
            'message_id': 'msg_007'
        },
        {
            'user_id': 'bob_friend',
            'platform': 'whatsapp',
            'message_text': 'Did you see my message about the party? Need to know headcount for food!',
            'timestamp': '2025-08-07T18:00:00Z',
            'message_id': 'msg_008'
        }
    ]

def create_analytics_charts(results):
    """Create analytics charts from processed results."""
    if not results:
        return None, None, None
    
    df = pd.DataFrame(results)
    
    # Intent distribution
    intent_counts = df['intent'].value_counts()
    fig_intent = px.pie(
        values=intent_counts.values,
        names=intent_counts.index,
        title="Intent Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
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
    
    # Platform distribution
    platform_counts = df['platform'].value_counts()
    fig_platform = px.bar(
        x=platform_counts.index,
        y=platform_counts.values,
        title="Messages by Platform",
        color=platform_counts.index,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    return fig_intent, fig_urgency, fig_platform

def display_message_result(message, result, index):
    """Display a message and its analysis result."""
    with st.container():
        # Create columns for layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Message content
            st.markdown(f"""
            <div class="metric-card platform-{message['platform']}">
                <h4>📱 {message['platform'].title()} - {message['user_id']}</h4>
                <p><strong>Message:</strong> {message['message_text']}</p>
                <p><strong>Summary:</strong> {result['summary']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Analysis results
            urgency_color = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[result['urgency']]
            
            st.markdown(f"""
            <div class="metric-card intent-{result['urgency']}">
                <p><strong>🎯 Intent:</strong> {result['intent'].title()}</p>
                <p><strong>{urgency_color} Urgency:</strong> {result['urgency'].title()}</p>
                <p><strong>🎲 Confidence:</strong> {result['confidence']:.2f}</p>
                <p><strong>🧠 Context:</strong> {'Yes' if result['context_used'] else 'No'}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Expandable reasoning
        with st.expander(f"🔍 Analysis Details - Message {index + 1}"):
            st.write("**Reasoning:**")
            for reason in result['reasoning']:
                st.write(f"• {reason}")
            
            if result.get('platform_optimized'):
                st.success("✅ Platform-optimized summary generated")
            
            st.json({
                'intent': result['intent'],
                'urgency': result['urgency'],
                'confidence': result['confidence'],
                'context_used': result['context_used']
            })

# Main app
def main():
    st.title("🤖 SmartBrief v3 - Interactive Demo")
    st.markdown("*Context-Aware, Platform-Agnostic Message Summarization*")
    
    # Sidebar
    st.sidebar.title("🎛️ Demo Controls")
    
    # Demo mode selection
    demo_mode = st.sidebar.radio(
        "Select Demo Mode:",
        ["Single Message", "Batch Processing", "Upload JSON", "Context Analysis", "Performance Test"],
        key="demo_mode_radio"
    )
    
    # Platform filter
    platforms = ['All', 'whatsapp', 'email', 'slack', 'teams', 'instagram', 'discord']
    selected_platform = st.sidebar.selectbox("Filter by Platform:", platforms)
    
    # Context settings
    st.sidebar.subheader("🧠 Context Settings")
    use_context = st.sidebar.checkbox("Use Context Awareness", value=True)
    max_context = st.sidebar.slider("Max Context Messages", 1, 10, 3)
    
    # Update summarizer settings
    st.session_state.summarizer.max_context_messages = max_context
    
    # Main content area
    if demo_mode == "Single Message":
        st.header("📝 Single Message Analysis")
        
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
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    with st.spinner("Analyzing message..."):
                        result = st.session_state.summarizer.summarize(message_data, use_context=use_context)
                    
                    st.success("✅ Analysis Complete!")
                    display_message_result(message_data, result, 0)
        
        with col2:
            st.subheader("📊 Quick Stats")
            stats = st.session_state.summarizer.get_stats()
            
            st.metric("Messages Processed", stats['processed'])
            st.metric("Context Usage Rate", f"{stats['context_usage_rate']:.1%}")
            st.metric("Unique Users", stats['unique_users'])
            
            if stats['platforms']:
                st.write("**Platform Distribution:**")
                for platform, count in stats['platforms'].items():
                    st.write(f"• {platform}: {count}")
    
    elif demo_mode == "Batch Processing":
        st.header("📦 Batch Message Processing")
        
        # Load sample messages
        sample_messages = load_sample_messages()
        
        # Filter by platform if selected
        if selected_platform != 'All':
            sample_messages = [msg for msg in sample_messages if msg['platform'] == selected_platform]
        
        st.write(f"**Sample Dataset:** {len(sample_messages)} messages")
        
        if st.button("🚀 Process All Messages"):
            with st.spinner("Processing messages..."):
                results = st.session_state.summarizer.batch_summarize(sample_messages, use_context=use_context)
            
            st.success(f"✅ Processed {len(results)} messages!")
            
            # Store results for analytics
            st.session_state.processed_messages = list(zip(sample_messages, results))
            
            # Display results
            st.subheader("📋 Processing Results")
            
            for i, (message, result) in enumerate(st.session_state.processed_messages):
                display_message_result(message, result, i)
                st.markdown("---")
            
            # Analytics
            st.subheader("📊 Analytics Dashboard")
            
            fig_intent, fig_urgency, fig_platform = create_analytics_charts(results)
            
            if fig_intent:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.plotly_chart(fig_intent, use_container_width=True)
                
                with col2:
                    st.plotly_chart(fig_urgency, use_container_width=True)
                
                with col3:
                    st.plotly_chart(fig_platform, use_container_width=True)
    
    elif demo_mode == "Upload JSON":
        st.header("📁 Upload Your Own Messages")
        
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
                    return
                
                st.success(f"✅ Loaded {len(messages)} messages from file")
                
                # Validate message format
                required_fields = ['user_id', 'platform', 'message_text']
                valid_messages = []
                
                for i, msg in enumerate(messages):
                    if all(field in msg for field in required_fields):
                        if 'timestamp' not in msg:
                            msg['timestamp'] = datetime.now().isoformat()
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
                            results = st.session_state.summarizer.batch_summarize(valid_messages, use_context=use_context)
                        
                        st.success("✅ Analysis Complete!")
                        
                        # Display results
                        for i, (message, result) in enumerate(zip(valid_messages, results)):
                            display_message_result(message, result, i)
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
    
    elif demo_mode == "Context Analysis":
        st.header("🧠 Context Awareness Demo")
        
        st.write("This demo shows how SmartBrief v3 uses conversation context to improve analysis.")
        
        # Predefined conversation flow
        conversation_flow = [
            {
                'user_id': 'demo_user',
                'platform': 'whatsapp',
                'message_text': 'Can you send me those vacation photos?',
                'timestamp': '2025-08-07T10:00:00Z',
                'step': 1,
                'description': 'Initial request'
            },
            {
                'user_id': 'demo_user',
                'platform': 'whatsapp',
                'message_text': 'I need them for my travel blog post',
                'timestamp': '2025-08-07T10:05:00Z',
                'step': 2,
                'description': 'Additional context'
            },
            {
                'user_id': 'demo_user',
                'platform': 'whatsapp',
                'message_text': 'Any update on those photos? Publishing the blog tomorrow!',
                'timestamp': '2025-08-07T14:30:00Z',
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
                if st.button(f"Analyze Step {msg['step']}", key=f"analyze_{msg['step']}"):
                    result = st.session_state.summarizer.summarize(msg, use_context=True)
                    
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
        context_stats = st.session_state.summarizer.get_stats()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Context Entries", context_stats['total_context_entries'])
        with col2:
            st.metric("Context Usage Rate", f"{context_stats['context_usage_rate']:.1%}")
        with col3:
            st.metric("Unique Users", context_stats['unique_users'])
    
    elif demo_mode == "Performance Test":
        st.header("🚀 Performance Testing")
        
        st.write("Test SmartBrief v3 performance with different message volumes.")
        
        # Performance test settings
        col1, col2 = st.columns(2)
        
        with col1:
            test_size = st.selectbox("Test Size:", [10, 50, 100, 500, 1000])
            test_platforms = st.multiselect(
                "Platforms to Test:", 
                ['whatsapp', 'email', 'slack', 'teams'],
                default=['whatsapp', 'email']
            )
        
        with col2:
            include_context = st.checkbox("Include Context Processing", value=True)
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
                    'timestamp': (datetime.now() - timedelta(minutes=i)).isoformat()
                })
            
            # Run performance test
            import time
            
            start_time = time.time()
            
            if show_progress:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                results = []
                for i, message in enumerate(test_messages):
                    result = st.session_state.summarizer.summarize(message, use_context=include_context)
                    results.append(result)
                    
                    # Update progress
                    progress = (i + 1) / len(test_messages)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing message {i+1}/{len(test_messages)}")
            else:
                with st.spinner("Running performance test..."):
                    results = st.session_state.summarizer.batch_summarize(test_messages, use_context=include_context)
            
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
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🤖 SmartBrief v3 - Context-Aware Message Summarization</p>
        <p>Built with Streamlit • Powered by Advanced NLP</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
