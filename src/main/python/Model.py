import os
import shutil
import tarfile
import math
from PyQt5.QtCore import pyqtSignal, QObject, QThread

# App modules
from EventsBuilder import EventsBuilder
from GCalV3 import GCalV3
import logging

log = logging.getLogger(__name__)


class Model(QObject):
	progressChanged = pyqtSignal(int)
	maximumChanged = pyqtSignal(int)
	sameNameCalExists = pyqtSignal()
	eventsUploadSuccess = pyqtSignal()
	statusMsgChanged = pyqtSignal()

	def __init__(self, appctxt):
		super(Model, self).__init__()

		self.appctxt = appctxt
		self.tmpOutputDir = ''
		self.settingsDir = ''

		self.confDirs()

		self.courseTarFile = ''
		self.tarUnpacked = False

		self.lang = ''
		self.courseRun = ''
		self.courseName = ''
		self.calName = ''

		self.downloadedEvents = None # events that exist in the Google Calendar
		self.events = None # events to be uploaded into the Google Calendar

		self.credFile = appctxt.get_resource('credentials.json')
		self.gcalv3 = GCalV3(self.settingsDir, self.credFile)

		self.eventsBuilder = EventsBuilder()
		self.eventsBuilder.setDir(self.tmpOutputDir)

	@property
	def statusMsg(self):
		return self._statusMsg

	@statusMsg.setter
	def statusMsg(self, value):
		self._statusMsg = value
		self.statusMsgChanged.emit()

	def confDirs(self):
		# Create support dirs
		self.tmpOutputDir = os.path.join(
			self.appctxt.build_settings['tmp_dir'],
			self.appctxt.build_settings['app_name'])
		# clean tmp dir
		if os.path.exists(self.tmpOutputDir):
			shutil.rmtree(self.tmpOutputDir)
			os.makedirs(self.tmpOutputDir)
		else:
			os.makedirs(self.tmpOutputDir)

		self.settingsDir = os.path.join(
			os.path.expanduser(self.appctxt.build_settings['settings_dir']),
			self.appctxt.build_settings['app_name']
			)
		if not os.path.exists(self.settingsDir):
			os.makedirs(self.settingsDir)

	def setTarFileName(self, fileName):
		if self.isValid(fileName):
			self.courseTarFile = fileName
		else:
			self.courseTarFile = ''

	def isValid(self, fileName):
		try:
			file = open( fileName, 'r' )
			file.close()
			return True
		except:
			return False

	def unpackTar(self):
		self.statusMsg = 'Unpacking course file...'
		self.cleanTmp()
		try:
			os.chdir(self.tmpOutputDir)
			tar = tarfile.open(self.courseTarFile)
			tar.extractall()
			tar.close()
			self.tarUnpacked = True
		except Exception as e:
			raise e
		self.statusMsg = 'Course file unpacked'

	def cleanTmp(self):
		self.statusMsg = 'Cleaning temporary directory...'
		os.chdir(self.tmpOutputDir)
		for x in os.listdir():
			if os.path.isdir(x):
				shutil.rmtree(x)
			else:
				os.unlink(x)
		self.statusMsg = 'Temporary directory cleaned'

	def buildCalName(self):
		self.calName = 'MOOC Técnico: ' + self.courseName + ' (ed. ' + self.courseRun +')'

	def createCalUploadEvents(self):
		self.progressChanged.emit(0)
		self.statusMsg = 'Building all events...'
		self.eventsBuilder.setCalLang(self.lang)
		self.eventsBuilder.buildAllEvents()
		self.events = self.eventsBuilder.events

		self.statusMsg = 'Checking for calendar duplicates...'
		self.gcalv3.setCalName(self.calName)
		self.gcalv3.getSameNameCals()

		if len(self.gcalv3.sameNameCals) > 0:
			self.statusMsg = 'Found duplicate(s)!'
			self.sameNameCalExists.emit()
		else:
			self.statusMsg = 'Creating new calendar...'
			self.gcalv3.createGCal()

			self.maximumChanged.emit(len(self.events) - 1)
			self.statusMsg = 'Uploading events...'
			self.runWithExpBackOff(self.gcalv3.uploadEvent, self.events)

			self.statusMsg = 'Done!'
			self.eventsUploadSuccess.emit()

	def updateCalEvents(self):
		self.progressChanged.emit(0)
		self.statusMsg = 'Setting target calendar...'
		self.gcalv3.setTargetCal(self.gcalv3.sameNameCals[0])

		self.statusMsg = 'Downloading all events...'
		allEvents = self.gcalv3.getAllEvents()

		self.maximumChanged.emit(len(allEvents) - 1)

		self.statusMsg = 'Deleting all events in calendar...'
		self.runWithExpBackOff(self.gcalv3.deleteEvent, allEvents)

		events = self.events

		self.maximumChanged.emit(len(events) - 1)

		self.statusMsg = 'Uploading events...'
		self.runWithExpBackOff(self.gcalv3.uploadEvent, events)

		self.statusMsg = 'Done!'
		self.eventsUploadSuccess.emit()

	def runWithExpBackOff(self, func, events):
		i = 0
		expWaitCnt = 4 # Exponential back off when Google's server rise errors
		waitMs = 0
		numEvent = len(events)
		while i is not numEvent:
			self.progressChanged.emit(i)
			self.statusMsg = 'Processing event {}/{}'.format(i, numEvent)
			if waitMs is not 0:
				QThread.msleep(waitMs)
			try:
				func(events[i])
				i+=1
			except Exception as e:
				self.statusMsg = 'Error processing event. Trying again in {0:.2f}s'.format(waitMs/1000)
				expWaitCnt+=1
				waitMs = int(math.exp(expWaitCnt))
