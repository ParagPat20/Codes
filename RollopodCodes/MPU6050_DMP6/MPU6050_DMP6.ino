#include <MPU6050_tockn.h>
#include <Wire.h>

MPU6050 mpu(Wire);

// Filter variables
float rollAngle = 0.0;
unsigned long lastUpdate = 0;

void setup() {
  Serial.begin(115200);
  while (!Serial);

  Serial.println("Initializing I2C...");
  Wire.begin();
  
  Serial.println("Initializing MPU6050 (tockn library)...");
  mpu.begin();
  
  Serial.println("Calculating gyro offsets, keep the robot completely still...");
  mpu.calcGyroOffsets(true); // 'true' prints the progress to Serial
  Serial.println("Calibration Done!");

  // Initialize time
  lastUpdate = millis();
}

void loop() {
  // Update all sensor readings internally in the library
  mpu.update();

  // Get raw acceleration in X and Y (in g's)
  float accX = mpu.getAccX();
  float accY = mpu.getAccY();
  
  // Get raw gyroscope rate around Z axis (in deg/s)
  float gyroZ = mpu.getGyroZ();

  // Calculate time delta (dt)
  unsigned long now = millis();
  float dt = (now - lastUpdate) / 1000.0;
  lastUpdate = now;
  if (dt <= 0.0) dt = 0.001;

  // 1. Calculate accelerometer angle (rotation about Z-axis, X-axis is vertical)
  // Gravity component rotates in the X-Y plane
  float accelRoll = atan2(accY, accX) * 180.0 / M_PI;

  // 2. Complementary Filter:
  // Fuses Gyro (fast, but drifts) & Accel (stable, but noisy)
  rollAngle = 0.98 * (rollAngle + gyroZ * dt) + 0.02 * accelRoll;

  // Print results
  Serial.print("roll\t");
  Serial.println(rollAngle);

  // Run loop at approx 100Hz
  delay(10); 
}
