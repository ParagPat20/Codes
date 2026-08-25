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
| **Actuators** | Rolling Drive Actuators | **2x High-Torque DC Geared Motors** (100 RPM, 25 kg·cm / 2.45 N·m each) |
| | Total Rolling Drive Torque | **≈ 4.90 N·m combined** |
| | Leg Articulation / Transformation | **20x High-Torque Servos** (Multi-DOF leg joints & transformation) |
| **Rolling Speeds** | Max Theoretical Speed (100% PWM) | **2.09 m/s (7.54 km/h / 4.68 mph)** |
| | Operating Waddle-Roll Speed | **1.05 – 1.25 m/s (3.8 – 4.5 km/h / 2.4 – 2.8 mph)** |
| **Walking Speeds** | Tripod Gait Cruising Speed | **0.15 – 0.25 m/s (0.54 – 0.90 km/h)** |
| | Max Peak Step Speed | **0.30 m/s (1.08 km/h)** |
| **Electronics Topology** | Distributed Microcontrollers | **ESP32 Sub-Master Head** (Central Pod) + **2x ESP32 Slaves** (Left & Right Sides) + **Remote ESP32** (Host Bridge) |
| | Wireless Protocol | **ESP-NOW** Point-to-Point Broadcast (10–30 ms latency) |
| | Actuator Drivers | **2x PCA9685** 16-Channel 12-Bit PWM Drivers (1 per side) + **2x Cytron MD13S** Motor Drivers (1 per side) |
| | Processing & Sensors | **Raspberry Pi 5**, **MPU6050 6-DOF IMU**, Intel RealSense 3D Depth Camera, LiDAR |
| **Power Distribution** | Central Pod Logic Supply | **Dedicated 5V Power Bank** (Powering Pi 5, ESP32 Sub-Master, Sensors) |
| | Left Side Actuator Supply | **Dedicated 3S LiPo Battery** (Powering Left ESP32 Slave, Left PCA9685, Left Cytron & Servos) |
| | Right Side Actuator Supply | **Dedicated 3S LiPo Battery** (Powering Right ESP32 Slave, Right PCA9685, Right Cytron & Servos) |
| | Grounding Scheme | **Unified Common Ground Topology** across isolated battery sections |

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
* **Technical Answer:** Rollopod achieves forward locomotion by applying a controlled **differential speed** across the two motors. Because both motor rotor output shafts are rigidly locked to the continuous central reaction rod, any speed differential builds up internal torsional torque across the rod. With no free rotational release on the coupled axle, this torque has nowhere to escape and is physically forced through the motor stators directly onto the heavy 5 kg side wheel assemblies against ground traction, propelling the robot forward.
  
  **Crucial Role of Closed-Loop PID:** Because both motors are mechanically linked through the rigid rod, without precise closed-loop speed control, cross-shaft mechanical feedback would occur: the higher-RPM motor would force-rotate and back-drive the lower-RPM motor (making it too easy/freewheeling for the lower-RPM side), causing the higher-RPM motor to heavily struggle under extreme reaction load. To prevent this, each motor uses an onboard **Quadrature Encoder and a 50 Hz PID controller** that continuously regulates motor PWM to strictly maintain the target RPM differential, ensuring balanced dynamic torque anchoring and smooth continuous rolling.
* **🗣️ Simple / Live Example to Explain:**
  > *"Sir, understand the physics like this: both motor shafts are joined together by a solid metal rod in the center. When we give different speeds to left and right motors, a twisting torque builds up on that rod. Because the rod is rigid and locked, that twisting force cannot escape anywhere—so it gets forced straight down onto the wheels against the floor, pushing the robot forward!*
  > 
  > *Now, why do we need the PID controller? Think of two people on a double-seater tandem bicycle with their pedals locked to the same chain. If person A pedals super fast and person B pedals slowly, person A has to struggle heavily and fight the resistance, while person B gets a free ride. Through the central rod, the same thing would happen to our motors! So our 50 Hz PID controller acts like an active power balancer: it checks the exact wheel RPM 50 times every second using optical encoders, dynamically adjusting motor power so the required speed difference is strictly maintained without either motor struggling or stalling."*

#### Q6: Can Rollopod turn in place (zero-radius steering)?
* **Technical Answer:** **Yes!** When the left and right DC motors are commanded in opposite directions (`LEFT_MOTOR = CW`, `RIGHT_MOTOR = CCW`), the stator reactions push the two 5 kg side assemblies in opposite directions, executing a 360° zero-radius skid turn on the spot.
* **🗣️ Simple / Live Example to Explain:**
  > *"Exactly like a military battle tank or a JCB excavator! If the left wheel rolls forward and the right wheel rolls in reverse, the robot spins 360 degrees on its own center point without needing any turning circle."*

---

### 🔌 C. Electronics, Power & Wireless Control Questions

#### Q7: What is the electronic and power distribution setup across the robot? How do you prevent brownouts?
* **Technical Answer:** Rollopod utilizes a fully distributed, physically isolated electronic and power architecture divided into three discrete physical zones:
  1. **Left Side Assembly:** Houses 1 dedicated 3S LiPo battery, 1 ESP32 Slave microcontroller, 1 PCA9685 16-channel PWM driver for left-side servos (10 servos), 1 Cytron MD13S motor driver, and 1 DC drive motor.
  2. **Right Side Assembly:** Houses 1 dedicated 3S LiPo battery, 1 ESP32 Slave microcontroller, 1 PCA9685 16-channel PWM driver for right-side servos (10 servos), 1 Cytron MD13S motor driver, and 1 DC drive motor.
  3. **Central Suspended Pod (Mid Part):** Houses a dedicated **5V Power Bank** that cleanly powers the Raspberry Pi 5 coprocessor, the **ESP32 Sub-Master Head controller**, and onboard sensors (IMU/Cameras). It communicates wirelessly with the operator's **Remote ESP32 bridge** via ESP-NOW.
  
  This complete electrical separation isolates high-current actuator spikes (from 20 servos and 2 DC motors) to their respective rotating side structures, ensuring zero voltage dips (brownouts) reach the central logic processors while eliminating slip-ring wire tangling across the rotating joints.
* **🗣️ Simple / Live Example to Explain:**
  > *"Imagine trying to run a heavy industrial welding machine and a sensitive medical laptop on the exact same weak extension cord—the laptop will immediately restart whenever the machine sparks!*
  > 
  > *To prevent this, Rollopod is split into 3 independent power islands:
  > - **Left Wheel Side:** Has its own battery, its own ESP32 brain, its own PCA servo driver, and its own motor driver.
  > - **Right Wheel Side:** Has its exact identical clone (battery, ESP32, PCA driver, motor driver).
  > - **Middle Pod (Brain & Eyes):** Runs completely off a clean 5V Power Bank powering the Raspberry Pi 5, the ESP32 Sub-Master head, and the camera sensors.
  > 
  > Because each moving wheel carries its own battery, we don't have dangerous thick power cables twisting around the axle, and the central computer never restarts even under peak motor load!"*

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

#### Q11: What manufacturing methods and materials were used to build the physical prototype?
* **Technical Answer:** 
  To achieve high structural rigidity while keeping fabrication costs strictly optimized:
  * **No Costly CNC Machining:** Completely avoided expensive multi-axis CNC milling to make the platform cost-effective and scalable.
  * **Chassis & Structural Plates:** Manufactured exclusively from **Laser-Cut 3.0 mm Aluminium** for high stiffness, structural integrity, and lightweight properties.
  * **Spherical Leg Appendages:** Fabricated from **0.8 mm Sheet Metal Steel plates**, precision CNC bent and powder-coated to form the curved, heavy-impact-resistant spherical rolling rings.
  * **Bearings:** Precision deep-groove radial ball bearings for central pod suspension.
* **🗣️ Simple / Live Example to Explain:**
  > *"Sir, we engineered this to be both high-strength and highly cost-effective! We avoided expensive CNC machining altogether. Instead, we used:
  > 1. **Laser-cut 3 mm Aluminium** for all main structural plates—giving great rigidity while keeping the chassis super light.
  > 2. **0.8 mm Steel sheet metal with precision bending and powder-coating** for the spherical leg structures—giving the legs rugged toughness to survive heavy floor impacts when walking or rolling over obstacles.
  > 
  > This gave us industrial-grade strength at a fraction of typical CNC prototype manufacturing costs!"*

#### Q12: What design challenges and motor sizing compromises occurred during development?
* **Technical Answer:**
  * **Market Actuator Availability Constraints:** Our initial engineering goal was to make the robot as lightweight as possible. Early prototype trials tested smaller micro-gearmotors with a smaller wheel radius; however, these failed due to the strict physics and leverage geometry required for Rollopod's reaction-based rolling (insufficient torque leverage and ground clearance).
  * **System Parameter Harmonization:** Constrained by off-the-shelf commercial components, we shifted to a larger **400 mm wheel diameter** paired with heavy-duty **25 kg·cm high-torque geared motors** (~5 kg per side). We balanced and matched the system equations: equating **Motor Power, Stall Torque, Gearbox Reduction, Wheel Radius, and Total Mass (11 kg)** so that the unique physics of reaction-torque rolling and 20-servo hexapod walking functioned reliably.
  * **Gearbox Durability:** Initial plastic-gear motors stripped under walking torque; we upgraded exclusively to all-metal steel gearboxes.
  * **Ground Indexing:** Prior to unfolding into walking mode, the onboard IMU gyro indexes the rotating rings to verify the legs are pointing downward toward the ground before actuation.
* **🗣️ Simple / Live Example to Explain:**
  > *"When designing a completely new type of robot, theory meets practical market reality! 
  > - Initially, our dream was to make it ultra-light using small toy motors and small wheels. But when we tested it, the physics didn't work—small motors simply didn't have enough leverage or torque to push the robot forward without a tail.
  > - So based on what heavy-duty motors are practically available in the market, we calculated the exact mathematics: we scaled the wheel up to **400 mm diameter** and upgraded to **25 kg·cm high-torque metal motors**. 
  > - We carefully harmonized the motor power, torque, wheel radius, and the 11 kg total weight so that the physics of reaction rolling and 20-servo walking work in perfect balance!"*

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
│ Mass Breakdown                 │ 11 kg (5 kg Left + 5 kg Right + 1 kg Pod)│
│ Physical Dimensions            │ 40 cm (L) × 50 cm (W) × 40 cm (H)     │
│ Outer Wheel Diameter           │ 400 mm (15.75 inches)                 │
│ Rolling Speed (Operating)      │ 1.05 – 1.25 m/s (~4.0 km/h)           │
│ Rolling Speed (Top Max)        │ 2.09 m/s (7.54 km/h)                  │
│ Walking Speed (Tripod Gait)    │ 0.15 – 0.25 m/s (~0.7 km/h)           │
│ DC Drive Motors                │ 2x 100 RPM, 25 kg·cm (2.45 N·m each)  │
│ Total Servos                   │ 20x High-Torque Servos (PCA9685 @ 50Hz)│
│ Microcontroller Setup          │ ESP32 Head + 2x ESP32 Slaves + Remote │
│ Wireless Communication         │ ESP-NOW (10–30 ms low latency)        │
│ Power Setup                    │ 2x 3S LiPos (Sides) + 5V Power Bank   │
│ Structural Materials           │ 3mm Laser-Cut Al + 0.8mm Powder Steel │
└────────────────────────────────┴───────────────────────────────────────┘
```
