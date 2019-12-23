# GCal4edX - Google Calendar for Open edX courses

This code processes a Open edX course export file and creates a Google Calendar with the events corresponding to new contents' publishing dates and dead lines.
Intended to be used with the [Google Calendar Tool] Xblock.
Developed for [MOOC Técnico].

## Download latest version
You can get the latest macOS App [here].

## Important notes
* Developed for Open edX Dogwood (might need adjustments for other releases)
* Peer Review partially supported
* Requires python 3.7+ (Not tested with earlier versions)
* All feedback and help is more than welcome

# Developer resources

## How to use this code yourself
To get started with this code:
* [Python Google Calendar API] - getting started tutorial
* Install all python 3 packages you are missing (see imports at the beggining of the code)
If you run into trouble you can contact me by creating a new issue. More detailed instructions would be provided if you find this usefull.

## Building this app step by step
1. Clone this repo
```bash
git clone https://github.com/caenrigen/GCal4edX.git; cd GCal4edX
```

2. Set up a virtual environment (make sure you are already in the gcal4edx folder, the `cd GCal4edX` above should do that)
```bash
python3 -m venv venv
```

3. Activate the environment
```bash
source ./venv/bin/activate
```

4. Install required packages. There might be other required packages, but at least the following are essential.
```bash
pip install -r requirements.txt
```

5. After you get started with the Google Calendar API, copy your `credentials.json` file into the project resource dir such that you end up with the following file, (you need to create the folders)
```bash
mkdir ./src/main/resources; mkdir ./src/main/resources/base/
# ./src/main/resources/base/credentials.json # you should end up with this file
```

6. Test if the app runs correctly:
```bash
python3 build.py run # you can also run 'fbs run'
```

7. Freeze the app
```bash
python3 build.py build_ui # convert ui files into python code
python3 build.py build # modified 'fbs freeze'
```

8. After freezing your app you can create an installer with the following
```bash
python3 build.py installer # or just 'fbs installer'
```

[Google Calendar Tool]: https://edx.readthedocs.io/projects/open-edx-ca/en/dogwood/exercises_tools/google_calendar.html
[MOOC Técnico]: https://mooc.tecnico.ulisboa.pt
[Python Google Calendar API]: https://developers.google.com/calendar/quickstart/python
[here]: https://fbs.sh/victor/GCal4edX/GCal4edX.dmg
