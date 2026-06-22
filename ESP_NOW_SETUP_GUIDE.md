# ESP-NOW Wireless Setup Guide

Complete step-by-step guide for setting up the dual ESP32 wireless configuration.

## 📋 What You'll Need

- 2× ESP32 development boards
- 2× USB cables
- Arduino IDE installed (1.8.13+ or Arduino IDE 2.x)
- **ESP32 Arduino Core 2.0.0 or higher** (3.0.0+ recommended)
- This codebase downloaded
- 10-20 minutes of setup time

### Installing/Updating ESP32 Core

If you haven't installed the ESP32 board support or need to update:

1. Open Arduino IDE
2. **File** → **Preferences**
3. In "Additional Board Manager URLs", add:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. **Tools** → **Board** → **Boards Manager**
5. Search for "esp32"
6. Install or update to **version 3.0.0 or higher**
7. Restart Arduino IDE

**Why this matters:** ESP-NOW callback registration changed in Core 3.0.0. The code in this project is compatible with the newer format. Reference: [Random Nerd Tutorials ESP-NOW Guide](https://randomnerdtutorials.com/esp-now-esp32-arduino-ide/)

## 🎯 Quick Overview

You'll be configuring two ESP32 boards:
1. **Master (Bridge)**: Stays with your PC, converts Serial → ESP-NOW
2. **Slave (Robot)**: Goes on your robot, receives ESP-NOW → controls servos

## 📝 Step-by-Step Instructions

### Step 1: Identify Your ESP32 Boards

Label your two ESP32 boards:
- **Board A**: "SLAVE" (sticker/marker on the board)
- **Board B**: "MASTER" (sticker/marker on the board)

This helps avoid confusion during setup!

### Step 2: Get the Slave's MAC Address

#### 2.1 Connect Slave ESP32 to PC
- Connect Board A (SLAVE) to your PC via USB
- Open Arduino IDE

#### 2.2 Upload Slave Code
1. **File** → **Open** → Navigate to `esp32_slave_pca9685/esp32_slave_pca9685.ino`
2. **Tools** → **Board** → Select **ESP32 Dev Module**
3. **Tools** → **Port** → Select the correct COM port
4. Click **Upload** button (→)
5. Wait for "Done uploading" message

#### 2.3 Read the MAC Address
1. Click **Serial Monitor** button (magnifying glass icon in top-right)
2. Set baud rate to **115200** (bottom-right dropdown)
3. Look for this line in the output:

```
========================================
ESP32 Slave PCA9685 Controller - ESP-NOW
========================================

*** SLAVE MAC ADDRESS: 24:6F:28:AB:CD:EF ***
*** Copy this MAC to master ESP32 sketch ***
```

#### 2.4 Write Down the MAC Address

**IMPORTANT**: Write this MAC address down carefully!

```
My Slave MAC Address: __ : __ : __ : __ : __ : __
```

Example: `24:6F:28:AB:CD:EF`

**Confidence: 100%** - This MAC address is unique to your ESP32 and won't change.

### Step 3: Configure the Master ESP32

#### 3.1 Open Master Code
1. In Arduino IDE: **File** → **Open**
2. Navigate to `esp32_master_bridge/esp32_master_bridge.ino`
3. The file will open in a new window

#### 3.2 Find the MAC Address Configuration

Look for these lines near the top of the code (around line 19):

```cpp
// ============================================================
// IMPORTANT: Replace with your SLAVE ESP32's MAC Address
// Get it by uploading the slave sketch and checking Serial Monitor
// ============================================================
uint8_t SLAVE_MAC_ADDRESS[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
// Example: {0x24, 0x6F, 0x28, 0xAB, 0xCD, 0xEF}
```

#### 3.3 Update with Your Slave's MAC Address

Convert your MAC address from `24:6F:28:AB:CD:EF` format to `{0x24, 0x6F, 0x28, 0xAB, 0xCD, 0xEF}` format:

**Conversion Example:**
- Your MAC: `24:6F:28:AB:CD:EF`
- Code format: `{0x24, 0x6F, 0x28, 0xAB, 0xCD, 0xEF}`

**How to convert:**
1. Add `0x` before each pair of characters
2. Replace colons (`:`) with commas and spaces (`, `)
3. Wrap in curly braces `{ }`

**Replace the line:**

```cpp
// BEFORE (default):
uint8_t SLAVE_MAC_ADDRESS[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

// AFTER (your slave's MAC):
uint8_t SLAVE_MAC_ADDRESS[] = {0x24, 0x6F, 0x28, 0xAB, 0xCD, 0xEF};
```

⚠️ **Common Mistakes:**
- ❌ Missing `0x` prefix: `{24, 6F, ...}` is WRONG
- ❌ Using colons: `{0x24:0x6F:...}` is WRONG
- ❌ Missing commas: `{0x24 0x6F ...}` is WRONG
- ✅ Correct format: `{0x24, 0x6F, 0x28, 0xAB, 0xCD, 0xEF}`

#### 3.4 Upload Master Code

1. **Disconnect** the Slave ESP32 from USB
2. **Connect** Board B (MASTER) to your PC via USB
3. **Tools** → **Port** → Select the Master's COM port
4. Click **Upload** button (→)
5. Wait for "Done uploading" message

### Step 4: Verify the Connection

#### 4.1 Check Master Serial Monitor

1. With Master still connected to PC, open **Serial Monitor** (115200 baud)
2. You should see:

```
========================================
ESP32 Master Bridge - Serial to ESP-NOW
========================================

Master MAC Address: XX:XX:XX:XX:XX:XX

ESP-NOW initialized successfully
Slave peer added successfully

Bridge ready - waiting for Serial commands...
```

✅ If you see "Slave peer added successfully", the MAC address is configured correctly!

❌ If you see errors, double-check the MAC address in the code.

#### 4.2 Power Up the Slave

1. Disconnect Slave from PC (if still connected)
2. Power the Slave using:
   - USB power bank
   - Battery with voltage regulator
   - 5V power supply

The Slave ESP32 should power on (LED indicator should light up).

#### 4.3 Test Communication

With Master connected to PC and Slave powered on:

1. In Master's Serial Monitor, type: `INFO`
2. Press **Enter**
3. You should see a response with servo configuration

**Example successful response:**

```
========== Current Configuration ==========
PWM Frequency: 50 Hz

Channel Configuration:
Ch  | Angle  | Curr Tick | Tick Min | Tick Max
----|--------|-----------|----------|----------
 0  |   90.0 |  307      |  102     |  512
 1  |   90.0 |  307      |  102     |  512
...
==========================================
```

✅ **Success!** Your ESP-NOW link is working!

### Step 5: Test with Python GUI

1. Make sure Master ESP32 is connected to PC via USB
2. Make sure Slave ESP32 is powered and near Master (within 10m for testing)
3. Launch the Python GUI:

```bash
python servo_controller_gui.py
```

4. In the GUI:
   - Go to **Connection** tab
   - Select the Master ESP32's COM port
   - Click **Connect**
   - Try controlling a servo

The GUI doesn't know about the wireless link - it just works!

## 🔧 Troubleshooting

### Problem: Compilation Error - "invalid conversion from 'void (*)(...)'"

**Solution:**
- This means you're using an older ESP32 Arduino Core version
- Update to **ESP32 Core 3.0.0 or higher**:
  - **Tools** → **Board** → **Boards Manager**
  - Search "esp32"
  - Click **Update** (if available)
  - Restart Arduino IDE
- The code uses the new callback format compatible with Core 3.0.0+
- **Confidence: 100%** - This is a well-documented compatibility issue

### Problem: Can't Find MAC Address in Slave Serial Output

**Solution:**
- Check baud rate is set to **115200**
- Press the **RESET** button on the Slave ESP32
- The MAC address is shown at startup
- Scroll to the top of Serial Monitor output

### Problem: Master Says "Slave MAC not configured"

**Solution:**
- You haven't updated the MAC address in master code yet
- Go back to Step 3.3 and update the MAC address
- Re-upload the master code

### Problem: Master Compiles but Shows "Failed to add slave peer"

**Solution:**
- Check MAC address format: `{0x24, 0x6F, 0x28, 0xAB, 0xCD, 0xEF}`
- Make sure you have `0x` before each byte
- Make sure you have commas between bytes
- Try uploading master code again

### Problem: No Response When Sending Commands

**Solution:**
- Verify Slave is powered on (check LED indicator)
- Ensure Slave and Master are within range (start with 2-5m)
- Check for WiFi interference (try different location)
- Power cycle both ESP32s
- Verify MAC address is correct (try Step 2 again)

### Problem: Intermittent Connection

**Solution:**
- Slave power supply may be insufficient
- Try different power source (e.g., USB power bank)
- Check for WiFi/Bluetooth interference
- Reduce distance between boards
- Add 100μF capacitor across Slave's VIN and GND pins

## 📊 Range Testing

Once everything works at close range, test the wireless distance:

1. Start with Master and Slave **2 meters apart**
2. Send command: `INFO`
3. If successful, move Slave **5 meters away**
4. Repeat testing, gradually increasing distance
5. Note where connection becomes unreliable

**Typical ranges:**
- Indoor (office): 30-50m
- Indoor (open space): 50-100m  
- Outdoor (line of sight): 150-250m
- Through walls: 10-30m (varies by construction)

**Confidence: 80%** - Range heavily depends on environment. Metal structures and WiFi networks significantly reduce range.

## 🎓 Understanding MAC Addresses

### What is a MAC Address?

- **MAC** = Media Access Control
- A unique identifier for every network device
- Format: 6 pairs of hexadecimal digits (e.g., `24:6F:28:AB:CD:EF`)
- Cannot be changed (it's burned into the ESP32 chip)

### Why Do We Need It?

ESP-NOW uses MAC addresses to identify devices:
- Master needs to know Slave's MAC to send messages
- Like a phone number - Master "calls" Slave using its MAC address
- Without correct MAC, messages go nowhere

### Can I Use the Same Code for Multiple Robots?

Yes, but each robot needs its own Slave ESP32 with a unique MAC address:

1. Get MAC address of Slave A → Configure Master A
2. Get MAC address of Slave B → Configure Master B
3. Each Master-Slave pair is independent

You can also configure one Master to talk to multiple Slaves (advanced topic).

## 📋 Quick Reference Card

### MAC Address Format Conversion

| Display Format | Code Format |
|----------------|-------------|
| `24:6F:28:AB:CD:EF` | `{0x24, 0x6F, 0x28, 0xAB, 0xCD, 0xEF}` |
| `A0:B1:C2:D3:E4:F5` | `{0xA0, 0xB1, 0xC2, 0xD3, 0xE4, 0xF5}` |

**Pattern:**
```
XX:XX:XX:XX:XX:XX  →  {0xXX, 0xXX, 0xXX, 0xXX, 0xXX, 0xXX}
```

### Master Serial Commands

| Command | Purpose |
|---------|---------|
| `GET_MAC` | Show Master and Slave MAC addresses |
| `HELP` | Show available commands |
| `PING` | Test connection to Slave |
| `INFO` | Get Slave configuration (tests connection) |

All other commands are forwarded to Slave.

## ✅ Checklist

Use this checklist during setup:

- [ ] Two ESP32 boards labeled "Master" and "Slave"
- [ ] Slave code uploaded to Slave ESP32
- [ ] Slave MAC address written down
- [ ] Master code opened in Arduino IDE
- [ ] MAC address converted to correct format
- [ ] MAC address pasted into master code
- [ ] Master code uploaded to Master ESP32
- [ ] Master Serial Monitor shows "peer added successfully"
- [ ] Slave powered on independently
- [ ] Test command (`INFO`) works
- [ ] Python GUI connects to Master
- [ ] Servos respond to GUI commands

## 🎉 Success!

Once all checklist items are complete, your wireless servo controller is ready!

Your robot can now move freely without being tethered to your laptop. The wireless range should be sufficient for most indoor robotics applications.

## 📞 Need Help?

If you're still having trouble:
1. Review the Troubleshooting section above
2. Check main README.md → ESP-NOW Wireless Issues
3. Verify both ESP32s are genuine (not clones with compatibility issues)
4. Try with fresh Arduino IDE installation
5. Test with shorter distance first (1-2 meters)

---

**Last Updated:** November 2025
**Difficulty:** ⭐⭐ Intermediate (15-20 minutes for first-time setup)

