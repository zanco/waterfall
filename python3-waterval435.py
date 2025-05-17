#!/usr/bin/python


from __future__ import division
import matplotlib
import matplotlib.style #Ben
import matplotlib as mpl #Ben
mpl.style.use('classic') #Ben
matplotlib.use('Agg')
from matplotlib import dates as mpl_dates
from matplotlib.ticker import AutoMinorLocator
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as pyl
import numpy as np
import sys
import time
import datetime as dt
from math import ceil
import ftplib
import os
import socket
import datetime
import thread
import csv
import StringIO



numWaterfallLines=960 #8 hours at 30s update scanInterval
gblScanInterval=30000 #update interval of waterfall in ms 30000
gblSaveInterval=30000 #save interval in ms 30000
gblUploadInterval=300000 #upload interval in ms 300000
gblLocalCopyInterval=14400000 # 4hrs
#gblFigSize = [21,12.42] #dimensions in inch
#gblFigSize = [42,24.84] #dimensions in inch
gblFigSize = [84,49.68] #dimensions in inch

gblDPI = 100
gblArchiveDir="images/"
gblLogFile="wasserfall.log"

Y_AXIS_LIMITS=[-40,0] #was -75
COLOR_SCALE_MIN=-56 #was -40 en te donker nu na reductie van de gain 
COLOR_SCALE_MAX=-20 #was 0

FTP_SERVER1="www.yourserver.nl"
FTP_DIR1="/"
FTP_USER1="skymonitor"
FTP_PASSWD1="Some Password"

FTP_SERVER2="www.pe2bz.nl"
FTP_DIR2="/public_html/hamradio/skymonitor"
FTP_USER2="your username"
FTP_PASSWD2="your password"

print matplotlib.rcParams['backend']

class Waterfall(object):
    #keyboard_buffer = []
    #shift_key_down = False
    localCopyCounter = 0
    saveCounter = 0
    uploadCounter = 0
    def __init__(self, start, step, numberOfBins, fig=None):
        self.fig = fig if fig else pyl.figure(figsize=gblFigSize)
        
        self.imageBuffer = -100*np.ones((numWaterfallLines, numberOfBins+1))
        self.init_plot(start, step, numberOfBins)

    def init_plot(self, start, step, numberOfBins):
        gs=gridspec.GridSpec(2,1, height_ratios=[1,4])
        gs.update(hspace=0.05,left=0.07,right=0.98,top=0.98,bottom=0.07)
        self.ax = self.fig.add_subplot(gs[0])#(2,1,1)
        self.imAx= self.fig.add_subplot(gs[1],sharex=self.ax)#(2,1,2)
        self.image = self.imAx.imshow(self.imageBuffer, aspect='auto',interpolation='bilinear', vmin=COLOR_SCALE_MIN, vmax=COLOR_SCALE_MAX)
        timeFormat = mpl_dates.DateFormatter('%d/%m %H:%M:%S')
        displayedSeconds=numWaterfallLines*gblScanInterval/1000
        if displayedSeconds <= 240: # 5 min
        	step=(displayedSeconds//7)
        	if step%15 > 7:
        		step = ((step//15)+1)
        	else: step = (step//15)
        	self.imAx.yaxis.set_major_locator(mpl_dates.SecondLocator(bysecond=[0,15,30,45],interval=1))
        else:
        	self.imAx.yaxis.set_major_locator(mpl_dates.MinuteLocator(byminute=[0,30])) 
        	self.imAx.yaxis.set_minor_locator(AutoMinorLocator(6))
        self.imAx.yaxis.set_major_formatter(timeFormat)
        self.imAx.tick_params(axis='x',which='minor',gridOn=True)
        #self.imAx.xaxis.grid(True,which='major',color='g')
        #self.imAx.yaxis.grid(True,which='major',color='g')
        stop = start + (numberOfBins) * step 
        x=[(start +x*step)/1e6 for x in range(0,numberOfBins+1)] 
        
        y=np.zeros(len(x))
        line=self.ax.plot(x,y,'b-',label='harr')

        self.plotLine=line[0]
        self.imAx.set_xlabel('Frequency (MHz)')
        self.ax.ticklabel_format(useOffset=False) #add by Ben
        self.ax.xaxis.tick_top()
        self.ax.minorticks_on()
        self.ax.tick_params(axis='y',which='minor',left='off',right='off')
        self.ax.tick_params(axis='x',which='minor',gridOn=True,labelcolor='r') #labelcolor add by Ben
        self.ax.tick_params(axis='x',which='both', bottom='on')

        self.ax.xaxis.set_minor_locator(AutoMinorLocator(20)) #was 10
        self.ax.set_ylabel('Level (a.u.)')
        self.ax.set_yticklabels([])
        self.ax.set_ylim(Y_AXIS_LIMITS)
        self.ax.xaxis.grid(True)

        
        self.ax.set_xlim(start/1e6,stop/1e6) 
        self.msg=self.ax.text(start/1e6+0.1,-5,"",bbox=dict(facecolor='whitesmoke',boxstyle='round')) #by Ben
        


    def update(self, scanLine):
        
        self.imageBuffer = np.roll(self.imageBuffer, 1, axis=0)
        self.imageBuffer[0,:]=scanLine
        lineBufferZ = scanLine
        self.image.set_array(self.imageBuffer)
        now = time.time()
        lineAdded=datetime.datetime.now()
        then = now-(numWaterfallLines-1)*gblScanInterval/1000
        now = dt.datetime.fromtimestamp(now)
        then = dt.datetime.fromtimestamp(then)
        now=mpl_dates.date2num(now)
        then=mpl_dates.date2num(then)
        self.image.set_extent([self.ax.get_xlim()[0],self.ax.get_xlim()[1],then,now])
        #self.plotLine.set_xdata(lineBufferX)
        self.plotLine.set_ydata(lineBufferZ)
        self.updateMessage()

        self.saveCounter += gblScanInterval
        self.localCopyCounter += gblScanInterval
        self.uploadCounter += gblScanInterval
        if self.saveCounter >= gblSaveInterval:
			self.fig.canvas.draw()
			self.saveCounter=0
			#timestamp=time.time()
			self.fig.savefig('waterfall_current.png')
        if self.uploadCounter >= gblUploadInterval:
			self.uploadCounter = 0
			self.fig.savefig('waterfall_upload.png',dpi=gblDPI)
			self.fig.savefig('waterfall_upload_lowres.png',dpi=gblDPI/5)
			thread.start_new_thread(upload,("waterfall_upload.png",FTP_SERVER1, FTP_USER1, FTP_PASSWD1,FTP_DIR1,"satband.png"))
			thread.start_new_thread(upload,("waterfall_upload.png",FTP_SERVER2, FTP_USER2, FTP_PASSWD2,FTP_DIR2,"rtlsat_power.png"))
        if self.localCopyCounter >= gblLocalCopyInterval:
        	self.localCopyCounter=0
        	timestamp = time.time()
        	self.fig.savefig(gblArchiveDir+str(datetime.datetime.now().strftime("1%Y-%m-%d_%H-%M-%S"))+'_waterfall.png',dpi=gblDPI)
        
        try:
        	file = open(gblLogFile,'a')
        	file.write(str(lineAdded.strftime("1%Y-%m-%d_%H-%M-%S"))+"\r\n")
        except Exception, e:
        	print str(e)
        finally:
        	if file is not None: file.close()
        return self.plotLine,

    
    def updateMessage(self):
		file=None
		try:
			file=open("msg.txt","r")
			text=file.read()
			self.msg.set_text(text)
		except Exception, e:
			print "Cannot open message file"
		finally:
			if file is not None:
				file.close()
				
def upload(localFile,ftpServer=FTP_SERVER2,ftpUser=FTP_USER2,ftpPasswd=FTP_PASSWD2, ftpDir=FTP_DIR2,ftpFileName=None):
	file = None
	session = None
	try:
		if ftpFileName==None:
			ftpFileName=os.path.basename(localFile)
		session = ftplib.FTP(ftpServer,ftpUser,ftpPasswd)
		session.cwd(ftpDir)
		file = open(localFile,'rb')                  # file to send
		sys.stdout.write("["+str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+"] Uploading " + str(localFile) +" to " + str(ftpServer) + " .... ")
		sys.stdout.flush()
		session.storbinary('STOR '+ ftpFileName, file)     # send the file
		session.quit()
		print "done"
	except Exception, e:
		print str(e)
	finally:
		if file is not None: file.close()                                # close file and FTP
		#if session is not None: session.quit()

def main():
    if len(sys.argv)!=5:
    	sys.exit()
    start = int(sys.argv[1])
    step = float(sys.argv[2])
    numberOfBins = int(sys.argv[3])
    numberOfHops = int(sys.argv[4])
    
    wf = Waterfall(start, step, numberOfBins)
    
    hopCounter=0
    spectrum =[]# np.zeros(numberOfBins)
    
    try:
    	while True:
        	line = sys.stdin.readline()
        	data = csv.reader(StringIO.StringIO(line.replace('-1.#J','NaN')))
        	specPart = []
        	for x in data:
        		specPart.extend(x)
        	if specPart:
        		hopCounter = hopCounter + 1
        		#nextIndex=hopCounter*len(specPart[6:len(specPart)-2])
        		#append to spectrum:
        		if hopCounter<numberOfHops:
        			spectrum.extend(specPart[6:len(specPart)-1])#[nextIndex:nextIndex+len(specPart[6:len(specPart)-2])-1]=(specPart[6:len(specPart)-2]) #skip the last sample as it is a duplicate of the beginning of the next hop
        		else:
        			spectrum.extend(specPart[6:len(specPart)])
                                spectrumNew = []
                                for i in spectrum:
                                        spectrumNew.append(float(i))
                                wf.update(spectrumNew)
        			spectrum=[] #clear the current line
        			hopCounter=0 #reset counter
        			
    except KeyboardInterrupt: 
    	sys.exit()

if __name__ == '__main__':
    main()
