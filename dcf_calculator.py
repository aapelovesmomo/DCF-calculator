"""
DCF (Discounted Cash Flow) Calculator Module
Fetches financial data from SEC XBRL filings and calculates company valuation
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple

try:
    from edgartools import Company
    EDGARTOOLS_AVAILABLE = True
except ImportError:
    EDGARTOOLS_AVAILABLE = False
    print("Warning: edgartools not installed. Install with: pip install edgartools")
    print("Falling back to yfinance for financial data.")


class DCFCalculator:
    """Calculates DCF valuation for a given stock ticker"""
    
    def __init__(self, ticker: str):
        """Initialize with a stock ticker"""
        self.ticker = ticker.upper()
        self.stock = yf.Ticker(self.ticker)
        self.info = None
        self.financials = None
        self.cashflow = None
        self.balance_sheet = None
        self.use_sec_data = EDGARTOOLS_AVAILABLE
        
    def fetch_data(self) -> Tuple[bool, str]:
        """Fetch all necessary financial data from SEC filings (or Yahoo Finance as fallback)"""
        try:
            # Always get market data from yfinance (current price, beta, market cap, etc.)
            try:
                self.info = self.stock.info
                if not self.info or len(self.info) == 0:
                    return False, "Could not fetch market data from yfinance"
            except Exception as e:
                return False, f"Error fetching market data: {str(e)}"
            
            # Try to get financial statements from SEC XBRL filings first
            if self.use_sec_data:
                try:
                    company = Company(self.ticker)
                    filings = company.get_filings(form="10-K")
                    
                    if filings and len(filings) > 0:
                        tenk = filings.latest(1).obj()
                        
                        if tenk and hasattr(tenk, 'financials'):
                            financials_obj = tenk.financials
                            
                            # Get financial statements - edgartools returns DataFrames
                            # These may have dates as index or columns, we'll normalize
                            balance_sheet_raw = financials_obj.get_balance_sheet()
                            income_statement_raw = financials_obj.get_income_statement()
                            cashflow_raw = financials_obj.get_cash_flow_statement()
                            
                            # Normalize DataFrames to match yfinance format (dates as columns, accounts as rows)
                            def normalize_dataframe(df):
                                """Convert SEC format to yfinance-like format (dates as columns)"""
                                if df is None or not isinstance(df, pd.DataFrame) or len(df) == 0:
                                    return None
                                
                                # edgartools typically returns: account names as index, dates as columns
                                # This matches yfinance format, so we might not need to transpose
                                # But check if we need to swap
                                
                                # Check if first column looks like dates (e.g., '2023-09-30' format)
                                # or if index looks like account names (strings with spaces/capitalization)
                                if len(df.columns) > 0:
                                    first_col_sample = str(df.columns[0])[:10]
                                    # If columns look like dates or periods, keep as is
                                    if any(x in first_col_sample for x in ['202', '201', 'Q1', 'Q2', 'Q3', 'Q4']):
                                        return df
                                
                                # If index looks like dates, transpose
                                if len(df.index) > 0:
                                    first_idx_sample = str(df.index[0])[:10]
                                    if any(x in first_idx_sample for x in ['202', '201', 'Q1', 'Q2', 'Q3', 'Q4']):
                                        df = df.T
                                
                                # Ensure we have columns
                                if len(df.columns) > 0 and len(df.index) > 0:
                                    return df
                                return None
                            
                            self.balance_sheet = normalize_dataframe(balance_sheet_raw)
                            self.financials = normalize_dataframe(income_statement_raw)
                            self.cashflow = normalize_dataframe(cashflow_raw)
                            
                            # Verify we have essential data
                            if (self.cashflow is not None and isinstance(self.cashflow, pd.DataFrame) and 
                                len(self.cashflow.columns) > 0 and len(self.cashflow.index) > 0):
                                if (self.financials is not None and isinstance(self.financials, pd.DataFrame) and
                                    len(self.financials.columns) > 0 and len(self.financials.index) > 0):
                                    return True, "Success (SEC XBRL data)"
                            
                            # Clear partial data if incomplete
                            if self.cashflow is None or len(self.cashflow.columns) == 0:
                                self.cashflow = None
                            if self.financials is None or len(self.financials.columns) == 0:
                                self.financials = None
                            if self.balance_sheet is None or len(self.balance_sheet.columns) == 0:
                                self.balance_sheet = None
                            
                            # If SEC data didn't work, fall back to yfinance
                            print(f"SEC data incomplete, falling back to yfinance for {self.ticker}")
                        else:
                            print(f"No financials found in 10-K filing, falling back to yfinance for {self.ticker}")
                    else:
                        print(f"No 10-K filings found, falling back to yfinance for {self.ticker}")
                except Exception as sec_error:
                    import traceback
                    print(f"Error fetching SEC data: {sec_error}")
                    traceback.print_exc()
                    print(f"Falling back to yfinance for {self.ticker}")
            
            # Fallback to yfinance for financial statements
            try:
                if self.financials is None or (isinstance(self.financials, pd.DataFrame) and len(self.financials.columns) == 0):
                    self.financials = self.stock.financials
                if self.cashflow is None or (isinstance(self.cashflow, pd.DataFrame) and len(self.cashflow.columns) == 0):
                    self.cashflow = self.stock.cashflow
                if self.balance_sheet is None or (isinstance(self.balance_sheet, pd.DataFrame) and len(self.balance_sheet.columns) == 0):
                    self.balance_sheet = self.stock.balance_sheet
            except Exception as e:
                pass  # Already have error handling below
            
            # Check if we have essential data
            if self.financials is None or self.cashflow is None:
                return False, "Could not fetch financial statements"
            
            if (isinstance(self.financials, pd.DataFrame) and len(self.financials.columns) == 0) or \
               (isinstance(self.cashflow, pd.DataFrame) and len(self.cashflow.columns) == 0):
                return False, "Financial statements are empty"
                
            return True, "Success"
            
        except Exception as e:
            return False, f"Error fetching data: {str(e)}"
    
    def get_free_cash_flow(self, years: int = 5) -> pd.Series:
        """Calculate Free Cash Flow for the last N years"""
        try:
            if self.cashflow is None or len(self.cashflow) == 0:
                return pd.Series()
            
            # Get Operating Cash Flow - try various names (yfinance and SEC XBRL formats)
            operating_cf = None
            operating_cf_keys = [
                'Operating Cash Flow',
                'Total Cash From Operating Activities',
                'NetCashProvidedByUsedInOperatingActivities',  # SEC XBRL tag
                'CashProvidedByUsedInOperatingActivities',
                'CashFromOperatingActivities',
                'OperatingActivitiesCashFlow'
            ]
            
            for key in operating_cf_keys:
                if key in self.cashflow.index:
                    operating_cf = self.cashflow.loc[key]
                    break
            
            # If not found, search by keywords
            if operating_cf is None:
                for idx in self.cashflow.index:
                    idx_str = str(idx).lower()
                    if (('operating' in idx_str or 'cashfromoperating' in idx_str.lower() or 
                         'cashprovidedby' in idx_str.lower()) and 'activity' in idx_str) or \
                       ('netcash' in idx_str and 'operating' in idx_str):
                        operating_cf = self.cashflow.loc[idx]
                        break
                
            # Get Capital Expenditures - try various names
            capex = None
            capex_keys = [
                'Capital Expenditure',
                'Capital Expenditures',
                'PaymentsForAcquisitionOfPropertyPlantAndEquipment',  # SEC XBRL tag
                'PurchaseOfPropertyPlantAndEquipment',
                'CapitalExpenditures',
                'Capex'
            ]
            
            for key in capex_keys:
                if key in self.cashflow.index:
                    capex = self.cashflow.loc[key]
                    break
            
            # If not found, search by keywords
            if capex is None:
                for idx in self.cashflow.index:
                    idx_str = str(idx).lower()
                    if (('capital' in idx_str and 'expenditure' in idx_str) or 
                        ('property' in idx_str and 'plant' in idx_str and 'equipment' in idx_str) or
                        'capex' in idx_str or
                        ('payment' in idx_str and 'acquisition' in idx_str and 'property' in idx_str)):
                        capex = self.cashflow.loc[idx]
                        break
            
            if operating_cf is None or capex is None:
                return pd.Series()
            
            # Calculate FCF = Operating Cash Flow - Capital Expenditures
            # Handle negative capex (it's usually reported as negative in financial statements)
            # In XBRL, capex might be reported as positive (outflow), so take absolute value
            if isinstance(capex, pd.Series):
                # If capex values are all positive, they're outflows - make negative
                if capex.min() >= 0:
                    capex = -abs(capex)
                fcf = operating_cf - capex
            else:
                # Single value
                if capex >= 0:
                    capex = -abs(capex)
                fcf = operating_cf - capex
            
            # Convert to Series if needed
            if not isinstance(fcf, pd.Series):
                fcf = pd.Series([fcf])
            
            # Sort by date (columns) and get most recent years
            # For edgartools, dates are typically in columns
            if isinstance(fcf, pd.Series):
                fcf = fcf.sort_index(ascending=False)
                fcf = fcf.head(years)
            
            return fcf
            
        except Exception as e:
            import traceback
            print(f"Error in get_free_cash_flow: {e}")
            traceback.print_exc()
            return pd.Series()
    
    def calculate_growth_rate(self, method: str = "average") -> float:
        """Calculate growth rate based on historical FCF"""
        fcf = self.get_free_cash_flow(years=5)
        
        if len(fcf) < 2:
            return 0.0
        
        if method == "average":
            # Average year-over-year growth rate
            growth_rates = []
            fcf_values = fcf.values
            
            for i in range(len(fcf_values) - 1):
                if fcf_values[i+1] != 0 and not pd.isna(fcf_values[i+1]):
                    growth = (fcf_values[i] - fcf_values[i+1]) / abs(fcf_values[i+1])
                    growth_rates.append(growth)
            
            if growth_rates:
                return np.mean(growth_rates)
            return 0.0
            
        elif method == "cagr":
            # Compound Annual Growth Rate
            fcf_values = fcf.values
            if len(fcf_values) >= 2 and fcf_values[-1] != 0:
                cagr = ((fcf_values[0] / abs(fcf_values[-1])) ** (1 / (len(fcf_values) - 1))) - 1
                return cagr
            return 0.0
            
        elif method == "recent":
            # Growth rate from last 2 years
            fcf_values = fcf.values
            if len(fcf_values) >= 2 and fcf_values[1] != 0:
                growth = (fcf_values[0] - fcf_values[1]) / abs(fcf_values[1])
                return growth
            return 0.0
        
        return 0.0
    
    def calculate_wacc(self, risk_free_rate: float = 0.04, market_risk_premium: float = 0.06) -> float:
        """Calculate Weighted Average Cost of Capital"""
        try:
            # Get beta
            beta = self.info.get('beta', 1.0) if self.info else 1.0
            if beta is None or pd.isna(beta):
                beta = 1.0
            
            # Get cost of debt (simplified - using interest expense / total debt)
            interest_expense = 0
            total_debt = 0
            
            if self.financials is not None:
                if 'Interest Expense' in self.financials.index:
                    interest_expense = abs(self.financials.loc['Interest Expense'].iloc[0])
            
            if self.balance_sheet is not None:
                if 'Total Debt' in self.balance_sheet.index:
                    total_debt = self.balance_sheet.loc['Total Debt'].iloc[0]
                elif 'Long Term Debt' in self.balance_sheet.index and 'Current Debt' in self.balance_sheet.index:
                    total_debt = (self.balance_sheet.loc['Long Term Debt'].iloc[0] + 
                                 self.balance_sheet.loc['Current Debt'].iloc[0])
            
            cost_of_debt = (interest_expense / total_debt) if total_debt > 0 else 0.05
            
            # Get market cap and equity
            market_cap = self.info.get('marketCap', 0) if self.info else 0
            if market_cap is None or pd.isna(market_cap):
                market_cap = 0
            
            # Calculate weights
            enterprise_value = market_cap + total_debt
            if enterprise_value == 0:
                # Fallback: assume 70% equity, 30% debt
                equity_weight = 0.7
                debt_weight = 0.3
            else:
                equity_weight = market_cap / enterprise_value
                debt_weight = total_debt / enterprise_value
            
            # Cost of equity (CAPM)
            cost_of_equity = risk_free_rate + (beta * market_risk_premium)
            
            # Tax rate (simplified)
            tax_rate = self.info.get('taxRate', 0.25) if self.info else 0.25
            if tax_rate is None or pd.isna(tax_rate):
                tax_rate = 0.25
            
            # WACC calculation
            wacc = (equity_weight * cost_of_equity) + (debt_weight * cost_of_debt * (1 - tax_rate))
            
            return max(wacc, 0.01)  # Ensure positive WACC
            
        except Exception as e:
            # Fallback to default WACC
            return 0.10
    
    def calculate_dcf(self, 
                     growth_rate: Optional[float] = None,
                     growth_method: str = "average",
                     discount_rate: Optional[float] = None,
                     risk_free_rate: float = 0.04,
                     market_risk_premium: float = 0.06,
                     projection_years: int = 10,
                     terminal_growth_rate: float = 0.025) -> Dict:
        """
        Calculate DCF valuation
        
        Returns dictionary with:
        - projected_fcf: projected free cash flows
        - terminal_value: terminal value
        - enterprise_value: total enterprise value
        - equity_value: equity value (enterprise value - net debt)
        - per_share_value: value per share
        """
        # Get current FCF
        fcf_history = self.get_free_cash_flow(years=5)
        if len(fcf_history) == 0:
            return {"error": "Could not calculate FCF from financial data"}
        
        current_fcf = fcf_history.iloc[0]  # Most recent FCF
        
        # Calculate or use provided growth rate
        if growth_rate is None:
            growth_rate = self.calculate_growth_rate(method=growth_method)
        
        # Cap growth rate at reasonable levels
        growth_rate = max(min(growth_rate, 0.50), -0.20)  # Between -20% and 50%
        
        # Calculate or use provided discount rate (WACC)
        if discount_rate is None:
            discount_rate = self.calculate_wacc(risk_free_rate, market_risk_premium)
        
        # Project FCF for next N years
        projected_fcf = []
        for year in range(1, projection_years + 1):
            projected_fcf_year = current_fcf * ((1 + growth_rate) ** year)
            projected_fcf.append({
                'year': year,
                'fcf': projected_fcf_year,
                'discounted_fcf': projected_fcf_year / ((1 + discount_rate) ** year)
            })
        
        # Calculate terminal value using perpetuity growth model
        final_year_fcf = projected_fcf[-1]['fcf']
        terminal_value = (final_year_fcf * (1 + terminal_growth_rate)) / (discount_rate - terminal_growth_rate)
        discounted_terminal_value = terminal_value / ((1 + discount_rate) ** projection_years)
        
        # Enterprise value = sum of discounted FCFs + discounted terminal value
        sum_discounted_fcf = sum([year['discounted_fcf'] for year in projected_fcf])
        enterprise_value = sum_discounted_fcf + discounted_terminal_value
        
        # Calculate equity value = enterprise value - net debt
        net_debt = 0
        if self.balance_sheet is not None:
            total_debt = 0
            if 'Total Debt' in self.balance_sheet.index:
                total_debt = self.balance_sheet.loc['Total Debt'].iloc[0]
            elif 'Long Term Debt' in self.balance_sheet.index and 'Current Debt' in self.balance_sheet.index:
                total_debt = (self.balance_sheet.loc['Long Term Debt'].iloc[0] + 
                             self.balance_sheet.loc['Current Debt'].iloc[0])
            
            cash_and_equivalents = 0
            if 'Cash And Cash Equivalents' in self.balance_sheet.index:
                cash_and_equivalents = self.balance_sheet.loc['Cash And Cash Equivalents'].iloc[0]
            
            net_debt = total_debt - cash_and_equivalents
        
        equity_value = enterprise_value - net_debt
        
        # Value per share
        shares_outstanding = self.info.get('sharesOutstanding', 0) if self.info else 0
        if shares_outstanding is None or shares_outstanding == 0:
            shares_outstanding = 1  # Fallback
        
        per_share_value = equity_value / shares_outstanding
        
        # Current stock price for comparison
        current_price = self.info.get('currentPrice', 0) if self.info else 0
        if current_price is None:
            current_price = 0
        
        return {
            'projected_fcf': projected_fcf,
            'terminal_value': terminal_value,
            'discounted_terminal_value': discounted_terminal_value,
            'enterprise_value': enterprise_value,
            'net_debt': net_debt,
            'equity_value': equity_value,
            'per_share_value': per_share_value,
            'current_price': current_price,
            'growth_rate': growth_rate,
            'discount_rate': discount_rate,
            'terminal_growth_rate': terminal_growth_rate,
            'current_fcf': current_fcf,
            'shares_outstanding': shares_outstanding,
            'risk_free_rate': risk_free_rate,
            'market_risk_premium': market_risk_premium
        }

