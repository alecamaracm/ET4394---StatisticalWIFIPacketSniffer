from cgitb import small
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
import sys
import plotly.figure_factory as ff

allSeenMacAdresses = []
totalSeenMacAdresses = []
smallestValue = 100000000000000
highestValue = 0

#Get all the data from the Redis server
def getCurrentData():
    print("Extracting the current data from the server")
    rserver = redis.Redis(host=configs.HOST , port=configs.PORT, password=configs.PASSWORD, decode_responses=True)
    global smallestValue
    global highestValue
    #Extract the values from the server and place them in a data container
    for key in rserver.scan_iter(configs.DEVICENAME + "*"):
        timestamp = str(int(key.split('|')[2]) + configs.OFFSETTIME) 
        data = rserver.get(key) 
        dataLines = data.splitlines()
        #print(timestamp)
        if(int(timestamp)/1000 > 1645401601):
            try:
                
                totalSeenMacAdresses.append({"timestamp":int(timestamp), "date": convertUnix(timestamp), "amountOfMacs": int(dataLines[0])})                   #Add the total amount of macs seen in that time stamp to the data container
            except:
                print("Error in txt file!")
            i = 0

            #Getting highest and lowest value
            if(int(timestamp) < int(smallestValue)):
                smallestValue = int(timestamp)
            if(int(timestamp) > int(highestValue)):
                highestValue = int(timestamp)

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

def convertUnixHour(time):
    datetime_obj = datetime.utcfromtimestamp(int(time)/1000)                                                                    #devide by 1000 because of milli
    return datetime_obj.strftime("%d.%m.%y %H")

def convertUnixDay(time):
    datetime_obj = datetime.utcfromtimestamp(int(time)/1000)                                                                    #devide by 1000 because of milli
    return datetime_obj.strftime("%d.%m.%y")


#Return true when value is in dictionary False when its not the case
def checkIfValueInListOfDict(listOfDicts, value):
    if(len(listOfDicts) == 0):
        return False
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
    return -1

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

    """ global smallestValue
    global highestValue
    smallestValue 
    UTCDays = []
    days = []
    dayValues = []
    i = 0
    while(smallestValue < highestValue):
        UTCDays.append(smallestValue + configs.BIN)
        days.append(convertUnixDay(smallestValue))
        dayValues.append(0)
        smallestValue += configs.BIN
        i += 1
        print(i)
    print(UTCDays)
    print(days)
    print(dayValues) """

    if(configs.DEVICENAME == "TUDelftDeviceData|App"):
        UTCDays = [1645484401, 1645570801, 1645657201, 1645743601,1645830001, 1645916401, 1646002801, 1646089201, 1646175601, 1646262001]
        days = ["21-02-2022","22-02-2022","23-02-2022","24-02-2022","25-02-2022","26-02-2022","27-02-2022","28-02-2022","01-03-2022","02-03-2022"]
        dayValues = [0,0,0,0,0,0,0,0,0,0]
    else:
        UTCDays = [1645570801, 1645657201, 1645743601, 1645830001, 1645916401, 1646002801, 1646089201, 1646175601, 1646262001, 1646348401, 1646434801, 1646521201]
        days = ["22-02-2022", "23-02-2022", "24-02-2022", "25-02-2022", "26-02-2022", "27-02-2022", "28-02-2022", "01-03-2022", "02-03-2022", "03-03-2022", "04-03-2022", "05-03-2022"]
        dayValues = [0,0,0,0,0,0,0,0,0,0,0,0]
        print("hello")

    for element in sortedList:
        if (element.get("timestamp")/1000 > 1645401601):
            dates.append(element["date"])
            amountOfMacs.append(element["amountOfMacs"])
        if listOfSpecialTimes:
            if(str(element["timestamp"]) in listOfSpecialTimes and element.get("timestamp")/1000 > 1645401601):
                specialPoints.append(element["amountOfMacs"])
                specialDates.append(element["date"])
        i = 0        
        for UTC in UTCDays:
            if(element.get("timestamp")/1000 < UTC and element.get("timestamp")/1000 > 1645401601):   
                dayValues[i] = dayValues[i] + element.get("amountOfMacs")
                break
            i += 1

    #movingAverageList = movingAverage(amountOfMacs) 

    fig = px.bar(x =days, y =dayValues, text_auto='.2s',
                title="Amount of Macs per day")
    fig.update_traces(textangle=0, textfont_size=14, textposition="outside", cliponaxis=False)
    fig.update_layout(xaxis_title='Day', yaxis_title='Amount of MAC adresses')
    fig.show()

    #fig = go.Figure()
    #fig.add_trace(go.Scatter(x=days, y=dayValues, mode='lines+markers', name='Amount of Mac adresses seen per day'))
    #fig.update_layout(title="Amount of Mac adressess seen per day", xaxis_title='Day', yaxis_title='Amount of MAC adresses')
    #fig.show() 

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=amountOfMacs, mode='lines+markers', name='Amount of MAC adresses', line=dict(color="#7876ff")))
    #fig.add_trace(go.Scatter(x=dates, y=movingAverageList, mode='lines', name='SMA Amount of MAC adresses'))
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
    print(listOfVendors)
    fig = px.bar(listOfVendors, y='Amount', x='Vendor', text_auto='.2s',
                title="Amount of vendors thast were found")
    fig.update_traces(textangle=0, textfont_size=14, textposition="outside", cliponaxis=False)
    fig.show()

def makeDistribution():
    distributionData = []
    print(len(allSeenMacAdresses))
    ones = 0
    for macDict in allSeenMacAdresses:
        amountSeen = int(len(macDict.allTimeFrames))
        addElement = True
        #print("amountseen = : " + str(amountSeen))
        index = indexOfSearchedDict(distributionData,"TimesSeen",amountSeen)
        if(index != -1):
            #print("Index is : " + str(indexOfSearchedDict(distributionData,"TimesSeen",amountSeen)))
            #print(distributionData)
            distributionData[index]["Amount"] = int(distributionData[index].get("Amount") + 1)
            addElement = False
        if(addElement and amountSeen != 1):
            newDict = {"TimesSeen": amountSeen, "Amount": int(1)}
            distributionData.append(newDict)
    print(distributionData)
    df = distributionData

    fig = px.histogram(df, x="TimesSeen", y = "Amount")

    fig.show()

def main():   
    getCurrentData()
    listOfSpecialTimes = getTimeStampsSpecialMac()
    plotFigureMacadresses(listOfSpecialTimes)
    #plotFigureDataPerTimeStamp()
    #printVendorSpecs()
    makeDistribution()
    
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