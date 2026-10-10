idf_component_register(SRCS "scan.c"
                    PRIV_REQUIRES esp_wifi nvs_flash esp_timer
                    INCLUDE_DIRS ".")
