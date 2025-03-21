# Hexapod Robot Power System Documentation

## Circuit Diagram
```
                                    Middle Section
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
                    |      | (Master)  |   | Circuit    |   |
                    |      +-----------+   +------------+   |
                    +----------------------------------------+
                                    |
                                    |
            +------------------------|------------------------+
            |                       |                        |
            v                       v                        v
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
| |   ESP32     |  |                           | |   ESP32     |  |
| +-------------+  |                           | +-------------+  |
|        |         |                           |        |         |
|        v         |                           |        v         |
| +-------------+  |                           | +-------------+  |
| |   STM32     |  |                           | |   STM32     |  |
| +-------------+  |                           | +-------------+  |
|        |         |                           |        |         |
|        v         |                           |        v         |
| +-------------+  |                           | +-------------+  |
| |Servo Motors |  |                           | |Servo Motors |  |
| |& DC Motors  |  |                           | |& DC Motors  |  |
| +-------------+  |                           | +-------------+  |
+------------------+                           +------------------+
```

## System Architecture Overview

The hexapod robot uses a distributed power system with three independent battery sections:

1. Middle Section (Control Hub)
2. Left Section (Leg Control)
3. Right Section (Leg Control)

### Key Features
- Independent power distribution for improved reliability
- Simultaneous charging and operation capability
- Protected charging circuits with Schottky diodes
- Wireless communication between sections

## Detailed Component Specifications

### Middle Section (Control Hub)
- Battery: 5000mAh 3S LiPo
- BMS: 3S Battery Management System
- Controller: ESP32 (Master)
- Primary Functions: Central control, charging management

### Side Sections (Left & Right)
- Battery: 2500mAh 3S LiPo
- BMS: 3S Battery Management System
- Controllers: ESP32 + STM32
- Actuators: 10 Servo motors, 1 DC motor
- Protection: Schottky diode (10A-20A)

## Connection Guide

### 1. Power Distribution

#### Middle Section Setup
1. Battery Connections
   ```
   Battery (+) â†’ BMS B+
   Battery (-) â†’ BMS B-
   Balance Leads â†’ BMS Balance Ports
   ```

2. Control Circuit
   ```
   BMS P+ â†’ ESP32 VIN
   BMS P- â†’ Common Ground
   BMS P+ â†’ Charging Circuit Input
   ```

#### Side Section Setup (Left/Right)
1. Battery Protection
   ```
   Battery (+) â†’ BMS B+
   Battery (-) â†’ BMS B-
   Balance Leads â†’ BMS Balance Ports
   ```

2. Servo Power Circuit
   ```
   BMS P+ â†’ Schottky Diode Anode
   Schottky Diode Cathode â†’ Servo Power Rail
   BMS P- â†’ Servo Ground Rail
   ```

3. Control Circuit Power
   ```
   BMS P+ â†’ Voltage Regulator Input
   Voltage Regulator Output â†’ ESP32/STM32 VIN
   BMS P- â†’ Control Circuit Ground
   ```

### 2. Communication Setup

#### ESP32 Network Configuration
```
Protocol: ESP-NOW
Topology: Star (Middle ESP32 as hub)
Data Rate: 1Mbps
```

#### Control Signal Routing
1. Middle ESP32 â†’ Side ESP32s
   - Movement commands
   - Status monitoring
   - Battery management

2. Side ESP32 â†’ STM32
   - Servo control signals
   - Motor control signals

## Safety Features

### 1. Overcurrent Protection
- BMS current limiting
- Fused power rails
- Schottky diode isolation

### 2. Battery Protection
- Over-voltage protection
- Under-voltage protection
- Short circuit protection
- Temperature monitoring

### 3. Charging Safety
- CC/CV charging profile
- Balance charging
- Isolated charging paths

## Maintenance Guidelines

### Regular Checks
1. Battery voltage monitoring
2. Connection integrity
3. Diode temperature during operation
4. Slip ring conductivity

### Troubleshooting
1. Power Issues
   - Check battery voltage
   - Verify BMS operation
   - Test diode continuity

2. Control Issues
   - Verify ESP32 communication
   - Check STM32 outputs
   - Monitor servo power rails

## Performance Specifications

### Power System
```
Input Voltage: 11.1V (3S LiPo)
Peak Current: 15A per side
Charging Current: 5A maximum
Operating Time: ~2 hours (typical use)
```

### Control System
```
Update Rate: 50Hz
Latency: <20ms
Communication Range: 10m (typical)
```
