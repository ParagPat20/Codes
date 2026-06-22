RolloPod

A Fastest Evolution of Hexapod



Rollopod is not a spherical robot. It is a dual-ring transformable hexapod with a central suspended body where three legs on each side transform into a wheel.

# Physical Architecture

Rollopod consists of:

- One central body module.
- Three legs on each side transform into a wheel.
- Three articulated legs mounted on the left ring.
- Three articulated legs mounted on the right ring.
- Six legs total.

The rolling rings remain visible in all operating modes.

The central body remains suspended between the two rolling rings.

The robot never transforms into a sphere.

# Transformation Mechanism

Walking Mode:

- Six legs fully extended.
- Three legs on each side.
- Robot operates as a hexapod.

Rolling Mode:

- Left legs fold into left rolling ring.
- Right legs fold into right rolling ring.
- Folded legs become part of the rolling structure.
- Two rolling rings provide locomotion.

During transformation:

- Central body remains visible.
- Central body remains suspended.
- No spherical enclosure is formed.

### Transformation States
Rollopod can exist in:

1. **Walking State**
   - All six legs deployed.

2. **Rolling State**
   - Both side rings closed.

3. **Transitional State**
   - One or more legs partially folded.
   - One ring may be deployed while the opposite ring remains closed.
   - Intermediate configurations are mechanically valid and visually important.

In the rapidly evolving field of robotics, there is a constant push for machines that can adapt to diverse environments and overcome complex challenges. Our proposed Rollopod Robot represents a significant leap forward in this pursuit, combining advanced mobility, adaptability, and autonomous capabilities in a single, versatile platform. The hexapod, or six-legged robot, is designed to navigate a wide range of terrains with unprecedented agility and stability. What sets our design of Rollopod apart is its unique ability to transform between walking and rolling modes, allowing it to efficiently traverse both rough terrain and smooth surfaces. This dual-mode locomotion system enables the robot to adapt to changing environments, making it suitable for a variety of applications from search and rescue operations to planetary exploration and keep scanning the environment in Rolling motion.

   

1. Product Concept & Development: 

Hexapod, also known as Six Legged Robot. Hexapod Robot, term hex means six. These types of robots are designed for tasks requiring stability, adaptability to rough terrain, or enhanced mobility in complex environments where traditional wheeled or tracked robots may struggle.

There will be several steps involved in the process of making Hexapod Robot:

Goal: 

Our goal is to create an autonomous hexapod robot capable of navigating various terrains effectively using six legs. One of the main challenges we face with hexapod robots is their speed limitation. Despite our efforts to manipulate the servo mechanisms quickly, hexapods cannot move much faster than rolling robots. However, rolling hexapods available in markets face their own limitations; they cannot scan the environment while in motion. To address this, we aim to develop a new mechanism system that enables the hexapod to perform both rolling and walking motions while simultaneously scanning the environment. To accomplish this, we will focus on several key aspects. 

      Fig 3.1.1 Festo Bionic Wheel Bot

First, we will design and construct a robust mechanical structure using appropriate materials, actuators, and transmission mechanisms to ensure durability and provide sufficient torque for each leg. This structure will also incorporate a rolling mechanism that allows the hexapod to transition seamlessly between walking and rolling modes, enhancing its speed and efficiency on flat or smooth terrains.

Additionally, we will implement efficient gait control algorithms that coordinate the movement of all six legs, adapting to different surface conditions and incorporating sensor feedback for dynamic adjustments. For rolling mode, we will develop algorithms to stabilize the robot and ensure smooth transitions between rolling and walking. To enable environmental scanning during motion, we will integrate advanced sensors, such as LiDAR, cameras, or ultrasonic sensors, into the system. These sensors will provide real-time data about the surroundings, allowing the robot to detect obstacles, map its environment, and adjust its path dynamically, whether it is walking or rolling.By combining these elements, our hexapod robot will achieve a unique balance of speed, adaptability, and environmental awareness, making it capable of navigating complex terrains and performing tasks in dynamic environments effectively. This versatile hexapod robot is designed for a wide range of applications, including search and rescue missions, planetary exploration, agricultural automation, industrial inspection tasks, military operations, disaster inspection, and navigating underground tunnels or confined spaces.

Fig 3.1.2: MorphX Hexapod Bot

Electronic System Architecture:

Fig 4.2.1: Electronic System Architecture

Design and Simulation: 

The first step in making Hexapod Robot will be to design the robot using cad software. This will involve creating a computer-aided design (CAD) model. Then we will simulate the robot for performing above goals that will provide our working and proof of concept.

We are developing a transforming hexapod capable of both walking and rolling. When there's a need to cover long distances quickly, we will utilize the rolling capability of the hexapod. However, in the event of obstacles detected by sensors, the hexapod will autonomously transform, opening its legs to facilitate climbing over obstacles.

Fig 4.3.1: Leg Connector CAD

FIg 4.3.2: Leg CAD

Different Mechanisms:

Transformation Mechanism: 

As we are developing a transforming hexapod robot with capabilities for both walking and rolling. Initially the hexapod robot is in compact dual-ring rolling configuration, where the legs fold inward toward their respective left and right rolling rings. For the transformation mechanism the legs are connected with servos, where the servo motors begin to actuate and move the leg segments. The servos will adjust their angles according to the floor surface. All six legs have been unfolded and projected, now the hexapod robot  is in hexapod state(walking state). The hexapod robot now stands in its fully articulated and functional form, with all six legs ready for locomotion or other tasks.

      

Fig 4.3.3: Transformation Steps

Walking Mechanism: 

The walking mechanism of the hexapod robot involves six legs connected to servos. When the legs are extended, the robot assumes its hexapod state. A depth camera is integrated into the hexapod circuit. This camera is used to detect and measure the depth or surface profile of the floor or terrain. The depth information from the camera is fed back to the controller, which then adjusts the angles and positions of the servo motors accordingly. This feedback loop enables the robot to adapt its leg movements and posture based on the detected floor surface or terrain. By continuously adjusting the servo motor angles based on the depth feedback, the hexapod robot can coordinate the movement of its six legs in a synchronized manner. This coordination allows the robot to walk effectively across different surfaces, maintaining stability and traction.

Fig 4.3.4: Forward Movement using Tripod gait pattern

The hexapod robot is capable of following multiple gait patterns to navigate its environment. It utilizes a stereoscopic 3D depth camera for object recognition and collision avoidance. 

Here, Figure 4.3.2 illustrates how the hexapod robot moves forward using the tripod gait pattern.

a) Lift and move the front and rear legs on one side of the hexapod (right or left) forward simultaneously, creating a triangular support with the remaining legs.

b) While the lifted legs are moving forward, the other three legs provide stability and support the robot's weight.

c) Alternate the movement with the legs on the opposite side of the hexapod to continue moving forward in a smooth and stable manner.

d) Adjust the speed and coordination of the leg movements to maintain balance and control during locomotion.

Climbing Mechanism:

Here's a step-by-step process of how the hexapod will climb the stairs by adjusting the angle of the servo motor.

Fig 4.3.5: Climbing mechanism

Anchoring the first set of legs : The hexapod starts on the ground floor with all its legs bent, in a crouched position. This low center of gravity provides stability as the hexapod prepares to climb the stairs. (a) in the image depicts this.

Lifting and positioning the body: The hexapod initiates its climbing sequence by extending two of its legs forward, placing them firmly on the first step. The remaining legs stay bent, keeping the hexapod's body close to the ground for stability. This ensures a controlled and balanced transition from the ground floor onto the stairs. (b) in the image depicts this.

Extending and anchoring the next set of legs: Once the front legs are securely positioned on the first step, the hexapod uses them to push its body upwards. As its body rises, it strategically extends the remaining legs, positioning them on the second step. This coordinated leg movement allows the hexapod to effectively lift its body weight and climb to the next level. (c) in the image depicts this.

Repeating the pattern: The hexapod's climbing motion becomes a repetitive sequence. Once on the second step, it repeats the same leg movements. By continuously extending and repositioning its legs, the hexapod can steadily climb up the stairs.

Internal high-torque DC motors play a crucial role in enabling hexapods to effectively climb stairs, particularly those of significant height. These motors provide the necessary rotational force (torque) to the hexapod's legs, allowing them to push against the stairs with the required strength.

During the stair-climbing process, the hexapod's legs need to exert significant force to lift its body weight against gravity.  Here's where high-torque DC motors come into play. They generate the power required for the legs to extend forcefully and propel the hexapod upwards. This is especially important for climbing higher stairs, where overcoming the increased gravitational pull demands a stronger pushing force from the legs.

It can also follow other patterns of climbing based on the height and position.

Rolling Mechanism:

The rolling mechanism comprises an structural rolling ring to which the legs are connected via servos. This disk is affixed with a gear, which in turn is linked to a DC motor. When the microcontroller signals the DC motor, it initiates rotation, causing the structural rolling ring to rotate as well. With both disks rotating in the same direction, the robot rolls forward or backward seamlessly.

Fig 4.3.7: Parts used for Rolling

Fig 4.3.8: Motion Study for Rolling

To maintain the central body of the robot in a stable and forward-facing position, the Return Wheel Mechanism is employed. This mechanism, which is spring-loaded, ensures that the central body consistently faces forward. Additionally, the inclusion of a ball bearing in the center of the structural rolling rings ensures independence between the central body and the structural rolling rings. Consequently, the central body, which houses the camera, can continuously face forward, allowing for tasks such as depth measurement and object detection. This mechanism facilitates the autonomous rolling of the hexapod in unfamiliar environments.

Both structural rolling rings are equipped with Inertial Measurement Units (IMUs) to provide feedback on structural rolling ring rotation. The IMU determines the gyroscopic position of the structural rolling ring, aiding the hexapod in transforming into a legged form with downward-facing legs. This transformation ensures that the robot remains upright and avoids flipping over. By rotating the structural rolling rings appropriately, the hexapod can position both sets of legs facing downward, maintaining stability and preventing the robot from turning upside down.

Fig 4.3.9: Return Wheel Mechanism

Selection of materials and components : 

Aluminium/Carbon Fibre Extrusion Frame and Linkages: The hexapod’s body will be constructed from high-grade aluminium, offering an exceptional strength-to-weight ratio, durability and resistance to corrosion.

Servo Motors and Control System: The hexapod uses standard PWM-controlled servo motors, driven by an STM32 microcontroller. The STM32 generates precise PWM signals to control each servo, enabling accurate and coordinated leg movements for walking and rolling.

High Torque DC Motors and DC Motor Driver: The high torque DC motors are employed to rotate the structural rolling rings, which house the servo legs, while in the rolling position. These motors are connected to the structural rolling rings through gears, providing the necessary torque for climbing by exerting rotational force forward.

Intel RealSense 3D Depth Sensing Camera: It is used in developing autonomous behavior in the hexapod robot. It continuously captures images and utilizes them for object detection, recognition, and avoidance (DRA). Additionally, it employs stereoscopic vision to sense the depth of objects, enabling the robot to navigate its environment more effectively. The camera's ability to perceive depth allows for more accurate decision-making, enhancing the robot's autonomy and adaptability in various scenarios.

Inertial Measurement Unit (MPU6050): This component plays a crucial role in maintaining stability in the hexapod robot during various actions such as walking, climbing, rolling, and transforming. It collects gyroscopic data to keep the robot steady, allowing the legs to move accordingly to maintain balance on uneven terrain. Additionally, the MPU6050 is used to collect attitude data of the structural rolling rings, ensuring that during autonomous rolling or transformation, the hexapod remains upright and avoids flipping over. This capability is essential for the robot's safe and stable operation in dynamic environments.

Raspberry Pi Processor: It is the main brain of the Hexapod robot which processes the data and generates the control signals based on the situations. The Raspberry Pi serves as the central processing unit of the hexapod robot, responsible for processing data and generating control signals based on environmental conditions. It receives sensor data and integrates them to develop autonomous behavior in the hexapod. Additionally, the Raspberry Pi performs depth measuring operations and object recognition, crucial for navigating and interacting with its surroundings. Its wireless capabilities enable remote operation via WiFi, allowing for flexible control and monitoring. The Raspberry Pi supports coding in multiple languages, making it accessible to a wide range of developers. Furthermore, it can save setups, codes, and trained data, enabling seamless reuse and customization for different applications and environments.

Microcontroller: In the context of the hexapod robot, the microcontroller serves as the signal distributor or controller. It receives data or orders generated by the microprocessor and, based on predefined numerical algorithms, controls the actuators connected to it. The microcontroller plays a crucial role in offloading the controlling load from the processor, as it is equipped with high-precision pins and controlling methods. This distinction sets it apart from the processor, which primarily focuses on data processing. Instead, the microcontroller focuses on controlling the actuators using the processed data, ensuring precise and efficient control over the robot's movements and actions.

Lithium Polymer Battery: It provides the main power supply to all electronic components. This rechargeable battery type offers a high energy density, making it lightweight and ideal for mobile applications. Its ability to deliver high current ensures reliable power to motors, sensors, and other components, enabling smooth operation and longer runtimes. 

Programming: 

The programming for our hexapod robot involves developing algorithms that govern its behavior in different situations. Gait control algorithms are at the core, dictating how the robot moves its legs to achieve stable locomotion. For instance, we use a tripod gait pattern that involves lifting and moving sets of legs in a coordinated manner to maintain stability while walking. These algorithms consider factors such as leg positions, angles, and timing to ensure smooth movement.

Sensor integration plays a crucial role in the robot's navigation and stability. Sensors like the stereoscopic 3D depth sensing camera and MPU6050 Inertial Measurement Unit provide data used to make decisions about leg movements and body posture. For example, the depth sensing camera helps in obstacle avoidance by providing information about the environment's geometry, while the IMU detects changes in orientation to maintain balance.

To enable remote control and monitoring, we use wireless communication, typically through WiFi or Bluetooth. This allows the Raspberry Pi Processor to communicate wirelessly with external devices and servers to send and receive commands and sensor data. Operators can thus control the robot from a distance and receive real-time feedback on its status and surroundings.

Achieving autonomous behavior is a key goal, and our code includes path planning algorithms for efficient navigation. Object recognition algorithms help identify obstacles and avoid collisions, while decision-making processes prioritize actions based on sensor inputs and predefined goals. These algorithms work together to enable the robot to navigate its environment autonomously.

Our program also includes robust error handling and recovery mechanisms. For example, if a leg gets stuck or a sensor malfunctions, the robot can stop, assess the situation, and attempt to correct it. These mechanisms ensure safe operation and prevent damage to the robot or its surroundings.

Safety features are paramount, and we've implemented emergency stop mechanisms triggered by specific conditions, such as detecting a fall or a collision. Additionally, obstacle detection algorithms continuously scan the environment to avoid potential hazards.

Users interact with the robot through a graphical user interface (GUI) or a command-line interface (CLI). The GUI provides a visual representation of the robot's status and allows users to control its movements and view sensor data. The CLI offers more advanced control options for experienced users.

Before deployment, rigorous testing and validation of the code are carried out using simulation software like Gazebo or ROS. This allows us to simulate various scenarios and verify that the algorithms behave as expected. Simulation results are then used to fine-tune the code and ensure optimal performance on the physical robot.

Transformation and rolling capabilities are seamlessly integrated into our algorithms, enabling the robot to adapt to different environments. For example, the robot can transform into a rolling mode when the terrain is smooth and transform back to walking mode when it encounters obstacles or uneven surfaces. The rolling mechanism algorithms manage the movement of the robot in rolling mode, ensuring stability and control.

Assembly: 

Once the materials and components have been selected, the next step is to assemble the parts and components of the robot. This will involve soldering, wiring, and attaching various components, such as motors, batteries, and sensors to create a functional Robot.The assembly process begins with mounting the structural components, such as the aluminum extrusion frame and linkages, to create the robot's body. The motors, including high torque servo motors and high torque DC motors, are then attached to the frame using mounting brackets.The electrical components, including the lithium polymer battery, stereoscopic 3D depth sensing camera, processor, microcontroller, servo motor driver, DC motor driver, LiDAR sensor, slip ring/rotary connector, and MPU9250 Inertial Measurement Unit, are connected according to the circuit diagram.Finally, the power switches and accessories, such as fasteners and hardware, are installed to complete the assembly process.

Fig 4.3.10: Assembly of Aluminium Plated Hexapod with Rolling Feature (Trials)

Testing and debugging: 

Before the Hexapod robot can be deployed, it is important to test and debug them to ensure that they are functioning properly.The testing process involves checking each component and subsystem to verify that they are working correctly. This includes testing the motors, sensors, and communication systems to ensure they are responding as expected.The debugging process involves identifying and fixing any issues that arise during testing. This may involve reprogramming the microcontroller, replacing faulty components, or adjusting the mechanical assembly to improve performance.Once the robot has been thoroughly tested and debugged, it can be deployed for further testing in real-world environments to validate its performance and functionality. 

2. Required Components:

Type of Components

Name

Approx Estimated Cost

Structural Components

Aluminum Extrusion Frame/ Carbon Fibre Frame

₹30,000

Aluminum Linkages

₹6,000

Motors Mounting Brackets

₹2,000

Nuts & Bolts

₹3,000

Ball Bearings

₹1,000

Motion Components

High Torque Servo Motors

₹50,000

High Torque DC Motors

₹7,000

Electronics Components

Lithium Polymer Battery

₹8,000

Intel RealSense 3D Depth Sensing Camera

₹39,000

Raspberry Pi 5

₹9,000

Microcontrollers

₹6,000

DC Motor Driver

₹7,000

LiDAR Sensor

₹13,000

Slip ring/Rotary connector

₹9,000

IMU / MPU6050

₹1,000

Power Switches

₹500

Accessories

Fasteners and Hardware

₹3,000

Total

₹1,94,500

Table 2.1: RolloPod Component Cost Analysis.

Pricing reflects market research conducted across multiple vendors including Robu, Robokits, RoboticDNA, and Amazon. Final procurement costs may vary.

3. Robot Assembly Design:

Fig 2.1: Robot Assembly

   

Fig 2.2: Robot Transformation  

Fig 2.3: Assembly of parts & components

4. Application of the proposed Robot in a societal context: 

Here is the reference where current hexapods can be used in market: https://locorobo.co/future-of-hexapod-robotics-real-world-uses-for-six-legged-botsIn these cases, Our Rollopod enhances the speed to cover long distances.

Rollopod finds applications across various fields due to its unique capabilities in mobility, stability, and adaptability to rough terrain. Some common applications include:

Search and Rescue: Hexapod robots can navigate through disaster zones, rubble, or hazardous environments where human access may be limited or dangerous. Equipped with sensors and cameras, they can locate and assist survivors, deliver supplies, or gather information for rescue teams.

Exploration: Hexapods are suitable for exploring challenging terrains such as forests, deserts, caves, or planetary surfaces. They can traverse uneven ground, climb obstacles, and collect samples or data for scientific research or geological surveys.

Agriculture: Hexapod robots can be used for precision agriculture tasks such as planting, weeding, and harvesting crops. Their ability to move through fields without compacting soil or damaging plants makes them suitable for sustainable farming practices.

Entertainment and Hobbyist Projects: Hexapod robots are popular among hobbyists and enthusiasts for building robotic toys, animatronics, or interactive exhibits. They provide opportunities for creativity, experimentation, and learning about robotics and electronics.

Military and Defense: Hexapod robots have potential applications in military operations for reconnaissance, surveillance, and logistics support. They can operate in rugged terrain, carry payloads, and provide situational awareness in complex operational environments.

Space Exploration: Hexapods could be used for planetary exploration missions, where they can navigate rough terrain, conduct scientific experiments, or assist in infrastructure construction on other planets or moons.

Education and Research: Hexapod robots serve as valuable educational tools for teaching robotics, programming, and engineering concepts. They also enable researchers to study biomechanics, locomotion strategies, and sensor integration in legged robots, advancing the field of robotics.

5. Robot Size:

Length in cm: 40

Width in cm: 50

Height in cm: 40

Fig 6.1: Detailed Dimensions of Model (Theoretical CAD Design for Understanding the Principles)

6. Concept Illustration and Artistic Rendering:

Fig 9.1: Rolling Motion study of hexapod gif

Fig 9.2: Hexapod Transformation gif

Fig 9.3: Environment Scanning via Depth Camera

Fig 9.2: Hexapod in Rolling Motion on Roads

Fig 9.3: Hexapod in agricultural application

Fig 9.4: Hexapod in exploration application

Respectfully Submitted by:

Parag Patil

Rutu Patel

—--- Thank You —---