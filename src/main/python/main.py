from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import *

# GCal4edX dependencies
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from datetime import datetime, timedelta
import sys, os, tarfile, shutil, xml.etree.ElementTree as ET, urllib.parse
from MainWindow import *

# from mainWindow import *

# class mainWindow(QtWidgets.QWidget):
# 	def __init__(self, parent=None):
# 		QtWidgets.QWidget.__init__(self, parent)
# 		self.ui = Ui_mainWindow()
# 		# self.ui.pushButton.clicked.connect(onButtonClicked)
# 		self.ui.setupUi(self)

class GCalV3(object):
	"""Performs necessary setup in order to use Google Calendar API v3"""
	def __init__(self, settingsDir, appctxt):
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
				flow = InstalledAppFlow.from_client_secrets_file(
					appctxt.get_resource('credentials.json'), self.scopes)
				self.creds = flow.run_local_server()
			# Save the credentials for the next run
			with open(self.tokenPath, 'wb') as token:
				pickle.dump(self.creds, token)

		self.service = build('calendar', 'v3', credentials=self.creds)

class MainWindowUI(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # self.model = Model()

    def setupUi(self, mainWindow):
        super().setupUi(mainWindow)

    def debugPrint(self, msg):
        self.textEdit.append(msg)

    def refreshAll(self):
        self.lineEdit.setText(self.model.getFileName())
        self.textEdit.setText(self.model.getFileContents())

    @QtCore.pyqtSlot()
    def createCalendarSlot(self):
        pass
        # self.debugPrint('Creat Calendar pressed')

    @QtCore.pyqtSlot()
    def browseSlot(self):
        onButtonClicked()
        # self.debugPrint('Browse button pressed')

def onButtonClicked():
	alert = QMessageBox()
	alert.setText('YEY!!')
	alert.exec_()

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

# XML parsing functions
def getCourseDisplayName(courseFilePath):
	courseXML = ET.parse(courseFilePath)
	attrib = courseXML.getroot().attrib

	return attrib.get('display_name').strip('\"')

def appendGlobalEvents(courseFilePath, events):
	courseXML = ET.parse(courseFilePath)
	attrib = courseXML.getroot().attrib

	globalCourseEvents = [
	['Course start', attrib.get('start').strip('\"')],
	['Course end', attrib.get('end').strip('\"')],
	['Enrollment start', attrib.get('enrollment_start').strip('\"')],
	['Enrollment end', attrib.get('enrollment_end').strip('\"')]
	]

	for globalEvent in globalCourseEvents:
		event = buildAllDayEvent(globalEvent[0], globalEvent[1], globalEvent[1])
		events.append(event)

	return events

def appendNewContentsEvents(chapterDir, events, eventDurationH=1, createAllDayEvents=True):
	titlePrefix = {'en':'New Content','pt': 'Novos Conteúdos'}
	os.chdir(chapterDir)
	for file in os.listdir('./'):
		if file.endswith('.xml'):
			attrib = ET.parse(file).getroot().attrib
			start = attrib.get('start')
			title = attrib.get('display_name')
			if start:
				start = start.strip('\"')
				title = titlePrefix[lang] + ': ' + title.strip('\"')
				events.append(buildEvent(title, start, addHours(start,eventDurationH)))
				if createAllDayEvents:
					events.append(buildAllDayEvent(title, start, start))
			else:
				print('    [Warning:] No start date found for chapter: '+ title + 'in file: ' + file + '.\n    You might need to change the date in Studio to a diffent one and back again.')
	return events

def appendDeadlineEvents(sequentialDir, events, deadlineDurationH=6, createAllDayEvents=True):
	# Deadlines for subsections
	titlePrefix = {'en': 'Deadline', 'pt': 'Fim de prazo'}
	os.chdir(sequentialDir)
	for file in os.listdir('./'):
		if file.endswith('.xml'):
			attrib = ET.parse(file).getroot().attrib
			due = attrib.get('due')
			if due:
				due = due.strip('\"')
				title = titlePrefix[lang] + ': ' + attrib.get('display_name').strip('\"')
				events.append(buildEvent(title, addHours(due, - deadlineDurationH), due))
				if createAllDayEvents:
					events.append(buildAllDayEvent(title, due, due))
	return events

def appendPeerReviewEvents(verticalDir, events, createAllDayEvents=True, eventDurationH=1, deadlineDurationH=6):
	# Peer Review
	titlePrefixSubStart = {'en': 'Response submission opened', 'pt': 'Início submissão de respostas'}
	titlePrefixSubDue   = {'en': 'Response submission deadline', 'pt': 'Fim de prazo submissão de respostas'}
	titlePrefixPAstart  = {'en': 'Peer assessment start', 'pt': 'Início avaliação dos pares'}
	titlePrefixPAdue    = {'en': 'Peer assessment deadline', 'pt': 'Fim de prazo avaliação dos pares'}
	os.chdir(verticalDir)
	for file in os.listdir('./'):
		if file.endswith('.xml'):
			root = ET.parse(file).getroot()
			for PR in root.iter('openassessment'):
				PRtitle = PR.find('title').text
				attrib = PR.attrib
				sub_start = attrib.get('submission_start')
				sub_due = attrib.get('submission_due')
				if sub_start:
					sub_start = sub_start.strip('\"')
					title = titlePrefixSubStart[lang] + ': ' + PRtitle
					events.append(buildEvent(title, sub_start, addHours(sub_start, eventDurationH)))
					events.append(buildAllDayEvent(title, sub_start, sub_start))
				if sub_due:
					sub_due = sub_due.strip('\"')
					title = titlePrefixSubDue[lang] + ': ' + PRtitle
					events.append(buildEvent(title, addHours(sub_due, - deadlineDurationH), sub_due))
					events.append(buildAllDayEvent(title, sub_due, sub_due))
				for assessments in PR.findall('assessments'):
					for assessment in assessments.findall('assessment'):
						PAattrib = assessment.attrib
						PAstart = PAattrib.get('start')
						PAdue = PAattrib.get('due')
						if PAstart:
							PAstart = PAstart.strip('\"')
							title = titlePrefixPAstart[lang] + ': ' + PRtitle
							events.append(buildEvent(title, PAstart, addHours(PAstart, eventDurationH)))
							events.append(buildAllDayEvent(title, PAstart, PAstart))
						if PAdue:
							PAdue = PAdue.strip('\"')
							title = titlePrefixPAdue[lang] + ': ' + PRtitle
							events.append(buildEvent(title, addHours(PAdue, - deadlineDurationH), PAdue))
							events.append(buildAllDayEvent(title, PAdue, PAdue))

if __name__ == '__main__':
	appctxt = ApplicationContext()       # 1. Instantiate ApplicationContext

	# Create support dirs
	tmpOutputDir = os.path.join(
		appctxt.build_settings['tmp_dir'],
		appctxt.build_settings['app_name'])
	# clean tmp dir
	if os.path.exists(tmpOutputDir):
		shutil.rmtree(tmpOutputDir)
		os.makedirs(tmpOutputDir)
	else:
		os.makedirs(tmpOutputDir)
	
	settingsDir = os.path.join(
		os.path.expanduser(appctxt.build_settings['settings_dir']),
		appctxt.build_settings['app_name']
		)
	if not os.path.exists(settingsDir):
		os.makedirs(settingsDir)

	gcalv3 = GCalV3(settingsDir, appctxt)
	service = gcalv3.service

# ====
	# get user input
	lang = "en"
	courseRun = "2020"
	# file = "course.MBoeOd.tar.gz"
	file = 'course.jAoyT2.tar.gz'

	absPath= os.path.abspath(file) 

	os.chdir(tmpOutputDir)
	tar = tarfile.open(absPath)
	tar.extractall()
	tar.close()

	courseDir = os.path.join(tmpOutputDir, 'course')
	courseFile = os.path.join(courseDir, 'course', 'course.xml')
	chapterDir = os.path.join(courseDir, 'chapter')
	sequentialDir = os.path.join(courseDir, 'sequential')
	verticalDir = os.path.join(courseDir, 'vertical')


	display_name = getCourseDisplayName(courseFile)
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

	# os.chdir(courseDir)

	events = []
	appendGlobalEvents(courseFile, events)
	appendNewContentsEvents(chapterDir, events)
	appendDeadlineEvents(sequentialDir, events)
	appendPeerReviewEvents(verticalDir, events)

	print('    Found events:')
	[print(event) for event in events]

	print('    Creating events...')
	# for event in events:
	# 	service.events().insert(calendarId=created_calendar['id'], body=event).execute()

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

	# =========================
	#app = QApplication([])
	# window = QWidget()
	# appctxt.app.setStyle('Macintosh')
	# layout = QVBoxLayout()
	# button = QPushButton('Create Calendar')
	# button.clicked.connect(onButtonClicked)
	# layout.addWidget(button)
	# window.setLayout(layout)
	# window.show()
	window = MainWindowUI()
	window.show()

	exit_code = appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
	sys.exit(exit_code)
