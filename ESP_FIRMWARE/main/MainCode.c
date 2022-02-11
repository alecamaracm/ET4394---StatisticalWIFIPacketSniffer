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

void GoToSleep();

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

static bool WiFiConnected=false;
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
    while(seenMACcount<MAX_MAC_COUNT && MACsSEEN[seenMACcount].blockUsed) seenMACcount++;
    ESP_LOGI("results","Seen %d different MACs",seenMACcount);

    //Create final stats END //////////////////////////////////////////////////////////////////////////

    

    //Push the new data to the database
    PushToRedis("key","value");  
    //Exit, the system will sleep here
}


void WIFI_DATA_CALLBACK(void* data,wifi_promiscuous_pkt_type_t packetType){
    if(!recordDataEnabled) return;
    wifi_pkt_rx_ctrl_t* metadata=&((wifi_promiscuous_pkt_t*)data)->rx_ctrl;
    struct wifi_packet* wifiPacket = ((wifi_promiscuous_pkt_t*)data)->payload;    
    unsigned int wifiDataLen = metadata->sig_len - sizeof(struct wifi_packet) -4; //-4 for the checksum
    
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