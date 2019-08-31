from PyQt5.QtWidgets import *

# App modules
from MainWindow import *
from Model import *

class MainWindowUI(QMainWindow, Ui_MainWindow):
	def __init__(self, appctxt):
		super().__init__()
		self.setupUi(self)
		self.model = Model(appctxt)

		self.updateCalOK = False

	def setupUi(self, mainWindow):
		super().setupUi(mainWindow)

	# def debugPrint(self, msg):
	# 	self.textEdit.append(msg)

	# def refreshAll(self):
	# 	self.lineEdit.setText(self.model.getFileName())
	# 	self.textEdit.setText(self.model.getFileContents())

	def openFileNameDialog(self):
		options = QFileDialog.Options()
		# options |= QFileDialog.DontUseNativeDialog
		fileName, _ = QFileDialog.getOpenFileName(self,
			"QFileDialog.getOpenFileName()",
			"",
			"edX Course Export Files (*.tar.gz);;All Files (*)",
			options=options)
		self.model.setTarFileName(fileName)

	def confirmCalUpdate(self):
		print('confirmCalUpdate called')

		msg = QMessageBox()
		msg.setIcon(QMessageBox.Question)
		msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
		msg.setText("Update existing calendar?")
		msg.setInformativeText("A Google calendar with the same name already exists in your account.\nClicking OK will delete all existing events and create the new events.")
		msg.setWindowTitle("Update calendar?")
		msg.setModal(True)
		msg.buttonClicked.connect(self.confirmCalUpdateSlot)
		msg.show()

		retval = msg.exec_()

	# SLOTS
	def createCalendarSlot(self):
		lang = self.comboBox.currentText()
		courseRun = self.lineEdit.text()
		calName = 'MOOC Técnico: ' + self.lineEdit_4.text() + ' (ed. ' + courseRun +')'

		self.model.eventsBuilder.setCalLang(lang)
		self.model.eventsBuilder.buildAllEvents()

		self.model.gcalv3.setCalName(calName)
		cals = self.model.gcalv3.getSameNameCals()
		if len(cals) > 0:
			self.confirmCalUpdate() # Freezes de code here
			if self.updateCalOK:
				self.model.gcalv3.setTargetCal(cals[0])
				self.model.gcalv3.clearEventsInCal()
				print('Uploading events...')
				# self.model.gcalv3.uploadEvents(self.model.eventsBuilder.events)
		else:
			self.model.gcalv3.createGCal()
			print('Uploading events...')
			# self.model.gcalv3.uploadEvents(self.model.eventsBuilder.events)

	def browseSlot(self):
		self.openFileNameDialog()
		self.lineEdit_3.setText(self.model.courseTarFile)
		self.model.unpackTar()
		self.lineEdit_4.setText(self.model.eventsBuilder.getCourseDisplayName())

	def settingsChangedSlot(self):
		if self.lineEdit.text() != '' and self.model.tarUnpacked:
			self.pushButton_2.setEnabled(True)
		else:
			self.pushButton_2.setDisabled(True)

	def confirmCalUpdateSlot(self, button):
		if button.text() == 'OK':
			self.updateCalOK = True
		else:
			self.updateCalOK = False

