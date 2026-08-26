/*
 * Rollopod ESP32-S3 AIoT Audio Bridge
 * =====================================
 * VERIFIED PINS from Waveshare manufacturer examples:
 *   03_audio_out_no_tf.ino  →  Speaker (ES8311 codec)
 *   06_esp_sr.ino           →  Microphone (ES7210 codec)
 *
 * This board uses CODEC CHIPS over I2C, not raw I2S.
 * Codec chips MUST be initialized via I2C before any audio works.
 * Speaker amp enable is via IO Expander (address 0x24), IO_6 = HIGH.
 *
 * Board: Waveshare ESP32-S3 AIoT Camera Development Board
 *
 * Connects to MIBEE (Open WiFi), streams audio to/from RPi5:
 *   MIC  → captures I2S audio (ES7210) → UDP to RPi5 :7778
 *   UDP  ← receives audio from RPi5    → I2S speaker (ES8311) :7779
 *
 * Audio: 16kHz, 16-bit, Stereo RX from ES7210 (left channel used)
 *
 * REQUIRED: Copy these support files from examples to this sketch folder:
 *   es8311.cpp / es8311.h / es8311_reg.h   (from 03_audio_out_no_tf)
 *   es7210.cpp / es7210.h / es7210_reg.h   (from 06_esp_sr)
 *   i2c.cpp    / i2c.h                      (from either example)
 *   io_extension.cpp / io_extension.h       (from either example)
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <Wire.h>
#include "ESP_I2S.h"        // Arduino ESP32 v3.x I2S driver
#include "esp_check.h"
#include "i2c.h"            // Waveshare I2C helper
#include "io_extension.h"   // IO expander (controls speaker amp)
#include "es8311.h"         // Speaker DAC codec
#include "es7210.h"         // Microphone ADC codec

// ============================================================
// NETWORK CONFIG
// ============================================================
const char* WIFI_SSID        = "MIBEE";
const char* WIFI_PASS        = "";      // Open network
const int   DISCOVERY_PORT   = 7777;   // RPi5 broadcasts hello here
const int   MIC_TX_PORT      = 7778;   // ESP32 → RPi5 (mic audio)
const int   SPK_RX_PORT      = 7779;   // RPi5  → ESP32 (speaker audio)
const char* DISCOVERY_MAGIC  = "ROLLOPOD_HELLO"; // beacon payload

// ============================================================
// EXACT PINS FROM WAVESHARE MANUFACTURER EXAMPLES
// Source: 03_audio_out_no_tf.ino + 06_esp_sr.ino
// ============================================================
#define I2S_PIN_MCK     GPIO_NUM_10   // Master Clock
#define I2S_PIN_BCK     GPIO_NUM_11   // Bit Clock
#define I2S_PIN_WS      GPIO_NUM_12   // Word Select / LRCK
#define I2S_PIN_DIN     GPIO_NUM_13   // Data In  (mic → ESP32, from ES7210)
#define I2S_PIN_DOUT    GPIO_NUM_14   // Data Out (ESP32 → speaker, to ES8311)

// I2C pins for codec control (from i2c.h: GPIO 8=SDA, GPIO 7=SCL)
// Handled inside DEV_I2C_Init() automatically

// ============================================================
// AUDIO CONFIG
// ============================================================
#define SAMPLE_RATE         16000
#define VOICE_VOLUME        95       // 0-100, speaker volume (matches working example)
#define MIC_GAIN_DB         ES7210_MIC_GAIN_30DB
#define MCLK_MULTIPLE       256
#define MCLK_FREQ_HZ        (SAMPLE_RATE * MCLK_MULTIPLE)

#define CHUNK_SAMPLES       512
#define CHUNK_BYTES         (CHUNK_SAMPLES * 2)   // 16-bit mono = 1024 bytes

// ============================================================
// GLOBALS
// ============================================================
I2SClass i2s;
WiFiUDP  udpMic;
WiFiUDP  udpSpk;
WiFiUDP  udpDiscovery;  // listens for RPi5 beacon

static const char* TAG = "main";
static es7210_dev_handle_t es7210_handle = NULL;

int16_t monoMicBuf[CHUNK_SAMPLES];            // mic PCM → UDP
int16_t spkBuf[CHUNK_BYTES / 2];              // received from RPi5

// Discovered RPi5 IP — starts empty, auto-filled on first beacon
IPAddress rpi5_ip;          
bool      rpi5_found = false;
unsigned long lastBeaconLog  = 0;
unsigned long lastReconnectAttempt = 0;

// Forward declaration
void playStartupSound();

// ============================================================
// CODEC INIT: ES8311 (Speaker DAC)
// Exact match with 03_audio_out_no_tf.ino
// ============================================================
static esp_err_t init_es8311_speaker() {
  es8311_handle_t es_handle = es8311_create(I2C_NUM_0, ES8311_ADDRRES_0);
  ESP_RETURN_ON_FALSE(es_handle, ESP_FAIL, TAG, "es8311 create failed");

  const es8311_clock_config_t es_clk = {
    .mclk_inverted     = false,
    .sclk_inverted     = false,
    .mclk_from_mclk_pin = true,
    .mclk_frequency    = MCLK_FREQ_HZ,
    .sample_frequency  = SAMPLE_RATE
  };

  ESP_ERROR_CHECK(es8311_init(es_handle, &es_clk, ES8311_RESOLUTION_16, ES8311_RESOLUTION_16));
  ESP_RETURN_ON_ERROR(es8311_voice_volume_set(es_handle, VOICE_VOLUME, NULL), TAG, "set es8311 volume failed");
  ESP_RETURN_ON_ERROR(es8311_microphone_config(es_handle, false), TAG, "set es8311 microphone failed");

  Serial.printf("[ES8311] Speaker codec initialized (volume=%d)\n", VOICE_VOLUME);
  return ESP_OK;
}

// ============================================================
// CODEC INIT: ES7210 (Microphone ADC)
// ============================================================
static void init_es7210_mic() {
  es7210_i2c_config_t i2c_conf = { .i2c_addr = ES7210_ADDRRES_00 };
  ESP_ERROR_CHECK(es7210_new_codec(&i2c_conf, &es7210_handle));

  es7210_codec_config_t codec_conf = {};
  codec_conf.i2s_format    = ES7210_I2S_FMT_I2S;
  codec_conf.mclk_ratio    = MCLK_MULTIPLE;
  codec_conf.sample_rate_hz = SAMPLE_RATE;
  codec_conf.bit_width     = ES7210_I2S_BITS_16B;
  codec_conf.mic_bias      = ES7210_MIC_BIAS_2V87;
  codec_conf.mic_gain      = MIC_GAIN_DB;
  codec_conf.flags.tdm_enable = false;

  ESP_ERROR_CHECK(es7210_config_codec(es7210_handle, &codec_conf));
  ESP_ERROR_CHECK(es7210_config_volume(es7210_handle, 0));
  Serial.println("[ES7210] Microphone codec initialized");
}

// ============================================================
// I2S INIT
// Exact match with 03_audio_out_no_tf.ino: MONO + I2S_STD_SLOT_LEFT
// ============================================================
static bool init_i2s() {
  i2s.setPins(I2S_PIN_BCK, I2S_PIN_WS, I2S_PIN_DOUT, I2S_PIN_DIN, I2S_PIN_MCK);
  i2s.setTimeout(1000);

  if (!i2s.begin(I2S_MODE_STD, SAMPLE_RATE, I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO, I2S_STD_SLOT_LEFT)) {
    Serial.println("[I2S] Failed to initialize I2S bus!");
    return false;
  }
  Serial.println("[I2S] Initialized (16kHz, 16-bit, Mono Left Slot)");
  return true;
}

// ============================================================
// WIFI CONNECT
// ============================================================
void connectWiFi() {
  Serial.printf("[WiFi] Connecting to %s (open)...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) {
    delay(300);
    Serial.print(".");
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("[WiFi] Connected! ESP32-S3 IP: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("[WiFi] Waiting for RPi5 beacon on UDP broadcast :%d...\n", DISCOVERY_PORT);
    udpDiscovery.begin(DISCOVERY_PORT);  // listen for RPi5 hello
    udpMic.begin(MIC_TX_PORT);
    udpSpk.begin(SPK_RX_PORT);
    rpi5_found = false;  // reset on reconnect
  } else {
    Serial.println("[WiFi] FAILED — will retry in background");
  }
}

// ============================================================
// SETUP — Exact Sequence from 03_audio_out_no_tf.ino
// ============================================================
void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("\n\n========================================");
  Serial.println("  Rollopod Audio Bridge — Waveshare     ");
  Serial.println("  ESP32-S3 AIoT Camera Board             ");
  Serial.println("  ES7210(Mic) + ES8311(Speaker) + UDP   ");
  Serial.println("========================================\n");

  // Step 1: Initialize I2C and IO Expander
  DEV_I2C_Init();
  IO_EXTENSION_Init();

  // Step 2: Turn on amplifier (IO_6 = 1) BEFORE codec init
  IO_EXTENSION_Output(IO_EXTENSION_IO_6, 1);
  Serial.println("[HW] Amplifier power enabled (IO_6 = 1)");

  // Step 3: Initialize Codecs
  init_es8311_speaker();
  init_es7210_mic();

  // Step 4: Initialize I2S
  if (!init_i2s()) {
    Serial.println("[ERROR] I2S init failed — halting");
    while (1) delay(1000);
  }

  // Step 5: Complete IO expander config (IO_4 = 1)
  IO_EXTENSION_Output(IO_EXTENSION_IO_4, 1);

  // Step 6: Play startup sound to immediately verify audio out
  playStartupSound();

  // Step 7: Connect WiFi
  connectWiFi();

  Serial.println("\n[READY] Audio bridge running.");
  Serial.println("  Auto-discovery mode: waiting for RPi5 to broadcast on MIBEE...");
  Serial.println("  Once RPi5 found: Speak → mic → UDP → RPi5 AI → TTS → UDP → speaker\n");
}

// ============================================================
// STARTUP CHIME / SPEAKER TEST
// Generates a pleasant rising 3-tone chime (C5 -> E5 -> G5 -> C6)
// ============================================================
void playTone(float freqHz, int durationMs, float volume = 0.4f) {
  int totalSamples = (SAMPLE_RATE * durationMs) / 1000;
  int16_t buffer[256];
  int bufIndex = 0;
  float phase = 0.0f;
  float phaseInc = (2.0f * PI * freqHz) / SAMPLE_RATE;

  int attackSamples = (SAMPLE_RATE * 10) / 1000;  // 10ms ramp in
  int decaySamples  = (SAMPLE_RATE * 20) / 1000;  // 20ms ramp out

  for (int i = 0; i < totalSamples; i++) {
    float env = 1.0f;
    if (i < attackSamples) {
      env = (float)i / attackSamples;
    } else if (i > totalSamples - decaySamples) {
      env = (float)(totalSamples - i) / decaySamples;
    }

    float sampleVal = sinf(phase) * 32767.0f * volume * env;
    buffer[bufIndex++] = (int16_t)sampleVal;
    phase += phaseInc;
    if (phase >= 2.0f * PI) phase -= 2.0f * PI;

    if (bufIndex >= 256) {
      i2s.write((uint8_t*)buffer, sizeof(buffer));
      bufIndex = 0;
    }
  }

  if (bufIndex > 0) {
    i2s.write((uint8_t*)buffer, bufIndex * sizeof(int16_t));
  }
}

void playStartupSound() {
  Serial.println("[AUDIO] Playing startup chime on speaker...");
  playTone(523.25f, 120, 0.8f);   // C5
  delay(30);
  playTone(659.25f, 120, 0.8f);   // E5
  delay(30);
  playTone(783.99f, 120, 0.8f);   // G5
  delay(30);
  playTone(1046.50f, 300, 0.9f);  // C6
  delay(50);
  Serial.println("[AUDIO] Startup chime completed.");
}

// ============================================================
// LOOP
// ============================================================
void loop() {
  // WiFi watchdog
  if (WiFi.status() != WL_CONNECTED) {
    if (millis() - lastReconnectAttempt > 5000) {
      lastReconnectAttempt = millis();
      Serial.println("[WiFi] Lost — reconnecting...");
      connectWiFi();
    }
    delay(100);
    return;
  }

  // === 0. DISCOVERY — listen for RPi5 beacon broadcast ===
  {
    int pktSize = udpDiscovery.parsePacket();
    if (pktSize > 0) {
      char buf[32] = {};
      udpDiscovery.read(buf, sizeof(buf) - 1);
      if (strncmp(buf, DISCOVERY_MAGIC, strlen(DISCOVERY_MAGIC)) == 0) {
        IPAddress newIp = udpDiscovery.remoteIP();
        if (!rpi5_found || newIp != rpi5_ip) {
          rpi5_ip    = newIp;
          rpi5_found = true;
          Serial.printf("[DISCOVERY] RPi5 found at %s — streaming started!\n",
                        rpi5_ip.toString().c_str());
        }
      }
    }
    // Log waiting status every 5s
    if (!rpi5_found && millis() - lastBeaconLog > 5000) {
      lastBeaconLog = millis();
      Serial.printf("[DISCOVERY] Waiting for RPi5 beacon on :%d ...\n", DISCOVERY_PORT);
    }
  }

  // Don't stream until RPi5 is discovered
  if (!rpi5_found) {
    yield();
    return;
  }

  // === 1. MIC CAPTURE (ES7210 Mono Left Slot) → UDP to RPi5 ===
  {
    if (i2s.readBytes((char*)monoMicBuf, CHUNK_BYTES) > 0) {
      udpMic.beginPacket(rpi5_ip, MIC_TX_PORT);
      udpMic.write((uint8_t*)monoMicBuf, CHUNK_BYTES);
      udpMic.endPacket();
    }
  }

  // === 2. SPEAKER RX — receive PCM from RPi5 → play on ES8311 ===
  {
    int packetSize = udpSpk.parsePacket();
    if (packetSize > 0) {
      int bytes = udpSpk.read((uint8_t*)spkBuf, sizeof(spkBuf));
      if (bytes > 0) {
        i2s.write((uint8_t*)spkBuf, bytes);
      }
    }
  }

  yield();
}
