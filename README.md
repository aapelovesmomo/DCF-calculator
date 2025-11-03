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

Create a simple script to launch the app:

```bash
#!/bin/bash
cd "$(dirname "$0")"
python3 main.py
```

Save it as `launch.sh`, make it executable:
```bash
chmod +x launch.sh
```

You can also create a `.command` file that opens in Terminal:
```bash
#!/bin/bash
cd "$(dirname "$0")"
python3 main.py
exit
```

Save as `DCF Calculator.command` and double-click to run.

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

