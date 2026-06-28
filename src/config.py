import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
ENV_PATH = ROOT_DIR / ".env"
CREDENTIALS_PATH = ROOT_DIR / "credentials.json"
TOKEN_PATH = ROOT_DIR / "token.json"

# Load variables from .env file
load_dotenv(ENV_PATH)

# --- Secret Parameters (Loaded from Environment) ---
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

# --- Google API Configurations ---
FOLDER_NAME = "PUFC_Fall2026"
SCOPES = ['https://googleapis.com', 'https://googleapis.com']

# --- SMTP Mail Server Settings ---
SMTP_SERVER = "://gmail.com"
SMTP_PORT = 587

# --- Dynamic File Naming Rules ---
TIMESTAMP = datetime.now().strftime("%Y%m%d_%I%M%p")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PDF_FILENAME = str(OUTPUT_DIR / f"Club_Schedule_{TIMESTAMP}.pdf")
DRIVE_DISPLAY_NAME = f"Club Master Schedule ({datetime.now().strftime('%b %d, %Y')})"
LOGO_FILENAME = str(ROOT_DIR / "club_logo.png")

# --- PDF Visual Layout Style Constants ---
COLOR_PRIMARY = "#1A365D"       # Navy Blue Header bar
COLOR_GRID_LINE = "#CBD5E1"     # Soft Gray Cell Border
COLOR_ROW_ALT = "#F8FAFC"       # Zebra striping background highlight

FONT_SIZE_TITLE = 20
FONT_SIZE_SUBTITLE = 9
FONT_SIZE_TABLE_HEADER = 10
FONT_SIZE_TABLE_CELL = 9

# Fixed column width sizing for ReportLab Tables (in points)
# [Date, Day, Time, Field A, Field B, Field C] -> 550 total width fits Letter page margins
TABLE_COLUMN_WIDTHS = [65, 55, 75, 115, 115, 125]
HEADER_TABLE_WIDTHS = [60, 490]
