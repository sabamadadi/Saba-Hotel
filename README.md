# 🏨 Saba Hotel
### Hotel Management System (Flask + PostgreSQL)

<p align="center">
  <img src="demo.gif" alt="Application Demo" width="800">
</p>

<p align="center">
  A modern hotel management system with a web dashboard and Telegram bot integration.
</p>

## 📌 Overview

**Saba Hotel** is a modern and lightweight **Hotel Management System** developed as an academic project.  
The system is built using **Flask** and **PostgreSQL (Neon)** and provides a clean web interface for hotel staff, along with a **Telegram bot** for quick access to hotel status.

The project focuses on **proper database design**, **normalization**, and **real-world business rules**, making it suitable for both academic evaluation and practical extension.

## 🗂️ Database Design

### Entity–Relationship (ER) Diagram

<p align="center">
  Conceptual ER diagram of the database schema, created using
  <a href="https://dbdiagram.io" target="_blank">dbdiagram.io</a>.
</p>

<p align="center">
  <img src="ER_Diagram.png" alt="ER Diagram" width="700">
</p>

The database schema is normalized to **Third Normal Form (3NF)** and supports:
- Multiple phone numbers and addresses per guest
- Many-to-many relationships between employees and guests
- Group reservations with multiple rooms
- Reservation history tracking

The database schema file is available in:
```

database/hotel_db.sql

```

## ✨ Features

### 🌐 Web Application
- 🔐 Secure employee authentication
- 📊 Management dashboard with real-time statistics
- 🧑 Guest management (profiles, phones, addresses)
- 🚪 Room management (status, capacity, pricing)
- 🧾 Reservation management (single & group bookings)
- 🧠 Room status workflow:
  - `available`
  - `reserved`
  - `occupied`
  - `cleaning`

### 🤖 Telegram Bot
- 📊 Quick hotel status overview
- 🧹 List of rooms under cleaning
- 🧾 Active reservations
- 🚪 Available rooms
- 🔗 Direct link to the web dashboard

Bot username: **@sabahotel_bot**

## 🧱 Tech Stack

- **Backend:** Python 3.10+, Flask
- **Database:** PostgreSQL (Neon / Local)
- **Authentication:** Flask-Login
- **Frontend:** Bootstrap 5 (RTL) + Bootstrap Icons
- **Bot:** pyTelegramBotAPI (Telebot)
- **Production:** Gunicorn


## 📂 Project Structure

```

Saba-Hotel/
├─ database/
│  ├─ hotel_db.sql
│  └─ hotel_db.dbn
├─ hotel-management-system/
│  ├─ app.py
│  ├─ auth.py
│  ├─ database.py
│  ├─ bot_app.py
│  ├─ test_bot.py
│  ├─ wsgi.py
│  ├─ requirements.txt
│  ├─ static/
│  │  ├─ css/style.css
│  │  ├─ js/app.js
│  │  └─ img/bg.png
│  └─ templates/
│     ├─ base.html
│     ├─ login.html
│     ├─ dashboard.html
│     ├─ profile.html
│     ├─ guests.html
│     ├─ rooms.html
│     ├─ reservations.html
├─ ER_Diagram.png
├─ demo.gif
├─ README.md
└─ LICENSE

````

## ⚙️ Local Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/sabamadadi/Saba-Hotel.git
cd hotel-management-system
````

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

Activate:

* **Windows**

```bash
venv\Scripts\activate
```

* **Linux / macOS**

```bash
source venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file next to `app.py`:

```env
SECRET_KEY=your-secret-key

DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DBNAME?sslmode=require
DB_URI=postgresql://USER:PASSWORD@HOST:PORT/DBNAME?sslmode=require

ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
DASHBOARD_URL=https://your-app-url
```

## ▶️ Running the Project

### Web Application

```bash
python app.py
```

Open:

```
http://localhost:5000
```

### Telegram Bot

```bash
python test_bot.py
```

## 🚀 Deployment

* **Database:** Neon
* **Application:** Leapcell
* **Production Server:**

```bash
gunicorn --bind 0.0.0.0:5000 wsgi:app
```

## 🛡️ Security Notes

* Store sensitive credentials only in `.env`
* Never commit real passwords or tokens
* Hash passwords in production
* Use HTTPS in production environments


## 🧩 Future Improvements

* Check-in / Check-out workflow
* Automatic room status updates
* Payment history tracking
* Revenue reports
* Advanced role-based access control
* Telegram notifications for room cleaning

## 📜 License

MIT License
