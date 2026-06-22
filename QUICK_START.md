# Quick Start Guide

## 🚀 5-Minute Setup

### 1. Hardware Setup (2 minutes)
```
ESP32 ──→ PCA9685
GPIO21 ──→ SDA
GPIO22 ──→ SCL
GND ────→ GND

PCA9685 Power:
VCC ────→ 5V (logic)
V+ ─────→ 5-6V External (servos)
GND ────→ GND
```

### 2. Upload Firmware (2 minutes)
1. Open `esp32_pca9685_controller/esp32_pca9685_controller.ino`
2. Select Board: **ESP32 Dev Module**
3. Select Port
4. Click **Upload**

### 3. Launch GUI (1 minute)
```bash
python servo_controller_gui.py
```

## 🎯 First Time Calibration

### Step 1: Connect
- **Connection Tab** → Select COM port → **Connect**

### Step 2: Calibrate One Channel
- **Calibration Tab** → Select Channel 0
- Default values: MIN=102, MAX=512
- Click **Test Min** → Servo moves to 0°
  - If buzzing: Increase MIN value
  - If not reaching limit: Decrease MIN value
- Click **Test Max** → Servo moves to 180°
  - If buzzing: Decrease MAX value
  - If not reaching limit: Increase MAX value
- Click **Test Angle** with 90° → Verify center position

### Step 3: Apply to All (If servos are identical)
- Set Global MIN and MAX values
- Click **Apply to All**
- Click **Send to Device**

### Step 4: Save Settings
- **Settings Tab** → **Save Settings**

## 🎮 Control Your Servos

### Manual Mode
- **Control Tab** → Select "Manual" mode
- Move sliders or enter angles
- Click **Set** to send commands

### Real-time Mode
- **Control Tab** → Select "Real-time" mode
- Move sliders → Servos move immediately

### Quick Presets
- **All to 0°** → All servos to minimum
- **All to 90°** → All servos to center
- **All to 180°** → All servos to maximum

## 📊 Understanding Ticks

**PWM Tick Values at 50Hz:**
| Pulse Width | Tick Value | Typical Servo Position |
|------------|------------|----------------------|
| 500μs | 102 | 0° (Min) |
| 1000μs | 205 | 45° |
| 1500μs | 307 | 90° (Center) |
| 2000μs | 410 | 135° |
| 2500μs | 512 | 180° (Max) |

**Formula:**
```
tick = (pulse_width_μs / 4.88)
angle_tick = MIN + (angle/180) × (MAX-MIN)
```

## 🔧 Common Calibration Values

| Servo Type | Typical MIN | Typical MAX |
|-----------|------------|------------|
| Standard SG90 | 102 | 512 |
| MG995 | 90 | 520 |
| High Torque | 80 | 550 |
| Digital Servo | 120 | 500 |
| Continuous Rotation | 102 | 512 |

**Note:** These are starting points. Always calibrate your specific servos!

## ⚡ Serial Commands Cheat Sheet

### Direct Control
```bash
TICK 0 307        # Set channel 0 to tick 307
ANGLE 0 90.0      # Set channel 0 to 90 degrees
```

### Calibration
```bash
CAL 0 102 512     # Calibrate channel 0
CAL_ALL 102 512   # Calibrate all channels
GET_CAL 0         # Get channel 0 calibration
GET_ALL_CAL       # Get all calibrations
```

### Device
```bash
FREQ 50           # Set frequency to 50Hz
SLEEP             # Sleep mode
WAKE              # Wake up
RESET             # Reset to defaults
INFO              # Show configuration
```

## 🐛 Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| Servo buzzing | Reduce tick range (increase MIN or decrease MAX) |
| Not full range | Increase tick range (decrease MIN or increase MAX) |
| Wrong angle | Recalibrate in Calibration tab |
| Erratic movement | Check power supply current rating |
| ESP32 resets | Separate servo power, add capacitor |
| Can't connect | Close Serial Monitor, check COM port |

## 💡 Pro Tips

1. **Test with one servo first** before connecting all 16
2. **Save settings often** during calibration
3. **Use Manual mode** for precise positioning
4. **Use Real-time mode** for smooth animations
5. **Label your servos** with their channel numbers
6. **Keep backup** of settings.json file

## 🎨 GUI Tab Overview

```
┌─────────────────────────────────────┐
│  [Connection] [Calibration] [Control] [Settings]  │
├─────────────────────────────────────┤
│  Connection Tab:                     │
│    - Serial connection               │
│    - PWM frequency                   │
│    - Device controls                 │
│                                       │
│  Calibration Tab:                    │
│    - Per-channel tick ranges         │
│    - Test min/max/angle buttons      │
│    - Global calibration              │
│                                       │
│  Control Tab:                        │
│    - Manual/Real-time modes          │
│    - 16 channel sliders              │
│    - Quick presets                   │
│                                       │
│  Settings Tab:                       │
│    - Save/Load settings              │
│    - Configuration display           │
│    - Reset to defaults               │
└─────────────────────────────────────┘
```

## 📝 Workflow Examples

### Example 1: Calibrate All Channels
1. Connect to ESP32
2. Go to Calibration tab
3. For each channel (0-15):
   - Click Test Min → Adjust if needed
   - Click Test Max → Adjust if needed
   - Click Test with 90° → Verify
4. Click "Send to Device"
5. Go to Settings tab → Save Settings

### Example 2: Control Multiple Servos
1. Connect to ESP32
2. Go to Control tab
3. Set mode to Manual
4. Adjust multiple sliders
5. Click each Set button
6. Or: Set mode to Real-time for immediate response

### Example 3: Create Servo Pattern
1. Control Tab → Manual mode
2. Set servo positions:
   - Ch 0: 0°
   - Ch 1: 45°
   - Ch 2: 90°
   - Ch 3: 135°
   - Ch 4: 180°
3. Click Set buttons in sequence

## 🔗 Files You'll Work With

```
Your Project/
├── esp32_pca9685_controller.ino  ← Upload to ESP32
├── servo_controller_gui.py       ← Run this
├── settings.json                 ← Auto-created, edit if needed
└── README.md                     ← Full documentation
```

## ✅ Success Checklist

- [ ] Hardware connected correctly
- [ ] ESP32 firmware uploaded
- [ ] GUI launches without errors
- [ ] Successfully connected to ESP32
- [ ] At least one servo calibrated
- [ ] Settings saved to settings.json
- [ ] Can control servo from Control tab
- [ ] Settings persist after restart

---

**Need more help?** Check `README.md` for comprehensive documentation!

