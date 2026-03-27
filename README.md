# CamSense.ai ⚡ 

### Intelligent Energy & Occupancy Monitoring System

CamSense.ai is a state-of-the-art computer vision solution designed to eliminate energy waste in institutional and residential buildings. Using deep learning and real-time video analysis, it detects room occupancy and appliance states to identify efficiency gaps and automate alerts.

---

## 💡 The problem it solves

Conventional energy management often relies on manual walk-throughs or basic motion (PIR) sensors, which are frequently ineffective. PIR sensors often turn off lights while people are still in the room (e.g., studying quietly) or fail to detect if specific high-drain appliances like fans or monitors were left active.

**CamSense.ai addresses these core challenges:**

- **Eliminating "Passive Waste"**: Automatically detects "Efficiency Gaps"—scenarios where a room is empty but appliances (lights, fans, monitors) are still running.
- **Context-Aware Monitoring**: Unlike binary motion sensors, our AI understands the difference between an empty room and a quiet but occupied one, preventing "false darkness" while ensuring appliances are off when truly not needed.
- **Data-Driven Accountability**: Provides managers with quantifiable data ($ cost, kWh waste, CO2 impact) rather than vague guesses about where energy is being lost.
- **Enhanced Safety**: Identifies appliances left running for extended periods, reducing the risk of overheating and electrical fire hazards.
- **Surveillance without Intrusion**: By using real-time edge-based pixelation, we solve the problem of privacy: the system "sees" efficiency, not people, making it safe for use in offices, labs, and schools.

---

## 📊 SWOT Analysis

CamSense.ai leverages cutting-edge technology while maintaining a strategic focus on efficiency and scalability:

-   **Strengths**: Real-time YOLOv8-based person detection, custom appliance state recognition (Light/Fan/Monitor), low-latency WebRTC streaming, and privacy-centric data handling.
-   **Weaknesses**: Initial hardware setup requirements for camera placement and dependable network bandwidth for high-resolution edge inference.
-   **Opportunities**: Integration with Smart Home/Building HVAC systems, expansion into corporate ESG reporting, and potential for predictive energy usage analytics.
-   **Threats**: Rapidly evolving data privacy regulations (GDPR/FERPA) and competition from legacy hardware-based occupancy sensors (PIR).

---

## 🛠️ Tech Stack

### Frontend (Dashboard)
-   **Core**: React 18.2 (Vite-powered)
-   **Styling**: Vanilla CSS with Modern Aesthetics (Glassmorphism, Dark Mode)
-   **Communication**: WebRTC for low-latency video, WebSockets for real-time telemetry
-   **State Management**: React Hooks & Context API

### Backend (Detection Engine)
-   **Language**: Python 3.9+ 🐍
-   **Web Framework**: FastAPI & Uvicorn (Asynchronous processing)
-   **Database**: SQLite via SQLAlchemy (Asset & Event persistence)
-   **Messaging**: WebSockets for real-time dashboard updates

### AI & Computer Vision
-   **Models**: YOLOv8 (Ultralytics) for person detection, Custom Roboflow Models for appliance states
-   **Inference**: Roboflow Inference SDK & PyTorch
-   **Processing**: OpenCV (Frame manipulation, Privacy blurring, Micro-zone analysis)

### Third-Party Integrations
-   **Alerts**: Twilio API (SMS & WhatsApp Business integration)
-   **Data Storage**: Persistent JSON logs and SQLite metrics

---

## ✨ Key Features

-   **Multi-Room Dashboard**: Monitor multiple zones (Classrooms, Offices, Lab) simultaneously.
-   **Real-time Energy Telemetry**: Live tracking of estimated wattage, hourly cost, and cumulative waste.
-   **Smart Alerts**: Automated WhatsApp/SMS notifications when waste exceeds configurable thresholds.
-   **Privacy-First Design**: On-device pixelation and blurring of human subjects to ensure GDPR/FERPA compliance.
-   **Micro-zone Intelligence**: Heatmap-style tracking of most-used areas within a single room.
-   **Customizable Wattage**: Easy configuration of electricity rates and appliance power ratings via `config.yaml`.

---

## 🧱 Challenges I ran into

Building a real-time, AI-powered system presented several technical hurdles that required creative solutions:

### 1. The Latency Trap
**Problem**: Real-time high-resolution video processing often leads to a 3–5 second lag between frame capture and detection display.
**Solution**: We implemented a frame-skipping logic and background inference threads. By separating the UI refresh rate from the AI detection cycle, we maintained a smooth dashboard experience without sacrificing detection accuracy.

### 2. Computational Overload
**Problem**: Running YOLOv8 for person detection alongside custom Roboflow models for multiple appliances (Light, Fan, Monitor) simultaneously maxed out CPU/GPU resources.
**Solution**: We decoupled inference intervals. While person detection runs at high frequency for tracking, appliance status checks are performed every 20-30 frames. This optimized the resource footprint by nearly 60% with zero impact on energy waste detection.

### 3. The "Static Occupant" Bug
**Problem**: Traditional motion sensors (PIR) often fail if a person is sitting still (e.g., reading).
**Solution**: By using YOLOv8 person-detection models rather than pixel-motion detection, CamSense.ai maintains "Occupied" status even for stationary subjects, preventing the "auto-lights-off" annoyance common in modern offices.

### 4. Balancing Privacy with Monitoring
**Problem**: Monitoring classrooms or offices can feel like intrusive surveillance.
**Solution**: We developed a real-time anonymization layer. The system processes the raw frame for detection but immediately applies high-level pixelation/blurring to human subjects before the feed reaching the dashboard or being logged.

---

## 🏃 Getting Started

### 1. Prerequisites
- Python 3.9+
- Node.js & npm
- Roboflow API Key

### 2. Installation
```powershell
# Clone the repository
git clone https://github.com/extremecoder-rgb/Watt-Watch.git
cd watt-watch

# Install Backend Dependencies
pip install -r requirements.txt

# Install Frontend Dependencies
cd dashboard-vite
npm install
```

### 3. Configuration
Rename/Edit `config.yaml` with your Roboflow API keys and local electricity rates.

### 4. Running the System
```powershell
# Start the Backend (from root)
python main.py

# Start the Dashboard (from dashboard-vite)
npm run dev
```

---

## 📈 Energy Impact
CamSense.ai helps organizations reduce their electricity footprint by identifying **Passive Energy Leakage**—often accounting for up to 30% of institutional power waste.

---
*Developed by the CamSense.ai Team*
