from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields, Namespace
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime

app = Flask(__name__)
api = Api(app, version='1.0', title='Cevi Wetzikon API',
          description='A simple API for accessing calendar events')

# Define the Namespace
ns = Namespace('calendar', description='Operations related to calendar events')

api.add_namespace(ns)

# Google Cloud API Credentials
SERVICE_ACCOUNT_FILE = 'credentials.json'
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
    """Format datetime to desired format."""
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

# Define a model for the query parameter
calendar_type_model = ns.model('CalendarType', {
    'calendar_type': fields.String(required=True, description='The type of calendar to query. Options: "leitende", "public"')
})

@ns.route('/next_nachmittagsprogramm')
class NextNachmittagsprogramm(Resource):
    @ns.expect(calendar_type_model, validate=True)
    def get(self):
        """Get the next event with 'Nachmittagsprogramm' in the title."""
        calendar_type = request.args.get('calendar_type')
        
        if calendar_type not in CALENDARS:
            return {'error': 'Please provide a valid calendar_type.'}, 400

        calendar_id = CALENDARS[calendar_type]
        keyword = 'Nachmittagsprogramm'
        event_details = get_next_event_with_keyword(service, calendar_id, keyword)

        if event_details:
            return event_details
        else:
            return {'message': f"No event with '{keyword}' in the title found."}, 404

if __name__ == '__main__':
    app.run(debug=True)
