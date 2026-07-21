# 100% Free 24/7 Cloud Deployment Guide

Here are the **top 100% FREE options** to run **Prediction_app** 24/7 in the cloud without spending a single penny or leaving your laptop on:

---

## 🌟 Option 1: GitHub Actions (100% FREE & Built-in — RECOMMENDED)

Since your code is on GitHub, you can use **GitHub Actions** to run the monitor automatically every 15 minutes (:00, :15, :30, :45) matching Kalshi 15m candle closes. Public repositories get **UNLIMITED FREE** Action minutes!

### How to Activate GitHub Actions (takes 1 minute):

1. Open your repository: [https://github.com/danelujapare-sys/Prediction_app](https://github.com/danelujapare-sys/Prediction_app)
2. Click **Settings** (top tab) -> **Secrets and variables** -> **Actions**.
3. Click **New repository secret** and add these 3 secrets:
   - Name: `RECIPIENT_EMAIL` | Value: `danelujapare@gmail.com`
   - Name: `SMTP_USERNAME`  | Value: `danelujapare@gmail.com`
   - Name: `SMTP_PASSWORD`  | Value: `rtlm fyoa maar lxcc`
   - Name: `SENDER_EMAIL`   | Value: `danelujapare@gmail.com`
4. Click **Actions** tab on GitHub -> Select **Kalshi 15m Crypto Streak Monitor** -> Click **Run workflow**.

GitHub will now execute the monitor every 15 minutes automatically in the cloud **100% FREE forever**!

---

## 🚀 Option 2: Koyeb.com (100% Free Continuous 24/7 Worker)

If you prefer a continuous daemon process running 24/7 without sleeping:

1. Sign up for a free account at [https://www.koyeb.com](https://www.koyeb.com) (No credit card required).
2. Click **Create App** -> Select **GitHub**.
3. Select repository **`danelujapare-sys/Prediction_app`**.
4. Set builder to **Dockerfile** (or Python).
5. Add Environment Variables:
   - `RECIPIENT_EMAIL` = `danelujapare@gmail.com`
   - `SMTP_USERNAME` = `danelujapare@gmail.com`
   - `SMTP_PASSWORD` = `rtlm fyoa maar lxcc`
   - `SENDER_EMAIL` = `danelujapare@gmail.com`
6. Click **Deploy**. Koyeb provides a 100% Free Nano Instance that runs 24/7 continuously.

---

## ⚡ Option 3: Oracle Cloud Always Free VPS

Oracle Cloud offers an **Always Free Tier** with 4 ARM cores + 24GB RAM that is 100% free forever:
1. Sign up at [https://www.oracle.com/cloud/free/](https://www.oracle.com/cloud/free/)
2. Create an Always Free Ubuntu VM.
3. SSH into the instance and run:
   ```bash
   git clone https://github.com/danelujapare-sys/Prediction_app.git
   cd Prediction_app
   nano .env # Paste your credentials
   docker-compose up -d --build
   ```
