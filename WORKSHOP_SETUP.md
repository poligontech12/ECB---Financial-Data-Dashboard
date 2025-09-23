# ECB Financial Data Visualizer - Workshop Setup Guide

## Quick Start for Workshop Participants

This guide will help you set up and run the ECB Financial Data Visualizer with secure PIN authentication.

## Prerequisites

- **Python 3.13.7** installed on your system (https://www.python.org/downloads)
- **Visual Studio Code** (https://code.visualstudio.com/)
- **Git** (for repository cloning) 
- **Github Copilot Pro** - The Pro version is required in order to use GPT5 and Claude Sonnet 4 models.     

## Setup Instructions

### Step 1: Clone the Repository
Windows (PowerShell):
```powershell
git clone https://github.com/poligontech12/ECB---Financial-Data-Dashboard.git
cd "ECB - Financial Data Visualizer"
```

### Step 2: Install Dependencies
Windows (PowerShell):
```powershell
py -m pip install -r requirements.txt
```

### Step 3: Run the Application
Windows (PowerShell):
```powershell
py app.py
```

You should see output similar to:
```
2025-09-18 16:57:30 - [c2347f8e] - ecb_visualizer.database.database - INFO - Database tables created successfully
2025-09-18 16:57:30 - [c2347f8e] - ecb_visualizer.database.database - INFO - Database initialized: sqlite:///...
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

## Accessing the Dashboard

1. **Open your web browser**
2. **Navigate to:** `http://localhost:5000` or `http://127.0.0.1:5000`
3. **Enter the PIN:** `112233`
4. **Click "Access Dashboard"**

## Troubleshooting

### Issue: Module Import Errors
Windows (PowerShell):
```powershell
# Install missing dependencies
py -m pip install -r requirements.txt

# Or install specific packages
py -m pip install flask plotly pandas sqlalchemy cryptography bcrypt pydantic
```

### Issue: Port 5000 Already in Use
Windows (PowerShell):
```powershell
# Run on a different port
py app.py --port 5001
```
Then access: `http://localhost:5001`

### Issue: Database Errors
Windows (PowerShell):
```powershell
# Delete and recreate database
Remove-Item -LiteralPath "data/database.db" -Force -ErrorAction SilentlyContinue
py app.py
```


**Happy Coding!**

*European Central Bank Financial Data Visualizer*

---

**Prepared by: Cosmin Irimia & Stefan Rusu**
