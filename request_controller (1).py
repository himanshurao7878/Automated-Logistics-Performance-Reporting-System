import pygsheets
import subprocess
import smtplib
from email.message import EmailMessage
from datetime import datetime
import zipfile
from google.oauth2 import service_account
from googleapiclient.discovery import build

EMAIL = "himanshu.yadav@shipway.com"
PASSWORD = "gaqnjyfzzfktzisz"

# ------------------------------------------
# CONFIG
# ------------------------------------------
SERVICE_ACCOUNT_FILE = "client_secret.json"
REQUESTS_SHEET_KEY = "16mDNE7UgKKpsmEGwS0oD5SjeKll9g1ZRlsZsnhEMsZU"
REQUESTS_TAB = "Form responses 1"
OUTPUT_SHEET_KEY = "1xGqShurVl6YCCDKzeb3DRGTsSIGSaPr2ns_0mNHgm54"
# ------------------------------------------
# CONNECT
# ------------------------------------------
gc = pygsheets.authorize(service_file=SERVICE_ACCOUNT_FILE)
sh = gc.open_by_key(REQUESTS_SHEET_KEY)
wks = sh.worksheet_by_title(REQUESTS_TAB)

def zip_file(file_path):
    zip_path = file_path.replace(".csv", ".zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(file_path, arcname=file_path.split("\\")[-1])
    return zip_path


def export_sheet_as_xlsx(sheet_key, output_path):
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    drive_service = build("drive", "v3", credentials=creds)

    request = drive_service.files().export_media(
        fileId=sheet_key,
        mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    with open(output_path, "wb") as f:
        f.write(request.execute())

    print(f"Exported live Google Sheet to: {output_path}")

def send_report_email(to_email, company_id, zip_path, excel_path):
    msg = EmailMessage()
    msg["Subject"] = f"{company_id} - Performance Report"
    msg["From"] = EMAIL
    msg["To"] = to_email
    msg.set_content(
        f"Hi Team,\n\nPlease find the attached Performance Report.\n\n"
        f"✔ XLSX summary\n"
        f"✔ Raw data attached as ZIP\n\n"
        f"Regards,\nKAM Performance Automation"
    )

    for file_path in [zip_path, excel_path]:
        with open(file_path, "rb") as f:
            file_data = f.read()
            file_name = file_path.split("\\")[-1]

        msg.add_attachment(
            file_data,
            maintype="application",
            subtype="octet-stream",
            filename=file_name
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL, PASSWORD)
        smtp.send_message(msg)

    print(f"Email sent to {to_email} for Company ID {company_id}")

# ------------------------------------------
# READ ALL ROWS AS DICTIONARIES
# ------------------------------------------
records = wks.get_all_records()

# each record looks like:
# {'Timestamp': '...', 'Email address': '...', 'Company ID': '53276', 'Duration': 'This Month', 'Status': ''}

# ------------------------------------------
# FIND PENDING ROWS (Status is blank)
# ------------------------------------------
pending_rows = []

for i, row in enumerate(records):
    row_number = i + 2
    row = {k.strip(): v for k, v in row.items()}  # clean up header whitespace
    status = str(row.get("Status", "")).strip()

    if status == "":
        pending_rows.append({
            "row_number": row_number,
            "company_id": str(row.get("Company ID", "")).strip(),
            "email": row.get("Email address", "").strip(),
        })

# ------------------------------------------
# PRINT RESULTS (just for testing right now)
# ------------------------------------------
# ------------------------------------------
# RUN PERFORMANCE SCRIPT FOR EACH PENDING ROW
# ------------------------------------------
print(f"Total rows found: {len(records)}")
print(f"Pending rows found: {len(pending_rows)}")

for r in pending_rows:
    company_id = r["company_id"]

    if company_id == "":
        print(f"Skipping row {r['row_number']} — no Company ID found")
        continue

    print(f"\nProcessing row {r['row_number']} — Company ID: {company_id}")

    result = subprocess.run(
        ["python", "Performance.py", company_id],
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:
        print(f"ERROR while processing Company ID {company_id}:")
        print(result.stderr)
    else:
        print(f"Successfully processed Company ID {company_id}")

        today_str = datetime.today().strftime("%d-%m-%Y")
        csv_path = fr"C:\Seller_performance\seller_data\{company_id}_{today_str}.csv"
        excel_path = fr"C:\Seller_performance\seller_data\{company_id}_{today_str}_Performance.xlsx"

        try:
            zip_path = zip_file(csv_path)
            export_sheet_as_xlsx(OUTPUT_SHEET_KEY, excel_path)
            send_report_email(r["email"], company_id, zip_path, excel_path)

            # Mark this row as Done so it isn't reprocessed next run
            wks.update_value(f"E{r['row_number']}", "Done")
            print(f"Marked row {r['row_number']} as Done")

        except Exception as e:
            print(f"Failed to send email for Company ID {company_id}: {e}")