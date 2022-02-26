import redis
import configs
import os

#Devicename 
#FILEPATH = r"C:/Users/Maksym/Desktop/Master/Q3/ET4394 Wireless IoT and LAN/DataAnalysis/BackupTxtFiles/"

#Get all the data from the Redis server
def getCurrentData():
    print("Extracting the current data from the server")
    rserver = redis.Redis(host=configs.HOST , port=configs.PORT, password=configs.PASSWORD, decode_responses=True)

    for key in rserver.scan_iter("TUDelftDeviceData|" + "*"):
        data = rserver.get(key)
        if(os.path.isfile(str(key) + ".txt")):
            print(os.path.isfile(str(key) + ".txt"))
            break
        else:
            print(os.path.isfile(str(key) + ".txt"))
            f = open("a" + ".txt", 'w+')
            f.write(data)

def main():   
    getCurrentData()
    
if __name__ == "__main__":
    main()
    