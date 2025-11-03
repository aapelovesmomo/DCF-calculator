# DCF Calculator Desktop App

A clean, simple desktop application for calculating Discounted Cash Flow (DCF) valuations of companies using just their stock ticker.

## Features

- **One-click calculation**: Simply enter a ticker and click "Calculate DCF"
- **Clean desktop interface**: Built with PyQt for a native, modern look
- **Configurable assumptions**:
  - Growth rate: Average (5-year), CAGR, Recent (2-year), or Manual
  - Discount rate (WACC): Auto-calculated or manual
  - Terminal growth rate: Adjustable
  - Risk-free rate and market risk premium: For auto WACC calculation
- **10-year projection period**
- **Perpetuity growth model** for terminal value
- **Easy to use**: Single window with all controls visible

## Installation

1. **Install Python dependencies:**
   ```bash
   python3 -m pip install -r requirements.txt
   ```
   
   Note: If `pip` command doesn't work, use `python3 -m pip` instead.

2. **Run the application:**
   ```bash
   python main.py
   ```

## Usage

1. Enter a company ticker (e.g., AAPL, MSFT, GOOGL) in the "Company Ticker" field
2. Configure your assumptions (or use defaults):
   - Choose growth rate method or enter manual rate
   - Set discount rate to "Auto Calculate" or enter manually
   - Adjust risk-free rate and market risk premium if using auto WACC
   - Set terminal growth rate (default 2.5%)
3. Click "Calculate DCF"
4. View results including:
   - Projected free cash flows for 10 years
   - Terminal value
   - Enterprise value and equity value
   - Value per share
   - Comparison with current market price

## Creating a One-Click Launcher

### macOS

**Option 1: Using the included `.command` file (Recommended)**

**First time setup:**
1. Navigate to the project folder in Finder
2. Right-click on `DCF Calculator.command` → "Get Info"
3. In the "Open with" section, select "Terminal" (or browse to `/Applications/Utilities/Terminal.app`)
4. Check "Always Open With" to make this permanent
5. Close the Get Info window

**To launch:**
1. Double-click `DCF Calculator.command` in Finder
2. The app will launch in a Terminal window

**If you see a security warning:**
1. macOS may block the file the first time
2. Go to System Preferences → Security & Privacy → General
3. Click "Open Anyway" next to the blocked message
4. Or right-click the file → "Open" and then click "Open" in the dialog

**Option 2: Using the shell script**

The project includes `launch.sh` which you can run from Terminal:

```bash
cd /path/to/dcf-calculator
./launch.sh
```

**Option 3: Create your own launcher**

1. Open Terminal
2. Navigate to the project folder
3. Create a `.command` file:
   ```bash
   cat > "DCF Calculator.command" << 'EOF'
   #!/bin/bash
   cd "$(dirname "$0")"
   python3 main.py
   exit
   EOF
   ```
4. Make it executable:
   ```bash
   chmod +x "DCF Calculator.command"
   ```
5. Double-click `DCF Calculator.command` in Finder to launch

**Troubleshooting:**

- If you see "command not found", make sure Python 3 is installed: `python3 --version`
- If macOS blocks the file, go to System Preferences → Security & Privacy → General, and click "Open Anyway"
- You may need to allow Terminal to run on first launch

### Windows

Create a `launch.bat` file:
```batch
@echo off
cd /d %~dp0
python main.py
```

Double-click `launch.bat` to run.

## Notes

- The app fetches financial data from Yahoo Finance using the `yfinance` library
- Calculations are based on publicly available financial statements
- Results are estimates and should not be the sole basis for investment decisions
- Some companies may have incomplete or unavailable data

## Requirements

- Python 3.8 or higher
- Internet connection (for fetching financial data)

