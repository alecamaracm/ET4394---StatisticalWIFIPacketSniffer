#define WIFI_SSID "testSSID"

//Comment this line if you would like to use a normal WiFi network
//#define USE_EDUORAM

#ifdef USE_EDUORAM
    #define WIFI_EDU_USERNAME "testUsername"
    #define WIFI_EDU_PASSWORD "testPassword"
#else
    #define WIFI_PASS "testPassword"
#endif

