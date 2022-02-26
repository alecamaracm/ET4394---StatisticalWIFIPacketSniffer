import redis
import configs
import os

#Devicename 
FILEPATH = r"C:/Users/Maksym/Desktop/Master/Q3/ET4394 Wireless IoT and LAN/DataAnalysis/BackupTxtFiles/"

#Get all the data from the Redis server
def getCurrentData():
    print("Extracting the current data from the server")
    rserver = redis.Redis(host=configs.HOST , port=configs.PORT, password=configs.PASSWORD, decode_responses=True)

    for key in rserver.scan_iter("TUDelftDeviceData|" + "*"):
        data = rserver.get(key)
        keyString = str(key.replace("|", "_"))
        if(os.path.isfile(FILEPATH + keyString + ".txt")):
            print(".")
        else:
            f = open(FILEPATH + keyString + ".txt", 'w')
            f.write(data)
            print("Added a file!")

def main():   
    getCurrentData()
    
if __name__ == "__main__":
    main()
    