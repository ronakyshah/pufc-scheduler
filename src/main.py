import sys
import pandas as pd
import random
import ast
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Import all clean settings directly from your configuration script
import config

# Google Workspace API Modules
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    Credentials = None
    InstalledAppFlow = None
    Request = None
    build = None
    MediaFileUpload = None

# PDF Styling Engine Modules
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ---------------------------------------------------------
# GOOGLE DRIVE API CONNECTOR
# ---------------------------------------------------------
def get_drive_service():
    if Credentials is None or InstalledAppFlow is None or Request is None or build is None or MediaFileUpload is None:
        raise RuntimeError("Google client libraries are not installed. Install them to use Google Sheet mode.")

    creds = None
    if os.path.exists(config.TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(str(config.TOKEN_PATH), config.SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(config.CREDENTIALS_PATH), config.SCOPES)
            creds = flow.run_local_server(port=0)
        with open(config.TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def get_or_create_folder(service, folder_name):
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, fields="files(id)").execute()
    items = results.get('files', [])
    if items:
        return items[0]['id']
    
    folder_metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    return folder.get('id')

# ---------------------------------------------------------
# CORE DATA PROCESSING ENGINE
# ---------------------------------------------------------
def read_local_schedule(example_path=None):
    example_path = example_path or config.INPUT_DIR / "exampleSchedule.csv"
    if not example_path.exists():
        raise FileNotFoundError(f"Local example file not found: {example_path}")

    df = pd.read_csv(example_path)
    df['Game Date'] = pd.to_datetime(df['Game Date'], errors='coerce')
    df['Game Time'] = pd.to_datetime(df['Game Time'], format='%H:%M:%S', errors='coerce')

    df['Date'] = df['Game Date'].dt.strftime('%Y-%m-%d')
    df['Day_of_Week'] = df['Game Date'].dt.day_name()
    df['Time_Slot'] = df['Game Time'].dt.strftime('%H:%M')
    df['Field_Name'] = df['Field'].fillna('TBD')
    df['Team_Name'] = df['Home Team'].fillna('TBD')
    df['Coach_Name'] = df['Home Coach'].fillna('TBD')
    return df


def export_referee_contacts(df, output_path=None):
    output_path = output_path or config.INPUT_DIR / "referee.csv"

    official_specs = [
        ("Referee", "Referee", "Referee Email", "Referee Contact Phone"),
        ("AR #1", "AR #1", "AR #1 Email", "AR #1 Contact Phone"),
        ("AR #2", "AR #2", "AR #2 Email", "AR #2 Contact Phone"),
        ("Other Official", "Other Official", "Other Official Email", "Other Official Contact Phone"),
    ]

    referee_rows = []
    for role, name_col, email_col, phone_col in official_specs:
        subset = df[[name_col, email_col, phone_col]].copy()
        subset = subset.dropna(how='all')
        for _, row in subset.iterrows():
            name = row.get(name_col)
            email = row.get(email_col)
            phone = row.get(phone_col)
            if pd.isna(name) and pd.isna(email) and pd.isna(phone):
                continue

            referee_rows.append({
                'Role': role,
                'Name': '' if pd.isna(name) else str(name).strip(),
                'Email': '' if pd.isna(email) else str(email).strip(),
                'Phone': '' if pd.isna(phone) else str(phone).strip(),
            })

    referee_df = pd.DataFrame(referee_rows)
    if not referee_df.empty:
        referee_df = referee_df.drop_duplicates(subset=['Role', 'Name', 'Email', 'Phone']).sort_values(by=['Role', 'Name'])

    referee_df.to_csv(output_path, index=False)
    return referee_df


def fetch_schedule_and_emails(mode="google"):
    mode = mode.lower()

    if mode == "local":
        df = read_local_schedule()

        recipient_emails = set()
        for col in ['Home Coach Email', 'Away Coach Email']:
            recipient_emails.update(
                df[col].dropna().astype(str).str.strip().tolist()
            )
        recipient_emails = {email for email in recipient_emails if '@' in email}

        export_referee_contacts(df)

        df_raw = df[['Date', 'Day_of_Week', 'Time_Slot', 'Field_Name', 'Team_Name', 'Coach_Name']].copy()
        df_raw = df_raw.drop_duplicates(subset=['Date', 'Day_of_Week', 'Time_Slot', 'Field_Name', 'Team_Name', 'Coach_Name'])
        df_raw = df_raw.sort_values(by=['Date', 'Time_Slot', 'Field_Name'])

        if df_raw.empty:
            return pd.DataFrame(columns=['Date', 'Day_of_Week', 'Time_Slot']), list(recipient_emails)

        visual_grid = (
            df_raw.groupby(['Date', 'Day_of_Week', 'Time_Slot', 'Field_Name'])['Team_Name']
            .first()
            .unstack('Field_Name')
            .fillna('—')
            .reset_index()
        )
        return visual_grid, list(recipient_emails)

    fields_url = f"https://google.com{config.SHEET_ID}/export?format=xlsx&sheet=Fields"
    teams_url = f"https://google.com{config.SHEET_ID}/export?format=xlsx&sheet=Teams"
    slots_url = f"https://google.com{config.SHEET_ID}/export?format=xlsx&sheet=Slots"

    df_fields = pd.read_excel(fields_url)
    df_teams = pd.read_excel(teams_url)
    df_slots = pd.read_excel(slots_url)

    df_fields['Allowed_Ages'] = df_fields['Allowed_Ages'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
    df_teams['Pref_Days'] = df_teams['Pref_Days'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

    email_cols = [col for col in df_teams.columns if 'Coach Email' in col]
    recipient_emails = set()
    for col in email_cols:
        valid_emails = df_teams[col].dropna().astype(str).str.strip()
        recipient_emails.update(valid_emails.tolist())
    
    recipient_emails = {email for email in recipient_emails if "@" in email}

    random.seed(45)
    final_schedule = []
    master_slots = []
    
    for _, slot in df_slots.iterrows():
        for _, field in df_fields.iterrows():
            master_slots.append({
                'Date': str(slot['Date']).split()[0],
                'Day_of_Week': slot['Day_of_Week'],
                'Time_Slot': slot['Time_Slot'],
                'Field_Name': field['Field_Name'],
                'Allowed_Ages': field['Allowed_Ages']
            })
            
    teams_list = df_teams.to_dict('records')
    random.shuffle(teams_list)
    
    for team in teams_list:
        valid_slots = []
        for slot in master_slots:
            if team['Age_Group'] not in slot['Allowed_Ages']: continue
            if any(s['Date'] == slot['Date'] and s['Time_Slot'] == slot['Time_Slot'] and s['Field_Name'] == slot['Field_Name'] for s in final_schedule): continue
            if any(s['Date'] == slot['Date'] and s['Time_Slot'] == slot['Time_Slot'] and s['Coach_Name'] == team['Coach_Name'] for s in final_schedule): continue
            
            score = 10 if slot['Day_of_Week'] in team['Pref_Days'] else 0
            score += random.uniform(0, 1)
            valid_slots.append((score, slot))
            
        if valid_slots:
            valid_slots.sort(key=lambda x: x[0], reverse=True)
            best_slot = valid_slots[0][1]
            final_schedule.append({
                'Date': best_slot['Date'], 'Day_of_Week': best_slot['Day_of_Week'],
                'Time_Slot': best_slot['Time_Slot'], 'Field_Name': best_slot['Field_Name'],
                'Team_Name': team['Team_Name'], 'Coach_Name': team['Coach_Name']
            })

    df_raw = pd.DataFrame(final_schedule).sort_values(by=['Date', 'Time_Slot', 'Field_Name'])
    visual_grid = df_raw.pivot(index=['Date', 'Day_of_Week', 'Time_Slot'], columns='Field_Name', values='Team_Name').fillna('—')
    return visual_grid.reset_index(), list(recipient_emails)

# ---------------------------------------------------------
# GRAPHIC REPORT GENERATOR
# ---------------------------------------------------------
def create_pdf(df_schedule):
    doc = SimpleDocTemplate(config.PDF_FILENAME, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=config.FONT_SIZE_TITLE, textColor=colors.HexColor(config.COLOR_PRIMARY), spaceAfter=2)
    meta_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], fontSize=config.FONT_SIZE_SUBTITLE, textColor=colors.HexColor("#64748B"), spaceAfter=15)
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=config.FONT_SIZE_TABLE_CELL, leading=11, alignment=1)
    header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=config.FONT_SIZE_TABLE_HEADER, bold=True, textColor=colors.white, alignment=1)
    
    header_text_block = [
        Paragraph("Master Soccer Club Practice Schedule", title_style),
        Paragraph(f"Published on: {config.datetime.now().strftime('%B %d, %Y at %I:%M %p')}", meta_style)
    ]
    
    if os.path.exists(config.LOGO_FILENAME):
        club_logo = Image(config.LOGO_FILENAME, width=60, height=60)
        header_table = Table([[club_logo, header_text_block]], colWidths=config.HEADER_TABLE_WIDTHS)
    else:
        header_table = Table([[header_text_block]], colWidths=[550])
        
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (1,0), (1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    
    table_data = [[Paragraph(str(col), header_style) for col in df_schedule.columns]]
    for _, row in df_schedule.iterrows():
        table_data.append([Paragraph(str(val), cell_style) for val in row])
        
    schedule_table = Table(table_data, colWidths=config.TABLE_COLUMN_WIDTHS)
    schedule_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor(config.COLOR_PRIMARY)),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor(config.COLOR_GRID_LINE)),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor(config.COLOR_ROW_ALT)]),
    ]))
    
    story.append(schedule_table)
    doc.build(story)

# ---------------------------------------------------------
# DEPLOYMENT AND DELIVERY PIPELINE
# ---------------------------------------------------------
def upload_to_folder(service, folder_id):
    file_metadata = {
        'name': config.DRIVE_DISPLAY_NAME,
        'parents': [folder_id],
        'mimeType': 'application/pdf'
    }
    media = MediaFileUpload(config.PDF_FILENAME, mimetype='application/pdf', resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
    service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'reader'}).execute()
    return file.get('webViewLink')

def broadcast_emails(email_list, web_link):
    if not email_list:
        print("⚠️ Warning: No valid coach email addresses found in the sheet.")
        return

    try:
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        server.starttls()
        server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
        
        for email in email_list:
            msg = MIMEMultipart()
            msg['From'] = config.SENDER_EMAIL
            msg['To'] = email
            msg['Subject'] = f"PUFC Fall 2026: Updated Practice Schedule Released ({config.TIMESTAMP})"
            
            body = f"Hello Coach,\n\nAn updated version of the master club practice schedule has been compiled and saved.\n\nYou can access the live, mobile-friendly layout document using the direct link below:\n\n🔗 View Schedule: {web_link}\n\nBest regards,\nPUFC Club Administration"
            msg.attach(MIMEText(body, 'plain'))
            server.send_mail(config.SENDER_EMAIL, email, msg.as_string())
            print(f" 📧 Dispatched notification to: {email}")
            
        server.quit()
    except Exception as e:
        print(f"❌ Failed to broadcast notification emails: {str(e)}")

# ---------------------------------------------------------
# SCRIPT RUNNER ENTRYPOINT
# ---------------------------------------------------------
if __name__ == "__main__":
    mode = (sys.argv[1] if len(sys.argv) > 1 else "google").strip().lower()
    print(f"Step 1: Loading schedule data from {'local example CSV' if mode == 'local' else 'Google Sheet'}...")

    df_schedule, recipient_emails = fetch_schedule_and_emails(mode)
    create_pdf(df_schedule)
    print(f"PDF created at: {config.PDF_FILENAME}")

    if mode == 'local':
        print("Local mode selected; skipping Google Drive upload and email broadcast.")
    else:
        service = get_drive_service()
        folder_id = get_or_create_folder(service, config.FOLDER_NAME)
        web_link = upload_to_folder(service, folder_id)
        broadcast_emails(recipient_emails, web_link)
