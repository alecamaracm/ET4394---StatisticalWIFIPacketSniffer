#Redis server configurations
HOST = "95.179.129.52"
PORT = 6379
PASSWORD = "hdaJA0ic6tVm7pxAZSofRugF4FPNFQVHQsQmsGQ2mB9d2eWvbSwEBhnGUbrhNATls9dQF0e8Z2tFzK4CZcpttoqzdSHMrCyIbcr"

#Device1 configuration settings
DEVICENAME = "TUDelftDeviceData|App"

#Special MACadress
specialMac = "4e:9b:05:55:9f:ce"

#Mobing averagefilter size
movingAverage = 5

#Offset the time with 1 hour because of timezone
OFFSETTIME = 3600000

#url to get specific vendor data
MACURL = "http:\\macvendors.co\api\%s"

#set size of the bins in microsecs 
BIN = 60 * 6 * 10^7