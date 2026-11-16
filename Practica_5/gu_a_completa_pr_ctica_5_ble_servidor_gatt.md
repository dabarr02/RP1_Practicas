# Guía Paso a Paso - Práctica 5 (BLE: Servidor GATT)

## Preparación del entorno y proyecto base
1. Cargar el entorno de ESP-IDF y abrir el proyecto `gatt_server_service_table`:
   ```bash
   source /home/danibc/.espressif/v6.1/esp-idf/export.sh
   cd ~/Documentos/PracticasMaster/RP1/Practica_5/gatt_server_service_table
   ```
2. Compilar, flashear y abrir el monitor serie:
   ```bash
   idf.py set-target esp32   # (o esp32s3 / esp32c3 según tu placa)
   idf.py build flash monitor
   ```

---

## Ejercicio 1: Cambiar el nombre del dispositivo anunciado
1. Abre `main/gatts_table_creat_demo.c`.
2. Localiza la macro `SAMPLE_DEVICE_NAME` y cámbiala por tu nombre personalizado:
   ```c
   #define SAMPLE_DEVICE_NAME "MI_ESP32_BLE"
   ```
3. *(Opcional)* Si tienes activado `CONFIG_SET_RAW_ADV_DATA` en `menuconfig`, actualiza también los bytes del nombre y su longitud en el array `raw_adv_data[]` (longitud = nº de caracteres + 1 del byte de tipo `ESP_BLE_AD_TYPE_NAME_CMPL`).
4. Recompila y flashea (`idf.py build flash monitor`).
5. En otra terminal, escanea con `bluetoothctl` para localizar el nuevo nombre y apuntar su MAC:
   ```bash
   bluetoothctl
   scan on
   # Apuntar MAC (ej. 34:85:18:00:DE:AA)
   scan off
   ```

---

## Ejercicio 2: Conexión con el servidor GATT
1. Desde `bluetoothctl`, conéctate usando la MAC obtenida:
   ```bash
   connect 34:85:18:00:DE:AA
   ```
2. Documenta la salida de `bluetoothctl` (descubrimiento de servicios) y el log del monitor serie del ESP32, donde se dispara el evento `ESP_GATTS_CONNECT_EVT` indicando el `conn_id` y la MAC del cliente.

---

## Ejercicio 3: Identificar atributos de la tabla GATT
1. En `bluetoothctl`, entra al submenú GATT y lista los atributos:
   ```bash
   menu gatt
   list-attributes
   ```
2. Identifica los UUIDs relevantes (primeros 32 bits):
   * **Servicio Principal (`0x00FF`):** `.../service0028`
   * **Característica Heart Rate Measurement (`0xFF01`):** `.../service0028/char0029`
   * **Descriptor CCCD (`0x2902`):** `.../service0028/char0029/desc002b`

---

## Ejercicio 4: Leer el valor de la característica (`0xFF01`)
1. Selecciona la característica `0xFF01` y lee su contenido:
   ```bash
   select-attribute /org/bluez/hci0/dev_34_85_18_00_DE_AA/service0028/char0029
   read
   ```
   *(Devolverá el array inicial definido en el firmware, por defecto `0x11 0x22 0x33 0x44`).*

---

## Ejercicio 5: Modificar el valor inicial en el firmware
1. En `main/gatts_table_creat_demo.c`, busca la definición de `char_value`:
   ```c
   static uint8_t char_value[4] = {0x11, 0x22, 0x33, 0x44};
   ```
2. Modifica sus valores (ej. `{0xAA, 0xBB, 0xCC, 0xDD}`), guarda, recompila y flashea (`idf.py build flash`).
3. Reconecta con `bluetoothctl`, entra en `menu gatt`, selecciona `char0029` y ejecuta `read` para verificar el nuevo valor.

---

## Ejercicio 6: Escribir un nuevo valor desde `bluetoothctl`
1. Con `char0029` seleccionado en `bluetoothctl`, escribe un nuevo valor en hexadecimal y léelo de vuelta:
   ```bash
   write "0x55 0x66 0x77 0x88"
   read
   ```
2. En el monitor del ESP32 observarás el evento `ESP_GATTS_WRITE_EVT` mostrando los bytes recibidos.

---

## Ejercicio 7: Activar notificaciones y comprobar el CCCD
1. Con `char0029` seleccionado, activa las notificaciones:
   ```bash
   notify on
   ```
2. Selecciona su descriptor CCCD (`desc002b`) y lee su valor para comprobar que se ha escrito `0x0001` (`01 00` en little-endian):
   ```bash
   select-attribute /org/bluez/hci0/dev_34_85_18_00_DE_AA/service0028/char0029/desc002b
   read
   ```
3. **Explicación en código:** En `gatts_profile_event_handler()`, dentro de `case ESP_GATTS_WRITE_EVT:`, el servidor comprueba si el `handle` escrito coincide con `heart_rate_handle_table[IDX_CHAR_CFG_A]` y si la longitud es 2 bytes. Al recibir `0x0001`, registra `notify enable` y llama inmediatamente a `esp_ble_gatts_send_indicate()` con `need_confirm = false` para enviar una notificación con el contenido de `notify_data`.

---

## Ejercicio 8: Envío periódico automático cada segundo
Modifica `main/gatts_table_creat_demo.c` para enviar datos aleatorios cada segundo mientras haya un cliente suscrito:

1. **Añadir cabecera aleatoria y variable global de estado** (al inicio del archivo):
   ```c
   #include "esp_random.h"

   static bool notify_enabled = false;
   static TaskHandle_t publish_task_handle = NULL;
   ```

2. **Definir la tarea periódica `publish_data_task`** (antes de `gatts_profile_event_handler`):
   ```c
   static void publish_data_task(void *pvParameters)
   {
       while (1) {
           char_value[0] = esp_random() % 256;

           if (notify_enabled) {
               ESP_LOGI(GATTS_TABLE_TAG, "Sending notification: 0x%02x", char_value[0]);
               esp_ble_gatts_send_indicate(heart_rate_profile_tab[0].gatts_if,
                                           heart_rate_profile_tab[0].conn_id,
                                           heart_rate_handle_table[IDX_CHAR_VAL_A],
                                           sizeof(char_value),
                                           char_value,
                                           false);
           }
           vTaskDelay(pdMS_TO_TICKS(1000));
       }
   }
   ```

3. **Actualizar `notify_enabled` al escribir en el CCCD** (dentro de `ESP_GATTS_WRITE_EVT`):
   * Donde imprime `ESP_LOGI(GATTS_TABLE_TAG, "notify enable");`, añade:
     ```c
     notify_enabled = true;
     ```
   * Donde imprime `ESP_LOGI(GATTS_TABLE_TAG, "notify disable");`, añade:
     ```c
     notify_enabled = false;
     ```

4. **Crear y destruir la tarea en conexión/desconexión**:
   * En `case ESP_GATTS_CONNECT_EVT:`:
     ```c
     if (publish_task_handle == NULL) {
         xTaskCreate(&publish_data_task, "publish_data_task", 4096, NULL, 5, &publish_task_handle);
     }
     ```
   * En `case ESP_GATTS_DISCONNECT_EVT:`:
     ```c
     notify_enabled = false;
     if (publish_task_handle != NULL) {
         vTaskDelete(publish_task_handle);
         publish_task_handle = NULL;
     }
     ```

5. **Compilar, flashear y probar:**
   * Ejecuta `idf.py build flash monitor`.
   * Conéctate desde `bluetoothctl`, entra en `menu gatt`, selecciona `char0029` y ejecuta `notify on`. Verás llegar un valor actualizado cada segundo en la terminal.