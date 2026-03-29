<div align="center">

<img src="/app/static/images/logo.png" width="200"/>

[![Hackathon](https://img.shields.io/badge/🏆%20Hackathon%20Project-Nepali%20Leaders%20Network-ff6b6b?style=for-the-badge)](https://github.com)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-blue?style=flat-square&logo=flask)](https://flask.palletsprojects.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-green?style=flat-square&logo=python)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red?style=flat-square&logo=database)](https://www.sqlalchemy.org/)
[![Cohere AI](https://img.shields.io/badge/Cohere%20AI-5.3-purple?style=flat-square&logo=ai)](https://cohere.com/)
[![License](https://img.shields.io/badge/License-MIT-orange?style=flat-square)](LICENSE)

<img src="https://img.shields.io/badge/Status-Active-success?style=for-the-badge" alt="Status: Active">

---

> *Empowering educators with AI-driven insights to identify at-risk students and support mental health*

[Features](#-features) • [Quick Start](#-setup-instructions) • [Team](#meet-the-team) • [API Docs](#-api-documentation)

</div>

---

<div align="center">
<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&pause=1000&color=4FACFE&center=true&vCenter=true&width=600&lines=Bringing+Data-Driven+Care+to+Students;Supporting+Mental+Health+Through+AI;Empowering+Educators+with+Insights" alt="Typing SVG" />
</div>

---

##  Quick Navigation

- [Overview](#-overview)
- [Features](#-features)
- [Setup Instructions](#-setup-instructions)
- [Project Structure](#-project-structure)
- [Meet the Team](#meet-the-team)
- [Usage Guide](#-usage-guide)
- [API Documentation](#-api-documentation)
- [Troubleshooting](#-troubleshooting)

---

##  Overview

**EduPulse AI** is an intelligent web application designed for school counselors, administrators, and educators to monitor student performance and mental health. The system uses machine learning and AI-powered analysis to identify at-risk students before problems escalate.

### Key Capabilities

-  Real-time student performance analytics
-  Automated risk assessment and flagging
-  AI-powered chatbot for guidance
-  Bulk data import with validation
-  Advanced search and filtering
-  Trend analysis and predictions
-  Comprehensive data management
-  Mental health-focused insights

---

## ✨ Features

### 📊 Dashboard
- Real-time statistics (Total Students, At-Risk Count, Attendance, Ratings)
- Interactive at-risk student list
- Color-coded risk levels (HIGH / MEDIUM / LOW)
- One-click student profile access
- Search and filter functionality

### 👤 Student Profiles
- Complete demographic information
- Academic performance tracking
- Attendance history
- Social engagement metrics
- Assignment submission timeline
- Teacher ratings and feedback
- AI-generated insights and recommendations

### 📤 Data Upload
- CSV file import with validation
- Batch student record creation/update
- Error reporting and handling
- Upload history tracking
- Template download for correct format
- Data merging for trend analysis

### 🗂️ Data Management
- View all student records
- Delete individual students
- Bulk data deletion with confirmation
- Upload audit trail
- Database statistics

### 📈 Advanced Analytics
- Risk distribution visualization
- Enrollment trend charts
- Advanced search capabilities
- Custom report generation
- Export-ready data formatting

### 💬 AI Chatbot
- Natural language student queries
- Context-aware responses
- Mental health guidance
- Intervention recommendations
- Resource suggestions
- Emergency support resources

### 🔐 Authentication
- Email/password login
- Session management (24-hour timeout)
- Role-based access control
- Secure credential handling

---

## 🚀 Setup Instructions

###  Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+** — [Download](https://www.python.org/downloads/)
- **pip** — Python package manager (usually comes with Python)
- **Git** — [Download](https://git-scm.com/)
- **Virtual Environment** — Built into Python 3.3+

###  System Requirements

| Component | Requirement |
|-----------|-------------|
| OS | Windows 10+, macOS 10.14+, Ubuntu 18.04+ |
| Python | 3.9 or higher |
| RAM | 2GB minimum, 4GB recommended |
| Storage | 500MB free space |
| Internet | For Cohere AI API (optional) |

---

### Step 1: Clone Repository

```bash
# Using HTTPS
git clone https://github.com/ashasiueThese/edupulse-ai.git
cd edupulse-ai

# OR using SSH
git clone git@github.com:ashasiueThese/edupulse-ai.git
cd edupulse-ai
```

### Step 2: Create Virtual Environment

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell)**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**Windows (Command Prompt)**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

>  **Verify activation:** You should see `(venv)` in your terminal prompt.

### Step 3: Upgrade pip

```bash
# macOS / Linux
python3 -m pip install --upgrade pip

# Windows
python -m pip install --upgrade pip
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs all required packages: Flask 2.3.3, SQLAlchemy 2.0.20, Pandas 2.0.3, Cohere 5.3.0, and more. Installation typically takes 2–3 minutes.

### Step 5: Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit with your editor
nano .env        # macOS/Linux
notepad .env     # Windows
```

**Edit `.env` with required values:**

```env
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-change-this-in-production

# Database
DATABASE_URL=sqlite:///edupulse.db

# Cohere AI (Optional - for advanced features)
COHERE_API_KEY=your-cohere-api-key-here
```

> **Note:** Get a free Cohere API key from [cohere.com](https://cohere.com)

### Step 6: Initialize & Run

```bash
python3 run.py
```

**Expected output:**
```
✓ Cohere client initialized (if API key is set)
 * Serving Flask app 'run'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

### Step 7: Access Application

Open your browser and navigate to: **http://localhost:5000**

### 🔐 Demo Login Credentials

| Role | Email | Password |
|------|-------|----------|
| Counselor | counselor@school.edu | password123 |

---

## 📁 Project Structure

```
edupulse-ai/
├── 📂 app/                          # Main application package
│   ├── __init__.py                  # App factory
│   ├── models.py                    # Database models
│   ├── analytics.py                 # Risk calculation
│   ├── chatbot.py                   # AI assistant logic
│   ├── decorators.py                # Auth decorators
│   │
│   ├── 📂 blueprints/               # Flask blueprints
│   │   ├── __init__.py
│   │   ├── auth.py                  # Login/Logout routes
│   │   ├── dashboard.py             # Dashboard page
│   │   ├── students.py              # Student profiles
│   │   ├── upload.py                # Data upload routes
│   │   ├── analytics.py             # Analytics page
│   │   └── api.py                   # REST API endpoints
│   │
│   ├── 📂 templates/                # HTML templates
│   │   ├── base.html                # Base layout
│   │   ├── login.html               # Login page
│   │   ├── dashboard.html           # Dashboard page
│   │   ├── profile.html             # Student profile
│   │   ├── upload.html              # Upload page
│   │   ├── analytics.html           # Analytics page
│   │   ├── data_management.html     # Data management
│   │   └── 📂 partials/             # Reusable components
│   │       ├── sidebar.html
│   │       ├── navbar.html
│   │       └── chatbot.html
│   │
│   ├── 📂 static/                   # Static files
│   │   ├── 📂 css/
│   │   │   ├── style.css            # Main stylesheet
│   │   │   ├── auth.css             # Authentication styles
│   │   │   └── charts.css           # Chart styling
│   │   ├── 📂 js/
│   │   │   ├── main.js              # Core JavaScript
│   │   │   ├── charts.js            # Chart helpers
│   │   │   └── chatbot.js           # Chatbot functionality
│   │   └── 📂 images/               # Images and icons
│   │
│   └── 📂 uploads/                  # Temporary upload storage
│
├── 📄 config.py                     # Configuration settings
├── 📄 run.py                        # Development entry point
├── 📄 wsgi.py                       # Production entry point
├── 📄 requirements.txt              # Python dependencies
├── 📄 .env.example                  # Environment template
├── 📄 README.md                     # This file
├── 📄 LICENSE                       # MIT License
├── 📄 sample_data.csv               # Example CSV data
└── 📂 venv/                         # Virtual environment (created locally)
```

---

##  Meet the Team

- Alabhya Pahari
- Arjun Pun Magar
- Asha Shah
- Sudip Bashyal
- Sugam Parajuli

---

##  Usage Guide

### Logging In
1. Open `http://localhost:5000`
2. Enter demo credentials (see table above)
3. Click **Login**

### Uploading Student Data
1. Go to **Upload Data** in the sidebar
2. Click the **Template** tab and download the CSV template
3. Fill it with your student data
4. Return to the **Upload** tab
5. Drag & drop or select your file
6. Review the import results

### Viewing Dashboards
- **Dashboard** — Overview of all metrics
- **Analytics** — Detailed charts and trend data
- **Data Management** — View, search, and delete records

### Using Student Profiles
1. Click any student name from the dashboard list
2. View their comprehensive information
3. Scroll to the **AI Insights** section
4. Click **Generate AI Insight** for an AI-powered analysis

### Chatbot Assistance
1. Click the 💬 button in the bottom-right corner
2. Ask about students or general questions
3. Receive AI-powered guidance and recommendations

---

## 🔌 API Documentation

### Authentication

```
POST   /login                         Login user
GET    /logout                        Logout user
```

### Dashboard

```
GET    /                              Main dashboard
GET    /api/dashboard-stats           Get statistics (JSON)
```

### Students

```
GET    /student/<id>                  View student profile
GET    /api/search-students           Search students
GET    /api/student/<id>/ai-insight   Get AI analysis
```

### Data Management

```
GET    /data-management               Data management page
DELETE /api/delete-student/<id>       Delete single student
DELETE /api/delete-all                Delete all data
```

### Upload

```
GET    /upload                        Upload page
POST   /api/upload                    Upload CSV file
GET    /api/download-template         Download CSV template
```

### Analytics & Chatbot

```
GET    /analytics                     Analytics page
POST   /api/chatbot                   Send chat message
```

---

## 🔧 Troubleshooting

**`ModuleNotFoundError: No module named 'flask'`**
```bash
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

**`numpy.dtype size changed` Error**
```bash
pip uninstall numpy pandas -y
pip install numpy==1.26.4 pandas==2.0.3
```

**Database Locked Error**
```bash
rm edupulse.db
python3 run.py
```

**Port 5000 Already in Use**
```bash
# Use a different port
python3 -c "from app import create_app; create_app().run(port=5001)"

# OR kill the process using port 5000
lsof -ti:5000 | xargs kill -9
```

**Cohere API Not Working**
- Verify the API key in your `.env` file
- Check your internet connection
- Visit [cohere.com](https://cohere.com) to obtain or regenerate your API key
- The app functions without Cohere, but with limited AI features

**Changes Not Reflecting**
```bash
# Stop server (Ctrl+C), clear browser cache, then restart
python3 run.py
```

---

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:4facfe,100:00f2fe&height=120&section=footer" width="100%"/>

<div align="center">

Made with  by the **EduPulse AI Team** — March 2026

🏆 Built for **Nepali Leaders Network Hackathon**

</div>
