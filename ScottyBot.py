import pandas as pd
import numpy as np
import math
import os
import json
import colorama
from datetime import datetime
import re

# -------------
# PREPROCESSING
# -------------

global fall, spring, table
fall, spring, table = None, None, None

def buildFce():
	global table
	dir = os.path.dirname(os.path.realpath(__file__)) 
	table = pd.read_csv(os.path.join(dir,'fce.csv'))
	table = np.array(table)[:,[*range(0,13)] + [23]]
	table = np.array([row for row in table if row[1] != 'Summer' and row[0] > 2013])

def buildCourses():
	global fall, spring
	dir = os.path.dirname(os.path.realpath(__file__))
	with open(os.path.join(dir,'spring.json')) as f:
		fall = json.load(f)
	with open(os.path.join(dir,'spring.json')) as f:
		spring = json.load(f)
		

# ---------------------------------
# THE ACTUAL BOT - CMU DATA SECTION
# ---------------------------------

def isValidCourse(msg): 
	"""
	Helper function that identifies if a string is a valid course or not.
	"""
	if len(msg) == 5 and msg.isdigit():
		return True
	if len(msg) == 6 and (msg[:2] + msg[3:]).isdigit() and msg[2] == '-':
		return True
	return False

def getString(mold, row):
	"""
	Takes particular columns from an FCE data frame row and assembles them into a string.
	"""
	indices = [0, 1, 6, 10, 9, 11, 12, 13]
	rowIndices = [row[index] for index in indices]
	string = mold.format(*rowIndices)
	return string

def toDigitString(ID):
	"""
	Turns a course ID argument into a compatible form for the FCE data frame.
	"""
	if ID.isdigit():
		# if ID[0] == '0':
		# 	return ID[1:]
		return ID
	else:
		if ID[0] == '0':
			return ID[:1] + ID[3:]
		return ID[:2] + ID[3:]


def fce(args):
	"""
	Function that defines the ;fce command. Also moonlights as a giant pain in the ass.
	"""
	#retrieve data
	global table
	if not table:
		buildFce()

	now = datetime.now().year
	numSemesters = 2
	responses = 0

	#if professor tag (-p), build list of courses for professor
	prof = None
	if args[0] == '-p':
		args = [x.strip(',') for x in args]
		courses = []
		if args[-1].isdigit():
			if len(args) < 3:
				print('Missing argument - please specify professor name')
				return
			if args[-2].isdigit():
				responses = int(args[-1])
				args = args[:-1]
			numSemesters = int(args[-1])
			prof = ', '.join(args[1:len(args)-1]).upper()
		else:
			prof = ', '.join(args[1:len(args)]).upper()

		for entry in table:
			if entry[0] <= now - numSemesters:
				break
			if (prof == entry[6] or prof in re.split(r'[;,\s]\s*',entry[6])) and entry[4] not in courses:
				courses.append(entry[4])

		if len(courses) == 0:
			print('Professor not found')
			return

		args = courses
	
	#check the args are valid
	indices = [0, 1, 4, 7, 6, 10, 9, 11, 12]
	if not isValidCourse(args[-1]) and args[-1].isdigit():
		if len(args) < 2:
			print('Missing argument - please specify course')
			return
		if not isValidCourse(args[-2]) and args[-2].isdigit():
			if len(args) < 3:
				print('Missing argument - please specify course')
				return
			responses = int(args[-1])
			args = args[:-1]
		numSemesters = int(args[-1])
		args = args[:-1]
	courses = []
	for course in args:
		if not isValidCourse(course):
			print('Invalid course: ' + course)
			return
		else:
			courses.append(course)

	courseIDs = [toDigitString(course) for course in courses]

	#segments the data by year, semester
	allRows = []
	for courseID in courseIDs:
		year = 'dummy_string.jpg omegalul' #lol
		semester = 'why are you reading this' #very cool
		courseList = []
		sameSemList = []
		for row in table:
			if not prof or prof == row[6] or prof in re.split(r'[;,\s]\s*',row[6]):
				if row[0] != year or row[1] != semester: 					# if this row is not the same course/semester as the rest of the section
					if len(sameSemList) != 0:
						courseList.append([item for sublist in sameSemList for item in sublist])
					sameSemList = []
					year = row[0]
					semester = row[1]
				if row[4] == str(courseID):
					sameSemList.append([row])
		allRows.append(courseList)


	#restricts to the rows requested
	newRows = [[[course for course in semesterList if course[0] >= now - numSemesters and int(course[10]) > responses] for semesterList in courseList] for courseList in allRows]
	newRows = [row for row in newRows if row != []]

	# adds up the FCE's
	totalFCEs = []
	totalRatings = []
	
	for i, course in enumerate(newRows):
		totalFCE = 0
		totalRating = 0
		count = 0
		for sem in course:
			for cour in sem:
				if not math.isnan(cour[12]):
					totalFCE += float(cour[12])
					totalRating += float(cour[13])
					count += 1
		else:
			totalFCEs.append(np.around(totalFCE / count, 2))
			totalRatings.append(np.around(totalRating / count, 2))

	# if only one course was requested, assemble the FCE data string
	if len(courses) == 1: 
		mold = '{0:^%d} | {1:^%d} | {2:^%d} | {3:^%d} | {4:^%d} | {5:^%d} | {6:^%d} | {7:^%d}\n' % (4, 8, 22, 7, 11, 9, 9, 9)
		docstrings = [mold.format('Year', 'Semester', 'Instructor', '# resp.', 'Total resp.', '% resp.', 'FCE hours', 'Rating')]

		for sem in newRows[0]:
			for row in sem:
				if not math.isnan(row[12]):
					docstrings.append(getString(mold, row))
		
		# separates the docstrings into messages
		endstrings = []
		temp = ''
		for docstring in docstrings:
			if len(temp) + len(docstring) <= 1992:
				temp += docstring
			else:
				endstrings.append(temp)
				temp = docstring
		endstrings.append(temp)

	# if there are plural semesters
	ess = ''
	if numSemesters > 1:
		ess = 's'
	
	# set up the optional string for if filtering was requested
	extraString = ''
	if responses != 0:
		filterNum = '{}'.format(responses)
		extraString = ', filtering for greater than {} responses'.format(filterNum)

	# set up the string containing the course names and ids
	courseStrings = ''
	listOfCourses = ['[\033[33m{} {}\033[39m], '.format(courseIDs[i], newRows[i][0][0][7]) for i in range(len(newRows))]
	for course in listOfCourses:
		courseStrings += course

	# if there are multiple courses, set up the addition string
	additionString = ''
	ess2 = ''
	if len(courses) > 1:
		ess2 = 's'
		fceStrings = [' {} +'.format(fce) for fce in totalFCEs]
		for string in fceStrings:
			additionString += string
		additionString = additionString[:-1] + '=' 
		
	# if there are multiple courses, set up the addition string
	additionString2 = ''
	if len(courses) > 1:
		additionString2 = '(' + ' + '.join([str(x) for x in totalRatings]) + ') / ' + str(len(totalRatings)) + ' = '
	

	# create and send the final string
	# [\033[33m (makes the string pretty colors!) \033[39m]
	stringFinal = 'Overall FCEs for {} within {} semester{}{}:\n - {} \033[31m{}\033[39m total hours \n -  {}\033[31m{}\033[39m / 5.0 avg rating'.format(
		courseStrings[:-2], numSemesters, ess, extraString, additionString, np.around(sum(totalFCEs), 2), additionString2, np.around(sum(totalRatings) / len(totalRatings),2))
	colorama.init()
	print('\n' + stringFinal) 
	colorama.deinit()

	# if only one course was requested, also send the messages of all the query data
	if len(courses) == 1:
		print()
		for endstring in endstrings:
			print(endstring.strip())


def getInstructors(lectures):
	"""
	Helper function that formats the instructors of a course in a particular way.
	"""
	output = '\n'
	for lecture in lectures:
		output += '['
		for instructor in lecture['instructors']:
			output += '({}) '.format(instructor)
		output = output[:-1] + '] '
	return output

def course(courseID):
	"""
	Function that defines the ;course command.
	"""
	#retrieve data
	global fall, spring
	if not fall and not spring:
		buildCourses()

	newFall = fall['courses']
	newSpring = spring['courses']

	if isValidCourse(courseID): # if the courseID is valid, then do all the work
		# remove hyphen if it exists
		if courseID[2] != "-":
			courseID = courseID[:2] + '-' + courseID[2:]

		# set flags for if the course exists in fall or spring
		inFall = courseID in newFall.keys()
		inSpring = courseID in newSpring.keys()
		
		# if it doesn't exist in either return early
		if not (inFall or inSpring):
			print('Course not found.')
			return

		# set some strings for later use
		semesters = ''
		instructorsFall = ''
		instructorsSpring = ''
		coreqs = ''

		# get the data if the course exists in spring
		if courseID in newSpring.keys(): 
			title = newSpring[courseID]['name']
			department = newSpring[courseID]['department']
			units = newSpring[courseID]['units']
			description = newSpring[courseID]['desc']
			prereqs = newSpring[courseID]['prereqs']
			if newSpring[courseID]['coreqs'] != None:
				coreqs = '\n -  Corequisites: {}'.format(newSpring[courseID]['coreqs'])
			instructorsSpring = getInstructors(newSpring[courseID]['lectures']) + ' (Spring)'
			semesters = spring['semester']

		# get the data if the course exists in fall
		else: 
			title = newFall[courseID]['name']
			department = newFall[courseID]['department']
			units = newFall[courseID]['units']
			description = newFall[courseID]['desc']
			prereqs = newFall[courseID]['prereqs']
			if newFall[courseID]['coreqs'] != None:
				coreqs = '\n -  Corequisites: {}'.format(newFall[courseID]['coreqs'])
			instructorsFall = getInstructors(newFall[courseID]['lectures']) + ' (Fall)'
			if len(semesters) == 0:
				semesters += fall['semester']
			else:
				semesters += ', {}'.format(fall['semester'])

		# put it all together with the magic of {}
		# [\033[33m (makes the string pretty colors!) \033[39m]
		instructors = '{}{}'.format(instructorsFall, instructorsSpring).strip()
		stringFinal = " [\033[33m{}\033[39m]".format(title) + '\n' + ' -  {} \n -  {} units \n -  {}\n -  Prerequisites: {}{}\n -  Instructors: {}\n -  Semesters: {}'.format(
				department, units, description, prereqs, coreqs, instructors, semesters)
		colorama.init()
		print('\n' + stringFinal + '\n')
		colorama.deinit()
	else:
		print('Invalid arguments - please specify the course ID (e.g. \".course 21127)\"')