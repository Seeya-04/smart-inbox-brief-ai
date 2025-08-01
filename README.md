# 📬 Smart Inbox Brief AI

An AI-powered assistant that reads your inbox (in `.json` format), analyzes message content, detects intent, assigns priority using reinforcement learning, and optionally reads it out loud using text-to-speech (TTS).

---

## 🚀 Features

### ✅ **Core Features**

**📧 Inbox Integration (Mock or Live)**
- ✅ Mock IMAP inbox parser with realistic email simulation
- ✅ Live Gmail connection with OAuth support
- ✅ Real-time email reading (5-10 emails)
- ✅ Email display: sender, subject, time, summarized content

**🏷️ Priority Tagging Agent**
- ✅ Comprehensive email classification:
  - **Urgent** - ASAP, emergency, critical, deadline
  - **Important** - Priority, attention required, action needed
  - **Meeting-related** - Schedule, appointment, conference call
  - **Financial/Transactional** - Invoice, payment, bill, receipt
  - **Promotional/Ignore** - Sale, offer, discount, deal
  - **Newsletter** - Weekly updates, monthly digest
  - **Security** - Password, login, suspicious, verify
  - **General** - Default category
- ✅ Tagging with reasoning (keywords detected, sender match, etc.)
- ✅ Rules-based classifier with advanced pattern matching

**🔄 User Feedback Loop**
- ✅ "👍 Was this summary helpful?" feedback buttons
- ✅ "🪄 Did I tag this right?" tag correction functionality
- ✅ Local JSON storage (`tagging_feedback.json`)
- ✅ Adaptive learning from user feedback
- ✅ Confidence scoring and trust indicators per tag/sender
- ✅ Sender preference learning over time

**💡 Smart Suggestions Module**
- ✅ Contextual action suggestions:
  - "Prepare quick reply"
  - "Add to calendar"
  - "Ignore for now"
  - "Set reminder for tomorrow"
- ✅ Tag-based suggestions (different for each email type)
- ✅ Action execution with simulated responses
- ✅ Usage tracking for continuous improvement

**🎨 User Interface Improvements**
- ✅ Complete Streamlit dashboard interface
- ✅ Inbox panel with filters (Urgent/Meeting/etc.)
- ✅ Feedback options on each email summary and tag
- ✅ Suggestion logging and usage analytics
- ✅ Email analytics dashboard with charts
- ✅ Pagination and sorting options

**🧠 Learning & Analytics**
- ✅ Reinforcement Learning (Q-Learning) for prioritization
- ✅ Smart Metrics extraction (intent, urgency, sentiment)
- ✅ Voice Playback (TTS) with pyttsx3
- ✅ Learning statistics and improvement suggestions
- ✅ Feedback quality metrics and sender insights

---

## 📂 Sample Input Format

Upload a file named like `inbox_sample.json` with the following structure:

```json
[
  {
    "id": "email_001",
    "subject": "Urgent: Project Deadline",
    "sender": "manager@company.com",
    "body": "We need to complete this project by tomorrow...",
    "date": "2024-01-01T10:00:00",
    "label": "work"
  }
]
```

---

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up email credentials (optional but recommended):**
   ```bash
   python setup_email.py
   ```
   This will securely store your email credentials so you don't need to enter them every time.

3. **Run the application:**
   
   **Option A: Dashboard (Recommended)**
   ```bash
   streamlit run dashboard.py
   ```
   
   **Option B: Command-line version**
   ```bash
   python main.py
   ```

## 📧 Email Setup

### **Secure Credentials Storage**
The app now includes a secure credentials manager that:
- ✅ **Encrypts your credentials** using Fernet encryption
- ✅ **Stores them locally** so you don't need to remember your app password
- ✅ **Supports multiple providers** (Gmail, Outlook, Yahoo)
- ✅ **Auto-detects IMAP servers** based on your email domain

### **How to Set Up Your Email**

1. **Run the setup script:**
   ```bash
   python setup_email.py
   ```

2. **Enter your credentials:**
   - Email address (e.g., yourname@gmail.com)
   - App password (not your regular password)
   - Email provider (auto-detected for most providers)

3. **For Gmail users:**
   - Enable 2-factor authentication
   - Generate an app password: Google Account → Security → App passwords
   - Use the app password, not your regular password

4. **For Outlook/Hotmail:**
   - Enable 2-factor authentication
   - Generate an app password in your Microsoft account settings

### **Alternative: No Setup Required**
If you don't want to set up live email, the app will automatically use mock emails for demonstration purposes.

---

## 🎯 Core Deliverables Status

| Feature | Status | Implementation |
|---------|--------|----------------|
| Inbox Integration (Mock/Live) | ✅ Complete | EmailReader class with IMAP |
| Priority Tagging Agent | ✅ Complete | PriorityTagger with 8 categories |
| User Feedback Loop | ✅ Complete | JSON storage + adaptive learning |
| Smart Suggestions Module | ✅ Complete | Contextual actions per tag |
| Streamlit UI with Filters | ✅ Complete | Full dashboard interface |
| Learning Analytics | ✅ Complete | Feedback tracking + improvements |

---

## 🔧 Technical Implementation

- **Email Processing**: IMAP integration with fallback to mock data
- **Priority Classification**: Rule-based + ML-enhanced tagging
- **Feedback Storage**: JSON-based local storage
- **UI Framework**: Streamlit with Plotly visualizations
- **TTS**: pyttsx3 for voice playback
- **Learning**: Q-Learning for prioritization + feedback-based adaptation

---

## 📊 Analytics Features

- Email distribution by tag
- Tagging confidence levels
- Sender preference learning
- Action usage statistics
- Feedback quality metrics
- Learning improvement suggestions

---

## 🎉 All Requirements Met!

This Smart Inbox Assistant successfully implements all the core deliverables from the original specification, providing a comprehensive email management solution with AI-powered prioritization, user feedback learning, and smart action suggestions.


