# 🚀 OCPP Backend with Django & WebSockets

This project is a **Django-based OCPP 1.6 backend** that allows communication between **EV chargers (Charge Points)** and a **central system** using WebSockets.  
It supports **BootNotification, Authorize, StartTransaction, StopTransaction, RemoteStartTransaction, RemoteStopTransaction**, and **JWT-based authentication**.

---

## **📌 Features**
✅ **OCPP 1.6 WebSocket Server** using Django Channels  
✅ **Supports `BootNotification`, `Authorize`, `StartTransaction`, and more**  
✅ **Secure WebSocket & API authentication with JWT (`dj-rest-auth`)**  
✅ **Stores charging transactions in PostgreSQL**  
✅ **Uses Redis for WebSocket message handling**  
✅ **Dockerized setup with `docker-compose`**  

---

## **🔹 Installation & Setup**
### **1️⃣ Clone the Repository**
```bash
git clone https://github.com/your-repo/ocpp-backend.git
cd ocpp-backend
```

### **2️⃣ Set Up Environment Variables**
Create a `.env` file:
```ini
DEBUG=True
SECRET_KEY=your-secret-key
REDIS_URL=redis://redis:6379/0
```

### **3️⃣ Start Docker Containers**
```bash
docker-compose up --build -d
```

### **4️⃣ Apply Migrations & Create Superuser**
```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

---

## **🔹 WebSocket Endpoints**
| **WebSocket URL** | **Purpose** |
|------------------|-------------|
| `ws://localhost:8001/ws/ocpp/{charger_id}/?token=your_jwt_token` | Connect a charger using JWT authentication |

✅ **Test with postman**
---

## **🔹 How to Start an OCPP Charging Session**
### **1️⃣ Charger Connects & Registers (`BootNotification`)**
```json
[2, "12345", "BootNotification", {
    "chargePointModel": "EVSE-123",
    "chargePointVendor": "EV-Charger Inc."
}]
```

✅ **Expected Response**
```json
[3, "12345", {"currentTime": "2025-03-05T12:00:00Z", "interval": 600, "status": "Accepted"}]
```

### **2️⃣ User Authenticates with RFID (`Authorize`)**
```json
[2, "12346", "Authorize", {"idTag": "testuser"}]
```

✅ **Expected Response**
```json
[3, "12346", {"idTagInfo": {"status": "Accepted"}}]
```

### **3️⃣ Start Charging Session (`StartTransaction`)**
```json
[2, "12347", "StartTransaction", {
    "connectorId": 1,
    "idTag": "testuser",
    "meterStart": 5000,
    "timestamp": "2025-03-05T12:10:00Z"
}]
```

✅ **Expected Response**
```json
[3, "12347", {"transactionId": 1741202913, "idTagInfo": {"status": "Accepted"}}]
```

### **4️⃣ Stop Charging Session (`StopTransaction`)**
```json
[2, "12348", "StopTransaction", {
    "transactionId": 1741202913,
    "meterStop": 10000,
    "timestamp": "2025-03-05T12:30:00Z"
}]
```

✅ **Expected Response**
```json
[3, "12348", {"idTagInfo": {"status": "Accepted"}}]
```

### **5 send HeartBeat signal (`HeartBeat`)**
```json
[2, "12346", "Heartbeat", {}]
```

✅ **Expected Response**
```json
[3,"12346",{"currentTime":"2025-03-07T19:04:14.189565+00:00"}]
```



---

## **🔹 API Endpoints**
| **Endpoint** | **Method** | **Description** |
|-------------|---------|-----------------|
| `/api/auth/registration/` | `POST` | Register a new user |
| `/api/auth/login/` | `POST` | Log in to get JWT |
| `/api/auth/logout/` | `POST` | Log out |
| `/api/auth/token/verify` | `POST` |
| `/api/auth/token/refresh` | `POST` |
| `/api/remote-transactions/start/` | `POST` | Start a charging session remotely |
| `/api/remote-transactions/stop/` | `POST` | Stop a session remotely |

---

## **🔹 Debugging & Logs**
### **Check Running Containers**
```bash
docker ps
```

### **View Logs**
```bash
docker-compose logs -f
```
