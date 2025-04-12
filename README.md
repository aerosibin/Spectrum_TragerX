# TragerX

![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)  
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)  
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🚀 Overview

**TragerX** combines **SLAM (Simultaneous Localization and Mapping)**, **A* Pathfinding**, and **robotic workflows** to create a dynamic environment for robotic navigation and task automation. This project simulates robots navigating through a grid-based map, detecting obstacles, planning paths, and interacting with customers or counters using QR codes and OTP verification.

---

## 📋 Table of Contents

1. [Features](#-features)
2. [Technologies Used](#-technologies-used)
3. [Project Workflow](#-project-workflow)
4. [Contributing](#-contributing)
5. [License](#-license)

---

## ✨ Features

- **Grid-Based SLAM**: Simulates a robot's ability to explore unknown environments and map obstacles dynamically.
- **A* Pathfinding Algorithm**: Implements efficient path planning for robots to navigate from source to destination.
- **Multi-Robot System**: Includes stationary and mobile robots with unique IDs and workflow states.
- **QR Code Scanning & OTP Verification**: Simulates customer interaction via QR code scanning and OTP validation.
- **Dynamic Obstacle Detection**: Robots detect obstacles in real-time using simulated ultrasonic sensors.
- **User Interface**: Visualize the robot's path, map updates, counters, and customer interactions using Pygame.

---

## 🛠️ Technologies Used

The project leverages the following technologies:

- **Python 3.11**
- **Pygame**: For visualization and simulation.
- **OpenCV**: For QR code scanning.
- **A* Algorithm**: For efficient pathfinding.
- **Tkinter**: For OTP verification GUI.
- **Numpy**: For grid-based calculations.

---

## 🔄 Project Workflow

1. The simulation starts with a welcome intro screen.
2. A mobile robot navigates from the charging station (source) to a customer location using A* pathfinding.
3. At the customer location:
   - The robot scans a QR code to determine the next counter destination.
   - The user verifies their identity using an OTP system.
4. The robot navigates to the assigned counter, waits for service, then returns to the charging station.

### Robot States:
- `Idle`: Waiting at the source or counter.
- `To Customer`: Navigating to the customer location.
- `At Customer`: Ready for QR scan and OTP verification.
- `To Counter`: Navigating to the assigned counter.
- `At Counter`: Waiting for service at the counter.

--

---

## 🖼️ Screenshots

### 1️⃣ Welcome Screen
The intro screen welcomes users with smooth animations.

### 2️⃣ SLAM Simulation
Real-time visualization of the SLAM map, including obstacles, clear spaces, and robot paths.

### 3️⃣ QR Code Scanning & OTP Verification
Interactive GUI for QR code scanning and OTP validation.

---

---

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details

---

## 🌟 Acknowledgments

Special thanks to all contributors who made this project possible!

---

Feel free to reach out if you have any questions or suggestions!


