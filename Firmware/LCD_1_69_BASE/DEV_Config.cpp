#include "DEV_Config.h"

void GPIO_Init()
{
    pinMode(DEV_CS_PIN, OUTPUT);
    pinMode(DEV_RST_PIN, OUTPUT);
    pinMode(DEV_DC_PIN, OUTPUT);
    pinMode(DEV_BL_PIN, OUTPUT);
    digitalWrite(DEV_BL_PIN, HIGH);
}

void Config_Init()
{
    Serial.begin(115200);
    GPIO_Init();

    // High-Speed 40MHz Hardware SPI on ESP32
    SPI.begin(18, 19, 23, DEV_CS_PIN);
    SPI.setFrequency(40000000);
    SPI.setDataMode(SPI_MODE3);
    SPI.setBitOrder(MSBFIRST);
}
