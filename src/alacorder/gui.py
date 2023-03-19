# gui playin' around not callin' it a test cuz i doubt im gonna actually make it and i think thats perfectly ok considering i already made a jupyter gui

from alacorder import alac
import PySimpleGUI as sg

buttons = [sg.Button("FETCH CASES"), sg.Button("MAKE ARCHIVE"), sg.Button("EXPORT TABLES"), sg.Button("APPEND ARCHIVE"), sg.Button("MARK QUERY")]

current_label = alac.title()

sg.theme("DarkBlack")
sg.set_options(font="Default 14")

current_container = buttons
layout = [[sg.Text(current_label,auto_size_text=True, font='Courier', size=[75,10])], [sg.VSeperator()], [current_container]]
window = sg.Window(title="Alacorder 78", layout=layout)

def new_window(label=[], container=[]):
	global window
	window.close()
	if label != [] and container != []: # both args fed
		layout = [[sg.Text(label,auto_size_text=True, font='Courier', size=[75,10])], [sg.VSeperator()], [container]]
	if label == [] and container != []: # container
		global current_label
		label = current_label
		layout = [[sg.Text(label,auto_size_text=True, font='Courier', size=[75,10])], [sg.VSeperator()], [container]]
	if label != [] and container == []: # label
		global current_container
		container = current_container
		layout = [[sg.Text(label,auto_size_text=True, font='Courier', size=[75,10])], [sg.VSeperator()], [container]]
	window = sg.Window(title="Alacorder 77", layout=layout)	

def show_fetch():
	global window
	layout = [
	[sg.Text("""Collect case PDFs in bulk from Alacourt.com\nfrom a list of names or search parameters.""", size=(100,2),font="Default 22")],
	[sg.Text("""Use column headers NAME, PARTY_TYPE, SSN, DOB, COUNTY, DIVISION, CASE_YEAR, and/or FILED_BEFORE in an Excel spreadsheet to submit a list of queries for Alacorder to scrape. Each column corresponds to a search field in Party Search. Missing columns and entries will be left empty, i.e. if only the NAME's and CASE_YEAR's are relevant to the search, a file with two columns will work.""",size=(70,6))],
	[sg.Text("Input Path: "), sg.InputText(key="-INPUTPATH-")],
	[sg.Text("Output Path: "), sg.InputText(key="-OUTPUTPATH-")],
	[sg.Text("Alacourt.com Credentials")],
	[sg.Text("Customer ID: "), sg.Input(key="-CUSTOMERID-")],
	[sg.Text("User ID: "), sg.Input(key="-USERID-")],
	[sg.Text("Password: "), sg.InputText(key="-PASSWORD-",password_char='*')],
	[sg.Text("Max queries: "), sg.Input(key="-MAX-", default_text="0", size=[10,1]),sg.Text("Skip from top: "), sg.Input(key="-SKIP-", default_text="0",size=[10,1]),sg.Text("Speed Multiplier: "), sg.Input(key="-SPEED-", default_text="1",size=[10,1])],
	[sg.Button("Start Query")]]
	window.close()
	window = sg.Window(title="Fetch Cases - Alacorder 77", layout=layout, size=[680,420])
	events, values = window.read()
	pwd = window["-PASSWORD-"].get()
	window["-PASSWORD-"].update("")
	a = alac.fetch(window['-INPUTPATH-'].get(),window['-OUTPUTPATH-'].get(),cID=window['-CUSTOMERID-'].get(),uID=window['-USERID-'].get(),pwd=pwd,qmax=int(window['-MAX-'].get()),speed=int(window['-SPEED-'].get()),qskip=int(window['-SKIP-'].get()))
	return a

def show_archive():
	global window
	layout = [
	[sg.Text("""Create full text archives from a directory with PDF cases.""", font="Default 22", size=(100,2))],
	[sg.Text("""Case text archives require a fraction of the storage capacity and processing time used to process PDF directories. Before exporting your data to tables, create an archive with supported file extensions .pkl.xz, .json(.zip), .parquet and .csv(.zip). Once archived, use your case text archive as an input for multitable or single table export.""",size=(70,6), font='Default 14')],
	[sg.Text("Input Path: "), sg.InputText(key="-INPUTPATH-")],
	[sg.Text("Output Path: "), sg.InputText(key="-OUTPUTPATH-")],
	[sg.Text("Skip Cases in Archive: "), sg.Input(key="-SKIP-")],
	[sg.Text("Max cases: "), sg.Input(key="-COUNT-", default_text="0", size=[10,1])],
	[sg.Checkbox("Try to Append",key="-APPEND-"), sg.Checkbox("Allow Overwrite",key="-OVERWRITE-")],
	[sg.Button("Make Archive")]]
	window.close()
	window = sg.Window(title="Make Archive - Alacorder 77", layout=layout, size=[680,375])
	events, values = window.read()
	a = alac.setinit(window['-INPUTPATH-'].get(),window['-OUTPUTPATH-'].get(),count=int(window['-COUNT-'].get()),archive=True,overwrite=window['-OVERWRITE-'].get(), append=window['-APPEND-'].get(), no_prompt=True)
	return a

def show_table():
	global window
	layout = [
	[sg.Text("""Export data tables from case archive or directory.""", font="Default 22", size=(100,1))],
	[sg.Text("""Alacorder processes case detail PDFs and case text archives into data tables suitable for research purposes. Export an Excel spreadsheet with detailed cases information (cases), fee sheets (fees), and charges information (charges, disposition, filing), or select a table to export to another format (.json, .csv, .parquet). Note: It is recommended that you create a case text archive from your target PDF directory before exporting tables. Case text archives can be processed into tables at a much faster rate and require far less storage.""", size=(70,7))],
	[sg.Text("Input Path: "), sg.InputText(key="-INPUTPATH-")],
	[sg.Text("Output Path: "), sg.InputText(key="-OUTPUTPATH-")],
	[sg.Text("Max cases: "), sg.Input(key="-COUNT-", default_text="0", size=[10,1])],
	[sg.Checkbox("All Tables (.xlsx, .xls)", key="-ALL-", default=True), 
		sg.Checkbox("Cases", key="-CASES-", default=False), 
		sg.Checkbox("All Charges", key="-CHARGES-", default=False)], 
	[sg.Checkbox("Disposition Charges", key="-DISPOSITION-",default=False), sg.Checkbox("Filing Charges",key="-FILING-",default=False),
		sg.Checkbox("Fee Sheets",key="-FEES-",default=False)],
	[sg.Checkbox("Allow Overwrite", key="-OVERWRITE-"), sg.Checkbox("Compress", key="-COMPRESS-")],
	[sg.Button("Export Table")]]
	window.close()
	window = sg.Window(title="Table Export - Alacorder 77", layout=layout, size=[680,390])
	events, values = window.read()
	tpick = False
	tabl = ""
	while not tpick:
		if bool(window["-ALL-"]) == True:
			tabl = "all"
			tpick = True
		elif bool(window["-CASES-"]) == True:
			tabl = "cases"
			tpick = True
		elif bool(window["-CHARGES-"]) == True:
			tabl = "charges"
			tpick = True
		elif bool(window["-DISPOSITION-"]) == True:
			tabl = "disposition"
			tpick = True
		elif bool(window["-FILING-"]) == True:
			tabl = "filing"
			tpick = True
		elif bool(window["-FEES-"]) == True:
			tabl = "fees"
			tpick = True
		else:
			print("Invalid table input choice.")
			tpick = False
	a = alac.setinit(window['-INPUTPATH-'].get(),window['-OUTPUTPATH-'].get(),count=int(window['-COUNT-'].get()),table=tabl,overwrite=window['-OVERWRITE-'].get(),compress=window['-COMPRESS-'].get(),no_prompt=True)
	return a

def show_mark():
	global window
	layout = [
	[sg.Text("""Mark query template with collected cases from input\narchive or directory.""", font="Default 22", size=(100,2))],
	[sg.Text("""Use column headers NAME, PARTY_TYPE, SSN, DOB, COUNTY, DIVISION, CASE_YEAR, and/or FILED_BEFORE in an Excel spreadsheet to submit a list of queries for Alacorder to scrape. Each column corresponds to a search field in Party Search. Missing columns and entries will be left empty, i.e. if only the NAME's and CASE_YEAR's are relevant to the search, a file with two columns will work.""",auto_size_text=True, font='Default 14', size=(70,6))],
	[sg.Text("Input Path: "), sg.InputText(key="-INPUTPATH-")],
	[sg.Text("Output Path: "), sg.InputText(key="-OUTPUTPATH-")],
	[sg.Button("Mark Query")]]
	window = sg.Window(title="Mark Query - Alacorder 77", layout=layout, size=[680,285])
	window.close()
	events, values = window.read()
	a = alac.mark(window['-INPUTPATH-'].get(),window['-OUTPUTPATH-'].get())
	return a

def show_append():
	global window
	layout = [
	[sg.Text("""Append case text archive with the contents\nof a PDF directory or the contents of another archive.""", font="Default 22", size=(100,2))],
	[sg.Text("""Case text archives require a fraction of the storage capacity and processing time used to process PDF directories. Before exporting your data to tables, create an archive with supported file extensions .pkl.xz, .json(.zip), .parquet and .csv(.zip). Once archived, use your case text archive as an input for multitable or single table export.""",auto_size_text=True, font='Default 14', size=(70,6))],
	[sg.Text("Input Path: "), sg.InputText(key="-INPUTPATH-")],
	[sg.Text("Output Path: "), sg.InputText(key="-OUTPUTPATH-")],
	[sg.Button("Append Archives")]]
	window = sg.Window(title="Append Archives - Alacorder 77", layout=layout, size=[680,285])
	window.close()
	events, values = window.read()
	a = alac.append_archive(window['-INPUTPATH-'].get(),window['-OUTPUTPATH-'].get())
	return a


while True:
	event, values = window.read()
	if event == "EXPORT TABLES":
		show_table()
	if event == "FETCH CASES":
		show_fetch()
	if event == "MAKE ARCHIVE":
		show_archive()
	if event == "APPEND ARCHIVE":
		show_append()
	if event == "MARK QUERY":
		show_mark()
	if event == "Exit" or event == sg.WIN_CLOSED:
		break