#include <Arduino.h>
#include <SPI.h>
#include "LCD_Driver.h"
#include "DEV_Config.h"
#include "GUI_Paint.h"
#include "frames_data.h" // 26 full-color frames from giphy.gif

// Buffer for 240-pixel expanded scanline
uint16_t scaledLine[LCD_WIDTH];

// Hardware 2X Scaler: Renders 120x140 frame into Full-Screen 240x280
void DrawFrame2x(const uint8_t *frameData) {
    // Set LCD address window to entire screen (0,0 to 239,279)
    LCD_SetCursor(0, 0, LCD_WIDTH - 1, LCD_HEIGHT - 1);
    
    DEV_Digital_Write(DEV_DC_PIN, 1);
    DEV_Digital_Write(DEV_CS_PIN, 0);

    const size_t lineBytes = FRAME_WIDTH * 2; // 120 * 2 = 240 bytes

    for (int y = 0; y < FRAME_HEIGHT; y++) {
        const uint16_t *srcLine = (const uint16_t *)(frameData + y * lineBytes);
        
        // Horizontal 2x Pixel Doubler (120 -> 240 pixels)
        for (int x = 0; x < FRAME_WIDTH; x++) {
            uint16_t pixel = srcLine[x];
            scaledLine[2 * x]     = pixel;
            scaledLine[2 * x + 1] = pixel;
        }

        // Vertical 2x Line Doubler (140 -> 280 lines)
        // Stream each line twice to fill full 240x280 screen
        SPI.writeBytes((uint8_t *)scaledLine, LCD_WIDTH * 2);
        SPI.writeBytes((uint8_t *)scaledLine, LCD_WIDTH * 2);
    }

    DEV_Digital_Write(DEV_CS_PIN, 1);
}

void setup()
{
    // Initialize Hardware SPI & GPIO for ESP32
    Config_Init();
    
    // Initialize ST7789V2 240x280 LCD
    LCD_Init();

    // Turn backlight to maximum brightness
    LCD_SetBacklight(100);

    // Clear entire screen to black
    LCD_Clear(0x0000);
}

void loop()
{
    // Play 26-frame fluid full-screen animation in continuous loop
    for (int i = 0; i < NUM_FRAMES; i++) {
        DrawFrame2x(animation_frames[i]);
        delay(40); // ~25 FPS smooth playback
    }
}
