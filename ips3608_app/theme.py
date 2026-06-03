"""Central design tokens for the IPS3608 instrument UI.

Single source of truth for colors so inline ``setStyleSheet`` literals don't
drift from DESIGN.md. Channel colors map one-to-one to a physical quantity
(the Channel Monopoly Rule); state colors are spectrally distinct from them.
"""

from __future__ import annotations

# --- Neutrals (surface) ---------------------------------------------------
INSTRUMENT_INK = "#0F1B2A"      # primary text
INSTRUMENT_PANEL = "#F4F6F8"    # window background (brushed-aluminum)
INSTRUMENT_WHITE = "#FFFFFF"    # widget surfaces
PANEL_SEAM = "#D7DEE6"          # 1px borders
CONSOLE_SLATE = "#4A5A6A"       # secondary text / inactive
HOVER_SURFACE = "#EBF2FB"       # button hover

# --- Channel colors (one physical quantity each) --------------------------
VOLTAGE_BLUE = "#0B84F3"
AMPERE_GREEN = "#00A86B"
WATT_GOLD = "#F59E0B"
CRITICAL_RED = "#EF4444"        # temperature channel

# --- State colors (spectrally distinct from channels) ---------------------
ACTIVE_GREEN = "#22C55E"        # status dots: live / on / running
ACTIVE_GREEN_DEEP = "#16A34A"   # active action button bg / status text
STOP_RED = "#DC2626"            # stop actions / output-off status
TRANSITIONAL_YELLOW = "#EAB308" # connecting (transient)
FAULT_ORANGE = "#F97316"        # communication error

# --- Connection button schemes (bg, text, border) ------------------------
CONN_SCHEME_CONNECTED = ("#dcfce7", "#166534", "#86efac")
CONN_SCHEME_DISCONNECTED = ("#fee2e2", "#991b1b", "#fca5a5")
CONN_SCHEME_CONNECTING = ("#fef9c3", "#a16207", "#fde047")
CONN_SCHEME_ERROR = ("#fed7aa", "#b45309", "#fb923c")

# --- Datalogger running banner -------------------------------------------
BANNER_BG = "#dcfce7"
BANNER_TEXT = "#14532d"
BANNER_BORDER = "#86efac"

# --- Radii ----------------------------------------------------------------
RADIUS_CARD = "12px"
RADIUS_PANEL = "8px"
RADIUS_BUTTON = "6px"
RADIUS_INPUT = "5px"


APP_STYLESHEET = f"""
QMainWindow {{ background-color: {INSTRUMENT_PANEL}; color: {INSTRUMENT_INK}; }}
QGroupBox {{
    border: 1px solid {PANEL_SEAM}; border-radius: {RADIUS_PANEL}; margin-top: 10px;
    font-weight: 700; color: {INSTRUMENT_INK}; background: {INSTRUMENT_WHITE};
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 6px; }}
QLabel {{ color: {INSTRUMENT_INK}; }}
QPushButton {{
    background-color: {INSTRUMENT_WHITE}; color: {INSTRUMENT_INK}; border: 1px solid {PANEL_SEAM};
    border-radius: {RADIUS_BUTTON}; padding: 6px 10px; font-weight: 600;
}}
QPushButton:hover {{ background-color: {HOVER_SURFACE}; }}
QPushButton:focus {{ border: 1px solid {VOLTAGE_BLUE}; }}
QComboBox, QDoubleSpinBox {{
    background-color: {INSTRUMENT_WHITE}; border: 1px solid {PANEL_SEAM}; border-radius: {RADIUS_INPUT};
    padding: 4px; color: {INSTRUMENT_INK};
}}
QComboBox:focus, QDoubleSpinBox:focus {{ border: 1px solid {VOLTAGE_BLUE}; }}
QTableWidget {{
    background-color: {INSTRUMENT_WHITE}; color: {INSTRUMENT_INK}; gridline-color: {PANEL_SEAM};
    border: 1px solid {PANEL_SEAM};
}}
QHeaderView::section {{
    background-color: {INSTRUMENT_PANEL}; color: {INSTRUMENT_INK}; border: 1px solid {PANEL_SEAM};
    padding: 4px; font-weight: 600;
}}
QTextEdit {{ background-color: {INSTRUMENT_WHITE}; border: 1px solid {PANEL_SEAM}; color: {INSTRUMENT_INK}; }}
QFrame#MetricCard {{
    background-color: {INSTRUMENT_WHITE}; border: 1px solid {PANEL_SEAM}; border-radius: {RADIUS_CARD};
}}
"""
