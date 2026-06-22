/*
 * ESP32 I2C Scanner
 * 
 * Scans the main I2C bus for connected devices:
 * - SDA = GPIO 21
 * - SCL = GPIO 22
 * 
 * Displays all found I2C addresses in hexadecimal format
 */

#include <Wire.h>

// I2C Pins
#define I2C_SDA 21
#define I2C_SCL 22

// MOSFET Power Control Pin (N-Channel low-side switch)
#define MOSFET_PIN 19

void setup() {
  // Configure and turn on MOSFET power control pin
  pinMode(MOSFET_PIN, OUTPUT);
  digitalWrite(MOSFET_PIN, HIGH); // Pull HIGH to turn on MOSFET (enable ground path for PCA9685)
  delay(100); // Wait for power to stabilize
  
  Serial.begin(115200);
  while (!Serial) {
    delay(10); // Wait for serial port to connect
  }
  
  Serial.println("\n\n========================================");
  Serial.println("ESP32 I2C Scanner");
  Serial.println("========================================\n");
  
  // Initialize I2C (default Wire)
  Wire.begin(I2C_SDA, I2C_SCL);
  Serial.println("I2C Bus initialized:");
  Serial.print("  SDA: GPIO ");
  Serial.println(I2C_SDA);
  Serial.print("  SCL: GPIO ");
  Serial.println(I2C_SCL);
  
  Serial.println("\n========================================\n");
  delay(1000);
}

void loop() {
  Serial.println("\n--- Scanning I2C Bus ---");
  Serial.println();
  
  // Scan I2C Bus
  int count = scanI2C(Wire);
  
  Serial.println();
  Serial.println("========================================");
  Serial.print("Total devices found: ");
  Serial.println(count);
  Serial.println("========================================");
  
  // Wait 5 seconds before next scan
  delay(5000);
}

/**
 * Scan an I2C bus for devices
 * @param wire The TwoWire instance to scan
 * @return Number of devices found
 */
int scanI2C(TwoWire &wire) {
  byte error, address;
  int nDevices = 0;
  
  Serial.print("  Scanning... ");
  
  for(address = 1; address < 127; address++) {
    // The i2c_scanner uses the return value of
    // the Write.endTransmission to see if
    // a device did acknowledge to the address.
    wire.beginTransmission(address);
    error = wire.endTransmission();
    
    if (error == 0) {
      Serial.print("\n  Device found at address 0x");
      if (address < 16) {
        Serial.print("0");
      }
      Serial.print(address, HEX);
      Serial.print(" (");
      Serial.print(address);
      Serial.println(")");
      
      nDevices++;
    } else if (error == 4) {
      Serial.print("\n  Unknown error at address 0x");
      if (address < 16) {
        Serial.print("0");
      }
      Serial.println(address, HEX);
    }
  }
  
  if (nDevices == 0) {
    Serial.println("No I2C devices found");
  } else {
    Serial.print("  ");
    Serial.print(nDevices);
    Serial.println(" device(s) found");
  }
  
  return nDevices;
}


