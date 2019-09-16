from fbs.cmdline import command
import fbs.cmdline
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from fbs_runtime import platform

from os.path import dirname, join
from os import system
import plistlib

@command
def fix_dark_mode():
	appctxt = ApplicationContext()
	pl = None
	fileName = join('target', appctxt.build_settings['app_name'] + '.app', 'Contents', 'Info.plist') 
	with open(fileName, 'rb') as file:
		pl = plistlib.load(file)
		if 'NSRequiresAquaSystemAppearance' not in pl:
			pl['NSRequiresAquaSystemAppearance'] = 'No'
	with open(fileName, 'wb') as file:
		plistlib.dump(pl, file)

@command
def build():
	fbs.builtin_commands.freeze()
	if platform.is_mac():
		fix_dark_mode()

@command
def build_ui():
	main_ui = 'MainWindow'
	cal_dialog = 'CalendarCreatedDialog'
	src_ui_dir = 'src-ui'
	out_dir = join('src','main','python')
	system('pyuic5 -x ' + join(src_ui_dir, main_ui+'.ui') + ' -o ' + join(out_dir,main_ui+'.py'))
	system('pyuic5 -x ' + join(src_ui_dir, cal_dialog+'.ui') + ' -o ' + join(out_dir,cal_dialog+'.py'))

if __name__ == '__main__':
	project_dir = dirname(__file__)
	fbs.cmdline.main(project_dir)