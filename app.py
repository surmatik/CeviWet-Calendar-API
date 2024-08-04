from flask import Flask, request, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime

app = Flask(__name__)

# Google Cloud API Credentials
SERVICE_ACCOUNT_FILE = 'credentials.json'

# Scopes
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('calendar', 'v3', credentials=credentials)

# Calendar-IDs
CALENDARS = {
    'leitende': 'web.cevi.wetzikon@gmail.com',
    'public': '0b64df5b9151fac2d93d5166185ec0ca8ebce838861ce5c8fe220ac112d84b9f@group.calendar.google.com'
}

def format_datetime(date_time_str):
    """Formatieren Sie das Datum und die Zeit im gewünschten Format."""
    dt = datetime.datetime.fromisoformat(date_time_str.replace('Z', '+00:00'))
    return dt.strftime('%d.%m.%Y'), dt.strftime('%H:%M')

def get_next_event_with_keyword(service, calendar_id, keyword):
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(calendarId=calendar_id, timeMin=now,
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    for event in events:
        if keyword.lower() in event['summary'].lower():
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            start_date, start_time = format_datetime(start)
            end_date, end_time = format_datetime(end) if end else (start_date, None)
            
            time_range = f"{start_time} – {end_time}" if end_time else start_time
            
            return {
                'summary': event['summary'],
                'datum': start_date,
                'zeit': time_range
            }
    return None

@app.route('/api/v1/next_nachmittagsprogramm', methods=['GET'])
def next_nachmittagsprogramm():
    calendar_type = request.args.get('calendar_type')
    
    if calendar_type not in CALENDARS:
        return jsonify({'error': 'Bitte geben Sie einen gültigen calendar_type an.'}), 400
    
    calendar_id = CALENDARS[calendar_type]
    keyword = 'Nachmittagsprogramm'
    event_details = get_next_event_with_keyword(service, calendar_id, keyword)
    
    if event_details:
        return jsonify(event_details)
    else:
        return jsonify({'message': f"Kein Termin mit '{keyword}' im Titel gefunden."}), 404

if __name__ == '__main__':
    app.run(debug=True)
