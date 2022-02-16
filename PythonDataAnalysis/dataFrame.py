class DataFrame:
    def __init__(self, macadress, timestamp, mngpktCntTx, mngpktCntRx, datapktCntTx, datapktCntRx, dataPktTotalSizeTx, dataPktTotalSizeRx):
        self.MACadress = macadress
        self.allTimeFrames =[]
        newDict = {
            "timestamp": timestamp,
            "mngpktCntTx":mngpktCntTx,
            "mngpktCntRx":mngpktCntRx,
            "datapktCntTx":datapktCntTx,
            "datapktCntRx":datapktCntRx,
            "dataPktTotalSizeTx":dataPktTotalSizeTx,
            "dataPktTotalSizeRx":dataPktTotalSizeRx
        }
        self.allTimeFrames.append(newDict)

    #If the macadress instance already exists a new timestamp can be added to the existing ones
    def addTimeFrame(self, timestamp, mngpktCntTx, mngpktCntRx, datapktCntTx, datapktCntRx, dataPktTotalSizeTx, dataPktTotalSizeRx):
        newDict = {
            "timestamp": timestamp,
            "mngpktCntTx":mngpktCntTx,
            "mngpktCntRx":mngpktCntRx,
            "datapktCntTx":datapktCntTx,
            "datapktCntRx":datapktCntRx,
            "dataPktTotalSizeTx":dataPktTotalSizeTx,
            "dataPktTotalSizeRx":dataPktTotalSizeRx
        }
        self.allTimeFrames.append(newDict)

    #Retreive a specific timeframe from this macdevice
    def getTimeFrame(self, timestamp):
        for dict in self.addTimeFrame:
            if(dict["timestamp"]) == timestamp:
                return dict
        return False

