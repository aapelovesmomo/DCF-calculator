"""
DCF Calculator Desktop App
Clean PyQt interface for Discounted Cash Flow valuation
"""

import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                                QComboBox, QDoubleSpinBox, QTextEdit, QGroupBox,
                                QMessageBox, QProgressBar, QTableWidget, 
                                QTableWidgetItem, QHeaderView, QScrollArea,
                                QGridLayout, QTabWidget, QSizePolicy, QDialog)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor, QPen, QBrush
from dcf_calculator import DCFCalculator
import locale


class DCFWorker(QThread):
    """Worker thread to calculate DCF without freezing UI"""
    finished = Signal(dict)  # result dict with calculator stored inside
    error = Signal(str)
    
    def __init__(self, ticker, growth_method, growth_rate, discount_rate, risk_free_rate, 
                 market_risk_premium, terminal_growth_rate):
        super().__init__()
        self.ticker = ticker
        self.growth_method = growth_method
        self.growth_rate = growth_rate
        self.discount_rate = discount_rate
        self.risk_free_rate = risk_free_rate
        self.market_risk_premium = market_risk_premium
        self.terminal_growth_rate = terminal_growth_rate
    
    def run(self):
        try:
            calc = DCFCalculator(self.ticker)
            success, message = calc.fetch_data()
            
            if not success:
                self.error.emit(message)
                return
            
            # Use manual growth rate if provided, otherwise use method
            growth_rate_input = self.growth_rate if self.growth_method == "manual" else None
            growth_method_input = None if self.growth_method == "manual" else self.growth_method
            
            result = calc.calculate_dcf(
                growth_rate=growth_rate_input,
                growth_method=growth_method_input,
                discount_rate=self.discount_rate if self.discount_rate > 0 else None,
                risk_free_rate=self.risk_free_rate,
                market_risk_premium=self.market_risk_premium,
                projection_years=10,
                terminal_growth_rate=self.terminal_growth_rate
            )
            
            if "error" in result:
                self.error.emit(result["error"])
            else:
                # Store calculator in result dict
                result['_calculator'] = calc
                self.finished.emit(result)
                
        except Exception as e:
            import traceback
            error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
            self.error.emit(error_msg)


class DetailedBreakdownDialog(QDialog):
    """Popup window for detailed breakdown and educational content"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📚 Detailed Breakdown & Educational Guide")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        self.setModal(True)  # Make it modal
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(main_layout)
        
        # Tab widget for different sections
        self.detail_tabs = QTabWidget()
        self.detail_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Tab 1: Raw Financial Data
        self.raw_data_tab = QWidget()
        raw_data_layout = QVBoxLayout()
        raw_data_layout.setContentsMargins(5, 5, 5, 5)
        raw_data_scroll = QScrollArea()
        raw_data_scroll.setWidgetResizable(True)
        raw_data_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        raw_data_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        raw_data_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        raw_data_container = QWidget()
        raw_data_container_layout = QVBoxLayout()
        raw_data_container_layout.setSpacing(15)
        raw_data_container_layout.setContentsMargins(10, 10, 10, 10)
        
        # Financial statements tables
        summary_font = QFont()
        summary_font.setPointSize(11)
        summary_font.setBold(True)
        
        # Cash Flow Statement
        cashflow_label = QLabel("Cash Flow Statement (Key Items)")
        cashflow_label.setFont(summary_font)
        raw_data_container_layout.addWidget(cashflow_label)
        self.cashflow_table = QTableWidget()
        self.cashflow_table.setAlternatingRowColors(True)
        self.cashflow_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cashflow_table.setMinimumHeight(150)
        self.cashflow_table.horizontalHeader().setStretchLastSection(False)
        self.cashflow_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        raw_data_container_layout.addWidget(self.cashflow_table)
        
        # Balance Sheet
        balance_label = QLabel("Balance Sheet (Key Items)")
        balance_label.setFont(summary_font)
        raw_data_container_layout.addWidget(balance_label)
        self.balance_sheet_table = QTableWidget()
        self.balance_sheet_table.setAlternatingRowColors(True)
        self.balance_sheet_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.balance_sheet_table.setMinimumHeight(150)
        self.balance_sheet_table.horizontalHeader().setStretchLastSection(False)
        self.balance_sheet_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        raw_data_container_layout.addWidget(self.balance_sheet_table)
        
        # Income Statement
        income_label = QLabel("Income Statement (Key Items)")
        income_label.setFont(summary_font)
        raw_data_container_layout.addWidget(income_label)
        self.income_table = QTableWidget()
        self.income_table.setAlternatingRowColors(True)
        self.income_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.income_table.setMinimumHeight(150)
        self.income_table.horizontalHeader().setStretchLastSection(False)
        self.income_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        raw_data_container_layout.addWidget(self.income_table)
        
        raw_data_container.setLayout(raw_data_container_layout)
        raw_data_scroll.setWidget(raw_data_container)
        raw_data_layout.addWidget(raw_data_scroll)
        self.raw_data_tab.setLayout(raw_data_layout)
        self.detail_tabs.addTab(self.raw_data_tab, "Raw Financial Data")
        
        # Tab 2: FCF Calculation Breakdown
        self.fcf_tab = QWidget()
        fcf_layout = QVBoxLayout()
        fcf_layout.setContentsMargins(5, 5, 5, 5)
        fcf_scroll = QScrollArea()
        fcf_scroll.setWidgetResizable(True)
        fcf_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        fcf_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        fcf_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        fcf_container = QWidget()
        fcf_container_layout = QVBoxLayout()
        
        fcf_explanation = QLabel(
            "Free Cash Flow (FCF) Calculation:\n\n"
            "FCF = Operating Cash Flow - Capital Expenditures\n\n"
            "Operating Cash Flow: Cash generated from core business operations\n"
            "Capital Expenditures: Cash spent on long-term assets (PP&E)\n\n"
            "FCF represents the cash available to shareholders after reinvesting in the business."
        )
        fcf_explanation.setWordWrap(True)
        fcf_explanation.setFont(QFont("", 10))
        fcf_container_layout.addWidget(fcf_explanation)
        
        self.fcf_calc_table = QTableWidget()
        self.fcf_calc_table.setAlternatingRowColors(True)
        self.fcf_calc_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.fcf_calc_table.setMinimumHeight(200)
        self.fcf_calc_table.horizontalHeader().setStretchLastSection(False)
        self.fcf_calc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.fcf_calc_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.fcf_calc_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.fcf_calc_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.fcf_calc_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        fcf_container_layout.addWidget(self.fcf_calc_table)
        
        fcf_container.setLayout(fcf_container_layout)
        fcf_scroll.setWidget(fcf_container)
        fcf_layout.addWidget(fcf_scroll)
        self.fcf_tab.setLayout(fcf_layout)
        self.detail_tabs.addTab(self.fcf_tab, "FCF Calculation")
        
        # Tab 3: Growth Rate Calculation
        self.growth_tab = QWidget()
        growth_layout = QVBoxLayout()
        growth_layout.setContentsMargins(5, 5, 5, 5)
        growth_scroll = QScrollArea()
        growth_scroll.setWidgetResizable(True)
        growth_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        growth_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        growth_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        growth_container = QWidget()
        growth_container_layout = QVBoxLayout()
        
        growth_explanation = QLabel(
            "Growth Rate Calculation:\n\n"
            "The growth rate estimates how fast the company's free cash flow will grow.\n"
            "Different methods provide different perspectives:\n\n"
            "• Average: Mean of year-over-year growth rates (most stable)\n"
            "• CAGR: Compound Annual Growth Rate over the period (smoother)\n"
            "• Recent: Latest year-over-year growth (most current)\n\n"
            "A high growth rate increases valuation, but should be realistic."
        )
        growth_explanation.setWordWrap(True)
        growth_explanation.setFont(QFont("", 10))
        growth_container_layout.addWidget(growth_explanation)
        
        self.growth_calc_table = QTableWidget()
        self.growth_calc_table.setAlternatingRowColors(True)
        self.growth_calc_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.growth_calc_table.setMinimumHeight(200)
        self.growth_calc_table.horizontalHeader().setStretchLastSection(False)
        self.growth_calc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.growth_calc_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.growth_calc_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.growth_calc_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.growth_calc_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        growth_container_layout.addWidget(self.growth_calc_table)
        
        growth_container.setLayout(growth_container_layout)
        growth_scroll.setWidget(growth_container)
        growth_layout.addWidget(growth_scroll)
        self.growth_tab.setLayout(growth_layout)
        self.detail_tabs.addTab(self.growth_tab, "Growth Rate")
        
        # Tab 4: WACC Calculation
        self.wacc_tab = QWidget()
        wacc_layout = QVBoxLayout()
        wacc_layout.setContentsMargins(5, 5, 5, 5)
        wacc_scroll = QScrollArea()
        wacc_scroll.setWidgetResizable(True)
        wacc_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        wacc_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        wacc_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        wacc_container = QWidget()
        wacc_container_layout = QVBoxLayout()
        
        wacc_explanation = QLabel(
            "Weighted Average Cost of Capital (WACC) Calculation:\n\n"
            "WACC = (E/V × Re) + (D/V × Rd × (1 - Tc))\n\n"
            "Where:\n"
            "• E = Market value of equity\n"
            "• D = Market value of debt\n"
            "• V = E + D (Total capital)\n"
            "• Re = Cost of equity (using CAPM: Rf + β × (Rm - Rf))\n"
            "• Rd = Cost of debt (interest expense / total debt)\n"
            "• Tc = Tax rate\n\n"
            "WACC represents the average rate a company pays to finance its assets."
        )
        wacc_explanation.setWordWrap(True)
        wacc_explanation.setFont(QFont("", 10))
        wacc_container_layout.addWidget(wacc_explanation)
        
        self.wacc_calc_table = QTableWidget()
        self.wacc_calc_table.setAlternatingRowColors(True)
        self.wacc_calc_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.wacc_calc_table.setMinimumHeight(200)
        self.wacc_calc_table.horizontalHeader().setStretchLastSection(True)
        self.wacc_calc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.wacc_calc_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        wacc_container_layout.addWidget(self.wacc_calc_table)
        
        wacc_container.setLayout(wacc_container_layout)
        wacc_scroll.setWidget(wacc_container)
        wacc_layout.addWidget(wacc_scroll)
        self.wacc_tab.setLayout(wacc_layout)
        self.detail_tabs.addTab(self.wacc_tab, "WACC Calculation")
        
        # Tab 5: DCF Step-by-Step
        self.dcf_steps_tab = QWidget()
        dcf_steps_layout = QVBoxLayout()
        dcf_steps_layout.setContentsMargins(5, 5, 5, 5)
        dcf_steps_scroll = QScrollArea()
        dcf_steps_scroll.setWidgetResizable(True)
        dcf_steps_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        dcf_steps_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        dcf_steps_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        dcf_steps_container = QWidget()
        dcf_steps_container_layout = QVBoxLayout()
        
        dcf_explanation = QLabel(
            "DCF Calculation Steps:\n\n"
            "1. Project Future FCFs: Apply growth rate to current FCF for 10 years\n"
            "2. Discount to Present: Divide each year's FCF by (1 + WACC)^year\n"
            "3. Calculate Terminal Value: Use perpetuity growth model\n"
            "   Terminal Value = (Final Year FCF × (1 + g)) / (WACC - g)\n"
            "4. Discount Terminal Value: Bring back to present value\n"
            "5. Sum Everything: Enterprise Value = Sum of Discounted FCFs + Discounted Terminal Value\n"
            "6. Calculate Equity Value: Enterprise Value - Net Debt\n"
            "7. Value Per Share: Equity Value / Shares Outstanding"
        )
        dcf_explanation.setWordWrap(True)
        dcf_explanation.setFont(QFont("", 10))
        dcf_steps_container_layout.addWidget(dcf_explanation)
        
        self.dcf_steps_table = QTableWidget()
        self.dcf_steps_table.setAlternatingRowColors(True)
        self.dcf_steps_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.dcf_steps_table.setMinimumHeight(300)
        self.dcf_steps_table.horizontalHeader().setStretchLastSection(False)
        self.dcf_steps_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.dcf_steps_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.dcf_steps_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.dcf_steps_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        dcf_steps_container_layout.addWidget(self.dcf_steps_table)
        
        dcf_steps_container.setLayout(dcf_steps_container_layout)
        dcf_steps_scroll.setWidget(dcf_steps_container)
        dcf_steps_layout.addWidget(dcf_steps_scroll)
        self.dcf_steps_tab.setLayout(dcf_steps_layout)
        self.detail_tabs.addTab(self.dcf_steps_tab, "DCF Steps")
        
        # Tab 6: All Assumptions
        self.assumptions_tab = QWidget()
        assumptions_detailed_layout = QVBoxLayout()
        assumptions_detailed_layout.setContentsMargins(5, 5, 5, 5)
        assumptions_scroll = QScrollArea()
        assumptions_scroll.setWidgetResizable(True)
        assumptions_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        assumptions_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        assumptions_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        assumptions_container = QWidget()
        assumptions_container_layout = QVBoxLayout()
        
        assumptions_explanation = QLabel(
            "All Assumptions Used in This Calculation:\n\n"
            "Understanding assumptions is crucial. Small changes can significantly impact valuation."
        )
        assumptions_explanation.setWordWrap(True)
        assumptions_explanation.setFont(QFont("", 10))
        assumptions_container_layout.addWidget(assumptions_explanation)
        
        self.assumptions_table = QTableWidget()
        self.assumptions_table.setAlternatingRowColors(True)
        self.assumptions_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.assumptions_table.setMinimumHeight(200)
        self.assumptions_table.horizontalHeader().setStretchLastSection(True)
        self.assumptions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        assumptions_container_layout.addWidget(self.assumptions_table)
        
        assumptions_container.setLayout(assumptions_container_layout)
        assumptions_scroll.setWidget(assumptions_container)
        assumptions_detailed_layout.addWidget(assumptions_scroll)
        self.assumptions_tab.setLayout(assumptions_detailed_layout)
        self.detail_tabs.addTab(self.assumptions_tab, "All Assumptions")
        
        main_layout.addWidget(self.detail_tabs)
        
        # Close button at bottom
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumHeight(35)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)


class DCFApp(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DCF Calculator")
        # Make window resizable with a larger default size
        self.setMinimumSize(1000, 800)
        self.resize(1200, 900)
        self.setGeometry(100, 100, 1200, 900)
        
        # Set up locale for formatting
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except:
            pass
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Title
        title = QLabel("Discounted Cash Flow Calculator")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Ticker input - Make it prominent at the top
        ticker_group = QGroupBox("Enter Company Ticker")
        ticker_layout = QHBoxLayout()
        ticker_label = QLabel("Ticker Symbol:")
        ticker_label_font = QFont()
        ticker_label_font.setPointSize(11)
        ticker_label_font.setBold(True)
        ticker_label.setFont(ticker_label_font)
        ticker_layout.addWidget(ticker_label)
        self.ticker_input = QLineEdit()
        self.ticker_input.setPlaceholderText("e.g., AAPL, MSFT, GOOGL")
        self.ticker_input.setMinimumWidth(200)
        self.ticker_input.setMaximumWidth(250)
        ticker_font = QFont()
        ticker_font.setPointSize(12)
        self.ticker_input.setFont(ticker_font)
        ticker_layout.addWidget(self.ticker_input)
        ticker_layout.addStretch()
        ticker_group.setLayout(ticker_layout)
        main_layout.addWidget(ticker_group)
        
        # Input section (for future use)
        input_group = QGroupBox("Settings")
        input_layout = QVBoxLayout()
        
        # Assumptions section
        assumptions_group = QGroupBox("Assumptions")
        assumptions_layout = QVBoxLayout()
        
        # Growth rate method
        growth_layout = QHBoxLayout()
        growth_layout.addWidget(QLabel("Growth Rate Method:"))
        self.growth_method = QComboBox()
        self.growth_method.addItems([
            "Average (Last 5 Years)",
            "CAGR (5 Year)",
            "Recent (Last 2 Years)",
            "Manual Entry"
        ])
        self.growth_method.currentIndexChanged.connect(self.on_growth_method_changed)
        growth_layout.addWidget(self.growth_method)
        growth_layout.addStretch()
        assumptions_layout.addLayout(growth_layout)
        
        # Manual growth rate (hidden initially)
        manual_growth_layout = QHBoxLayout()
        manual_growth_layout.addWidget(QLabel("Manual Growth Rate (%):"))
        self.manual_growth_rate = QDoubleSpinBox()
        self.manual_growth_rate.setRange(-20.0, 50.0)
        self.manual_growth_rate.setValue(5.0)
        self.manual_growth_rate.setSuffix("%")
        self.manual_growth_rate.setDecimals(2)
        self.manual_growth_rate.setVisible(False)
        manual_growth_layout.addWidget(self.manual_growth_rate)
        manual_growth_layout.addStretch()
        assumptions_layout.addLayout(manual_growth_layout)
        
        # Discount rate
        discount_layout = QHBoxLayout()
        discount_layout.addWidget(QLabel("Discount Rate (WACC):"))
        self.discount_rate = QDoubleSpinBox()
        self.discount_rate.setRange(1.0, 30.0)
        self.discount_rate.setValue(10.0)
        self.discount_rate.setSuffix("%")
        self.discount_rate.setDecimals(2)
        self.discount_rate.setSpecialValueText("Auto (Calculate)")
        discount_layout.addWidget(self.discount_rate)
        discount_layout.addWidget(QLabel("or Auto"))
        self.auto_wacc = QComboBox()
        self.auto_wacc.addItems(["Auto Calculate", "Manual"])
        self.auto_wacc.currentIndexChanged.connect(self.on_wacc_method_changed)
        discount_layout.addWidget(self.auto_wacc)
        discount_layout.addStretch()
        assumptions_layout.addLayout(discount_layout)
        
        # Risk-free rate (for auto WACC)
        risk_free_layout = QHBoxLayout()
        risk_free_layout.addWidget(QLabel("Risk-Free Rate:"))
        self.risk_free_rate = QDoubleSpinBox()
        self.risk_free_rate.setRange(0.0, 10.0)
        self.risk_free_rate.setValue(4.0)
        self.risk_free_rate.setSuffix("%")
        self.risk_free_rate.setDecimals(2)
        risk_free_layout.addWidget(self.risk_free_rate)
        risk_free_layout.addStretch()
        assumptions_layout.addLayout(risk_free_layout)
        
        # Market risk premium
        mrp_layout = QHBoxLayout()
        mrp_layout.addWidget(QLabel("Market Risk Premium:"))
        self.market_risk_premium = QDoubleSpinBox()
        self.market_risk_premium.setRange(0.0, 15.0)
        self.market_risk_premium.setValue(6.0)
        self.market_risk_premium.setSuffix("%")
        self.market_risk_premium.setDecimals(2)
        mrp_layout.addWidget(self.market_risk_premium)
        mrp_layout.addStretch()
        assumptions_layout.addLayout(mrp_layout)
        
        # Terminal growth rate
        terminal_layout = QHBoxLayout()
        terminal_layout.addWidget(QLabel("Terminal Growth Rate:"))
        self.terminal_growth_rate = QDoubleSpinBox()
        self.terminal_growth_rate.setRange(0.0, 5.0)
        self.terminal_growth_rate.setValue(2.5)
        self.terminal_growth_rate.setSuffix("%")
        self.terminal_growth_rate.setDecimals(2)
        terminal_layout.addWidget(self.terminal_growth_rate)
        terminal_layout.addStretch()
        assumptions_layout.addLayout(terminal_layout)
        
        assumptions_group.setLayout(assumptions_layout)
        
        # Calculate button
        self.calculate_btn = QPushButton("Calculate DCF")
        self.calculate_btn.setMinimumHeight(40)
        self.calculate_btn.clicked.connect(self.calculate_dcf)
        calculate_font = QFont()
        calculate_font.setPointSize(12)
        calculate_font.setBold(True)
        self.calculate_btn.setFont(calculate_font)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Results section with scrollable area
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        
        # Create scroll area for results - make it flexible
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        results_container = QWidget()
        results_container_layout = QVBoxLayout()
        results_container_layout.setSpacing(15)
        results_container_layout.setContentsMargins(5, 5, 5, 5)
        results_container.setLayout(results_container_layout)
        
        # Summary metrics grid
        summary_label = QLabel("Summary Metrics")
        summary_font = QFont()
        summary_font.setPointSize(11)
        summary_font.setBold(True)
        summary_label.setFont(summary_font)
        results_container_layout.addWidget(summary_label)
        
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(2)
        self.summary_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.summary_table.horizontalHeader().setStretchLastSection(True)
        self.summary_table.horizontalHeader().setVisible(True)
        self.summary_table.verticalHeader().setVisible(False)
        self.summary_table.setMinimumHeight(150)
        self.summary_table.setAlternatingRowColors(True)
        self.summary_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.summary_table.setSelectionBehavior(QTableWidget.SelectRows)
        results_container_layout.addWidget(self.summary_table)
        
        # Projected cash flows table
        projections_label = QLabel("10-Year Projected Free Cash Flows")
        projections_label.setFont(summary_font)
        results_container_layout.addWidget(projections_label)
        
        self.projections_table = QTableWidget()
        self.projections_table.setColumnCount(4)
        self.projections_table.setHorizontalHeaderLabels(["Year", "FCF", "Discount Factor", "Discounted FCF"])
        self.projections_table.horizontalHeader().setStretchLastSection(True)
        self.projections_table.horizontalHeader().setVisible(True)
        self.projections_table.verticalHeader().setVisible(False)
        header = self.projections_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.projections_table.setMinimumHeight(250)
        self.projections_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.projections_table.setAlternatingRowColors(True)
        self.projections_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.projections_table.setSelectionBehavior(QTableWidget.SelectRows)
        results_container_layout.addWidget(self.projections_table)
        
        # Valuation comparison
        valuation_label = QLabel("Valuation & Comparison")
        valuation_label.setFont(summary_font)
        results_container_layout.addWidget(valuation_label)
        
        self.valuation_table = QTableWidget()
        self.valuation_table.setColumnCount(2)
        self.valuation_table.setHorizontalHeaderLabels(["Item", "Value"])
        self.valuation_table.horizontalHeader().setStretchLastSection(True)
        self.valuation_table.horizontalHeader().setVisible(True)
        self.valuation_table.verticalHeader().setVisible(False)
        self.valuation_table.setMinimumHeight(120)
        self.valuation_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.valuation_table.setAlternatingRowColors(True)
        self.valuation_table.setEditTriggers(QTableWidget.NoEditTriggers)
        results_container_layout.addWidget(self.valuation_table)
        
        scroll_area.setWidget(results_container)
        results_layout.addWidget(scroll_area)
        
        # Add spacer before detailed breakdown section
        results_layout.addSpacing(10)
        
        # Detailed breakdown button - opens popup window
        self.detailed_breakdown_btn = QPushButton("📊 Show Detailed Breakdown & Calculations")
        self.detailed_breakdown_btn.clicked.connect(self.open_detailed_breakdown)
        self.detailed_breakdown_btn.setVisible(False)  # Only show after calculation
        self.detailed_breakdown_btn.setMinimumHeight(40)
        self.detailed_breakdown_btn.setMaximumHeight(40)
        btn_font = QFont()
        btn_font.setPointSize(11)
        btn_font.setBold(True)
        self.detailed_breakdown_btn.setFont(btn_font)
        results_layout.addWidget(self.detailed_breakdown_btn)
        
        results_group.setLayout(results_layout)
        
        # Assemble main layout
        main_layout.addWidget(assumptions_group)
        main_layout.addWidget(self.calculate_btn)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(results_group)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        main_layout.addWidget(close_btn)
        
        # Initialize state
        self.on_wacc_method_changed(0)
    
    def open_detailed_breakdown(self):
        """Open detailed breakdown in a popup window"""
        if not hasattr(self, 'calculator') or not hasattr(self, 'result_data'):
            QMessageBox.warning(self, "No Data", "Please calculate DCF first")
            return
        
        # Create dialog
        try:
            dialog = DetailedBreakdownDialog(self)
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Error", f"Failed to create dialog:\n{str(e)}")
            return
        
        # Populate the dialog's tables
        try:
            self.populate_detailed_breakdown(self.result_data, self.calculator, dialog)
        except Exception as e:
            import traceback
            # Still show the dialog even if population failed
            QMessageBox.warning(self, "Warning", f"Some data may be incomplete:\n{str(e)}")
        
        # Show dialog (modal)
        dialog.exec()
    
    def on_growth_method_changed(self, index):
        """Show/hide manual growth rate input"""
        self.manual_growth_rate.setVisible(index == 3)  # "Manual Entry"
    
    def on_wacc_method_changed(self, index):
        """Enable/disable discount rate input based on auto/manual"""
        is_manual = (index == 1)
        self.discount_rate.setEnabled(is_manual)
        self.risk_free_rate.setEnabled(not is_manual)
        self.market_risk_premium.setEnabled(not is_manual)
    
    def calculate_dcf(self):
        """Trigger DCF calculation"""
        ticker = self.ticker_input.text().strip().upper()
        
        if not ticker:
            QMessageBox.warning(self, "Error", "Please enter a company ticker")
            return
        
        # Disable calculate button and show progress
        self.calculate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        # Clear main result tables
        self.summary_table.setRowCount(0)
        self.projections_table.setRowCount(0)
        self.valuation_table.setRowCount(0)
        
        # Hide detailed breakdown button
        self.detailed_breakdown_btn.setVisible(False)
        
        # Get inputs
        growth_method_map = {
            0: "average",
            1: "cagr",
            2: "recent",
            3: "manual"
        }
        growth_method = growth_method_map[self.growth_method.currentIndex()]
        
        # Manual growth rate if selected
        manual_growth = None
        if growth_method == "manual":
            manual_growth = self.manual_growth_rate.value() / 100.0
        
        # Discount rate
        discount_rate = 0.0
        if self.auto_wacc.currentIndex() == 1:  # Manual
            discount_rate = self.discount_rate.value() / 100.0
        
        # Create and start worker thread
        self.worker = DCFWorker(
            ticker=ticker,
            growth_method=growth_method,
            growth_rate=manual_growth,
            discount_rate=discount_rate,
            risk_free_rate=self.risk_free_rate.value() / 100.0,
            market_risk_premium=self.market_risk_premium.value() / 100.0,
            terminal_growth_rate=self.terminal_growth_rate.value() / 100.0
        )
        
        self.worker.finished.connect(self.on_calculation_complete)
        self.worker.error.connect(self.on_calculation_error)
        self.worker.start()
    
    def format_currency(self, value):
        """Format number as currency"""
        try:
            return locale.currency(value, grouping=True)
        except:
            return f"${value:,.2f}"
    
    def format_currency_table(self, value):
        """Format number as currency for table display"""
        import math
        import pandas as pd
        
        # Check for NaN or None values
        if value is None:
            return "N/A"
        if pd.isna(value) if hasattr(pd, 'isna') else (value != value):
            return "N/A"
        if isinstance(value, (int, float)) and (math.isnan(value) or math.isinf(value)):
            return "N/A"
        
        try:
            # Ensure value is numeric
            value = float(value)
            formatted = locale.currency(value, grouping=True, symbol=True)
            return formatted
        except (ValueError, TypeError, OverflowError):
            return "N/A"
    
    def on_calculation_complete(self, result):
        """Display DCF calculation results in tables"""
        try:
            self.progress_bar.setVisible(False)
            self.calculate_btn.setEnabled(True)
            self.detailed_breakdown_btn.setVisible(True)
            
            # Extract calculator from result
            calc = result.pop('_calculator', None)
            if calc is None:
                QMessageBox.critical(self, "Error", "Calculator object not found in results")
                return
            
            # Store calculator for detailed view
            self.calculator = calc
            self.result_data = result
            
            # Data is stored and will be populated when dialog opens
            
            # Populate Summary Metrics Table
            summary_data = [
                ("Company", self.ticker_input.text().upper()),
                ("Current FCF", self.format_currency_table(result['current_fcf'])),
                ("Growth Rate", f"{result['growth_rate']*100:.2f}%"),
                ("Discount Rate (WACC)", f"{result['discount_rate']*100:.2f}%"),
                ("Terminal Growth Rate", f"{result['terminal_growth_rate']*100:.2f}%"),
                ("Shares Outstanding", f"{result['shares_outstanding']:,.0f}"),
            ]
            
            self.summary_table.setRowCount(len(summary_data))
            for row, (metric, value) in enumerate(summary_data):
                metric_item = QTableWidgetItem(metric)
                metric_item.setFont(QFont("", 9, QFont.Bold))
                self.summary_table.setItem(row, 0, metric_item)
                self.summary_table.setItem(row, 1, QTableWidgetItem(str(value)))
            
            # Populate Projected Cash Flows Table
            self.projections_table.setRowCount(len(result['projected_fcf']) + 1)  # +1 for total row
            
            import math
            for row, year_data in enumerate(result['projected_fcf']):
                year = year_data.get('year', row + 1)
                fcf = year_data.get('fcf', 0)
                discount_rate = result.get('discount_rate', 0.1)
                
                # Calculate discount factor safely
                if discount_rate > 0 and not math.isnan(discount_rate):
                    discount_factor = 1 / ((1 + discount_rate) ** year)
                else:
                    discount_factor = 1.0
                
                discounted_fcf = year_data.get('discounted_fcf', 0)
                
                # Check for NaN values
                if math.isnan(fcf) or math.isnan(discounted_fcf) or math.isnan(discount_factor):
                    self.projections_table.setItem(row, 0, QTableWidgetItem(f"Year {year}"))
                    self.projections_table.setItem(row, 1, QTableWidgetItem("N/A"))
                    self.projections_table.setItem(row, 2, QTableWidgetItem("N/A"))
                    self.projections_table.setItem(row, 3, QTableWidgetItem("N/A"))
                else:
                    self.projections_table.setItem(row, 0, QTableWidgetItem(f"Year {year}"))
                    self.projections_table.setItem(row, 1, QTableWidgetItem(self.format_currency_table(fcf)))
                    self.projections_table.setItem(row, 2, QTableWidgetItem(f"{discount_factor:.4f}"))
                    self.projections_table.setItem(row, 3, QTableWidgetItem(self.format_currency_table(discounted_fcf)))
                    
                    # Right-align currency columns
                    for col in [1, 3]:
                        item = self.projections_table.item(row, col)
                        if item:
                            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # Add total row
            total_row = len(result['projected_fcf'])
            sum_discounted_fcf = sum([
                year.get('discounted_fcf', 0) for year in result['projected_fcf']
                if not math.isnan(year.get('discounted_fcf', 0))
            ])
            
            # Use darker background for better visibility
            total_bg_color = QColor(170, 170, 170)  # Darker gray - more visible than white
            
            total_item = QTableWidgetItem("Total (Discounted FCF)")
            total_item.setFont(QFont("", 9, QFont.Bold))
            total_item.setBackground(QBrush(total_bg_color))
            total_item.setForeground(QBrush(QColor(0, 0, 0)))  # Black text
            self.projections_table.setItem(total_row, 0, total_item)
            
            empty_item = QTableWidgetItem("")
            empty_item.setBackground(QBrush(total_bg_color))
            self.projections_table.setItem(total_row, 1, empty_item)
            
            empty_item2 = QTableWidgetItem("")
            empty_item2.setBackground(QBrush(total_bg_color))
            self.projections_table.setItem(total_row, 2, empty_item2)
            
            total_value = QTableWidgetItem(self.format_currency_table(sum_discounted_fcf))
            total_value.setFont(QFont("", 9, QFont.Bold))
            total_value.setBackground(QBrush(total_bg_color))
            total_value.setForeground(QBrush(QColor(0, 0, 0)))  # Black text
            total_value.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.projections_table.setItem(total_row, 3, total_value)
            
            # Populate Valuation Table
            valuation_data = [
                ("Terminal Value", self.format_currency_table(result['terminal_value'])),
                ("Discounted Terminal Value", self.format_currency_table(result['discounted_terminal_value'])),
                ("Enterprise Value", self.format_currency_table(result['enterprise_value'])),
                ("Net Debt", self.format_currency_table(result['net_debt'])),
                ("Equity Value", self.format_currency_table(result['equity_value'])),
                ("Value Per Share", self.format_currency_table(result['per_share_value'])),
            ]
            
            # Add current price and comparison
            valuation_data.append(("", ""))  # Separator
            valuation_data.append(("Current Market Price", self.format_currency_table(result['current_price'])))
            
            # Check for valid current price and per share value
            current_price = result.get('current_price', 0) or 0
            per_share_value = result.get('per_share_value', 0) or 0
            
            import math
            if current_price > 0 and not math.isnan(current_price) and not math.isnan(per_share_value):
                premium = ((per_share_value - current_price) / current_price) * 100
                if not math.isnan(premium):
                    valuation_data.append(("Premium/(Discount)", f"{premium:+.2f}%"))
                    
                    if premium > 0:
                        valuation_data.append(("Assessment", f"UNDERVALUED by {premium:.2f}%"))
                        assessment_color = QColor(200, 255, 200)  # Light green
                    else:
                        valuation_data.append(("Assessment", f"OVERVALUED by {abs(premium):.2f}%"))
                        assessment_color = QColor(255, 200, 200)  # Light red
                else:
                    valuation_data.append(("Premium/(Discount)", "N/A"))
                    valuation_data.append(("Assessment", "Calculation error"))
                    assessment_color = QColor(230, 230, 230)
            else:
                valuation_data.append(("Premium/(Discount)", "N/A"))
                valuation_data.append(("Assessment", "Price data unavailable"))
                assessment_color = QColor(230, 230, 230)
            
            self.valuation_table.setRowCount(len(valuation_data))
            assessment_row = None
            for row, (item, value) in enumerate(valuation_data):
                item_widget = QTableWidgetItem(item)
                if item:
                    item_widget.setFont(QFont("", 9, QFont.Bold if row < len(valuation_data) - 3 else QFont.Normal))
                self.valuation_table.setItem(row, 0, item_widget)
                
                value_item = QTableWidgetItem(str(value))
                if value and "$" in str(value):
                    value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if "UNDERVALUED" in str(value) or "OVERVALUED" in str(value):
                    # Use darker background for better visibility
                    if assessment_color == QColor(200, 255, 200):  # Light green
                        darker_color = QColor(120, 180, 120)  # Darker green - more visible
                    elif assessment_color == QColor(255, 200, 200):  # Light red
                        darker_color = QColor(180, 120, 120)  # Darker red - more visible
                    else:
                        darker_color = QColor(170, 170, 170)  # Gray
                    value_item.setBackground(QBrush(darker_color))
                    value_item.setForeground(QBrush(QColor(0, 0, 0)))  # Black text for visibility
                    
                    # Also set darker background on label column
                    if item_widget:
                        item_widget.setBackground(QBrush(darker_color))
                        item_widget.setForeground(QBrush(QColor(0, 0, 0)))
                    
                    assessment_row = row
                self.valuation_table.setItem(row, 1, value_item)
                
        except Exception as e:
            import traceback
            error_msg = f"Error displaying results: {str(e)}"
            QMessageBox.critical(self, "Display Error", f"Unable to display results:\n\n{error_msg}")
    
    def populate_detailed_breakdown(self, result, calc, dialog):
        """Populate all detailed breakdown tables with educational content"""
        import pandas as pd
        
        # Wrap each population in try-except so one failure doesn't break others
        try:
            self.populate_raw_financial_data(calc, dialog)
        except Exception as e:
            import traceback
            print(f"Error populating raw financial data: {e}")
            traceback.print_exc()
        
        try:
            self.populate_fcf_calculation(calc, dialog)
        except Exception as e:
            import traceback
            print(f"Error populating FCF calculation: {e}")
            traceback.print_exc()
        
        try:
            self.populate_growth_calculation(calc, result, dialog)
        except Exception as e:
            import traceback
            print(f"Error populating growth calculation: {e}")
            traceback.print_exc()
        
        try:
            self.populate_wacc_calculation(calc, result, dialog)
        except Exception as e:
            import traceback
            print(f"Error populating WACC calculation: {e}")
            traceback.print_exc()
        
        try:
            self.populate_dcf_steps(result, dialog)
        except Exception as e:
            import traceback
            print(f"Error populating DCF steps: {e}")
            traceback.print_exc()
        
        try:
            self.populate_assumptions(result, dialog)
        except Exception as e:
            import traceback
            print(f"Error populating assumptions: {e}")
            traceback.print_exc()
    
    def populate_raw_financial_data(self, calc, dialog):
        """Populate raw financial statements"""
        import pandas as pd
        
        # Cash Flow Statement - search flexibly for items
        if calc.cashflow is not None and len(calc.cashflow.columns) > 0:
            # First try exact matches
            key_items = ['Operating Cash Flow', 'Total Cash From Operating Activities',
                         'Capital Expenditure', 'Capital Expenditures', 'Free Cash Flow',
                         'Total Cashflows From Operating Activities', 'Cash And Cash Equivalents At End Of Period']
            available_items = [item for item in key_items if item in calc.cashflow.index]
            
            # If we don't have enough items, search more flexibly
            if len(available_items) < 3:
                # Search by keywords in index names
                all_items = list(calc.cashflow.index)
                keywords = {
                    'operating': ['operating', 'cash from operating', 'operating activities'],
                    'capital': ['capital expenditure', 'capex', 'capital expenditures'],
                    'free': ['free cash flow'],
                    'total': ['total cash']
                }
                
                for keyword_list in keywords.values():
                    for item in all_items:
                        item_lower = str(item).lower()
                        if any(kw in item_lower for kw in keyword_list):
                            if item not in available_items:
                                available_items.append(item)
                                break
                
                # Limit to 8 most relevant items
                available_items = available_items[:8]
            
            if available_items and len(available_items) > 0:
                num_cols = min(4, len(calc.cashflow.columns)) + 1  # +1 for item name column, show up to 4 years
                dialog.cashflow_table.setColumnCount(num_cols)
                dialog.cashflow_table.setRowCount(len(available_items))
                
                # Set headers - first column is "Item", rest are years
                headers = ["Item"]
                for i, col in enumerate(calc.cashflow.columns[:min(4, len(calc.cashflow.columns))]):
                    # Format date column header properly
                    if hasattr(col, 'year'):
                        headers.append(f"{col.year}")
                    elif hasattr(col, 'strftime'):
                        try:
                            headers.append(col.strftime('%Y'))
                        except:
                            headers.append(str(col)[:10])
                    else:
                        col_str = str(col)
                        headers.append(col_str[:12] if len(col_str) > 12 else col_str)
                dialog.cashflow_table.setHorizontalHeaderLabels(headers)
                dialog.cashflow_table.horizontalHeader().setVisible(True)
                dialog.cashflow_table.verticalHeader().setVisible(False)
                
                for row, item in enumerate(available_items):
                    item_name = str(item)
                    # Truncate item name if too long, but show full name on hover
                    display_name = item_name[:40] + "..." if len(item_name) > 40 else item_name
                    item_cell = QTableWidgetItem(display_name)
                    item_cell.setToolTip(item_name)  # Show full name on hover
                    dialog.cashflow_table.setItem(row, 0, item_cell)
                    for col_idx in range(min(4, len(calc.cashflow.columns))):
                        try:
                            val = calc.cashflow.loc[item].iloc[col_idx]
                            if pd.notna(val):
                                # Always show value, even if zero
                                dialog.cashflow_table.setItem(row, col_idx + 1, 
                                    QTableWidgetItem(self.format_currency_table(val)))
                            else:
                                dialog.cashflow_table.setItem(row, col_idx + 1, QTableWidgetItem("N/A"))
                        except (IndexError, KeyError):
                            dialog.cashflow_table.setItem(row, col_idx + 1, QTableWidgetItem("N/A"))
            else:
                # Show message if no data found
                dialog.cashflow_table.setColumnCount(1)
                dialog.cashflow_table.setRowCount(1)
                dialog.cashflow_table.setHorizontalHeaderLabels(["Message"])
                dialog.cashflow_table.horizontalHeader().setVisible(True)
                dialog.cashflow_table.verticalHeader().setVisible(False)
                dialog.cashflow_table.setItem(0, 0, QTableWidgetItem("Cash flow data not available"))
        
        # Balance Sheet - search flexibly
        if calc.balance_sheet is not None and len(calc.balance_sheet.columns) > 0:
            key_items = ['Total Debt', 'Long Term Debt', 'Current Debt', 
                        'Cash And Cash Equivalents', 'Total Assets', 'Total Liabilities',
                        'Cash Cash Equivalents And Short Term Investments', 'Short Term Debt']
            available_items = [item for item in key_items if item in calc.balance_sheet.index]
            
            # Search more flexibly if needed
            if len(available_items) < 4:
                all_items = list(calc.balance_sheet.index)
                keywords = {
                    'debt': ['total debt', 'long term debt', 'current debt', 'short term debt'],
                    'cash': ['cash', 'cash equivalents'],
                    'assets': ['total assets'],
                    'liabilities': ['total liabilities', 'total liability']
                }
                
                for keyword_list in keywords.values():
                    for item in all_items:
                        item_lower = str(item).lower()
                        if any(kw in item_lower for kw in keyword_list):
                            if item not in available_items:
                                available_items.append(item)
                                break
                
                available_items = available_items[:8]
            
            if available_items and len(available_items) > 0:
                num_cols = min(4, len(calc.balance_sheet.columns)) + 1
                dialog.balance_sheet_table.setColumnCount(num_cols)
                dialog.balance_sheet_table.setRowCount(len(available_items))
                
                # Set headers properly
                headers = ["Item"]
                for i, col in enumerate(calc.balance_sheet.columns[:min(4, len(calc.balance_sheet.columns))]):
                    if hasattr(col, 'year'):
                        headers.append(f"{col.year}")
                    elif hasattr(col, 'strftime'):
                        try:
                            headers.append(col.strftime('%Y'))
                        except:
                            headers.append(str(col)[:10])
                    else:
                        col_str = str(col)
                        headers.append(col_str[:12] if len(col_str) > 12 else col_str)
                    dialog.balance_sheet_table.setHorizontalHeaderLabels(headers)
                dialog.balance_sheet_table.horizontalHeader().setVisible(True)
                dialog.balance_sheet_table.verticalHeader().setVisible(False)
                
                for row, item in enumerate(available_items):
                    item_name = str(item)
                    display_name = item_name[:40] + "..." if len(item_name) > 40 else item_name
                    item_cell = QTableWidgetItem(display_name)
                    item_cell.setToolTip(item_name)
                    dialog.balance_sheet_table.setItem(row, 0, item_cell)
                    for col_idx in range(min(4, len(calc.balance_sheet.columns))):
                        try:
                            val = calc.balance_sheet.loc[item].iloc[col_idx]
                            if pd.notna(val):
                                dialog.balance_sheet_table.setItem(row, col_idx + 1, 
                                    QTableWidgetItem(self.format_currency_table(val)))
                            else:
                                dialog.balance_sheet_table.setItem(row, col_idx + 1, QTableWidgetItem("N/A"))
                        except (IndexError, KeyError):
                            dialog.balance_sheet_table.setItem(row, col_idx + 1, QTableWidgetItem("N/A"))
            else:
                dialog.balance_sheet_table.setColumnCount(1)
                dialog.balance_sheet_table.setRowCount(1)
                dialog.balance_sheet_table.setHorizontalHeaderLabels(["Message"])
                dialog.balance_sheet_table.horizontalHeader().setVisible(True)
                dialog.balance_sheet_table.verticalHeader().setVisible(False)
                dialog.balance_sheet_table.setItem(0, 0, QTableWidgetItem("Balance sheet data not available"))
        
        # Income Statement - search flexibly
        if calc.financials is not None and len(calc.financials.columns) > 0:
            key_items = ['Total Revenue', 'Revenue', 'Net Income', 'Interest Expense', 
                        'Operating Income', 'Operating Income Loss', 'Gross Profit', 
                        'Cost Of Revenue', 'Income Tax Expense']
            available_items = [item for item in key_items if item in calc.financials.index]
            
            # Search more flexibly if needed
            if len(available_items) < 4:
                all_items = list(calc.financials.index)
                keywords = {
                    'revenue': ['total revenue', 'revenue', 'net revenue'],
                    'income': ['net income', 'operating income', 'income'],
                    'interest': ['interest expense', 'interest'],
                    'profit': ['gross profit', 'profit']
                }
                
                for keyword_list in keywords.values():
                    for item in all_items:
                        item_lower = str(item).lower()
                        if any(kw in item_lower for kw in keyword_list):
                            if item not in available_items:
                                available_items.append(item)
                                break
                
                available_items = available_items[:8]
            
            if available_items and len(available_items) > 0:
                num_cols = min(4, len(calc.financials.columns)) + 1
                dialog.income_table.setColumnCount(num_cols)
                dialog.income_table.setRowCount(len(available_items))
                
                # Set headers properly
                headers = ["Item"]
                for i, col in enumerate(calc.financials.columns[:min(4, len(calc.financials.columns))]):
                    if hasattr(col, 'year'):
                        headers.append(f"{col.year}")
                    elif hasattr(col, 'strftime'):
                        try:
                            headers.append(col.strftime('%Y'))
                        except:
                            headers.append(str(col)[:10])
                    else:
                        col_str = str(col)
                        headers.append(col_str[:12] if len(col_str) > 12 else col_str)
                dialog.income_table.setHorizontalHeaderLabels(headers)
                dialog.income_table.horizontalHeader().setVisible(True)
                dialog.income_table.verticalHeader().setVisible(False)
                
                for row, item in enumerate(available_items):
                    item_name = str(item)
                    display_name = item_name[:40] + "..." if len(item_name) > 40 else item_name
                    item_cell = QTableWidgetItem(display_name)
                    item_cell.setToolTip(item_name)
                    dialog.income_table.setItem(row, 0, item_cell)
                    for col_idx in range(min(4, len(calc.financials.columns))):
                        try:
                            val = calc.financials.loc[item].iloc[col_idx]
                            if pd.notna(val):
                                dialog.income_table.setItem(row, col_idx + 1, 
                                    QTableWidgetItem(self.format_currency_table(val)))
                            else:
                                dialog.income_table.setItem(row, col_idx + 1, QTableWidgetItem("N/A"))
                        except (IndexError, KeyError):
                            dialog.income_table.setItem(row, col_idx + 1, QTableWidgetItem("N/A"))
            else:
                dialog.income_table.setColumnCount(1)
                dialog.income_table.setRowCount(1)
                dialog.income_table.setHorizontalHeaderLabels(["Message"])
                dialog.income_table.horizontalHeader().setVisible(True)
                dialog.income_table.verticalHeader().setVisible(False)
                dialog.income_table.setItem(0, 0, QTableWidgetItem("Income statement data not available"))
    
    def populate_fcf_calculation(self, calc, dialog):
        """Show FCF calculation breakdown with actual numbers per year"""
        fcf_history = calc.get_free_cash_flow(years=5)
        
        dialog.fcf_calc_table.setColumnCount(5)
        dialog.fcf_calc_table.setHorizontalHeaderLabels(["Year", "Operating CF", "Capital Expenditures", "FCF Calculation", "FCF Result"])
        dialog.fcf_calc_table.horizontalHeader().setVisible(True)
        dialog.fcf_calc_table.verticalHeader().setVisible(False)
        
        if len(fcf_history) > 0:
            dialog.fcf_calc_table.setRowCount(len(fcf_history) + 1)
            
            # Get actual operating CF and capex for each year
            for idx, (date, fcf) in enumerate(fcf_history.items()):
                year = str(date)[:4] if hasattr(date, 'year') else str(date)
                dialog.fcf_calc_table.setItem(idx, 0, QTableWidgetItem(year))
                
                # Get actual values for this specific year/date
                operating_cf = None
                capex = None
                
                if calc.cashflow is not None and len(calc.cashflow.columns) > idx:
                    # Try to find operating cash flow for this year
                    for key in ['Operating Cash Flow', 'Total Cash From Operating Activities']:
                        if key in calc.cashflow.index:
                            try:
                                operating_cf = calc.cashflow.loc[key].iloc[idx]
                            except:
                                pass
                            break
                    
                    # Try to find capex for this year
                    for key in ['Capital Expenditure', 'Capital Expenditures']:
                        if key in calc.cashflow.index:
                            try:
                                capex = calc.cashflow.loc[key].iloc[idx]
                            except:
                                pass
                            break
                
                # If not found, try alternative method - search by date
                if operating_cf is None or pd.isna(operating_cf):
                    for key in ['Operating Cash Flow', 'Total Cash From Operating Activities']:
                        if key in calc.cashflow.index:
                            series = calc.cashflow.loc[key]
                            if date in series.index:
                                operating_cf = series[date]
                                break
                            elif len(series) > idx:
                                operating_cf = series.iloc[idx]
                                break
                
                if capex is None or pd.isna(capex):
                    for key in ['Capital Expenditure', 'Capital Expenditures']:
                        if key in calc.cashflow.index:
                            series = calc.cashflow.loc[key]
                            if date in series.index:
                                capex = series[date]
                                break
                            elif len(series) > idx:
                                capex = series.iloc[idx]
                                break
                
                # Display actual values
                if pd.notna(operating_cf) and operating_cf is not None:
                    opcf_item = QTableWidgetItem(self.format_currency_table(operating_cf))
                    opcf_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    dialog.fcf_calc_table.setItem(idx, 1, opcf_item)
                else:
                    na_item = QTableWidgetItem("N/A")
                    na_item.setTextAlignment(Qt.AlignCenter)
                    dialog.fcf_calc_table.setItem(idx, 1, na_item)
                
                if pd.notna(capex) and capex is not None:
                    # Capex is usually negative, show as positive in display
                    capex_item = QTableWidgetItem(self.format_currency_table(abs(capex)))
                    capex_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    dialog.fcf_calc_table.setItem(idx, 2, capex_item)
                else:
                    na_item = QTableWidgetItem("N/A")
                    na_item.setTextAlignment(Qt.AlignCenter)
                    dialog.fcf_calc_table.setItem(idx, 2, na_item)
                
                # Show calculation
                if pd.notna(operating_cf) and pd.notna(capex):
                    calc_str = f"{self.format_currency_table(operating_cf)} - {self.format_currency_table(abs(capex))}"
                else:
                    calc_str = "Operating CF - CapEx"
                
                dialog.fcf_calc_table.setItem(idx, 3, QTableWidgetItem(calc_str))
                dialog.fcf_calc_table.setItem(idx, 4, QTableWidgetItem(self.format_currency_table(fcf)))
                
                # Right-align currency columns
                for col in [1, 2, 4]:
                    item = dialog.fcf_calc_table.item(idx, col)
                    if item:
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # Current FCF row (highlighted)
            current_fcf = fcf_history.iloc[0]
            row = len(fcf_history)
            dialog.fcf_calc_table.setItem(row, 0, QTableWidgetItem("Current (Most Recent)"))
            dialog.fcf_calc_table.setItem(row, 1, QTableWidgetItem(""))
            dialog.fcf_calc_table.setItem(row, 2, QTableWidgetItem(""))
            dialog.fcf_calc_table.setItem(row, 3, QTableWidgetItem("Used for projections"))
            item = QTableWidgetItem(self.format_currency_table(current_fcf))
            item.setFont(QFont("", 9, QFont.Bold))
            item.setBackground(QColor(230, 230, 255))
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            dialog.fcf_calc_table.setItem(row, 4, item)
    
    def populate_growth_calculation(self, calc, result, dialog):
        """Show growth rate calculation breakdown with actual FCF values"""
        fcf_history = calc.get_free_cash_flow(years=5)
        growth_rate = result['growth_rate']
        
        dialog.growth_calc_table.setColumnCount(5)
        dialog.growth_calc_table.setHorizontalHeaderLabels(["Year", "FCF (Year N)", "FCF (Year N-1)", "Growth Calculation", "Growth Rate"])
        dialog.growth_calc_table.horizontalHeader().setVisible(True)
        dialog.growth_calc_table.verticalHeader().setVisible(False)
        
        if len(fcf_history) >= 2:
            rows = []
            fcf_items = list(fcf_history.items())
            fcf_values = fcf_history.values
            
            for i in range(len(fcf_values) - 1):
                year1_val = fcf_values[i]
                year2_val = fcf_values[i + 1]
                year1_date = fcf_items[i][0]
                year2_date = fcf_items[i + 1][0]
                
                year1_str = str(year1_date)[:4] if hasattr(year1_date, 'year') else str(year1_date)[:4]
                year2_str = str(year2_date)[:4] if hasattr(year2_date, 'year') else str(year2_date)[:4]
                
                if year2_val != 0 and not pd.isna(year2_val):
                    growth = (year1_val - year2_val) / abs(year2_val)
                    calc_str = f"({self.format_currency_table(year1_val)} - {self.format_currency_table(year2_val)}) / {self.format_currency_table(abs(year2_val))}"
                    rows.append((f"{year1_str} vs {year2_str}", year1_val, year2_val, calc_str, growth))
            
            dialog.growth_calc_table.setRowCount(len(rows) + 1)
            
            for idx, (year_pair, y1, y2, calc_str, growth) in enumerate(rows):
                dialog.growth_calc_table.setItem(idx, 0, QTableWidgetItem(year_pair))
                y1_item = QTableWidgetItem(self.format_currency_table(y1))
                y1_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                dialog.growth_calc_table.setItem(idx, 1, y1_item)
                y2_item = QTableWidgetItem(self.format_currency_table(y2))
                y2_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                dialog.growth_calc_table.setItem(idx, 2, y2_item)
                dialog.growth_calc_table.setItem(idx, 3, QTableWidgetItem(calc_str))
                growth_item = QTableWidgetItem(f"{growth*100:.2f}%")
                growth_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                dialog.growth_calc_table.setItem(idx, 4, growth_item)
            
            # Average/CAGR result
            result_row = len(rows)
            dialog.growth_calc_table.setItem(result_row, 0, QTableWidgetItem("Final Growth Rate"))
            dialog.growth_calc_table.setItem(result_row, 1, QTableWidgetItem(""))
            dialog.growth_calc_table.setItem(result_row, 2, QTableWidgetItem(""))
            dialog.growth_calc_table.setItem(result_row, 3, QTableWidgetItem("Average of above growth rates"))
            item = QTableWidgetItem(f"{growth_rate*100:.2f}%")
            item.setFont(QFont("", 9, QFont.Bold))
            item.setBackground(QColor(230, 255, 230))
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            dialog.growth_calc_table.setItem(result_row, 4, item)
        else:
            # Not enough data - show message
            dialog.growth_calc_table.setRowCount(1)
            dialog.growth_calc_table.setItem(0, 0, QTableWidgetItem("Insufficient data"))
            dialog.growth_calc_table.setItem(0, 1, QTableWidgetItem("Need at least 2 years of FCF data"))
            dialog.growth_calc_table.setItem(0, 2, QTableWidgetItem(""))
            dialog.growth_calc_table.setItem(0, 3, QTableWidgetItem(""))
            dialog.growth_calc_table.setItem(0, 4, QTableWidgetItem(""))
    
    def populate_wacc_calculation(self, calc, result, dialog):
        """Show WACC calculation breakdown with actual numbers"""
        wacc_data = []
        
        # Get components from actual stock data
        info = calc.info or {}
        beta = info.get('beta', 1.0) or 1.0
        market_cap = info.get('marketCap', 0) or 0
        shares_outstanding = info.get('sharesOutstanding', 0) or 0
        current_price = info.get('currentPrice', 0) or 0
        tax_rate = info.get('taxRate', 0.25) or 0.25
        
        # Get debt info from actual financials
        total_debt = 0
        long_term_debt = 0
        current_debt = 0
        interest_expense = 0
        
        if calc.balance_sheet is not None and len(calc.balance_sheet.columns) > 0:
            if 'Total Debt' in calc.balance_sheet.index:
                total_debt = calc.balance_sheet.loc['Total Debt'].iloc[0] if pd.notna(calc.balance_sheet.loc['Total Debt'].iloc[0]) else 0
            elif 'Long Term Debt' in calc.balance_sheet.index and 'Current Debt' in calc.balance_sheet.index:
                long_term_debt = calc.balance_sheet.loc['Long Term Debt'].iloc[0] if pd.notna(calc.balance_sheet.loc['Long Term Debt'].iloc[0]) else 0
                current_debt = calc.balance_sheet.loc['Current Debt'].iloc[0] if pd.notna(calc.balance_sheet.loc['Current Debt'].iloc[0]) else 0
                total_debt = long_term_debt + current_debt
        
        if calc.financials is not None and len(calc.financials.columns) > 0:
            if 'Interest Expense' in calc.financials.index:
                interest_expense = abs(calc.financials.loc['Interest Expense'].iloc[0]) if pd.notna(calc.financials.loc['Interest Expense'].iloc[0]) else 0
        
        cost_of_debt = (interest_expense / total_debt) if total_debt > 0 else 0.05
        enterprise_value = market_cap + total_debt
        
        equity_weight = (market_cap / enterprise_value) if enterprise_value > 0 else 0.7
        debt_weight = (total_debt / enterprise_value) if enterprise_value > 0 else 0.3
        
        risk_free_rate = result.get('risk_free_rate', 0.04)
        market_risk_premium = result.get('market_risk_premium', 0.06)
        cost_of_equity = risk_free_rate + (beta * market_risk_premium)
        
        wacc = result['discount_rate']
        
        # Calculate WACC with actual formula
        after_tax_cost_debt = cost_of_debt * (1 - tax_rate)
        calculated_wacc = (equity_weight * cost_of_equity) + (debt_weight * after_tax_cost_debt)
        
        wacc_data = [
            ("Stock Price", self.format_currency_table(current_price), f"Current market price per share"),
            ("Shares Outstanding", f"{shares_outstanding:,.0f}", "Total number of shares"),
            ("Market Cap (E)", self.format_currency_table(market_cap), f"Price × Shares = {current_price:,.2f} × {shares_outstanding:,.0f}"),
            ("", "", ""),
            ("Beta (β)", f"{beta:.2f}", f"From stock data - volatility measure"),
            ("Risk-Free Rate (Rf)", f"{risk_free_rate*100:.2f}%", "10-year Treasury yield (assumed)"),
            ("Market Risk Premium", f"{market_risk_premium*100:.2f}%", "Expected market return - Risk-free rate (assumed)"),
            ("Cost of Equity (Re)", f"{cost_of_equity*100:.2f}%", f"Re = Rf + β × MRP = {risk_free_rate*100:.2f}% + {beta:.2f} × {market_risk_premium*100:.2f}%"),
            ("", "", ""),
            ("Interest Expense", self.format_currency_table(interest_expense), "From most recent income statement"),
            ("Total Debt (D)", self.format_currency_table(total_debt), "From balance sheet (current + long-term)"),
            ("Cost of Debt (Rd)", f"{cost_of_debt*100:.2f}%", f"Rd = Interest / Debt = {self.format_currency_table(interest_expense)} / {self.format_currency_table(total_debt)}"),
            ("Tax Rate (Tc)", f"{tax_rate*100:.2f}%", "Corporate tax rate from stock data"),
            ("After-Tax Cost of Debt", f"{after_tax_cost_debt*100:.2f}%", f"Rd × (1 - Tc) = {cost_of_debt*100:.2f}% × (1 - {tax_rate*100:.2f}%)"),
            ("", "", ""),
            ("Enterprise Value (V)", self.format_currency_table(enterprise_value), f"V = E + D = {self.format_currency_table(market_cap)} + {self.format_currency_table(total_debt)}"),
            ("Equity Weight (E/V)", f"{equity_weight*100:.2f}%", f"E/V = {self.format_currency_table(market_cap)} / {self.format_currency_table(enterprise_value)}"),
            ("Debt Weight (D/V)", f"{debt_weight*100:.2f}%", f"D/V = {self.format_currency_table(total_debt)} / {self.format_currency_table(enterprise_value)}"),
            ("", "", ""),
            ("WACC Calculation", f"{wacc*100:.2f}%", f"WACC = (E/V × Re) + (D/V × Rd × (1-Tc))"),
            ("Formula Breakdown", "", f"= ({equity_weight*100:.2f}% × {cost_of_equity*100:.2f}%) + ({debt_weight*100:.2f}% × {after_tax_cost_debt*100:.2f}%)"),
            ("Calculated WACC", f"{calculated_wacc*100:.2f}%", f"= ({equity_weight:.4f} × {cost_of_equity*100:.2f}%) + ({debt_weight:.4f} × {after_tax_cost_debt*100:.2f}%)"),
        ]
        
        dialog.wacc_calc_table.setColumnCount(3)
        dialog.wacc_calc_table.setHorizontalHeaderLabels(["Component", "Value", "Explanation"])
        # Ensure headers are visible
        dialog.wacc_calc_table.horizontalHeader().setVisible(True)
        dialog.wacc_calc_table.verticalHeader().setVisible(False)
        dialog.wacc_calc_table.setRowCount(len(wacc_data))
        
        for row, (component, value, explanation) in enumerate(wacc_data):
            dialog.wacc_calc_table.setItem(row, 0, QTableWidgetItem(component))
            dialog.wacc_calc_table.setItem(row, 1, QTableWidgetItem(value))
            dialog.wacc_calc_table.setItem(row, 2, QTableWidgetItem(explanation))
            
            if "WACC" in component or "Calculated WACC" in component:
                for col in range(3):
                    item = dialog.wacc_calc_table.item(row, col)
                    if item:
                        item.setFont(QFont("", 9, QFont.Bold))
                        item.setBackground(QColor(230, 255, 230))
    
    def populate_dcf_steps(self, result, dialog):
        """Show step-by-step DCF calculation"""
        steps_data = [
            ("Step 1", "Project Future FCFs", f"Current FCF × (1 + Growth Rate)^year for 10 years", ""),
            ("", "", f"Starting FCF: {self.format_currency_table(result['current_fcf'])}", ""),
            ("", "", f"Growth Rate: {result['growth_rate']*100:.2f}%", ""),
            ("", "", "", ""),
            ("Step 2", "Discount to Present Value", "Divide each year's FCF by (1 + WACC)^year", ""),
            ("", "", f"Discount Rate (WACC): {result['discount_rate']*100:.2f}%", ""),
            ("", "", "", ""),
        ]
        
        # Add projection details
        for year_data in result['projected_fcf'][:3]:  # Show first 3 years
            year = year_data['year']
            fcf = year_data['fcf']
            discounted = year_data['discounted_fcf']
            steps_data.append(("", f"Year {year}", 
                             f"FCF: {self.format_currency_table(fcf)}, Discounted: {self.format_currency_table(discounted)}", ""))
        
        steps_data.extend([
            ("", "...", "...", ""),
            ("", "", "", ""),
            ("Step 3", "Sum Discounted FCFs", 
             f"Total: {self.format_currency_table(sum([y['discounted_fcf'] for y in result['projected_fcf']]))}", ""),
            ("", "", "", ""),
            ("Step 4", "Calculate Terminal Value", 
             f"(Final Year FCF × (1 + Terminal Growth)) / (WACC - Terminal Growth)", ""),
            ("", "", 
             f"= ({self.format_currency_table(result['projected_fcf'][-1]['fcf'])} × (1 + {result['terminal_growth_rate']*100:.2f}%)) / ({result['discount_rate']*100:.2f}% - {result['terminal_growth_rate']*100:.2f}%)", ""),
            ("", "", f"Terminal Value: {self.format_currency_table(result['terminal_value'])}", ""),
            ("", "", "", ""),
            ("Step 5", "Discount Terminal Value", 
             f"Terminal Value / (1 + WACC)^{len(result['projected_fcf'])}", ""),
            ("", "", 
             f"= {self.format_currency_table(result['terminal_value'])} / (1 + {result['discount_rate']*100:.2f}%)^{len(result['projected_fcf'])}", ""),
            ("", "", f"Discounted Terminal Value: {self.format_currency_table(result['discounted_terminal_value'])}", ""),
            ("", "", "", ""),
            ("Step 6", "Calculate Enterprise Value", 
             f"Sum of Discounted FCFs + Discounted Terminal Value", ""),
            ("", "", 
             f"= {self.format_currency_table(sum([y['discounted_fcf'] for y in result['projected_fcf']]))} + {self.format_currency_table(result['discounted_terminal_value'])}", ""),
            ("", "", f"Enterprise Value: {self.format_currency_table(result['enterprise_value'])}", ""),
            ("", "", "", ""),
            ("Step 7", "Calculate Equity Value", 
             f"Enterprise Value - Net Debt", ""),
            ("", "", 
             f"= {self.format_currency_table(result['enterprise_value'])} - {self.format_currency_table(result['net_debt'])}", ""),
            ("", "", f"Equity Value: {self.format_currency_table(result['equity_value'])}", ""),
            ("", "", "", ""),
            ("Step 8", "Value Per Share", 
             f"Equity Value / Shares Outstanding", ""),
            ("", "", 
             f"= {self.format_currency_table(result['equity_value'])} / {result['shares_outstanding']:,.0f}", ""),
            ("", "", f"Value Per Share: {self.format_currency_table(result['per_share_value'])}", ""),
        ])
        
        dialog.dcf_steps_table.setColumnCount(4)
        dialog.dcf_steps_table.setHorizontalHeaderLabels(["Step", "Description", "Calculation", ""])
        # Ensure headers are visible
        dialog.dcf_steps_table.horizontalHeader().setVisible(True)
        dialog.dcf_steps_table.verticalHeader().setVisible(False)
        dialog.dcf_steps_table.setRowCount(len(steps_data))
        
        for row, (step, desc, calc, extra) in enumerate(steps_data):
            if step:
                item = QTableWidgetItem(step)
                item.setFont(QFont("", 9, QFont.Bold))
                item.setBackground(QColor(240, 240, 255))
                dialog.dcf_steps_table.setItem(row, 0, item)
            else:
                dialog.dcf_steps_table.setItem(row, 0, QTableWidgetItem(""))
            
            dialog.dcf_steps_table.setItem(row, 1, QTableWidgetItem(desc if desc else ""))
            dialog.dcf_steps_table.setItem(row, 2, QTableWidgetItem(calc if calc else ""))
            dialog.dcf_steps_table.setItem(row, 3, QTableWidgetItem(extra if extra else ""))
    
    def populate_assumptions(self, result, dialog):
        """Show all assumptions used"""
        assumptions_data = [
            ("Growth Rate", f"{result['growth_rate']*100:.2f}%", "Applied to each year's FCF projection"),
            ("Discount Rate (WACC)", f"{result['discount_rate']*100:.2f}%", "Used to discount future cash flows"),
            ("Terminal Growth Rate", f"{result['terminal_growth_rate']*100:.2f}%", "Long-term growth rate after projection period"),
            ("Projection Period", "10 years", "Number of years to project FCFs"),
            ("Terminal Value Model", "Perpetuity Growth Model", "Gordon Growth Model: FCF × (1+g) / (WACC - g)"),
            ("Current FCF", self.format_currency_table(result['current_fcf']), "Starting point for projections"),
            ("", "", ""),
            ("Data Source", "Yahoo Finance", "Financial statements from public filings"),
            ("Market Data", "Real-time", "Current stock price and market cap"),
            ("Currency", "USD", "All values in US Dollars"),
        ]
        
        dialog.assumptions_table.setColumnCount(3)
        dialog.assumptions_table.setHorizontalHeaderLabels(["Assumption", "Value", "Note"])
        # Ensure headers are visible
        dialog.assumptions_table.horizontalHeader().setVisible(True)
        dialog.assumptions_table.verticalHeader().setVisible(False)
        dialog.assumptions_table.setRowCount(len(assumptions_data))
        
        for row, (assumption, value, note) in enumerate(assumptions_data):
            dialog.assumptions_table.setItem(row, 0, QTableWidgetItem(assumption))
            dialog.assumptions_table.setItem(row, 1, QTableWidgetItem(value))
            dialog.assumptions_table.setItem(row, 2, QTableWidgetItem(note))
    
    def on_calculation_error(self, error_msg):
        """Display error message"""
        self.progress_bar.setVisible(False)
        self.calculate_btn.setEnabled(True)
        
        # Show simplified error message
        error_display = error_msg.split('\n')[0]  # Just show first line
        QMessageBox.critical(self, "Calculation Error", f"Unable to calculate DCF:\n\n{error_display}")
        
        # Clear tables
        self.summary_table.setRowCount(0)
        self.projections_table.setRowCount(0)
        self.valuation_table.setRowCount(0)
        
        self.detailed_breakdown_btn.setVisible(False)


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = DCFApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

