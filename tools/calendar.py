from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import GOOGLE_CALENDAR_CREDENTIALS_FILE, GOOGLE_CALENDAR_TOKEN_FILE
from utils import get_logger
import os
import pickle
import datetime

logger = get_logger(__name__)

class CalendarManager:
    def __init__(self):
        self.credentials = None
        self.service = None
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']

    def authenticate(self):
        """Authenticate with Google Calendar API"""
        try:
            if os.path.exists(GOOGLE_CALENDAR_TOKEN_FILE):
                with open(GOOGLE_CALENDAR_TOKEN_FILE, 'rb') as token:
                    self.credentials = pickle.load(token)

            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        GOOGLE_CALENDAR_CREDENTIALS_FILE, self.SCOPES)
                    self.credentials = flow.run_local_server(port=0)

                with open(GOOGLE_CALENDAR_TOKEN_FILE, 'wb') as token:
                    pickle.dump(self.credentials, token)

            self.service = build('calendar', 'v3', credentials=self.credentials)
            logger.info("Successfully authenticated with Google Calendar")
            
        except Exception as e:
            logger.error(f"Error authenticating with Google Calendar: {str(e)}")
            raise

    def create_event(self, summary, start_time, end_time, description=None, location=None):
        """Create a new calendar event"""
        try:
            if not self.service:
                self.authenticate()

            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'Asia/Seoul',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'Asia/Seoul',
                },
            }

            if description:
                event['description'] = description
            if location:
                event['location'] = location

            event = self.service.events().insert(calendarId='primary', body=event).execute()
            logger.info(f"Created calendar event: {summary}")
            return event

        except Exception as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            raise

    def get_events(self, start_time=None, end_time=None, max_results=10):
        """Get calendar events for a time period"""
        try:
            if not self.service:
                self.authenticate()

            if not start_time:
                start_time = datetime.datetime.utcnow()
            if not end_time:
                end_time = start_time + datetime.timedelta(days=7)

            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_time.isoformat() + 'Z',
                timeMax=end_time.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            logger.info(f"Retrieved {len(events)} calendar events")
            return events

        except Exception as e:
            logger.error(f"Error getting calendar events: {str(e)}")
            raise

    def delete_event(self, event_id):
        """Delete a calendar event"""
        try:
            if not self.service:
                self.authenticate()

            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            logger.info(f"Deleted calendar event: {event_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting calendar event: {str(e)}")
            raise 