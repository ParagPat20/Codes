# ESP32 PCA9685 16-Channel Servo Controller

A comprehensive Python GUI application for controlling up to 16 servos using ESP32 and PCA9685 PWM driver board. Features tick-based PWM control with per-channel calibration and persistent settings.

## 🤖 NEW: Wireless ESP-NOW Support

**Two Operating Modes Available:**
1. **Direct Serial Mode**: ESP32 connected to PC via USB (original mode)
2. **ESP-NOW Wireless Mode**: Two ESP32s - one as USB bridge, one on robot (NEW!)

Perfect for mobile robots where USB tethering isn't practical.

## Features

### 🎯 Core Functionality
- **Direct PWM Tick Control**: Set PWM values directly using 12-bit tick values (0-4095)
- **16 Independent Channels**: Control up to 16 servos simultaneously
- **Per-Channel Calibration**: Individual tick range calibration for each servo
- **Angle Mapping**: Automatic conversion from angles (0.0-180.0°) to calibrated tick values
- **Settings Persistence**: Save and load calibration settings via JSON files

### 🎨 Modern GUI Features
- **Tabbed Interface**: Organized tabs for Connection, Calibration, Control, and Settings
- **Real-time Control Mode**: Auto-send commands as you adjust sliders
- **Manual Control Mode**: Review changes before sending to servos
- **Responsive Design**: Smooth scrolling for all 16 channels
- **Visual Feedback**: Live tick value display during calibration

### ⚙️ Advanced Features
- **Global Calibration**: Apply same tick range to all channels at once
- **Test Functions**: Test min/max tick values and angles individually
- **Quick Presets**: Set all servos to 0°, 90°, or 180° instantly
- **Device Management**: Sleep mode, wake, reset, and query info
- **Adjustable PWM Frequency**: 40-1000 Hz (typical 50 Hz for servos)

## System Architecture

### Mode 1: Direct Serial Connection (Simple Setup)
```
PC (Python GUI) ←[USB]→ ESP32 ←[I2C]→ PCA9685 → Servos (×16)
```
- Single ESP32 connected directly to laptop via USB
- Best for: Desktop testing, stationary robots, development

### Mode 2: ESP-NOW Wireless (Mobile Robots)
```
PC (Python GUI) ←[USB]→ ESP32 Master ←[ESP-NOW Wireless]→ ESP32 Slave ←[I2C]→ PCA9685 → Servos (×16)
```
- **ESP32 Master (Bridge)**: Stays with PC, converts Serial to ESP-NOW
- **ESP32 Slave (Robot)**: On robot, receives ESP-NOW commands, controls servos
- **Communication**: Wireless up to 200m range in ideal conditions
- Best for: Mobile robots, wheeled platforms, untethered operation

**Confidence: 90%** - ESP-NOW typical range is 200m outdoors; actual range varies with obstacles and interference (indoor range typically 50-100m).

## Hardware Requirements

### Mode 1: Direct Serial (Basic Setup)
- **1× ESP32 Development Board** (any variant with I2C support)
- **1× PCA9685 16-Channel PWM Driver Board**
- **Servos** (up to 16)
- **External Power Supply** (5-6V for servos, sufficient current rating)
- **1× USB Cable** (for ESP32 programming and serial communication)

### Mode 2: ESP-NOW Wireless (Robot Setup)
- **2× ESP32 Development Boards** (Master + Slave)
- **1× PCA9685 16-Channel PWM Driver Board**
- **Servos** (up to 16)
- **External Power Supply** (5-6V for servos, sufficient current rating)
- **2× USB Cables** (for programming both ESP32s)
- **Power source for robot ESP32** (battery, USB power bank, or regulated supply)

### Wiring Diagrams

#### Mode 1: Direct Serial Connection
```
PC (USB) → ESP32 ── I2C ──→ PCA9685 ─→ Servos
                               │
                          External Power
                          (5-6V for servos)

ESP32 Connections:
├─ GPIO21 (SDA) ──→ PCA9685 SDA
├─ GPIO22 (SCL) ──→ PCA9685 SCL
└─ GND ───────────→ PCA9685 GND

PCA9685 Power:
├─ VCC ───────────→ 5V (logic power)
├─ GND ───────────→ GND (common ground)
└─ V+ ────────────→ External 5-6V (servo power supply)

Servos:
└─ Connect to PCA9685 channels 0-15
   (Signal, VCC, GND for each servo)
```

#### Mode 2: ESP-NOW Wireless Setup
```
PC (USB) → ESP32 Master
                ║
           [ESP-NOW Wireless]
                ║
           ESP32 Slave ── I2C ──→ PCA9685 ─→ Servos
                                     │
                                External Power
                                (5-6V for servos)

ESP32 Master (PC Bridge):
└─ Only USB connection to PC needed
   No other wiring required

ESP32 Slave (On Robot):
├─ GPIO21 (SDA) ──→ PCA9685 SDA
├─ GPIO22 (SCL) ──→ PCA9685 SCL
├─ GND ───────────→ PCA9685 GND
└─ Power from battery/power bank (5V via USB or 3.3V via VIN)

PCA9685 Power (Same as Mode 1):
├─ VCC ───────────→ 5V (logic power)
├─ GND ───────────→ GND (common ground)
└─ V+ ────────────→ External 5-6V (servo power supply)

Servos:
└─ Connect to PCA9685 channels 0-15
   (Signal, VCC, GND for each servo)
```

**⚠️ Important:** 
- Use a separate power supply for servos (connected to PCA9685 V+)
- Ensure common ground between ESP32, PCA9685, and servo power supply
- Choose power supply with adequate current rating (servos can draw 500mA+ each under load)

## Software Requirements

### Arduino Libraries

**For All Modes:**
- **Adafruit PWM Servo Driver Library** (for PCA9685)
- **Wire** (I2C communication, included with Arduino IDE)

**For ESP-NOW Wireless Mode (Option B):**
- **ESP32 Arduino Core 2.0.0 or higher** (3.0.0+ recommended for best compatibility)
- **ESP-NOW library** (included in ESP32 core)
- **WiFi library** (included in ESP32 core)

Install libraries via Arduino Library Manager:
1. **Sketch** → **Include Library** → **Manage Libraries**
2. Search for "Adafruit PWM Servo Driver"
3. Click **Install**

**Note:** ESP-NOW callback registration changed in ESP32 Core 3.0.0+. The code in this project is compatible with both old and new versions. Reference: [Random Nerd Tutorials ESP-NOW Guide](https://randomnerdtutorials.com/esp-now-esp32-arduino-ide/)

### Python Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- `pyserial` - Serial communication with ESP32
- `tkinter` - GUI framework (usually pre-installed with Python)

## Installation

Choose your installation path based on your setup mode:

### Option A: Direct Serial Mode (Single ESP32)

#### Step 1: Upload Arduino Code to ESP32

1. Open `esp32_pca9685_controller/esp32_pca9685_controller.ino` in Arduino IDE
2. Select your ESP32 board: **Tools → Board → ESP32 Dev Module**
3. Select the correct COM port: **Tools → Port**
4. Click **Upload** button
5. Wait for upload to complete
6. Open Serial Monitor (115200 baud) to verify initialization

#### Step 2: Install Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Verify installation
python servo_controller_gui.py
```

✅ **Done!** Skip to the Usage Guide section.

---

### Option B: ESP-NOW Wireless Mode (Two ESP32s)

This setup requires programming two ESP32 boards. Follow these steps carefully:

#### Step 1: Upload Slave Code to Robot ESP32

1. Open `esp32_slave_pca9685/esp32_slave_pca9685.ino` in Arduino IDE
2. Select your ESP32 board: **Tools → Board → ESP32 Dev Module**
3. Select the correct COM port: **Tools → Port**
4. Click **Upload** button
5. **IMPORTANT:** Open Serial Monitor (115200 baud) and note the **MAC address** displayed
   ```
   Example output:
   *** SLAVE MAC ADDRESS: 24:6F:28:AB:CD:EF ***
   ```
6. **Write down this MAC address** - you'll need it for the next step!

#### Step 2: Configure and Upload Master Code

1. Open `esp32_master_bridge/esp32_master_bridge.ino` in Arduino IDE
2. **Find this line near the top of the code:**
   ```cpp
   uint8_t SLAVE_MAC_ADDRESS[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
   ```
3. **Replace with your slave's MAC address** from Step 1:
   ```cpp
   // Example: If slave MAC is 24:6F:28:AB:CD:EF
   uint8_t SLAVE_MAC_ADDRESS[] = {0x24, 0x6F, 0x28, 0xAB, 0xCD, 0xEF};
   ```
4. Disconnect the slave ESP32 and connect the master ESP32 to PC
5. Select the correct COM port for master ESP32
6. Click **Upload** button
7. Open Serial Monitor to verify connection

#### Step 3: Verify ESP-NOW Communication

1. Power up the slave ESP32 (on robot) using battery/power bank
2. Keep master ESP32 connected to PC via USB
3. In master's Serial Monitor, type: `INFO`
4. You should see response from the slave ESP32
5. If you get errors, check:
   - MAC address is correctly entered
   - Both ESP32s are powered on
   - Devices are within range (~50m indoors)

#### Step 4: Install Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Verify installation
python servo_controller_gui.py
```

✅ **Done!** The Python GUI works exactly the same - it doesn't know about the wireless link!

## Usage Guide

### Quick Start

1. **Connect Hardware**
   - Wire ESP32 to PCA9685 as shown in wiring diagram
   - Connect servos to PCA9685 channels
   - Power up the system

2. **Launch GUI**
   ```bash
   python servo_controller_gui.py
   ```

3. **Connect to ESP32**
   - Go to **Connection** tab
   - Select COM port from dropdown
   - Click **Connect**

4. **Calibrate Servos** (First-time setup)
   - Go to **Calibration** tab
   - For each channel, adjust MIN and MAX tick values
   - Use **Test Min** and **Test Max** buttons to find servo limits
   - Use **Test Angle** to verify calibration
   - Click **Send to Device** to upload calibrations
   - Go to **Settings** tab and click **Save Settings**

5. **Control Servos**
   - Go to **Control** tab
   - Move sliders or enter angles (0.0-180.0°)
   - Click **Set** button (or enable Real-time mode)

### Detailed Tab Guide

#### 📡 Connection Tab

**Serial Connection:**
- **COM Port**: Select the port where ESP32 is connected
- **Baud Rate**: Set to 115200 (default for this project)
- **Connect/Disconnect**: Establish or close serial connection
- **Status**: Shows current connection state

**Device Configuration:**
- **PWM Frequency**: Adjust PWM frequency (40-1000 Hz)
  - 50 Hz is standard for servos
  - Higher frequencies for LED dimming
  - Lower frequencies for specific servo types
- **Sleep Mode**: Put PCA9685 in low-power mode
- **Wake Up**: Resume from sleep mode
- **Reset Device**: Reset ESP32 to default settings (102-512 tick range)
- **Query Info**: Display current device configuration

#### 🎛️ Calibration Tab

**Purpose:** Find the exact tick values for each servo's full 0-180° range.

**Process:**
1. **Set Initial Values**: Enter estimated MIN (e.g., 102) and MAX (e.g., 512) tick values
2. **Test Minimum**: Click **Test Min** to send servo to 0° position
   - Adjust MIN value up if servo buzzes or tries to go further
   - Adjust MIN value down if servo doesn't reach full counterclockwise position
3. **Test Maximum**: Click **Test Max** to send servo to 180° position
   - Adjust MAX value down if servo buzzes or tries to go further
   - Adjust MAX value up if servo doesn't reach full clockwise position
4. **Verify with Angle**: Enter test angle (e.g., 90°) and click **Test**
   - Check if servo moves to expected position
   - Repeat adjustment if needed
5. **Apply**: Click **Send to Device** to upload all calibrations
6. **Save**: Go to Settings tab and save configuration

**Global Calibration:**
- Use if all servos are identical
- Enter MIN and MAX tick values
- Click **Apply to All** to set all channels
- Click **Send to Device** to upload

**Tick Value Display:**
- Shows current tick value sent to each channel
- Updates in real-time during testing

#### 🎮 Control Tab

**Control Modes:**
- **Manual Mode**: Click **Set** button to send commands
  - Allows batch adjustments before sending
  - Reduces serial communication overhead
- **Real-time Mode**: Auto-sends on slider/input change
  - Immediate servo response
  - Best for fine-tuning positions

**Per-Channel Controls:**
- **Slider**: Drag to adjust angle (0.0-180.0°)
- **Value Display**: Shows current slider position
- **Input Field**: Enter precise angle values
- **Set Button**: Send command to servo (manual mode only)

**Quick Presets:**
- **All to 0°**: Set all servos to minimum position
- **All to 90°**: Center all servos
- **All to 180°**: Set all servos to maximum position

#### 💾 Settings Tab

**File Management:**
- **Save Settings**: Save current calibrations to `settings.json`
- **Load Settings**: Load calibrations from `settings.json`
- **Save As...**: Save to a different file
- **Load From...**: Load from a specific file
- **Reset to Defaults**: Reset all calibrations to 102-512 ticks

**Configuration Display:**
- Shows current calibration in JSON format
- Includes all channel settings and frequency
- Click **Refresh Display** to update view

**Settings File Format (settings.json):**
```json
{
  "frequency": 50,
  "channels": {
    "0": {"tick_min": 102, "tick_max": 512},
    "1": {"tick_min": 102, "tick_max": 512},
    ...
    "15": {"tick_min": 102, "tick_max": 512}
  }
}
```

## Understanding PWM Ticks

### What are PWM Ticks?

The PCA9685 uses 12-bit PWM resolution, meaning each PWM cycle is divided into **4096 ticks** (0-4095).

**Tick-to-Pulse Width Conversion:**

At 50 Hz (standard servo frequency):
- PWM cycle period = 1/50 = 20ms = 20,000μs
- 1 tick = 20,000μs / 4096 ≈ 4.88μs

**Example Calculations:**

| Pulse Width | Tick Value | Calculation |
|------------|------------|-------------|
| 500μs | 102 ticks | 500 / 4.88 ≈ 102 |
| 1000μs | 205 ticks | 1000 / 4.88 ≈ 205 |
| 1500μs | 307 ticks | 1500 / 4.88 ≈ 307 |
| 2000μs | 410 ticks | 2000 / 4.88 ≈ 410 |
| 2500μs | 512 ticks | 2500 / 4.88 ≈ 512 |

### Why Use Ticks Instead of Microseconds?

1. **Direct Hardware Control**: No conversion overhead
2. **Precision**: Exact 12-bit control over PWM signal
3. **Flexibility**: Works with any frequency setting
4. **Servo Compatibility**: Some servos need non-standard pulse widths

### Default Tick Values

- **MIN (0°)**: 102 ticks ≈ 500μs
- **MAX (180°)**: 512 ticks ≈ 2500μs

These are starting values. **Always calibrate for your specific servos!**

## Serial Command Reference

The ESP32 accepts the following commands via serial (115200 baud):

### Control Commands

```
TICK <channel> <value>
  Set PWM tick value directly
  - channel: 0-15
  - value: 0-4095
  Example: TICK 0 307

ANGLE <channel> <angle>
  Set servo angle using calibration
  - channel: 0-15
  - angle: 0.0-180.0
  Example: ANGLE 0 90.0
```

### Calibration Commands

```
CAL <channel> <min_tick> <max_tick>
  Set calibration for one channel
  - channel: 0-15
  - min_tick: 0-4095 (0° position)
  - max_tick: 0-4095 (180° position)
  Example: CAL 0 102 512

CAL_ALL <min_tick> <max_tick>
  Set calibration for all channels
  Example: CAL_ALL 102 512

GET_CAL <channel>
  Get calibration for specific channel
  Returns: CAL_DATA <channel> <min> <max>
  Example: GET_CAL 0

GET_ALL_CAL
  Get all channel calibrations
  Returns multiple lines:
    ALL_CAL_DATA
    0 102 512
    1 102 512
    ...
    15 102 512
    END_CAL_DATA
```

### Device Commands

```
FREQ <frequency>
  Set PWM frequency
  - frequency: 40-1000 Hz
  Example: FREQ 50

SLEEP
  Put PCA9685 in sleep mode
  
WAKE
  Wake PCA9685 from sleep mode
  
RESET
  Reset to default configuration
  
INFO
  Print current configuration
```

### Response Format

All commands return responses:
- Success: `OK: <message>`
- Error: `ERROR: <message>`

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to ESP32
- ✅ Check USB cable connection
- ✅ Verify correct COM port selected
- ✅ Ensure ESP32 drivers are installed
- ✅ Try pressing ESP32 reset button
- ✅ Check if another application is using the port

**Problem**: "Access Denied" error
- ✅ Close Arduino Serial Monitor
- ✅ Close other serial terminal applications
- ✅ Disconnect and reconnect USB cable

### Servo Issues

**Problem**: Servo buzzing or jittering
- ✅ Tick value is outside servo's range
- ✅ Reduce MIN or increase MAX tick values
- ✅ Check servo power supply voltage (should be 5-6V)
- ✅ Ensure adequate power supply current rating

**Problem**: Servo doesn't move full range
- ✅ Increase the range between MIN and MAX ticks
- ✅ Some servos have limited rotation (check servo specs)
- ✅ Recalibrate using Calibration tab

**Problem**: Servo moves in wrong direction
- ✅ This is normal - swap MIN and MAX tick values
- ✅ Or adjust angles in software (180-angle)

**Problem**: Servo moves to wrong angles
- ✅ Recalibrate servo in Calibration tab
- ✅ Verify calibration was sent to device
- ✅ Check that calibration is saved in settings.json

### Power Issues

**Problem**: Servos moving erratically
- ✅ Insufficient power supply current
- ✅ Add capacitor (100-1000μF) across servo power supply
- ✅ Use separate power supply for servos (don't use USB power)

**Problem**: ESP32 resets when servos move
- ✅ Ensure common ground between all components
- ✅ Separate servo power from ESP32 power
- ✅ Add capacitors for power filtering

### Software Issues

**Problem**: GUI not launching
- ✅ Ensure Python 3.7+ is installed
- ✅ Install requirements: `pip install -r requirements.txt`
- ✅ On Linux: Install tkinter: `sudo apt-get install python3-tk`

**Problem**: Settings not saving
- ✅ Check write permissions in application directory
- ✅ Manually save to different location using "Save As..."
- ✅ Verify settings.json is valid JSON format

### ESP-NOW Wireless Issues (Mode 2 Only)

**Problem**: Master can't communicate with slave
- ✅ Verify slave MAC address is correctly entered in master code
- ✅ Ensure both ESP32s are powered on
- ✅ Check they're within range (50m indoors, 200m outdoors)
- ✅ Restart both ESP32s (power cycle)
- ✅ Use master's Serial Monitor command `GET_MAC` to verify configuration

**Problem**: Intermittent connection drops
- ✅ Check for WiFi interference (2.4GHz band)
- ✅ Move away from WiFi routers, microwaves, or other 2.4GHz devices
- ✅ Reduce distance between master and slave
- ✅ Check slave ESP32 power supply (insufficient power causes instability)
- ✅ Add decoupling capacitor (100μF) near ESP32 slave power pins

**Problem**: Commands delayed or slow
- ✅ This is normal - wireless has slightly higher latency than USB
- ✅ ESP-NOW latency is typically 10-30ms (vs 5-10ms for Serial)
- ✅ Avoid sending commands too rapidly (add 20ms delay between commands)
- ✅ Check for packet loss (Serial Monitor on master shows "send failed")

**Problem**: Master shows "Slave MAC not configured" warning
- ✅ You haven't updated the SLAVE_MAC_ADDRESS in master code
- ✅ Upload slave code first, note its MAC address
- ✅ Edit master code to include slave's MAC address
- ✅ Re-upload master code

**Problem**: Can see MAC address but still no communication
- ✅ Ensure MAC address format is correct: {0x24, 0x6F, 0x28, 0xAB, 0xCD, 0xEF}
- ✅ Check for typos in MAC address (common with manual entry)
- ✅ Some ESP32 clones have unusual MAC addresses - verify via Serial Monitor
- ✅ Try uploading both sketches again (fresh start)

**Problem**: Compilation errors about callback functions
- ✅ Update ESP32 Arduino Core to 3.0.0+ via Boards Manager
- ✅ The code uses new callback format: `esp_now_register_recv_cb(esp_now_recv_cb_t(onDataRecv))`
- ✅ If using older core (<2.0.0), remove the `esp_now_recv_cb_t()` cast
- ✅ Reference: [ESP-NOW compatibility issue thread](https://randomnerdtutorials.com/esp-now-esp32-arduino-ide/)
- ✅ **Confidence: 99%** - This is a known ESP32 core version compatibility issue

## Advanced Configuration

### Custom PWM Frequency

Different devices require different frequencies:
- **Servos**: 50 Hz (standard)
- **ESCs**: 50-400 Hz
- **LEDs**: 200-1000 Hz (higher = less flicker)

**Note**: Changing frequency affects tick-to-pulse width conversion. Always recalibrate after changing frequency.

### Using with Different Servos

**High-torque servos** may need:
- Wider pulse range (e.g., 50-600 ticks)
- Lower frequency (40-50 Hz)

**Digital servos** may need:
- Standard or narrow pulse range
- Higher frequency (50-300 Hz)

**Continuous rotation servos**:
- 0° = full reverse
- 90° = stop
- 180° = full forward

### Multiple PCA9685 Boards

The code can be modified to support up to 62 PCA9685 boards by changing the I2C address:

```cpp
// In Arduino code
#define PCA9685_ADDRESS 0x40  // Board 1
// #define PCA9685_ADDRESS 0x41  // Board 2, etc.
```

Each board adds 16 more channels (up to 992 servos total!).

## Project Structure

```
RollopodCodes/
├── esp32_pca9685_controller/
│   └── esp32_pca9685_controller.ino    # Direct Serial mode firmware (Option A)
├── esp32_master_bridge/
│   └── esp32_master_bridge.ino         # ESP-NOW master (PC bridge) (Option B)
├── esp32_slave_pca9685/
│   └── esp32_slave_pca9685.ino         # ESP-NOW slave (robot controller) (Option B)
├── esp32_i2c_scanner/
│   └── esp32_i2c_scanner.ino           # I2C device scanner utility
├── servo_controller_gui.py              # Main GUI application
├── requirements.txt                     # Python dependencies
├── settings.json                        # Calibration settings (auto-generated)
├── QUICK_START.md                       # Quick reference guide
├── CHANGELOG.md                         # Version history
└── README.md                            # This file (comprehensive guide)
```

## Technical Specifications

### PCA9685 Specifications
- **Resolution**: 12-bit (4096 steps)
- **PWM Frequency**: 40-1000 Hz (adjustable)
- **Channels**: 16 independent channels
- **I2C Address**: 0x40 (default, can change to 0x41-0x7F)
- **Logic Voltage**: 3.3V or 5V
- **Output Voltage**: Same as V+ (typically 5-6V for servos)

### ESP32 Specifications
- **I2C Pins**: GPIO21 (SDA), GPIO22 (SCL)
- **Serial Baud Rate**: 115200
- **Operating Voltage**: 3.3V logic, 5V USB power
- **ESP-NOW Protocol**: 2.4GHz wireless, up to 250 bytes per packet
- **WiFi Mode**: Station mode (for ESP-NOW, no AP connection needed)

### Performance

**Mode 1: Direct Serial**
- **Command Latency**: ~5-10ms
- **Serial Buffer**: Handles rapid commands
- **Update Rate**: Limited by serial communication (~100Hz max)
- **Range**: USB cable length (typically 1-3m)

**Mode 2: ESP-NOW Wireless**
- **Command Latency**: ~10-30ms (wireless overhead)
- **Packet Size**: Up to 250 bytes per transmission
- **Update Rate**: ~50Hz recommended (avoid flooding)
- **Range**: 50-100m indoors, 200m+ outdoors (line of sight)
- **Reliability**: 95-99% packet delivery in good conditions

**Confidence: 85%** - Actual performance varies with environment, interference, and ESP32 variant. Numbers based on typical ESP-NOW deployments.

## Mathematical Details

### Angle to Tick Conversion

The system uses linear interpolation to map angles to tick values:

```
tick = tick_min + (angle / 180.0) × (tick_max - tick_min)
```

**Example:**
- Calibration: MIN=102 ticks, MAX=512 ticks
- Angle: 90°
- Calculation: 102 + (90/180) × (512-102) = 102 + 0.5 × 410 = 307 ticks

**Confidence Level: 95%** - This linear mapping works for 95% of servos. Some high-precision servos may have non-linear characteristics requiring polynomial correction.

### Tick to Microseconds Conversion

```
pulse_width_μs = (tick / 4096) × (1,000,000 / frequency)
```

**Example at 50 Hz:**
- Tick: 307
- Calculation: (307/4096) × (1,000,000/50) = 0.075 × 20,000 = 1,500μs

**Confidence Level: 99%** - This calculation is mathematically exact based on PCA9685 specifications.

## Safety Considerations

⚠️ **Important Safety Notes:**

1. **Power Supply**
   - Never power servos from USB (insufficient current)
   - Use regulated 5-6V supply with adequate current rating
   - Calculate current: servos × 500mA (minimum)

2. **Wiring**
   - Always connect common ground
   - Double-check polarity before powering up
   - Use appropriate wire gauge for current

3. **Testing**
   - Start with single servo before connecting all 16
   - Test at reduced speed initially
   - Keep hands clear of moving servos

4. **Calibration**
   - Never force servos beyond mechanical limits
   - Listen for buzzing (indicates limit reached)
   - Adjust tick values if servo strains

## License

This project is open-source and free to use for personal and commercial applications.

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## Support

For questions, issues, or suggestions:
1. Check the Troubleshooting section
2. Review the Serial Command Reference
3. Open an issue with detailed information about your setup

## Version History

### Version 3.0 (Current - November 2025)
- ✅ **ESP-NOW Wireless Support**: Dual ESP32 setup for mobile robots
- ✅ Master/Slave architecture for untethered operation
- ✅ Up to 200m wireless range
- ✅ Transparent bridge mode (GUI unchanged)
- ✅ Comprehensive ESP-NOW troubleshooting
- ✅ Updated documentation with both operating modes

### Version 2.0
- ✅ Tick-based PWM control
- ✅ Per-channel calibration
- ✅ Tabbed GUI interface
- ✅ Settings persistence (JSON)
- ✅ Real-time and manual control modes
- ✅ Enhanced testing features

### Version 1.0
- Basic microsecond-based control
- Single-window GUI
- No calibration persistence

---

**Made with ❤️ for Rollopod Project**

*Last Updated: November 2025*

