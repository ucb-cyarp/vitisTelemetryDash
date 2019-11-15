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
itterToIndex = [] #This is used to refer to what index in the internall history arrays correspond

period = 100 #in ms
telemFiles = []
computeTimeMetricName = ''
totalTimeMetricName = ''
timestampSecName = ''
timestampNSecName = ''
telemPath = ''

class History:
    def __init__(self):
        self.computePercent = []
        self.time = []

class RPCHistory:
    def __init__(self):
        self.percent = []
        self.time = []


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

def getComputeTimePercentHistory(partitionInd, itter, timeRangeSec):
    updatingLock.acquire()

    endInd = itterToIndex[partitionInd][itter]
    endTime = history[partitionInd].time[endInd]

    tgtStartTime = endTime - timeRangeSec
    
    #Find the start of the interval
    startInd = endInd-1
    foundEnd = False
    while not foundEnd:
        if startInd < 0:
            #Reached the beginning of the history before finding the beginning of the time range we were interested in
            startInd = 0
            foundEnd = True
        elif history[partitionInd].time[endInd] > tgtStartTime:
            #Still looking
            startInd = startInd - 1
        else:
            #Found it
            foundEnd = True
    

    hist = RPCHistory()
    hist.percent = []
    hist.time = []

    for i in range(startInd, endInd+1):
        hist.percent.append(history[partitionInd].computePercent[i])
        hist.time.append(history[partitionInd].time[i])

    updatingLock.release()
    return hist

def watchTelem():
    global currentItter

    #Open files
    fileHandles = []
    firstLine = []

    computeTimeMetricInd = []
    totalTimeMetricInd = []
    timestampSecInd = []
    timestampNSecInd = []

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
                        firstLine[i] = False
                    else:
                        changed = True
                        timestamp = int(tokenized[timestampSecInd[i]].strip()) + int(tokenized[timestampNSecInd[i]].strip()) * 1e-9
                        computeTime = float(tokenized[computeTimeMetricInd[i]].strip()) 
                        totalTime = float(tokenized[totalTimeMetricInd[i]].strip())
                        percentCompute = 0
                        if totalTime != 0:#handle the startup case
                            percentCompute = computeTime / totalTime * 100

                        print(str(i) + ' | Timestamp: ' + str(timestamp) + ' Percent Compute: ' + str(percentCompute) + ' Compute Time: ' + str(computeTime) + ', Total Time: ' + str(totalTime))

                        history[i].computePercent.append(percentCompute)
                        history[i].time.append(timestamp)
                else:
                    reading = False

        if changed:
            print('Changed!')
            currentItter = currentItter+1
            for i in range(0, len(partitions)):
                itterToIndex[i].append(len(history[i].time)-1)

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
    computeTimeMetricName = telemConfig['computeTimeMetricName']
    totalTimeMetricName = telemConfig['totalTimeMetricName']
    timestampSecName = telemConfig['timestampSecName']
    timestampNSecName = telemConfig['timestampNSecName']

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
    server.register_function(getComputeTimePercentHistory, "getComputeTimePercentHistory")
    server.serve_forever()

if __name__ == '__main__':
    setup()