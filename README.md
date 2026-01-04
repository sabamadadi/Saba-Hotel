
# 🏨 Saba Hotel

## سیستم مدیریت هتل (Flask + PostgreSQL/Neon)

به **Saba Hotel** خوش اومدی 👋
این پروژه یک **سیستم مدیریت هتل** مدرن و ساده است که با **Flask** پیاده‌سازی شده و از **PostgreSQL (Neon)** استفاده می‌کند.
در کنار پنل وب، یک **بات تلگرام** هم برای مشاهده وضعیت سریع هتل طراحی شده است 📲✨

---

## ✨ امکانات پروژه

### 🌐 پنل وب (Flask)

* 🔐 لاگین امن کارمندان (Employee)
* 📊 داشبورد مدیریتی

  * تعداد کل اتاق‌ها
  * اتاق‌های خالی (available)
  * رزروهای فعال (active)
  * نمایش اتاق‌های در حال نظافت (cleaning 🧹)
* 🧑‍🤝‍🧑 مدیریت مهمان‌ها (Guest)
* 🚪 مدیریت اتاق‌ها (Room)
* 🧾 مدیریت رزروها (Reservation)
* 🧠 وضعیت‌های استاندارد اتاق:

  * ✅ `available` — خالی و آماده
  * 🟡 `reserved` — رزرو شده (مهمان هنوز نیامده)
  * 🔴 `occupied` — اشغال (مهمان داخل اتاق)
  * 🧹 `cleaning` — در حال نظافت

---

### 🤖 بات تلگرام

بات تلگرام برای دسترسی سریع مدیر یا کارمند به وضعیت هتل:

* 📊 وضعیت سریع هتل
* 🧹 لیست اتاق‌های cleaning
* 🧾 لیست رزروهای active
* 🚪 لیست اتاق‌های available
* 🔗 لینک داشبورد
* آدرس بات: **@sabahotel_bot**

---

## 🧱 تکنولوژی‌ها

* 🐍 Python 3.10+
* 🌶 Flask
* 🐘 PostgreSQL (Neon / Local)
* 🔐 Flask-Login
* 🎨 Bootstrap 5 (RTL) + Bootstrap Icons
* 🤖 pyTelegramBotAPI (telebot)
* ⚙️ Gunicorn (Production)

---

## 📂 ساختار پروژه

```
hotel-management-system/
├─ app.py
├─ auth.py
├─ database.py
├─ wsgi.py
├─ bot_app.py        # منطق اصلی بات تلگرام
├─ test_bot.py       # فایل اجرای بات
├─ requirements.txt
├─ .env
├─ static/
│  ├─ css/style.css
│  ├─ js/app.js
│  └─ img/bg.jpg
└─ templates/
   ├─ base.html
   ├─ login.html
   ├─ dashboard.html
   ├─ profile.html
   ├─ guests.html
   ├─ rooms.html
   ├─ reservations.html
```

---

## ⚙️ نصب و راه‌اندازی (Local)

### 1️⃣ کلون پروژه

```
git clone <REPO_URL>
cd hotel-management-system
```

### 2️⃣ ساخت محیط مجازی

```
python -m venv venv
```

ویندوز:

```
venv\Scripts\activate
```

لینوکس / مک:

```
source venv/bin/activate
```

### 3️⃣ نصب وابستگی‌ها

```
pip install -r requirements.txt
```

---

## 🔑 تنظیم فایل `.env`

یک فایل `.env` کنار `app.py` بساز:

```
SECRET_KEY=your-secret-key

DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DBNAME?sslmode=require
DB_URI=postgresql://USER:PASSWORD@HOST:PORT/DBNAME?sslmode=require

ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

BOT_TOKEN=123456:ABCDEF

DASHBOARD_URL=https://YOUR_APP.leapcell.dev
```

📌 نکته:

* `DATABASE_URL` → وب‌اپ Flask
* `DB_URI` → بات تلگرام (می‌تواند همان DATABASE_URL باشد)

---

## ▶️ اجرای پروژه

### اجرای وب‌اپ

```
python app.py
```

آدرس:

```
http://localhost:5000
```

### اجرای بات تلگرام

```
python test_bot.py
```

---

## 🚀 Deploy روی Leapcell

* دیتابیس روی **Neon**
* وب‌اپ روی **Leapcell**

برای production:

```
gunicorn --bind 0.0.0.0:5000 wsgi:app
```

متغیرهای `.env` را در **Environment Variables** تنظیم کن.

---

## 🧪 تست سریع دیتابیس

اتاق در حال نظافت:

```
UPDATE room SET status='cleaning' WHERE room_id=101;
```

اتاق خالی:

```
UPDATE room SET status='available' WHERE room_id=101;
```

---

## 🛡️ نکات امنیتی

* 🔑 SECRET_KEY قوی انتخاب کن
* ❌ BOT_TOKEN را commit نکن
* 🔒 اطلاعات حساس فقط در `.env`
* 🌐 برای production از SSL استفاده کن

---

## 🧩 ایده‌های توسعه آینده 🚀

* دکمه Check-in / Check-out
* تغییر خودکار status بر اساس تاریخ
* نوتیف تلگرام هنگام cleaning
* گزارش درآمد و پرداخت‌ها
* سطوح دسترسی پیشرفته کارمندان

---

## 📜 لایسنس

MIT

---

ساخته شده با ❤️ برای **Saba Hotel**

---
