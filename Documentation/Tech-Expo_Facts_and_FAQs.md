# Rollopod — Tech-Expo Operator Guide: Quick Facts & FAQs

---

## 🏆 Project Overview & Meta Information

* **Project Title:** Rollopod — A Transforming Hexapod Robot with Dual-Mode Walking and Rolling Locomotion
* **Team Members:** Parag Patil, Rutu Patel
* **Institution:** Parul Institute of Technology, Parul University
* **Expo Category:** Senior Category
* **Exhibition Theme:** Robotics & Aerial Robotics
* **Future Vision:** Core locomotion platform for the **Modular Robotic Field Assistant (MRFA)**

---

## ⚡ 1. The "30-Second Elevator Pitch"
> *"Rollopod is a transformable hybrid robot that solves the classic mobility dilemma in mobile robotics: wheeled rovers are fast on flat ground but get stuck on obstacles, while walking hexapods can step over anything but crawl slowly and waste energy. Rollopod bridges this gap by using a shared transformable mechanical structure. Its 6 articulated legs fold edge-to-edge into dual 400 mm rolling rings for high-speed travel (up to 7.5 km/h), and unfold into a terrain-adaptive hexapod for stairs, rubble, and rough terrain—all while keeping the central sensor payload upright and stabilized through a bearing-decoupled gravity pendulum."*

---

## 📊 2. Master Quick-Facts Sheet (Numbers & Specs)

| Category | Parameter | Specification / Exact Value |
| :--- | :--- | :--- |
| **Physical Dimensions** | Length × Width × Height | **40 cm × 50 cm × 40 cm** (0.40 m × 0.50 m × 0.40 m) |
| **Mass Breakdown** | Total System Mass | **~11.0 kg** |
| | Left Wheel / Leg Assembly | **~5.0 kg** (45.45%) |
| | Right Wheel / Leg Assembly | **~5.0 kg** (45.45%) |
| | Central Suspended Pod | **~1.0 kg** (9.10%) |
| **Wheel Geometry** | Wheel Outer Diameter ($D$) | **400 mm** (0.40 m / 15.75 in) |
| | Wheel Circumference ($C$) | **1.2566 m** (1256.6 mm) |
| | Arc Segment per Leg (3 per side) | **418.9 mm** per leg arc |
| **Drive Motors** | Rolling Drive Actuators | **2x High-Torque DC Geared Motors** (100 RPM, 25 kg·cm / 2.45 N·m each) |
| | Total Rolling Drive Torque | **≈ 4.90 N·m combined** |
| | Leg Articulation / Transformation | **18x High-Torque Servos** (3 DOF per leg × 6 legs) |
| **Rolling Speeds** | Max Theoretical Speed (100% PWM) | **2.09 m/s (7.54 km/h / 4.68 mph)** |
| | Operating Waddle-Roll Speed | **1.05 – 1.25 m/s (3.8 – 4.5 km/h / 2.4 – 2.8 mph)** |
| **Walking Speeds** | Tripod Gait Cruising Speed | **0.15 – 0.25 m/s (0.54 – 0.90 km/h)** |
| | Max Peak Step Speed | **0.30 m/s (1.08 km/h)** |
| **Electronics & Control** | Microcontrollers | **Master ESP32 Bridge** (Host) + **Slave ESP32-C6** (On-Robot Edge) |
| | Wireless Protocol | **ESP-NOW** Point-to-Point Broadcast (10–30 ms latency) |
| | Motor Drivers | **2x Cytron MD13S** (13A continuous per channel) |
| | Servo PWM Drivers | **Dual PCA9685** 16-Channel 12-Bit I2C PWM Drivers (50 Hz) |
| | Sensor Payload | **MPU6050 6-DOF IMU**, Intel RealSense 3D Depth Camera, LiDAR |
| **Power Architecture** | Logic Battery Rail | **3S 5000 mAh LiPo** (Regulated via DC-DC Buck Converter) |
| | Actuator Battery Rail | **3S 6200 mAh / 2500 mAh LiPo Packs** (Dedicated High-Current Rails) |
| | Grounding Scheme | **Unified Common Ground Topology** |

---

## ❓ 3. Frequently Asked Questions (FAQs) for Operators

---

### 🟢 A. Concept & Novelty Questions

#### Q1: Why not just put regular wheels on the bottom of a hexapod chassis?
* **Technical Answer:** Adding dedicated permanent wheels and separate drive axles adds massive dead weight, increases bulk, reduces ground clearance, and makes the legs vulnerable to catching on obstacles. Rollopod utilizes **shared structural transformation**—the legs *themselves* are the wheels. When folded, the curved, treaded leg links form the outer rolling rings.
* **🗣️ Simple / Live Example to Explain:**
  > *"Sir, think of it like this: if you attach bicycle wheels below a spider’s feet, it becomes too bulky, heavy, and clumsy to walk properly. In Rollopod, it works like a Transformer or an umbrella—when you fold the 3 legs on each side, their outer curved edges snap together to form the outer wheel rim itself. It is a true 2-in-1 mechanism with zero wasted wheel weight!"*

#### Q2: How does Rollopod compare to existing bio-inspired robots like Festo BionicWheelBot?
* **Technical Answer:** Festo’s robot rolls like an acrobat over its entire body, which violently tumbles any cameras or onboard electronics. Rollopod features a **bearing-decoupled suspended central pod** that remains horizontal and forward-facing at all times, allowing continuous LiDAR and 3D depth scanning even while rolling at high speeds.
* **🗣️ Simple / Live Example to Explain:**
  > *"Festo's bot rolls by doing continuous gymnastics somersaults—its whole body tumbles round and round. If you mount a camera on Festo, the video feed will just spin like a washing machine! In Rollopod, our camera pod stays completely still and upright in the middle, while only the outer side rings roll around it. So our sensors can scan the environment uninterrupted."*

---

### ⚙️ B. Mechanical & Kinematic Architecture Questions

#### Q3: How does the central pod stay upright when the robot rolls without flipping over?
* **Technical Answer:** The central ~1 kg pod is mounted on **precision radial ball bearings** around the continuous central rod, with its Center of Gravity (CG) concentrated **below** the axis. It acts as a **passive gravity-biased pendulum**. Gravity holds the pod level and facing forward, completely isolating the sensitive sensors from the rotation of the outer rings. It does **not** require complex Segway-style inverted-pendulum balancing.
* **🗣️ Simple / Live Example to Explain:**
  > *"Think of a grandfather clock pendulum or a passenger standing in a Metro train holding the overhead grab handle. Because all the heavy parts (batteries, boards) are located down in the bottom of the pod, gravity naturally pulls it straight downward. The wheels spin freely around the axle on bearings, so the pod never flips or tumbles."*

#### Q4: What is the central rod, and does it spin freely?
* **Technical Answer:** The central rod is a **single rigid reaction rod** that is rigidly locked to both motor rotor shafts. It forms one mechanically coupled rotating assembly. It is **NOT** fixed to the chassis, **NOT** fixed to the ground, and does **NOT** spin like a free idler.
* **🗣️ Simple / Live Example to Explain:**
  > *"Think of a solid metal axle directly locking both motor shafts together from inside. It's not a loose dummy rod, and it's not bolted solid to the body either. It is a locked reaction shaft that couples the motors together, while the center pod simply hangs over it on smooth bearings."*

#### Q5: How can Rollopod roll forward if both motor rotors are locked to the same rod without a tail/skid?
* **Technical Answer:** This is Rollopod’s proprietary **Dynamic Torque Anchoring (Waddle-Roll Gait)**. Instead of raw on/off pulses, both motors operate on a base PWM (50–60%) overlaid with a 180° phase-shifted low-frequency sine wave (1.5 Hz – 3.0 Hz). When the left motor torque rises and the right decreases, the robot uses the internal gearbox resistance and inertia of the right wheel as a temporary dynamic brace to push the left side forward, and vice versa. This creates smooth, tail-less forward rolling.
* **🗣️ Simple / Live Example to Explain:**
  > *"Think of how a human walks or how someone skates: you firmly plant your right foot down on the ground as an anchor to push your left foot forward, and then you shift weight and push the other side. Rollopod does the exact same thing electrically! One motor acts as a temporary brake/anchor against the ground while the opposite motor pushes forward. It does a rapid 'waddling' roll from side to side, so it moves straight ahead smoothly without needing any tail or support wheel dragging behind it."*

#### Q6: Can Rollopod turn in place (zero-radius steering)?
* **Technical Answer:** **Yes!** When the left and right DC motors are commanded in opposite directions (`LEFT_MOTOR = CW`, `RIGHT_MOTOR = CCW`), the stator reactions push the two 5 kg side assemblies in opposite directions, executing a 360° zero-radius skid turn on the spot.
* **🗣️ Simple / Live Example to Explain:**
  > *"Exactly like a military battle tank or a JCB excavator! If the left wheel rolls forward and the right wheel rolls in reverse, the robot spins 360 degrees on its own center point without needing any turning circle."*

---

### 🔌 C. Electronics, Power & Wireless Control Questions

#### Q7: How do you prevent high servo currents from resetting or crashing the microcontrollers?
* **Technical Answer:** We use an **Isolated Dual-Power Architecture**. Logic electronics (ESP32, IMU, sensors) run on a dedicated 3S LiPo battery through a regulated buck converter. High-current actuators (18 servos + 2 Cytron DC drivers) draw from separate heavy-duty LiPo packs. Both rails share a **unified common ground** to guarantee clean I2C communication without inductive voltage dips (brownouts).
* **🗣️ Simple / Live Example to Explain:**
  > *"Imagine running a heavy water pumping motor and your sensitive home Wi-Fi router on the exact same weak inverter line. Whenever the motor kicks in, the voltage drops and the Wi-Fi resets. To prevent that, we have 2 completely separated power channels: one clean battery solely for the brain (ESP32 microcontrollers and sensors), and separate heavy-duty batteries for the 18 servos and DC drive motors. Common ground ties them together so signals stay crystal clear."*

#### Q8: What wireless protocol is used, and why not standard Wi-Fi or Bluetooth?
* **Technical Answer:** We use **ESP-NOW** (point-to-point wireless broadcast by Espressif). Standard Wi-Fi has unpredictable packet buffering (100–300 ms) and connection drops. ESP-NOW provides **deterministic low-latency communication (10–30 ms)** without needing an external Wi-Fi router.
* **🗣️ Simple / Live Example to Explain:**
  > *"Normal Wi-Fi is like sending messages through a busy local network router—it can lag, buffer, or drop when crowded at a tech expo. ESP-NOW is like an instant military walkie-talkie: direct chip-to-chip transmission with ultra-low delay (under 30 milliseconds) and zero pairing hassle."*

#### Q9: What happens if an ESP-NOW wireless packet drops during rolling? Will the motors de-sync?
* **Technical Answer:** **No.** We use **Edge Parametric Calculation**. The master controller only sends a small broadcast packet containing the gait mathematical parameters (`Base_PWM`, `Amplitude`, `Frequency`). When received, both ESP32-C6 motor controllers reset their internal hardware timers (`micros()`) to `t=0` simultaneously and calculate the sine wave locally on the chip. Even if wireless communication drops for several seconds, both motors remain in absolute mathematical lockstep.
* **🗣️ Simple / Live Example to Explain:**
  > *"Instead of constantly screaming speed numbers every millisecond over the air, the laptop just sends a single formula: 'Run at 50% power with a 2 Hz sine wave'. Both wheels start their stopwatches at the exact same microsecond and calculate the speed locally on their own chips. Even if the laptop signal disconnects for 5 seconds, both wheels stay in 100% perfect mathematical rhythm."*

#### Q10: How do you prevent the motors from back-driving when one is stopped?
* **Technical Answer:** Each motor has a **Quadrature Optical/Magnetic Encoder** running at 50 Hz on the ESP32-C6. When speed is commanded to zero, the controller latches its position (`P_hold`) and runs an **Active Zero-Speed Position Hold PID**, instantly applying counter-torque to lock the shaft against any reaction torque transmitted through the central rod.
* **🗣️ Simple / Live Example to Explain:**
  > *"Think of the Hill-Hold feature in modern cars. When you stop on a steep flyover, the car brakes lock so you don't roll backward. Here, if one motor is turned off and the other motor tries to violently twist it through the central rod, the encoder senses the tiny twist and immediately fires counter-power to freeze the motor shaft rock-solid in place."*

---

### 🛠️ D. Prototype Evolution & Materials Questions

#### Q11: What materials were used to build the physical prototype?
* **Technical Answer:** 
  * **Structure:** High-strength aluminium extrusion frame and CNC-machined carbon fibre linkage plates for high stiffness-to-weight ratio.
  * **Leg Appendages:** Redesigned CNC powder-coated steel legs to handle high dynamic ground impacts.
  * **Bearings:** Industrial-grade deep-groove radial ball bearings for pod decoupling.
* **🗣️ Simple / Live Example to Explain:**
  > *"We used aluminium and carbon fibre for the inner chassis so the robot stays lightweight, but we upgraded the legs to heavy-duty laser-cut powder-coated steel so it can take hard drops, rough stepping, and sudden impacts without bending."*

#### Q12: What design challenges were discovered during prototype testing?
* **Technical Answer:**
  1. **Gearbox Failure:** Early tests with standard plastic-gear DC motors stripped teeth under heavy shock loads; we upgraded to all-metal 25 kg·cm steel gearboxes.
  2. **Current Spikes:** Simultaneous 18-servo movement caused voltage dips, which led directly to the implementation of the isolated dual-battery power rail.
  3. **Ground Indexing:** Before unfolding into walking mode, the robot uses IMU orientation feedback to verify that legs are facing downward toward the ground before opening.
* **🗣️ Simple / Live Example to Explain:**
  > *"In our early testing, two main practical issues happened: first, normal plastic motor gears stripped instantly under the robot's 11 kg weight, so we upgraded to all-metal steel gearboxes. Second, moving 18 servos together created huge power spikes, which led to our dual isolated battery system. Also, before opening the legs, the IMU gyro checks that the robot isn't upside down so legs always touch the floor safely."*

---

### 🚀 E. Real-World Applications & Future Scope

#### Q13: What are the practical applications of Rollopod?
* **Technical Answer:**
  1. **Search & Rescue in Disasters:** Rapidly rolls over paved roads to reach disaster zones, then unfolds into hexapod mode to climb through collapsed concrete rubble, stairs, and voids.
  2. **Industrial & Pipeline Inspection:** Traverses smooth factory floors and pipeline corridors in rolling mode, stepping over curbs, pipes, and obstacles without stopping.
  3. **Agricultural Surveying:** Navigates muddy fields and furrowed crop rows without compacting soil or damaging plant beds.
  4. **Planetary / Subterranean Exploration:** Enters uncharted caves, craters, and rough terrains where traditional 4-wheel rovers get permanently trapped.
* **🗣️ Simple / Live Example to Explain:**
  > *"Take an earthquake disaster in a building: a standard 4-wheeled rover gets stuck at the first broken staircase. A drone can't enter narrow rubble pockets without crashing. Rollopod can roll fast for 5 km on the road, reach the disaster site, and then unfold its 6 legs to climb over shattered concrete slabs, climb steps, and find trapped people using its thermal camera."*

#### Q14: What is the MRFA vision?
* **Technical Answer:** Rollopod is the mobility subsystem for the **Modular Robotic Field Assistant (MRFA)**. Future MRFA units will feature hot-swappable payload bays (thermal cameras, gas detectors, robotic manipulator arms), edge AI for real-time terrain classification, and collaborative multi-robot swarm mapping in GPS-denied environments.
* **🗣️ Simple / Live Example to Explain:**
  > *"Rollopod is designed as a universal mobile base. In the future, like swapping lenses on a DSLR camera, you can snap on a robotic arm for bomb disposal, a pesticide sprayer for farm fields, or toxic gas sensors for coal mines—without changing the core walking and rolling chassis."*

---

## 🎯 4. Operator Quick Cheat-Sheet (At-A-Glance Numbers)

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        ROLLOPOD AT A GLANCE                            │
├────────────────────────────────┬───────────────────────────────────────┤
│ Mass                           │ 11 kg (5 kg Left + 5 kg Right + 1 kg Pod)│
│ Dimensions                     │ 40 cm (L) × 50 cm (W) × 40 cm (H)     │
│ Outer Wheel Diameter           │ 400 mm (15.75 inches)                 │
│ Rolling Speed (Operating)      │ 1.05 – 1.25 m/s (~4.0 km/h)           │
│ Rolling Speed (Top Max)        │ 2.09 m/s (7.54 km/h)                  │
│ Walking Speed (Tripod Gait)    │ 0.15 – 0.25 m/s (~0.7 km/h)           │
│ DC Drive Torque                │ 25 kg·cm (2.45 N·m) × 2 = 4.90 N·m    │
│ Total Servos                   │ 18x High-Torque Servos (PCA9685 @ 50Hz)│
│ Wireless Communication         │ ESP-NOW (10–30 ms low latency)        │
│ Power Architecture             │ Fully Isolated Logic & Actuator Rails │
└────────────────────────────────┴───────────────────────────────────────┘
```
