# Name:       PartyLaps for Assetto Corsa
# Version:    v1.1
# Anthor:     Rob Haswell
# Contact:    me@robhaswell.co.uk
# Date:       01.05.2016
# Original:   Sylvlain Villet <sylvain.villet@gmail.com>
# Desc.:      This app provides a list of the last "N" laps
#             done, the current lap projection and performance
#             delta, and the total session time.
#             The deltas can be calculated from the best lap, the median
#             or the average time of the top 25, 50 or 75% laps.
#             The app can be fully configured from the PartyLaps_config widget.
#
# Thanks:     - Rombik for the sim_info module
#             - Rivali (OV1Info) and Fernando Deutsch (ferito-LiveCarTracker)
#             for the inspiration and example
#             - PanaRace970 for the Touristenfahrten workaround
unitTesting = False
try:
    import ac
    import acsys
except ImportError:
    # Hopefully in a test case
    unitTesting = True

import sys
import os
import configparser
import time
import platform

from ACTable import ACTable

# Parameters from config file
showHeader = 0
fontSize = 18
opacity = 50
showBorder = 1

lapDisplayedCount = 6
showDelta = 1
deltaColor = "white"
redAt = 500
greenAt = -500
showCurrent = 1
showReference = 1
reference = "median"
showTotal = 1

updateTime = 100
logLaps = 1
logBest = "always"
lockBest = 0

driversList = []
driversListText = ""
currentDriver = ""

# Objects
partyLapsApp = 0
config = 0
configApp = 0

# Display global settings
spacing = 5
topPadding = 30
fontSizeConfig = 18
lapLabelCount = 50

# Global variable
lastUpdateTime = 0
useMyPerf = 1
trackName = ""
trackConf = ""
carName = ""
bestLapFile = ""

PIT_EXIT_STATE_IDLE         = 0
PIT_EXIT_STATE_IN_PIT_LANE  = 1
PIT_EXIT_STATE_THROTTLE     = 2
PIT_EXIT_STATE_BRAKE        = 3
PIT_EXIT_STATE_APPLY_OFFSET = 4

nurbTourist = False

# import libraries
if not unitTesting:
    try:
        if platform.architecture()[0] == "64bit":
          sysdir='apps/python/PartyLaps/PartyLaps_dll/stdlib64'
        else:
          sysdir='apps/python/PartyLaps/PartyLaps_dll/stdlib'
        sys.path.insert(0, sysdir)
        os.environ['PATH'] = os.environ['PATH'] + ";."

        from PartyLaps_lib.sim_info import info
    except Exception as e:
        ac.log("PartyLaps: Error importing libraries: %s" % e)


def acMain(ac_version):
    """
    Initialise the application.
    """
    try:
        global partyLapsApp, configApp, config
        global showHeader, fontSize, opacity, showBorder
        global lapDisplayedCount, showDelta, deltaColor, redAt, greenAt
        global reference, showCurrent, showReference, showTotal
        global updateTime, logLaps, logBest, lockBest
        global driversListText, driversList, currentDriver
        global trackName, trackConf, carName, bestLapFile
        global nurbTourist

        if ac_version < 1.0:
            return "PartyLaps"

        for dirName in ["PartyLaps_bestlap", "PartyLaps_config", "PartyLaps_session"]:
            fullDirName = "apps/python/PartyLaps/" + dirName
            if not os.path.exists(fullDirName):
                os.mkdir(fullDirName)

        config = configparser.ConfigParser()
        configFile = "apps/python/PartyLaps/PartyLaps_config/config.ini"
        mlConfigFile = "apps/python/MultiLaps/MultiLaps_config/config.ini"

        config.read([mlConfigFile, configFile])

        try:
            config.add_section("SETTINGS")
        except configparser.DuplicateSectionError:
            pass

        showHeader        = config.getint("SETTINGS", "showHeader", fallback=0)
        fontSize          = config.getint("SETTINGS", "fontSize", fallback=18)
        opacity           = config.getint("SETTINGS", "opacity", fallback=50)
        showBorder        = config.getint("SETTINGS", "showBorder", fallback=0)
        lapDisplayedCount = config.getint("SETTINGS", "lapDisplayedCount", fallback=5)
        showDelta         = config.getint("SETTINGS", "showDelta", fallback=1)
        deltaColor        = config.get("SETTINGS", "deltaColor", fallback="white")
        redAt             = config.getint("SETTINGS", "redAt", fallback=1000)
        greenAt           = config.getint("SETTINGS", "greenAt", fallback=1000)
        reference         = config.get("SETTINGS", "reference", fallback="best")
        showCurrent       = config.getint("SETTINGS", "showCurrent", fallback=1)
        showTotal         = config.getint("SETTINGS", "showTotal", fallback=1)
        showReference     = config.getint("SETTINGS", "showReference", fallback=1)
        updateTime        = config.getint("SETTINGS", "updateTime", fallback=100)
        logLaps           = config.getint("SETTINGS", "logLaps", fallback=1)
        logBest           = config.get("SETTINGS", "logBest", fallback="always")
        lockBest          = config.getint("SETTINGS", "lockBest", fallback=0)
        driversListText   = config.get("SETTINGS", "driversListText", fallback='')
        driversList       = explodeCSL(driversListText)
        currentDriver     = config.get("SETTINGS", "currentDriver", fallback=driversList[0])

        trackName = ac.getTrackName(0)
        trackConf = ac.getTrackConfiguration(0)
        carName = ac.getCarName(0)

        if trackConf == "":
            bestLapFile = "apps/python/PartyLaps/PartyLaps_bestlap/{0} - {1}.ini".format(
                trackName, carName)
        else:
            bestLapFile = "apps/python/PartyLaps/PartyLaps_bestlap/{0} [{1}] - {2}.ini".format(
                trackName, trackConf, carName)

        if trackName == "ks_nordschleife" and trackConf == "touristenfahrten":
            nurbTourist = True

        deltaApp = PartyDelta()

        partyLapsApp = PartyLaps(ac, "PartyLaps", "Laps", deltaApp)
        partyLapsApp.refreshParameters()

        configApp = PartyLaps_config("PartyLaps_config", "PartyLaps config", fontSizeConfig, 0)
        configApp.updateView()

        ac.addRenderCallback(partyLapsApp.window, onRenderCallback)

        return "PartyLaps"
    except Exception as e:
        import traceback
        ac.log("PartyLaps: Error in acMain: %s" % e)
        ac.log(traceback.format_exc())


def acShutdown():
    try:
        if info.graphics.status != 1:
            partyLapsApp.writeSession()
            partyLapsApp.writeBestLap()

    except Exception as e:
        ac.log("PartyLaps: Error in acShutdown: %s" % e)

def writeParameters():
    try:
        config.set("SETTINGS", "showHeader", str(showHeader))
        config.set("SETTINGS", "fontSize", str(fontSize))
        config.set("SETTINGS", "opacity", str(opacity))
        config.set("SETTINGS", "showBorder", str(showBorder))
        config.set("SETTINGS", "lapDisplayedCount", str(lapDisplayedCount))
        config.set("SETTINGS", "showDelta", str(showDelta))
        config.set("SETTINGS", "deltaColor", str(deltaColor))
        config.set("SETTINGS", "redAt", str(redAt))
        config.set("SETTINGS", "greenAt", str(greenAt))
        config.set("SETTINGS", "reference", str(reference))
        config.set("SETTINGS", "showCurrent", str(showCurrent))
        config.set("SETTINGS", "showTotal", str(showTotal))
        config.set("SETTINGS", "showReference", str(showReference))
        config.set("SETTINGS", "updateTime",  str(updateTime))
        config.set("SETTINGS", "logLaps",  str(logLaps))
        config.set("SETTINGS", "logBest",  str(logBest))
        config.set("SETTINGS", "lockBest",  str(lockBest))
        config.set("SETTINGS", "driversListText", driversListText)
        config.set("SETTINGS", "currentDriver", currentDriver)

        configFile = open("apps/python/PartyLaps/PartyLaps_config/config.ini", 'w')
        config.write(configFile)
        configFile.close()

    except Exception as e:
        ac.log("PartyLaps: Error in writeParameters while writing the file: %s" % e)

def refreshAndWriteParameters():
    try:
        partyLapsApp.refreshParameters()
        partyLapsApp.updateData()
        partyLapsApp.updateView()
        configApp.updateView()
        writeParameters()

    except Exception as e:
        ac.log("PartyLaps: Error in refreshAndWriteParameters: %s" % e)

def acUpdate(deltaT):
    """
    This function is called for every frame rendered. Instruct every app to
    update its view, if the time since the last update is great enough.
    """
    try:
        global lastUpdateTime
        lastUpdateTime += deltaT

        if lastUpdateTime < float(updateTime)/1000:
            return

        lastUpdateTime = 0

        # block refresh during replay
        #if info.graphics.status != 1:
        partyLapsApp.updateData()
        partyLapsApp.updateView()
        configApp.updateView()

    except Exception as e:
        import traceback
        ac.log("PartyLaps: Error in acUpdate: %s" % e)
        ac.log(traceback.format_exc())

def onRenderCallback(deltaT):
    """
    This is called when the app has been moved.
    """
    try:
        partyLapsApp.onRenderCallback(deltaT)
        configApp.onRenderCallback(deltaT)

    except Exception as e:
        ac.log("PartyLaps: Error in onRenderCallback: %s" % e)

class PartyLaps:

    def __init__(self, ac, name, headerName, deltaApp):
        self.ac = ac
        self.headerName = headerName
        self.deltaApp = deltaApp
        self.window = self.ac.newApp(name)

        self.lastLapDataRefreshed = -1
        self.lastLapViewRefreshed = 0
        self.total = 0
        self.bestLapAc = 0
        self.bestLapTimeSession = 0
        self.bestLapTime = 0
        self.bestLapHolder = ""
        self.referenceTime = 0
        self.laps = []
        self.bestLapFile = bestLapFile
        self.bestLapData = []
        self.currentLapData = [(0.0,0.0)]
        self.personalBests = {}
        self.sfCrossed = 0
        try:
            self.session = info.graphics.session
        except NameError:
            # In a test
            pass
        self.lastSession = 0
        self.lapInvalidated = False
        self.justCrossedSf = False
        self.position = 0
        self.lastPosition = 0
        self.currentTime = 0
        self.lastCurrentTime = 0
        self.pitExitState = 0
        self.pitExitDeltaOffset = 0
        self.pitExitLap = 0

        self.readBestLap()

        self.table = ACTable(self.ac, self.window)


    def draw(self):
        """
        Redraw the whole window. This must be done whenever the table geometry
        changes.
        """
        if showHeader:
            self.ac.setTitle(self.window, self.headerName)
            self.ac.setIconPosition(self.window, 0, 0)
            topPadding = 30
        else:
            self.ac.setTitle(self.window, "")
            self.ac.setIconPosition(self.window, -10000, -10000)
            topPadding = 0

        tableRows = 1 + lapDisplayedCount + showCurrent + showReference + 1 + showTotal

        self.table.setSize(3, tableRows)
        self.table.setTablePadding(5, topPadding)
        self.table.setCellSpacing(0, 5)
        self.table.setColumnWidths(2, 5, 5)
        self.table.setColumnAlignments("left", "right", "right")
        self.table.setFontSize(fontSize)

        self.table.draw()

        width, height = self.table.getDimensions()
        self.ac.setSize(self.window, width, height)

        self.table.setCellValue("Driver:", 0, 0)

        self.currRowIndex = lapDisplayedCount + showCurrent
        self.refRowIndex = self.currRowIndex + showReference
        self.pbRowIndex = self.refRowIndex + 1
        self.totRowIndex = self.pbRowIndex + showTotal

        if showCurrent:
            self.table.setCellValue("Curr.", 0, self.currRowIndex)
        if showReference:
            if reference == "best":
                refText = "Best"
            elif reference == "median":
                refText = "Med."
            elif reference == "top25":
                refText = "25%"
            elif reference == "top50":
                refText = "50%"
            elif reference == "top75":
                refText = "75%"
            self.table.setCellValue(refText, 0, self.refRowIndex)
        self.table.setCellValue("Pers.", 0, self.pbRowIndex)
        self.table.setCellValue("-.---", 2, self.pbRowIndex)
        if showTotal:
            self.table.setCellValue("Tot.", 0, self.totRowIndex)

        self.table.addOnClickedListener(0, 0, onClickDriver)
        self.table.addOnClickedListener(1, 0, onClickDriver)

        self.setDriverCellValues()
        self.setPersonalBestCellValues()


    def setDriverCellValues(self):
        """
        Set the values for the current driver information row.
        """
        self.table.setCellValue(
                currentDriver if currentDriver != "" else "OPEN CONFIG TO SET DRIVERS",
                1, 0)

    def setPersonalBestCellValues(self):
        """
        Display the correct personal best.
        """
        self.table.setCellValue(timeToString(self.personalBest()), 1, self.pbRowIndex)


    def refreshParameters(self):
        # Force full refresh
        self.draw()
        self.updateDataFast()
        self.updateDataRef()
        self.updateViewFast()
        self.updateViewNewLap()

    def onRenderCallback(self, deltaT):
        # Update background and border in case the app has been moved
        self.ac.setBackgroundOpacity(self.window, float(opacity)/100)
        self.ac.drawBorder(self.window, showBorder)
        self.deltaApp.onRenderCallback()

    def updateData(self):
        self.updateDataFast()

        # Refresh on a new lap if we are not watching a replay
        if (self.lastLapDataRefreshed != self.lapDone) and (info.graphics.status != 1):
            # To be sure that the last lap has been updated, we wait for the 2nd refresh or 200ms
            if self.justCrossedSf or (self.currentTime > 200):
                self.updateDataNewLap()
                self.updateDataRef()
                self.justCrossedSf = False
            else:
                self.justCrossedSf = True

    def updateDataFast(self):
        self.currentTime = self.ac.getCarState(0, acsys.CS.LapTime)

        if info.graphics.status == 1:
            self.projection = 0
            self.performance = 0
            self.pbPerformance = 0
            return

        self.lapDone = self.ac.getCarState(0, acsys.CS.LapCount)
        self.currentPosition = self.ac.getCarState(0, acsys.CS.NormalizedSplinePosition)

        if self.ac.isCarInPitline(0):
            self.pitExitState = PIT_EXIT_STATE_IN_PIT_LANE
        elif self.pitExitState == PIT_EXIT_STATE_IN_PIT_LANE:
            self.pitExitLap = self.lapDone
            self.pitExitState = PIT_EXIT_STATE_THROTTLE
        elif self.pitExitState == PIT_EXIT_STATE_THROTTLE and info.physics.brake > 0.1:
            self.pitExitState = PIT_EXIT_STATE_BRAKE
        elif self.pitExitState == PIT_EXIT_STATE_BRAKE and info.physics.gas > 0.9:
            self.pitExitState = PIT_EXIT_STATE_APPLY_OFFSET
            self.pitExitDeltaOffset = self.performance
        elif self.pitExitState == PIT_EXIT_STATE_APPLY_OFFSET and self.lapDone > self.pitExitLap:
            self.pitExitState = PIT_EXIT_STATE_IDLE

        # correct pos for Nordschleife tourist setup
        if nurbTourist:
            if self.currentPosition > 0.9525: # bridge
                self.currentPosition = self.currentPosition - 0.9525
            else:
                self.currentPosition = self.currentPosition + 0.0475 # (1.0 - 0.9525)
            # normalize to 0.0 - 1.0
            self.currentPosition = self.currentPosition / 0.9165 # 1/(0.8690 + (1.0 - 0.9525))
            if self.currentPosition > 1.0:
                self.currentPosition = 0.0

        #Filter AC's bullshits...
        if self.lastPosition > self.currentPosition and self.currentTime > self.lastCurrentTime and self.currentTime < (self.lastCurrentTime+1000):
            return

        self.lastCurrentTime = self.currentTime

        self.position = self.currentPosition
        self.lastPosition = self.currentPosition
        self.bestLapAc = self.ac.getCarState(0, acsys.CS.BestLap)

        self.lapInvalidated = info.physics.numberOfTyresOut == 4 or self.lapInvalidated

        self.session = info.graphics.session

        # This will happend after a reset AND at the beginning of the first lap
        if self.session != self.lastSession or (self.currentTime < 500 and self.lapDone == 0):
            self.currentLapData = [(0.0,0.0)]

            self.writeSession()
            self.bestLapTimeSession = 0
            self.total = 0
            self.referenceTime = self.bestLapTime
            self.laps = []

            self.lastSession = self.session

            if logBest == "never":
                self.bestLapTime == 0
                self.bestLapData == []

            # Check if the reset has put us behind the s/f line
            if self.position > 0.5:
                self.sfCrossed = False

        # Check if we have crossed the s/f line
        if not self.sfCrossed:
            if self.position < 0.5:
                self.sfCrossed = True
            else:
                return

        if useMyPerf:
            # If the position has increased and we are not in replay, add the new position
            if self.position > self.currentLapData[len(self.currentLapData)-1][0]:
                self.currentLapData.append((self.position, self.currentTime))

            self.myPerformance = calculateDelta(self.position, self.currentTime, self.bestLapData)

            self.projection = self.bestLapTime + self.myPerformance
            self.performance = self.myPerformance + (self.bestLapTime - self.referenceTime)*self.position

            self.pbPerformance = calculateDelta(self.position, self.currentTime, self.personalBestData())

        else:
            # This path is never followed
            self.performanceAc = int(self.ac.getCarState(0, acsys.CS.PerformanceMeter) * 1000)
            self.projection = self.bestLapAc + self.performanceAc
            self.performance = self.performanceAc + (self.bestLapAc - self.referenceTime)*self.position
            self.pbPerformance = 0

    def updateDataNewLap(self):
        """
        A new lap has been started.
        """
        self.lastLapDataRefreshed = self.lapDone

        # Reset
        if self.lapDone <= 0:
            return

        # Wait 100ms to be sure that the last time is updated
        #time.sleep(0.1)

        # self.ac.getCarState(0, acsys.CS.LastLap) doesn't work yet
        #lapTime = self.ac.getCarState(0, acsys.CS.LastLap)
        lapTime = info.graphics.iLastTime
        if lapTime <= 0:
            lastSplits = self.ac.getLastSplits(0)
            lapTime = 0
            for split in lastSplits:
                lapTime += split

        if self.bestLapTimeSession == 0 or lapTime < self.bestLapTimeSession:
            self.bestLapTimeSession = lapTime

        if not lockBest and (self.bestLapTime == 0 or lapTime < self.bestLapTime) and not self.lapInvalidated:
            # New record!
            self.bestLapTime = lapTime
            self.bestLapHolder = currentDriver
            self.currentLapData.append((1.0, lapTime))
            self.bestLapData = self.currentLapData
            #self.ac.log("PartyLaps: New best lap time: {0} Data: {1}".format(timeToString(self.bestLapTime), str(self.bestLapData)))

        # Look for a personal best
        pb = self.personalBest()
        if not lockBest and (pb == 0 or lapTime < pb) and not self.lapInvalidated:
            # New personal best lap time!
            pbInfo = {
                "time": lapTime,
                "data": self.currentLapData,
            }
            pbInfo['data'].append((1.0, lapTime))
            self.personalBests[currentDriver] = pbInfo
            self.setPersonalBestCellValues()

        # Reset for the new lap
        self.currentLapData = [(0.0,0.0)]
        self.lapInvalidated = False

        self.total += lapTime
        self.laps.append(lapTime)

    def updateDataRef(self):
        if reference == "best":
            if useMyPerf:
                self.referenceTime = self.bestLapTime
            else:
                self.referenceTime = self.bestLapAc
        elif len(self.laps) < 1:
            self.referenceTime = 0
        elif len(self.laps) == 1:
            self.referenceTime = self.laps[0]
        else:
            lapsSorted = sorted(self.laps)

            if reference == "median":
                if len(lapsSorted) %2 == 1:
                    self.median = lapsSorted[int(((len(lapsSorted)+1)/2)-1)]
                elif len(lapsSorted) %2 == 0:
                    self.median = float(sum(lapsSorted[int((len(lapsSorted)/2)-1):int((len(lapsSorted)/2)+1)]))/2.0
                self.referenceTime = self.median

            elif reference == "top25":
                self.referenceTime = self.getTopAvg(25, lapsSorted)

            elif reference == "top50":
                self.referenceTime = self.getTopAvg(50, lapsSorted)

            elif reference == "top75":
                self.referenceTime = self.getTopAvg(75, lapsSorted)


    def getTopAvg(self, topPercent, lapsSorted):
        count = int((len(lapsSorted) + len(lapsSorted)%2)*topPercent/100)

        if count:
            lapSum = 0
            for index in range(count):
                lapSum += lapsSorted[index]
            return lapSum/count
        else:
            return lapsSorted[0]

    def updateView(self):
        if self.justCrossedSf:
            return

        self.updateViewFast()

        # Refresh laps and total only on lap change and not replay
        if self.lastLapViewRefreshed != self.lastLapDataRefreshed and info.graphics.status != 1:
            self.updateViewNewLap()


    def updateViewNewLap(self):
        """
        Refresh the laps and the total.
        """
        for index in range(lapDisplayedCount):
            rowIndex = index + 1
            lapIndex = index
            if len(self.laps) > lapDisplayedCount:
                lapIndex += len(self.laps)-lapDisplayedCount

            # Refresh lap number
            if (self.pitExitLap > 0) and (self.pitExitLap <= lapIndex < self.lapDone):
                self.table.setCellValue("{0}. ({1})".format(lapIndex+1, lapIndex-self.pitExitLap+1), 0, rowIndex)
            else:
                self.table.setCellValue("%d." % (lapIndex+1), 0, rowIndex)

            # Refresh lap times and deltas
            if lapIndex < len(self.laps):
                self.table.setCellValue(timeToString(self.laps[lapIndex]), 1, rowIndex)

                # Best lap in green
                if self.laps[lapIndex] == self.bestLapAc:
                    self.table.setFontColor(0, 1, 0, 1, 1, rowIndex)
                else:
                    self.table.setFontColor(1, 1, 1, 1, 1, rowIndex)

                # Refresh delta label
                setDelta(self.table.getCellLabel(2, rowIndex),
                        self.laps[lapIndex] - self.referenceTime)

            else:
                self.table.setCellValue(timeToString(0), 1, rowIndex)
                self.table.setFontColor(1, 1, 1, 1, 1, rowIndex)
                self.table.setCellValue("-.---", 2, rowIndex)
                self.table.setFontColor(1, 1, 1, 1, 2, rowIndex)

        # Refresh Total
        self.table.setCellValue(timeToString(self.total), 1, self.totRowIndex)

        # Refresh reference
        self.table.setCellValue(timeToString(self.referenceTime), 1, self.refRowIndex)

        # Update the new lap holder view
        self.table.setCellValue(self.bestLapHolder, 2, self.refRowIndex)

        self.lastLapViewRefreshed = self.lastLapDataRefreshed


    def updateViewFast(self):
        """
        Refresh current lap projection and performance.
        """
        if self.sfCrossed and len(self.bestLapData) > 0 and info.graphics.status != 1 and self.position > 0.00001:
            self.table.setCellValue(timeToString(self.projection), 1, self.currRowIndex)
            if self.pitExitState == PIT_EXIT_STATE_APPLY_OFFSET:
                setDelta(self.table.getCellLabel(2, self.currRowIndex),
                        self.performance-self.pitExitDeltaOffset, self.deltaApp)
                setDelta(self.table.getCellLabel(2, self.pbRowIndex),
                        self.pbPerformance-self.pitExitDeltaOffset, self.deltaApp, True)
            else:
                setDelta(self.table.getCellLabel(2, self.currRowIndex),
                        self.performance, self.deltaApp)
                setDelta(self.table.getCellLabel(2, self.pbRowIndex),
                        self.pbPerformance, self.deltaApp, True)
        else:
            self.table.setCellValue(timeToString(self.currentTime), 1, self.currRowIndex)
            self.table.setCellValue("-.---", 2, self.currRowIndex)
            self.table.setFontColor(1, 1, 1, 1, 2, self.currRowIndex)

        if self.lapInvalidated:
            self.table.setFontColor(1, 0, 0, 1, 1, self.currRowIndex)
        else:
            self.table.setFontColor(1, 1, 1, 1, 1, self.currRowIndex)


    def writeSession(self):
        try:
            if logLaps and len(self.laps) > 0:
                lapsLog = configparser.ConfigParser()
                if trackConf == "":
                    fileName = "apps/python/PartyLaps/PartyLaps_session/{0} - {1} - {2}.ini".format(
                        trackName, carName, time.strftime("%Y-%m-%d"))
                else:
                    fileName = "apps/python/PartyLaps/PartyLaps_session/{0} [{1}] - {2} - {3}.ini".format(
                        trackName, trackConf, carName, time.strftime("%Y-%m-%d"))

                if os.path.exists(fileName):
                    lapsLog.read(fileName)

                sessionNumer = 1
                sectionName = "Session {0}".format(sessionNumer)

                while lapsLog.has_section(sectionName):
                    sessionNumer += 1
                    sectionName = "Session {0}".format(sessionNumer)

                lapsLog.add_section(sectionName)

                for index in range(len(self.laps)):
                    lapsLog.set(sectionName, "Lap {0}".format(index+1), timeToString(self.laps[index]))

                if reference != "best":
                    lapsLog.set(sectionName, reference.title(), timeToString(self.referenceTime))

                lapsLog.set(sectionName, "Best", timeToString(self.bestLapTimeSession))
                lapsLog.set(sectionName, "Total", timeToString(self.total))

                lapsLogFile = open(fileName, "w")
                lapsLog.write(lapsLogFile)
                lapsLogFile.close()

        except Exception as e:
            self.ac.log("PartyLaps class: Error in writeSession: %s" % e)

    def readBestLap(self):
        try:
            if logBest == "always":
                configBestLap = configparser.ConfigParser()
                bestLapFile = self.bestLapFile

                mlBestLapFile = bestLapFile.replace("PartyLaps", "MultiLaps")
                configBestLap.read([mlBestLapFile, bestLapFile])

                self.bestLapTime = configBestLap.getint("TIME", "best", fallback=0)
                self.bestLapHolder = configBestLap.get("TIME", "holder", fallback='')
                self.bestLapData = eval(configBestLap.get("DATA", "data", fallback="[]"))
                self.referenceTime = self.bestLapTime

        except Exception as e:
            self.ac.log("PartyLaps class: Error in writeBestLap: %s" % e)

        self.readPersonalBests()


    def readPersonalBests(self):
        """
        Read the personal bests from the bestLapFile and store on
        self.personalBests.
        """
        if logBest != "always":
            return

        personalBests = {}
        # Load the best lap as the personal best of the holder, for users
        # upgrading from an earlier version.
        if self.bestLapHolder:
            personalBests[self.bestLapHolder] = {
                "driver": self.bestLapHolder,
                "time": self.bestLapTime,
                "data": self.bestLapData,
            }

        config = configparser.ConfigParser()
        config.read(self.bestLapFile)

        sections = config.sections()
        for section in sections:
            if not section.startswith("PB_"):
                continue
            driver = config.get(section, "driver")
            time = config.getint(section, "time")
            data = eval(config.get(section, "data"))
            personalBests[driver] = {"time":time, "data":data}

        self.personalBests = personalBests


    def writePersonalBests(self):
        """
        Serialize the personal best information to a config file.
        """
        if logBest != "always":
            return

        config = configparser.ConfigParser()
        config.read(self.bestLapFile)

        for driver, info in self.personalBests.items():
            if not driver: # driver name might not be set
                continue
            section = "PB_" + driver
            try:
                config.add_section(section)
            except configparser.DuplicateSectionError:
                pass
            config.set(section, "driver", driver)
            config.set(section, "time", str(info['time']))
            config.set(section, "data", str(info['data']))

        fd = open(self.bestLapFile, "w")
        config.write(fd)
        fd.close()


    def personalBest(self):
        """
        Return the integer personal best lap time.
        """
        try:
            return self.personalBests[currentDriver]['time']
        except KeyError:
            return 0


    def personalBestData(self):
        """
        Return the personal best lap time data.
        """
        try:
            return self.personalBests[currentDriver]['data']
        except KeyError:
            return []


    def resetBestLap(self):
        try:
            self.bestLapTime = 0
            self.bestLapData = []

            if os.path.exists(self.bestLapFile):
                os.remove(self.bestLapFile)

        except Exception as e:
            self.ac.log("PartyLaps class: Error in resetBestLap: %s" % e)

    def writeBestLap(self):
        try:
            if logBest == "always" and self.bestLapTime and len(self.bestLapData) > 0:
                configBestLap = configparser.ConfigParser()

                if os.path.exists(self.bestLapFile):
                    configBestLap.read(self.bestLapFile)
                    lastBest = configBestLap.getint("TIME", "best")
                    if lastBest != 0 and lastBest < self.bestLapTime:
                        return
                else:
                    configBestLap.add_section("TIME")
                    configBestLap.add_section("DATA")

                configBestLap.set("TIME", "best", str(self.bestLapTime))
                configBestLap.set("TIME", "holder", str(self.bestLapHolder))
                configBestLap.set("DATA", "data", str(self.bestLapData))

                fd = open(self.bestLapFile, "w")
                configBestLap.write(fd)
                fd.close()

        except Exception as e:
            self.ac.log("PartyLaps class: Error in writeBestLap: %s" % e)

        self.writePersonalBests()

'''
Show header:    Yes       Change
Font size:      18        + -
Opacity:        50 %      + -
Show border:    Yes       Change

Lap count:      6         + -
Show delta:     Yes       Change
Delta color:    White     Change
Red at:         +0.5 s    + -
Green at:       -0.5 s    - +
Show Curr.:     Yes       Change
Reference:      Median    Change
Show ref.:      Yes       Change
Show total:     Yes       Change

Refresh every:  0.1 s     + -
Log sessions:   Yes       Change
Remember best:  Always    Change
Best lap:       1:52.123  Reset
Lock best:      Locked    Lock/Unlock

Driver names, comma-separated:
[ ]
'''
class PartyLaps_config:
    """
    A configuration widget.
    """
    def __init__(self, name, headerName, fontSize, showHeader):
        self.headerName = headerName
        self.window = ac.newApp(name)
        if showHeader == 1:
            ac.setTitle(self.window, "")
            ac.setIconPosition(self.window, -10000, -10000)
            self.topPadding = 0
        else:
            ac.setTitle(self.window, headerName)
            self.topPadding = topPadding

        self.fontSize = fontSize

        widthLeft       = fontSize*8
        widthCenter     = fontSize*5
        widthRight      = fontSize*5
        self.width      = widthLeft + widthCenter + widthRight + 2*spacing
        height          = self.topPadding + (fontSize*1.5 + spacing)*22

        ac.setSize(self.window, self.width, height)

        self.leftLabel = []
        self.centerLabel = []
        self.changeButton = []
        self.plusButton = []
        self.minusButton = []

        for index in range(21):
            self.leftLabel.append(ac.addLabel(self.window, ""))
            ac.setFontSize(self.leftLabel[index], fontSize)
            ac.setPosition(self.leftLabel[index], spacing, self.topPadding + index*(fontSize*1.5+spacing))
            ac.setSize(self.leftLabel[index], widthLeft, fontSize+spacing)
            ac.setFontAlignment(self.leftLabel[index], 'left')

            self.centerLabel.append(ac.addLabel(self.window, ""))
            ac.setFontSize(self.centerLabel[index], fontSize)
            ac.setPosition(self.centerLabel[index], spacing + widthLeft, self.topPadding + index*(fontSize*1.5+spacing))
            ac.setSize(self.centerLabel[index], widthCenter, fontSize+spacing)
            ac.setFontAlignment(self.centerLabel[index], 'left')

            self.changeButton.append(ac.addButton(self.window, "Change"))
            ac.setFontSize(self.changeButton[index], self.fontSize)
            ac.setPosition(self.changeButton[index], spacing + widthLeft + widthCenter, self.topPadding + index*(fontSize*1.5+spacing))
            ac.setSize(self.changeButton[index], fontSize*4, fontSize*1.5)

            self.plusButton.append(ac.addButton(self.window, "+"))
            ac.setFontSize(self.plusButton[index], self.fontSize)
            ac.setPosition(self.plusButton[index], spacing + widthLeft + widthCenter, self.topPadding + index*(fontSize*1.5+spacing))
            ac.setSize(self.plusButton[index], fontSize*1.5, fontSize*1.5)

            self.minusButton.append(ac.addButton(self.window, "-"))
            ac.setFontSize(self.minusButton[index], self.fontSize)
            ac.setPosition(self.minusButton[index], spacing + widthLeft + widthCenter + fontSize*2.5, self.topPadding + index*(fontSize*1.5+spacing))
            ac.setSize(self.minusButton[index], fontSize*1.5, fontSize*1.5)

        rowIndex = 0

        ac.setText(self.leftLabel[rowIndex], "Show header:")
        ac.addOnClickedListener(self.changeButton[rowIndex], toggleHeader)
        ac.setVisible(self.plusButton[rowIndex], 0)
        ac.setVisible(self.minusButton[rowIndex], 0)
        self.showHeaderId = rowIndex

        rowIndex += 1

        ac.setText(self.leftLabel[rowIndex], "Font size:")
        ac.setVisible(self.changeButton[rowIndex], 0)
        ac.addOnClickedListener(self.plusButton[rowIndex], fontSizePlus)
        ac.addOnClickedListener(self.minusButton[rowIndex], fontSizeMinus)
        self.fontSizeId = rowIndex

        rowIndex += 1

        ac.setText(self.leftLabel[rowIndex], "Opacity:")
        ac.setVisible(self.changeButton[rowIndex], 0)
        ac.addOnClickedListener(self.plusButton[rowIndex], opacityPlus)
        ac.addOnClickedListener(self.minusButton[rowIndex], opacityMinus)
        self.opacityId = rowIndex

        rowIndex += 1

        ac.setText(self.leftLabel[rowIndex], "Show border:")
        ac.addOnClickedListener(self.changeButton[rowIndex], toggleBorder)
        ac.setVisible(self.plusButton[rowIndex], 0)
        ac.setVisible(self.minusButton[rowIndex], 0)
        self.showBorderId = rowIndex

        rowIndex += 1

        ac.setVisible(self.changeButton[rowIndex], 0)
        ac.setVisible(self.plusButton[rowIndex], 0)
        ac.setVisible(self.minusButton[rowIndex], 0)

        rowIndex += 1

        ac.setText(self.leftLabel[rowIndex], "Lap count:")
        ac.setVisible(self.changeButton[rowIndex], 0)
        ac.addOnClickedListener(self.plusButton[rowIndex], lapCountPlus)
        ac.addOnClickedListener(self.minusButton[rowIndex], lapCountMinus)
        self.lapCountId = rowIndex

        rowIndex += 1

        ac.setText(self.leftLabel[rowIndex], "Show delta:")
        ac.addOnClickedListener(self.changeButton[rowIndex], toggleDelta)
        ac.setVisible(self.plusButton[rowIndex], 0)
        ac.setVisible(self.minusButton[rowIndex], 0)
        self.showDeltaId = rowIndex

        rowIndex += 1

        ac.setText(self.leftLabel[rowIndex], "Delta color:")
        ac.addOnClickedListener(self.changeButton[rowIndex], toggleColor)
        ac.setVisible(self.plusButton[rowIndex], 0)
        ac.setVisible(self.minusButton[rowIndex], 0)
        self.deltaColorId = rowIndex

        rowIndex += 1

        ac.setText(self.leftLabel[rowIndex], "Red at:")
        ac.setVisible(self.changeButton[rowIndex], 0)
        ac.addOnClickedListener(self.plusButton[rowIndex], redAtPlus)
        ac.addOnClickedListener(self.minusButton[rowIndex], redAtMinus)
        self.redAtId = rowIndex

        rowIndex += 1

        ac.setText(self.leftLabel[rowIndex], "Green at:")
        ac.setVisible(self.changeButton[rowIndex], 0)
        ac.addOnClickedListener(self.plusButton[rowIndex], greenAtPlus)
        ac.addOnClickedListener(self.minusButton[rowIndex], greenAtMinus)
        self.greenAtId = rowIndex

        rowIndex += 1

        ac.setText(self.leftLabel[rowIndex], "Show curr.:")
        ac.addOnClickedListener(self.changeButton[rowIndex], toggleCurrent)
        ac.setVisible(self.plusButton[rowIndex], 0)
        ac.setVisible(self.minusButton[rowIndex], 0)
        self.showCurrentId = rowIndex

        rowIndex += 1

        ac.setText(self.leftLabel[rowIndex], "Reference:")
        ac.addOnClickedListener(self.changeButton[rowIndex], toggleRefSource)
        ac.setVisible(self.plusButton[rowIndex], 0)
        ac.setVisible(self.minusButton[rowIndex], 0)
        self.referenceId = rowIndex

        rowIndex += 1

        ac.setText(self.leftLabel[rowIndex], "Show ref.:")
        ac.addOnClickedListener(self.changeButton[rowIndex], toggleRef)
        ac.setVisible(self.plusButton[rowIndex], 0)
        ac.setVisible(self.minusButton[rowIndex], 0)
        self.showReferenceId = rowIndex

        rowIndex += 1

        ac.setText(self.leftLabel[rowIndex], "Show total:")
        ac.addOnClickedListener(self.changeButton[rowIndex], toggleTotal)
        ac.setVisible(self.plusButton[rowIndex], 0)
        ac.setVisible(self.minusButton[rowIndex], 0)
        self.showTotalId = rowIndex

        rowIndex += 1

        ac.setVisible(self.changeButton[rowIndex], 0)
        ac.setVisible(self.plusButton[rowIndex], 0)
        ac.setVisible(self.minusButton[rowIndex], 0)

        rowIndex += 1

        ac.setText(self.leftLabel[rowIndex], "Refresh every:")
        ac.setVisible(self.changeButton[rowIndex], 0)
        ac.addOnClickedListener(self.plusButton[rowIndex], refreshPlus)
        ac.addOnClickedListener(self.minusButton[rowIndex], refreshMinus)
        self.refreshId = rowIndex

        rowIndex += 1

        ac.setText(self.leftLabel[rowIndex], "Log sessions:")
        ac.addOnClickedListener(self.changeButton[rowIndex], toggleLogLaps)
        ac.setVisible(self.plusButton[rowIndex], 0)
        ac.setVisible(self.minusButton[rowIndex], 0)
        self.logLapsId = rowIndex

        rowIndex += 1

        ac.setText(self.leftLabel[rowIndex], "Remember best:")
        ac.addOnClickedListener(self.changeButton[rowIndex], toggleLogBest)
        ac.setVisible(self.plusButton[rowIndex], 0)
        ac.setVisible(self.minusButton[rowIndex], 0)
        self.logBestId = rowIndex

        rowIndex += 1

        ac.setText(self.leftLabel[rowIndex], "Best lap:")
        ac.addOnClickedListener(self.changeButton[rowIndex], resetBestLap)
        ac.setText(self.changeButton[rowIndex], "Reset")
        ac.setVisible(self.plusButton[rowIndex], 0)
        ac.setVisible(self.minusButton[rowIndex], 0)
        self.resetBestLapId = rowIndex

        rowIndex += 1

        ac.setText(self.leftLabel[rowIndex], "Lock best:")
        ac.addOnClickedListener(self.changeButton[rowIndex], toggleLockBest)
        ac.setVisible(self.plusButton[rowIndex], 0)
        ac.setVisible(self.minusButton[rowIndex], 0)
        self.lockBestId = rowIndex

        rowIndex += 1

        ac.setText(self.leftLabel[rowIndex], "Driver names, comma-separated:")
        # Hide all the widgets used for other rows
        ac.setVisible(self.changeButton[rowIndex], 0)
        ac.setVisible(self.plusButton[rowIndex], 0)
        ac.setVisible(self.minusButton[rowIndex], 0)

        # Text input widget for driver names
        rowIndex += 1

        self.driversInput = ac.addTextInput(self.window, driversListText)
        ac.setText(self.driversInput, driversListText)
        ac.setFontSize(self.driversInput, self.fontSize)
        ac.setPosition(self.driversInput, spacing, self.topPadding + rowIndex*(fontSize*1.5+spacing))
        ac.setSize(self.driversInput, widthLeft + widthCenter + widthRight, fontSize*1.5)


    def onRenderCallback(self, deltaT):
        # Update background in case the app has been moved
        ac.setBackgroundOpacity(self.window, 1.0)

    def updateView(self):
        ac.setText(self.centerLabel[self.showHeaderId], yesOrNo(showHeader))
        ac.setText(self.centerLabel[self.fontSizeId],   str(fontSize))
        ac.setText(self.centerLabel[self.opacityId],   "{0} %".format(opacity))
        ac.setText(self.centerLabel[self.showBorderId], yesOrNo(showBorder))
        ac.setText(self.centerLabel[self.lapCountId],   str(lapDisplayedCount))
        ac.setText(self.centerLabel[self.showDeltaId],  yesOrNo(showDelta))
        ac.setText(self.centerLabel[self.deltaColorId], deltaColor.title())
        ac.setText(self.centerLabel[self.redAtId],
                "{:+.1f} s".format(float(redAt)/1000))
        ac.setText(self.centerLabel[self.greenAtId],
                "{:+.1f} s".format(float(greenAt)/1000))
        ac.setText(self.centerLabel[self.showCurrentId], yesOrNo(showCurrent))

        if reference == "best":
            ac.setText(self.centerLabel[self.referenceId], "Best lap")
        elif reference == "median":
            ac.setText(self.centerLabel[self.referenceId], "Median")
        elif reference == "top25":
            ac.setText(self.centerLabel[self.referenceId], "Top 25%")
        elif reference == "top50":
            ac.setText(self.centerLabel[self.referenceId], "Top 50%")
        elif reference == "top75":
            ac.setText(self.centerLabel[self.referenceId], "Top 75%")

        ac.setText(self.centerLabel[self.showReferenceId], yesOrNo(showReference))
        ac.setText(self.centerLabel[self.showTotalId], yesOrNo(showTotal))

        if updateTime == 0:
            ac.setText(self.centerLabel[self.refreshId], "Min")
        elif updateTime == 50:
            ac.setText(self.centerLabel[self.refreshId], "0.05 s")
        else:
            ac.setText(self.centerLabel[self.refreshId], "{:.1f} s".format(float(updateTime)/1000))

        ac.setText(self.centerLabel[self.logLapsId], yesOrNo(logLaps))
        ac.setText(self.centerLabel[self.logBestId], logBest.title())
        ac.setText(self.centerLabel[self.resetBestLapId], timeToString(partyLapsApp.bestLapTime))

        if lockBest:
            ac.setText(self.centerLabel[self.lockBestId], "Locked")
        else:
            ac.setText(self.centerLabel[self.lockBestId], "Unlocked")

        # Store new drivers list if it has been changed
        global driversList, driversListText
        newDriversListText = ac.getText(self.driversInput)
        if newDriversListText != driversListText:
            driversListText = newDriversListText
            driversList = explodeCSL(driversListText)
            writeParameters()


class PartyDelta(object):
    """
    Display the delta in a separate window.
    """

    fontSize = 36
    pbFontSize = 24

    def __init__(self):
        self.window = ac.newApp("PartyLaps_delta")

        # The reference delta
        self.deltaLabel = ac.addLabel(self.window, "-.---")
        ac.setSize(self.window, 150, self.fontSize + self.pbFontSize)
        ac.setIconPosition(self.window, -10000, -10000)
        ac.setTitle(self.window, "")
        self.setBackgroundOpacity()

        ac.setSize(self.deltaLabel, 150, self.fontSize)
        ac.setPosition(self.deltaLabel, 0, 0)
        ac.setFontSize(self.deltaLabel, self.fontSize)
        ac.setFontAlignment(self.deltaLabel, "center")

        # The personal delta
        self.pbDeltaLabel = ac.addLabel(self.window, "-.---")

        ac.setSize(self.pbDeltaLabel, 150, self.pbFontSize)
        ac.setPosition(self.pbDeltaLabel, 0, self.fontSize)
        ac.setFontSize(self.pbDeltaLabel, self.pbFontSize)
        ac.setFontAlignment(self.pbDeltaLabel, "center")



    def onRenderCallback(self):
        """
        Reset the background opacity when the app has been moved.
        """
        self.setBackgroundOpacity()


    def setBackgroundOpacity(self):
        """
        Set the opacity to zero.'
        """
        ac.setBackgroundOpacity(self.window, 0.0)
        ac.drawBorder(self.window, False)


    def setDelta(self, delta, isPB=False):
        """
        Set the best lap delta.
        """
        ac.setText(self.deltaLabel if not isPB else self.pbDeltaLabel, delta)


    def setColor(self, r, g, b, s, isPB=False):
        """
        Set the delta color.
        """
        ac.setFontColor(self.deltaLabel if not isPB else self.pbDeltaLabel,
                r, g, b, s)


def toggleHeader(dummy, variable):
    global showHeader

    if showHeader:
        showHeader = 0
    else:
        showHeader = 1

    refreshAndWriteParameters()

def fontSizePlus(dummy, variable):
    global fontSize

    fontSize += 1

    refreshAndWriteParameters()

def fontSizeMinus(dummy, variable):
    global fontSize

    if fontSize > 6:
        fontSize -= 1

    refreshAndWriteParameters()

def opacityPlus(dummy, variable):
    global opacity

    if opacity < 100:
        opacity += 10

    refreshAndWriteParameters()

def opacityMinus(dummy, variable):
    global opacity

    if opacity >= 10:
        opacity -= 10

    refreshAndWriteParameters()

def toggleBorder(dummy, variable):
    global showBorder

    if showBorder:
        showBorder = 0
    else:
        showBorder = 1

    refreshAndWriteParameters()

def lapCountPlus(dummy, variable):
    global lapDisplayedCount

    if lapDisplayedCount < lapLabelCount:
        lapDisplayedCount += 1

    refreshAndWriteParameters()

def lapCountMinus(dummy, variable):
    global lapDisplayedCount

    if lapDisplayedCount > 0:
        lapDisplayedCount -= 1

    refreshAndWriteParameters()

def toggleDelta(dummy, variable):
    global showDelta

    if showDelta:
        showDelta = 0
    else:
        showDelta = 1

    refreshAndWriteParameters()

def toggleColor(dummy, variable):
    global deltaColor

    if deltaColor == "yellow":
        deltaColor = "white"
    elif deltaColor == "white":
        deltaColor = "yellow"

    refreshAndWriteParameters()

def redAtPlus(dummy, variable):
    global redAt

    if redAt < 1000:
        redAt += 100
    elif redAt < 2000:
        redAt += 200
    elif redAt < 10000:
        redAt += 1000

    refreshAndWriteParameters()

def redAtMinus(dummy, variable):
    global redAt

    if redAt > 2000:
        redAt -= 1000
    elif redAt > 1000:
        redAt -= 200
    elif redAt > 0:
        redAt -= 100

    refreshAndWriteParameters()

def greenAtPlus(dummy, variable):
    global greenAt

    if greenAt < -2000:
        greenAt += 1000
    elif greenAt < -1000:
        greenAt += 200
    elif greenAt < 0:
        greenAt += 100

    refreshAndWriteParameters()

def greenAtMinus(dummy, variable):
    global greenAt

    if greenAt > -1000:
        greenAt -= 100
    elif greenAt > -2000:
        greenAt -= 200
    elif greenAt > -10000:
        greenAt -= 1000

    refreshAndWriteParameters()

def toggleRefSource(dummy, variable):
    global reference
    if reference == "best":
        reference = "median"
    elif reference == "median":
        reference = "top25"
    elif reference == "top25":
        reference = "top50"
    elif reference == "top50":
        reference = "top75"
    elif reference == "top75":
        reference = "best"

    refreshAndWriteParameters()

def toggleCurrent(dummy, variable):
    global showCurrent

    if showCurrent:
        showCurrent = 0
    else:
        showCurrent = 1

    refreshAndWriteParameters()

def toggleTotal(dummy, variable):
    global showTotal

    if showTotal:
        showTotal = 0
    else:
        showTotal = 1

    refreshAndWriteParameters()

def toggleRef(dummy, variable):
    global showReference

    if showReference:
        showReference = 0
    else:
        showReference = 1

    refreshAndWriteParameters()

def refreshPlus(dummy, variable):
    global updateTime

    if updateTime == 0:
        updateTime = 50
    elif updateTime == 50:
        updateTime = 100
    elif updateTime < 200:
        updateTime += 100
    else:
        updateTime = 200

    refreshAndWriteParameters()

def refreshMinus(dummy, variable):
    global updateTime

    if updateTime == 50:
        updateTime = 0
    elif updateTime == 100:
        updateTime = 50
    elif updateTime > 100:
        updateTime -= 100
    else:
        updateTime = 0

    refreshAndWriteParameters()

def toggleLogLaps(dummy, variable):
    global logLaps

    if logLaps:
        logLaps = 0
    else:
        logLaps = 1

    refreshAndWriteParameters()

def toggleLogBest(dummy, variable):
    global logBest
    if logBest == "always":
        logBest = "sessions"
    elif logBest == "sessions":
        logBest = "never"
    elif logBest == "never":
        logBest = "always"

    refreshAndWriteParameters()

def toggleLockBest(dummy, variable):
    global lockBest
    if lockBest:
        lockBest = 0
    else:
        lockBest = 1

    refreshAndWriteParameters()

def resetBestLap(dummy, variable):
    partyLapsApp.resetBestLap()
    refreshAndWriteParameters()

def timeToString(time):
    try:
        if time <= 0:
            return "-:--.---"
        else:
            return "{:d}:{:0>2d}.{:0>3d}".format(int(time/60000), int((time%60000)/1000), int(time%1000))
    except Exception as e:
        ac.log("PartyLaps: Error in timeToString: %s" % e)
        return "-:--.---"

def deltaToString(time):
    try:
        return "{:+.3f}".format(float(time)/1000)
    except Exception as e:
        ac.log("PartyLaps: Error in deltaToString: %s" % e)
        return "+0.000"

def yesOrNo(value):
    if value:
        return "Yes"
    else:
        return "No"

def setDelta(label, delta, deltaApp=None, isPB=False):
    deltaStr = deltaToString(delta)
    ac.setText(label, deltaStr)
    if deltaApp:
        deltaApp.setDelta(deltaStr, isPB)

    if delta >= redAt:
        ac.setFontColor(label, 1, 0, 0, 1)
        if deltaApp:
            deltaApp.setColor(1, 0, 0, 1, isPB)
    elif delta <= greenAt:
        ac.setFontColor(label, 0, 1, 0, 1)
        if deltaApp:
            deltaApp.setColor(0, 1, 0, 1, isPB)
    else:
        if deltaColor == "yellow":
            if delta > 0:
                # color factor [0..1]
                colorFactor = float(delta)/redAt
                ac.setFontColor(label, 1, 1-colorFactor, 0, 1)
                if deltaApp:
                    deltaApp.setColor(1, 1-colorFactor, 0, 1, isPB)
            else:
                # color factor [0..1]
                colorFactor = float(delta)/greenAt
                ac.setFontColor(label, 1-colorFactor, 1, 0, 1)
                if deltaApp:
                    deltaApp.setColor(1-colorFactor, 1, 0, 1, isPB)

        elif deltaColor == "white":
            if delta > 0:
                # color factor [0..1]
                colorFactor = float(delta)/redAt
                ac.setFontColor(label, 1, 1-colorFactor, 1-colorFactor, 1)
                if deltaApp:
                    deltaApp.setColor(1, 1-colorFactor, 1-colorFactor, 1, isPB)
            else:
                # color factor [0..1]
                colorFactor = float(delta)/greenAt
                ac.setFontColor(label, 1-colorFactor, 1, 1-colorFactor, 1)
                if deltaApp:
                    deltaApp.setColor(1-colorFactor, 1, 1-colorFactor, 1, isPB)


def explodeCSL(string, sep=','):
    return list(map(str.strip, string.split(sep)))


def onClickDriver(*args):
    # Callbacks must be first-order functions in the main file :-/
    global currentDriver
    currentDriver = cycleDriver(driversList, currentDriver)
    writeParameters()
    partyLapsApp.setDriverCellValues()
    partyLapsApp.setPersonalBestCellValues()
    return 1


def cycleDriver(drivers, currentDriver):
    """
    Return the next driver in the drivers list, or the first driver if it is
    not found.
    """
    if not drivers:
        return ""
    returnNow = False
    for driver in drivers:
        if returnNow:
            return driver
        if driver == currentDriver:
            returnNow = True
    return drivers[0]


def calculateDelta(position, currentTime, lapData):
    """
    Calculate the delta to the reference data.
    """
    # If there is a best lap, calculate the interpolation
    if len(lapData):

        # Check where is our actual position in the best lap data
        index = 0
        while position > lapData[index][0]:
            index += 1

        if index == 0:
            return 0
        else:
            # Interpolation
            bestLapDeltaPos  = lapData[index][0] - lapData[index-1][0]
            bestLapDeltaTime = lapData[index][1] - lapData[index-1][1]
            currentDeltaPos  = position - lapData[index-1][0]
            currentDeltaTime = currentDeltaPos*bestLapDeltaTime/bestLapDeltaPos
            return currentTime - lapData[index-1][1] - currentDeltaTime
    else:
        # No best lap, no performance delta.
        return 0
