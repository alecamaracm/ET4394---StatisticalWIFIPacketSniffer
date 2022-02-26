from os import times
import time
from turtle import color
from xml.etree.ElementTree import ElementTree
import redis
import configs
import dataFrame
from datetime import datetime
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import requests
from mac_vendor_lookup import MacLookup
import json

allSeenMacAdresses = []
totalSeenMacAdresses = []

#Get all the data from the Redis server
def getCurrentData():
    print("Extracting the current data from the server")
    rserver = redis.Redis(host=configs.HOST , port=configs.PORT, password=configs.PASSWORD, decode_responses=True)

    #Extract the values from the server and place them in a data container
    for key in rserver.scan_iter(configs.DEVICENAME + "*"):
        timestamp = str(int(key.split('|')[2]) + configs.OFFSETTIME) 
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
        if listOfSpecialTimes:
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

    #method for plotting new seen macadresses called here because the timestamplist is needed
    plotTotalNewMacAdresses(timeStampsList, dateList)

#method that plots all the new seen mac adresses per timestamp
def plotTotalNewMacAdresses(timeStampList, dateList):
    listOfMacAdressFirstSeen = []
    numberOfNewMacs = []
    
    for MAC in allSeenMacAdresses:
        newDict = {"MAC": MAC.MACadress, "FirstSeen": int(MAC.allTimeFrames[0].get("timestamp"))}
        for frame in MAC.allTimeFrames:
            if(int(frame.get("timestamp")) < newDict.get("FirstSeen")):
                newDict["FirstSeen"] = int(frame.get("timestamp"))
        listOfMacAdressFirstSeen.append(newDict)

    newMacs = 0
    for timeStamp in timeStampList:
        for dict in listOfMacAdressFirstSeen:
            if(dict["FirstSeen"] == int(timeStamp)):
                newMacs += 1
        numberOfNewMacs.append(newMacs)
    print(timeStampList[0])
    print(timeStampList[-1])
    print(len(timeStampList))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dateList, y=numberOfNewMacs, mode='lines', name='new seen MAC adresses')) 
    fig.update_layout(title="Amount of new seen MAC adresses per timestamp", xaxis_title='TimeStamp', yaxis_title='new Mac adresses')
    fig.show()

#Get specific vendor data from mac adresses, which resides in a lookuptable and throws exception when it couldnt find a mac adress
#Takes 
def printVendorSpecs():
    listOfVendors, name, size = [], [], []
    listOfVendors.append({'Vendor':"No vendor", "Amount": 0})
    
    for adress in allSeenMacAdresses:
        try:
            vendor = MacLookup().lookup(str(adress.MACadress))
            addDict = True
            for item in listOfVendors:
                if(item.get('Vendor') == vendor):
                    item['Amount'] = item.get('Amount') + 1
                    addDict = False
                    break
            if(addDict):
                newdict = {'Vendor': vendor, 'Amount': 1}
                listOfVendors.append(newdict)

            listOfVendors[0]['Amount']  = listOfVendors[0].get('Amount') + 1
        except:
            listOfVendors[0]['Amount']  = listOfVendors[0].get('Amount') + 1

    fig = px.bar(listOfVendors, y='Amount', x='Vendor', text_auto='.2s',
                title="Default: various text sizes, positions and angles")
    fig.update_traces(textangle=0, textfont_size=14, textposition="outside", cliponaxis=False)
    fig.show()
    
def main():   
    getCurrentData()
    listOfSpecialTimes = getTimeStampsSpecialMac()
    plotFigureMacadresses(listOfSpecialTimes)
    plotFigureDataPerTimeStamp()
    #printVendorSpecs()
    
if __name__ == "__main__":
    main()





    """   for adress in allSeenMacAdresses:
        r = requests.get('http://macvendors.co/api/%s' % str(adress.MACadress))
        #print(r.json())
        #print(r.status_code)
        try:
            if('error' not in r.json()['result']):
                vendor = r.json()['result']['company']
                addDict = True
                for item in listOfVendors:
                    if(item.get('Vendor') == vendor):
                        item['Amount'] = item.get('Amount') + 1
                        addDict = False
                        break
                if(addDict):
                    newdict = {'Vendor':vendor, 'Amount': 1}
                    listOfVendors.append(newdict)    

            else:
                listOfVendors[0]['Amount']  = listOfVendors[0].get('Amount') + 1
            i += 1
            print(i)
        except:
            print("an error?")  """

""" 
#Plot figure amountofMacs per timestamp, when the "special" mac adress is detected, its highlighted in the graph
def plotFigureMacadresses(listOfSpecialTimes):
sortedList = sorted(totalSeenMacAdresses, key=lambda d: d['timestamp'])                                                     #sort the list based on the unixtimestamp
    dates, amountOfMacs, specialPoints, specialDates = [], [], [], []
    time = sortedList[0].get("timestamp") + configs.BIN
    adresses = 0

    for element in sortedList:
        if(element.get("timestamp") < time):
            adresses += element.get("amountOfMacs") 
        else:
            dates.append(convertUnix(time - 0.5 * configs.BIN))
            amountOfMacs.append(adresses)
            adresses = 
        dates.append(element["date"])
        amountOfMacs.append(element["amountOfMacs"])
        if listOfSpecialTimes:
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
  """