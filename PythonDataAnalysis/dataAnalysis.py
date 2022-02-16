import time
from turtle import color
import redis
import configs
import dataFrame
from datetime import datetime
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

allSeenMacAdresses = []
totalSeenMacAdresses = []

#Get all the data from the Redis server
def getCurrentData():
    print("Extracting the current data from the server")
    rserver = redis.Redis(host=configs.HOST , port=configs.PORT, password=configs.PASSWORD, decode_responses=True)

    #Extract the values from the server and place them in a data container
    for key in rserver.scan_iter(configs.DEVICENAME + "*"):
        timestamp = key.split('|')[2]
        data = rserver.get(key) 
        dataLines = data.splitlines()
        totalSeenMacAdresses.append({"timestamp":int(timestamp), "date": convertUnix(timestamp), "amountOfMacs": int(dataLines[0])})                   #Add the total amount of macs seen in that time stamp to the data container
        i = 0

        for line in dataLines:
            if(i > 1):                                                                                                          #first item is total amount of adress and second is own macadress, should be skipped here
                elements = line.split('|')
                MACadress = elements[0]
                if(any(mac.MACadress == MACadress for mac in allSeenMacAdresses)):                                              #Check if there already exists a mac object                             if(~any(frame.get("timestamp") == timestamp for frame in obj.allTimeFrames)):                               #only add new frame if the current timestamp is not already added
                    obj = next(item for item in allSeenMacAdresses if item.MACadress == MACadress) 
                    obj.addTimeFrame(timestamp, elements[1], elements[2], elements[3], elements[4], elements[5], elements[6])
                else:
                    newObj = dataFrame.DataFrame(MACadress, timestamp, elements[1], elements[2], elements[3], elements[4], elements[5], elements[6])
                    allSeenMacAdresses.append(newObj)     
            i += 1

#Method that can convert the unixtimestamp to normal time     
def convertUnix(time):
    datetime_obj = datetime.utcfromtimestamp(int(time)/1000)                                                                    #devide by 1000 because of milli
    return datetime_obj.strftime("%d.%m.%y %H:%M:%S")

#Return true when value is in dictionary False when its not the case
def checkIfValueInListOfDict(listOfDicts, value):
    for element in listOfDicts:
        if value in element.values():
            return True
    return False

#Search the index of a list of dictionaries with certain key value pair
def indexOfSearchedDict(listOfDicts, key, value):
    i = 0
    for element in listOfDicts:
        if element[key] == value:
            return i 
        i += 1

#Calculate the moving average on a given list and return the moving average list
def movingAverage(dataList):
    movingAverageList = []
    movingAverageList.append(dataList[0])
    total = 0
    for i in range(1,configs.movingAverage):
        total += dataList[i]
        movingAverageList.append(total/i)

    startIndex = 0
    endIndex = configs.movingAverage
    for i in range(configs.movingAverage, len(dataList)):
        SMAtot = 0
        for z in range(startIndex, endIndex):
            SMAtot += dataList[z]
        movingAverageList.append(SMAtot/configs.movingAverage)
        startIndex += 1
        endIndex += 1
    return movingAverageList

#Plot figure amountofMacs per timestamp, when the "special" mac adress is detected, its highlighted in the graph
def plotFigureMacadresses(listOfSpecialTimes):
    sortedList = sorted(totalSeenMacAdresses, key=lambda d: d['timestamp'])                                                     #sort the list based on the unixtimestamp
    dates, amountOfMacs, specialPoints, specialDates = [], [], [], []

    for element in sortedList:
        dates.append(element["date"])
        amountOfMacs.append(element["amountOfMacs"])
        if(str(element["timestamp"]) in listOfSpecialTimes):
            specialPoints.append(element["amountOfMacs"])
            specialDates.append(element["date"])
    movingAverageList = movingAverage(amountOfMacs) 

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=amountOfMacs, mode='lines+markers', name='Amount of MAC adresses', line=dict(color="#7876ff")))
    fig.add_trace(go.Scatter(x=dates, y=movingAverageList, mode='lines', name='SMA Amount of MAC adresses'))
    fig.add_trace(go.Scatter(x=specialDates, y=specialPoints, mode='markers', name='Special MAC Adres Was Seen'))
    fig.update_layout(title="Amount of Mac adressess seen per timestamp", xaxis_title='TimeStamp', yaxis_title='Amount of MAC adresses')
    fig.show()

#Method that returns a list of all the timeStamps the predetermined special mac adress was seen (for identifying unique user)
def getTimeStampsSpecialMac():
    if(any(mac.MACadress == configs.specialMac for mac in allSeenMacAdresses)):
        obj = next(item for item in allSeenMacAdresses if item.MACadress == configs.specialMac) 
        timeSeen = []
        for times in obj.allTimeFrames:
            timeSeen.append(times["timestamp"])
        return timeSeen
    else:
        print("The special Mac adress was never seen!")

#plot amount of traffic per timestamp
def plotFigureDataPerTimeStamp():
    sortedList = sorted(totalSeenMacAdresses, key=lambda d: d['timestamp'])   
    timeStampsList, dateList = [], []
    totDataPktCnt, totDataSize, totManagement = [], [], []
    
    for element in sortedList:
        timeStampsList.append(element["timestamp"])
        dateList.append(convertUnix(element["timestamp"]))        

    #loop through all the timestamps and add all the data from the objects
    for timeStamp in timeStampsList:
        totalData, totalSize, totalMng = 0, 0, 0 #1
        for MACObj in allSeenMacAdresses:
            if(checkIfValueInListOfDict(MACObj.allTimeFrames, str(timeStamp))):
                index = indexOfSearchedDict(MACObj.allTimeFrames, "timestamp", str(timeStamp))
                totalData += int(MACObj.allTimeFrames[index]["datapktCntTx"]) + int(MACObj.allTimeFrames[index]["datapktCntRx"]) 
                totalSize += int(MACObj.allTimeFrames[index]["dataPktTotalSizeTx"]) + int(MACObj.allTimeFrames[index]["dataPktTotalSizeRx"]) #2
                totalMng += int(MACObj.allTimeFrames[index]["mngpktCntTx"]) + int(MACObj.allTimeFrames[index]["mngpktCntRx"]) #2
        totDataPktCnt.append(totalData)
        totDataSize.append(totalSize) #3
        totManagement.append(totalMng) #3

    smaDataPkt = movingAverage(totDataPktCnt)
    smaDataSiz = movingAverage(totDataSize)
    smaMngmt = movingAverage(totManagement)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dateList, y=totDataSize, mode='lines', name='totSize')) #4
    fig.add_trace(go.Scatter(x=dateList, y=smaDataSiz, mode='lines', name='MA totSize')) #4
    fig.update_layout(title="Amount of data seen per timestamp", xaxis_title='TimeStamp', yaxis_title='Amount of data')
    fig.show()

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=dateList, y=totDataPktCnt, mode='lines', name='totData'))
    fig2.add_trace(go.Scatter(x=dateList, y=totManagement, mode='lines', name='totMng')) #4
    fig2.add_trace(go.Scatter(x=dateList, y=smaDataPkt, mode='lines', name='MA Data'))
    fig2.add_trace(go.Scatter(x=dateList, y=smaMngmt, mode='lines', name='MA Mng')) #4
    fig2.update_layout(title="Amount of data seen per timestamp", xaxis_title='TimeStamp', yaxis_title='Amount of data')
    fig2.show()

#Function that returns a list of buckets that represent certain window intervals
def bucketizeTimeStamps():
    print("Test")

def main():   
    getCurrentData()
    listOfSpecialTimes = getTimeStampsSpecialMac()
    plotFigureMacadresses(listOfSpecialTimes)
    plotFigureDataPerTimeStamp()
    #for obj in allSeenMacAdresses:
    #    print(obj.allTimeFrames)
        #for element in obj.allTimeFrames:
        #    print(element["datapktCntTx"])
    
if __name__ == "__main__":
    main()