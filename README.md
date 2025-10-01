# Fraud Guard 🛡️  
*A rules + ML-based fraud detection tool with Stripe integration (Flask + Python)*

[![Render Deploy](https://render.com/images/deploy-to-render-button.svg)](https://render.com)

---

## 🔎 Overview
Fraud Guard is a lightweight fraud detection service built with **Flask** that integrates directly with **Stripe Webhooks**.  

It demonstrates:
- Real-time monitoring of Stripe payment events (`payment_intent.succeeded`, `payment_intent.failed`, etc.)  
- A **rules engine** that flags disposable emails, missing customer info, and high-value transactions  
- A toy **ML-based scorer** (for demo purposes) that assigns risk scores  
- Automatic logging to **SQLite** for audit/history    

---

## 🛠️ Tech Stack
- **Backend**: Flask + Gunicorn  
- **Payments**: Stripe Webhooks API  
- **Database**: SQLite
- **Language**: Python 3.11

---

## ⚙️ How It Works
1. A customer makes a payment through Stripe.  
2. Stripe sends a **webhook event** → Fraud Guard receives it.  
3. Fraud Guard extracts details like **email, IP, amount**.  
4. A **rules engine** + optional **ML scorer** assigns a fraud risk score (0.0–1.0).  
5. Transactions are logged into a local database (`transactions.db`) with score + reason.  
6. Alerts are printed in logs for **MEDIUM/HIGH risk** events.  

---

## 🚀 Setup

Clone the repo:
```bash
git clone https://github.com/amanciomedina/fraud-guard.git
cd fraud-guard
