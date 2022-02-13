#include "RedisFunctions.h"
#include "CREDENTIALS.h"

#include "esp_log.h"

#include <string.h>
#include <sys/param.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "nvs_flash.h"
#include "esp_netif.h"
#include "lwip/err.h"
#include "lwip/sockets.h"

char AUTH_COMMAND[] ="AUTH " REDIS_PASSWORD "\r\n";

char redisTag[] = "redis"; //Used to identify logs coming from here

void PushToRedis(char* key, char* value, bool append){
    ESP_LOGI(redisTag,"Pushed key %s to redis. Value: %s\n",key,value);

    struct sockaddr_in dest_addr;
    dest_addr.sin_addr.s_addr = inet_addr(REDIS_HOST_IP);
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_port = htons(REDIS_HOST_PORT);

    int sock =  socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
    if (sock < 0) {
        ESP_LOGE(redisTag, "Unable to create socket: errno %d", errno);
        goto end;
    }

    ESP_LOGI(redisTag, "Socket created, connecting to %s:%d", REDIS_HOST_IP, REDIS_HOST_PORT);


    int err = connect(sock, (struct sockaddr *)&dest_addr, sizeof(struct sockaddr_in6));
    if (err != 0) {
        ESP_LOGE(redisTag, "Socket unable to connect: errno %d", errno);
        goto end;
    }
    ESP_LOGI(redisTag, "Successfully connected");

    
    err = send(sock,AUTH_COMMAND , strlen(AUTH_COMMAND), 0);
    if (err < 0) {
        ESP_LOGE(redisTag, "Error occurred during sending auth: errno %d", errno);
        goto end;
    }

    err = send(sock,(append?"APPEND ":"SET ") , strlen((append?"APPEND ":"SET ")), 0); //APPEND or SET, as you want
    if (err < 0) {
        ESP_LOGE(redisTag, "Error occurred during sending key (1): errno %d", errno);
        goto end;
    }

    err = send(sock,key , strlen(key), 0);
    if (err < 0) {
        ESP_LOGE(redisTag, "Error occurred during sending key (2): errno %d", errno);
        goto end;
    }

    err = send(sock," \"", 2, 0);
    if (err < 0) {
        ESP_LOGE(redisTag, "Error occurred during sending key (2): errno %d", errno);
        goto end;
    }

    err = send(sock,value , strlen(value), 0);
    if (err < 0) {
        ESP_LOGE(redisTag, "Error occurred during sending key (3): errno %d", errno);
        goto end;
    }

    err = send(sock,"\"\r\n" , 3, 0);
    if (err < 0) {
        ESP_LOGE(redisTag, "Error occurred during sending key (4): errno %d", errno);
        goto end;
    }

    //Redis will answer here. We do not care about knowing if it was received properly, so just close the socket and ignore it.

end:
    if (sock != -1) {
        ESP_LOGI(redisTag, "Closing socket...");
        shutdown(sock, 0);
        close(sock);
    }
    
}