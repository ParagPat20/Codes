#ifndef __CYBERPUNK_RENDERER_H
#define __CYBERPUNK_RENDERER_H

#include <Arduino.h>
#include "LCD_Driver.h"
#include "fonts.h"

// Premium Cyberpunk 16-bit RGB565 Colors (Pre-swapped Big-Endian)
#define CP_BLACK       0x0000
#define CP_DARK_BG     0x2108 // Deep Obsidian Navy #040814
#define CP_CYAN        0xFF07 // Neon Electric Cyan #00F0FF
#define CP_MAGENTA     0x1FF8 // Neon Magenta Pink #FF007F
#define CP_YELLOW      0xE0FF // Cyberpunk Yellow #FFE600
#define CP_WHITE       0xFFFF // Pure Bright White
#define CP_GREEN       0xE007 // Neon Matrix Green #00FF66

#define NUM_SPECTRUM_BANDS 16

struct AudioData {
    uint8_t bands[NUM_SPECTRUM_BANDS];
    uint8_t bass;
    uint8_t mid;
    uint8_t treble;
    uint8_t volume;
    bool isBeat;
    char speechText[96]; // Live speech transcript
};

class CyberpunkRenderer {
public:
    CyberpunkRenderer();
    void init();
    void update(const AudioData &audio);
    void setSpeechText(const char *text);

private:
    uint32_t frameCount;
    float peakBands[NUM_SPECTRUM_BANDS];
    char currentSpeech[96];
    bool speechDirty;

    void drawTopCenteredSpeech(const char *text);
    void drawTallSpectrum(const AudioData &audio);
    void fillRectBurst(int x, int y, int w, int h, uint16_t beColor);
    void drawChar(int x, int y, char c, sFONT* font, uint16_t fgColor, uint16_t bgColor);
    void drawCenteredString(int y, const char *str, sFONT* font, uint16_t fgColor, uint16_t bgColor);
};

#endif
