#ifndef _DEV_CONFIG_H_
#define _DEV_CONFIG_H_

#include <Arduino.h>
#include <stdint.h>
#include <stdio.h>
#include <SPI.h>

#define UBYTE   uint8_t
#define UWORD   uint16_t
#define UDOUBLE uint32_t

/**
 * GPIO config for ESP32 NodeMCU-32S
 * CS  -> GPIO 5  (VSPI SS)
 * DC  -> GPIO 21 (Safe Non-Strapping Pin)
 * RST -> GPIO 4
 * BL  -> GPIO 22
 * DIN -> GPIO 23 (Hardware VSPI MOSI)
 * CLK -> GPIO 18 (Hardware VSPI SCK)
**/
#define DEV_CS_PIN  5
#define DEV_DC_PIN  21
#define DEV_RST_PIN 4
#define DEV_BL_PIN  22

#define DEV_Digital_Write(_pin, _value) digitalWrite(_pin, _value == 0 ? LOW : HIGH)
#define DEV_Digital_Read(_pin) digitalRead(_pin)
#define DEV_SPI_WRITE(_dat) SPI.transfer(_dat)
#define DEV_Delay_ms(__xms) delay(__xms)
#define DEV_Set_BL(_Pin, _Value) digitalWrite(_Pin, HIGH)

void Config_Init();

#endif
