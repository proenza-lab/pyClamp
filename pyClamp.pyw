#!/usr/bin/env python3


"""
pyClamp (graphical user interface for the dyClamp sketch)
Copyright (C) 2019 Christian Rickert <mail@crickert.de>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNBESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA.

pyClamp was partially developed at Laboratory of Catherine Proenza,
Department of Physiology & Biophysics, University of Colorado,
Anschutz Medical Campus.

Version 1.0
"""


#  imports

import time
import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import matplotlib
matplotlib.use('TkAgg')  # call before matplotlib modules
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np


#  constants

ANIM = None		# placeholder for animation object
BEGIN = 0		# start time [s] for current experiment
HISTORY = 500	# number of report values displayed simultaneously
DATA_X = np.linspace(0, -HISTORY, HISTORY)	# values for x axis
REPORTS = 3		# number of values in transmission string
DATA_YY = np.zeros((REPORTS, HISTORY))		# array with previous report values
INTERVAL = 1	# interval [ms] for plot updates (0 = None)
LINES = []		# tuple list with graph data for plot updates
LOOP = False	# active status of animation loop
MAXOFFSET = 64	# maximum number of bytes to clear to confirm command
NEW_YY = np.zeros((REPORTS))	# array with new report values
REDRAW = 100	# redraw canvas (update scales) in intervals of n REPORTS
SER = serial.Serial()			# port object
STATUS = "Welcome! Select a port to connect to the Teensy."
SUTATS = STATUS	# remember previous state
SYNC = False	# comparison between command sent and command received
TIMEOUT = 0.02	# maximum wait time [s] for serial transmissions
TIMER = False	# display an experiment timer instead of the local time


#  functions

def activate_port(string="COM1"):
	""" activate the serial com port """
	global SER, STATUS, SYNC, TIMEOUT
	try:
		SER = serial.Serial(string, 115200, timeout=TIMEOUT)
	except serial.SerialException:
		PYCLAMP.stsentry.var.set(new_status_string(False, "Port unavailable."))
		PYCLAMP.prtmenu.var.set("(Select)")  # prevents redraw and port activation
		SER.close()
	else:
		SYNC = write_command(new_command([0, 0]))
		if SYNC:
			for button in get_buttons(get_children(PYCLAMP.masframe, [])):
				button.configure(state="normal")
			SER.reset_output_buffer()
			SER.reset_input_buffer()
			download()
			PYCLAMP.stsentry.var.set(new_status_string(True, "Connection to Teensy."))
		else:
			PYCLAMP.stsentry.var.set(new_status_string(False, "Teensy not responding."))
			PYCLAMP.prtmenu.var.set("(Select)")
			SER.close()

def download():
	""" download parameters and conductances (Download button) """
	global SER, SYNC
	SYNC = write_command(new_command([0, 1]))
	if SYNC:
		tuples = []
		while SER.in_waiting > 4:
			tuples.append(string_to_tuple(read_string()))
		lencals = int(abs(min([v[0] for v in tuples])))	# number of calibration parameters
		lencons = int(max([v[0] for v in tuples]))		# number of conductance values
		calibras = [[].append(0.0) for i in range(lencals)]
		conducts = [[].append(0.0) for i in range(lencons)]
		for values in tuples:
			index = int(values[0])
			if index < 0:	# negative index, update parameters
				index = -1 * index - 1
				calibras[index] = values[1]
			elif index > 0:	# positive index, update conductances
				index -= 1
				conducts[index] = values[1]
			else:			# zero index, not yet reported
				pass
		set_values(calibras, conducts)
	PYCLAMP.stsentry.var.set(new_status_string(SYNC, "Download of calibration parameters and conductance values."))

def get_buttons(children=None):  # see: https://docs.python.org/3/tutorial/controlflow.html#default-argument-values
	""" returns a list of buttons from a list of children """
	entries = []
	for child in children:
		if (child.winfo_name().startswith("!button") or \
			child.winfo_name().startswith("!mycheckbutton")):
			entries.append(child)
	return entries

def get_children(widget=None, children=None):
	""" returns a recursive list of children from a widget """
	widgets = widget.winfo_children()	# buggy
	for child in widgets:
		children.append(child)
		get_children(child, children)	# recursion
	return children

def get_numentries(children=None):
	""" returns a list of text entries from a list of children """
	entries = []
	for child in children:
		if str(child.winfo_name()).startswith("!mynumentry"):
			entries.append(child)
	return entries

def get_values():
	""" read parameters and conductances from the corresponding entries """
	tuples = []
	cals = get_numentries(get_children(PYCLAMP.calframe, []))  # calibration parameters
	cons = get_numentries(get_children(PYCLAMP.conframe, []))  # conductance values
	for index, entry in zip(range(1, len(cals)+2), cals):
		entry.var.get()
		value = float(entry.var.get() or 0.0)
		tuples.append((-index, value))	# get calibration parameters
	for index, entry in zip(range(1, len(cons)+2), cons):
		value = float(entry.var.get() or 0.0)
		tuples.append((index, value))	# get conductance values
	return tuples

def initialize_animation():
	""" prepares the looping animation function """
	global ANIM, INTERVAL
	ANIM = FuncAnimation(PYCLAMP.figure, update_plot, blit=True, interval=INTERVAL)

def initialize_plot():
	""" set up plot with numpy arrays """
	global DATA_X, DATA_YY, LINES
	labels = ('Membrane Potential [mV]', 'Injected Current [pA]', 'Cycle Time [µs]')
	subplot = PYCLAMP.figure.add_subplot(111, xlabel="Reports", ylabel="Values", title="Transmission History")
	for i, data_y in enumerate(DATA_YY):
		line, = subplot.plot(DATA_X, data_y, label=labels[i], linestyle='-', linewidth=0.75, marker='.', markevery=[0, ])
		LINES.append(line)
	subplot.yaxis.tick_right()
	subplot.yaxis.set_label_position("right")
	subplot.legend(fancybox=True, framealpha=0.75, loc=2)
	plt.show()

def new_command(values=None):
	""" creates a new (command) string from a list of values """
	carriage = "\r"
	tabulator = "\t"
	linefeed = "\n"
	index = 0
	string = carriage
	for value in values[0:2]:  # limit command string length
		if index > 0:
			string += tabulator
		string += str(value)
		index += 1
	string += linefeed
	return string

def new_status_string(boolean=True, string=""):
	""" returns a status string """
	status = "SUCCESS:" if boolean else "FAILURE:"
	return status + " " + string

def prepr(string=""):
	""" print a string with a printable representation of an object (for debugging) """
	print(repr(string))

def read_string():
	""" receives a string from the serial COM port """
	global SER
	string = str(SER.readline(), encoding='utf-8', errors='strict')  # avoid timeout
	return string

def report():
	""" toggle live REPORTS (Live Report button) """
	global SYNC
	SYNC = write_command(new_command([0, 2]))
	PYCLAMP.stsentry.var.set(new_status_string(SYNC, "Toggle of live REPORTS."))

def send():
	""" send a manual command (Send button) """
	global SYNC
	index = PYCLAMP.idxentry.var.get()
	value = PYCLAMP.valentry.var.get()
	SYNC = write_command(new_command((index, value)))
	PYCLAMP.stsentry.var.set(new_status_string(SYNC, "Transmission of manual command."))

def set_values(calibras=None, conducts=None):
	""" writing parameters and conductances into the corresponding entries """
	global SYNC
	if SYNC:
		for entry, value in zip(get_numentries(get_children(PYCLAMP.calframe, [])), calibras):
			entry.var.set(value)  # set calibration parameters
			entry.configure(state="normal", background="light green", foreground="black")
		for entry, value in zip(get_numentries(get_children(PYCLAMP.conframe, [])), conducts):
			entry.var.set(value)  # set conductance values
			entry.configure(state="normal", background="light green", foreground="black")

def split_string(string=""):
	""" strips and splits a string """
	string = string.strip().split("\t")  # remove '\r' and '\n', split by '\t'
	return string

def start():
	""" start experiments by updating conductance values (Start button) """
	global BEGIN, SYNC, TIMER
	SYNC = True
	for tuples in get_values():
		if tuples[0] > 0:
			if not write_command(new_command(tuples)):
				SYNC = False
	if SYNC:
		BEGIN = time.time()
		TIMER = True
		download()
	PYCLAMP.stsentry.var.set(new_status_string(SYNC, "Upload of conductance values."))

def stop():
	""" stop all experiments by zeroing conductance values (Stop button) """
	global SYNC, TIMER
	SYNC = True
	for tuples in get_values():
		if tuples[0] > 0:
			if not write_command(new_command((tuples[0], 0.0))):
				SYNC = False
	if SYNC:
		TIMER = False
		download()
	PYCLAMP.stsentry.var.set(new_status_string(SYNC, "Reset of conductance values."))

def string_to_tuple(string=""):
	""" returns a list of float value tuples from a (command) string """
	tuples = []
	values = split_string(string)
	for value in values:
		tuples += float(value),
	return tuples

def time_to_string(begin=0, end=0):
	""" converts a time difference into a string for display """
	hrs, rem = divmod(end-begin, 3600)  #  return a pair of numbers consisting of their quotient and remainder
	mins, secs = divmod(rem, 60)
	return "{:0>2}: {:0>2}: {:02.0f}".format(int(hrs), int(mins), secs)

def toggle_animation():
	""" toggles the animation on or off depending on the checkbutton activation """
	global ANIM, LOOP
	if PYCLAMP.repbutton.var.get():
		LOOP = True
		ANIM.event_source.start()	# start animation
	else:
		LOOP = False
		ANIM.event_source.stop()	# stop animation to save CPU

def toggle_buttons():
	""" toggles the buttons active or inactive depending on text entry validity """
	valid = True
	for entry in get_numentries(get_children(PYCLAMP.trframe, [])):
		if entry.cget('background') == 'red':
			valid = False
	for button in get_buttons(get_children(PYCLAMP.trframe, [])):
		if valid:
			button.configure(state='normal')
		else:
			button.configure(state='disabled')
	PYCLAMP.stsentry.var.set(new_status_string(valid, "Interpretation of input values."))

def toggle_checkbutton():
	""" toggles the checkbutton text depending on its activation """
	if PYCLAMP.repbutton.var.get():
		PYCLAMP.repbutton.configure(text="Live Reports\n(Active)")
	else:
		PYCLAMP.repbutton.configure(text="Live Reports\n(Inactive)")

def toggle_live_reports():
	""" toggles the live reports on and off """
	report()
	toggle_animation()
	toggle_checkbutton()

def toggle_tooltip(message):
	""" toggles the display of a tooltip in the status entry """
	global STATUS, SUTATS
	if message:
		SUTATS = PYCLAMP.stsentry.var.get()
		PYCLAMP.stsentry.var.set(message)
	else:
		PYCLAMP.stsentry.var.set(SUTATS)

def update_plot(count=0):
	""" update plot with numpy arrays """
	global DATA_X, DATA_YY, LINES, LOOP, NEW_YY, REDRAW, SER
	if LOOP:  # save some CPU instead of querying the widget
		try:
			NEW_YY = np.asarray(string_to_tuple(read_string()))
			DATA_YY[:, 1:] = DATA_YY[:, :-1]	# shift data to the right
			DATA_YY[:, 0] = NEW_YY				# insert data to the left
		except ValueError:						# transmission failed or delayed
			SER.reset_input_buffer()
		else:
			for i, data_y in enumerate(DATA_YY):
				LINES[i].set_ydata(data_y) # update line data
			if not count % REDRAW:			# redraw in intervals
				PYCLAMP.figure.gca().relim(visible_only=True)					# compute new data limits
				PYCLAMP.figure.gca().autoscale_view(scalex=False, scaley=True)	# autoscale view based on new data limits
				PYCLAMP.canvas.draw()											# update axes despite active blitting
	return LINES

def update_timer():
	""" updates the time string in given intervals """
	global BEGIN, TIMER
	if TIMER:
		PYCLAMP.clkentry.var.set(time_to_string(BEGIN, time.time()))
	elif not BEGIN:
		PYCLAMP.clkentry.var.set(time_to_string(0, 0))  # at startup
	ROOT.after(1000, update_timer)  # recursive tk alarm callback

def upload():
	""" upload calibration parameters and conductance values (Upload button) """
	global SYNC
	SYNC = True
	for values in get_values():
		if not write_command(new_command(values)):
			SYNC = False
	if SYNC:
		download()
	PYCLAMP.stsentry.var.set(new_status_string(SYNC, "Upload of calibration parameters and conductance values."))

def write_command(command=""):
	""" writes a command string and confirms synchronization with the echo string """
	global MAXOFFSET
	write_string(command)
	offset = 0
	echo = ""
	while echo != command and offset < MAXOFFSET:  # ignore buffered data
		echo = read_string()
		offset += 1
	return echo == command

def write_string(string=""):
	""" sends a string to the serial COM port """
	global SER
	SER.write(string.encode())

def _quit():
	""" manage GUI exit """
	global LOOP, SER
	ROOT.quit()  # stop mainloop
	ROOT.destroy()  # prevent fatal python error on Windows
	if LOOP:
		report()  # turn off live REPORTS
	SER.close()  # close serial COM port


# classes

class MyCheckbutton(tk.Checkbutton):
	""" customized checkbutton """

	def __init__(self, parent, **options):
		""" initialization method """
		tk.Checkbutton.__init__(self, parent, **options)
		self.var = tk.BooleanVar()
		self.configure(indicatoron=False, state='disabled', variable=self.var, command=toggle_live_reports)

class MyPortOptionMenu(tk.OptionMenu):
	""" customized port option menu """

	def __init__(self, parent, **options):
		""" initialization method """
		self.var = tk.StringVar()
		self.options = ["(Select)"]
		self.var.set(self.options[0])
		tk.OptionMenu.__init__(self, parent, self.var, tuple(self.options), **options)

	def callback(self, *events):
		""" callback method triggered by a change in activation status """
		choice = self.var.get()
		if choice != "(Select)":
			activate_port(choice)

	def update_port_options(self, *events):
		""" updates the list of available ports """
		self.options = []
		for ports in serial.tools.list_ports.comports():	# update port list
			self.options.append(ports.device)
		self["menu"].delete(0, "end")
		for option in self.options:							# update port menu
			self["menu"].add_command(label=option, command=tk._setit(self.var, option))

class MyTextEntry(tk.Entry):
	""" customized text entry """

	def __init__(self, parent, **options):
		""" initialization method """
		tk.Entry.__init__(self, parent, **options)
		self.var = tk.StringVar()
		self.configure(textvariable=self.var)

	def set(self, string, *events):
		""" setter method to update the text entry """
		state = self.cget('state')
		self.configure(state='normal')	# enable writing
		self.delete(0, 'end')
		self.insert(0, string)
		self.configure(state=state)		# return to previous state

class MyNumEntry(MyTextEntry):
	""" customized number entry """

	def __init__(self, parent, **options):
		""" initialization method """
		tk.Entry.__init__(self, parent, **options)
		self.var = tk.DoubleVar()
		self.var.trace_variable('w', self.callback)
		self.configure(textvariable=self.var)

	def callback(self, *events):
		""" callback method triggered by a change in activation status """
		self.configure(background='white')
		try:
			float(self.var.get())
		except tk.TclError:
			self.configure(background='red', foreground='white')
			toggle_buttons()
		else:
			if self.var.get() < 0:
				self.configure(foreground='red')
			elif self.var.get() == 0:
				self.configure(foreground='black')
			else:  # self.var.get() > 0
				self.configure(foreground='green')
			toggle_buttons()

class PYCLAMP():
	""" graphical user interface """
	global STATUS, SUTATS

	def __init__(self):
		""" initialization method """
		global STATUS, SUTATS

		"""
		The grid layout highlights elements created
		in this section of the code with an 'x':
		Use as a simple map for navigation.

		1.0 Master frame
		-------------
		| x | x | x |
		-------------
		| x | x | x |
		-------------
		| x | x | x |
		-------------
		"""
		self.masframe = ttk.Frame(ROOT)						# window assignment
		self.masframe.grid(column=0, row=0, sticky='nesw')	# positioning
		self.masframe.columnconfigure(0, weight=1)			# left
		self.masframe.columnconfigure(1, weight=1)			# center
		self.masframe.columnconfigure(2, weight=0)			# right
		self.masframe.rowconfigure(0, weight=1)				# top
		self.masframe.rowconfigure(1, weight=1)				# middle
		self.masframe.rowconfigure(2, weight=0)				# bottom
		self.masframe['borderwidth'] = 2
		self.masframe['relief'] = 'groove'

		"""
		1.1 Top-Left frame
		-------------
		| x | x |   |
		-------------
		| x | x |   |
		-------------
		|   |   |   |
		-------------
		"""
		self.tlframe = ttk.Frame(self.masframe, padding='5')  # frame assignment
		self.tlframe.grid(column=0, row=0, columnspan=2, rowspan=2, sticky='nesw')
		self.tlframe.columnconfigure(0, weight=1)
		self.tlframe.rowconfigure(0, weight=1)
		self.tlframe.rowconfigure(0, weight=0)
		self.tlframe['borderwidth'] = 2
		self.tlframe['relief'] = 'groove'

		# 1.1.1 Figure canvas
		self.figure = plt.Figure(dpi=84, frameon=True, tight_layout=True)		# frameon improves performance
		self.canvas = FigureCanvasTkAgg(self.figure, master=self.tlframe)
		self.canvas.draw()
		self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)	# no grid support
		self.toolbar = NavigationToolbar2Tk(self.canvas, self.tlframe)
		self.toolbar.config(background='white')
		self.toolbar._message_label.config(background='white')
		self.toolbar.update()
		self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)			# no grid object

		"""
		1.2 Top-Right frame
		-------------
		|   |   | x |
		-------------
		|   |   | x |
		-------------
		|   |   |   |
		-------------
		"""
		self.trframe = ttk.Frame(self.masframe, padding='5')
		self.trframe.grid(column=2, row=0, rowspan=2, sticky='nesw')
		self.trframe.columnconfigure(0, weight=1)
		self.trframe.columnconfigure(1, weight=1)
		self.trframe.rowconfigure(0, weight=1)
		self.trframe.rowconfigure(1, weight=1)
		self.trframe.rowconfigure(2, weight=1)
		self.trframe.rowconfigure(3, weight=1)
		self.trframe.rowconfigure(4, weight=1)
		self.trframe.rowconfigure(5, weight=1)
		self.trframe['borderwidth'] = 2
		self.trframe['relief'] = 'groove'

		# 1.2.1 Calibration parameters frame
		self.calframe = ttk.Labelframe(self.trframe, padding='5', text='Calibration Parameters')
		self.calframe.grid(column=0, row=0, columnspan=2, sticky='nesw')
		self.calframe.columnconfigure(0, weight=1)
		self.calframe.columnconfigure(1, weight=0)
		self.calframe.columnconfigure(2, weight=0)
		self.calframe.columnconfigure(3, weight=0)
		self.calframe.columnconfigure(4, weight=0)
		self.calframe.columnconfigure(5, weight=0)
		self.calframe.columnconfigure(6, weight=0)
		self.calframe.rowconfigure(0, weight=1)
		self.calframe.rowconfigure(1, weight=1)
		self.calframe.rowconfigure(2, weight=1)
		self.calframe.rowconfigure(3, weight=1)
		self.calframe.rowconfigure(4, weight=1)
		self.calframe.rowconfigure(5, weight=1)
		self.calframe.rowconfigure(6, weight=1)
		self.calframe.rowconfigure(7, weight=1)

		# Calibration 1 label
		self.cal1label = ttk.Label(self.calframe, text="AMP_i\t[mV/mV]")
		self.cal1label.grid(column=0, row=0, sticky='nw')
		self.cal1label.bind('<Enter>', lambda s: ROOT.after(0, toggle_tooltip("VALUE: Amplifier input gain [mV/mV]. Set to 1.0 for calibration.")))
		self.cal1label.bind('<Leave>', lambda s: ROOT.after(0, toggle_tooltip("")))

		# Calibration 1 text entry
		self.cal1entry = MyNumEntry(self.calframe, state="readonly")
		self.cal1entry.grid(column=2, row=0, columnspan=5, sticky='new', padx=(5, 0))

		# Calibration 2 label
		self.cal2label = ttk.Label(self.calframe, text="AMP_o\t[pA/V]")
		self.cal2label.grid(column=0, row=1, sticky='nw')
		self.cal2label.bind('<Enter>', lambda s: ROOT.after(0, toggle_tooltip("VALUE: Amplifier output gain [pA/V]. Set to 1.0 for calibration.")))
		self.cal2label.bind('<Leave>', lambda s: ROOT.after(0, toggle_tooltip("")))

		# Calibration 2 text entry
		self.cal2entry = MyNumEntry(self.calframe, state="readonly")
		self.cal2entry.grid(column=2, row=1, columnspan=5, sticky='new', padx=(5, 0))

		# Calibration 3 label
		self.cal3label = ttk.Label(self.calframe, text="ADC_m\t[mV/1]")
		self.cal3label.grid(column=0, row=2, sticky='nw')
		self.cal3label.bind('<Enter>', lambda s: ROOT.after(0, toggle_tooltip("VALUE: Analog-to-digital converter input slope [mV/1]. Set to 1.0 for calibration.")))
		self.cal3label.bind('<Leave>', lambda s: ROOT.after(0, toggle_tooltip("")))

		# Calibration 3 text entry
		self.cal3entry = MyNumEntry(self.calframe, state="readonly")
		self.cal3entry.grid(column=2, row=2, columnspan=5, sticky='new', padx=(5, 0))

		# Calibration 4 label
		self.cal4label = ttk.Label(self.calframe, text="ADC_n\t[mV]")
		self.cal4label.grid(column=0, row=3, sticky='nw')
		self.cal4label.bind('<Enter>', lambda s: ROOT.after(0, toggle_tooltip("VALUE: Analog-to-digital converter input intercept [mV]. Set to 0.0 for calibration.")))
		self.cal4label.bind('<Leave>', lambda s: ROOT.after(0, toggle_tooltip("")))

		# Calibration 4 text entry
		self.cal4entry = MyNumEntry(self.calframe, state="readonly")
		self.cal4entry.grid(column=2, row=3, columnspan=5, sticky='new', padx=(5, 0))

		# Calibration 5 label
		self.cal5label = ttk.Label(self.calframe, text="DAC_m\t[1/pA]")
		self.cal5label.grid(column=0, row=4, sticky='nw')
		self.cal5label.bind('<Enter>', lambda s: ROOT.after(0, toggle_tooltip("VALUE: Digital-to-analog converter output slope [1/pA]. Set to 1.0 for calibration.")))
		self.cal5label.bind('<Leave>', lambda s: ROOT.after(0, toggle_tooltip("")))

		# Calibration 5 text entry
		self.cal5entry = MyNumEntry(self.calframe, state="readonly")
		self.cal5entry.grid(column=2, row=4, columnspan=5, sticky='new', padx=(5, 0))

		# Calibration 6 label
		self.cal6label = ttk.Label(self.calframe, text="DAC_n\t[0-4095]")
		self.cal6label.grid(column=0, row=5, sticky='nw')
		self.cal6label.bind('<Enter>', lambda s: ROOT.after(0, toggle_tooltip("VALUE: Digital-to-analog output intercept [0-4095]. Set value for calibration.")))
		self.cal6label.bind('<Leave>', lambda s: ROOT.after(0, toggle_tooltip("")))

		# Calibration 6 text entry
		self.cal6entry = MyNumEntry(self.calframe, state="readonly")
		self.cal6entry.grid(column=2, row=5, columnspan=5, sticky='new', padx=(5, 0))

		# Calibration 7 label
		self.cal7label = ttk.Label(self.calframe, text="VLT_d\t[mV]")
		self.cal7label.grid(column=0, row=7, sticky='nw')
		self.cal7label.bind('<Enter>', lambda s: ROOT.after(0, toggle_tooltip("VALUE: Voltage offset to correct for the liquid junction potential [mV].")))
		self.cal7label.bind('<Leave>', lambda s: ROOT.after(0, toggle_tooltip("")))

		# Calibration 7 text entry
		self.cal7entry = MyNumEntry(self.calframe, state="readonly")
		self.cal7entry.grid(column=2, row=7, columnspan=5, sticky='new', padx=(5, 0))

		# Upload button
		self.uplbutton = ttk.Button(self.trframe, state='disabled', text="Upload", command=upload)
		self.uplbutton.grid(column=0, row=1, sticky='ne', pady=(5, 10))

		# Download button
		self.dwnbutton = ttk.Button(self.trframe, state='disabled', text="Download", command=download)
		self.dwnbutton.grid(column=1, row=1, sticky='nw', pady=(5, 10))

		# 1.2.2 Conductance values frame
		self.conframe = ttk.Labelframe(self.trframe, padding='5', text='Conductance Values')
		self.conframe.grid(column=0, row=2, columnspan=2, sticky='nesw')
		self.conframe.columnconfigure(0, weight=1)
		self.conframe.columnconfigure(1, weight=1)
		self.conframe.columnconfigure(2, weight=1)
		self.conframe.columnconfigure(3, weight=1)
		self.conframe.columnconfigure(4, weight=1)
		self.conframe.columnconfigure(5, weight=1)
		self.conframe.columnconfigure(6, weight=1)
		self.conframe.rowconfigure(0, weight=1)
		self.conframe.rowconfigure(1, weight=1)
		self.conframe.rowconfigure(2, weight=1)
		self.conframe.rowconfigure(3, weight=1)
		self.conframe.rowconfigure(4, weight=1)
		self.conframe.rowconfigure(5, weight=1)
		self.conframe.rowconfigure(6, weight=1)
		self.conframe.rowconfigure(7, weight=1)

		# Conductance 1 label
		self.con1label = ttk.Label(self.conframe, text="G_Shunt\t[nS]")
		self.con1label.grid(column=0, row=0, sticky='nw')
		self.con1label.bind('<Enter>', lambda s: ROOT.after(0, toggle_tooltip("VALUE: Shunting current model conductance [nS].")))
		self.con1label.bind('<Leave>', lambda s: ROOT.after(0, toggle_tooltip("")))

		# Conductance 1 text entry
		self.con1entry = MyNumEntry(self.conframe, state="readonly")
		self.con1entry.grid(column=2, row=0, columnspan=5, sticky='new', padx=(5, 0))

		# Conductance 2 label
		self.con2label = ttk.Label(self.conframe, text="G_H\t[nS]")
		self.con2label.grid(column=0, row=1, sticky='nw')
		self.con2label.bind('<Enter>', lambda s: ROOT.after(0, toggle_tooltip("VALUE: HCN current model conductance [nS].")))
		self.con2label.bind('<Leave>', lambda s: ROOT.after(0, toggle_tooltip("")))

		# Conductance 2 text entry
		self.con2entry = MyNumEntry(self.conframe, state="readonly")
		self.con2entry.grid(column=2, row=1, columnspan=5, sticky='new', padx=(5, 0))

		# Conductance 2 label
		self.con3label = ttk.Label(self.conframe, text="G_Na\t[nS]")
		self.con3label.grid(column=0, row=2, sticky='nw')
		self.con3label.bind('<Enter>', lambda s: ROOT.after(0, toggle_tooltip("VALUE: Sodium current model conductance [nS].")))
		self.con3label.bind('<Leave>', lambda s: ROOT.after(0, toggle_tooltip("")))

		# Conductance 2 text entry
		self.con3entry = MyNumEntry(self.conframe, state="readonly")
		self.con3entry.grid(column=2, row=2, columnspan=5, sticky='new', padx=(5, 0))

		# Conductance 4 label
		self.con4label = ttk.Label(self.conframe, text="OU1_m\t[nS]")
		self.con4label.grid(column=0, row=3, sticky='nw')
		self.con4label.bind('<Enter>', lambda s: ROOT.after(0, toggle_tooltip("VALUE: Excitatory Ornstein-Uhlenbeck mean conductance [nS].")))
		self.con4label.bind('<Leave>', lambda s: ROOT.after(0, toggle_tooltip("")))

		# Conductance 4 text entry
		self.con4entry = MyNumEntry(self.conframe, state="readonly")
		self.con4entry.grid(column=2, row=3, columnspan=5, sticky='new', padx=(5, 0))

		# Conductance 5 label
		self.con5label = ttk.Label(self.conframe, text="OU1_D\t[nS^2/ms]")
		self.con5label.grid(column=0, row=4, sticky='nw')
		self.con5label.bind('<Enter>', lambda s: ROOT.after(0, toggle_tooltip("VALUE: Excitatory Ornstein-Uhlenbeck diffusion constant [nS^2/ms].")))
		self.con5label.bind('<Leave>', lambda s: ROOT.after(0, toggle_tooltip("")))

		# Conductance 5 text entry
		self.con5entry = MyNumEntry(self.conframe, state="readonly")
		self.con5entry.grid(column=2, row=4, columnspan=5, sticky='new', padx=(5, 0))

		# Conductance 6 label
		self.con6label = ttk.Label(self.conframe, text="OU2_m\t[nS]")
		self.con6label.grid(column=0, row=5, sticky='nw')
		self.con6label.bind('<Enter>', lambda s: ROOT.after(0, toggle_tooltip("VALUE: Inhibitory Ornstein-Uhlenbeck mean conductance [nS].")))
		self.con6label.bind('<Leave>', lambda s: ROOT.after(0, toggle_tooltip("")))

		# Conductance 6 text entry
		self.con6entry = MyNumEntry(self.conframe, state="readonly")
		self.con6entry.grid(column=2, row=5, columnspan=5, sticky='new', padx=(5, 0))

		# Conductance 7 label
		self.con7label = ttk.Label(self.conframe, text="OU2_D\t[nS^2/ms]")
		self.con7label.grid(column=0, row=6, sticky='nw')
		self.con7label.bind('<Enter>', lambda s: ROOT.after(0, toggle_tooltip("VALUE: Inhibitory Ornstein-Uhlenbeck diffusion constant [nS^2/ms].")))
		self.con7label.bind('<Leave>', lambda s: ROOT.after(0, toggle_tooltip("")))

		# Conductance 7 text entry
		self.con7entry = MyNumEntry(self.conframe, state="readonly")
		self.con7entry.grid(column=2, row=6, columnspan=5, sticky='new', padx=(5, 0))

		# Conductance 8 label
		self.con8label = ttk.Label(self.conframe, text="G_EPSC\t[nS]")
		self.con8label.grid(column=0, row=7, sticky='nw')
		self.con8label.bind('<Enter>', lambda s: ROOT.after(0, toggle_tooltip("VALUE: Maximal excitatory postsynaptic potential conductance [nS].")))
		self.con8label.bind('<Leave>', lambda s: ROOT.after(0, toggle_tooltip("")))

		# Conductance 8 text entry
		self.con9entry = MyNumEntry(self.conframe, state="readonly")
		self.con9entry.grid(column=2, row=7, columnspan=5, sticky='new', padx=(5, 0))

		# Start button
		self.strbutton = ttk.Button(self.trframe, state='disabled', text="Start", command=start)
		self.strbutton.grid(column=0, row=3, sticky='ne', pady=(5, 10))

		# Stop button
		self.stpbutton = ttk.Button(self.trframe, state='disabled', text="Stop", command=stop)
		self.stpbutton.grid(column=1, row=3, sticky='nw', pady=(5, 10))

		# 1.2.3 Command frame
		self.cmdframe = ttk.Labelframe(self.trframe, padding='5', text='Manual Command')
		self.cmdframe.grid(column=0, row=4, columnspan=2, sticky='esw')
		self.cmdframe.columnconfigure(0, weight=1)
		self.cmdframe.columnconfigure(1, weight=1)
		self.cmdframe.columnconfigure(2, weight=1)
		self.cmdframe.columnconfigure(3, weight=1)
		self.cmdframe.columnconfigure(4, weight=1)
		self.cmdframe.columnconfigure(5, weight=1)
		self.cmdframe.columnconfigure(6, weight=1)
		self.cmdframe.rowconfigure(0, weight=1)

		# Carriage return label
		self.crlabel = ttk.Label(self.cmdframe, text="<cr>")
		self.crlabel.grid(column=0, row=0, sticky='nw', padx=(0, 5))

		# Command index text entry
		self.idxentry = MyNumEntry(self.cmdframe, width=8)
		self.idxentry.grid(column=1, row=0, columnspan=2, sticky='new')

		# Tabulator label
		self.tblabel = ttk.Label(self.cmdframe, text="<tb>")
		self.tblabel.grid(column=3, row=0, sticky='nw', padx=(5, 5))

		# Command value text entry
		self.valentry = MyNumEntry(self.cmdframe, width=8)
		self.valentry.grid(column=4, row=0, columnspan=2, sticky='new')

		# Linefeed label
		self.lflabel = ttk.Label(self.cmdframe, text="<lf>")
		self.lflabel.grid(column=6, row=0, sticky='nw', padx=(5, 0))

		# Send button
		self.sndbutton = ttk.Button(self.trframe, state='disabled', text="Send", command=send)
		self.sndbutton.grid(column=0, row=5, columnspan=2, sticky='n', pady=(5, 10))

		"""
		1.3 Bottom-Right frame
		-------------
		|   |   |   |
		-------------
		|   |   |   |
		-------------
		|   |   | x |
		-------------
		"""
		self.brframe = ttk.Frame(self.masframe, padding='5')
		self.brframe.grid(column=2, row=2, sticky='nesw')
		self.brframe.columnconfigure(0, weight=1)
		self.brframe.rowconfigure(0, weight=1)
		self.brframe['borderwidth'] = 2
		self.brframe['relief'] = 'groove'

		# 1.3.1 Timer frame
		self.clkframe = ttk.Labelframe(self.brframe, padding='5', text='Experiment Timer')
		self.clkframe.grid(column=0, sticky='nesw')
		self.clkframe.columnconfigure(0, weight=1)
		self.clkframe.columnconfigure(1, weight=1)
		self.clkframe.columnconfigure(2, weight=1)
		self.clkframe.columnconfigure(3, weight=1)
		self.clkframe.columnconfigure(4, weight=1)
		self.clkframe.columnconfigure(5, weight=1)
		self.clkframe.columnconfigure(6, weight=1)
		self.clkframe.rowconfigure(0, weight=1)

		# Time label
		self.clklabel = ttk.Label(self.clkframe, text="[hh: mm: ss]")
		self.clklabel.grid(column=0, row=0, sticky='nw')

		# Time text entry
		self.clkentry = MyTextEntry(self.clkframe, state='readonly')
		self.clkentry.grid(column=2, row=0, columnspan=5, sticky='new', padx=(5, 0))

		"""
		1.4 Bottom-Left frame
		-------------
		|   |   |   |
		-------------
		|   |   |   |
		-------------
		| x | x |   |
		-------------
		"""
		self.blframe = ttk.Frame(self.masframe, padding='5')
		self.blframe.grid(column=0, row=2, columnspan=2, sticky='nesw')
		self.blframe.columnconfigure(0, weight=0)
		self.blframe.columnconfigure(1, weight=1)
		self.blframe.columnconfigure(2, weight=0)
		self.blframe.rowconfigure(0, weight=1)
		self.blframe.rowconfigure(1, weight=1)
		self.blframe['borderwidth'] = 2
		self.blframe['relief'] = 'groove'

		# 1.4.1 Port frame
		self.prtframe = ttk.Labelframe(self.blframe, padding=('5', '0', '5', '5'), text='Port')
		self.prtframe.grid(column=0, row=0, sticky='nesw')
		self.prtframe.columnconfigure(0, weight=1)
		self.prtframe.rowconfigure(0, weight=1)

		# Port option menu
		self.prtmenu = MyPortOptionMenu(self.prtframe)
		self.prtmenu.grid(column=0, row=0, sticky='nesw')
		self.prtmenu.bind('<Enter>', self.prtmenu.update_port_options)	# create options
		self.prtmenu.bind('<Configure>', self.prtmenu.callback)			# option selected

		# 1.4.2 Status frame
		self.stsframe = ttk.Labelframe(self.blframe, padding='5', text='Status')
		self.stsframe.grid(column=1, row=0, sticky='nesw', padx=(10, 0))
		self.stsframe.columnconfigure(0, weight=1)
		self.stsframe.rowconfigure(0, weight=1)

		# Status text entry
		self.stsentry = MyTextEntry(self.stsframe, state='readonly')
		self.stsentry.grid(column=0, row=0, sticky='new')

		# 1.4.3 Report frame (invisible)
		self.repframe = ttk.Frame(self.blframe, padding=('10', '13', '5', '5'))
		self.repframe.grid(column=2, row=0, columnspan=2, sticky='nesw')
		self.repframe.columnconfigure(0, weight=1)
		self.repframe.rowconfigure(0, weight=1)

		# Report button
		self.repbutton = MyCheckbutton(self.repframe, text="Live Reports\n(Inactive)", command=report)
		self.repbutton.grid(column=0, row=0, sticky='nsew')

# 0.0 Root window
ROOT = tk.Tk()
ROOT.minsize(width=960, height=540)
ROOT.columnconfigure(0, weight=1)
ROOT.rowconfigure(0, weight=1)
ROOT.title("pyClamp 1.0 (GUI for dyClamp)")

# 0.1 Footer
AUTHOR = tk.Label(ROOT, text="© Christian Rickert <mail@crickert.de>")
AUTHOR.grid(column=0, row=1, sticky=('e', 'w'))
RESIZER = ttk.Sizegrip(ROOT)
RESIZER.grid(column=0, row=1, sticky=('s', 'e'))

# Start GUI elements
PYCLAMP = PYCLAMP()
PYCLAMP.stsentry.var.set(STATUS)
initialize_plot()		# create plot before animation
initialize_animation()	# update plot regularly
update_timer()			# update timer regularly
ROOT.after(1, lambda: ANIM.event_source.stop())	# suspend animation
ROOT.protocol('WM_DELETE_WINDOW', _quit)
ROOT.mainloop()
