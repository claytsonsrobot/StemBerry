#!/usr/bin/python3
#do not erase (needed to be executable for autostart)

'''
StemBerry V.84
Last updated: 8/27/2022
Dev: Clayton Bennett
OG dev: Austin Bebee
Description: SOCEM GUI. Connect RPi to Arduino, collect raw data. Save text inputs.

Contents (in order):
- Libraries
- Global Variables
- Global Functions
- GUI Class
    - Home / geo. input screen
    - Data collection screen
        - Runs data collection function
        - Stores data & saves data
        - Plots F v D graph
    - Load cell calibration screen
    - Error report screen
- Excute GUI command

V15
    - Change to 9 cell and 3 range count inputs
V19
    - Rip out defunct calculations
    - Clean up code, specifically by organizing statements of place for tkinter items
V37
    - Dial in functionality with pretty new GUI.
    - barbottom (not barmiddle) set to 70%-90% of stem height
V42
    - Develop top level methods
V50
    - Functional save state, save files, naming convention edge cases, and crisp appearance

V54
    - Generate CSV's, suppress XLSX's
V56
    - Retain 9-cell variables, for EI assessment upon saving counts, without reopening CSV files
V67
    - So many things.
v77
    - Serial collection functial, drinking from a waterhose, high hz
    - Tare button message.
    - PeakClick popup window.

V84
    - The way peak clicks are handled and saved was moved to the inside of the choose peaks code, becuase plt.show() won't give up.
    - Shut down plt.show after CSV file is saved.

Fix:
- Fix serial connection problem between RasPi and Arduino (mostly fixed)
- Check that the Aruino is recieving ser.write characters ('x','d','s','t') # resolved
- Compile Csv's into Excel workbook # can be done
- Remove auto graph button, or at least uncheck it: use it to refer to auto clicker
- Develop autoclicker to be used for more than just side hits
- Finish autoclicker by setting plt.show() into an inset tkinter gui popup, and then mainloop.
     Use: FigureCanvasTkAgg,NavigationToolbar2Tk,plt,Cursor.
- dev port is currently defined manually, given dev_manualOverride
- move header variable inputs
- make directory inputtable using dropdown menu item and textbox
- upgrade tkinter items to CustomTkinter
- PRIORITY: CREATE BASE NAME FROM VARIABLE AND PLOT: GUI.filename_force.get() is getting dangerous.
     
Notes:
- exec() is your friend. Use is to run multiple lines of code which you can copy and paste into a shell, using triple '  commenting
- save as separate CSV files, then as one combined XLSX file with multiple pages
'''


#Make sure this is USB address for saving data to
usb = '/media/pi/0000-0001' # update code so data is saved here too
#Data File Saving Locations:
address = '/home/pi/Desktop/SOCEM_data_2022'
address = r'C:\Users\clayton\OneDrive - University of Idaho\AqMEQ\SOCEM\Data - Instron and SOCEM - 2020, 2021\SOCEM_DATA_2021'
path = address
#address = '/home/pi/Desktop/SAVED DATA 2019/RAW_'

''' Libraries '''
import serial
from serial import Serial
# from serial import *
import serial.tools.list_ports # need this
import tkinter as tk
from tkinter import * # tk.Label == Label, tk.Button == Button, tk.Entry == Entry
import threading
from multiprocessing import Process
import csv

import matplotlib
from matplotlib import style
matplotlib.use("TkAgg")

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
#import matplotlib.animation as animation

import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor

#import EI_Interaction_Fx
#import EI_No_Interaction_Fx
import itertools
from itertools import zip_longest
import subprocess
import sys
import os
from os import path
import numpy as np
import pandas as pd
#import optiH # script that determine optiaml force bar height
#import peakutils
#from PeakUtils.Plot import plot as pplot
import math
import struct
from PIL import ImageTk,Image
import datetime
from datetime import date
import time
#from time import time
#import PeakClick_vCurrent
#peakclick = PeakClick_vCurrent.peakclick
    

''' Global Variables '''
script = os.path.basename(__file__)
directory = os.path.dirname(__file__)
collect = True # controls data collection loop from GUI frontend
today = date.today()
datestring = today.strftime("%b-%d-%Y")
ignoreserial = False # True 
#ignoreserial = True # delete this # if RecordForce.ser.isOpen() == False:
barlength = 76 # cm. this shouldn't ever change, unless the bar is replaced. i.e. the width of a side hit cell.
dev_manualOverride = True
dev_manual = 'COM3' # manual override
useInitialPlot_PeackClick = False
disReferenced_PeakClick = False
#dev_manual = 'COM7' # manual override
# Constants
barradius = 1 # 1 cm = 0.32 inches
default_stemheight = 20.0 # cm
initial_barbottomOverStemheight_coeff = 0.8
convert_KgToLbs = 2.20462262 #kg to lbs
convert_KgToN = 9.81 #kg to N # CHECK FOR ACCURACY CB 8/9/2022
inchonvert = (((math.pi*(0.764))*31.4136)/359) # converts displacement to inches, wheel diameter = 31.4136
visualizeDatastream = False #True #set to live graph for data display
#visualizeDatastream = True
# visualizeDatastream ( search: "def datafeed(" ) is broken right now. Refer to earlier versions (pre v65)for reference of how Bebee left it.

'''
try:
    import EI_Interaction_Fx
    import EI_No_Interaction_Fx
except:
    print("Put EI_Interaction_Fx.py and EI_No_Interaction_Fx.py in directory.")
'''
''' matplotlib Graph Settings '''
'''
style.use("ggplot")
f = Figure(figsize=(4.85,3.9), dpi=75)
a = f.add_subplot(111)
a.set_ylim(0, 25)
'''

''' Methods'''
# Determine Arduino serial port address
def SerConnect():
    #try:
    ports = serial.tools.list_ports.comports()
    try:
        dev = ports[0].device
    except:
        dev = '/dev/ttyACM0' # only works on pi
    if dev_manualOverride == True:
        dev = dev_manual # manual override
    try:
        ser = serial.Serial(dev, 115200, timeout=4,writeTimeout = 2,) # 1 second timeout
        #print(type(ser))
        print("dev = "+dev)
        ser.reset_input_buffer()  
        #ser.isOpen()
        #GUI.ignoreserial = False
        return ser # this is the only spot it should be called ser, not RecordForce.ser
    
    except:
        GUI.ignoreserial = True
        error = 'serial connection never established'
        eCode = 'e1' # eCode = e1
        GUI.errors.append(error) # append error label
        GUI.errorCodes.append(eCode) # append error code
        #popup('serial connection')
        print("eCode = "+eCode)
        
        

# if serial disconnect (unplugged) reconnect - NOTE: doesn't properly work currently. 
def SerReconnect():
    try:
    #if GUI.ignoreserial == False:
        GUI.ignoreserial = False
        try:
            RecordForce.ser.close()
            GUI.ignoreserial = False
        except:
            GUI.ignoreserial = True
        RecordForce.ser = SerConnect()
        print("SerReconnect()")
    except:
    #else:
        GUI.ignoreserial = True
        print("\nYou hit the 'SerReconnect' dropdown menu item while GUI.ignoreserial == True.\nSerial cannot be reconnected because\neither an arduino is not connected to your computer\nor the arduino is not sought by StemBerry.")
        RecordForce.message_connectArduino()

def overwriteGuard(filename):# prevents overwriting by checking if filename already exists in saving folder
        return path.exists(filename) # True = already exits, False = doesn't exist
    
def overwriteGuardPage(filename):# prevents overwriting by checking if filename already exists in saving folder
        #return path.exists(filename) # True = already exits, False = doesn't exist
        return False # don't mess up!
    
def data_display(visual): #changes display method    #DELETE?
    global visualizeDatastream
    visualizeDatastream = visual
    return visualizeDatastream

#if any error occurs, display popup error msg
def popup(error):
    popup = tk.Tk()
    popup.wm_title("Error")
    E_label = Label(popup, text="A {} error occurred.".format(error), font=("arial", 12, "bold"))
    E_label.pack(side="top", fill="x", pady=10)               
    popup.mainloop()

def popup_chooseFolder():
    popup_chooseFolder = tk.Tk()
    popup_chooseFolder.wm_title("Choose Folder")
    E_label = Label(popup_chooseFolder, text="Paste file output directory here.", font=("arial", 12, "bold"))
    #E_label.pack(side="top", fill="x", pady=10)
    E_label.grid(row=0, column=1)
    #GUI.addressInput.set("")
    folder_entry = Entry(popup_chooseFolder, textvariable=GUI.addressInput, font = ("arial", 11, "bold"), width= 70, bg="white", fg="gray1")
    folder_entry.grid(row=1, column=1)
    save_button = Button(popup_chooseFolder,text = "Save", font = ("arial", 14, "bold"), height = 1, width = 6, fg = "ghost white", bg = "dodgerblue3",command=lambda:updateAdress())
    save_button.grid(row=2, column=1)
    popup_chooseFolder.mainloop()
    
    ''' Frame: Folder Input Field''
    barset_frame = tk.LabelFrame(self, text='Bar Bottom Quickset',font = ("arial", 14, "bold"), width= 10, bg="white", fg="gray1")
    barset_frame.place(x = 340, y = 230)
    ''' ''

def updateAdress():
    print("updateAddress is broken. Please develop.")
    print("GUI.addressInput.get() = ",GUI.addressInput.get())
    print("GUI.address = ",GUI.address)
    #GUI.address = GUI.addressInput.get() # broken right now
    #print("GUI.address = ",GUI.address)

def showErrors():
    GUI.show_frame(ErrorReport) # show Error Report page
    ErrorReport.showErrors2(GUI.frames[ErrorReport]) # display errors in lists

def update_filename_preTest():
    filename_preTest = nameBlackBox("preTest",GUI.filename_preTest.get())
    GUI.filename_preTest.set(filename_preTest)
    filename_all = filename_preTest.replace("preTest","all")
    GUI.filename_all.set(filename_all)

def testForNineCellFilename(): # used to identify when nine-cell force, distance, and time data exists, and passes it to state data.
    # the purpose of this is to avoid reopening CSV files in order to assess nine-cell data
    # because, we have to wait for counts after to assess EI
    # it would be easier to test right away to get peaks
    # have a check box for nine cell test
    # EI cannot be assessed for non-nine cell, because counts don't exist
    # if box not checked, post test frame goes to single input for stem count, one number, with another number for range distance of count
    # # Assessment is trigged at save state button push
    ninecellfilename = GUI.varietyname.get()+","+GUI.plotname.get()+"_"
    ninecellfilename_side1 = ninecellfilename+"_side1"
    ninecellfilename_side2 = ninecellfilename+"_side2"
    ninecellfilename_side3 = ninecellfilename+"_side3"
    ninecellfilename_forward = ninecellfilename+"_foward"
    currentFilename_force = GUI.filename_force.get()
    # create GUI variable, for handling without reopening CSV's
    #if (currentFilename_force == ninecellfilename_side1):
    if (GUI.currentdirection.get() == "side1"):
        GUI.forcePushed_side1 = GUI.forcePushed
        GUI.distanceTraveled_side1 = GUI.distanceTraveled
        GUI.timeElapsed_side1 = GUI.timeElapsed
        #if (currentFilename_force == ninecellfilename_side2):
    if (GUI.currentdirection.get() == "side2"):
        GUI.forcePushed_side2 = GUI.forcePushed
        GUI.distanceTraveled_side2 = GUI.distanceTraveled
        GUI.timeElapsed_side2 = GUI.timeElapsed
        #if (currentFilename_force == ninecellfilename_side3):
    if (GUI.currentdirection.get() == "side3"):
        GUI.forcePushed_side3 = GUI.forcePushed
        GUI.distanceTraveled_side3 = GUI.distanceTraveled
        GUI.timeElapsed_side3 = GUI.timeElapsed
        #if (currentFilename_force == ninecellfilename_forward):
    if (GUI.currentdirection.get() == "forward"):
        GUI.forcePushed_forward = GUI.forcePushed
        GUI.distanceTraveled_forward = GUI.distanceTraveled
        GUI.timeElapsed_forward = GUI.timeElapsed
    
def createBackupFile():
    ''' Create a temp text file, with a list of all variables and variable names, that would be awesome '''
    '''update_filename_preTest()
    update_filename_postTest()
    sniff_filename_force()
    update_filename_postTest()
    saveState_update_filenames()'''
    now = datetime.datetime.now()
    unix_now = time.mktime(now.timetuple())
    unix_now_int = int(unix_now) # still gets seconds # the purpose of this is to append to filenames
    str(unix_now_int)
    filename_savestate = "backup_stemberry_"+str(unix_now_int)+".txt"
    filename_savestate_full = GUI.address+"/"+filename_savestate
    print("State saved at "+str(datetime.datetime.fromtimestamp(unix_now_int))+": "+filename_savestate)
    # list all GUI vars, add them to a txt file
    GUI.masslist=[GUI.cell1Mass.get(),GUI.cell2Mass.get(),GUI.cell3Mass.get(),GUI.cell4Mass.get(),GUI.cell5Mass.get(),GUI.cell6Mass.get(),GUI.cell7Mass.get(),GUI.cell8Mass.get(),GUI.cell9Mass.get()] 
    GUI.stemcounts=[GUI.cell1Count.get(),GUI.cell2Count.get(),GUI.cell3Count.get(),GUI.cell4Count.get(),GUI.cell5Count.get(),GUI.cell6Count.get(),GUI.cell7Count.get(),GUI.cell8Count.get(),GUI.cell9Count.get()] 
    GUI.diameters_cell1 = [GUI.cell1Diameter1.get(),GUI.cell1Diameter2.get(),GUI.cell1Diameter3.get(),GUI.cell1Diameter4.get()]
    GUI.diameters_cell2 = [GUI.cell2Diameter1.get(),GUI.cell2Diameter2.get(),GUI.cell2Diameter3.get(),GUI.cell2Diameter4.get()]
    GUI.diameters_cell3 = [GUI.cell3Diameter1.get(),GUI.cell3Diameter2.get(),GUI.cell3Diameter3.get(),GUI.cell3Diameter4.get()]
    GUI.diameters_cell4 = [GUI.cell4Diameter1.get(),GUI.cell4Diameter2.get(),GUI.cell4Diameter3.get(),GUI.cell4Diameter4.get()]
    GUI.diameters_cell5 = [GUI.cell5Diameter1.get(),GUI.cell5Diameter2.get(),GUI.cell5Diameter3.get(),GUI.cell5Diameter4.get()]
    GUI.diameters_cell6 = [GUI.cell6Diameter1.get(),GUI.cell6Diameter2.get(),GUI.cell6Diameter3.get(),GUI.cell6Diameter4.get()]
    GUI.diameters_cell7 = [GUI.cell7Diameter1.get(),GUI.cell7Diameter2.get(),GUI.cell7Diameter3.get(),GUI.cell7Diameter4.get()]
    GUI.diameters_cell8 = [GUI.cell8Diameter1.get(),GUI.cell8Diameter2.get(),GUI.cell8Diameter3.get(),GUI.cell8Diameter4.get()]
    GUI.diameters_cell9 = [GUI.cell9Diameter1.get(),GUI.cell9Diameter2.get(),GUI.cell9Diameter3.get(),GUI.cell9Diameter4.get()]

    lines = [
        'Units: diameter (mm), height (cm), range (cm), length (cm), mass (kg) \n',
        'script = '+script,
        'directory = '+directory+'/',
        'collect = '+str(collect),
        'GUI.ignoreserial = '+str(GUI.ignoreserial),
        'barlength = '+str(barlength),
        'datestring = '+datestring,
        'today = '+str(today),
        'now = '+str(now),
        'unix_now '+str(unix_now),
        'unix_now_int = '+str(unix_now_int),
        'backup filename unix_now_int decoded: '+ str(datetime.datetime.fromtimestamp(unix_now_int))+'\n',
        'GUI.timestring.get() = '+GUI.timestring.get(),
        'GUI.errors = '+makeDataString(GUI.errors),
        'GUI.errorCodes = '+makeDataString(GUI.errorCodes),
        'GUI.varietyname.get() = '+GUI.varietyname.get(),
        'GUI.plotname.get() = '+GUI.plotname.get(),
        'GUI.currentdirection.get() = '+GUI.currentdirection.get(),
        'RecordForce.collect = '+str(RecordForce.collect),
        'GUI.filename_force.get() = '+GUI.filename_force.get(),
        'GUI.filename_preTest.get() = '+GUI.filename_preTest.get(),
        'GUI.filename_postTest.get() = '+GUI.filename_postTest.get(),
        'GUI.stemheight.get() = '+str(GUI.stemheight.get()),
        'GUI.barmiddle.get() = '+str(GUI.barmiddle.get()),
        'GUI.barbottom.get() = '+str(GUI.barbottom.get()),
        'GUI.passfillednames_checkbox.get() = '+str(GUI.passfillednames_checkbox.get()),
        'GUI.startRange1.get() = '+str(GUI.startRange1.get()),
        'GUI.startRange2.get() = '+str(GUI.startRange2.get()),
        'GUI.startRange3.get() = '+str(GUI.startRange3.get()),
        'GUI.travelvelocity = '+str(GUI.travelvelocity),
        'GUI.samplingrate = '+str(GUI.samplingrate),
        'GUI.masslist = '+makeDataString(GUI.masslist),
        'GUI.stemcounts = '+makeDataString(GUI.stemcounts),
        'GUI.diameters_cell1 = '+makeDataString(GUI.diameters_cell1),
        'GUI.diameters_cell2 = '+makeDataString(GUI.diameters_cell2),
        'GUI.diameters_cell3 = '+makeDataString(GUI.diameters_cell3),
        'GUI.diameters_cell4 = '+makeDataString(GUI.diameters_cell4),
        'GUI.diameters_cell5 = '+makeDataString(GUI.diameters_cell5),
        'GUI.diameters_cell6 = '+makeDataString(GUI.diameters_cell6),
        'GUI.diameters_cell7 = '+makeDataString(GUI.diameters_cell7),
        'GUI.diameters_cell8 = '+makeDataString(GUI.diameters_cell8),
        'GUI.diameters_cell9 = '+makeDataString(GUI.diameters_cell9),
        'GUI.EI_fullcontact = '+makeDataString(GUI.EI_fullcontact),
        'GUI.EI_intermediatecontact = '+makeDataString(GUI.EI_intermediatecontact),
        'GUI.EI_nocontact = '+makeDataString(GUI.EI_nocontact),
        'GUI.AvgEI_intermediatecontact = '+makeDataString(GUI.AvgEI_intermediatecontact),
        str(datetime.datetime.now())+'\n']

    
    evenmorelines = [
        'GUI.filename_all.get() = '+GUI.filename_all.get(), # no longer exists, compilation XLSX
        'GUI.distanceTraveled = '+makeDataString(GUI.distanceTraveled),
        'GUI.forcePushed = '+makeDataString(GUI.forcePushed),
        'GUI.timeElapsed = '+makeDataString(GUI.timeElapsed)+'\n',
        'Collected data, nine cell scheme:',
        'GUI.forcePushed_side1 = '+makeDataString(GUI.forcePushed_side1),
        'GUI.distanceTraveled_side1 = '+makeDataString(GUI.distanceTraveled_side1),
        'GUI.timeElapsed_side1 = '+makeDataString(GUI.timeElapsed_side1),
        'GUI.forcePushed_side2 = '+makeDataString(GUI.forcePushed_side2),
        'GUI.distanceTraveled_side2 = '+makeDataString(GUI.distanceTraveled_side2),
        'GUI.timeElapsed_side2 = '+makeDataString(GUI.timeElapsed_side2),
        'GUI.forcePushed_side3 = '+makeDataString(GUI.forcePushed_side3),
        'GUI.distanceTraveled_side3 = '+makeDataString(GUI.distanceTraveled_side3),
        'GUI.timeElapsed_side3 = '+makeDataString(GUI.timeElapsed_side3),
        'GUI.forcePushed_forward = '+makeDataString(GUI.forcePushed_forward),
        'GUI.distanceTraveled_forward = '+makeDataString(GUI.distanceTraveled_forward),
        'GUI.timeElapsed_forward = '+makeDataString(GUI.timeElapsed_forward),
        str(datetime.datetime.now())]
        
    try:
        morelines = [
            '\n',
            'RecordForce.ser = '+str(RecordForce.ser),
            str(datetime.datetime.now())]
    except:
        morelines = [
            '\n',
            'RecordForce.ser = '+'error',
            str(datetime.datetime.now())]
    
    with open(filename_savestate_full, 'w') as f:
        f.write('\n'.join(lines))
        f.write('\n'.join(morelines))
        try:
            f.write('\n'.join(evenmorelines))
        except:
            pass

def makeDataString(dataVector):
    #timeElapsed_string = ' '.join(str(e) for e in GUI.timeElapsed)
    dataString = ' '.join(str(e) for e in dataVector)
    return dataString

'''
#def ninecellpuzzler():
    put together known pieces, and then calculate EI for each cell
    don't even worry about forward hits right now
    BUt putting together where side hits line up in the forward hit will be good.
'''

def restoreState():
    print("Please develop.")
    # choose txt file (example: backup_stemberry_1660192559.txt
    # trigger GUI directory and file selection would be sick.
    # only restore postTest fields? start there. 

def rename(filename): #if filename already exists - prompt user to rename
    popup = tk.Tk()
    popup.wm_title('Prompt Rename')
    renameIt = Label(popup, text = 'Filename\n"{}"\nalready exists in the saving location.\nPlease rename and press Save.'.format(filename), font = ('arial', 10, 'bold'))
    increment_button = Button(popup,text = "Auto Modify", font = ("arial", 14, "bold"), height = 2, width = 6, fg = "ghost white", bg = "dodgerblue3",command=lambda:incrementRename(filename))
    overwrite_button = Button(popup, text = "Overwrite", font = ("arial", 14, "bold"), height = 2, width = 6, fg = "ghost white", bg = "red4",command=lambda:overwrite(filename))
    
    
    renameIt.pack(side='top', fill='x', ipadx=10, ipady=10)
    increment_button.pack(side='top', fill='both', ipadx=10, ipady=1)
    overwrite_button.pack(side='top', fill='both', ipadx=10,ipady=1)

    popup.mainloop()
def renamePage(filename):
    print("Please develop, prevent pages from being overwritten in the filename_all spreadsheet")
    
def incrementRename(filename):
    print("please develop, auto modify filename")
    
def overwrite(filename):
    print("please develop, overwrite filename")
        
#closes GUI (from file menubar)
def close():
    createBackupFile()
    python = sys.executable
    os.execl(python, python, * sys.argv)

def datafeed():
    #frame = tk.Frame.RecordForce
    frame = RecordForce.container
    RecordForce.datafeed_frame
    print("frame = ",frame)
    if visualizeDatastream == True:# data displayed in scrollbars (default)
        # Displays incoming data
        # scroll = Scrollbar(RecordForce.datafeed_frame)
        scroll = Scrollbar(frame)# what is this? TK!
        print("scroll = ",scroll)
        #scroll = Scrollbar(self)# what is this? TK!
        ''
        RecordForce.time_label = Label(RecordForce.datafeed_frame, text = "Time (s)",font = ("arial", 14, "bold"), fg = "dodgerblue3", bg = "ghost white")
        RecordForce.Timelist = Listbox(RecordForce.datafeed_frame, yscrollcommand = scroll.set, bg = "ghost white",highlightbackground = "gray2", width = 7, height = 1, font = ("arial", 14, "bold"), fg = "dodgerblue3")
        RecordForce.dis_label = Label(RecordForce.datafeed_frame, text = "Distance (cm)",font = ("arial", 14, "bold"), fg = "dodgerblue3", bg = "ghost white")
        RecordForce.Dislist = Listbox(RecordForce.datafeed_frame, yscrollcommand = scroll.set, bg = "ghost white",highlightbackground = "gray2", width = 7, height = 1, font = ("arial", 14, "bold"), fg = "dodgerblue3")
        RecordForce.force_label = Label(RecordForce.datafeed_frame, text = "Force (N)",font = ("arial", 14, "bold"), fg = "dodgerblue3", bg = "ghost white")
        RecordForce.Forcelist = Listbox(RecordForce.datafeed_frame, yscrollcommand = scroll.set, bg = "ghost white",highlightbackground = "gray2", width = 7, height = 5, font = ("arial", 14, "bold"), fg = "dodgerblue3")
        '''
        RecordForce.time_label = Label(frame, text = "Time (s)",font = ("arial", 14, "bold"), fg = "dodgerblue3", bg = "ghost white")
        RecordForce.Timelist = Listbox(frame, yscrollcommand = scroll.set, bg = "ghost white",highlightbackground = "gray2", width = 7, height = 1, font = ("arial", 14, "bold"), fg = "dodgerblue3")
        RecordForce.dis_label = Label(frame, text = "Distance (cm)",font = ("arial", 14, "bold"), fg = "dodgerblue3", bg = "ghost white")
        RecordForce.Dislist = Listbox(frame, yscrollcommand = scroll.set, bg = "ghost white",highlightbackground = "gray2", width = 7, height = 1, font = ("arial", 14, "bold"), fg = "dodgerblue3")
        RecordForce.force_label = Label(frame, text = "Force (N)",font = ("arial", 14, "bold"), fg = "dodgerblue3", bg = "ghost white")
        RecordForce.Forcelist = Listbox(frame, yscrollcommand = scroll.set, bg = "ghost white",highlightbackground = "gray2", width = 7, height = 5, font = ("arial", 14, "bold"), fg = "dodgerblue3")
        '''
        RecordForce.time_label.place(x = 180, y = 110)

        RecordForce.Timelist.place(x = 180, y = 140)
        RecordForce.dis_label.place(x = 280, y = 110)
        RecordForce.Dislist.place(x = 280, y = 140)
        RecordForce.force_label.place(x = 420, y = 110)
        RecordForce.Forcelist.place(x = 420, y = 140)

    else:# user decided for no data display
        try:#clear scrollbars if they were there
            RecordForce.Dislist.place_forget()
            RecordForce.Forcelist.place_forget()
            RecordForce.Timelist.place_forget()
            RecordForce.dis_label.place_forget()
            RecordForce.force_label.place_forget()
            RecordForce.time_label.place_forget()
        except:# no scrollbars
            pass
        
def passData():

    '''Scrollbars Options'''
    # if scrollbars option = on:
    if visualizeDatastream == True:
        try: # puts data on GUI display by default (user can turn off)
            
            RecordForce.Dislist.insert(END, str(GUI.distanceTraveled[i]))# inserts at end of listbox to actually display
            RecordForce.Dislist.see(END)# makes sure listbox is at end so it displays live data
            RecordForce.Forcelist.insert(END, str('%.2f' % GUI.forcePushed[i]))
            RecordForce.Forcelist.see(END)
            RecordForce.Timelist.insert(END, str('%.2f' % GUI.timeElapsed[i]))
            RecordForce.Timelist.see(END)

            #scrollbars options = off
            '''
        except:
            pass
        '''
        except:
            GUI.errors.append('data append') # label 
            eCode = 'e4'
            GUI.errorCodes.append(eCode)
            print("eCode = "+eCode) # eCode = e4
                

# * # DATA COLLECTION FUNCTION - Acquires live data from Arduino # * #
def collectData():
    hang=0
    nothingToRead=0 # controls timeout
    blankline = "b'\n"
    while RecordForce.hasStarted==True and RecordForce.hasSentStop==False:
        #time.sleep(0.02)
        bytecount = RecordForce.ser.in_waiting
        print("RecordForce.ser.in_waiting = ",bytecount)
        if bytecount > 5 and RecordForce.hasSentStop==False: # this does happen
            print("datachunk...") # stopping after this
            
            try:
                time.sleep(0.2) # no luck
                #ser_bytes = RecordForce.ser.readline()
                ser_bytes = RecordForce.ser.read(bytecount)
                #ser_bytes = RecordForce.ser.read(1)
                
                if blankline in str(ser_bytes):
                    print("blankline")
                    continue
                # first time: ser_bytes =  b'0.00|-23.280\r'
                # second time: ser_bytes =  b'\n0.00|'
                # failure correlates with RecordForce.ser.in_waiting =  5
                # sometimes: ser_bytes =  b'0.00|0.000\r\n0.00|', shows next one is printing preemtively
            except:
                print("Failed: ser_bytes = RecordForce.ser.readline()")
                continue
            hang = 0
            nothingToRead=0
            #print("ser_bytes = ",ser_bytes)
            line = ser_bytes.decode('utf-8').rstrip()
            datapacket = line.splitlines()
            # parse datapacket
            for i in datapacket:
                split = i.split("|")
                if RecordForce.hasSentStop == False:
                    try:
                        #print("split = ",split, float(split[0]),float(split[1]),float(split[2]))
                        print("split = ",split)
                        distance = round(float(split[0]),3)
                        force = round(float(split[1]),3)
                        timetick = round(float(split[2]),3)
                        GUI.timeElapsed.append(timetick)# list of GUI.distanceTraveled time
                        GUI.distanceTraveled.append(distance)# list of inches traveled @ does this happen with the whole list, or one element at a time?
                        GUI.forcePushed.append(force)# list of force traveled
                    except:
                        print("missed a line, list index out of range.")
                        pass
                
                
            if line =="Stopped!": 
                RecordForce.sendStop()
                
        # the purpose of this elif is to allow the while loop to iterate if there's nothing to read.
        # But also, it has primarily been entered if the serial connection has already timed out
        elif bytecount < 6 and bytecount > 0 : 
            ser_bytes = RecordForce.ser.read(bytecount)
            #print("ser_bytes = ",ser_bytes)
            nothingToRead +=1
            if nothingToRead>5: # if the while loop goes through five iterations, without seeing anything worth recording, give up.
                RecordForce.sendStop()
                print("Hung up.")
                SerReconnect()
                GUI.show_frame(InitialInputs)
        else:
            hang +=1
            print("go back to top of while loop")
            if hang>10: # if the while loop goes through ten iterations of radio silence, give up. The serial connection probably timed out. search 'timeout = '
                RecordForce.sendStop()
                print("Hung up, timeout.")
                SerReconnect()
                GUI.show_frame(InitialInputs)

def runDataCollect():
    try:        
        RecordForce.sendStart()
    except:
        print("run fail")
        GUI.errors.append('serial com. (start data)') # label 
        eCode = 'e2' # eCode = e2
        GUI.errorCodes.append(eCode)
        print("eCode = "+eCode)
        popup('start data collect')
        
    #collectData()
    RecordForce.thread2_collectData = threading.Thread(target = collectData)
    #RecordForce.thread2_collectData = Process(target = collectData)
    RecordForce.thread2_collectData.start()
    #passdata()
    #datafeed()

def incrementName(filename):
        hyphen = "_"

        # determine last few characters from a filename
        def incrementvars(filename):
            lastchar = filename[len(filename)-1]
            secondtolastchar = filename[len(filename)-2]
            thirdtolastchar = filename[len(filename)-3]
            lastcharandsecondtolastchar = str(secondtolastchar+lastchar)
            return lastchar, secondtolastchar, thirdtolastchar, lastcharandsecondtolastchar

        #check if the last two are hyphens. if there is more than one hypthen, remove the last character until there is only one hyphen.
        def hyphencheck(filename,hyphen,lastchar, secondtolastchar, thirdtolastchar, lastcharandsecondtolastchar):
            while lastchar == hyphen and secondtolastchar == hyphen: # if two hyphens at the end
                filename = filename[:-1] # remove last character
                incrementvars()
            return filename, lastchar, secondtolastchar, thirdtolastchar, lastcharandsecondtolastchar

        if filename == "": # default, if user tried to increment without inputting any varietyname, plotname, or filename
            filename = datestring+","+GUI.timestring.get()
            
        lastchar, secondtolastchar, thirdtolastchar, lastcharandsecondtolastchar = incrementvars(filename)
        filename, lastchar, secondtolastchar, thirdtolastchar, lastcharandsecondtolastchar = hyphencheck(filename,hyphen,lastchar, secondtolastchar, thirdtolastchar, lastcharandsecondtolastchar)
        
        if lastchar == hyphen: # if last character is a hyphen
            newName = str(filename+str("1"))
        elif secondtolastchar == hyphen and lastchar.isnumeric: # if single digit preceded by a hyphen
            #newName = str(filename+str(int(lastchar)+1))
            filename = filename[:-1] # remove last character
            newName = str(filename+str(int(lastchar)+1))
        elif thirdtolastchar == hyphen and lastcharandsecondtolastchar.isnumeric: # if double digits preceded by a hyphen
            filename = filename[:-1] # remove last character
            filename = filename[:-1] # remove last character
            newName = str(filename+str(int(lastcharandsecondtolastchar)+1))
        elif filename == "":
            newName = date
        else:
            newName = str(filename+"_1")
        return newName
        #GUI.filename_force.set(newName)
    
''' Edge cases: Filenaming '''
def nameDirectionScrub(filename):
    if ("_side1" in filename):
        filename=filename.replace("_side1","")
        print(filename)
    if ("_side2" in filename):
        filename=filename.replace("_side2","")
    if ("_side3" in filename):
        filename=filename.replace("_side3","")
    if ("_forward" in filename):
        filename=filename.replace("_forward","")
    if ("_postTest" in filename):
        filename=filename.replace("_postTest","")
    return filename

def nameMissing(varietyname,plotname):
    if varietyname == "":
        varietyname = datestring
    if plotname == "":
        plotname = GUI.timestring.get() # plotname = GUI.timestring.get() # if you want the timestring (serving at plotname) to not change...but then it will never change
    return varietyname, plotname

def nameBlackBox(direction,filename):
    varietyname = GUI.varietyname.get()
    plotname = GUI.plotname.get()
    check=GUI.passfillednames_checkbox.get()
    if GUI.filename_force.get()=="" and check==1:
        varietyname, plotname = nameMissing(varietyname, plotname)
        #print(varietyname, plotname)
        filename = str(varietyname+str(",")+plotname+str("_")+direction)
    elif GUI.filename_force.get()=="" and check==0:
        filename = datestring+","+time.strftime("%H%M")+"_"+direction
    elif GUI.filename_force.get()!="" and check==1:
        varietyname, plotname = nameMissing(varietyname, plotname)
        filename = str(varietyname+str(",")+plotname+str("_")+direction)
    elif GUI.filename_force.get()!="" and check==0:
        if ("side1" in filename) or ("side2" in filename) or ("side3" in filename) or ("forward" in filename) or ("postTest" in filename):
            filename = nameDirectionScrub(GUI.filename_force.get())
            filename = filename+"_"+direction
        else:
            filename = filename+"_"+direction
    #GUI.filename_postTest.set(filename_postTest)
    return filename
''' end: Edge cases: Filenaming '''

''' Single XLSX workbook created from all expected CSV files for 9-cell study'''
#import pandas as pd
#import sys
#import os
def generateXSLXcombinedFile():
    writer = pd.ExcelWriter('default.xlsx')
    for csvfilename in sys.ar[1:]:
        df = pd.read.csv(csvfilename)
        #FIX df.to_excel(writer.sheet_names=os.path.splitext(csvfilename)[0]) # "keyword cannot be an expression"
    writer.save()
def peakClickRunAndSave(filename):
    PeakClick() # you cannot put in counts first....because they haven't been collected yet!
    #ergo, run clicks after triggered XLSX workbook creation
''' trigger with button, on Initial Inputs page. Button also clears all data from stemberry, wait it dods not triggers PeakClick.py, which saves to a separate CSV before all CSV's are wrapped into a xlsx workbook.
'''
'''Classes, Tkinter GUI'''
# GUI overarching class
class GUI(tk.Tk):
    def __init__(self, *args, **kwargs):# automatically runs
        
        tk.Tk.__init__(self, *args, **kwargs)

        GUI.initializeVarsGUI()
        GUI.refreshAll()
        
        container = tk.Frame(self)
        container.pack(side='top', fill='both',expand = True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        # top menu configuration
        menubar = Menu(container)
        filemenu = Menu(menubar, tearoff=0)
        datamenu = Menu(menubar, tearoff=0)
        pagemenu = Menu(menubar, tearoff=0)
        
        filemenu.add_command(label='Serial Reconnect', command = lambda:SerReconnect())
        filemenu.add_command(label='Choose Output Folder', command = lambda:popup_chooseFolder())
        filemenu.add_command(label='Errors', command = lambda:showErrors())
        filemenu.add_command(label='Save State', command = lambda:createBackupFile())
        filemenu.add_command(label="Exit", command = lambda:close())
        pagemenu.add_command(label="Guide", command=lambda:GUI.show_frame(Guide))
        pagemenu.add_command(label="Initial Inputs", command=lambda:GUI.show_frame(InitialInputs))
        pagemenu.add_command(label="Record Force", command=lambda:GUI.show_frame(RecordForce))
        pagemenu.add_command(label="Post Test Inputs", command=lambda:GUI.show_frame(FinalInputs))
        pagemenu.add_command(label="Calibrate", command=lambda:GUI.show_frame(Calibrate))
        pagemenu.add_command(label="Stem Count PreTest, Classic", command=lambda:GUI.show_frame(StemCountClassic))
        datamenu.add_command(label="Data Feed Display, On", command = lambda:data_display(True))
        datamenu.add_command(label="Data Feed Display, Off", command = lambda:data_display(False))

        menubar.add_cascade(label='File', menu=filemenu)
        menubar.add_cascade(label="Pages", menu=pagemenu)
        menubar.add_cascade(label="Livestream Data Recording", menu=datamenu)
        
        tk.Tk.config(self, menu=menubar)                
        GUI.frames = {}# empty dictionary

        for F in (InitialInputs, RecordForce, FinalInputs, Calibrate, Guide, ErrorReport, StemCountClassic):# must put all pages in here
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky='nsew')
            frame.configure(background = 'ghost white')
        
        GUI.show_frame(InitialInputs)
        
    def initializeVarsGUI():
        GUI.filename_force = StringVar()
        GUI.filename_preTest = StringVar()
        GUI.filename_postTest = StringVar()
        GUI.filename_all = StringVar()
        GUI.varietyname = StringVar()
        GUI.plotname = StringVar()
        GUI.stemheight = DoubleVar()
        GUI.currentdirection = StringVar()#
        GUI.barmiddle = DoubleVar() #
        GUI.barbottom = DoubleVar() #
        GUI.passfillednames_checkbox =  IntVar() # revert
        GUI.timestring = StringVar()
        GUI.startRange1, GUI.startRange2, GUI.startRange3 =  DoubleVar(),  DoubleVar(),  DoubleVar() # cm = StringVar()
        GUI.addressInput = StringVar()
        
        GUI.cell1Mass,GUI.cell2Mass,GUI.cell3Mass,GUI.cell4Mass,GUI.cell5Mass,GUI.cell6Mass,GUI.cell7Mass,GUI.cell8Mass,GUI.cell9Mass =  DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar()
        GUI.cell1Count,GUI.cell2Count,GUI.cell3Count,GUI.cell4Count,GUI.cell5Count,GUI.cell6Count,GUI.cell7Count,GUI.cell8Count,GUI.cell9Count =  DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar()
        GUI.cell1Diameter1,GUI.cell2Diameter1,GUI.cell3Diameter1,GUI.cell4Diameter1,GUI.cell5Diameter1,GUI.cell6Diameter1,GUI.cell7Diameter1,GUI.cell8Diameter1,GUI.cell9Diameter1 =  DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar()
        GUI.cell1Diameter2,GUI.cell2Diameter2,GUI.cell3Diameter2,GUI.cell4Diameter2,GUI.cell5Diameter2,GUI.cell6Diameter2,GUI.cell7Diameter2,GUI.cell8Diameter2,GUI.cell9Diameter2 =  DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar()
        GUI.cell1Diameter3,GUI.cell2Diameter3,GUI.cell3Diameter3,GUI.cell4Diameter3,GUI.cell5Diameter3,GUI.cell6Diameter3,GUI.cell7Diameter3,GUI.cell8Diameter3,GUI.cell9Diameter3 =  DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar()
        GUI.cell1Diameter4,GUI.cell2Diameter4,GUI.cell3Diameter4,GUI.cell4Diameter4,GUI.cell5Diameter4,GUI.cell6Diameter4,GUI.cell7Diameter4,GUI.cell8Diameter4,GUI.cell9Diameter4 =  DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar(), DoubleVar()

        ''' Non-tkinter GUI vars, initialize ''' # for nine cell assessment, save state
        # may as well keep everything here, for fun
        GUI.errors = [] # for tracking errors
        GUI.errorCodes = [] # for tracking errors
        GUI.ignoreserial = ignoreserial
        GUI.address = address

        GUI.forcePushed = []
        GUI.distanceTraveled = []
        GUI.timeElapsed = []
        GUI.travelvelocity = []
        GUI.samplingrate = []

        GUI.forcePushed_side1 = []
        GUI.forcePushed_side2 = []
        GUI.forcePushed_side3 = []
        GUI.forcePushed_forward = []
        GUI.distanceTraveled_side1 = []
        GUI.distanceTraveled_side2 = []
        GUI.distanceTraveled_side3 = []
        GUI.distanceTraveled_forward = []
        GUI.timeElapsed_side1 = []
        GUI.timeElapsed_side2 = []
        GUI.timeElapsed_side3 = []
        GUI.timeElapsed_forward =  []
        GUI.peaks_force_side1 = []
        GUI.peaks_force_side2 = []        
        GUI.peaks_force_side3 = []
        GUI.peaks_force_forward = []
        GUI.peaks_distance_side1 = []
        GUI.peaks_distance_side2 = []        
        GUI.peaks_distance_side3 = []
        GUI.peaks_distance_forward = []
        GUI.peaks_time_side1 = []
        GUI.peaks_time_side2 = []        
        GUI.peaks_time_side3 = []
        GUI.peaks_time_forward = []

        GUI.peaks_force = []
        GUI.peaks_distance = []
        GUI.peaks_time = []

        peakclick.peaks_force = []
        peakclick.peaks_distance = []
        peakclick.peaks_time = []

        GUI.stemcounts = []

        GUI.peak_force_cell1, GUI.peak_force_cell2, GUI.peak_force_cell3, GUI.peak_force_cell4, GUI.peak_force_cell5, GUI.peak_force_cell6, GUI.peak_force_cell7, GUI.peak_force_cell8, GUI.peak_force_cell9 = [],[],[],[],[],[],[],[],[]
        GUI.peak_distance_cell1, GUI.peak_distance_cell2, GUI.peak_distance_cell3, GUI.peak_distance_cell4, GUI.peak_distance_cell5, GUI.peak_distance_cell6, GUI.peak_distance_cell7, GUI.peak_distance_cell8, GUI.peak_distance_cell9 = [],[],[],[],[],[],[],[],[]
        GUI.peak_time_cell1, GUI.peak_time_cell2, GUI.peak_time_cell3, GUI.peak_time_cell4, GUI.peak_time_cell5, GUI.peak_time_cell6, GUI.peak_time_cell7, GUI.peak_time_cell8, GUI.peak_time_cell9 = [],[],[],[],[],[],[],[],[]

        GUI.data_preTest,GUI.data_recordForce,GUI.data_postTest,GUI.data_peaks,GUI.data_EI = [],[],[],[],[]
        
    def refreshAll(): #clearall(self)?
        
    
        GUI.filename_force.set("")
        GUI.filename_preTest.set("")
        GUI.filename_postTest.set("")
        GUI.filename_all.set("")
        GUI.varietyname.set("")
        GUI.plotname.set("")
        GUI.startRange1.set(50)
        GUI.startRange2.set(150) 
        GUI.startRange3.set(250) # centimeters
        GUI.stemheight.set(default_stemheight) # cm
        GUI.barbottom.set(round(GUI.stemheight.get()*initial_barbottomOverStemheight_coeff,3)) # cm
        GUI.barmiddle.set(round(GUI.barbottom.get()+barradius,3)) # cm
        GUI.passfillednames_checkbox.set(1)
        GUI.timestring.set(time.strftime("%H%M"))
        GUI.currentdirection.set("")
        GUI.addressInput.set("")
        
        ''' Set post test variables for mass, count, and diameter'''
        GUI.cell1Mass.set(0),GUI.cell2Mass.set(0),GUI.cell3Mass.set(0),GUI.cell4Mass.set(0),GUI.cell5Mass.set(0),GUI.cell6Mass.set(0),GUI.cell7Mass.set(0),GUI.cell8Mass.set(0),GUI.cell9Mass.set(0)
        GUI.cell1Count.set(0),GUI.cell2Count.set(0),GUI.cell3Count.set(0),GUI.cell4Count.set(0),GUI.cell5Count.set(0),GUI.cell6Count.set(0),GUI.cell7Count.set(0),GUI.cell8Count.set(0),GUI.cell9Count.set(0)
        GUI.cell1Diameter1.set(0),GUI.cell2Diameter1.set(0),GUI.cell3Diameter1.set(0),GUI.cell4Diameter1.set(0),GUI.cell5Diameter1.set(0),GUI.cell6Diameter1.set(0),GUI.cell7Diameter1.set(0),GUI.cell8Diameter1.set(0),GUI.cell9Diameter1.set(0)
        GUI.cell1Diameter2.set(0),GUI.cell2Diameter2.set(0),GUI.cell3Diameter2.set(0),GUI.cell4Diameter2.set(0),GUI.cell5Diameter2.set(0),GUI.cell6Diameter2.set(0),GUI.cell7Diameter2.set(0),GUI.cell8Diameter2.set(0),GUI.cell9Diameter2.set(0)
        GUI.cell1Diameter3.set(0),GUI.cell2Diameter3.set(0),GUI.cell3Diameter3.set(0),GUI.cell4Diameter3.set(0),GUI.cell5Diameter3.set(0),GUI.cell6Diameter3.set(0),GUI.cell7Diameter3.set(0),GUI.cell8Diameter3.set(0),GUI.cell9Diameter3.set(0)
        GUI.cell1Diameter4.set(0),GUI.cell2Diameter4.set(0),GUI.cell3Diameter4.set(0),GUI.cell4Diameter4.set(0),GUI.cell5Diameter4.set(0),GUI.cell6Diameter4.set(0),GUI.cell7Diameter4.set(0),GUI.cell8Diameter4.set(0),GUI.cell9Diameter4.set(0)
        ''' end '''
        
        ''' Non-tkinter GUI vars, initialize ''' # for nine cell assessment, save state
        # may as well keep everything here, for fun
        GUI.errors = [] # for tracking errors
        GUI.errorCodes = [] # for tracking errors

        GUI.forcePushed = []
        GUI.distanceTraveled = []
        GUI.timeElapsed = []

        GUI.forcePushed_side1 = []
        GUI.forcePushed_side2 = []
        GUI.forcePushed_side3 = []
        GUI.forcePushed_forward = []
        GUI.distanceTraveled_side1 = []
        GUI.distanceTraveled_side2 = []
        GUI.distanceTraveled_side3 = []
        GUI.distanceTraveled_forward = []
        GUI.timeElapsed_side1 = []
        GUI.timeElapsed_side2 = []
        GUI.timeElapsed_side3 = []
        GUI.timeElapsed_forward =  []
        GUI.peaks_force_side1 = []
        GUI.peaks_force_side2 = []        
        GUI.peaks_force_side3 = []
        GUI.peaks_force_forward = []
        GUI.peaks_distance_side1 = []
        GUI.peaks_distance_side2 = []        
        GUI.peaks_distance_side3 = []
        GUI.peaks_distance_forward = []
        GUI.peaks_time_side1 = []
        GUI.peaks_time_side2 = []        
        GUI.peaks_time_side3 = []

        GUI.peaks_force = []
        GUI.peaks_distance = []
        GUI.peaks_time = []

        GUI.stemcounts = []
        
        GUI.peak_force_cell1, GUI.peak_force_cell2, GUI.peak_force_cell3, GUI.peak_force_cell4, GUI.peak_force_cell5, GUI.peak_force_cell6, GUI.peak_force_cell7, GUI.peak_force_cell8, GUI.peak_force_cell9 = [],[],[],[],[],[],[],[],[]
        GUI.peak_distance_cell1, GUI.peak_distance_cell2, GUI.peak_distance_cell3, GUI.peak_distance_cell4, GUI.peak_distance_cell5, GUI.peak_distance_cell6, GUI.peak_distance_cell7, GUI.peak_distance_cell8, GUI.peak_distance_cell9 = [],[],[],[],[],[],[],[],[]
        GUI.peak_time_cell1, GUI.peak_time_cell2, GUI.peak_time_cell3, GUI.peak_time_cell4, GUI.peak_time_cell5, GUI.peak_time_cell6, GUI.peak_time_cell7, GUI.peak_time_cell8, GUI.peak_time_cell9 = [],[],[],[],[],[],[],[],[]

        
        GUI.peak_EI_fullcontact_cell1, GUI.peak_EI_fullcontact_cell2, GUI.peak_EI_fullcontact_cell3, GUI.peak_EI_fullcontact_cell4, GUI.peak_EI_fullcontact_cell5, GUI.peak_EI_fullcontact_cell6, GUI.peak_EI_fullcontact_cell7, GUI.peak_EI_fullcontact_cell8, GUI.peak_EI_fullcontact_cell9 = [],[],[],[],[],[],[],[],[]
        GUI.peak_EI_intermediatecontact_cell1, GUI.peak_EI_intermediatecontact_cell2, GUI.peak_EI_intermediatecontact_cell3, GUI.peak_EI_intermediatecontact_cell4, GUI.peak_EI_intermediatecontact_cell5, GUI.peak_EI_intermediatecontact_cell6, GUI.peak_EI_intermediatecontact_cell7, GUI.peak_EI_intermediatecontact_cell8, GUI.peak_EI_intermediatecontact_cell9 = [],[],[],[],[],[],[],[],[]
        GUI.peak_EI_nocontact_cell1, GUI.peak_EI_nocontact_cell2, GUI.peak_EI_nocontact_cell3, GUI.peak_EI_nocontact_cell4, GUI.peak_EI_nocontact_cell5, GUI.peak_EI_nocontact_cell6, GUI.peak_EI_nocontact_cell7, GUI.peak_EI_nocontact_cell8, GUI.peak_EI_nocontact_cell9 = [],[],[],[],[],[],[],[],[]

        GUI.peaks_time_forward = []
        GUI.EI_fullcontact = [] 
        GUI.EI_intermediatecontact = []
        GUI.EI_nocontact = []
        GUI.AvgEI_intermediatecontact = []

        GUI.data_preTest,GUI.data_recordForce,GUI.data_postTest,GUI.data_peaks,GUI.data_EI = [],[],[],[],[]
    
    def show_frame(cont):
        frame = GUI.frames[cont]
        frame.tkraise()

        frame.event_generate("<<ShowFrame>>") # event

# buttons that are the same for each page
#'''
class repeatPageButtons:
    def __init__(self, parent, controller): # automatically runs
        filler=1
    def showButtons(self, parent, controller):
        guide_button = Button(self, text = "Guide", font = ("arial", 14, "bold"), height = 2, width = 8, fg = "ghost white", bg = "gray2",command=lambda:GUI.show_frame(Guide))
        initialInputs_button = Button(self, text = "Initial\nInputs", font = ("arial", 14, "bold"), height = 2, width = 8, fg = "ghost white", bg = "gray2",command=lambda:GUI.show_frame(InitialInputs))
        recordForce_button = Button(self, text = "Record\nForce", font = ("arial", 14, "bold"), height = 2, width = 8, fg = "ghost white", bg = "gray2",command=lambda:GUI.show_frame(RecordForce))
        postInputs_button = Button(self, text = "Post Test\nInputs", font = ("arial", 14, "bold"), height = 2, width = 8, fg = "ghost white", bg = "gray2",command=lambda:GUI.show_frame(FinalInputs))

        guide_button.place(x = 0, y = 340)
        initialInputs_button.place(x = 375/3*1, y = 340)
        recordForce_button.place(x = 375/3*2, y = 340)
        postInputs_button.place(x = 375/3*3, y = 340)
        #'''
#Home page
class InitialInputs(tk.Frame):
    
    def __init__(self, parent, controller): # automatically runs

        # global variables within Home that are used in multiple Classes & functions
        # global ser # serial port

        # Once the program launches, the InitialInput screen will be shown for the first time, prompting serial connection
        try:
        #if GUI.ignoreserial == False:
            RecordForce.ser = SerConnect()
            #SerReconnect(RecordForce.ser)
        except:
            GUI.ignoreserial = True
            print("Serial not connected.")
        
        tk.Frame.__init__(self, parent)
        
        ''' GUI design, non-frame '''
        pageButtons = repeatPageButtons.showButtons(self, parent, controller)
        homeheader = Label(self, text = "INITIAL INPUTS", font = ("arial", 17, "bold"), fg = "gray3", bg="ghost white")
        unit_label = Label(self, text=str("Distance and height are in centimeters."), font = ("arial", 12, "italic"), fg = "red4", bg="ghost white")
        savePreTestInputs_button = Button(self, text ="Save Initial Inputs", font = ("arial", 16, "bold"), height = 1, width = 20, fg = "ghost white", bg = "dodgerblue3", command=lambda:self.savePreTestInputs())
        variety_label = Label(self, text = "Variety: ", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white")
        varietyname_entryBox = Entry(self, textvariable=GUI.varietyname, font = ("arial", 14, "bold"), width="20", bg="white", fg="gray1")
        plotname_label = Label(self, text = "Plot: ", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white")
        plotname_entryBox = Entry(self, textvariable=GUI.plotname, font = ("arial", 14, "bold"), width="10", bg="white", fg="gray1")
        passfillednames_checkbox = Checkbutton(self, text = "Use variety & plot names", variable = GUI.passfillednames_checkbox, width=23, height=2, font = ("arial", 12), bg='ghost white')
        stemHeight_label = Label(self, text = "Avg. Stem Height (cm):", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white")
        stemHeight_entry = Entry(self, textvariable=GUI.stemheight, font = ("arial", 14, "bold"), width= 6, bg="white", fg="gray1")
        barHeight_label = Label(self, text = "Bar Middle Height (cm):", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white")
        barHeight_entry = Entry(self, textvariable=GUI.barmiddle, font = ("arial", 14, "bold"), width= 6, bg="white", fg="gray1")

        homeheader.place(x=275,y=0)
        unit_label.place(x=500,y=0)
        savePreTestInputs_button.place(x = 510, y = 340)
        variety_label.place(x=0,y=35)
        varietyname_entryBox.place(x = 80, y = 35)
        plotname_label.place(x=310,y=35)
        plotname_entryBox.place(x = 360, y = 35)
        passfillednames_checkbox.place(x = 540 , y = 25)
        stemHeight_label.place(x=0,y=240)
        stemHeight_entry.place(x = 220, y = 240)
        barHeight_label.place(x=0,y=280) 
        barHeight_entry.place(x = 220, y = 280)
        
        ''' Frame: Range'''
        range_frame = tk.LabelFrame(self, text='Side Hit Ranges',font = ("arial", 14, "bold"), width= 10, bg="white", fg="gray1")
        range_frame.place(x = 20, y = 80)
        startRange1Dis_label = Label(range_frame, text = "Range 1 start (cm):", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=2, column=0)
        startRange2Dis_label = Label(range_frame, text = "Range 2 start (cm):", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=1, column=0)
        startRange3Dis_label = Label(range_frame, text = "Range 3 start (cm):", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=0, column=0)
        startRange1_entry = Entry(range_frame, textvariable=GUI.startRange1,font = ("arial", 14, "bold"), width= 4, bg="white", fg="gray1").grid(row=2, column=1)
        startRange2_entry = Entry(range_frame, textvariable=GUI.startRange2,font = ("arial", 14, "bold"), width= 4, bg="white", fg="gray1").grid(row=1, column=1)
        startRange3_entry = Entry(range_frame, textvariable=GUI.startRange3, font = ("arial", 14, "bold"), width= 4, bg="white", fg="gray1").grid(row=0, column=1)
        ''' end '''

        ''' Frame: Force Bar Quickset buttons'''
        barset_frame = tk.LabelFrame(self, text='Bar Bottom Quickset',font = ("arial", 14, "bold"), width= 10, bg="white", fg="gray1")
        barset_frame.place(x = 340, y = 230)
        #button that calculates optimized force bar height
        height70percent_button = Button(barset_frame, text ="70%", font=("arial",14,"bold"), height=1, width=6, fg="ghost white", bg="red4",command=lambda:self.height70percent(GUI.stemheight.get()))
        height80percent_button = Button(barset_frame, text ="80%", font=("arial",14,"bold"), height=1, width=6, fg="ghost white", bg="red4",command=lambda:self.height80percent(GUI.stemheight.get()))
        height90percent_button = Button(barset_frame, text ="90%", font=("arial",14,"bold"), height=1, width=6, fg="ghost white", bg="red4",command=lambda:self.height90percent(GUI.stemheight.get()))
        height70percent_button.grid(row=0, column=0)
        height80percent_button.grid(row=0, column=1)
        height90percent_button.grid(row=0, column=2)
        ''' end '''
        
        ''' Frame: PreCount Buttons '' # Hide, access via menu
        precount_frame = tk.LabelFrame(self, text='Count First',font = ("arial", 10, "bold"), width= 4, bg="white", fg="gray1")
        precount_frame.place(x = 650, y = 100)
        precount_button = tk.Button(precount_frame, text ="Don't", font=("arial",10,"bol;d"), height=1, width=10, fg="ghost white", bg="purple3",command=lambda:self.height70percent(GUI.stemheight.get()))
        precount_button.grid(row=0, column=4)
        '' end '''
        
        self.bind("<<ShowFrame>>", self.on_show_frame_InitialInputs) # why is this really here

    def height70percent(self, stemheight):
        coeff = 0.7
        GUI.barbottom.set(round(coeff*stemheight,3))
        GUI.barmiddle.set(round(GUI.barbottom.get()+barradius,3))
        print("70%: stemheight",GUI.stemheight.get(),"cm, barheight = ",GUI.barmiddle.get(),"cm, barbottom = ",GUI.barbottom.get(),"cm")
    def height80percent(self, stemheight):
        coeff = 0.8
        GUI.barbottom.set(round(coeff*stemheight,3))
        GUI.barmiddle.set(round(GUI.barbottom.get()+barradius,3))
        print("80%: stemheight",GUI.stemheight.get(),"cm, barheight = ",GUI.barmiddle.get(),"cm, barbottom = ",GUI.barbottom.get(),"cm")
    def height90percent(self, stemheight):
        coeff = 0.9
        GUI.barbottom.set(round(coeff*stemheight,3))
        GUI.barmiddle.set(round(GUI.barbottom.get()+barradius,3))
        print("90%: stemheight",GUI.stemheight.get(),"cm, barheight = ",GUI.barmiddle.get(),"cm, barbottom = ",GUI.barbottom.get(),"cm")
    
    def savePreTestInputs(self):
        GUI.barbottom.set(round(GUI.barmiddle.get()-barradius,3)) # cm
        print(str(int(GUI.barbottom.get()/GUI.stemheight.get()*100)),"%: stemheight",GUI.stemheight.get(),"cm, barheight = ",GUI.barmiddle.get(),"cm, barbottom = ",GUI.barbottom.get(),"cm")

        variety, plot, stemheight, barbottom, barmiddle, startRange1, startRange2, startRange3 = ['variety'], ['plot'], ['stemheight(cm)'], ['barbottom(cm)'], ['barmiddle(cm)'], ['startRange1(cm)'], ['startRange2(cm)'], ['startRange3(cm)']
        variety.append(GUI.varietyname.get())
        plot.append(GUI.plotname.get())
        stemheight.append(GUI.stemheight.get())
        barbottom.append(GUI.barbottom.get())
        barmiddle.append(GUI.barmiddle.get())
        startRange1.append(GUI.startRange1.get())
        startRange2.append(GUI.startRange2.get())
        startRange3.append(GUI.startRange3.get())
        
        update_filename_preTest()
        filename_preTest_csv = GUI.address + '/' + GUI.filename_preTest.get() + '.csv'

        if overwriteGuard(filename_preTest_csv) == True: # filename already exists, needs to be renamed
            rename(GUI.filename_preTest.get()) # prompt user to rename file  
        ''' write CSV'''
        GUI.data_preTest = [variety, plot, stemheight, barbottom, barmiddle, startRange1, startRange2, startRange3]
        columns_data_preTest = zip_longest(*GUI.data_preTest)
        with open(filename_preTest_csv,'w',newline='') as f:
            writer = csv.writer(f)
            writer.writerows(columns_data_preTest)
        ''' end: write CSV '''
        print("filename_preTest_csv = "+filename_preTest_csv)
        
    def on_show_frame_InitialInputs(self, event):
        filler=1
        #print("show Initial Inputs screen")
        
# Data collection page
class RecordForce(tk.Frame):
    def __init__(self, parent, controller):# automatically runs

        RecordForce.collect = collect # takes top-of-script input
        RecordForce.peaks_force = []
        RecordForce.peaks_distance = []
        RecordForce.peaks_time = []
        
        self.legends = []
        
        tk.Frame.__init__(self, parent)
        self.controller = controller # fuck?

        RecordForce.container = tk.Frame(self)
        
        ''' GUI design, non-frame '''
        pageButtons = repeatPageButtons.showButtons(self, parent, controller)
        title = Label(self, text ="RECORD FORCE", font = ("arial", 17, "bold"), fg = "gray3", bg="ghost white")
        filename_label = Label(self, text = "Filename: ", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white")
        filename_entryBox = Entry(self, textvariable=GUI.filename_force, font = ("arial", 14, "bold"), width="32", bg="white", fg="gray1")
        self.checkAutoGraph =  IntVar() # on/off control of auto graph after stopping & saving data
        #self.checkAutoGraph.set(1)
        self.checkAutoGraph.set(0)
        graph_checkbox = Checkbutton(self, text = "Auto graph", variable = self.checkAutoGraph, width = 13, height = 2, bg = 'ghost white')

        title.place(x=275,y=0)
        filename_label.place(x=0,y=80)
        filename_entryBox.place(x = 110, y = 80)
        graph_checkbox.place(x = 675 , y = 0)

        RecordForce.datafeed_frame = tk.LabelFrame(self, text='Data Feed',font = ("arial", 14, "bold"), width= 10, bg="white", fg="gray1")
        RecordForce.datafeed_frame.place(x = 20, y = 0)
        clear_button = Button(RecordForce.datafeed_frame,text = "Clear",font = ("arial", 16, "bold"), height = 1, width = 6, fg = "ghost white", bg = "red4",command=lambda:RecordForce.clearDisplay())
        clear_button.grid(row=0, column=0)
        RecordForce.msgbox =  tk.LabelFrame(self, text='',font = ("arial", 14, "bold"), width= 10, bg="white", fg="gray1")

        RecordForce.msgbox.place(x = 5, y = 120)
        #forceSaved_label.place(x=5, y = 120)
        
        ''' Frame: Filename Quickset buttons'''
        nameset_frame = tk.LabelFrame(self, text='Filename\nQuickset',font = ("arial", 14, "bold"), width= 10, bg="white", fg="gray1")
        nameset_frame.place(x = 570, y = 40)
        #button that calculates optimized force bar height
        side1TestButton = Button(nameset_frame, text = "Side 1", font = ("arial", 16, "bold"), height = 1, width = 6, fg = "ghost white", bg = "red4",command=lambda:self.nameSide1())
        side2TestButton = Button(nameset_frame, text = "Side 2", font = ("arial", 16, "bold"), height = 1, width = 6, fg = "ghost white", bg = "red4",command=lambda:self.nameSide2())
        side3TestButton = Button(nameset_frame, text = "Side 3", font = ("arial", 16, "bold"), height = 1, width = 6,fg = "ghost white", bg = "red4",command=lambda:self.nameSide3())
        forwardTestButton = Button(nameset_frame, text = "Forward", font = ("arial", 16, "bold"), height = 1, width = 6, fg = "ghost white", bg = "red4",command=lambda:self.nameForward())
        increment_button = Button(nameset_frame, text = "+1", font = ("arial", 16, "bold"), height = 1, width = 6, fg = "ghost white", bg = "purple4",command=lambda:self.incrementName_Force(GUI.filename_force.get()))
        
        side1TestButton.grid(row=0, column=0)
        side2TestButton.grid(row=1, column=0)
        side3TestButton.grid(row=2, column=0)
        forwardTestButton.grid(row=3, column=0)
        increment_button.grid(row=4, column=0)
        ''' end '''

        ''' Record Data Frame'''
        dataButtons_frame = tk.LabelFrame(self, text='',font = ("arial", 14, "bold"), width= 10, bg="white", fg="gray1")
        dataButtons_frame.place(x = 675, y = 40)
        #tells Arduino to start collecting data
        start_button = Button(dataButtons_frame, text = "Start", font = ("arial", 16, "bold"), height = 3, width = 8, fg = "ghost white", bg = "dodgerblue3",command=lambda:RecordForce.startCollect())
        #tells Arduino to stop collecting data & saves the data (calls filename function)
        stop_button = Button(dataButtons_frame, text = "Stop\n&\nSave", font = ("arial", 16, "bold"), height = 3, width = 8, fg = "ghost white", bg = "dodgerblue3",command=lambda:RecordForce.stopAndSave())
        #tares/zeros load cell
        tare_button = Button(dataButtons_frame, text = "Tare", font = ("arial", 16, "bold"), height = 3, width = 8, fg = "ghost white", bg = "dodgerblue3",command=lambda:RecordForce.tare())
        
        start_button.grid(row = 1, column = 0)
        stop_button.grid(row = 2, column = 0)
        tare_button.grid(row = 3, column = 0)
        ''' end frame'''
        
        self.bind("<<ShowFrame>>", self.on_show_frame_RecordForce)

    def nameForward(self):
        direction = "forward"
        filename_force = nameBlackBox(direction,GUI.filename_force.get())
        GUI.filename_force.set(filename_force)
        GUI.currentdirection.set(direction)
    def nameSide1(self):
        direction = "side1"
        filename_force = nameBlackBox(direction,GUI.filename_force.get())
        GUI.filename_force.set(filename_force)
        GUI.currentdirection.set(direction)
    def nameSide2(self):
        direction = "side2"
        filename_force = nameBlackBox(direction,GUI.filename_force.get())
        GUI.filename_force.set(filename_force)
        GUI.currentdirection.set(direction)
    def nameSide3(self):
        direction = "side3"
        filename_force = nameBlackBox(direction,GUI.filename_force.get())
        GUI.filename_force.set(filename_force)
        GUI.currentdirection.set(direction)
    def nameFresh(self,varietyname,plotname):
        direction = ""
        filename_force = nameBlackBox(direction,GUI.filename_force.get())
        GUI.filename_force.set(filename_force)
        set(direction)
    
    def clearDisplay():
        time.sleep(0.3)
        print('You hit the "Clear" button. Please develop clearDisplay().')
        '''
        try:
            RecordForce.Forcelist.delete(0, 'end')
            RecordForce.Dislist.delete(0, 'end')
            RecordForce.Timelist.delete(0, 'end')
            print('You hit the "Clear" button and deleted recorded data. This was not useful.')
        except:
            pass
            '''
        
    def incrementName_Force(self,filename):
        newName = incrementName(filename)
        GUI.filename_force.set(newName)
    
        
    # calls run function (for collecting Arduino data) to run in backend while GUI runs in frontend     
    def startCollect():
        now = datetime.datetime.now()
        unix_now = time.mktime(now.timetuple())
        time.sleep(0.4) # for visual effect
        #threading run function (simultaneously performs run function in backend)
        if GUI.ignoreserial == False:
            if RecordForce.ser.isOpen() == False:
               RecordForce.ser.open()
            runDataCollect()
            if visualizeDatastream == True:
                thread2_visualizeData = threading.Thread(target = datafeed,args=(RecordForce.container))
                thread2_visualizeData.start()
        else:
            print("Data collection not run, because GUI.ignoreserial ==",str(GUI.ignoreserial),"...")

    # saves raw force data
    def sendStart():
        if RecordForce.ser.isOpen() == False:
           RecordForce.ser.open()
           
        started = 's'
        print("\nPython sent "+started+".")
        RecordForce.hasStarted = False
        RecordForce.hasSentStop = False
        RecordForce.hasStopped = False
        # wipe vars
        GUI.forcePushed = []
        GUI.distanceTraveled = []
        GUI.timeElapsed = []
        RecordForce.datastream = []
        #thread2_count_stop.start()
        while RecordForce.hasStarted == False: # len(line)==0
            RecordForce.ser.write(started.encode())
            #time.sleep(sleepSend) # if this is on, it takes another two seconds to start, but the arduino yells less.
            if RecordForce.ser.in_waiting > 0: # this does happen
                ser_bytes = RecordForce.ser.readline()
                line = ser_bytes.decode('utf-8').rstrip()
                if line =="Started!": #if line == started:
                    RecordForce.hasStarted = True
                    RecordForce.startTime = time.time() #stopwatch starts
                    RecordForce.i = 0
                    print(started+" received by arduino.")
                    
    def sendStop():
        stopped = 'x'
        RecordForce.hasSentStop = True
        print("Python sent "+stopped+".")
        
        while RecordForce.hasStopped == False: # len(line)==0
            print("brake", end =" ")
            RecordForce.ser.write(stopped.encode())
            RecordForce.ser.flush()
            #time.sleep(sleepSend)
            if RecordForce.ser.in_waiting > 0: # this does happen
                bytecount = RecordForce.ser.in_waiting
                ser_bytes = RecordForce.ser.read(bytecount)
                line = ser_bytes.decode('utf-8').rstrip()
                datapacket = line.splitlines()
                #print(line)
                if line =="Stopped!" or ("Stopped!" in datapacket): #if line == stopped:
                #if ("Stopped!" in ser_bytes): #if line == stopped:
                    RecordForce.hasStopped = True
                    print(stopped+" received by arduino.")
                    #RecordForce.ser.close()
                    #print(RecordForce.dataStream)
                    '''
                    RecordForce.allocateNineCellData() # what is this for, nine cell stuff?
                    '''
        RecordForce.ser.close()
        print("Test runtime: ",max(GUI.timeElapsed)/1000," seconds.")
                        
    def stopAndSave():
        time.sleep(.1)
        if GUI.ignoreserial == False:
                
            testForNineCellFilename()
            if RecordForce.ser.isOpen():
                try:
                    RecordForce.ser.flushInput()# wait until all data is written
                    #print("Not flushing input.")
                except:
                    print("failed RecordForce.ser.flushInput()")
                RecordForce.sendStop()
                
            RecordForce.saveForce()
        else:
            print("File not saved. GUI.ignoreserial == True.")

    def saveForce():
        createBackupFile()
        # force data filename
        filename_force = GUI.filename_force.get()
        filename_force_csv = GUI.address + '/' + (GUI.filename_force.get()) + '.csv'
        if overwriteGuard(filename_force_csv) == True: # filename already exists, needs to be renamed
            rename(filename_force) # prompt user to rename file

        #ave. SOCEM velocity
        avelocity = ["AvgTravelVelocity(cm/s)"]
        try:
            travelvelocity = max(GUI.distanceTraveled)/(max(GUI.timeElapsed)/1000) #cm/s
            avelocity.append(travelvelocity)
        except:
            travelvelocity=0
            avelocity.append(travelvelocity)

        #Sampling Rate
        sampling=["SamplingRate(Hz)"]
        hz = list()
        try:
            for i in range(len(GUI.distanceTraveled)-1):
                change = GUI.timeElapsed[i+1] - GUI.timeElapsed[i] # ms
                hz.append(change)
            rate = sum(hz)/len(hz)/1000 # why flip? 
            sampling.append(1/rate) # why flip?
        except:
            rate = 0
            sampling.append(0)

        GUI.travelvelocity = travelvelocity
        GUI.samplingrate = 1/rate # changed from 1/rate, to avoid a divide by zero error

        RecordForce.sidehitPeakClick()
                
        if GUI.ignoreserial == False and len(GUI.forcePushed)>0:
            GUI.distanceTraveled.insert(0, "Distance(cm)")
            GUI.forcePushed.insert(0, "Force(N)")
            GUI.timeElapsed.insert(0 , "Time(ms)")

            ''' write CSV'''
            GUI.data_recordForce = [GUI.timeElapsed,GUI.distanceTraveled, GUI.forcePushed, avelocity, sampling,RecordForce.peaks_force,RecordForce.peaks_distance,RecordForce.peaks_time]
            columns_data_recordForce = zip_longest(*GUI.data_recordForce)
            with open(filename_force_csv,'w',newline='') as f:
                writer = csv.writer(f)
                writer.writerows(columns_data_recordForce)
            ''' end: write CSV '''
            print("filename_force_csv = "+filename_force_csv)
            
            # tell user raw data was saved
            #print("File saved: "+GUI.filename_force.get()+".csv\n")
            try:
                forceSaved_label = Label(RecordForce.msgbox, text = "Force data saved.", font = ("arial", 14, "bold"), fg = "dodgerblue3", bg = "ghost white")
                #forceSaved_label = Label(RecordForce.msgbox, text = "Force data saved.", font = ("arial", 14, "bold"), fg = "dodgerblue3", bg = "ghost white").grid(row=0, column=0)
            except:
                print("attempt to generate in-window forceSaved_label messsage. fail, dave.")
        else:
            print("Force data not saved. GUI.ignoreserial = "+str(GUI.ignoreserial)+". len(GUI.forcePushed) = ",len(GUI.forcePushed))
            
        #RecordForce.clearDisplay()
        '''
        self.instantGraph()
        '''
        '''
        Why clear?
        GUI.timeElapsed.clear()
        GUI.forcePushed.clear()
        GUI.distanceTraveled.clear()
        avelocity.clear()
        hz.clear()
        sampling.clear()
        '''
        
    '''
    def overwriteGuard(self, filename):# prevents overwriting by checking if filename already exists in saving folder
        return path.exists(filename) # True = already exits, False = doesn't exist
    '''
    '''
    #auto graph feature 
    def instantGraph(self):
        try:
        #if self.dataset-1 <= 1:
            self.legends = []
        except:
            pass
            
        if not plt.get_fignums():#if graph figure was closed, reset legend
            self.legends.clear()
            #print("new fig who dis")
        self.legends.append(GUI.filename_force.get())#add current filename to legend
        #fig = plt.figure(figsize=(8,4.8)) #fig size control 
        #plots force displacement graph
        print("len(GUI.distanceTraveled) = ",len(GUI.distanceTraveled))
        if self.checkAutoGraph.get() == 1 and len(GUI.distanceTraveled)>5 and GUI.ignoreserial == False:
            plt.plot(GUI.distanceTraveled, GUI,forcePushed)
            plt.xlabel("Distance (cm)")
            plt.ylabel("Force (N)")
            plt.title(filename.get())
            plt.legend(self.legends)
            plt.axis = ([min(distance), max(distance), min(force), max(force)])
            plt.show()
        else:
            print("There is no data to graph. Try GUI.ignoreserial = False, in StemBerry.")
        '''
    def sidehitPeakClick():
        RecordForce.peaks_force,RecordForce.peaks_distance,RecordForce.peaks_time= [],[],[]
        # currently only lauches click assessment for side1, side2, side3
        #print("GUI.currentdirection = ",GUI.currentdirection.get())
        #print("len(GUI.forcePushed) = ",len(GUI.forcePushed))
        if (GUI.currentdirection.get() == "side1") or (GUI.currentdirection.get() == "side2") or (GUI.currentdirection.get() == "side3"): 
            if len(GUI.forcePushed)>0:
                varietyAndPlotnameAndDetail = GUI.filename_force.get()
                RecordForce.plotshown = True
                RecordForce.closedplt = False
                RecordForce.thread3_plotchecker = threading.Thread(target = RecordForce.plotchecker)
                RecordForce.thread3_plotchecker.start()
                peakclick.peakclick(GUI.forcePushed,GUI.distanceTraveled,GUI.timeElapsed,GUI.filename_force.get(),GUI.address,GUI.travelvelocity)
                #RecordForce.peaks_force,RecordForce.peaks_distance,RecordForce.peaks_time = peakclick.peaks_force,peakclick.peaks_distance,peakclick.peaks_time
                
                # RecordForce.sortClicks(RecordForce.peaks_force,RecordForce.peaks_distance,RecordForce.peaks_time)
                print("Delete this note about side hit completing")
            else:
                print("PeaksClick figure not triggered because len(GUI.forcePushed) = 0.")
    def plotchecker():
        while RecordForce.plotshown == True:
            time.sleep(1)
            if RecordForce.closedplt == True:
                time.sleep(.5)
                RecordForce.sortClicks()
                RecordForce.plotshown = False
            '''
            else:
                print("loop while")
                '''
    def allocateNineCellData():
        print("allocate")

    def sortClicks():
        if GUI.currentdirection.get() == "side1":
            GUI.peak_force_cell1, GUI.peak_force_cell2, GUI.peak_force_cell3 = RecordForce.peaks_force[0],RecordForce.peaks_force[1],RecordForce.peaks_force[2]
            GUI.peak_distance_cell1, GUI.peak_distance_cell2, GUI.peak_distance_cell3 = RecordForce.peaks_distance[0],RecordForce.peaks_distance[1],RecordForce.peaks_distance[2]
            GUI.peak_time_cell1, GUI.peak_time_cell2, GUI.peak_time_cell3=RecordForce.peaks_time[0],RecordForce.peaks_time[1],RecordForce.peaks_time[2]
        elif GUI.currentdirection.get() == "side2":
            GUI.peak_force_cell4, GUI.peak_force_cell5, GUI.peak_force_cell6 = RecordForce.peaks_force[0],RecordForce.peaks_force[1],RecordForce.peaks_force[2]
            GUI.peak_distance_cell4, GUI.peak_distance_cell5, GUI.peak_distance_cell6 = RecordForce.peaks_distance[0],RecordForce.peaks_distance[1],RecordForce.peaks_distance[2]
            GUI.peak_time_cell4, GUI.peak_time_cell5, GUI.peak_time_cell6=RecordForce.peaks_time[0],RecordForce.peaks_time[1],RecordForce.peaks_time[2]
        elif GUI.currentdirection.get() == "side3":
            GUI.peak_force_cell7, GUI.peak_force_cell8, GUI.peak_force_cell9 = RecordForce.peaks_force[0],RecordForce.peaks_force[1],RecordForce.peaks_force[2]
            GUI.peak_distance_cell7, GUI.peak_distance_cell8, GUI.peak_distance_cell9 = RecordForce.peaks_distance[0],RecordForce.peaks_distance[1],RecordForce.peaks_distance[2]
            GUI.peak_time_cell7, GUI.peak_time_cell8, GUI.peak_time_cell9=RecordForce.peaks_time[0],RecordForce.peaks_time[1],RecordForce.peaks_time[2]

    #zeroes load cell measurement
            
    def tare():
        if GUI.ignoreserial == False:
            RecordForce.ser.flush()#wait until all data is written
            tare = 't'
            RecordForce.ser.write(tare.encode()) #sends 't' to arduino, telling it to tare
            time.sleep(0.3)#wait x seconds for Arduino to tare load cell (for smoothing)
        else:
            print("\nYou hit the 'tare' button while GUI.ignoreserial == True.\nLoadcell cannot be tared because it is neither connected nor sought.")
            RecordForce.message_connectArduino()
            
    def message_connectArduino():
        #print("\nYou hit the 'tare' button while GUI.ignoreserial == True.\nLoadcell cannot be tared because it is neither connected nor sought.\n\nConnect an arduino.\nFlash Ardunio with serialConnection_v11.ino(&+).\n\nIn StemBerry header variables:\nGUI.ignoreserial = False.\nMatch dev_manual port ID with ID on Arduino IDE.\n\nSigned, Clayton Bennett, August 25, 2022.")
        print("\n\nConnect an arduino.\nFlash Ardunio with serialConnection_v11.ino(&+).\n\nIn StemBerry header variables:\nGUI.ignoreserial = False.\nMatch dev_manual port ID with ID on Arduino IDE.\n\nSigned, Clayton Bennett, August 25, 2022.")

    def on_show_frame_RecordForce(self, event):
        #Flip to data collection screen, GUI variables
        if (GUI.varietyname.get()!="" or GUI.plotname.get()!="") and (GUI.passfillednames_checkbox.get()==1): # checks if a varietyname or plotname has been given
            self.nameFresh(GUI.varietyname.get(),GUI.plotname.get()) # if so, autopopulate the basic filestructure
        filename_force = nameBlackBox("",GUI.filename_force.get())
        GUI.filename_force.set(filename_force)
        
class StemCountClassic(tk.Frame):
    def __init__(self, parent, controller): # automatically runs
        
        tk.Frame.__init__(self, parent)

        header_label = Label(self, text = "STEM COUNT INITIAL INPUT", font = ("arial", 17, "bold"), fg = "gray3", bg="ghost white")
        construction_label = Label(self, text = "Under Construction.\nWill allow user to input sample density data before pushing SOCEM,\nrather than use the nine-cell post test count input fields.", font = ("arial", 17, "bold"), fg = "red4", bg="ghost white")
        header_label.place(x=235,y=0)
        construction_label.place(x=10,y=100)
        
        pageButtons = repeatPageButtons.showButtons(self, parent, controller)
    
# Load cell calibration page 
class Calibrate(tk.Frame):
    
    def __init__(self, parent, controller): # automatically runs
        
        tk.Frame.__init__(self, parent)
        
        ''' GUI design, non-frame '''
        pageButtons = repeatPageButtons.showButtons(self, parent, controller)
        header_label = Label(self, text = "FORCE SENSOR CALIBRATION", font = ("arial", 17, "bold"), fg = "gray3", bg="ghost white")
        tareIt_label = Label(self, text = "1. Tare w/ no weight", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white")
        inputWeight_label = Label(self, text = "2. Input weight (kg)", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white")
        caliIt_label = Label(self, text = '3. Place weight', font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white")
        caliIt4_label = Label(self, text = '4. Optimize so Diff. = 0', font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white")
        testWeight_label = Label(self, text = "Weight:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white")

        header_label.place(x=235,y=0)
        tareIt_label.place(x=5,y=43)
        inputWeight_label.place(x=5,y=73)
        caliIt_label.place(x=5,y=103)
        caliIt4_label.place(x=5,y=133)
        testWeight_label.place(x=5,y=183)
        

        self.knownWeight = DoubleVar() # know weight textvariable
        self.knownWeight.set(0.0) # initially = 1.0 kg (assuming 1.0 kg will be used)
        knownW_entry = Entry(self, textvariable=self.knownWeight, font = ("arial", 14, "bold"), width= 5, bg="white", fg="gray1").place(x = 80, y =183)

        kg = Label(self, text = "kg", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").place(x=140,y=183)

        self.force = self.knownWeight.get() * convert_KgToN # convert known weight kg to N
        self.strWeight = str('%.3f' % self.force) # store as string
        self.strForce = StringVar() # for displaying & updating on GUI
        self.strForce.set(self.strWeight) # initial value = self.knownWeight

        eq_label = Label(self, text = '= ', font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white")
        force_label = Label(self, textvariable = self.strForce, font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white")
        unit_label = Label(self, text = " N", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white")
        cali_label = Label(self, text = "Cali. Factor:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white")

        eq_label.place(x=170,y=183)
        force_label.place(x=187,y=183)
        unit_label.place(x=249,y=183)
        cali_label.place(x=5,y=223)
    
        self.calibra =  DoubleVar() 
        self.calibra.set(199750) # initial calibration num. Has been working well. AB.
        self.factor = self.calibra.get() 
        self.calibra_entry = Entry(self, textvariable=self.calibra, font = ("arial", 14, "bold"), width= 10, bg="white", fg="gray1")
        

        #tares/zeros load cell
        tare_button = Button(self, text = "Tare", font = ("arial", 16, "bold"), height = 3, width = 8, fg = "ghost white", bg = "gray2",command=lambda:RecordForce.tare) # confirm this works
        # updates cali factor & starts/continues cali. process
        cali_button = Button(self, text ="Update\nCali.\nFactor", font = ("arial", 16, "bold"), height = 3, width = 8, fg = "ghost white", bg = "gray2", command=lambda:self.caliThread())
        # stops cali. process
        done_button = Button(self, text ="Done", font = ("arial", 16, "bold"), height = 3, width = 8, fg = "ghost white", bg = "gray2", command=lambda:self.doneCali())
        # + 1000 to calibra
        p1000_button = Button(self, text ="+1000", font = ("arial", 16, "bold"), height = 1, width = 8, fg = "ghost white", bg = "gray2", command=lambda:self.updateCali(1000))
        # - 1000 to calibra
        n1000_button = Button(self, text ="-1000", font = ("arial", 16, "bold"), height = 1, width = 8, fg = "ghost white", bg = "gray2", command=lambda:self.updateCali(-1000))
        # + 100
        p100_button = Button(self, text ="+100", font = ("arial", 16, "bold"), height = 1, width = 8, fg = "ghost white", bg = "gray2", command=lambda:self.updateCali(100))
        # - 100
        n100_button = Button(self, text ="-100", font = ("arial", 16, "bold"), height = 1, width = 8, fg = "ghost white", bg = "gray2", command=lambda:self.updateCali(-100))

        scroll = Scrollbar(self)

        self.LC_label = Label(self, text = "N",font = ("arial", 14, "bold"), fg = "dodgerblue3", bg = "ghost white")
        self.LClist = Listbox(self, yscrollcommand = scroll.set, bg = "ghost white",highlightbackground = "gray2", width = 7, height = 10, font = ("arial", 14, "bold"), fg = "dodgerblue3")
        self.Diff_label = Label(self, text = "Diff.",font = ("arial", 14, "bold"), fg = "dodgerblue3", bg = "ghost white")
        self.Difflist = Listbox(self, yscrollcommand = scroll.set, bg = "ghost white",highlightbackground = "gray2", width = 7, height = 10, font = ("arial", 14, "bold"), fg = "dodgerblue3")

        self.calibra_entry.place(x = 125, y = 223)
        tare_button.place(x = 559, y = 44)
        cali_button.place(x = 675, y = 44)
        done_button.place(x = 675, y = 224)
        p1000_button.place(x = 559, y = 136)
        n1000_button.place(x = 559, y = 136+44)
        p100_button.place(x = 675, y = 136)
        n100_button.place(x = 675, y = 136+44)
        
        self.LC_label.place(x = 330, y = 43)
        self.LClist.place(x = 310, y = 73)
        self.Diff_label.place(x = 420, y = 43)
        self.Difflist.place(x = 400, y = 73)

    def updateCali(self, cali): # update calibration factor
        self.factor = self.calibra.get() + cali
        self.calibra_entry.delete(0, 'end')
        self.calibra_entry.insert(0, self.factor)
        return self.factor

    def tare(self):
        RecordForce.ser.flush()#wait until all data is written
        tare = 't'
        RecordForce.ser.write(tare.encode()) #sends 't' to arduino, telling it to tare
        time.sleep(0.3)#wait x seconds for Arduino to tare load cell (for smoothing)
       
    def caliFactor(self):
        self.force = self.knownWeight.get() * convert_KgToN # convert known weight kg to lbs
        self.strW = str('%.3f' % self.force) # store as string
        self.strForce.set(self.strW) # update GUI text
        
        scroll = Scrollbar(self)
        self.factor = self.calibra.get() # get user input calibration factor
        self.doneCali() # if Arduino sending force data, this will momentarily stop it 
        
        strFactor = str(self.factor) # cali factor as string
        RecordForce.ser.write(strFactor.encode()) # send cali factor to Arduino
        RecordForce.ser.flush() # make sure it gets it before proceeding

        global caliLoop
        caliLoop = True

        while caliLoop == True: # loop to continuously print Arduino force readings

            if RecordForce.ser.inWaiting() > 0: #checks to see if Serial is available 
                    
                try: #make sure serial data can be read/is there
                    ser_bytes = RecordForce.ser.readline()
                except:
                    GUI.errors.append('serial read')
                    eCode = 'e8'
                    GUI.errorCodes.append(eCode)
                    print("eCode = "+eCode)
                    #popup("serial read")
                    
                bytesDecoded = (ser_bytes[0:len(ser_bytes)-2].decode("utf-8")) # force reading bytes
                try:
                    reading = float(bytesDecoded) # convert bytes to float
                    diff = self.force - reading # difference between reading & known weight
                    self.LClist.insert(END, str('%.2f' % reading)) # scrollbar list for force readings
                    self.Difflist.see(END)
                    self.Difflist.insert(END, str('%.1f' % diff)) # scrollbar list for forcebar - known weight 
                    self.LClist.see(END)
                except:
                    pass 

                
    def caliThread(self): #threading calibrate function (simultaneously performs caliFactor function in backend)
        thread = threading.Thread(target = Calibrate.caliFactor,args=(self,))
        thread.start()

    def doneCali(self): # stops calibration process
        RecordForce.ser.reset_input_buffer()# clear the input buffer
        global caliLoop
        caliLoop = False # stop loop asking for data
        
        send = 'd' # stop Arduino sending
        RecordForce.ser.write(send.encode()) # send 'd' to stop Arduino sending data
        
# error page for displaying errors
class ErrorReport(tk.Frame):

    def __init__(self, parent, controller): # automatically runs
        tk.Frame.__init__(self, parent)

        # button that returns to Geo. Inputs page
        initialInputs_button = Button(self, text ="Initial\nInputs", font = ("arial", 16, "bold"), height = 3, width = 8, fg = "ghost white", bg = "gray2",command=lambda:GUI.show_frame(InitialInputs))
        initialInputs_button.place(x = 675, y = 316)
        # button that returns to RecordForce page
        recordForce_button = Button(self, text = "Record\nForce",font = ("arial", 16, "bold"), height = 3, width = 8, fg = "ghost white", bg = "gray2",command=lambda:GUI.show_frame(RecordForce))
        recordForce_button.place(x = 675, y = 225)
        
        scroll = Scrollbar(self)
        
        self.ErrorCode_label = Label(self, text = "Error Code\n(Location)",font = ("arial", 14, "bold"), fg = "gray3", bg = "ghost white").place(x = 179, y = 50)
        self.ErrorCodeList = Listbox(self, yscrollcommand = scroll.set, bg = "ghost white",highlightbackground = "gray2", width = 10, height = 13, font = ("arial", 14, "bold"), fg = "dodgerblue3")
        self.ErrorCodeList.place(x = 175, y = 100)

        self.Error_label = Label(self, text = "Description",font = ("arial", 14, "bold"), fg = "gray3", bg = "ghost white")
        self.Error_label.place(x = 400, y = 75)
        self.ErrorDesc = Listbox(self, yscrollcommand = scroll.set, bg = "ghost white",highlightbackground = "gray2", width = 30, height = 13, font = ("arial", 14, "bold"), fg = "dodgerblue3")
        self.ErrorDesc.place(x = 289, y = 100)
        
    def showErrors2(self):

        self.ErrorCodeList.delete(0, 'end')
        self.ErrorDesc.delete(0, 'end')

        for e in range(len(GUI.errorCodes)):
            self.ErrorCodeList.insert(END, GUI.errorCodes[e])# inserts at end of listbox to actually display
            self.ErrorCodeList.see(END)# makes sure listbox is at end so it displays live data
            self.ErrorDesc.insert(END, GUI.errors[e])
            self.ErrorDesc.see(END)
'''
class Heights(tk.Frame):
    destroyed. see StemBerry_v13.
'''
 # Guide page 
class Guide(tk.Frame):
    def __init__(self, parent, controller): # automatically runs
        tk.Frame.__init__(self, parent)

        pageButtons = repeatPageButtons.showButtons(self, parent, controller)

        # button that enters Calibrate page/class
        calibrate_button = Button(self, text = "Calibrate\nForce\nSensor", font = ("arial", 16, "bold"), height = 3, width = 8, fg = "ghost white", bg = "gray2", command=lambda:GUI.show_frame(Calibrate)) #tares/zeros load cell
        calibrate_button.place(x = 510, y = 340)
        
        # instruction steps:
        '''
        Nine-cell scheme design:
        '''
        guide_frame = tk.LabelFrame(self, text='Nine-Cell Scheme',font = ("arial", 14, "bold"), width= 10, bg="white", fg="gray1")
        guide_frame.place(x = 0, y = 20)
        #guideHeader = Label(self, text = "Nine-cell scheme design", font = ("arial", 17, "bold"), fg = "gray3", bg="ghost white").place(x=350,y=0)
        one = Label(guide_frame, text = '1.  Equalize stem heights', font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=0, column=0)
        two = Label(guide_frame, text = '2.  Record Variety and Plot names', font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=1, column=0)
        three = Label(guide_frame, text = '3.  Enter stem height and cell location data', font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=2, column=0)
        four = Label(guide_frame, text = '4.  Perform four SOCEM tests (3 side hits, 1 forward hit)', font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=3, column=0)
        five = Label(guide_frame, text = '5.  Collect stems for mass, count, and diameters.', font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=4, column=0)
        six = Label(guide_frame, text = '6.  Press compile to complete nine-cell data object.\nGo on to the next small plot!', font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=5, column=0)  
        
        try:
            # SOCEM diagram of use # 
            load = Image.open('GuideSOCEM_2022.png')
            load = load.resize((275,275))
            render = ImageTk.PhotoImage(load)
            img = Label(self, image=render)
            img.image = render
            img.place(x = 520, y = 35)
        except:
            print("Guide image not found.")
        
class FinalInputs(tk.Frame):
        
    def __init__(self, parent, controller): # automatically runs

        FinalInputs.mass1 = [] # TypeError: 'float' object is not iterable
        FinalInputs.mass2 = []
        FinalInputs.mass3 = []
        FinalInputs.mass4 = []
        FinalInputs.mass5 = []
        FinalInputs.mass6 = []
        FinalInputs.mass7 = []
        FinalInputs.mass8 = []
        FinalInputs.mass9 = []
        FinalInputs.count1 = [] 
        FinalInputs.count2 = []
        FinalInputs.count3 = []
        FinalInputs.count4 = []
        FinalInputs.count5 = []
        FinalInputs.count6 = []
        FinalInputs.count7 = []
        FinalInputs.count8 = []
        FinalInputs.count9 = []

        FinalInputs.diam1 = []
        FinalInputs.diam2 = []
        FinalInputs.diam3 = []
        FinalInputs.diam4 = []
        FinalInputs.diam5 = []
        FinalInputs.diam6 = []
        FinalInputs.diam7 = []
        FinalInputs.diam8 = []
        FinalInputs.diam9 = []
        
        tk.Frame.__init__(self, parent)

        ''' GUI design, non-frame '''
        pageButtons = repeatPageButtons.showButtons(self, parent, controller)
        unit_label = Label(self, text=str("Mass unit is kilograms, diameter unit is millimeters."), font = ("arial", 12, "italic"), fg = "red4", bg="ghost white")        
        #backupFinalInputs_button = Button(self, text ="Create Backup File", font = ("arial", 14, "bold"), height = 1, width = 20, fg = "ghost white", bg = "dodgerblue3", command=lambda:createBackupFile())
        savePostTestInputs_button = Button(self, text ="Save Post Test Inputs", font = ("arial", 14, "bold"), height = 1, width = 20, fg = "ghost white", bg = "dodgerblue3", command=lambda:self.savePostTestInputs())
        compileNineCellData_button = Button(self, text ="Compile Nine-Cell Data", font = ("arial", 14, "bold"), height = 1, width = 20, fg = "ghost white", bg = "dodgerblue3", command=lambda:self.compileNineCellData())
        
        unit_label.place(x=400+30,y=0)
        #backupFinalInputs_button.place(x = 510, y = 340+38)
        compileNineCellData_button.place(x = 510, y = 340+38)
        savePostTestInputs_button.place(x = 510, y = 340)

        ''' Frame: Cell 1 '''
        cell1_frame = tk.LabelFrame(self, text='Cell 1',font = ("arial", 14, "bold"), width= 10, bg="white", fg="gray1")
        cell1_frame.place(x = 0, y = 230)
        cell1Mass_label = Label(cell1_frame, text = "Mass:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=0, column=0)
        cell1Count_label = Label(cell1_frame, text = "Count:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=1, column=0)
        cell1Diameters_label = Label(cell1_frame, text = "Diam:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=2, column=0)
        cell1Mass_entry = Entry(cell1_frame, textvariable=GUI.cell1Mass, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=0, column=1)
        cell1Count_entry = Entry(cell1_frame, textvariable=GUI.cell1Count, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=1, column=1)
        cell1Diameter1_entry = Entry(cell1_frame, textvariable=GUI.cell1Diameter1, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=2, column=1)
        cell1Diameter2_entry = Entry(cell1_frame, textvariable=GUI.cell1Diameter2, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=2)
        cell1Diameter3_entry = Entry(cell1_frame, textvariable=GUI.cell1Diameter3, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=3)
        cell1Diameter4_entry = Entry(cell1_frame, textvariable=GUI.cell1Diameter4, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=4)
        ''' end '''

        ''' Frame: Cell 2 '''
        cell2_frame = tk.LabelFrame(self, text='Cell 2',font = ("arial", 14, "bold"), width= 10, bg="white", fg="gray1")
        #cell2_frame.place(x = 250, y = 230)
        cell2_frame.place(x = 0, y = 125)
        cell2Mass_label = Label(cell2_frame, text = "Mass:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=0, column=0)
        cell2Count_label = Label(cell2_frame, text = "Count:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=1, column=0)
        cell2Diameters_label = Label(cell2_frame, text = "Diam:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=2, column=0)
        cell2Mass_entry = Entry(cell2_frame, textvariable=GUI.cell2Mass, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=0, column=1)
        cell2Count_entry = Entry(cell2_frame, textvariable=GUI.cell2Count, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=1, column=1)
        cell2Diameter1_entry = Entry(cell2_frame, textvariable=GUI.cell2Diameter1, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=2, column=1)
        cell2Diameter2_entry = Entry(cell2_frame, textvariable=GUI.cell2Diameter2, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=2)
        cell2Diameter3_entry = Entry(cell2_frame, textvariable=GUI.cell2Diameter3, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=3)
        cell2Diameter4_entry = Entry(cell2_frame, textvariable=GUI.cell2Diameter4, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=4)
        ''' end '''

        ''' Frame: Cell 3 '''
        cell3_frame = tk.LabelFrame(self, text='Cell 3',font = ("arial", 14, "bold"), width= 10, bg="white", fg="gray1")
        #cell3_frame.place(x = 500, y = 230)
        cell3_frame.place(x = 0, y = 20)
        cell3Mass_label = Label(cell3_frame, text = "Mass:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=0, column=0)
        cell3Count_label = Label(cell3_frame, text = "Count:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=1, column=0)
        cell3Diameters_label = Label(cell3_frame, text = "Diam:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=2, column=0)
        cell3Mass_entry = Entry(cell3_frame, textvariable=GUI.cell3Mass, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=0, column=1)
        cell3Count_entry = Entry(cell3_frame, textvariable=GUI.cell3Count, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=1, column=1)
        cell3Diameter1_entry = Entry(cell3_frame, textvariable=GUI.cell3Diameter1, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=2, column=1)
        cell3Diameter2_entry = Entry(cell3_frame, textvariable=GUI.cell3Diameter2, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=2)
        cell3Diameter3_entry = Entry(cell3_frame, textvariable=GUI.cell3Diameter3, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=3)
        cell3Diameter4_entry = Entry(cell3_frame, textvariable=GUI.cell3Diameter4, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=4)
        ''' end '''

        ''' Frame: Cell 4 '''
        cell4_frame = tk.LabelFrame(self, text='Cell 4',font = ("arial", 14, "bold"), width= 10, bg="white", fg="gray1")
        #cell4_frame.place(x = 0, y = 125)
        cell4_frame.place(x = 250, y = 230)
        cell4Mass_label = Label(cell4_frame, text = "Mass:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=0, column=0)
        cell4Count_label = Label(cell4_frame, text = "Count:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=1, column=0)
        cell4Diameters_label = Label(cell4_frame, text = "Diam:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=2, column=0)
        cell4Mass_entry = Entry(cell4_frame, textvariable=GUI.cell4Mass, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=0, column=1)
        cell4Count_entry = Entry(cell4_frame, textvariable=GUI.cell4Count, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=1, column=1)
        cell4Diameter1_entry = Entry(cell4_frame, textvariable=GUI.cell4Diameter1, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=2, column=1)
        cell4Diameter2_entry = Entry(cell4_frame, textvariable=GUI.cell4Diameter2, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=2)
        cell4Diameter3_entry = Entry(cell4_frame, textvariable=GUI.cell4Diameter3, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=3)
        cell4Diameter4_entry = Entry(cell4_frame, textvariable=GUI.cell4Diameter4, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=4)
        ''' end '''

        ''' Frame: Cell 5 '''
        cell5_frame = tk.LabelFrame(self, text='Cell 5',font = ("arial", 14, "bold"), width= 10, bg="white", fg="gray1")
        cell5_frame.place(x = 250, y = 125)
        cell5Mass_label = Label(cell5_frame, text = "Mass:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=0, column=0)
        cell5Count_label = Label(cell5_frame, text = "Count:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=1, column=0)
        cell5Diameters_label = Label(cell5_frame, text = "Diam:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=2, column=0)
        cell5Mass_entry = Entry(cell5_frame, textvariable=GUI.cell5Mass, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=0, column=1)
        cell5Count_entry = Entry(cell5_frame, textvariable=GUI.cell5Count, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=1, column=1)
        cell5Diameter1_entry = Entry(cell5_frame, textvariable=GUI.cell5Diameter1, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=2, column=1)
        cell5Diameter2_entry = Entry(cell5_frame, textvariable=GUI.cell5Diameter2, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=2)
        cell5Diameter3_entry = Entry(cell5_frame, textvariable=GUI.cell5Diameter3, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=3)
        cell5Diameter4_entry = Entry(cell5_frame, textvariable=GUI.cell5Diameter4, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=4)
        ''' end '''

        ''' Frame: Cell 6 '''
        cell6_frame = tk.LabelFrame(self, text='Cell 6',font = ("arial", 14, "bold"), width= 10, bg="white", fg="gray1")
        #cell6_frame.place(x = 500, y = 125)
        cell6_frame.place(x = 250, y = 20)
        cell6Mass_label = Label(cell6_frame, text = "Mass:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=0, column=0)
        cell6Count_label = Label(cell6_frame, text = "Count:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=1, column=0)
        cell6Diameters_label = Label(cell6_frame, text = "Diam:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=2, column=0)
        cell6Mass_entry = Entry(cell6_frame, textvariable=GUI.cell6Mass, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=0, column=1)
        cell6Count_entry = Entry(cell6_frame, textvariable=GUI.cell6Count, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=1, column=1)
        cell6Diameter1_entry = Entry(cell6_frame, textvariable=GUI.cell6Diameter1, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=2, column=1)
        cell6Diameter2_entry = Entry(cell6_frame, textvariable=GUI.cell6Diameter2, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=2)
        cell6Diameter3_entry = Entry(cell6_frame, textvariable=GUI.cell6Diameter3, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=3)
        cell6Diameter4_entry = Entry(cell6_frame, textvariable=GUI.cell6Diameter4, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=4)
        ''' end '''

        ''' Frame: Cell 7 '''
        cell7_frame = tk.LabelFrame(self, text='Cell 7',font = ("arial", 14, "bold"), width= 10, bg="white", fg="gray1")
        #cell7_frame.place(x = 0, y = 20)
        cell7_frame.place(x = 500, y = 230)
        cell7Mass_label = Label(cell7_frame, text = "Mass:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=0, column=0)
        cell7Count_label = Label(cell7_frame, text = "Count:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=1, column=0)
        cell7Diameters_label = Label(cell7_frame, text = "Diam:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=2, column=0)
        cell7Mass_entry = Entry(cell7_frame, textvariable=GUI.cell7Mass, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=0, column=1)
        cell7Count_entry = Entry(cell7_frame, textvariable=GUI.cell7Count, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=1, column=1)
        cell7Diameter1_entry = Entry(cell7_frame, textvariable=GUI.cell7Diameter1, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=2, column=1)
        cell7Diameter2_entry = Entry(cell7_frame, textvariable=GUI.cell7Diameter2, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=2)
        cell7Diameter3_entry = Entry(cell7_frame, textvariable=GUI.cell7Diameter3, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=3)
        cell7Diameter4_entry = Entry(cell7_frame, textvariable=GUI.cell7Diameter4, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=4)
        ''' end '''
        
        ''' Frame: Cell 8 '''
        cell8_frame = tk.LabelFrame(self, text='Cell 8',font = ("arial", 14, "bold"), width= 10, bg="white", fg="gray1")
        #cell8_frame.place(x = 250, y = 20)
        cell8_frame.place(x = 500, y = 125)
        cell8Mass_label = Label(cell8_frame, text = "Mass:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=0, column=0)
        cell8Count_label = Label(cell8_frame, text = "Count:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=1, column=0)
        cell8Diameters_label = Label(cell8_frame, text = "Diam:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=2, column=0)
        cell8Mass_entry = Entry(cell8_frame, textvariable=GUI.cell8Mass, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=0, column=1)
        cell8Count_entry = Entry(cell8_frame, textvariable=GUI.cell8Count, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=1, column=1)
        cell8Diameter1_entry = Entry(cell8_frame, textvariable=GUI.cell8Diameter1, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=2, column=1)
        cell8Diameter2_entry = Entry(cell8_frame, textvariable=GUI.cell8Diameter2, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=2)
        cell8Diameter3_entry = Entry(cell8_frame, textvariable=GUI.cell8Diameter3, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=3)
        cell8Diameter4_entry = Entry(cell8_frame, textvariable=GUI.cell8Diameter4, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=4)
        ''' end '''
        
        ''' Frame: Cell 9 '''
        cell9_frame = tk.LabelFrame(self, text='Cell 9',font = ("arial", 14, "bold"), width= 10, bg="white", fg="gray1")
        cell9_frame.place(x = 500, y = 20)
        cell9Mass_label = Label(cell9_frame, text = "Mass:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=0, column=0)
        cell9Count_label = Label(cell9_frame, text = "Count:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=1, column=0)
        cell9Diameters_label = Label(cell9_frame, text = "Diam:", font = ("arial", 14, "bold"), fg = "gray3", bg="ghost white").grid(row=2, column=0)
        cell9Mass_entry = Entry(cell9_frame, textvariable=GUI.cell9Mass, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=0, column=1)
        cell9Count_entry = Entry(cell9_frame, textvariable=GUI.cell9Count, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=1, column=1)
        cell9Diameter1_entry = Entry(cell9_frame, textvariable=GUI.cell9Diameter1, font = ("arial", 14, "bold"), width=4, bg="white", fg="gray1").grid(row=2, column=1)
        cell9Diameter2_entry = Entry(cell9_frame, textvariable=GUI.cell9Diameter2, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=2)
        cell9Diameter3_entry = Entry(cell9_frame, textvariable=GUI.cell9Diameter3, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=3)
        cell9Diameter4_entry = Entry(cell9_frame, textvariable=GUI.cell9Diameter4, font = ("arial", 14, "bold"), width=3, bg="white", fg="gray1").grid(row=2, column=4)
        ''' end '''

        self.bind("<<ShowFrame>>", self.on_show_frame_FinalInputs) # need this?
              
    def savePostTestInputs(self):   
        
        filename_postTest_csv = GUI.address + '/' + (GUI.filename_postTest.get()) + '.csv'
     
        FinalInputs.mass1 = [GUI.cell1Mass.get()] # TypeError: 'float' object is not iterable
        FinalInputs.mass2 = [GUI.cell2Mass.get()]
        FinalInputs.mass3 = [GUI.cell3Mass.get()]
        FinalInputs.mass4 = [GUI.cell4Mass.get()]
        FinalInputs.mass5 = [GUI.cell5Mass.get()]
        FinalInputs.mass6 = [GUI.cell6Mass.get()]
        FinalInputs.mass7 = [GUI.cell7Mass.get()]
        FinalInputs.mass8 = [GUI.cell8Mass.get()]
        FinalInputs.mass9 = [GUI.cell9Mass.get()]
        FinalInputs.count1 = [GUI.cell1Count.get()] # TypeError: 'float' object is not iterable
        FinalInputs.count2 = [GUI.cell2Count.get()]
        FinalInputs.count3 = [GUI.cell3Count.get()]
        FinalInputs.count4 = [GUI.cell4Count.get()]
        FinalInputs.count5 = [GUI.cell5Count.get()]
        FinalInputs.count6 = [GUI.cell6Count.get()]
        FinalInputs.count7 = [GUI.cell7Count.get()]
        FinalInputs.count8 = [GUI.cell8Count.get()]
        FinalInputs.count9 = [GUI.cell9Count.get()]

        FinalInputs.diam1 = [GUI.cell1Diameter1.get(),GUI.cell1Diameter2.get(),GUI.cell1Diameter3.get(),GUI.cell1Diameter4.get()]
        FinalInputs.diam2 = [GUI.cell2Diameter1.get(),GUI.cell2Diameter2.get(),GUI.cell2Diameter3.get(),GUI.cell2Diameter4.get()]
        FinalInputs.diam3 = [GUI.cell3Diameter1.get(),GUI.cell3Diameter2.get(),GUI.cell3Diameter3.get(),GUI.cell3Diameter4.get()]
        FinalInputs.diam4 = [GUI.cell4Diameter1.get(),GUI.cell4Diameter2.get(),GUI.cell4Diameter3.get(),GUI.cell4Diameter4.get()]
        FinalInputs.diam5 = [GUI.cell5Diameter1.get(),GUI.cell5Diameter2.get(),GUI.cell5Diameter3.get(),GUI.cell5Diameter4.get()]
        FinalInputs.diam6 = [GUI.cell6Diameter1.get(),GUI.cell6Diameter2.get(),GUI.cell6Diameter3.get(),GUI.cell6Diameter4.get()]
        FinalInputs.diam7 = [GUI.cell7Diameter1.get(),GUI.cell7Diameter2.get(),GUI.cell7Diameter3.get(),GUI.cell7Diameter4.get()]
        FinalInputs.diam8 = [GUI.cell8Diameter1.get(),GUI.cell8Diameter2.get(),GUI.cell8Diameter3.get(),GUI.cell8Diameter4.get()]
        FinalInputs.diam9 = [GUI.cell9Diameter1.get(),GUI.cell9Diameter2.get(),GUI.cell9Diameter3.get(),GUI.cell9Diameter4.get()]

         # Labels for Excel
        FinalInputs.diam1.insert(0,"diameters_cell1(mm)")
        FinalInputs.diam2.insert(0,"diameters_cell2(mm)")
        FinalInputs.diam3.insert(0,"diameters_cell3(mm)")
        FinalInputs.diam4.insert(0,"diameters_cell4(mm)")
        FinalInputs.diam5.insert(0,"diameters_cell5(mm)")
        FinalInputs.diam6.insert(0,"diameters_cell6(mm)")
        FinalInputs.diam7.insert(0,"diameters_cell7(mm)")
        FinalInputs.diam8.insert(0,"diameters_cell8(mm)")
        FinalInputs.diam9.insert(0,"diameters_cell9(mm)")
        FinalInputs.mass1.insert(0,"mass_cell1(kg)")
        FinalInputs.mass2.insert(0,"mass_cell2(kg)")
        FinalInputs.mass3.insert(0,"mass_cell3(kg)")
        FinalInputs.mass4.insert(0,"mass_cell4(kg)")
        FinalInputs.mass5.insert(0,"mass_cell5(kg)")
        FinalInputs.mass6.insert(0,"mass_cell6(kg)")
        FinalInputs.mass7.insert(0,"mass_cell7(kg)")
        FinalInputs.mass8.insert(0,"mass_cell8(kg)")
        FinalInputs.mass9.insert(0,"mass_cell9(kg)")
        FinalInputs.count1.insert(0,"count_cell1")
        FinalInputs.count2.insert(0,"count_cell2")
        FinalInputs.count3.insert(0,"count_cell3")
        FinalInputs.count4.insert(0,"count_cell4")
        FinalInputs.count5.insert(0,"count_cell5")
        FinalInputs.count6.insert(0,"count_cell6")
        FinalInputs.count7.insert(0,"count_cell7")
        FinalInputs.count8.insert(0,"count_cell8")
        FinalInputs.count9.insert(0,"count_cell9")
        
        if overwriteGuardPage(filename_postTest_csv) == True: # filename already exists, needs to be renamed
            renamePage(GUI.filename_postTest.get()) # prompt user to rename file
        ''' write CSV'''

        GUI.data_postTest = [FinalInputs.diam1,FinalInputs.diam2,FinalInputs.diam3,FinalInputs.diam4,FinalInputs.diam5,FinalInputs.diam6,FinalInputs.diam7,FinalInputs.diam8,FinalInputs.diam9,FinalInputs.mass1,FinalInputs.mass2,FinalInputs.mass3,FinalInputs.mass4,FinalInputs.mass5,FinalInputs.mass6,FinalInputs.mass7,FinalInputs.mass8,FinalInputs.mass9,FinalInputs.count1,FinalInputs.count2,FinalInputs.count3,FinalInputs.count4,FinalInputs.count5,FinalInputs.count6,FinalInputs.count7,FinalInputs.count8,FinalInputs.count9]
        columns_data_postTest = zip_longest(*GUI.data_postTest)

        with open(filename_postTest_csv,'w',newline='') as f:
            writer = csv.writer(f)
            writer.writerows(columns_data_postTest)
        ''' end: write CSV '''
        print("filename_postTest_csv = "+filename_postTest_csv)
        
    def saveEIs():
        GUI.EI_fullcontact.insert(0 , "EI_fullcontact(N*cm^2)")
        GUI.EI_intermediatecontact.insert(0 , "EI_intermediatecontact(N*cm^2)")
        GUI.EI_nocontact.insert(0 , "EI_nocontact(N*cm^2")
        GUI.AvgEI_intermediatecontact.insert(0 , "AvgEI_intermediatecontact(N*cm^2)")
        ''' write CSV'''
        filename_EI_csv = GUI.address + '/' + GUI.filename_force.get() + '_EI.csv'
        GUI.data_EI = [GUI.EI_fullcontact,GUI.EI_intermediatecontact,GUI.EI_nocontact,GUI.AvgEI_intermediatecontact]
        columns_data_EI = zip_longest(*GUI.data_EI)
        with open(filename_EI_csv,'w',newline='') as f:
            writer = csv.writer(f)
            writer.writerows(columns_data_EI)
        ''' end: write CSV '''
        print("filename_EI_csv = "+filename_EI_csv)
        #print("saved:", filename_EI_csv)
        
    def compileNineCellData(self):
        createBackupFile()

        #try:       
        #if len(GUI.peaks_force) == 9:            
        #GUI.peaks_force[0],GUI.peaks_force[1],GUI.peaks_force[2],GUI.peaks_force[3],GUI.peaks_force[4],GUI.peaks_force[5],GUI.peaks_force[6],GUI.peaks_force[7],GUI.peaks_force[8] = GUI.peak_force_cell1, GUI.peak_force_cell2, GUI.peak_force_cell3, GUI.peak_force_cell4, GUI.peak_force_cell5, GUI.peak_force_cell6, GUI.peak_force_cell7, GUI.peak_force_cell8, GUI.peak_force_cell9
        #GUI.peaks_distance[0],GUI.peaks_distance[1],GUI.peaks_distance[2],GUI.peaks_distance[3],GUI.peaks_distance[4],GUI.peaks_distance[5],GUI.peaks_distance[6],GUI.peaks_distance[7],GUI.peaks_distance[8] = GUI.peak_distance_cell1, GUI.peak_distance_cell2, GUI.peak_distance_cell3, GUI.peak_distance_cell4, GUI.peak_distance_cell5, GUI.peak_distance_cell6, GUI.peak_distance_cell7, GUI.peak_distance_cell8, GUI.peak_distance_cell9
        #GUI.peaks_time[0],GUI.peaks_time[1],GUI.peaks_time[2],GUI.peaks_time[3],GUI.peaks_time[4],GUI.peaks_time[5],GUI.peaks_time[6],GUI.peaks_time[7],GUI.peaks_time[8] = GUI.peak_time_cell1, GUI.peak_time_cell2, GUI.peak_time_cell3, GUI.peak_time_cell4, GUI.peak_time_cell5, GUI.peak_time_cell6, GUI.peak_time_cell7, GUI.peak_time_cell8, GUI.peak_time_cell9
        GUI.peaks_force = [GUI.peak_force_cell1, GUI.peak_force_cell2, GUI.peak_force_cell3, GUI.peak_force_cell4, GUI.peak_force_cell5, GUI.peak_force_cell6, GUI.peak_force_cell7, GUI.peak_force_cell8, GUI.peak_force_cell9]
        GUI.peaks_distance = [GUI.peak_distance_cell1, GUI.peak_distance_cell2, GUI.peak_distance_cell3, GUI.peak_distance_cell4, GUI.peak_distance_cell5, GUI.peak_distance_cell6, GUI.peak_distance_cell7, GUI.peak_distance_cell8, GUI.peak_distance_cell9]
        GUI.peaks_time = [GUI.peak_time_cell1, GUI.peak_time_cell2, GUI.peak_time_cell3, GUI.peak_time_cell4, GUI.peak_time_cell5, GUI.peak_time_cell6, GUI.peak_time_cell7, GUI.peak_time_cell8, GUI.peak_time_cell9] 
        GUI.stemcounts=[GUI.cell1Count.get(),GUI.cell2Count.get(),GUI.cell3Count.get(),GUI.cell4Count.get(),GUI.cell5Count.get(),GUI.cell6Count.get(),GUI.cell7Count.get(),GUI.cell8Count.get(),GUI.cell9Count.get()]
        
        GUI.stemspacing_average, GUI.EI_fullcontact, GUI.EI_nocontact, GUI.EI_intermediatecontact = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0],[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0],[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0],[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
        print("GUI.stemcounts = ",GUI.stemcounts)
        for i in range(0,9):
            GUI.stemspacing_average[i], GUI.EI_fullcontact[i], GUI.EI_nocontact[i], GUI.EI_intermediatecontact[i] = FinalInputs.calculateEI(GUI.peaks_force[i], GUI.stemheight.get(), GUI.barbottom.get(), GUI.stemcounts[i])
        GUI.AvgEI_intermediatecontact = [0.0]
        GUI.AvgEI_intermediatecontact[0] = round(sum(GUI.EI_intermediatecontact)/len(GUI.EI_intermediatecontact),3)
        FinalInputs.saveEIs()
        FinalInputs.saveCompiled()
        time.sleep(1) # pause x seconds
        GUI.refreshAll() # refresh all variables 
        #except:
        #else:
        #    print("The nine cell scheme requires exactly 9 clips, 3 from each side hit.")
        
        
    
    def calculateEI(peak_force, stemheight, barbottom, stemcount):
        try:
            stemspacing_average = 1/(stemcount/barlength)
            EI_fullcontact = EI_Interaction_Fx.EI_Interaction(peak_force, stemheight, barbottom,stemspacing_average) # uses clicked forces (Y axis), force bar height, horizontal plot heights, and count density
            EI_nocontact = EI_No_Interaction_Fx.EI_NoInteraction(peaks[i], stemheight, barbottom, stemspacing_average) # the x value of the click does nothing other than find the nearest height from horz. It is not factored in to the number of beams or the character of the beams. 
            EI_intermediatecontact = (EI_fullcontact + EI_nocontact)/2
            EI_Interaction_Fx.clearAll()
            EI_No_Interaction_Fx.clearAll()
        except:
            stemspacing_average = 0 # if count is zero
            EI_fullcontact = 0 
            EI_nocontact = 0 
            EI_intermediatecontact = 0
            
        return stemspacing_average, EI_fullcontact, EI_nocontact, EI_intermediatecontact;
    
    def saveCompiled():
        #print("Compiled Data button does not currently work. Please develop.")
        # ned to change the way I handle filename_force : we need a base name, that is variety and plot
        # same for the peakcliclk setion.
        ''' write XSLX'''
        filename_compiled_xlsx = GUI.address + '/' + GUI.filename_force.get() + '_compiled.xlsx'
        
        filename_preTest_csv = GUI.address + '/' + GUI.filename_preTest.get() + '.csv'
        filename_forceSide1_csv = GUI.address + '/' + (GUI.filename_force.get()) + '_side1.csv'
        filename_forceSide2_csv = GUI.address + '/' + (GUI.filename_force.get()) + '_side2.csv'
        filename_forceSide3_csv = GUI.address + '/' + (GUI.filename_force.get()) + '_side3.csv'
        filename_forceForward_csv = GUI.address + '/' + (GUI.filename_force.get()) + '_forward.csv'
        filename_EIside1_csv = GUI.address + '/' + GUI.filename_force.get() + 'side1_EI.csv'
        filename_EIside2_csv = GUI.address + '/' + GUI.filename_force.get() + 'side2_EI.csv'
        filename_EIside3_csv = GUI.address + '/' + GUI.filename_force.get() + 'side3_EI.csv'
        filename_EIforward_csv = GUI.address + '/' + GUI.filename_force.get() + 'forward_EI.csv'
        filename_postTest_csv = GUI.address + '/' + (GUI.filename_postTest.get()) + '.csv'
        
        filenames_CSV = [filename_preTest_csv,filename_forceSide1_csv,filename_forceSide2_csv,filename_forceSide3_csv,filename_forceForward_csv,filename_EIside1_csv,filename_EIside2_csv,filename_EIside3_csv,filename_EIforward_csv,filename_postTest_csv]
        sheetnames_XLSX = ['preTest','force_side1','force_side2','force_side3','force_forward','EI_side1','EI_side2','EI_side3','EI_forward','postTest']

        ''' test names, sans arduino'''
        filenames_CSV = [filename_preTest_csv,filename_postTest_csv]
        sheetnames_XLSX = ['preTest','postTest']
        
        try:
            writer = pd.ExcelWriter(filename_compiled_xlsx, engine='xlsxwriter')
            i=0 
            for csvfilename in filenames_CSV:
                df = pd.read_csv(csvfilename)
                df.to_excel(writer,sheet_name=sheetnames_XLSX[i])
                i+=1
            writer.save()
            print("filename_compiled_xlsx = "+filename_compiled_xlsx)
        except:
            print("Complete all required files before attempting to compile.")
                           
    def on_show_frame_FinalInputs(self, event):
        #print("Flip to FinalInputs screen.")
        background_box = Label(self, text="This is hidden text meant to cover up old text.", font = ("arial", 14, "bold"), fg = "ghost white", bg="ghost white")
        background_box.place(x=0,y=0)
        # Update stringname of postTest file, based on filename_force, if it exists. 
        filename_postTest = nameBlackBox("postTest",GUI.filename_postTest.get())
        GUI.filename_postTest.set(filename_postTest)

        filename_label = Label(self, text="Filename:"+filename_postTest, font = ("arial", 14, "bold"), fg = "dodgerblue3", bg="ghost white")    
        filename_label.place(x=0,y=0)

''' Figure Interation classes '''

class SnaptoCursor(object):
    '''
    Cursor crossshair snaps to nearest x, y point.
    '''
    def __init__(self, ax, x, y):
        self.ax = ax
        #self.lx = ax.axhline(color='gold') # horizontal line
        self.ly = ax.axvline(color='orange', linewidth=1, linestyle="--") # vertical line
        self.x = x
        self.y = y
        # text location in axes coords
        self.txt = ax.text(0.7, 0.9, '', transform=ax.transAxes)

    def mouse_move(self, event):
        if not event.inaxes:
            return

        x, y = event.xdata, event.ydata
        indx = min(np.searchsorted(self.x, x), len(self.x)-1)
        x = self.x[indx]
        y = self.y[indx]
        # update the line positions
        #self.lx.set_ydata(y) # why is this commented out
        self.ly.set_xdata(x)

        self.txt.set_text('x=%1.2f, y=%1.2f' % (x, y))
        #print('x=%1.2f, y=%1.2f' % (x, y))
        self.ax.figure.canvas.draw()

class Cursor(object):
    '''
    Cursor crosshair that follows mouse
    '''

    def __init__(self, ax):
        self.ax = ax
        self.lx = ax.axhline(color='orange', linewidth=1, linestyle="--")
        self.ly = ax.axvline(color='orange', linewidth=1, linestyle="--")
        #text location in axes coords
        self.txt = ax.text(0.7, 0.9, '',transform=ax.transAxes)

    def mouse_move(self, event):
        if not event.inaxes:
            return
        x, y = event.xdata, event.ydata
        #update line positions
        self.lx.set_ydata(y)
        self.ly.set_xdata(x)

        self.txt.set_text('x=%1.2f, y=%1.2f' % (x, y))
        self.ax.figure.canvas.draw()

''' Peak click plotter methods'''
def initialPlot(distanceTraveled, forcePushed, timeElapsed, encoderWorked, varietyAndPlotnameAndDetail, documentationFolder,averageVelocity):
    fig, ax = plt.subplots()

    ''' vertical lines, for suggesting edge effect regions for forward tests '''
    if encoderWorked == True:  
        start = 50 # cm , cut off 1st 50cm = 20" usually #
        end = 305 # cm, cut off after 120 inches = 305 cm usually
    else:
        startDis = 50 # cut off 1st 50cm = 20" usually
        try:
            speed = averageVelocity # assume cm/ms . would need encode to work.....
            start = startDis/speed # CB edit # 20/speed # find t where SOCEM ~ 20" into plot
        except:
            speed = 50 # assume 50 cm/s
            start = startDis/speed # CB edit # 20/speed # find t where SOCEM ~ 20" into plot
        endDis = 305 # cut of after 120" usually
        end = endDis/speed # CB edit # time[-1] - (20/speed) # find t where SOCME ~ 20" before end of plot
        
        disReferenced_input = str(input('Would you like to type in known distance points (y/n)? '))
        if disReferenced_input == 'y':
            disReferenced_PeakClick = True
        elif disReferenced_input == 'n':
            disReferenced_PeakClick = False
        else: # just in case
            disReferenced_PeakClick = False
            
        if disReferenced_PeakClick == True:
            startDisRef = (int(input('Start point x (in): ')))
            endDisRef = (int(input('End point x (in): ')))
              
        ''' '''
    maxPt = max(forcePushed)
    # draw cut off lines
    cutStart = [start, start]
    cutEnd = [end, end]
    cutLine = [0, maxPt]
    ax.plot(cutStart,cutLine, color = 'red') # start cut off line
    ax.plot(cutEnd, cutLine, color = 'red') # end cut off line
    
    
    # plot dis vs forcePushed    
    if encoderWorked == True:
        ax.plot(distanceTraveled, forcePushed, color='midnightblue')
        ax.set_xlabel('Distance (cm)')
        snap_cursor = SnaptoCursor(ax, distanceTraveled, forcePushed) # create snap cursor object
    # plot time vs forcePushed
    else:
        ax.plot(timeElapsed, forcePushed, color='midnightblue')
        ax.set_xlabel('Time (ms)')
        snap_cursor = SnaptoCursor(ax, timeElapsed, forcePushed) # create snap cursor object
        
    title3 = '\n*click outside plot if red lines good*'
    fig.suptitle(GUI.filename_force.get() + '\nCut off edges: click start x pt, then end x pt.' + title3)
    #ax.set_title('*click outside plot if red lines good*')
    ax.set_ylabel('Force (N)')
    
    snap = fig.canvas.mpl_connect('motion_notify_event', snap_cursor.mouse_move) # update snap cursor upon mouse movement

    xCut = [] # stores where to cut off ends of plot (eliminate edge effects)
    def click(event): # get x coord once mouse is pressed
        x = event.xdata
        if x is None:
            print('red lines')
            xCut.append((start))
            xCut.append((end))
        else:
            print('x clicked = %1.2f' % x)
            xCut.append((x))
          #  self.fig.canvas.mpl_disconnect(cid)
        if len(xCut) >= 2:
            fig.canvas.mpl_disconnect(cid)
            fig.canvas.mpl_disconnect(snap)
            fig.canvas.set_window_title('InitialPlot')
            if encoderWorked == True:
                savename = GUI.filename_force.get() + '_' + str(round(xCut[0],1)) + '-' + str(round(xCut[1],1)) + '_raw.PNG'
            elif encoderWorked == False and disReferenced_PeakClick == True:
                savename = GUI.filename_force.get() + '_' + str(round(xCut[0],1)) + '-' + str(round(xCut[1],1)) + '_disref' + '_raw.PNG'
            elif encoderWorked == False and disReferenced_PeakClick == False:
                savename = GUI.filename_force.get() + '_' + str(round(xCut[0],1)) + '-' + str(round(xCut[1],1)) + '_timebased' + '_raw.PNG'
            else:
                savename = GUI.filename_force.get() + '_' + str(round(xCut[0],1)) + '-' + str(round(xCut[1],1)) + '_else' + '_raw.PNG'
            ax.plot([xCut[0],xCut[0]],cutLine, color = 'orange', linewidth=1, linestyle="--") # start cut off line
            ax.plot([xCut[1],xCut[1]], cutLine, color = 'orange', linewidth=1, linestyle="--") # end cut off line
            #print("Initial plot show...")
            #plt.show()
            #print("Initial plot shown.")
            if not os.path.exists(documentationFolder):
              os.makedirs(documentationFolder) # Create documentationFolder because it does not exist
            print("did")
            plt.savefig(documentationFolder + '\\' + savename)
            print("did2")
            plt.close(block)
            print("xCut = ",xCut)
        return xCut # return start & end x (dis. or time) pts
    
    cid = fig.canvas.mpl_connect('button_press_event', click) # connects click event
    print("cid")

    #clicked = snap_cursor.click()
    #print('clicked', snap_cursor.click.coords)
    plt.draw()
    plt.ion()
    plt.show() # never getting past this
    #plt.show(block=False) # never getting past this
    print("did4")
    print("encoderWorked = ",encoderWorked)
    print("disReferenced_PeakClick = ",disReferenced)
    if encoderWorked == True:
        return xCut
    elif encoderWorked == False and disReferenced_PeakClick == True:
        return xCut, disReferenced, disNew, i, j
    elif disReferenced_PeakClick == False:
        disNew = []
        return xCut, disReferenced, disNew, i, j
    print("Complete initial plot.")
    print("xCut, disReferenced, disNew,i,j = ", xCut, disReferenced, disNew,i,j)


###############################################################################

def choosePeaks(xData, forcePushed, xCut, varietyAndPlotnameAndDetail, encoderWorked, disReferenced, documentationFolder):
    #please: EMBED THE MATPLOTLIB PLOT INTO A TKINTER WINDOW< WHICH CAB BE A POPUP< LEADING TO POPUP.MAINLOOP()
    def nearest_pt(pt): # get nearest dis index to starting pt in disCut
        idx = (np.abs(np.asarray(xData)- pt)).argmin()
        #print('idx ', idx)
        return idx
    peakclick.peaks_force = [] # force peaks
    peakclick.peaks_xaxis = [] # x (distance) pt of force peak
    
    startIdx = nearest_pt(xCut[0]) # starting index
    print('startIdx = ',startIdx) # , dis[startIdx])
    endIdx = nearest_pt(xCut[1])
    print('Closest distance pts: ', [xData[startIdx] , xData[endIdx]]) 
    xCenter = xData[startIdx:endIdx]
    fCenter = forcePushed[startIdx:endIdx]
    
    fig, ax = plt.subplots()
    fig.canvas.set_window_title('ChoosePeaks')
    fig.suptitle(GUI.filename_force.get() + '\nSelect Force Peaks, *click outside when done*')
    #fig.suptitle(GUI.filename_force.get() + '\nCut off edges: click start x pt, then end x pt.' + title3)
    #ax.set_title('*click outside when done*')
    ax.plot(xCenter, fCenter) # needed?
    maxPt = max(forcePushed)
    ax.set_xlim(min(xCenter)-5, max(xCenter)+5)
    ax.set_ylabel('Force/row (lbs.)')
    if encoderWorked == True or disReferenced_PeakClick == True:
        ax.set_xlabel('Distance (in.)')
    else:
        ax.set_xlabel('Time (ms)')
            
    cursor = Cursor(ax) # create snap cursor object
    cursorMove = fig.canvas.mpl_connect('motion_notify_event', cursor.mouse_move) # update snap cursor upon mouse movement
    
    closeplt = False
    def click(event): # get x coord once mouse is pressed
        y, x = event.ydata, event.xdata
        if y is None and len(peakclick.peaks_force)>2:
            cursorMove = fig.canvas.mpl_connect('motion_notify_event', cursor.mouse_move) # update snap cursor upon mouse movement
            fig.canvas.mpl_disconnect(cid)
            fig.canvas.mpl_disconnect(cursorMove)
            # auto save file
            # example: CF452_24hr_4_23-156_disref_clicks.PNG
            if encoderWorked == True:
                savename = GUI.filename_force.get() + '_' + str(round(xCut[0],1)) + '-' + str(round(xCut[1],1)) + '_clicks.PNG'
            elif encoderWorked == False and disReferenced_PeakClick == True:
                savename = GUI.filename_force.get() + '_' + str(round(xCut[0],1)) + '-' + str(round(xCut[1],1)) + '_disref' + '_clicks.PNG'
            elif encoderWorked == False and disReferenced_PeakClick == False:
                savename = GUI.filename_force.get() + '_' + str(round(xCut[0],1)) + '-' + str(round(xCut[1],1)) + '_timebased' + '_clicks.PNG'
            plt.savefig(documentationFolder + '\\' + savename)
            print("choosePeaks: ",savename)

            print('peaks_xaxis = ', peakclick.peaks_xaxis)

            # lists of numbers, from analysis choice
            xCutL = ['xCut(in)'] # Distance, analysis range
            tCutL = ['tCut(sec)']# Time, analysis range
            print("test")
            plt.close()

            if encoderWorked == True:
                peakclick.peaks_distance = peakclick.peaks_xaxis
                peakclick.peaks_time = peakclick.findmatchtime(forcePushed,distanceTraveled,timeElapsed,peaks_distance)
                print("peaks_force =",peakclick.peaks_force) 
            elif encoderWorked == False and disReferenced_PeakClick == True:
                peakclick.peaks_distance = peakclick.peaks_xaxis
                peakclick.peaks_time = peakclick.findmatchtime(forcePushed,distanceTraveled,timeElapsed,peaks_distance)
                print("peaks_force =",peakclick.peaks_force)
            else: #elif encoderWorked == False and disReferenced_PeakClick == False: # possible issue dave
                peakclick.peaks_time = peakclick.peaks_xaxis
                peakclick.peaks_distance = [0, 0, 0] # might error, if there are not three clicks
                print("peaks_force =",peakclick.peaks_force)
                
            peakclick.saveCSV(GUI.filename_force.get(),GUI.address)
            RecordForce.closedplt = True
        else:
            # print('Force clicked = %1.2f at %1.2f' % (y, x)) # hide, CB
            peakclick.peaks_force.append((y))
            peakclick.peaks_xaxis.append((x))
            '''
            peaks_force.append((y))
            peaks_xaxis.append((x))
            '''
            ax.scatter(x, y, color='red')
            cursorMove = fig.canvas.mpl_connect('motion_notify_event', cursor.mouse_move) # update snap cursor upon mouse movement
            fig.canvas.draw()
            
        if peakclick.peaks_force == []:
            quit()
            
        #return peaks_force # return start & end dis pts

    #plt.draw() # the magic ingredient
    plt.ion()
    #fig.canvas.draw()
    cid = fig.canvas.mpl_connect('button_press_event', click) # connects click event
    #fig.canvas.draw()
    #plt.show(block=False)
    plt.show()
        
# MAIN
class peakclick:
    '''
    - Finish autoclicker by setting plt.show() into an inset tkinter gui popup, and then mainloop.
         Use: FigureCanvasTkAgg,NavigationToolbar2Tk,plt,Cursor.
    '''
    def __init__():
        peakclick.peaks_force = []
        peakclick.peaks_distance = []
        peakclick.peaks_time = []
    
    def findmatchtime(forcePushed,distanceTraveled,timeElapsed,peaks_distance):
        i=0
        for peaks_distance_i in peaks_distance:
            peaks_time = timeElapsed[distanceTraveled.find(peaks_axis_i)]
            i+=1
        return peaks_time
    
    # peaks_force,peaks_distance,peaks_time = peakclick.input(GUI.forcePushed,GUI.distanceTraveled,GUI.timeElapsed,GUI.filename_force.get(),GUI.address)
    def peakclick(forcePushed,distanceTraveled,timeElapsed,varietyAndPlotnameAndDetail,address,averageVelocity):
        #documentationFolder = GUI.address + '\\' + 'documentation'
        documentationFolder = GUI.address # for PNG and raw data to go to the same place.
        if max(distanceTraveled) > 10: # Assess if the encoder worked or not. Assuems that if it worked, the max value would exceeed 1 inch.
            encoderWorked = True # 
        else: encoderWorked = False

        print('Encoder? ', encoderWorked)
        print('max(distanceTraveled) = ', str(max(distanceTraveled)))
        print(GUI.filename_force.get())

        if useInitialPlot_PeackClick == True:
            if encoderWorked == False:
                xCut, disReferenced, disNew,i,j = initialPlot(distanceTraveled, forcePushed, timeElapsed, encoderWorked, GUI.filename_force.get(), documentationFolder,averageVelocity)
            elif encoderWorked == True:
                xCut = initialPlot(distanceTraveled, forcePushed, timeElapsed, encoderWorked,GUI.filename_force.get(), documentationFolder,averageVelocity)
                disReferenced_PeakClick = False
        else:
            xCut = [min(distanceTraveled),max(distanceTraveled)]
            tCut = [min(timeElapsed),max(timeElapsed)]
            disReferenced_PeakClick = False
            
        if encoderWorked == True:
            print('Distance cut at: ', xCut) # cut forcePushed and horz!!! 
            #peakclick.peaks_force,peakclick.peaks_xaxis = choosePeaks(distanceTraveled, forcePushed, xCut,GUI.filename_force.get(),encoderWorked, disReferenced_PeakClick,documentationFolder)
            choosePeaks(distanceTraveled, forcePushed, xCut,GUI.filename_force.get(),encoderWorked, disReferenced_PeakClick,documentationFolder) 
        elif encoderWorked == False and disReferenced_PeakClick == True:
            print('troubleshoot702')
            print('Distance cut at: ', xCut)
            #peakclick.peaks_force,peakclick.peaks_xaxis = choosePeaks(disNew, forcePushed, xCut,GUI.filename_force.get(),encoderWorked, disReferenced_PeakClick, documentationFolder)
            choosePeaks(disNew, forcePushed, xCut,GUI.filename_force.get(),encoderWorked, disReferenced_PeakClick, documentationFolder)
        else: #elif encoderWorked == False and disReferenced_PeakClick == False: # possible issue dave
            xCut=tCut
            print('Time cut at: ', xCut)
            #peakclick.peaks_force,peakclick.peaks_xaxis = choosePeaks(timeElapsed, forcePushed, xCut,GUI.filename_force.get(),encoderWorked, disReferenced_PeakClick, documentationFolder)
            choosePeaks(timeElapsed, forcePushed, xCut,GUI.filename_force.get(),encoderWorked, disReferenced_PeakClick, documentationFolder)

        #peakclick.saveCSV(GUI.filename_force.get(),GUI.address)
        #return peakclick.peaks_force,peakclick.peaks_distance,peakclick.peaks_time

    def saveCSV(varietyAndPlotnameAndDetail,address):
        #print("not yet saved. develop.")
        filename_peaks_csv = GUI.address + "/" + GUI.filename_force.get() + "_peaks.csv"
        ''' write CSV'''
        GUI.data_peaks = [peakclick.peaks_force,peakclick.peaks_distance,peakclick.peaks_time]
        RecordForce.peaks_force = peakclick.peaks_force
        RecordForce.peaks_distance = peakclick.peaks_distance
        RecordForce.peaks_time = peakclick.peaks_time
        RecordForce.peaks_distance.insert(0, "PeaksDistance(cm)")
        RecordForce.peaks_force.insert(0, "PeaksForce(N)")
        RecordForce.peaks_time.insert(0 , "PeaksTime(ms)")
        columns_data_peaks = zip_longest(*GUI.data_peaks)
        with open(filename_peaks_csv,'w',newline='') as f:
            writer = csv.writer(f)
            writer.writerows(columns_data_peaks)
        ''' end: write CSV '''
        print("filename_peaks_csv = "+filename_peaks_csv)
        
class EI_Interaction_Fx:
    '''
    Closed-form solution for calculating EI via the Multiple Inline Interacting Cantilever Beam Model
    Author: Austin Bebee
    Last updated: 7/6/2020
    Require input values for peak force (f), force bar height (h), beam length (l), beam-to-beam spacing (s).
    Assumes the system contains the full/max number of beams (full interaction) at the first beam's max deflection.
    If this is not the case, set the variable "finite_beam_num" to True and set the variable "beam-num" to the number
    of beams in a row.
    Additional assumptions:
        - beams deflect linearly inline
        - force bar force always perpendicular to 1st beam's end angle
        - each beam has same K & KO
    '''
    # INPUT PARAMETERS. EI will be calculated in units of f*(l^2)
    # example
    #f = 5  # peak force
    #h = 8  # force bar height
    #l = 10  # beam length
    #s = 1  # beam-to-beam spacing
    definite_beam_num = False  # if False, assumes max number of beams (full interaction) at the first beam's max deflection
    beams = 8  # num. of beams in a row (only used if "definite_beam_num" set to True)

    # Model lists/arrays - each index is a beam's attribute (0 index = 1st beam, last index = last beam)
    theta = list()  # PRBM angle (radians)
    beta = list()  # math.pi/2 - theta (radians)
    x = list()  # x deflection
    d = list()  # horizontal distance a beam extends past the next (x - s)
    phi = list()  # force vector angle w/ respect to undeflected axis (vertical axis in this case)
    forces = list()  # individual reaction forces
    q = list()  # effective beam lengths
    KO = list()  # stiffness coefficient
    gl = list()  # gamma*l (longer rigid link length)

    def clearAll(): # Clears variables for new simulation
        beta.clear()
        x.clear()
        d.clear()
        phi.clear()
        forces.clear()
        q.clear()
        KO.clear()
        gl.clear()

    def MultiPhiCor(h, l, s, phi): # Phi correctoin for multiple beams (exp. developed) used when h/l < 0.7
        if h/l < 0.7:
            mphi = 244.7802*(s/l) - 683.4973*((s/l)**2) - 165.1557*((s/l)*(h/l)) + 43.4227*((h/l)**2)
            mphi = mphi * ((math.pi) / 180)
        else:
            mphi = phi

        return mphi

    def Parametric_angle_coefficient(n): # returns c (parametric angle coefficient) when given n
        if -4 < n <= -1.5:
            c = 1.238945 + 0.012035*n + 0.00454*(n**2)
        elif -0.5 < n: # <= 10: # some conditions yield n = 10.25, which is just beyond the defined limits of n. Can either remove n <= 10 boundary or set n = 10 if n > 10.
            c = 1.238845 + 0.009113*n - 0.001929*(n**2) + 0.000191*(n**3) - 0.000007*(n**4)
        return c

    def gammaUpdate(n):# returns gamma value when give n
        if n > .5: # <= 10: # some conditions yield n = 10.25, which is just beyond the defined limits of n. Can either remove n <= 10 boundary or set n = 10 if n > 10.
            gamma = .841655 - 0.0067807 * n + .000438 * (n ** 2)
        elif n > -1.8316 and n < 0.5:
            gamma = .852144 - 0.0182867 * n
        elif n > -5 and n < -1.8316:
            gamma = .912364 + .0145928 * n

        return gamma

    def KOupdate(n):# returns Ko (stiffness coefficient) when given n
        if n > -5 and n <= -2.5:
            Ko = (3.024112 + 0.121290 * n + 0.003169 * (n ** 2))
        elif n > -2.5 and n <= -1:
            Ko = (1.967647 - 2.616021 * n - 3.738166 * (n ** 2) - 2.649437 * (n ** 3) - 0.891906 * (n ** 4) - 0.113063 * (n ** 5))
        elif n > -1: # and n <= 10: # <= 10: # some conditions yield n = 10.25, which is just beyond the defined limits of n. Can either remove n <= 10 boundary or set n = 10 if n > 10.
            Ko = (2.654855 - 0.509896 * (10 ** -1) * n + 0.126749 * (10 ** -1) * (n ** 2) - 0.142039 * (10 ** -2) * (n ** 3) + 0.584525 * (10 ** -4) * (n ** 4))

        return Ko

    # MAIN FUNCTION THAT RETURNS THE SYSTEM'S MEAN EI
    def EI_Interaction(f, h, l, s):

        ## DETERMINE 1ST BEAM'S KINEMATICS ##

        #initial assumption that force bar applies a horizontal force yields:
        n = 0 # initial n value
        gamma = gammaUpdate(n)  # initial gamma

        # Gamma Convergence Cycle - update gamma for better estimate
        j = 0
        while j < 100:  # gamma converges well before 100 iterations
            b = (1 - gamma) * l  # length below torsional spring (in.)
            betaV = (np.arcsin((h - b) / (gamma * l)))  # beta angle value (rads)
            thetaV = (math.pi / 2) - betaV  # PRBM theta value (rads)
            c = Parametric_angle_coefficient(n)  # get parametric angle coefficient
            beam_end_angle = thetaV * c  # corrected beam end angle
            phiV = (math.pi / 2) - beam_end_angle  # phi value (perpendicular to beam end angle)
            n = (1 / np.tan(phiV))  # update n
            #  Option below: if n > 10 (beyond PRBM defined limits) set n = 10 (note: negligible change if used)
            #if n > 10:
             #   n = 10
            gamma = gammaUpdate(n)  # update gamma
            j += 1
        
        b1 = b # stores final b of 1st beam
        gamma1 = gamma  # stores final gamma of 1st beam

        # 1st beam's geometry & attributes:
        q.insert(0, l)  # effective beam length
        gl.insert(0, gamma * l)  # stores longer rigid link length
        Ko = KOupdate(n)  # update Ko (stiffness coefficient)
        KO.insert(0, Ko)  # stores 1st beam's stiffness coefficient
        beta.insert(0, betaV)  # stores beta angle
        x.insert(0, gl[0] * np.cos(beta[0]))  # stores x deflection
        d.insert(0, x[0] - s)  # stores horizontal distance beam extends past the next

        phiCorrection = MultiPhiCor(h, l, s, phiV) # correct phi (if h/l < 0.7)
        phi.insert(0, phiCorrection)  # force vector angle w/ respect to undeflected axis

        # ALL OTHER BEAM'S KINEMATICS
        def otherBeams(i): # called after determining # of beams
            beta.insert(i + 1, np.arctan((gl[i] * np.sin(beta[i])) / d[i]))
            phiV = (beta[i])  # initially assume phi = previous beta
            n = (1 / np.tan(phiV))  # determine n
            c = Parametric_angle_coefficient(n) # determine c
            phiV = (math.pi / 2) - (math.pi / 2 - beta[i]) * c # correct & update phi
            phiCorrection = MultiPhiCor(h, l, s, phiV) # correct phi (if h/l < 0.7)
            phi.insert(i + 1, phiCorrection) # store beam's phi
            Ko = KOupdate(n)  # update Ko
            KO.insert(i+1, Ko)  # store beam's Ko
            gamma = gammaUpdate(n)  # update gamma
            b = (1 - gamma) * l  # update base length
            q.insert(i + 1, b + math.sqrt(d[i] ** 2 + (gl[i] * np.sin(beta[i])) ** 2))  # effective cantilever beam length (base to applied force from previous beam or force bar)
            gl.append(gamma * l)  # store beam's gamma*length  
            x.insert(i + 1, gl[i + 1] * np.cos(beta[i + 1]))  # x deflection at end of beam
            #y.insert(i+1, gl[i+1] * np.sin(beta[i + 1])) # y deflection at end of beam (not needed for EI calculation)
            d.insert(i + 1, x[i + 1] - s)# stores horizontal distance beam extends past the next


            return d[i]  # returns distance to check to continue looping or not

        # Determine # of other beams:
        if definite_beam_num == False:  # full interaction @ 1st beam's max deflection
            i = 0
            while d[i] > 0:  # will previous beam hit next beam? If so, run that beam through otherBeams()
                otherBeams(i)
                i += 1
        else:  # definite number of beams in a row (may not be full/max interaction possible)
            i = 0
            while d[i] > 0 and i < beams-1:  # will previous beam hit next beam & does that beam exist? If so, run that beam through otherBeams()
                otherBeams(i)
                i += 1

        # BACKSOLVE TO GET ALL FORCES/K EXCEPT 1ST FORCE/K

        # Last beam force/k
        if len(beta) > 1:  # check if more than 1 beam
            num = ((math.pi / 2) - beta[-1])  # numerator = theta
            den = ((x[-2] - s) * np.cos(phi[-1]) + (gl[-2] * np.sin(beta[-2]) * np.sin(phi[-1])))  # denominator
            forces.insert(-1, num / den)  # last force/k
        else:  # if only one beam, skip
            pass

        # middle beam forces/k
        j = -2
        if len(beta) > 1:  # check if more than 1 beam
            while j > -(len(beta)):  # loop until reaching 1st force/K
                num1 = ((math.pi / 2) - beta[j])  # 1st numerator term = theta
                num2 = forces[j + 1] * (gl[j] * np.sin(beta[j]) * np.sin(phi[j + 1]) + x[j] * np.cos(phi[j + 1]))  # force due to previous beam
                den1 = (x[j - 1] - s) * np.cos(phi[j])  # denominator term 1
                den2 = gl[j - 1] * np.sin(beta[j - 1]) * np.sin(phi[j])  # denominator term 2
                forces.insert(j, (num1 + num2) / (den1 + den2))  # forces/k

                j = j - 1  # increment backwards

        # 1st Beam calculations
        fx = f / np.sin(phi[0])
        forces.insert(0, fx)  # store force bar applied force in 0 index
        
        # calculate K (torsional spring constant) of 1st beam
        knum1 = fx * (x[0] * np.cos(phi[0]) + (h - b1) * np.sin(phi[0]))  # numerator
        kden1 = ((math.pi / 2) - beta[0])  # denominator 1st term

        if len(beta) > 1:  # if more than 1 beam (i.e., interacting beams)
            kden2 = forces[1] * ((h - b1) * np.sin(phi[1]) + x[0] * np.cos(phi[1])) # denominator 2nd term due to interactions
        else: # only 1 beam, no interactions
            kden2 = 0

        K = (knum1) / (kden1 + kden2)  # compute K (torsional spring constant)

        ## COMPUTE EI ##
        EI = (l * K) / (KO[0] * gamma1)

        #t_num = len(beta)  # total number of interacting beams @ 1st beam's deflection
        
        return EI

    def test(f, h, l, s):
        clearAll()
        EI = EI_Interaction(f, h, l, s)
        print(EI)
    #test(7, 5, 10, 1)
        
class EI_No_Interaction_Fx:
    '''
    No-Interaction Closed-form solution for calculating EI via the Multiple Inline Non-Interacting Cantilever Beam Model
    Author: Austin Bebee
    Last updated: 7/6/2020
    Require input values for peak force (f), force bar height (h), beam length (l), beam-to-beam spacing (s).
    Assumes the system contains the full/max number of beams at the first beam's max deflection.
    If this is not the case, set the variable "finite_beam_num" to True and set the variable "beam-num" to the number
    of beams in a row.
    Additional assumptions:
        - no contact between beams. Beams only contact the force bar
        - force bar force always perpendicular to 1st beam's end angle
        - each beam may have different K & KO
    '''
    # INPUT PARAMETERS (EI will be calculated in units of f*l^2)
    # f = 5 # peak force
    # h = 8 # force bar height
    # l = 10 # beam length
    # s = 1 # beam-to-beam spacing
    definite_beam_num = False # # if False, assumes max number of beams at the first beam's max deflection
    beams = 8 # num. of beams in a row (only used if "definite_beam_num" set to True)

    # Model lists/arrays - each index is a beam's attribute (0 index = 1st beam, last index = last beam)
    theta = list() # PRBM angle (rads)
    beta = list() # math.pi/2 - theta (rads)
    x = list() # x deflection
    d = list() # horizontal distance a beam extends past the next (x - s)
    phi = list() # 180 deg. - alpha
    q = list()# effective l term in following k's equation 
    KO = list() # stiffness coefficient
    gl = list() # gamma*l (longer rigid link length)
    dens = list() # denominator terms for EI

    def clearAll(): # clears variables for new simulation 
        beta.clear()
        theta.clear()
        x.clear()
        d.clear()
        phi.clear()
        q.clear()
        KO.clear()
        gl.clear()
        dens.clear()

    def Parametric_angle_coefficient(n): # returns c (parametric angle coefficient) when given n
        if -4 < n <= -1.5:
            c = 1.238945 + 0.012035*n + 0.00454*(n**2)
        elif -0.5 < n: # <= 10: # some conditions yield n = 10.25, which is just beyond the defined limits of n. Can either remove n <= 10 boundary or set n = 10 if n > 10.
            c = 1.238845 + 0.009113*n - 0.001929*(n**2) + 0.000191*(n**3) - 0.000007*(n**4)
        return c

    def gammaUpdate(n):# returns gamma value when give n
        if n > .5: # <= 10: # some conditions yield n = 10.25, which is just beyond the defined limits of n. Can either remove n <= 10 boundary or set n = 10 if n > 10.
            gamma = .841655 - 0.0067807 * n + .000438 * (n ** 2)
        elif n > -1.8316 and n < 0.5:
            gamma = .852144 - 0.0182867 * n
        elif n > -5 and n < -1.8316:
            gamma = .912364 + .0145928 * n

        return gamma

    def KOupdate(n):# returns Ko (stiffness coefficient) when given n
        if n > -5 and n <= -2.5:
            Ko = (3.024112 + 0.121290 * n + 0.003169 * (n ** 2))
        elif n > -2.5 and n <= -1:
            Ko = (1.967647 - 2.616021 * n - 3.738166 * (n ** 2) - 2.649437 * (n ** 3) - 0.891906 * (n ** 4) - 0.113063 * (n ** 5))
        elif n > -1: # and n <= 10: # <= 10: # some conditions yield n = 10.25, which is just beyond the defined limits of n. Can either remove n <= 10 boundary or set n = 10 if n > 10.
            Ko = (2.654855 - 0.509896 * (10 ** -1) * n + 0.126749 * (10 ** -1) * (n ** 2) - 0.142039 * (10 ** -2) * (n ** 3) + 0.584525 * (10 ** -4) * (n ** 4))

        return Ko

    # MAIN FUNCTION THAT RETURNS THE SYSTEM'S MEAN EI
    def EI_NoInteraction(f, h, l, s):

        ## DETERMINE 1ST BEAM'S KINEMATICS ##

        #initial assumption that force bar applies a horizontal force yields:
        n = 0 # initial n value
        gamma = gammaUpdate(n)  # initial gamma

        # Gamma Convergence Cycle - update gamma for better estimate
        j = 0

        while j < 100:  # gamma converges well before 100 iterations
            b = (1 - gamma) * l  # length below torsional spring (in.)
            betaV = (np.arcsin((h - b) / (gamma * l)))  # beta angle value (rads)
            thetaV = (math.pi / 2) - betaV  # PRBM theta value (rads)
            c = Parametric_angle_coefficient(n)  # get parametric angle coefficient
            beam_end_angle = thetaV * c  # corrected beam end angle
            phiV = (math.pi / 2) - beam_end_angle  # phi value (perpendicular to beam end angle)
            n = (1 / np.tan(phiV))  # update n
            #  Option below: if n > 10 (beyond PRBM defined limits) set n = 10 (note: negligible change if used)
            #if n > 10:
             #   n = 10
            gamma = gammaUpdate(n)  # update gamma
            j += 1

        b1 = b # stores final b of 1st beam
        gamma1 = gamma # stores final gamma of 1st beam
        
        # 1st beam's geometry & attributes:
        q.insert(0, l)  # effective beam length
        gl.insert(0, gamma1 * l)  # stores longer rigid link length
        Ko = KOupdate(n)  # update Ko (stiffness coefficient)
        KO.insert(0, Ko)  # stores 1st beam's stiffness coefficient
        beta.insert(0, betaV)  # stores beta angle
        x.insert(0, gl[0] * np.cos(beta[0]))  # stores x deflection
        d.insert(0, x[0] - s)  # stores horizontal distance beam extends past the next
        phi.insert(0, phiV)  # force vector angle w/ respect to undeflected axis

        # ALL OTHER BEAM'S KINEMATICS
        i = 0
        def otherBeams(i): # called after determining # of beams
            beta.insert(i+1, np.arctan((gl[0] * np.sin(beta[0])) / (d[i])))
            phiV = beta[i] # initialy assum phi = previous beta
            n = (1/np.tan(phiV)) # determine n
            c = Parametric_angle_coefficient(n) # get parametric angle coefficient 
            phiV = (math.pi / 2) - (math.pi / 2 - beta[i]) * c # correct & update phi
            phi.insert(i+1, phiV) # store beam's phi
            Ko = KOupdate(n) # update Ko
            KO.insert(i+1, Ko) # store Ko
            gamma = gammaUpdate(n) # update gamma
            gl.append(gamma * l) # store g*l
            b = ((1 - gamma) * l) # update base length
            x.insert(i+1, d[i]) # x distance from base of beam to force bar's positon @ 1st beam's max deflection
            d.insert(i+1, x[i+1] - s) # horizontal distance beam extends past the next
            q.insert(i+1, b + math.sqrt(x[i]**2 + (gl[0]*np.sin(beta[0]))**2)) # effective cantilever beam length (base to applied force)

            return i

        # Determine # of other beams:
        numBeams = int(round(x[0]/s)) # number of additional beams hitting force bar at 1st one's max deflection
        
        if definite_beam_num == False:  # full number of beams @ 1st beam's max deflection
            i = 0 
            while i <= (numBeams-2):  # will beam hit force bar? If so, run that beam through otherBeams()
            # numBeams - 2: -2 because 1st beam already computed, i starts at 0
                otherBeams(i)
                i += 1
        else:  # definite number of beams in a row (may expect more beams than the system actually has)
            i = 0
            while i <= (numBeams-2) and i < beams-1:  # will beam hit force bar & does that beam exist? If so, run that beam through otherBeams()
                otherBeams(i)
                i += 1
                
        # Calculations required to compute EI
        for i in range(len(beta)):
            theta.insert(i, ((math.pi/2)-beta[i])) # PRBM Theta
            #s.insert(i, deltaTheta[i]/(gamma*(q[i]**2)))                     
            dens.insert(i, (KO[i]*theta[i])/(q[i]**2)) # denominator terms for EI
        EIden = sum(dens) # denominator sum term for EI
        # Compute EI
        Ftot = f/np.sin(phi[0]) # estimate F total from Fx 
        EI = Ftot/EIden

        return EI
        
    def test(f, h, l, s):
        clearAll()
        EI = EI_NoInteraction(f, h, l, s)
        print(EI)

    #test(5, 8, 10, 1)

        
''' Main '''
print("StemBerry is loading.")
print("output: address = "+address)
print("script = "+script)
print("directory = "+directory)
print("ignoreserial = "+str(ignoreserial))
app = GUI() # INITIATES GUI TO START
app.title("StemBerry")
app.geometry("800x480+0+0")
app.aspect()
#app.geometry("700x700+0+0")
#fig = plt.figure()
#app.iconbitmap(s'/home/pi/Desktop/SOCEM Code')
#app.geometry("{0}x{1}+0+0".format(app.winfo_screenwidth()-3,app.winfo_screenheight()-3)) #full screen:
app.mainloop()
''' End '''
