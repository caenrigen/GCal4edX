from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

# App modules
from MainWindow import *
from CalendarCreatedDialog import *
from Model import *


class CalendarCreatedDialogUI(QDialog, Ui_CalendarCreatedDialog):

	def __init__(self):
		super(CalendarCreatedDialogUI, self).__init__()
		self.setupUi(self)
		self.clipboard = QApplication.clipboard()

		self.pushButton.pressed.connect(self.nameToClipboard)
		self.pushButton_2.pressed.connect(self.idToClipboard)
		self.pushButton_3.pressed.connect(self.linkToClipboard)

	# SLOTS
	@pyqtSlot()
	def nameToClipboard(self):
		self.clipboard.setText(self.lineEdit.text())

	@pyqtSlot()
	def idToClipboard(self):
		self.clipboard.setText(self.lineEdit_2.text())

	@pyqtSlot()
	def linkToClipboard(self):
		self.clipboard.setText(self.lineEdit_3.text())


class MainWindowUI(QMainWindow, Ui_MainWindow):
	def __init__(self, appctxt):
		super(MainWindowUI, self).__init__()
		self.setupUi(self)

		self.statusLabel = QLabel()
		self.statusLabel.setText('Hi, there!')
		self.statusbar.addWidget(self.statusLabel)

		self.model = Model(appctxt)
		self.model.maximumChanged.connect(self.progressBar.setMaximum)
		self.model.progressChanged.connect(self.progressBar.setValue)
		self.model.sameNameCalExists.connect(self.confirmCalUpdate)
		self.model.eventsUploadSuccess.connect(self.eventsUploadSuccessSlot)
		self.model.statusMsgChanged.connect(self.modelStatusChangeSlot)

		self.thread = QThread(self)
		self.model.moveToThread(self.thread)
		self.thread.start()

	def setupUi(self, mainWindow):
		super().setupUi(mainWindow)

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
	@pyqtSlot()
	def modelStatusChangeSlot(self):
		self.statusLabel.setText(self.model.statusMsg)

	@pyqtSlot()
	def confirmCalUpdate(self):
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Warning)
		msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
		msg.setText("Update existing calendar?")
		msg.setInformativeText("A Google calendar with the same name already exists in your account.\nClicking OK will delete all existing events and create the new events.")
		msg.setWindowTitle("Update calendar?")
		msg.setModal(True)
		msg.buttonClicked.connect(self.confirmCalUpdateSlot)
		msg.show()

		retVal = msg.exec_()

	@pyqtSlot()
	def createCalendarSlot(self):
		self.model.lang = self.comboBox.currentText()
		self.model.courseRun = self.lineEdit.text()
		self.model.courseName = self.lineEdit_4.text()
		self.model.buildCalName()

		QTimer.singleShot(0, self.model.createCalUploadEvents)

	@pyqtSlot()
	def browseSlot(self):
		self.openFileNameDialog()
		self.lineEdit_3.setText(self.model.courseTarFile)
		self.model.unpackTar()
		self.lineEdit_4.setText(self.model.eventsBuilder.getCourseDisplayName())

	@pyqtSlot()
	def settingsChangedSlot(self):
		if self.lineEdit.text() != '' and self.model.tarUnpacked:
			self.pushButton_2.setEnabled(True)
		else:
			self.pushButton_2.setDisabled(True)

	@pyqtSlot(QAbstractButton)
	def confirmCalUpdateSlot(self, button):
		if button.text() == 'OK':
			QTimer.singleShot(0, self.model.updateCalEvents)

	@pyqtSlot()
	def eventsUploadSuccessSlot(self):
		dialog = CalendarCreatedDialogUI()
		dialog.lineEdit.setText(self.model.gcalv3.getCalName())
		dialog.lineEdit_2.setText(self.model.gcalv3.getCalId())
		dialog.lineEdit_3.setText(self.model.gcalv3.getCalPublicLink())

		dialog.setModal(True)

		dialog.show()

		retVal = dialog.exec_()

	@pyqtSlot()
	def advancedSettingsChangedSlot(self):
		eb = self.model.eventsBuilder
		eb.emailReminderBeforeH = self.spinBox_3.value()
		eb.eventDurationH = self.spinBox.value()
		eb.defaultReminders = not self.groupBox_6.isChecked()
		eb.deadlineDurationH = self.spinBox_2.value()
		eb.createAllDayEvents = self.checkBox.isChecked()

	@pyqtSlot()
	def logoutSlot(self):
		self.model.gcalv3.logout()
		QApplication.exit()