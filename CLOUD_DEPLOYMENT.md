# 24/7 Cloud Deployment & Email Setup Guide

This guide details how to deploy the **Kalshi Crypto Streak Email Monitor** to the cloud so it runs 24/7 autonomously **without keeping your laptop open**, sending real-time email alerts to **`danelujapare@gmail.com`** whenever any coin hits $\ge 4$ consecutive trends on Kalshi.

---

## 📧 Step 1: Configure SMTP Email Credentials (Gmail App Password)

To send actual email alerts directly to `danelujapare@gmail.com`, set up a free SMTP sender using Gmail:

1. Go to your Google Account: [https://myaccount.google.com/security](https://myaccount.google.com/security)
2. Ensure **2-Step Verification** is turned **ON**.
3. Search for **App Passwords** or visit: [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
4. Create a new App Password (name it `Kalshi Monitor`).
5. Google will display a 16-character password (e.g. `abcd efgh ijkl mnop`).
6. Add these credentials to your `.env` file or Cloud Environment Variables:

```env
RECIPIENT_EMAIL=danelujapare@gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-gmail@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
SENDER_EMAIL=your-gmail@gmail.com
```

---

## ☁️ Step 2: Deploy to Cloud (Runs Forever 24/7)

Choose any of the following 100% cloud-hosted options so you don't need your laptop open:

### Option A: Render.com (Easiest & Free/Cheap 24/7 Hosting)
1. Push your repository code to GitHub or GitLab.
2. Sign up / log in to [https://render.com](https://render.com).
3. Click **New +** -> **Background Worker**.
4. Connect your GitHub repository.
5. Set:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python src/realtime_monitor.py`
6. Under **Environment Variables**, add:
   - `RECIPIENT_EMAIL` = `danelujapare@gmail.com`
   - `SMTP_SERVER` = `smtp.gmail.com`
   - `SMTP_PORT` = `587`
   - `SMTP_USERNAME` = `your-gmail@gmail.com`
   - `SMTP_PASSWORD` = `your-16-char-app-password`
7. Click **Create Background Worker**. Render will automatically run the app 24/7 in the cloud.

---

### Option B: Railway.app (1-Click Deployment)
1. Log in to [https://railway.app](https://railway.app).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select this repository.
4. Add the Environment Variables (`RECIPIENT_EMAIL`, `SMTP_USERNAME`, `SMTP_PASSWORD`, etc.).
5. Railway automatically detects the `Dockerfile` and runs it continuously 24/7.

---

### Option C: AWS EC2 / DigitalOcean VPS (Docker Compose)
If you have a Linux VPS or AWS EC2 instance ($3–$5/mo or AWS Free Tier):

1. SSH into your VPS:
   ```bash
   ssh root@YOUR_SERVER_IP
   ```
2. Clone your project code:
   ```bash
   git clone https://github.com/YOUR_USER/kalshi-streak-monitor.git
   cd kalshi-streak-monitor
   ```
3. Edit `.env` with your SMTP details and target recipient:
   ```bash
   nano .env
   ```
4. Start container in background (detached mode):
   ```bash
   docker-compose up -d --build
   ```
5. View 24/7 live logs:
   ```bash
   docker-compose logs -f
   ```

---

## 🧪 Testing Email Setup

To verify your email credentials before starting 24/7 deployment, run:

```powershell
.\.venv\Scripts\python src/realtime_monitor.py --test-email
```

Or test a single poll pass with email alerting enabled:

```powershell
.\.venv\Scripts\python src/realtime_monitor.py --single-pass --threshold 4
```
