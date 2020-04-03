from cmu_course_api import get_course_data
import json

def build_courses(args):
	if args == None:
		args = ['F','S','M1','M2']
	for sem in args:
		if sem in ['F','S','M1','M2']:
			dat = get_course_data(sem)
			with open(sem + '.json', 'w') as f:
				json.dump(dat, f, indent=2)
		else:
			print('Invalid semester, try "F", "S", "M1", or "M2"')
    
