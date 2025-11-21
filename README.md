# 🚀 CareerTrials AI API

### *AI-powered Career Assistant using FastAPI + Agno + Google Gemini*

This project is an **AI microservice** that guides users through a personalized career diagnostic flow and generates **custom learning challenges** using Google Gemini via the **Agno framework**.

It exposes a REST API used by a frontend (React or other clients) and maintains conversation context across sessions using SQLite-based agent memory.

---

# 📘 Table of Contents

* [Features](#-features)
* [Architecture Overview](#-architecture-overview)
* [Technologies Used](#-technologies-used)
* [How It Works](#-how-it-works)
* [Installation](#-installation)
* [Environment Variables](#-environment-variables)
* [Running the Server](#-running-the-server)
* [API Endpoints](#-api-endpoints)
* [Session Flow](#-session-flow)
* [Challenge Generation Logic](#-challenge-generation-logic)
* [Project Structure](#-project-structure)
* [References](#-references)

---

# ✨ Features

### **1. Career Diagnostic (Phase 1)**

* AI asks up to `MAX_QUESTIONS` questions
* The first question is fixed:
  **"Legal, antes de começarmos, qual é o objetivo da sua carreira hoje?"**
* AI responds in **natural Portuguese**
* User answers are stored in SQLite (via Agno Memory)

---

### **2. Challenge Generation (Phase 2)**

Triggered by sending the message:

```
GENERATE_CHALLENGES
```

The AI then outputs ONLY a **valid JSON array** containing customized challenges, following the structure:

```json
{
  "title": "...",
  "description": "...",
  "type": "Code | Quiz | Project",
  "difficulty": "Easy | Medium | Hard",
  "xp": 10,
  "level": 1,
  "estimatedTime": "1h",
  "tags": ["tag1"],
  "questions": [...]
}
```

The backend:

* Cleans AI output
* Validates JSON
* Assigns **incremental IDs**
* Rebuilds **difficulty/level progression**

---

### **3. Persistent Session Memory**

Using **Agno + SQLite**, each session stores:

* Conversation history
* User answers
* Agent state

Sessions persist until explicitly deleted.

---

### **4. Fully Typed Endpoints**

DTOs include:

* `MessageRequest`
* `MessageResponse`
* `ChallengesResponse`
* `ErrorResponse`

---

### **5. Frontend-friendly API**

Built to integrate smoothly with React, mobile apps, or any client.

---

# 🧱 Architecture Overview

```
Frontend (React, etc.)
          ↓ HTTP
FastAPI Server
 ├── Session Management
 ├── AI Message Routing
 ├── Challenge Generation
 ├── JSON Cleaning & Validation
 └── Agent Factory
       └── Agno Agent (Google Gemini)
            ├── Memory (SQLite)
            └── System Prompt Logic
```

---

# 🛠 Technologies Used

| Component        | Technology                                     |
| ---------------- | ---------------------------------------------- |
| Backend API      | **FastAPI**                                    |
| AI Orchestration | **Agno Framework**                             |
| LLM              | **Google Gemini (via generativelanguage API)** |
| Database         | SQLite (Agent Memory)                          |
| Deploy           | Uvicorn                                        |
| Config           | `.env`                                         |

---

# ⚙️ Installation

```bash
git clone <repo-url>
cd project-folder
pip install -r requirements.txt
```

---

# 🔐 Environment Variables

Create a `.env` file:

```
DEFAULT_MODEL=gemini-2.0-flash-exp
GOOGLE_API_KEY=YOUR_API_KEY
GOOGLE_CLOUD_PROJECT=your-gcp-project
GOOGLE_CLOUD_LOCATION=us-central1
DB_FILE=/tmp/agents.db
```

---

# ▶️ Running the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API documentation is available at:

* Swagger: **[http://localhost:8000/docs](http://localhost:8000/docs)**
* ReDoc: **[http://localhost:8000/redoc](http://localhost:8000/redoc)**

---

# 📡 API Endpoints

## 🟩 **Health Check**

### `GET /`

Quick service status.

### `GET /health`

Includes database + model info.

---

## 🟦 **Session Management**

### **Create a Session**

```
POST /session/create/{user_id}
```

Response:

```json
{
  "session_id": "s_ac8457b31b",
  "user_id": "1"
}
```

### **Check Session Status**

```
GET /session/{session_id}/{user_id}/status
```

### **Delete Session**

```
DELETE /session/{session_id}/{user_id}
```

---

## 🟨 **AI Conversation**

### **Send a Message**

```
POST /session/{session_id}/{user_id}/message
```

Body:

```json
{ "message": "Quero melhorar minhas soft skills" }
```

Response:

```json
{
  "response": "Ótimo! Qual é o seu nível de experiência atual?",
  "session_id": "s_12345",
  "user_id": "1"
}
```

---

## 🟥 **Generate Challenges (Phase 2)**

### **Complete the Session**

```
POST /session/{session_id}/{user_id}/complete
```

Returns:

```json
{
  "session_id": "s_123",
  "total": 10,
  "challenges": [
    {
      "id": 1,
      "title": "...",
      "level": 1,
      "difficulty": "Easy",
      ...
    }
  ]
}
```

This endpoint:

1. Sends `"GENERATE_CHALLENGES"` to the AI
2. Cleans malformed JSON
3. Validates the challenge structure
4. Adds IDs
5. Fixes levels based on progression logic

---

# 🔄 Session Flow Explained

### **1. Frontend creates a session**

* Receives `session_id`
* Stores it in localStorage

### **2. User answers AI questions**

Every message calls:

```
POST /session/{session}/{user}/message
```

Agno keeps context stored in SQLite memory.

### **3. Once user finishes, call:**

```
POST /session/{session}/{user}/complete
```

The AI switches to Phase 2 and sends back the challenge JSON.

---

# 🧠 Challenge Generation Logic

After receiving challenges:

### 1. `validate_challenges()`

Ensures structure & required fields.

### 2. `add_ids_to_challenges()`

Adds:

```
challenge.id = incremental number
```

### 3. `fix_levels()`

Assigns levels sequentially (e.g., 2 challenges per level).

Example:

| Challenges | Assigned Level |
| ---------- | -------------- |
| 0          | 1              |
| 1          | 1              |
| 2          | 2              |
| 3          | 2              |
| 4          | 3              |

---

# 📁 Project Structure

```
.
├── main.py
├── AgentFactory.py
├── Config.py
├── Utils.py
├── dtos/
│   ├── MessageRequest.py
│   ├── MessageResponse.py
│   ├── ChallengesResponse.py
│   ├── ErrorResponse.py
├── .env
├── requirements.txt
└── README.md
```

---

# 🔗 References

### **Agno Framework**

[https://github.com/agnohq/agno](https://github.com/agnohq/agno)

### **Google Gemini API**

[https://ai.google.dev/gemini-api/docs](https://ai.google.dev/gemini-api/docs)

### **FastAPI Documentation**

[https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)

### **Uvicorn**

[https://www.uvicorn.org/](https://www.uvicorn.org/)

## 👥 Autores

- **Lucas Perez Bonato** - *565356* - [LucasBonato](https://github.com/LucasBonato)
- **Diogo Oliveira Lima** - *562559* - [oliveiralimadiogo](https://github.com/oliveiralimadiogo)
- **Lucas dos Reis Aquino** - *562414* - [LucassAquino](https://github.com/LucassAquino)