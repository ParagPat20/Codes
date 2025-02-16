# Two-Wheeled Balancing Robot with Fixed Axle

This document describes the design and operation of a two-wheeled robot where the middle section is fixed to the wheel axle, creating a unique challenge for achieving forward motion.

## Mechanical Structure

The robot consists of three main parts:

1.  **Middle Section:** A rigid body, symmetrically balanced about the wheel axis. Its center of mass lies directly on the axle.
2.  **Left Wheel:** Attached to one end of the axle.
3.  **Right Wheel:** Attached to the other end of the axle.

The middle section is *fixed* to the axle, meaning it cannot rotate independently of the wheels.  This is the key difference from a typical balancing robot like a Segway.

## Components

*   **Motors:** Two DC motors, one for each wheel, with sufficient torque and speed for the desired robot performance.  Consider motors with encoders for precise speed control.
*   **Motor Drivers:**  Motor driver circuits capable of controlling the speed and direction of each motor independently.  H-bridges are commonly used for this purpose.
*   **Microcontroller:**  A microcontroller (e.g., Arduino, ESP32) to process sensor data, run the control algorithms, and control the motors.
*   **IMU (Inertial Measurement Unit):**  A sensor (combination of accelerometer and gyroscope) to measure the angle and angular rate of the middle section.  A high-quality IMU is essential for stability.
*   **Wheel Encoders (Optional but Recommended):** Sensors attached to the motor shafts or wheels to measure wheel rotation and speed.  These provide valuable feedback for the control system.
*   **Power Source:** A battery or power supply suitable for the motors and electronics.
*   **Chassis/Frame:**  A structure to hold all the components together.  Rigidity is important to minimize vibrations.
*   **Wheels:** Two wheels with good traction.  Larger diameter wheels can improve stability.

## How the Robot Moves Forward

Forward motion is achieved through *differential wheel speeds*.

1.  **Equal Wheel Speeds = Rotation Only:** If both wheels rotate at the same speed, the middle section rotates, but the robot does not translate (move from one place to another).

2.  **Differential Wheel Speeds = Rotation + Translation:** When one wheel rotates faster than the other:
    *   The middle section *still* rotates.
    *   This rotation, *combined* with the difference in wheel speeds, results in a *net* translational movement.  The robot moves forward and turns.

3.  **Example (Left wheel faster):** The robot moves forward and turns *towards* the right.

4.  **Example (Right wheel faster):** The robot moves forward and turns *towards* the left.

## Control System

A feedback control system is crucial for precise movement.  A PID (Proportional-Integral-Derivative) controller is a common choice.

1.  **Sensor Input:** The IMU provides angle and angular rate data. Wheel encoders (if used) provide wheel speed data.

2.  **PID Controller:** The PID controller calculates the necessary adjustments to the motor speeds based on the sensor input and the desired motion.

3.  **Motor Output:** The PID controller output is sent to the motor drivers to control the speed and direction of each motor.

## Other Information

*   **Balancing is Not the Primary Concern:**  Since the middle section is balanced and its center of mass is on the wheel axis, the robot won't *fall over* in the traditional sense.  The control system focuses on *controlling rotation* to achieve forward movement.
*   **Tuning:**  Tuning the PID controller gains (Kp, Ki, Kd) is essential for stable and responsive control.
*   **Sensor Fusion:** Combining data from the IMU and wheel encoders (if used) can improve state estimation and control accuracy.
*   **Mechanical Design:**  Minimizing friction and ensuring structural rigidity are important for smooth operation.

This document provides a comprehensive overview of the design and operation of this type of two-wheeled robot.  Differential wheel speeds and a feedback control system are the core principles that enable controlled movement.
