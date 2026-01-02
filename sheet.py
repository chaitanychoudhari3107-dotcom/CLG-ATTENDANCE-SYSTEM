def connect_sheet():
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "credentials.json", scope
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(os.getenv("SHEET_ID")).sheet1
        return sheet
    except Exception as e:
        print("Google Sheets connection FAILED:", e)
        return None
  