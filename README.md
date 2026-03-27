# CamSense.ai ⚡ 

### Intelligent Energy & Occupancy Monitoring System

CamSense.ai is a state-of-the-art computer vision solution designed to eliminate energy waste in institutional and residential buildings. Using deep learning and real-time video analysis, it detects room occupancy and appliance states to identify efficiency gaps and automate alerts.

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
