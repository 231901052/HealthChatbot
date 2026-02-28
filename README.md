# 🏥 HealthBot – WhatsApp-Based Health Assistance System

HealthBot is a containerized health assistance ecosystem designed to bridge the gap between patients and healthcare workers. Built using **Flask**, **Rasa**, and **Twilio**, the system enables patients to seek medical advice via WhatsApp while ensuring critical cases are escalated to **ASHA (Accredited Social Health Activists)** workers via a real-time dashboard.

---

## 🚀 Project Overview

HealthBot utilizes a multi-service architecture to provide seamless interaction and monitoring:

* **📲 WhatsApp Integration:** Powered by Twilio API for global accessibility.
* **🧠 Natural Language Processing:** Rasa-driven intent detection and response generation.
* **🔧 Flask Backend:** Acts as the central nervous system, routing data between services.
* **🩺 ASHA Dashboard:** A dedicated interface for health workers to monitor and respond to alerts.
* **🐳 Dockerized:** Fully orchestrated using Docker Compose for "plug-and-play" deployment.

### System Data Flow
`User (WhatsApp) ⮕ Twilio Webhook ⮕ Flask Backend ⮕ Rasa (NLP) ⮕ ASHA Dashboard (Alerts)`

---

## 🏗️ Architecture & Project Structure

The project is organized into modular services for scalability:

```text
healthbot/
│
├── backend/            # Flask backend for webhook handling & logic
├── asha_dashboard/     # Monitoring dashboard for health workers
├── rasa/               # Rasa model, stories, and domain configurations
├── docker-compose.yml  # Orchestration for all services
└── README.md
```
## 🛠️ Tech Stack
```
Component        |    Technology         |       Description
-----------------|-----------------------|-----------------------------------------------------
Language         |   Python 3.9+         |     Primary programming language
Web Framework    |   Flask               |     Handles routing and dashboard logic
NLP Engine       |   Rasa                |     Processes natural language and intents
Messaging API    |   Twilio              |     Integrates with WhatsApp Business API
Containerization |  Docker               |    Ensures consistent environments across services
Orchestration    |   Docker Compose      |     Manages multi-container deployment

```

## ⚙️ How It Works
* User Interaction: The user sends a message via WhatsApp.
* Processing: Twilio forwards the message to the Flask backend.
* Intelligence: The backend queries the Rasa service to understand user intent.
* Escalation: If the NLP detects a serious symptom (e.g., "High Fever," "Chest Pain"), the backend pushes a notification to the ASHA Dashboard.
* Response: The user receives an automated response while the health worker is alerted for follow-up.

## 🐳 Running the Project (Docker Recommended)
## Step 1 – Clone Repository
Bash
* git clone [https://github.com/231901052/HealthChatbot.git](https://github.com/231901052/HealthChatbot.git)
* cd healthbot
## Step 2 – Add Twilio Environment Variables
* Navigate to .env file inside the backend/ directory and update with your credentials:
* Code snippet
TWILIO_ACCOUNT_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_token_here
TWILIO_WHATSAPP_NUMBER=your_twilio_number
## Step 3 – Build and Run
* Execute the following command to start all services:
Bash
* python3 runme.py
# Alternatively: docker-compose up --build
## Step 4 – Access Services
Flask Backend: http://localhost:5000
ASHA Dashboard: http://localhost:5001
Rasa Engine: http://localhost:5005

## 📲 Twilio Webhook Setup
* In your Twilio Console, navigate to: Messaging > Try it Out > Send a WhatsApp Message.

* Go to Sandbox Settings.

* Paste your generated public URL (via ngrok or your server) into the "When a message comes in" field.

* Set the method to POST.

* Join the Sandbox by sending the generated code (e.g., join word-word) to the Twilio number.

## 🧪 Testing the System
* Send a WhatsApp message like:

    "I have a high fever and a cough."

* Expected Result:

* The chatbot provides a preliminary response.

* The ASHA Dashboard receives a real-time alert for patient attention.

## 🔐 Key Features
✔ WhatsApp Integration via Twilio.

✔ Real-time NLP for symptom classification.

✔ Modular Architecture using Docker Compose.

✔ Emergency Escalation system for health workers.

✔ Clean & Scalable code structure.
