#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"

#include "CREDENTIALS.h"
#include "RedisFunctions.h"
#include <driver/adc.h>
#include "time.h"

void GoToSleep();

char keyToSend[256];
char valueToAppend[1024];

////////////////////////// INTERNAL WIFI STRUCTURE //////////////////////
struct wifi_packet{
	unsigned frame_control:16;
	unsigned duration_or_id:16;
	uint8_t addrRX[6];
	uint8_t addrTX[6];
	uint8_t addrFILT[6];
	unsigned seq_control:16;
    uint8_t addrOPT[6];
    uint8_t payload[0]; //CHECKSUM IS THE LAST 4 BYTES    
};
///////////////////////////////////////////////////////////////////////////////////////////

extern bool WiFiConnected;
bool recordDataEnabled=false;

struct mac_data{
    uint8_t mac[6]; //Data about this MAC
    unsigned int managementPacketCountTX; //Number of management packets sent
    unsigned int managementPacketCountRX; //Number of management packets received
    unsigned int dataPacketCountTX; //Number of data packets sent
    unsigned int dataPacketCountRX; //Number of data packets received
    uint64_t dataPacketTotalSizeTX; //Total size (bytes) of data packets sent
    uint64_t dataPacketTotalSizeRX; //Total size (bytes) of data packets received
    bool blockUsed; //whether this MAC storage block is being used
};



struct mac_data MACsSEEN[MAX_MAC_COUNT];

//Finds the right storage block for the specified MAC. If it could not find one, returns false
bool FindMACStorageStruct(uint8_t* macPtr,struct mac_data** blockAddress){
    struct mac_data* currentPtr = MACsSEEN;
    int count=0;
    while(count < MAX_MAC_COUNT){
        if(memcmp(currentPtr->mac,macPtr,6)==0 || !currentPtr->blockUsed) //Found the right block or a new one
        {
            if(!currentPtr->blockUsed){ //Non initialized block, initialize it
                currentPtr->blockUsed=true; //Mark this block as used
                memcpy(currentPtr->mac,macPtr,6);
                //ESP_LOGI("block","New %d",macPtr[0]);
            }else{
                //ESP_LOGI("block","Used %d",macPtr[0]);
            }
            *blockAddress = currentPtr; //Write the return address of this function            
            return true;
        }
        count++;
        currentPtr++;
    }
    return false; //Could not find an empty spot 
}

char* MACToString(uint8_t* input, char* macadress){
    snprintf(macadress, 18, "%02x:%02x:%02x:%02x:%02x:%02x" ,input[0], input[1], input[2], input[3], input[4], input[5]);
    return macadress;
}

//This function is called whenever wifi is started. When this function returns, the system will go into sleep mode
void DoWork(){        
    //Reset the stats counters
    memset(MACsSEEN,0,sizeof(MACsSEEN));

    recordDataEnabled=true; //Start gathering smamples    
    vTaskDelay(TIME_WORKING_MS/portTICK_PERIOD_MS);   //Keep recording samples here during the "wake" time
    recordDataEnabled=false; //Stop gathering samples
    vTaskDelay(500/portTICK_PERIOD_MS); //Wait for any samples still coming


    //Create final stats //////////////////////////////////////////////////////////////////////////

    //Count how many MACs
    int seenMACcount=0;
    struct mac_data* temp;
    //while(seenMACcount<MAX_MAC_COUNT && MACsSEEN[seenMACcount].blockUsed) seenMACcount++;
    while(seenMACcount<MAX_MAC_COUNT && MACsSEEN[seenMACcount].blockUsed){
        temp = &MACsSEEN[seenMACcount];
        // 00:aa:bb:cc:dd:ee        
        char macadress[18];
        MACToString(temp->mac, macadress);
        ESP_LOGW("results","Mac is %s", macadress);
        if(strcmp(macadress,"a4:50:46:4c:af:3b")==0){
            ESP_LOGE("results","Ale found!");
        }
        seenMACcount++; 
    }
    ESP_LOGI("results","Seen %d different MACs",seenMACcount);
    
    //Create final stats END //////////////////////////////////////////////////////////////////////////

    

    //Push the new data to the database
    if(!WiFiConnected) return; //Don't even try to send data if we are not connected to a wifi network

    //Get current time (from NTP servers as set in the WIFI initialization)
    struct timeval tv_now;
    gettimeofday(&tv_now, NULL);
    int64_t time_us = (int64_t)tv_now.tv_sec * 1000L + (int64_t)tv_now.tv_usec/1000;

    //Get our own MAC
    uint8_t myMAC[6];
    ESP_ERROR_CHECK(esp_read_mac(myMAC, ESP_MAC_WIFI_STA));


    //Create key
     char myMacString[18];
    MACToString(myMAC, myMacString);
    snprintf(keyToSend, sizeof(keyToSend),"TUDelftDeviceData|%s|%lld",DEVICE_NAME,time_us);

    //Create fixed lines for the value and submit them
    snprintf(valueToAppend,sizeof(valueToAppend),"%d\\r\\n%s\\r\\n",seenMACcount,myMacString);
    PushToRedis(keyToSend, valueToAppend, false); //Don't append here

    //Push each line
    char* currentPrintLocation = valueToAppend;
    seenMACcount=0;
    while(seenMACcount<MAX_MAC_COUNT && MACsSEEN[seenMACcount].blockUsed){
        temp = &MACsSEEN[seenMACcount];
        // 00:aa:bb:cc:dd:ee        
        char macadress[18];
        MACToString(temp->mac, macadress);

        ESP_LOGW("mac","%s",macadress);
        int remainingSpaceInValue=valueToAppend+sizeof(valueToAppend)-currentPrintLocation;

        currentPrintLocation+= snprintf(currentPrintLocation,remainingSpaceInValue,"%s|%u|%u|%u|%u|%llu|%llu\\r\\n",
                    macadress,temp->managementPacketCountTX,temp->managementPacketCountRX,temp->dataPacketCountTX,temp->dataPacketCountRX,temp->dataPacketTotalSizeTX,temp->dataPacketTotalSizeRX);

        if(remainingSpaceInValue< 256){ //If the next MAC data has a chance to not fit in the buffer, just append it to the redis key and start again
            PushToRedis(keyToSend,valueToAppend,true); //Append the next block of data to redis
            currentPrintLocation = valueToAppend;
        }
        seenMACcount++; 
    }

    //If there is data in the buffer push it to redis
    if(currentPrintLocation!=valueToAppend){
        PushToRedis(keyToSend,valueToAppend,true); //Append the next block of data to redis
    }
    

    //Exit, the system will sleep here
}


void WIFI_DATA_CALLBACK(void* data,wifi_promiscuous_pkt_type_t packetType){
    if(!recordDataEnabled) return;
    wifi_pkt_rx_ctrl_t* metadata=&((wifi_promiscuous_pkt_t*)data)->rx_ctrl;
    struct wifi_packet* wifiPacket = ((wifi_promiscuous_pkt_t*)data)->payload;    
    unsigned int wifiDataLen = metadata->sig_len-4; //-4 bc the checksum is included (and at the end)
    
    //Find the MAC storage blocks
    struct mac_data* TXMAC_StoragePtr=NULL;
    struct mac_data* RXMAC_StoragePtr=NULL;

    if(FindMACStorageStruct(wifiPacket->addrTX,&TXMAC_StoragePtr)){ //If we can find a place to store the data about the TX MAC
        if(packetType==WIFI_PKT_MGMT){
            TXMAC_StoragePtr->managementPacketCountTX++;
        }else if(packetType==WIFI_PKT_DATA){
            TXMAC_StoragePtr->dataPacketCountTX++;
            TXMAC_StoragePtr->dataPacketTotalSizeTX+=wifiDataLen;
        }
    }else
        ESP_LOGW("callback","Can not find storage space for TX MAC!");

    if(FindMACStorageStruct(wifiPacket->addrRX,&RXMAC_StoragePtr)){ //If we can find a place to store the data about the TX MAC
        if(packetType==WIFI_PKT_MGMT){
            RXMAC_StoragePtr->managementPacketCountRX++;
        }else if(packetType==WIFI_PKT_DATA){
            RXMAC_StoragePtr->dataPacketCountRX++;
            RXMAC_StoragePtr->dataPacketTotalSizeRX+=wifiDataLen;
        }
    }else 
        ESP_LOGW("callback","Can not find storage space for RX MAC!");
}