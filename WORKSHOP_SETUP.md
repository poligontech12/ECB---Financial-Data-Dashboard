# ECB Financial Data Visualizer - Workshop Setup Guide

## Prerequisites

- **Python 3.13.7** installed on your system (https://www.python.org/downloads)
- **Visual Studio Code** (https://code.visualstudio.com/)
- **Git** (for repository cloning) 
- **Github Copilot Pro** - The Pro version is required in order to use GPT5 and Claude Sonnet 4 models.

**Note on Python Commands**: This guide uses `py` commands which work on most Windows systems. If `py` doesn't work on your system, replace `py` with `python` in all commands.     

## Setup Instructions

### Step 1: Clone the Repository
Windows (PowerShell):
```powershell
git clone https://github.com/poligontech12/ECB---Financial-Data-Dashboard.git
cd "ECB - Financial Data Visualizer"
```

**Alternative: Manual Download (if git clone is not working)**
If the git clone command fails or you don't have Git installed:
1. Go to the GitHub repository: https://github.com/poligontech12/ECB---Financial-Data-Dashboard
2. Click the green **"Code"** button
3. Select **"Download ZIP"**
4. Extract the downloaded ZIP file to your desired location
5. Open PowerShell and navigate to the extracted folder:
```powershell
cd "path\to\your\extracted\ECB---Financial-Data-Dashboard-main"
```

### Step 2: Install Dependencies
Windows (PowerShell):
```powershell
py -m pip install -r requirements.txt
```

### Step 3: Configure Data Mode
Before running the application, you need to configure it to use local data mode:

Windows (PowerShell):
```powershell
py scripts/toggle_data_mode.py --mode local
```

You should see output similar to:
```
✅ Configuration updated: Data mode set to LOCAL

📊 ECB Data Visualizer Status:
   Current Mode: API
   API Base URL: https://data-api.ecb.europa.eu/service 
   API Timeout: 30 seconds

💡 Tips for local mode:
   - Make sure you have downloaded data files using:
     python scripts/download_ecb_data.py
   - Data files should be in: data/raw-data/
   - Restart the application to apply changes
```

Verify the configuration by checking the status:
```powershell
py scripts/toggle_data_mode.py --status
```

Expected output:
```
📊 ECB Data Visualizer Status:
   Current Mode: LOCAL
   Local Data Directory: [Your Path]\data\raw-data
   Available Data Files: 5 XML files, 5 metadata files
   📁 Data Files:
      - ECB_MAIN_RATE.xml (170,562 bytes)
      - EUR_GBP_DAILY.xml (125,917 bytes)
      - EUR_USD_DAILY.xml (121,446 bytes)
      - EUR_USD_MONTHLY.xml (7,625 bytes)
      - INFLATION_MONTHLY.xml (7,478 bytes)
```

### Step 4: Run the Application
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

---

**Prepared by: Cosmin Irimia & Stefan Rusu**
