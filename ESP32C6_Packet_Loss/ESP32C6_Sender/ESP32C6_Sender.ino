/*
  ===============================================================================
  ESP32-C6 ESP-NOW PACKET LOSS TRACER - SENDER (TRANSMITTER)
  Target Board: Seeed Studio XIAO ESP32-C6
  Environment: Arduino IDE (ESP32 Board Package v3.x+)
  ===============================================================================

  Antenna Control Notes (Seeed XIAO ESP32-C6):
  - GPIO 3: Enable control pin (Must be set LOW to activate RF antenna switching)
  - GPIO 14: Antenna Selection pin
      - LOW  = Built-in / Internal PCB Antenna (Default)
      - HIGH = External Antenna (U.FL connector)
  ===============================================================================
*/

#include <esp_idf_version.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>

// Antenna Selection: false = Internal Built-in Antenna, true = External Antenna
bool useExternalAntenna = false;

// Transmit Interval (ms)
uint32_t sendIntervalMs = 100; // Default 10 pkts/sec

// Broadcast MAC Address
uint8_t broadcastAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

#define PAYLOAD_SIZE 180

// High-Stress Packet Structure with Wireless Relay Telemetry (233 bytes total)
typedef struct __attribute__((packed)) {
  uint32_t magic;             // Header signature (0x4553504E = 'ESPN')
  uint32_t sequence;          // Packet index
  uint32_t sendTimestamp;     // millis() at transmission time
  uint8_t  isEcho;            // 0 = Normal packet, 1 = Echo response
  char     senderMac[18];     // Sender MAC address
  uint16_t payloadLen;        // Length of heavy string payload
  uint32_t checksum;          // Payload integrity checksum

  // Wireless Telemetry Relay Fields (Receiver populates in Echo response)
  uint32_t rxPacketsReceived; // Receiver total received count
  uint32_t rxPacketsLost;     // Receiver total lost count
  float    rxLossRate;        // Receiver loss rate %
  uint32_t rxCorrupted;       // Receiver corrupted count

  char     payload[PAYLOAD_SIZE]; // 180-byte heavy test payload
} PacketData;

#define MAGIC_SIGNATURE 0x4553504E

// Checksum calculation for data integrity verification
uint32_t calculateChecksum(const char *data, uint16_t len) {
  uint32_t hash = 5381;
  for (uint16_t i = 0; i < len; i++) {
    hash = ((hash << 5) + hash) + (uint8_t)data[i];
  }
  return hash;
}

// Generate a long dense string filled with sequential numbers & patterns
const char STRESS_PATTERN[] = "0123456789_ESP32C6_HIGH_STRESS_PACKET_LOSS_TRACER_PAYLOAD_890123456789_ABCDEFGHIJKLMNOPQRSTUVWXYZ_";

void generateLongStringPayload(char *buffer, uint16_t size, uint32_t seq) {
  int offset = snprintf(buffer, size, "PKT#%u-NUMS:0123456789876543210-DATA:", seq);
  if (offset < 0) offset = 0;
  
  while ((uint16_t)offset < size - 1) {
    uint16_t copyLen = sizeof(STRESS_PATTERN) - 1;
    if (offset + copyLen >= size - 1) {
      copyLen = (size - 1) - offset;
    }
    memcpy(buffer + offset, STRESS_PATTERN, copyLen);
    offset += copyLen;
  }
  buffer[size - 1] = '\0';
}

// Telemetry Statistics
struct Statistics {
  uint32_t packetsSent = 0;
  uint32_t sendSuccess = 0;
  uint32_t sendFail = 0;
  int      lastRssi = 0;
  uint32_t lastRttMs = 0;
  uint32_t avgRttMs = 0;
  uint32_t rttSampleCount = 0;
} stats;

uint32_t lastSendTime = 0;
uint32_t lastReportTime = 0;

// Antenna Setup (Auto-detects XIAO ESP32-C6 vs Standard ESP32 DevKit)
void setupAntenna(bool useExternal) {
#if defined(CONFIG_IDF_TARGET_ESP32C6) || defined(ARDUINO_SEEED_XIAO_ESP32C6) || defined(ESP32C6)
  pinMode(3, OUTPUT);
  digitalWrite(3, LOW); // Enable antenna selection circuit on XIAO C6
  delay(100);

  pinMode(14, OUTPUT);
  digitalWrite(14, useExternal ? HIGH : LOW); // LOW = Built-in, HIGH = External

  useExternalAntenna = useExternal;

  Serial.println("--------------------------------------------------");
  if (useExternal) {
    Serial.println("[ANTENNA] XIAO C6: EXTERNAL Antenna (GPIO3=LOW, GPIO14=HIGH)");
  } else {
    Serial.println("[ANTENNA] XIAO C6: BUILT-IN Internal Antenna (GPIO3=LOW, GPIO14=LOW)");
  }
  Serial.println("--------------------------------------------------");
#else
  Serial.println("--------------------------------------------------");
  Serial.println("[ANTENNA] Standard ESP32 DevKit Board (Built-in PCB Antenna)");
  Serial.println("--------------------------------------------------");
#endif
}

// ESP-NOW Delivery Callback
#if defined(ESP_IDF_VERSION_MAJOR) && (ESP_IDF_VERSION_MAJOR >= 5)
void OnDataSent(const wifi_tx_info_t *tx_info, esp_now_send_status_t status) {
#else
void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
#endif
  if (status == ESP_NOW_SEND_SUCCESS) {
    stats.sendSuccess++;
  } else {
    stats.sendFail++;
  }
}

/// ESP-NOW Receive Callback (Receives Echo reply from Receiver for RTT, RSSI & Remote Telemetry)
#if defined(ESP_IDF_VERSION_MAJOR) && (ESP_IDF_VERSION_MAJOR >= 5)
void OnDataRecv(const esp_now_recv_info_t *recv_info, const uint8_t *incomingData, int len) {
  int currentRssi = recv_info->rx_ctrl->rssi;
#else
void OnDataRecv(const uint8_t *srcMac, const uint8_t *incomingData, int len) {
  int currentRssi = 0;
#endif

  if (len != sizeof(PacketData)) return;

  PacketData packet;
  memcpy(&packet, incomingData, sizeof(packet));

  if (packet.magic != MAGIC_SIGNATURE || !packet.isEcho) return;

  uint32_t now = millis();
  uint32_t rtt = now - packet.sendTimestamp;
  
  stats.lastRttMs = rtt;
  stats.rttSampleCount++;
  stats.avgRttMs = ((stats.avgRttMs * (stats.rttSampleCount - 1)) + rtt) / stats.rttSampleCount;
  stats.lastRssi = currentRssi;

  // Stream Wireless Receiver telemetry returned over ESP-NOW Echo response!
  Serial.printf("$DAT,RECV,%u,%d,%u,%u,%.2f,%u\n", 
                packet.sequence, currentRssi, packet.rxPacketsReceived, packet.rxPacketsLost, packet.rxLossRate, packet.rxCorrupted);
}

void setup() {
  Serial.begin(115200);
  delay(1500);

  Serial.println("\n==================================================");
  Serial.println("    ESP32-C6 ESP-NOW PACKET LOSS TRACER (SENDER)  ");
  Serial.println("==================================================");

  // 1. Initialize Built-in Internal Antenna
  setupAntenna(useExternalAntenna);

  // 2. WiFi Station Mode
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  Serial.print("[WIFI] Sender MAC Address: ");
  Serial.println(WiFi.macAddress());

  // Set maximum WiFi transmit power for range testing (21dBm)
  esp_wifi_set_max_tx_power(84);

  // 3. Initialize ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("[ERROR] ESP-NOW Init Failed!");
    return;
  }
  Serial.println("[ESP-NOW] Initialized.");

  esp_now_register_send_cb(OnDataSent);
  esp_now_register_recv_cb(OnDataRecv);

  // 4. Register Broadcast Peer
  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, broadcastAddress, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;

  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("[ESP-NOW] Warning: Broadcast Peer Add Failed.");
  } else {
    Serial.println("[ESP-NOW] Broadcast Peer Ready.");
  }

  printMenu();
}

void sendPacket() {
  PacketData packet;
  memset(&packet, 0, sizeof(packet));
  packet.magic = MAGIC_SIGNATURE;
  packet.sequence = ++stats.packetsSent;
  packet.sendTimestamp = millis();
  packet.isEcho = 0;

  String macStr = WiFi.macAddress();
  macStr.toCharArray(packet.senderMac, sizeof(packet.senderMac));

  generateLongStringPayload(packet.payload, PAYLOAD_SIZE, packet.sequence);
  packet.payloadLen = (uint16_t)strlen(packet.payload);
  packet.checksum = calculateChecksum(packet.payload, packet.payloadLen);

  esp_now_send(broadcastAddress, (uint8_t *)&packet, sizeof(packet));

  // High-speed stream output for Python UI (Emits on EVERY sent packet!)
  Serial.printf("$DAT,SENDER,%u,%d,%u,%u,%u,%u\n", 
                packet.sequence, stats.lastRssi, stats.lastRttMs, stats.packetsSent, stats.sendSuccess, stats.sendFail);
}

// Transmit Interval (microseconds for up to multi-kHz speeds)
uint32_t sendIntervalMicros = 10000; // Default 100 Hz (10,000 us)
uint32_t currentFrequencyHz = 100;
uint32_t lastSendMicros = 0;

void setFrequencyHz(uint32_t hz) {
  if (hz == 0) return;
  currentFrequencyHz = hz;
  sendIntervalMicros = 1000000UL / hz;
  Serial.printf("[CONFIG] Frequency set to %u Hz (%u us interval)\n", hz, sendIntervalMicros);
}

void printDashboard() {
  Serial.println("\n----------------- [SENDER TELEMETRY REPORT] -----------------");
  Serial.print(" Target Frequency: "); Serial.print(currentFrequencyHz); Serial.println(" Hz");
  Serial.print(" Total Sent:      "); Serial.println(stats.packetsSent);
  Serial.print(" Send Success:    "); Serial.print(stats.sendSuccess);
  
  float sendLoss = stats.packetsSent ? ((float)(stats.packetsSent - stats.sendSuccess) / stats.packetsSent) * 100.0 : 0;
  Serial.print(" (MAC Ack Loss: "); Serial.print(sendLoss, 2); Serial.println("%)");
  
  Serial.print(" Send Failed:     "); Serial.println(stats.sendFail);
  Serial.print(" Last RTT:        "); Serial.print(stats.lastRttMs); Serial.println(" ms");
  Serial.print(" Average RTT:     "); Serial.print(stats.avgRttMs); Serial.println(" ms");
  Serial.print(" Target RSSI:     "); Serial.print(stats.lastRssi); Serial.println(" dBm");
  Serial.print(" Active Antenna:  "); Serial.println(useExternalAntenna ? "EXTERNAL (GPIO14=HIGH)" : "BUILT-IN / INTERNAL (GPIO14=LOW)");
  Serial.println("----------------------------------------------------------------");
}

bool isTransmitting = true;

void printMenu() {
  Serial.println("\n--- Sender Remote Controls ---");
  Serial.println("  's' : Start / Resume Packet Transmission");
  Serial.println("  'p' : Pause / Stop Packet Transmission");
  Serial.println("  'x' : Reboot ESP32 Hardware");
  Serial.println("  'a' : Toggle Antenna (Built-in Internal <-> External)");
  Serial.println("  'r' : Reset Statistics");
  Serial.println("  '1' : 100 Hz (10ms)");
  Serial.println("  '2' : 10 Hz (100ms)");
  Serial.println("  '4' : 1 kHz (1ms)");
  Serial.println("  '5' : 2 kHz (0.5ms)");
  Serial.println("  $FREQ,<hz> : Set custom frequency in Hz");
  Serial.println("------------------------------\n");
}

void handleSerialInput() {
  while (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    if (input.length() == 0) continue;

    if (input.startsWith("$FREQ,")) {
      uint32_t hz = input.substring(6).toInt();
      if (hz > 0) setFrequencyHz(hz);
    } else {
      char c = input.charAt(0);
      switch (c) {
        case 's': case 'S': 
          isTransmitting = true; 
          Serial.println("[STATE] TRANSMISSION_STARTED"); 
          break;
        case 'p': case 'P': 
          isTransmitting = false; 
          Serial.println("[STATE] TRANSMISSION_PAUSED"); 
          break;
        case 'x': case 'X': 
          Serial.println("[STATE] REBOOTING_ESP32"); 
          delay(100); 
          ESP.restart(); 
          break;
        case 'a': case 'A': setupAntenna(!useExternalAntenna); break;
        case 'r': case 'R': memset(&stats, 0, sizeof(stats)); Serial.println("[INFO] Stats Reset."); break;
        case '1': setFrequencyHz(100); break;
        case '2': setFrequencyHz(10); break;
        case '3': setFrequencyHz(2); break;
        case '4': setFrequencyHz(1000); break; // 1 kHz
        case '5': setFrequencyHz(2000); break; // 2 kHz
        case 'h': case 'H': printMenu(); break;
      }
    }
  }
}

void loop() {
  uint32_t currentMicros = micros();

  if (isTransmitting && (currentMicros - lastSendMicros >= sendIntervalMicros)) {
    lastSendMicros = currentMicros;
    sendPacket();
  }

  uint32_t currentMillis = millis();
  if (currentMillis - lastReportTime >= 1000) {
    lastReportTime = currentMillis;
    printDashboard();
  }

  handleSerialInput();
}
