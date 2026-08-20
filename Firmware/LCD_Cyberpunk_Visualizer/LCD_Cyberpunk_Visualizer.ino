/*****************************************************************************
* ROLLOPOD CYBERPUNK AUDIO SPECTRUM VISUALIZER & LIVE SPEECH HUD
* - Top: Real-Time Live Speech Subtitles Box
* - Bottom: Tall ~190px Neon Equalizer Spectrum Analyzer
******************************************************************************/

#include <Arduino.h>
#include <SPI.h>
#include "LCD_Driver.h"
#include "DEV_Config.h"
#include "Cyberpunk_Renderer.h"

CyberpunkRenderer renderer;
AudioData currentAudio;
unsigned long lastAudioPacketTime = 0;
uint32_t simQuoteTimer = 0;
int simQuoteIdx = 0;

const char *sampleQuotes[] = {
    "Listening for sound...",
    "Cyberpunk Beat Active",
    "Audio Spectrum 44.1kHz",
    "Bass Drop Detected!",
    "Rollopod AI Ready"
};

// Procedural music and subtitle simulator when PC stream is idle
void GenerateSimulatedAudio() {
    uint32_t t = millis();
    
    // 128 BPM electronic beat (~468ms period)
    float beatPhase = fmod(t / 468.0f, 1.0f);
    bool isKick = (beatPhase < 0.15f);
    
    currentAudio.isBeat = isKick;
    currentAudio.bass   = isKick ? (uint8_t)(255 * (1.0f - beatPhase / 0.15f)) : (uint8_t)(40 + 30 * sin(t * 0.005f));
    currentAudio.mid    = (uint8_t)(100 + 70 * sin(t * 0.003f + 1.0f));
    currentAudio.treble = (uint8_t)(90 + 60 * sin(t * 0.007f + 2.0f));
    currentAudio.volume = (uint8_t)((currentAudio.bass + currentAudio.mid + currentAudio.treble) / 3);

    // 16 Frequency EQ simulation
    for (int i = 0; i < NUM_SPECTRUM_BANDS; i++) {
        float freq = 0.0025f * (i + 1);
        float baseVal = 70.0f + 60.0f * sin(t * freq + i * 0.45f);
        if (i < 4 && isKick) {
            baseVal += currentAudio.bass * 0.85f;
        }
        currentAudio.bands[i] = (uint8_t)constrain((int)baseVal, 10, 255);
    }

    // Cycle demo subtitle quotes every 4 seconds
    if (millis() - simQuoteTimer > 4000) {
        simQuoteTimer = millis();
        simQuoteIdx = (simQuoteIdx + 1) % 5;
        strncpy(currentAudio.speechText, sampleQuotes[simQuoteIdx], sizeof(currentAudio.speechText) - 1);
    }
}

// Process Serial Audio & Speech Subtitles from Python PC
void ProcessSerialInput() {
    while (Serial.available() >= 2) {
        uint8_t b1 = Serial.peek();
        
        if (b1 == 0xAA) {
            uint8_t header[2];
            Serial.readBytes(header, 2);

            // 1. Audio Packet (0xAA 0x55)
            if (header[1] == 0x55) {
                if (Serial.available() >= 21) {
                    uint8_t payload[21];
                    Serial.readBytes(payload, 21);

                    for (int i = 0; i < NUM_SPECTRUM_BANDS; i++) {
                        currentAudio.bands[i] = payload[i];
                    }
                    currentAudio.bass   = payload[16];
                    currentAudio.mid    = payload[17];
                    currentAudio.treble = payload[18];
                    currentAudio.volume = payload[19];
                    currentAudio.isBeat = (payload[20] > 0);

                    lastAudioPacketTime = millis();
                }
            } 
            // 2. Speech Subtitle Packet (0xAA 0x66 + textLen + text)
            else if (header[1] == 0x66) {
                while (!Serial.available()) {}
                uint8_t textLen = Serial.read();
                textLen = min((int)textLen, 63);
                
                size_t readCount = 0;
                while (readCount < textLen) {
                    if (Serial.available()) {
                        currentAudio.speechText[readCount++] = Serial.read();
                    }
                }
                currentAudio.speechText[textLen] = '\0';
                renderer.setSpeechText(currentAudio.speechText);
            }
        } 
        else if (b1 == 'T') {
            // Text Command line: "TXT:Hello World\n"
            String line = Serial.readStringUntil('\n');
            if (line.startsWith("TXT:")) {
                String sub = line.substring(4);
                sub.trim();
                strncpy(currentAudio.speechText, sub.c_str(), sizeof(currentAudio.speechText) - 1);
                renderer.setSpeechText(currentAudio.speechText);
            }
        } 
        else {
            Serial.read(); // Discard noise
        }
    }
}

void setup()
{
    Serial.begin(115200);
    Serial.setTimeout(100);

    Config_Init();
    renderer.init();

    strcpy(currentAudio.speechText, "Listening for voice...");
    renderer.setSpeechText(currentAudio.speechText);

    Serial.println("=================================================");
    Serial.println(" ROLLOPOD CYBERPUNK VISUALIZER & SPEECH HUD");
    Serial.println(" Send 'TXT:Hello World' to update subtitles");
    Serial.println("=================================================");
}

void loop()
{
    // Read live audio / subtitles from PC
    ProcessSerialInput();

    // Simulated music if PC stream is idle
    if (millis() - lastAudioPacketTime > 1500) {
        GenerateSimulatedAudio();
    }

    // Render frame (Top HUD + Tall Spectrum)
    renderer.update(currentAudio);

    delay(10); // ~50-60 FPS
}
