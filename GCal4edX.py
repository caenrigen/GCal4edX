#! /usr/local/bin/python3

# Usefull documentation:
# https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/index.html
# https://developers.google.com/calendar/v3/reference/
# https://docs.python.org/3/library/xml.etree.elementtree.html#module-xml.etree.ElementTree

import pickle
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import sys, os, tarfile, shutil, xml.etree.ElementTree as ET, urllib.parse

def main():
	# If modifying these scopes, delete the file token.pickle.
	SCOPES = ['https://www.googleapis.com/auth/calendar']

	creds = None
	# The file token.pickle stores the user's access and refresh tokens, and is
	# created automatically when the authorization flow completes for the first
	# time.
	if os.path.exists('token.pickle'):
		with open('token.pickle', 'rb') as token:
			creds = pickle.load(token)
	# If there are no (valid) credentials available, let the user log in.
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(
				'credentials.json', SCOPES)
			creds = flow.run_local_server()
		# Save the credentials for the next run
		with open('token.pickle', 'wb') as token:
			pickle.dump(creds, token)

	service = build('calendar', 'v3', credentials=creds)

	if len(sys.argv) < 3:
		print('Usage: GCal4edX <tar file path> <course run>')
		return
	# get user input
	courseRun = sys.argv[-1]
	file = sys.argv[-2]

	absPath= os.path.abspath(file) 

	tmpOutputDir = '/tmp/GCal4edX-output'
	# clean tmp dir
	if os.path.exists(tmpOutputDir):
		shutil.rmtree(tmpOutputDir)
		os.makedirs(tmpOutputDir)
	else:
		os.makedirs(tmpOutputDir)

	os.chdir(tmpOutputDir)
	tar = tarfile.open(absPath)
	tar.extractall()
	tar.close()

	courseDir = './course/'
	courseFile = './course/course.xml'
	chapterDir = './chapter/'
	sequentialDir = './sequential/'

	os.chdir(courseDir)

	courseXML = ET.parse(courseFile)
	attrib = courseXML.getroot().attrib

	display_name = attrib.get('display_name').strip('\"')

	globalCourseEvents = [
	['Course start', attrib.get('start').strip('\"')],
	['Course end', attrib.get('end').strip('\"')],
	['Enrollment start', attrib.get('enrollment_start').strip('\"')],
	['Enrollment end', attrib.get('enrollment_end').strip('\"')]
	]

	calName = 'MOOC Técnico: ' + display_name + ' (ed. ' + courseRun +')'
	calendar = {
	'summary': calName,
	'timeZone': 'Europe/Lisbon'
	}

	created_calendar = None
	calendars = service.calendarList().list().execute()['items']
	# clear calendar if exists
	for cal in calendars:
		if cal['summary']==calName:
			if not created_calendar:
				print('\"' + calName + '\" calendar found.\nDeleting all events...')
				created_calendar = cal
				# service.calendars().clear(calendarId=cal['id'])
				page_token = None
				allEvents = []
				while True:
					events = service.events().list(calendarId=created_calendar['id'], pageToken=page_token).execute()
					for event in events['items']:
						allEvents.append(event)
					page_token = events.get('nextPageToken')
					if not page_token:
						break
				for event in allEvents:
					service.events().delete(calendarId=cal['id'], eventId=event['id']).execute()
					# print('Deleted event w/ id: '+event['id'])
			else:
				print('Found one more calendar with same name! Only the first was cleared!')
	
	if not created_calendar:
			print('Creating new calendar...')
			created_calendar = service.calendars().insert(body=calendar).execute()
	
	events = []

	for globalEvent in globalCourseEvents:
		event = buildAllDayEvent(globalEvent[0], globalEvent[1], globalEvent[1])
		events.append(event)

	titlePrefix = 'New Content: '
	os.chdir(chapterDir)
	for file in os.listdir('./'):
		if file.endswith('.xml'):
			attrib = ET.parse(file).getroot().attrib
			start = attrib.get('start')
			title = attrib.get('display_name')
			if start:
				start = start.strip('\"')
				title = titlePrefix + title.strip('\"')
				events.append(buildEvent(title, start, addHours(start,1)))
				events.append(buildAllDayEvent(title, start, start))
			else:
				print('    [Warning:] No start date found for chapter: '+ title + 'in file: ' + file + '.\n    You might need to change the date in Studio to a diffent one and back again.')

	titlePrefix = 'Deadline: '
	os.chdir('../'+sequentialDir)	
	for file in os.listdir('./'):
		if file.endswith('.xml'):
			attrib = ET.parse(file).getroot().attrib
			due = attrib.get('due')
			if due:
				due = due.strip('\"')
				title = titlePrefix + attrib.get('display_name').strip('\"')
				events.append(buildEvent(title, addHours(due,-6), due))
				events.append(buildAllDayEvent(title, due, due))

	print('    Found events:')
	[print(event) for event in events]

	print('    Creating events...')
	for event in events:
		service.events().insert(calendarId=created_calendar['id'], body=event).execute()

	print('    Calendar Name: '+ created_calendar['summary'])
	print('    Calendar ID: '+created_calendar['id'])

	publicLinkPrefix='https://calendar.google.com/calendar/ical/'
	publicLinkSufix='/public/basic.ics'
	publicLink = publicLinkPrefix + urllib.parse.quote_plus(created_calendar['id']) + publicLinkSufix
	print('    Calendar Public Link: ' + publicLink)
	print('    [NOTE: You must set the calendar to public!]')
	print('    NB: Subscribe to the calendar yourself!')

	# clean tmp dir
	shutil.rmtree(tmpOutputDir)

def buildEvent(title, startStr, endStr):
	return {
	'summary': title,
	'start': {'dateTime': startStr},
	'end': {'dateTime': endStr},
	'reminders': {
		'useDefault': False,
		'overrides': [
			{'method': 'email', 'minutes': 24 * 60}
			]
		}
	}

def buildAllDayEvent(title, startStr, endStr):
	dateFormat = '{:%Y-%m-%d}'
	return {
	'summary': title,
	'start': {'date': dateFormat.format(datetime.fromisoformat(startStr))},
	'end': {'date': dateFormat.format(datetime.fromisoformat(endStr))}
	}

def addHours(dateTimeStr, h):
	return (datetime.fromisoformat(dateTimeStr)+timedelta(hours=h)).isoformat()

if __name__ == '__main__':
	main()