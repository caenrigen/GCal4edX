from datetime import datetime, timedelta
import os
import xml.etree.ElementTree as ET
import logging

log = logging.getLogger(__name__)


class EventsBuilder(object):
    def __init__(
        self,
        createAllDayEvents=True,
        eventDurationH=1,
        deadlineDurationH=6,
        defaultReminders=False,
        emailReminderBeforeH=24,
    ):
        self.emailReminderBeforeH = emailReminderBeforeH
        self.eventDurationH = eventDurationH
        self.createAllDayEvents = createAllDayEvents
        self.deadlineDurationH = deadlineDurationH
        self.defaultReminders = defaultReminders

        # To be set up later
        self.tmpOutputDir = ""
        self.courseDir = ""
        self.courseFile = ""
        self.chapterDir = ""
        self.sequentialDir = ""
        self.verticalDir = ""

        self.lang = ""

        self.events = []

    def setDir(self, tmpOutputDir):
        self.tmpOutputDir = tmpOutputDir
        self.courseDir = os.path.join(self.tmpOutputDir, "course")
        self.courseFile = os.path.join(self.courseDir, "course", "course.xml")
        self.chapterDir = os.path.join(self.courseDir, "chapter")
        self.sequentialDir = os.path.join(self.courseDir, "sequential")
        self.verticalDir = os.path.join(self.courseDir, "vertical")

    def setCalLang(self, lang):
        self.lang = lang

    def appendEvent(self, title, startStr, endStr):
        self.events.append(
            {
                "summary": title,
                "start": {"dateTime": startStr},
                "end": {"dateTime": endStr},
                "reminders": {
                    "useDefault": self.defaultReminders,
                    "overrides": [
                        {"method": "email", "minutes": self.emailReminderBeforeH * 60}
                    ],
                },
            }
        )

    def getCourseDisplayName(self):
        courseXML = ET.parse(self.courseFile)
        attrib = courseXML.getroot().attrib
        display_name = attrib.get("display_name") or ""
        return display_name

    def addHours(self, dateTimeStr, h):
        return (datetime.fromisoformat(dateTimeStr) + timedelta(hours=h)).isoformat()

    def getSequentialOfVertical(self, verticalFile):
        verticalName = os.path.splitext(os.path.basename(verticalFile))[0]
        os.chdir(self.sequentialDir)
        for file in [os.path.abspath(filebase) for filebase in os.listdir()]:
            if file.endswith(".xml"):
                root = ET.parse(file).getroot()
                for vertical in root.iter("vertical"):
                    if vertical.attrib.get("url_name") == verticalName:
                        return os.path.abspath(file)
        return None

    def getChapterOfSequential(self, sequentialFile):
        sequentialName = os.path.splitext(os.path.basename(sequentialFile))[0]
        os.chdir(self.chapterDir)
        for file in [os.path.abspath(filebase) for filebase in os.listdir()]:
            if file.endswith(".xml"):
                root = ET.parse(file).getroot()
                for vertical in root.iter("sequential"):
                    if vertical.attrib.get("url_name") == sequentialName:
                        return os.path.abspath(file)
        return None

    def isStaffOnly(self, verticalName):
        # expects abspath
        try:
            attrib = ET.parse(verticalName).getroot().attrib
            if attrib.get("visible_to_staff_only") == "true":
                return True

            seq = self.getSequentialOfVertical(verticalName)
            attrib = ET.parse(seq).getroot().attrib
            if attrib.get("visible_to_staff_only") == "true":
                return True

            chap = self.getChapterOfSequential(seq)
            attrib = ET.parse(chap).getroot().attrib
            if attrib.get("visible_to_staff_only") == "true":
                return True

            return False
        except Exception as e:
            log.warning('Problem verifying if unit is staff only.\n{}'.format(e))
            return False

    def buildAllEvents(self):
        self.events = []
        self.appendGlobalEvents()
        self.appendNewContentsEvents()
        self.appendDeadlineEvents()
        self.appendPeerReviewEvents()

    def appendAllDayEvent(self, title, startStr, endStr):
        dateFormat = "{:%Y-%m-%d}"
        try:
            self.events.append(
                {
                    "summary": title,
                    "start": {"date": dateFormat.format(datetime.fromisoformat(startStr))},
                    "end": {"date": dateFormat.format(datetime.fromisoformat(endStr))},
                }
            )
        except Exception as e:
            log.warning('Failed creating event "{}", start: {}, end: {}\n{}'.format(title, startStr, endStr, e))

    def appendGlobalEvents(self):
        courseXML = ET.parse(self.courseFile)
        attrib = courseXML.getroot().attrib

        globalCourseEvents = [
            {
                "title": {"en": "Course start", "pt": "Início do curso"},
                "attr_name": "start",
            },
            {"title": {"en": "Course end", "pt": "Fim do curso"}, "attr_name": "end"},
            {
                "title": {"en": "Enrollment start", "pt": "Abertura inscrições"},
                "attr_name": "enrollment_start",
            },
            {
                "title": {"en": "Enrollment end", "pt": "Fecho inscrições"},
                "attr_name": "enrollment_end",
            },
        ]
        if attrib:
            for globalEvent in globalCourseEvents:
                date = attrib.get(globalEvent["attr_name"])
                if date and date != 'null':
                    date = date.strip('"')
                    self.appendAllDayEvent(globalEvent["title"][self.lang], date, date)

    def appendNewContentsEvents(self):
        titlePrefix = {"en": "New Content", "pt": "Novos Conteúdos"}
        os.chdir(self.chapterDir)
        for file in [os.path.abspath(filebase) for filebase in os.listdir()]:
            if file.endswith(".xml"):
                attrib = ET.parse(file).getroot().attrib
                if attrib.get("visible_to_staff_only") != "true":
                    start = attrib.get("start")
                    title = attrib.get("display_name") or ''
                    if start:
                        start = start.strip('"')
                        title = titlePrefix[self.lang] + ": " + title.strip('"')
                        self.appendEvent(
                            title, start, self.addHours(start, self.eventDurationH)
                        )
                        if self.createAllDayEvents:
                            self.appendAllDayEvent(title, start, start)
                    else:
                        log.warning(
                            'No start date found for chapter: "'
                            + title
                            + '"" in file: '
                            + file
                            + ". You might need to change the date in Studio to a diffent one and back again."
                        )

    def appendDeadlineEvents(self):
        # Deadlines for subsections
        titlePrefix = {"en": "Deadline", "pt": "Fim de prazo"}
        os.chdir(self.sequentialDir)
        for file in [os.path.abspath(filebase) for filebase in os.listdir()]:
            if file.endswith(".xml"):
                attrib = ET.parse(file).getroot().attrib
                if attrib.get("visible_to_staff_only") != "true":
                    due = attrib.get("due")
                    if due:
                        due = due.strip('"')
                        disp_name = attrib.get("display_name").strip('"') or ''
                        title = (
                            titlePrefix[self.lang] + ": " + disp_name
                        )
                        self.appendEvent(
                            title, self.addHours(due, -self.deadlineDurationH), due
                        )
                        if self.createAllDayEvents:
                            self.appendAllDayEvent(title, due, due)
                else:
                    log.info('Skipping visible to staff only in file: "{}"'.format(file))

    def appendPeerReviewEvents(self):
        # Peer Review
        titlePrefixSubStart = {
            "en": "Response submission opened",
            "pt": "Início submissão de respostas",
        }
        titlePrefixSubDue = {
            "en": "Response submission deadline",
            "pt": "Fim de prazo submissão de respostas",
        }
        titlePrefixPAstart = {
            "en": "Peer assessment start",
            "pt": "Início avaliação dos pares",
        }
        titlePrefixPAdue = {
            "en": "Peer assessment deadline",
            "pt": "Fim de prazo avaliação dos pares",
        }
        os.chdir(self.verticalDir)
        for file in [os.path.abspath(filebase) for filebase in os.listdir()]:
            if file.endswith(".xml") and not self.isStaffOnly(file):
                root = ET.parse(file).getroot()
                for PR in root.iter("openassessment"):
                    PRtitle = PR.find("title").text or ""
                    attrib = PR.attrib
                    sub_start = attrib.get("submission_start")
                    sub_due = attrib.get("submission_due")
                    if sub_start:
                        sub_start = sub_start.strip('"')
                        title = titlePrefixSubStart[self.lang] + ": " + PRtitle
                        self.appendEvent(
                            title,
                            sub_start,
                            self.addHours(sub_start, self.eventDurationH),
                        )
                        if self.createAllDayEvents:
                            self.appendAllDayEvent(title, sub_start, sub_start)
                    if sub_due:
                        sub_due = sub_due.strip('"')
                        title = titlePrefixSubDue[self.lang] + ": " + PRtitle
                        self.appendEvent(
                            title,
                            self.addHours(sub_due, -self.deadlineDurationH),
                            sub_due,
                        )
                        if self.createAllDayEvents:
                            self.appendAllDayEvent(title, sub_due, sub_due)
                    for assessments in PR.findall("assessments"):
                        for assessment in assessments.findall("assessment"):
                            PAattrib = assessment.attrib
                            PAstart = PAattrib.get("start")
                            PAdue = PAattrib.get("due")
                            if PAstart:
                                PAstart = PAstart.strip('"')
                                title = titlePrefixPAstart[self.lang] + ": " + PRtitle
                                self.appendEvent(
                                    title,
                                    PAstart,
                                    self.addHours(PAstart, self.eventDurationH),
                                )
                                if self.createAllDayEvents:
                                    self.appendAllDayEvent(title, PAstart, PAstart)
                            if PAdue:
                                PAdue = PAdue.strip('"')
                                title = titlePrefixPAdue[self.lang] + ": " + PRtitle
                                self.appendEvent(
                                    title,
                                    self.addHours(PAdue, -self.deadlineDurationH),
                                    PAdue,
                                )
                                if self.createAllDayEvents:
                                    self.appendAllDayEvent(title, PAdue, PAdue)
