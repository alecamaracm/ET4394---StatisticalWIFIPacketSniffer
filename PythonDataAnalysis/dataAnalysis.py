from lib2to3.pgen2.token import NEWLINE
import redis
import configs
import dataFrame
from datetime import datetime
import plotly.express as px
import pandas as pd

allSeenMacAdresses = []
totalSeenMacAdresses = []

#Get all the data from the Redis server
def getCurrentData():
    print("Extracting the current data from the server")
    rserver = redis.Redis(host=configs.HOST , port=configs.PORT, password=configs.PASSWORD, decode_responses=True)
    #keyVal = configs.DEVICENAME + "1644727698921"

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

def plotFigureMacadresses():
    sortedList = sorted(totalSeenMacAdresses, key=lambda d: d['timestamp'])                                                     #sort the list based on the unixtimestamp
    print(len(sortedList))
    df = pd.DataFrame(data=sortedList)
    fig = px.line(df, x="date", y="amountOfMacs", title='Amount of Macs per timestamp')
    fig.show()

def main():   
    getCurrentData()
    plotFigureMacadresses()
    print(totalSeenMacAdresses)

if __name__ == "__main__":
    main()