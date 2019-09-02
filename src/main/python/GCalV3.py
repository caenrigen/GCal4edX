# GCal4edX dependencies
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import os, urllib.parse

class GCalV3(object):
	"""Performs necessary setup in order to use Google Calendar API v3"""
	def __init__(self, settingsDir, credFile):
		self.settingsDir = settingsDir
		self.credFile = credFile
		self.targetCalName = ''

		self.calendar = None		
		self.timeZone = 'Europe/Lisbon'

		self.sameNameCals = []

		# If modifying these scopes, delete the file token.pickle.
		self.scopes = ['https://www.googleapis.com/auth/calendar']

		self.creds = None
		# The file token.pickle stores the user's access and refresh tokens, and is
		# created automatically when the authorization flow completes for the first
		# time.
		self.tokenPath = os.path.join(settingsDir, 'token.pickle')
		if os.path.exists(self.tokenPath):
			with open(self.tokenPath, 'rb') as token:
				self.creds = pickle.load(token)
		# If there are no (valid) credentials available, let the user log in.
		if not self.creds or not self.creds.valid:
			if self.creds and self.creds.expired and self.creds.refresh_token:
				self.creds.refresh(Request())
			else:
				flow = InstalledAppFlow.from_client_secrets_file(self.credFile, self.scopes)
				self.creds = flow.run_local_server()
			# Save the credentials for the next run
			with open(self.tokenPath, 'wb') as token:
				pickle.dump(self.creds, token)

		self.service = build('calendar', 'v3', credentials=self.creds)

	def setCalName(self, name):
		self.targetCalName = name

	def getSameNameCals(self):
		calendars = self.service.calendarList().list().execute()['items']
		self.sameNameCals = []
		for cal in calendars:
			if cal['summary'] == self.targetCalName:
				self.sameNameCals.append(cal)
		return self.sameNameCals

	def setTargetCal(self, cal):
		self.calendar = cal

	def createGCal(self):
		calBody = {
		'summary': self.targetCalName,
		'timeZone': self.timeZone
		}
		self.calendar = self.service.calendars().insert(body=calBody).execute()

	def getAllEvents(self):
		page_token = None
		allEvents = []
		while True:
			events = self.service.events().list(calendarId=self.getCalId(), pageToken=page_token).execute()
			for event in events['items']:
				allEvents.append(event)
			page_token = events.get('nextPageToken')
			if not page_token:
				break
		return allEvents

	def clearEventsInCal(self, allEvents = None):
		if allEvents == None:
			allEvents = self.getAllEvents()
		for event in allEvents:
			self.service.events().delete(calendarId=self.getCalId(), eventId=event['id']).execute()

	def deleteEvent(self, event):
		self.service.events().delete(calendarId=self.getCalId(), eventId=event['id']).execute()

	def getCalName(self):
		return self.calendar['summary']

	def getCalId(self):
		return self.calendar['id']

	def getCalPublicLink(self):
		publicLinkPrefix='https://calendar.google.com/calendar/ical/'
		publicLinkSufix='/public/basic.ics'
		return publicLinkPrefix + urllib.parse.quote_plus(self.calendar['id']) + publicLinkSufix

	def uploadEvents(self, events):
		for event in events:
			self.service.events().insert(calendarId=self.getCalId(), body=event).execute()

	def uploadEvent(self, event):
		self.service.events().insert(calendarId=self.getCalId(), body=event).execute()

	def logout(self):
		if os.path.exists(self.tokenPath):
			os.unlink(self.tokenPath)
		
	def createOrClearCal(self):
		calendars = self.service.calendarList().list().execute()['items']
		# clear calendar if exists
		for cal in calendars:
			if cal['summary']==self.targetCalName:
				if not self.calendar:
					print('\"' + self.targetCalName + '\" calendar found.\nDeleting all events...')
					self.calendar = cal
					page_token = None
					allEvents = []
					while True:
						events = self.service.events().list(calendarId=self.getCalId(), pageToken=page_token).execute()
						for event in events['items']:
							allEvents.append(event)
						page_token = events.get('nextPageToken')
						if not page_token:
							break
					for event in allEvents:
						self.service.events().delete(calendarId=self.getCalId(), eventId=event['id']).execute()
						# print('Deleted event w/ id: '+event['id'])
				else:
					print('Found one more calendar with same name! Only the first was cleared!')
		
		if not self.calendar:
				print('Creating new calendar...')
				calBody = {
				'summary': self.targetCalName,
				'timeZone': self.timeZone
				}
				self.calendar = self.service.calendars().insert(body=calBody).execute()