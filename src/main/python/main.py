from fbs_runtime.application_context.PyQt5 import ApplicationContext

# GCal4edX dependencies
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from datetime import datetime, timedelta
import sys, shutil

# App modules
from MainWindowUI import *
from GCalV3 import *
from Model import *

if __name__ == '__main__':
	appctxt = ApplicationContext()       # 1. Instantiate ApplicationContext

	window = MainWindowUI(appctxt)
	window.show()

	# print('    Calendar Name: '+ model.gcalv3.getCalName())
	# print('    Calendar ID: '+ model.gcalv3.getCalId())

	# print('    Calendar Public Link: ' + model.gcalv3.getCalPublikLink())
	# print('    [NOTE: You must set the calendar to public!]')
	# print('    NB: Subscribe to the calendar yourself!')

	exit_code = appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
	# clean tmp dir
	shutil.rmtree(window.model.tmpOutputDir)
	sys.exit(exit_code)
