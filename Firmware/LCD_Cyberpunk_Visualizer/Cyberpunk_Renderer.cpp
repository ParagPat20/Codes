#include "Cyberpunk_Renderer.h"
#include <SPI.h>
#include <math.h>
#include <string.h>

CyberpunkRenderer::CyberpunkRenderer() {
    frameCount = 0;
    speechDirty = true;
    strcpy(currentSpeech, "Speak into your mic...");
    for (int i = 0; i < NUM_SPECTRUM_BANDS; i++) {
        peakBands[i] = 0.0f;
    }
}

void CyberpunkRenderer::init() {
    LCD_Init(0); // Portrait 240x280
    LCD_SetBacklight(100);
    fillRectBurst(0, 0, LCD_WIDTH, LCD_HEIGHT, CP_DARK_BG);
    speechDirty = true;
}

void CyberpunkRenderer::setSpeechText(const char *text) {
    if (strcmp(currentSpeech, text) != 0) {
        strncpy(currentSpeech, text, sizeof(currentSpeech) - 1);
        currentSpeech[sizeof(currentSpeech) - 1] = '\0';
        speechDirty = true;
    }
}

void CyberpunkRenderer::fillRectBurst(int x, int y, int w, int h, uint16_t beColor) {
    if (w <= 0 || h <= 0 || x >= LCD_WIDTH || y >= LCD_HEIGHT) return;
    int x1 = max(0, x);
    int y1 = max(0, y);
    int x2 = min((int)LCD_WIDTH - 1, x + w - 1);
    int y2 = min((int)LCD_HEIGHT - 1, y + h - 1);
    int drawW = x2 - x1 + 1;
    int drawH = y2 - y1 + 1;

    static uint16_t fillBuf[LCD_WIDTH];
    for (int i = 0; i < drawW; i++) {
        fillBuf[i] = beColor;
    }

    LCD_SetCursor(x1, y1, x2, y2);
    DEV_Digital_Write(DEV_DC_PIN, 1);
    DEV_Digital_Write(DEV_CS_PIN, 0);

    const size_t lineBytes = drawW * 2;
    for (int i = 0; i < drawH; i++) {
        SPI.writeBytes((uint8_t *)fillBuf, lineBytes);
    }
    DEV_Digital_Write(DEV_CS_PIN, 1);
}

void CyberpunkRenderer::drawChar(int x, int y, char c, sFONT* font, uint16_t fgColor, uint16_t bgColor) {
    if (c < ' ' || c > '~') c = ' ';
    uint32_t charOffset = (c - ' ') * font->Height * (font->Width / 8 + (font->Width % 8 ? 1 : 0));
    const uint8_t *ptr = &font->table[charOffset];

    static uint16_t charBuf[32 * 32];
    int w = font->Width;
    int h = font->Height;
    int bytesPerRow = font->Width / 8 + (font->Width % 8 ? 1 : 0);

    for (int row = 0; row < h; row++) {
        for (int col = 0; col < w; col++) {
            uint8_t byteVal = ptr[row * bytesPerRow + (col / 8)];
            bool isPixel = (byteVal & (0x80 >> (col % 8))) != 0;
            charBuf[row * w + col] = isPixel ? fgColor : bgColor;
        }
    }

    LCD_SetCursor(x, y, x + w - 1, y + h - 1);
    DEV_Digital_Write(DEV_DC_PIN, 1);
    DEV_Digital_Write(DEV_CS_PIN, 0);
    SPI.writeBytes((uint8_t *)charBuf, w * h * 2);
    DEV_Digital_Write(DEV_CS_PIN, 1);
}

// Draw string horizontally centered on screen
void CyberpunkRenderer::drawCenteredString(int y, const char *str, sFONT* font, uint16_t fgColor, uint16_t bgColor) {
    int strLen = strlen(str);
    if (strLen == 0) {
        fillRectBurst(0, y, LCD_WIDTH, font->Height, bgColor);
        return;
    }

    int totalW = strLen * font->Width;
    int startX = max(4, (LCD_WIDTH - totalW) / 2);

    // Clear left padding
    if (startX > 0) {
        fillRectBurst(0, y, startX, font->Height, bgColor);
    }

    // Draw characters
    int curX = startX;
    while (*str) {
        if (curX + font->Width > LCD_WIDTH - 4) break;
        drawChar(curX, y, *str, font, fgColor, bgColor);
        curX += font->Width;
        str++;
    }

    // Clear right padding
    if (curX < LCD_WIDTH) {
        fillRectBurst(curX, y, LCD_WIDTH - curX, font->Height, bgColor);
    }
}

// Clean Top-Middle Centered Speech Subtitles (No box, no header badge)
void CyberpunkRenderer::drawTopCenteredSpeech(const char *text) {
    const int maxCharsPerLine = 24;
    char lines[2][28];
    memset(lines, 0, sizeof(lines));

    const char *src = text;
    int lineIdx = 0;

    while (*src && lineIdx < 2) {
        while (*src == ' ') src++; // Skip leading spaces
        if (!*src) break;

        int len = strlen(src);
        if (len <= maxCharsPerLine) {
            strncpy(lines[lineIdx], src, maxCharsPerLine);
            break;
        } else {
            int breakPos = maxCharsPerLine;
            while (breakPos > 0 && src[breakPos] != ' ') {
                breakPos--;
            }
            if (breakPos == 0) breakPos = maxCharsPerLine;

            strncpy(lines[lineIdx], src, breakPos);
            lines[lineIdx][breakPos] = '\0';
            src += breakPos;
            lineIdx++;
        }
    }

    // Line 1: Centered Bright White
    drawCenteredString(8, lines[0], &Font16, CP_WHITE, CP_DARK_BG);

    // Line 2: Centered Electric Yellow
    if (strlen(lines[1]) > 0) {
        drawCenteredString(28, lines[1], &Font16, CP_YELLOW, CP_DARK_BG);
    } else {
        fillRectBurst(0, 28, LCD_WIDTH, 18, CP_DARK_BG);
    }

    // Subtle Cyber Divider Dots
    fillRectBurst(10, 52, 6, 2, CP_CYAN);
    fillRectBurst(LCD_WIDTH - 16, 52, 6, 2, CP_CYAN);
    fillRectBurst(0, 56, LCD_WIDTH, 1, CP_DARK_BG);
}

// Ultra-Tall High-Impact Spectrum Visualizer (Y = 60 to 279, Height ~215px!)
void CyberpunkRenderer::drawTallSpectrum(const AudioData &audio) {
    const int startX = 10;
    const int barW = 11;
    const int spacing = 3;
    const int maxH = 205; // Massive ~205px height!
    const int baseY = 270;

    for (int i = 0; i < NUM_SPECTRUM_BANDS; i++) {
        int x = startX + i * (barW + spacing);
        int val = audio.bands[i];
        int barH = map(val, 0, 255, 3, maxH);

        // Peak decay physics
        if (barH > peakBands[i]) {
            peakBands[i] = barH;
        } else {
            peakBands[i] -= 3.2f;
            if (peakBands[i] < 0) peakBands[i] = 0;
        }

        // Clear only upper unlit portion
        int unlitH = maxH - barH;
        if (unlitH > 0) {
            fillRectBurst(x, baseY - maxH, barW, unlitH, CP_DARK_BG);
        }

        // Segmented glowing neon blocks
        int numSegments = barH / 5;
        for (int s = 0; s < numSegments; s++) {
            int segY = baseY - (s * 5) - 4;
            uint16_t segColor;
            if (s < 14) {
                segColor = CP_CYAN;    // Bottom 0-35%: Neon Cyan
            } else if (s < 26) {
                segColor = CP_MAGENTA; // Mid 35-65%: Neon Magenta
            } else if (s < 35) {
                segColor = CP_YELLOW;  // Upper 65-85%: Cyber Yellow
            } else {
                segColor = CP_WHITE;   // Peak 85-100%: Pure White
            }
            fillRectBurst(x, segY, barW, 3, segColor);
        }

        // Floating peak cap
        int peakY = baseY - (int)peakBands[i] - 5;
        if (peakY < baseY && peakY > (baseY - maxH)) {
            fillRectBurst(x, peakY, barW, 2, CP_WHITE);
        }
    }

    // Base glowing energy horizon
    uint16_t horizonCol = audio.isBeat ? CP_YELLOW : CP_CYAN;
    fillRectBurst(0, 274, LCD_WIDTH, 4, horizonCol);
}

void CyberpunkRenderer::update(const AudioData &audio) {
    frameCount++;

    if (strlen(audio.speechText) > 0) {
        setSpeechText(audio.speechText);
    }

    // Redraw Top-Centered Speech Subtitles when text changes
    if (speechDirty || (frameCount % 30 == 0)) {
        drawTopCenteredSpeech(currentSpeech);
        speechDirty = false;
    }

    // Draw Massive ~205px Tall Spectrum Visualizer
    drawTallSpectrum(audio);
}
