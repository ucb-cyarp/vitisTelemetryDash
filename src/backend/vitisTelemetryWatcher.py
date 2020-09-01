#!/usr/bin/python3

import argparse
import json
from xmlrpc.server import SimpleXMLRPCServer
import threading
import time

currentItter = 0
partitions = []
updatingLock = threading.Semaphore() #used to lock access durring update (investigate need for this.  May be able to get away without doing this since single reader and single producer.  Requires that the index update occur after the lists are modified.  Also not sure what would happen if the list is moved internally)
history = [] #There is an entry for each partition.  Each entry is a structure of time and percentage values
itterToIndex = [] #This is used to refer to what index in the internal history arrays correspond

period = 100 #in ms
telemFiles = []
computeTimeMetricName = ''
totalTimeMetricName = ''
timestampSecName = ''
timestampNSecName = ''
rateMSPSName = ''
waitingForInputFIFOsName = ''
readingInputFIFOsName = ''
waitingForOutputFIFOsName = ''
writingOutputFIFOsName = ''
telemetryMiscName = ''
telemPath = ''
designName = ''

#Internal structure for storing the history of performance metrics for 
class History:
    def __init__(self):
        self.computePercent = []
        self.waitingForInputFIFOsPercent = []
        self.readingInputFIFOsPercent = []
        self.waitingForOutputFIFOsPercent = []
        self.writingOutputFIFOsPercent = []
        self.telemetryMiscPercent = []
        self.time = []
        self.rate = []

#Class for passing the history of compute utilization (percent time waiting for compute to finish) and rate to the dashboard over RPC
class RPCHistory:
    def __init__(self):
        self.percent = []
        self.time = []
        self.rate = []

class ComputeStatPoint:
    def __init__(self):
        self.computePercent = 0.0
        self.waitingForInputFIFOsPercent = 0.0
        self.readingInputFIFOsPercent = 0.0
        self.waitingForOutputFIFOsPercent = 0.0
        self.writingOutputFIFOsPercent = 0.0
        self.telemetryMiscPercent = 0.0

def getPartitions():
    #No need to aquire the lock, this does not change after init
    return partitions

def getItter():
    updatingLock.acquire()
    rtnItter = currentItter
    updatingLock.release()
    return rtnItter

def getComputeTimePercent(itter):
    vals = []

    updatingLock.acquire()

    for i in range(0, len(partitions)):
        ind = itterToIndex[i][itter]
        vals.append(history[i].computePercent[ind])

    updatingLock.release()
    return vals

def getCurrentStats(itter):
    vals = []

    updatingLock.acquire()

    for i in range(0, len(partitions)):
        ind = itterToIndex[i][itter]
        statPoint = ComputeStatPoint()
        statPoint.computePercent = history[i].computePercent[ind]
        statPoint.waitingForInputFIFOsPercent = history[i].waitingForInputFIFOsPercent[ind]
        statPoint.readingInputFIFOsPercent = history[i].readingInputFIFOsPercent[ind]
        statPoint.waitingForOutputFIFOsPercent = history[i].waitingForOutputFIFOsPercent[ind]
        statPoint.writingOutputFIFOsPercent = history[i].writingOutputFIFOsPercent[ind]
        statPoint.telemetryMiscPercent = history[i].telemetryMiscPercent[ind]
        vals.append(statPoint)

    updatingLock.release()
    return vals

#Gets the history of CPU utilization (percent waiting for compute) and rate
def getHistory(partitionInd, itter, timeRangeSec):
    updatingLock.acquire()

    endInd = itterToIndex[partitionInd][itter]
    endTime = history[partitionInd].time[endInd]

    tgtStartTime = endTime - timeRangeSec

    # print('Tgt Start Time: ' + str(tgtStartTime) + ' End time: ' + str(endTime))
    
    #Find the start of the interval
    startInd = endInd-1
    foundEnd = False
    while not foundEnd:
        if startInd < 0:
            #Reached the beginning of the history before finding the beginning of the time range we were interested in
            startInd = 0
            foundEnd = True
        elif history[partitionInd].time[startInd] > tgtStartTime:
            #Still looking
            startInd = startInd - 1
        else:
            #Found it
            foundEnd = True
    

    hist = RPCHistory()
    hist.percent = []
    hist.time = []
    hist.rate = []

    for i in range(startInd, endInd+1):
        hist.percent.append(history[partitionInd].computePercent[i])
        hist.rate.append(history[partitionInd].rate[i])
        hist.time.append(history[partitionInd].time[i])

    updatingLock.release()
    return hist

def getDesignName():
    return designName

def watchTelem():
    global currentItter

    #Open files
    fileHandles = []
    firstLine = []

    computeTimeMetricInd = []
    totalTimeMetricInd = []
    timestampSecInd = []
    timestampNSecInd = []
    rateMSPSInd = []
    waitingForInputFIFOsInd = []
    readingInputFIFOsInd = []
    waitingForOutputFIFOsInd = []
    writingOutputFIFOsInd = []
    telemetryMiscInd = []

    for i in range(0, len(partitions)):
        try:
            telemFileHandle = open(telemPath + '/' + telemFiles[i])
            fileHandles.append(telemFileHandle)
        except Exception as err:
            print('Error encountered when reading telem file: ' + telemPath + '/' + telemFiles[i])
            print(err)
            exit(1)
        firstLine.append(True)
        computeTimeMetricInd.append(0)
        totalTimeMetricInd.append(0)
        timestampSecInd.append(0)
        timestampNSecInd.append(0)
        rateMSPSInd.append(0)
        waitingForInputFIFOsInd.append(0)
        readingInputFIFOsInd.append(0)
        waitingForOutputFIFOsInd.append(0)
        writingOutputFIFOsInd.append(0)
        telemetryMiscInd.append(0)

    while True:
        changed = False
        updatingLock.acquire()
        for i in range(0, len(partitions)):
            reading = True
            while reading:
                line = fileHandles[i].readline()
                tokenized = line.split(',')
                if line:
                    if firstLine[i]:
                        #this is the first line in the telemetry file
                        for token in range(0, len(tokenized)):
                            tokenStr = tokenized[token].strip()
                            if tokenStr == computeTimeMetricName:
                                computeTimeMetricInd[i] = token
                            elif tokenStr == totalTimeMetricName:
                                totalTimeMetricInd[i] = token
                            elif tokenStr == timestampSecName:
                                timestampSecInd[i] = token
                            elif tokenStr == timestampNSecName:
                                timestampNSecInd[i] = token
                            elif tokenStr == rateMSPSName:
                                rateMSPSInd[i] = token
                            elif tokenStr == waitingForInputFIFOsName:
                                waitingForInputFIFOsInd[i] = token
                            elif tokenStr == readingInputFIFOsName:
                                readingInputFIFOsInd[i] = token
                            elif tokenStr == waitingForOutputFIFOsName:
                                waitingForOutputFIFOsInd[i] = token
                            elif tokenStr == writingOutputFIFOsName:
                                writingOutputFIFOsInd[i] = token
                            elif tokenStr == telemetryMiscName:
                                telemetryMiscInd[i] = token
                        firstLine[i] = False
                    else:
                        changed = True
                        timestamp = int(tokenized[timestampSecInd[i]].strip()) + int(tokenized[timestampNSecInd[i]].strip()) * 1e-9
                        computeTime = float(tokenized[computeTimeMetricInd[i]].strip()) 
                        totalTime = float(tokenized[totalTimeMetricInd[i]].strip())
                        rateMSPS = float(tokenized[rateMSPSInd[i]].strip())

                        waitingForInputFIFOs = float(tokenized[waitingForInputFIFOsInd[i]].strip())
                        readingInputFIFOs = float(tokenized[readingInputFIFOsInd[i]].strip())
                        waitingForOutputFIFOs = float(tokenized[waitingForOutputFIFOsInd[i]].strip())
                        writingOutputFIFOs = float(tokenized[writingOutputFIFOsInd[i]].strip())
                        telemetryMisc = float(tokenized[telemetryMiscInd[i]].strip())

                        percentCompute = 0
                        percentWaitingForInputFIFOs = 0
                        percentReadingInputFIFOs = 0
                        percentWaitingForOutputFIFOs = 0
                        percentWritingOutputFIFOs = 0
                        percentTelemetryMisc = 0
                        if totalTime != 0:#handle the startup case
                            percentCompute = computeTime / totalTime * 100
                            percentWaitingForInputFIFOs = waitingForInputFIFOs / totalTime * 100
                            percentReadingInputFIFOs = readingInputFIFOs / totalTime * 100
                            percentWaitingForOutputFIFOs = waitingForOutputFIFOs / totalTime * 100
                            percentWritingOutputFIFOs = writingOutputFIFOs / totalTime * 100
                            percentTelemetryMisc = telemetryMisc / totalTime * 100

                        # print(str(i) + ' | Timestamp: ' + str(timestamp) + ' Percent Compute: ' + str(percentCompute) + ' Compute Time: ' + str(computeTime) + ', Total Time: ' + str(totalTime))

                        history[i].computePercent.append(percentCompute)
                        history[i].rate.append(rateMSPS)
                        history[i].time.append(timestamp)
                        history[i].waitingForInputFIFOsPercent.append(percentWaitingForInputFIFOs)
                        history[i].readingInputFIFOsPercent.append(percentReadingInputFIFOs)
                        history[i].waitingForOutputFIFOsPercent.append(percentWaitingForOutputFIFOs)
                        history[i].writingOutputFIFOsPercent.append(percentWritingOutputFIFOs)
                        history[i].telemetryMiscPercent.append(percentTelemetryMisc)
                else:
                    reading = False

        if changed:
            print('Changed!')
            currentItter = currentItter+1
            for i in range(0, len(partitions)):
                itterToIndex[i].append(len(history[i].time)-1)

        #TODO: Limit the size of history, for now it is slow enough that it is not a problem for a practical demo
        #Needs to be done while still allowing itterations to increment (or wrapping itterations at some point)
        #Needs to be coordinated with the dashboard so that that the limited window is not exceed (plus some error checks here)

        updatingLock.release()
        time.sleep(period/1000)

def setup():
    rpcHost = 'localhost'
    rpcPort = 8090

    #Parse CLI Arguments for Config File Location
    parser = argparse.ArgumentParser(description='Start vitis telemetry dashboard')
    parser.add_argument('--config', type=str, required=True, help='Path to the telemetry configuration JSON file')
    parser.add_argument('--telem-path', type=str, required=True, help='Path to the telemetry files referenced in the configuration JSON file')
    args = parser.parse_args()

    print(args)

    #Load the Config Json file.
    #This file contains information about the application incuding
    #   * Name
    #   * IO Thread Telemetry File Location (if applicable)
    #   * Compute Thread Telemetry File Locations
    #   * Column Label of Compute Time Metric
    #   * Column Label of Total Time Metric
    #   * Partition To CPU Number Mapping
    #   * Generation Report Files (if applicable)
    #        - Schedule GraphML file (if applicable)
    #        - Communication Report
    #        - Computation Report
    #   

    global telemPath
    telemPath = args.telem_path

    configFile = None
    try:
        configFile = open(args.config)
    except Exception as err:
        print('Error encountered when reading config file')
        print(err)
        exit(1)

    #Parse the XML File
    telemConfig = json.load(configFile)
    configFile.close()

    #Get an array of compute threads
    for computePartStr, telemFileLoc in telemConfig["computeTelemFiles"].items(): #https://stackoverflow.com/questions/3294889/iterating-over-dictionaries-using-for-loops
        partitions.append(int(computePartStr))
        telemFiles.append(telemFileLoc)

        #Create a history object for each compute thread
        history.append(History())

        itterToIndex.append([0]) #this is a dummy entry

    print(telemFiles)

    #Get headers
    global computeTimeMetricName
    global totalTimeMetricName
    global timestampSecName
    global timestampNSecName
    global rateMSPSName
    global designName
    global waitingForInputFIFOsName
    global readingInputFIFOsName
    global waitingForOutputFIFOsName
    global writingOutputFIFOsName
    global telemetryMiscName

    computeTimeMetricName = telemConfig['computeTimeMetricName']
    totalTimeMetricName = telemConfig['totalTimeMetricName']
    timestampSecName = telemConfig['timestampSecName']
    timestampNSecName = telemConfig['timestampNSecName']
    rateMSPSName = telemConfig['rateMSPSName']
    designName = telemConfig['name']
    waitingForInputFIFOsName = telemConfig['waitingForInputFIFOsMetricName']
    readingInputFIFOsName = telemConfig['readingInputFIFOsMetricName']
    waitingForOutputFIFOsName = telemConfig['waitingForOutputFIFOsMetricName']
    writingOutputFIFOsName = telemConfig['writingOutputFIFOsMetricName']
    telemetryMiscName = telemConfig['telemetryMiscMetricName']

    #Can parse telemetry in single thread since it looks like file readline is non-blocking if the file is not a stream (stdio or pipe)
    #Creating a new thread so it can go to sleep between updates (not shure if this is nessisary - would be if RPC server runs in this thread)
    watcher = threading.Thread(target = watchTelem)
    watcher.start()

    server = SimpleXMLRPCServer((rpcHost, rpcPort))
    print('Listening on port ' + str(rpcPort) + '...')

    #For the telemetry files, we read them line by line

    server.register_function(getPartitions, "getPartitions")
    server.register_function(getItter, "getItter")
    server.register_function(getComputeTimePercent, "getComputeTimePercent")
    server.register_function(getCurrentStats, "getCurrentStats")
    server.register_function(getHistory, "getHistory")
    server.register_function(getDesignName, "getDesignName")
    server.serve_forever()

if __name__ == '__main__':
    setup()