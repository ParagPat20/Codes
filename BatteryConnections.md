# Hexapod Robot Power System Documentation

## Circuit Diagram
```text
                                    Middle Section (Logic & Comm Hub)
                    +----------------------------------------+
                    |   +------------+      +------------+    |
                    |   | 5000mAh    |      |    3S     |    |
                    |   |   LiPo     |----->|    BMS    |    |
                    |   | Battery    |      |           |    |
                    |   +------------+      +------------+    |
                    |           |                |           |
                    |           v                v           |
                    |      +-----------+   +------------+   |
                    |      |  ESP32    |   | Charging   |   |
                    |      |  (Slave)  |   | Circuit    |   |
                    |      +-----------+   +------------+   |
                    +----------------------------------------+
                                    | (I2C: SDA/SCL)
                                    |
            +------------------------|------------------------+
            |                        |                        |
            v                        v                        v
    Left Section                                     Right Section
+------------------+                            +------------------+
|  +------------+  |                           |  +------------+  |
|  | 2500mAh    |  |                           |  | 2500mAh    |  |
|  |   LiPo     |--|                           |  |   LiPo     |--|
|  | Battery    |  |                           |  | Battery    |  |
|  +------------+  |                           |  +------------+  |
|        |         |                           |        |         |
|        v         |                           |        v         |
|  +------------+  |                           |  +------------+  |
|  |    3S      |  |                           |  |    3S      |  |
|  |    BMS     |  |                           |  |    BMS     |  |
|  +------------+  |                           |  +------------+  |
|        |         |                           |        |         |
|        v         |                           |        v         |
|    [Schottky]    |                           |    [Schottky]    |
|        |         |                           |        |         |
|        v         |                           |        v         |
| +-------------+  |                           | +-------------+  |
| |  PCA9685    |  |                           | |  PCA9685    |  |
| | PWM Driver  |  |                           | | PWM Driver  |  |
| +-------------+  |                           | +-------------+  |
|        |         |                           |        |         |
|        v         |                           |        v         |
| +-------------+  |                           | +-------------+  |
| |Servo Motors |  |                           | |Servo Motors |  |
| +-------------+  |                           | +-------------+  |
+------------------+                           +------------------+
```

## System Architecture Overview

The hexapod robot uses a distributed power system with three independent battery sections to separate sensitive logic electronics from the high-current demands of the servos.

1. **Middle Section (Control Hub)**: Powers the logic side (Slave ESP32).
2. **Left Section (Leg Control)**: Powers the PCA9685 high-current rail and left-side servos.
3. **Right Section (Leg Control)**: Powers the PCA9685 high-current rail and right-side servos.

### Key Features
- Independent power distribution for improved reliability.
- Prevention of brownouts: ESP32 remains stable even under heavy servo load.
- Hardware-based PWM generation via PCA9685 over I2C.
- Wireless commands received via ESP-NOW from a PC-connected Master ESP32.

## Detailed Component Specifications

### Middle Section (Control Hub)
- **Battery**: 5000mAh 3S LiPo
- **BMS**: 3S Battery Management System
- **Controller**: ESP32 (Slave)
- **Primary Functions**: Wireless communication reception (ESP-NOW), I2C master control.

### Side Sections (Left & Right)
- **Battery**: 6200mAh 3S LiPo
- **BMS**: 3S Battery Management System
- **Controllers**: PCA9685 16-Channel PWM Drivers
- **Actuators**: Servo motors
- **Protection**: Schottky diode (10A-20A)

## Connection Guide

### 1. Power Distribution

#### Middle Section Setup
1. **Battery Connections**
   ```text
   Battery (+) → BMS B+
   Battery (-) → BMS B-
   Balance Leads → BMS Balance Ports
   ```
2. **Control Circuit**
   ```text
   BMS P+ → Voltage Regulator (e.g., 5V Buck) Input
   Voltage Regulator Output → ESP32 VIN (or 5V pin)
   BMS P- → Common Ground
   ```

#### Side Section Setup (Left/Right)
1. **Battery Protection**
   ```text
   Battery (+) → BMS B+
   Battery (-) → BMS B-
   ```
2. **Servo Power Circuit**
   ```text
   BMS P+ → Schottky Diode Anode
   Schottky Diode Cathode → PCA9685 "V+" (Servo Power Input)
   BMS P- → PCA9685 Ground (Must be tied to Common Ground)
   ```
3. **PCA9685 Logic Power**
   ```text
   From Middle Section 5V Regulator → PCA9685 "VCC"
   ```

### 2. Communication Setup

#### ESP32 Network Configuration
```text
Protocol: ESP-NOW
Topology: Point-to-Point (PC Master ESP32 to Robot Slave ESP32)
```

#### Control Signal Routing
1. **Master ESP32 (on PC) → Slave ESP32 (on Robot)**
   - Translates Python GUI serial commands to wireless ESP-NOW packets.
2. **Slave ESP32 → PCA9685 Boards**
   - Transmits PWM tick adjustments over the I2C bus (`GPIO21`/`GPIO22`).
3. **PCA9685 Boards → Servos**
   - Directly drives servo signal lines with 50Hz PWM signals based on I2C commands.

## Safety Features

### 1. Overcurrent Protection
- BMS current limiting
- Fused power rails
- Schottky diode isolation to prevent reverse currents from regenerative braking.

### 2. Common Ground Requirement
- **Critical:** The grounds for all three batteries, the ESP32, and the PCA9685 boards *must* be connected together. Without a common ground, I2C signals will fail and servos may behave erratically.

## Performance Specifications

### Power System
```text
Input Voltage: 11.1V (3S LiPo, dropped down via buck converters)
Peak Current: Dependent on servos (can exceed 10A per side)
```

### Control System
```text
Protocol: ESP-NOW
Update Rate: Optimized via Serial/I2C
Latency: ~10-30ms over wireless link
```
