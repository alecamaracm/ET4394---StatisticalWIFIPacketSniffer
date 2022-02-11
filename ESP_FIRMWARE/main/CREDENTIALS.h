//WIFI

#define WIFI_SSID "testSSID"

//Comment this line if you would like to use a normal WiFi network
//#define USE_EDUORAM

#ifdef USE_EDUORAM
    #define WIFI_EDU_USERNAME "testUsername"
    #define WIFI_EDU_PASSWORD "testPassword"
#else
    #define WIFI_PASS "testPassword"
#endif




//REDIS
#define REDIS_HOST_IP "95.179.129.52"
#define REDIS_HOST_PORT 6379
#define REDIS_PASSWORD "wowThisIsAVeryHardPasswordThatNoOneWouldBeAbleToFind69*"





//GENERAL SETTINGS
#define DEVICE_NAME "testALE1"

#define MAX_MAC_COUNT 1000

#define TIME_WORKING_MS 10000 //60 seconds = 1 mins
#define TIME_SLEEPING_MS 30000 //240 seconds = 4mins