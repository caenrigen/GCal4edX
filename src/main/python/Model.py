import os, shutil, tarfile
from PyQt5 import QtCore

# App modules
from EventsBuilder import *
from GCalV3 import *

class Model(QtCore.QObject):
	progressChanged = QtCore.pyqtSignal(int)
	maximumChanged = QtCore.pyqtSignal(int)
	sameNameCalExists = QtCore.pyqtSignal()

	def __init__(self, appctxt):
		super(Model, self).__init__()

		print('Model id ->', int(QtCore.QThread.currentThreadId()))

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
		self.cleanTmp()
		try:
			os.chdir(self.tmpOutputDir)
			tar = tarfile.open(self.courseTarFile)
			tar.extractall()
			tar.close()
			self.tarUnpacked = True
		except Exception as e:
			raise e

	def cleanTmp(self):
		os.chdir(self.tmpOutputDir)
		for x in os.listdir():
			if os.path.isdir(x):
				shutil.rmtree(x)
			else:
				os.unlink(x)

	def buildCalName(self):
		self.calName = 'MOOC Técnico: ' + self.courseName + ' (ed. ' + self.courseRun +')'

	def createCalUploadEvents(self):

		print('Model id ->', int(QtCore.QThread.currentThreadId()))

		self.eventsBuilder.setCalLang(self.lang)
		self.eventsBuilder.buildAllEvents()
		self.events = self.eventsBuilder.events

		self.gcalv3.setCalName(self.calName)
		# ===
		# cals = self.gcalv3.getSameNameCals()
		cals = []
		# ===
		if len(cals) > 0:
			self.sameNameCalExists.emit()
			# self.confirmCalUpdate() # Freezes de code here
		# 	if self.updateCalOK:
		# 		self.gcalv3.setTargetCal(cals[0])
		# 		# self.gcalv3.clearEventsInCal()
		# 		allEvents = self.gcalv3.getAllEvents()
				
		# 		print(len(allEvents))
		# 		self.maximumChanged.emit(len(allEvents))

		# 		for i, event in enumerate(allEvents):
		# 			print('Deleting event: ' + event['id'])

		# 			self.progressChanged.emit(i)

		# 			# self.gcalv3.deleteEvent(event)

		# 		events = self.eventsBuilder.events

		# 		self.maximumChanged.emit(len(events))

		# 		print('Uploading events...')
		# 		for i, event in enumerate(events):
		# 			print(event)

		# 			self.progressChanged.emit(i)
					
		# 			# self.gcalv3.uploadEvent(event)
		# 		# self.gcalv3.uploadEvents(self.eventsBuilder.events)
		else:
			# self.gcalv3.createGCal()
			print('Uploading events...')
			self.maximumChanged.emit(len(self.events) - 1)
			for i, event in enumerate(self.events):
				print(event)

				self.progressChanged.emit(i)
				QtCore.QThread.msleep(100)
				# self.gcalv3.uploadEvent(event)

	def updateCalEvents(self):
		print('updateCalEvents()')
		pass
