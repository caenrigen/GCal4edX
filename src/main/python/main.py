from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import *

# GCal4edX dependencies
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from datetime import datetime, timedelta
import sys, os, tarfile, shutil, urllib.parse

# App modules
from MainWindow import *
from EventsBuilder import *
from GCalV3 import *
from Model import *

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

if __name__ == '__main__':
	appctxt = ApplicationContext()       # 1. Instantiate ApplicationContext

	# =========================
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

	credFile = appctxt.get_resource('credentials.json')
	gcalv3 = GCalV3(settingsDir, credFile)

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

	eventsBuilder = EventsBuilder()
	eventsBuilder.setDir(tmpOutputDir)
	eventsBuilder.setCalLang(lang)

	display_name = eventsBuilder.getCourseDisplayName()
	calName = 'MOOC Técnico: ' + display_name + ' (ed. ' + courseRun +')'
	gcalv3.setCalName(calName)
	gcalv3.createOrClearCal()

	eventsBuilder.buildAllEvents()
	print('    Found events:')
	[print(event) for event in eventsBuilder.events]

	print('    Creating events...')
	gcalv3.uploadEvents(eventsBuilder.events)

	print('    Calendar Name: '+ gcalv3.getCalName())
	print('    Calendar ID: '+ gcalv3.getCalId())

	print('    Calendar Public Link: ' + gcalv3.getCalPublikLink())
	print('    [NOTE: You must set the calendar to public!]')
	print('    NB: Subscribe to the calendar yourself!')

	# clean tmp dir
	shutil.rmtree(tmpOutputDir)

	# =========================

	window = MainWindowUI()
	window.show()

	exit_code = appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
	sys.exit(exit_code)
