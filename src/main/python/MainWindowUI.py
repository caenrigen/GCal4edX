from PyQt5.QtWidgets import *
from PyQt5 import QtCore

# App modules
from MainWindow import *
from Model import *

class MainWindowUI(QMainWindow, Ui_MainWindow):
	def __init__(self, appctxt):
		super(MainWindowUI, self).__init__()
		self.setupUi(self)

		print('MainWindow id ->', int(QtCore.QThread.currentThreadId()))

		self.model = Model(appctxt)
		self.model.maximumChanged.connect(self.progressBar.setMaximum)
		self.model.progressChanged.connect(self.progressBar.setValue)
		self.model.sameNameCalExists.connect(self.confirmCalUpdate)

		self.createCalUploadEventsSig.connect(self.model.createCalUploadEvents)
		# self.model.processQtEvents.connect(self.QApplication.processEvents())

		self.thread = QtCore.QThread(self)
		self.model.moveToThread(self.thread)
		self.thread.start()

		# ===
		self.browseSlot()
		# ===

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

	# SLOTS
	@QtCore.pyqtSlot()
	def confirmCalUpdate(self):
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

	@QtCore.pyqtSlot()
	def createCalendarSlot(self):
		self.model.lang = self.comboBox.currentText()
		self.model.courseRun = self.lineEdit.text()
		self.model.courseName = self.lineEdit_4.text()
		self.model.buildCalName()

		QtCore.QTimer.singleShot(0, self.model.createCalUploadEvents)

		# self.model.eventsBuilder.setCalLang(lang)
		# self.model.eventsBuilder.buildAllEvents()

		# self.model.gcalv3.setCalName(calName)
		# cals = self.model.gcalv3.getSameNameCals()
		# if len(cals) > 0:
		# 	self.confirmCalUpdate() # Freezes de code here
		# 	if self.updateCalOK:
		# 		self.model.gcalv3.setTargetCal(cals[0])
		# 		# self.model.gcalv3.clearEventsInCal()
		# 		allEvents = self.model.gcalv3.getAllEvents()
				
		# 		print(len(allEvents))
		# 		self.maximumChanged.emit(len(allEvents))

		# 		for i, event in enumerate(allEvents):
		# 			print('Deleting event: ' + event['id'])

		# 			self.progressChanged.emit(i)

		# 			# self.model.gcalv3.deleteEvent(event)

		# 		events = self.model.eventsBuilder.events

		# 		self.maximumChanged.emit(len(events))

		# 		print('Uploading events...')
		# 		for i, event in enumerate(events):
		# 			print(event)

		# 			self.progressChanged.emit(i)
					
		# 			# self.model.gcalv3.uploadEvent(event)
		# 		# self.model.gcalv3.uploadEvents(self.model.eventsBuilder.events)
		# else:
		# 	self.model.gcalv3.createGCal()
		# 	print('Uploading events...')
		# 	for i, event in enumerate(events):
		# 		print(event)

		# 		self.progressChanged.emit(i)

		# 		self.model.gcalv3.uploadEvent(event)
		# 	# self.model.gcalv3.uploadEvents(self.model.eventsBuilder.events)
	@QtCore.pyqtSlot()
	def browseSlot(self):
		# self.openFileNameDialog()
		# ===
		self.model.setTarFileName('/Users/Victor/Documents/ProjectsDev/GCal4edX/course.jAoyT2.tar.gz')
		# ===
		self.lineEdit_3.setText(self.model.courseTarFile)
		self.model.unpackTar()
		self.lineEdit_4.setText(self.model.eventsBuilder.getCourseDisplayName())
	@QtCore.pyqtSlot()
	def settingsChangedSlot(self):
		if self.lineEdit.text() != '' and self.model.tarUnpacked:
			self.pushButton_2.setEnabled(True)
		else:
			self.pushButton_2.setDisabled(True)
	@QtCore.pyqtSlot()
	def confirmCalUpdateSlot(self, button):
		if button.text() == 'OK':
			self.model.updateCalEvents()

