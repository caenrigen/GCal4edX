import os, shutil, tarfile

# App modules
from EventsBuilder import *
from GCalV3 import *

class Model:
	def __init__( self, appctxt ):
		self.appctxt = appctxt
		self.tmpOutputDir = ''
		self.settingsDir = ''
		self.confDirs()

		self.courseTarFile = ''
		self.tarUnpacked = False

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


