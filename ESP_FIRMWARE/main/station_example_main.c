#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_sleep.h"

#include "lwip/err.h"
#include "lwip/sys.h"
#include "sntp.h"

#include "esp_wpa2.h"

#include "CREDENTIALS.h"
#include "RedisFunctions.h"

static const char *TAG = "wifi station";

bool WiFiConnected=false;

void DoWork();
void WIFI_DATA_CALLBACK(void* data,wifi_promiscuous_pkt_type_t packetType);

static void event_handler(void* arg, esp_event_base_t event_base,
                                int32_t event_id, void* event_data)
{
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
        WiFiConnected=false;
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {        
        esp_wifi_connect();
        WiFiConnected=false;
        ESP_LOGI(TAG,"Disconnected to the AP!");
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_CONNECTED) {                
        ESP_LOGI(TAG,"Connected to the AP!");
        WiFiConnected=true;
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(TAG, "got ip:" IPSTR, IP2STR(&event->ip_info.ip));
    }
}

void wifi_init_sta(void)
{
    ESP_ERROR_CHECK(esp_netif_init());

    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    esp_event_handler_instance_t instance_any_id;
    esp_event_handler_instance_t instance_got_ip;
    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT,
                                                        ESP_EVENT_ANY_ID,
                                                        &event_handler,
                                                        NULL,
                                                        &instance_any_id));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT,
                                                        IP_EVENT_STA_GOT_IP,
                                                        &event_handler,
                                                        NULL,
                                                        &instance_got_ip));

   
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA) );
    
    
    ESP_ERROR_CHECK(esp_wifi_set_promiscuous(true));
    ESP_ERROR_CHECK(esp_wifi_set_promiscuous_rx_cb(WIFI_DATA_CALLBACK));
    #ifdef USE_EDUORAM
		   wifi_config_t wifi_config = {
        .sta = {
            .ssid = "eduroam",
           
            /* Setting a password implies station will connect to all security modes including WEP/WPA.
             * However these modes are deprecated and not advisable to be used. Incase your Access point
             * doesn't support WPA2, these mode can be enabled by commenting below line */
	     .threshold.authmode = WIFI_AUTH_WPA2_PSK,

            .pmf_cfg = {
                .capable = true,
                .required = false
            },
        },
		};
		ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config) );
        esp_wifi_sta_wpa2_ent_set_identity((uint8_t *)WIFI_EDU_USERNAME, strlen(WIFI_EDU_USERNAME));
	esp_wifi_sta_wpa2_ent_set_username((uint8_t *)WIFI_EDU_USERNAME, strlen(WIFI_EDU_USERNAME));
	esp_wifi_sta_wpa2_ent_set_password((uint8_t *)WIFI_EDU_PASSWORD, strlen(WIFI_EDU_PASSWORD));
  
	esp_wifi_sta_wpa2_ent_enable(); //set config settings to enable function
  #else
	   wifi_config_t wifi_config = {
        .sta = {
            .ssid = WIFI_SSID,
            .password = WIFI_PASS,
            /* Setting a password implies station will connect to all security modes including WEP/WPA.
             * However these modes are deprecated and not advisable to be used. Incase your Access point
             * doesn't support WPA2, these mode can be enabled by commenting below line */
	     .threshold.authmode = WIFI_AUTH_WPA2_PSK,

            .pmf_cfg = {
                .capable = true,
                .required = false
            },
        },
		};
		ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config) );
    #endif
	ESP_ERROR_CHECK(esp_wifi_start() );
    sntp_setoperatingmode(SNTP_OPMODE_POLL);
    sntp_setservername(0, "pool.ntp.org");
    sntp_init();

    ESP_LOGI(TAG, "wifi_init_sta finished.");
}



void app_main(void)
{
    //Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
      ESP_ERROR_CHECK(nvs_flash_erase());
      ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    ESP_LOGI(TAG, "ESP_WIFI_MODE_STA");
    wifi_init_sta();

    vTaskDelay(1000/portTICK_RATE_MS); //Give everything some time to initialize

    ESP_LOGI("main","ESP READY");

    DoWork();
        
    esp_wifi_stop();

    ESP_LOGI("main","ESP GOING TO SLEEP");
    vTaskDelay(500/portTICK_RATE_MS); //Give everything some time to flush
    //Sleep
    esp_deep_sleep(TIME_SLEEPING_MS*1000);        
}
