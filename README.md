# GCal4edX - Google Calendar for Open edX courses

This code processes a Open edX course export file and creates a Google Calendar with the events corresponding to new contents' publishing dates and dead lines.
Intended to be used with the [Google Calendar Tool] Xblock.
Developed for [MOOC Técnico].

## Important notes
* Developed for Open edX Dogwood (might need adjustments for other releases)
* Running the script again cleares all events in the calendar with the same name
* Peer Review partially supported
* Requires python 3.7+ (Not tested with earlier versions)
* All feedback and help is more than welcome

## How to use this code yourself
To get started with this code:
* [Python Google Calendar API] - getting started tutorial
* Install all python 3 packages you are missing (see imports at the beggining of the code)
If you run into trouble you can contact me by creating a new issue. More detailed instructions would be provided if you find this usefull.

[Google Calendar Tool]: https://edx.readthedocs.io/projects/open-edx-ca/en/dogwood/exercises_tools/google_calendar.html 
[MOOC Técnico]: https://mooc.tecnico.ulisboa.pt
[Python Google Calendar API]: https://developers.google.com/calendar/quickstart/python 
