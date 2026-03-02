# 🌐 DataScout — Custom Domain & Hosting Management Guide (Manual)

> This guide explains how to **manually add a custom domain** to your DataScout app hosted on **Amazon EC2**, **check all hosting information**, and answers the question about **pausing App Runner**.

> [!IMPORTANT]
> Your DataScout app runs on **EC2** (`http://13.221.158.225:8501`), **NOT App Runner**. App Runner was replaced because Streamlit requires WebSocket support, which App Runner doesn't provide.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [How to Add a Custom Domain Manually (EC2)](#2-how-to-add-a-custom-domain-manually-ec2)
3. [How to Check All Hosting Info Manually](#3-how-to-check-all-hosting-info-manually)
4. [Will Pausing App Runner Affect My App?](#4-will-pausing-app-runner-affect-my-app)

---

## 1. Prerequisites

Before adding a domain, make sure you have:

- ✅ A **registered domain name** (e.g., from GoDaddy, Namecheap, Route 53, Google Domains, etc.)
- ✅ Access to your **domain's DNS management panel**
- ✅ Your **EC2 instance running** (Instance ID: `i-08724135da02b9455`)
- ✅ Access to the **AWS Management Console** with appropriate IAM permissions

---

## 2. How to Add a Custom Domain Manually (EC2)

Since your app runs on EC2 (not App Runner), you need to point your domain's DNS to your EC2 instance's public IP.

### Option A — Direct DNS (Simple, No HTTPS)

#### Step 1 — Get Your EC2 Public IP

Your current public IP: **`13.221.158.225`**

> [!WARNING]
> EC2 public IPs can **change** if the instance is stopped and restarted. Use an **Elastic IP** (Option B below) to get a permanent IP.

#### Step 2 — Add DNS Records in Your Domain Registrar

Go to your domain registrar (GoDaddy, Namecheap, Route 53, etc.) and add:

| Record Type | Name (Host)       | Value               | TTL      |
|-------------|-------------------|----------------------|----------|
| **A**       | `@` (root domain) | `13.221.158.225`     | 600      |
| **A**       | `www`              | `13.221.158.225`     | 600      |

##### For GoDaddy:
1. Go to **My Products** → **DNS** next to your domain
2. Click **"Add Record"** → Type: **A**
3. **Name:** `@` | **Value:** `13.221.158.225` | **TTL:** 600
4. Click **Save**
5. Repeat with **Name:** `www`

##### For Namecheap:
1. **Dashboard** → **Domain List** → **Manage** → **Advanced DNS**
2. Click **"Add New Record"** → **A Record**
3. **Host:** `@` | **Value:** `13.221.158.225`
4. Save and repeat with **Host:** `www`

##### For AWS Route 53:
1. **Route 53** → **Hosted Zones** → your domain
2. **Create Record** → Type: **A** → Value: `13.221.158.225`
3. Click **Create records**

#### Step 3 — Update Security Group

Make sure your EC2 security group (`datascout-ec2-sg` / `sg-082aa58b3782b109b`) allows traffic on port 8501:

1. Go to **EC2** → **Security Groups** → click `datascout-ec2-sg`
2. **Inbound rules** tab → Verify these rules exist:

| Type           | Port  | Source    |
|----------------|-------|-----------|
| Custom TCP     | 8501  | 0.0.0.0/0 |
| SSH            | 22    | Your IP   |

#### Step 4 — Verify

Visit `http://yourdomain.com:8501` in your browser. Your DataScout app should load.

---

### Option B — Elastic IP (Recommended — Permanent IP)

An Elastic IP gives your EC2 a **permanent static IP** that won't change even if you stop/restart the instance.

#### Step 1 — Allocate an Elastic IP

1. Go to **EC2** → **Elastic IPs** (left sidebar under Network & Security)
2. Click **"Allocate Elastic IP address"**
3. Click **"Allocate"**

#### Step 2 — Associate with Your Instance

1. Select the new Elastic IP → **Actions** → **"Associate Elastic IP address"**
2. **Instance:** Select `i-08724135da02b9455` (your DataScout EC2)
3. Click **"Associate"**
4. Note the new **Elastic IP address** — use this in your DNS records instead of `13.221.158.225`

#### Step 3 — Update DNS Records

Same as Option A Step 2, but use your **Elastic IP** instead.

> [!TIP]
> Elastic IPs are **free** as long as they are attached to a running instance. You only get charged if the IP is allocated but **not** associated with any instance.

---

### Option C — With HTTPS (Production-Ready)

For HTTPS, you need a **reverse proxy** (like Nginx) in front of Streamlit and an SSL certificate.

#### Step 1 — Install Nginx on EC2

```bash
# SSH into your EC2
ssh -i datascout-key.pem ec2-user@13.221.158.225

# Install Nginx
sudo yum install -y nginx

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

#### Step 2 — Configure Nginx as Reverse Proxy

```bash
sudo nano /etc/nginx/conf.d/datascout.conf
```

Paste:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

```bash
sudo nginx -t        # Test config
sudo systemctl reload nginx
```

#### Step 3 — Update Security Group for Port 80 & 443

Add these inbound rules to `datascout-ec2-sg`:

| Type  | Port | Source    |
|-------|------|-----------|
| HTTP  | 80   | 0.0.0.0/0 |
| HTTPS | 443  | 0.0.0.0/0 |

#### Step 4 — Install SSL with Certbot (Free HTTPS)

```bash
sudo yum install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Follow the prompts to get your free **Let's Encrypt** SSL certificate.

#### Step 5 — Update DNS to Point to EC2

Use **A records** pointing to your EC2 IP (same as Option A/B).

#### Step 6 — Verify

Visit `https://yourdomain.com` — your app should load with a 🔒 padlock.

---

## 3. How to Check All Hosting Info Manually

### 3.1 — EC2 Instance Details

1. Go to **AWS Console** → **EC2** → **Instances**
2. Find instance `i-08724135da02b9455`
3. Check the following:

| Information              | Value / Where to Find                        |
|--------------------------|----------------------------------------------|
| **Instance ID**          | `i-08724135da02b9455`                        |
| **Instance Type**        | `t3.micro`                                   |
| **AMI**                  | `ami-0f3caa1cf4417e51b` (Amazon Linux 2023)  |
| **Availability Zone**    | `us-east-1a`                                 |
| **Public IP**            | `13.221.158.225`                             |
| **Live URL**             | `http://13.221.158.225:8501`                 |
| **Key Pair**             | `datascout-key`                              |
| **Security Group**       | `datascout-ec2-sg` (`sg-082aa58b3782b109b`)  |
| **IAM Role**             | `DataScout-EC2Role`                          |
| **Instance Profile**     | `DataScout-EC2Profile`                       |
| **Instance State**       | Running / Stopped / etc.                     |

### 3.2 — Check App Status via SSH

```bash
# SSH into the instance
ssh -i datascout-key.pem ec2-user@13.221.158.225

# Check if the Streamlit app is running
sudo systemctl status datascout.service

# View live logs
sudo journalctl -u datascout.service -f

# Check port 8501 is listening
ss -tlnp | grep 8501
```

### 3.3 — Check Environment Variables on EC2

```bash
# SSH in, then:
sudo systemctl cat datascout.service
# or
cat /etc/systemd/system/datascout.service
```

Expected variables:

| Variable                 | Expected Value                                            |
|--------------------------|-----------------------------------------------------------|
| `AWS_REGION`             | `us-east-1`                                               |
| `S3_BUCKET`              | `datascout-storage`                                       |
| `BEDROCK_AGENT_ID`       | `2V8KLCC97S`                                              |
| `BEDROCK_AGENT_ALIAS_ID` | `ADO5CA4VCF`                                             |
| `DYNAMODB_TABLE`         | `datascout-queries`                                       |
| `ENABLE_DYNAMODB`        | `true`                                                    |
| `API_GATEWAY_URL`        | `https://r19ewjwx53.execute-api.us-east-1.amazonaws.com/prod` |

### 3.4 — Check Other AWS Services

| Service          | How to Check                                                  |
|------------------|---------------------------------------------------------------|
| **S3**           | Console → S3 → `datascout-storage` → check files/folders     |
| **DynamoDB**     | Console → DynamoDB → Tables → `datascout-queries` → Items    |
| **Lambda**       | Console → Lambda → `datascout-api` → check status & logs     |
| **API Gateway**  | Console → API Gateway → `r19ewjwx53` → check stages          |
| **Bedrock**      | Console → Bedrock → Agents → Agent ID `2V8KLCC97S`           |
| **CloudWatch**   | Console → CloudWatch → Log Groups → search "datascout"       |

### 3.5 — Check via AWS CLI

```bash
# Describe your EC2 instance
aws ec2 describe-instances \
  --instance-ids i-08724135da02b9455 \
  --region us-east-1

# Check instance status
aws ec2 describe-instance-status \
  --instance-ids i-08724135da02b9455 \
  --region us-east-1

# Check security group rules
aws ec2 describe-security-groups \
  --group-ids sg-082aa58b3782b109b \
  --region us-east-1
```

---

## 4. Will Pausing App Runner Affect My App?

### ✅ Short Answer: **No, pausing App Runner will NOT affect your live app.**

Your DataScout app runs on **EC2** (`http://13.221.158.225:8501`), not App Runner. The App Runner service (`datascout-frontend-prod`) was **replaced** because Streamlit requires WebSocket support.

### What Happens If You Pause App Runner:

| Aspect                        | Effect                                         |
|-------------------------------|-------------------------------------------------|
| **Your live app (EC2)**       | ✅ **NOT affected** — continues running normally |
| **EC2 URL (`13.221.158.225:8501`)** | ✅ **Still accessible**                   |
| **App Runner URL**            | ❌ Goes offline (but you're not using it anyway) |
| **App Runner compute charges**| ✅ **Stop** — saves money                       |
| **S3, DynamoDB, Lambda, etc.**| ✅ **NOT affected**                             |

> [!TIP]
> **You should pause (or even delete) the App Runner service** to save costs, since you're not using it. Your app is fully served from EC2.

### How to Pause App Runner:

1. Go to **App Runner** → Click `datascout-frontend-prod`
2. Click **"Actions"** → **"Pause"**
3. Confirm

### How to Delete App Runner (Optional — saves all cost):

1. Go to **App Runner** → Click `datascout-frontend-prod`
2. Click **"Actions"** → **"Delete"**
3. Confirm

> [!CAUTION]
> If you **stop or terminate the EC2 instance** — **THAT will take your app offline**. Only pause/delete the App Runner service, not the EC2 instance.

---

## Quick Summary

| Task                             | How                                            |
|----------------------------------|-------------------------------------------------|
| Add custom domain                | Point DNS **A record** to EC2 IP `13.221.158.225` |
| Add HTTPS                        | Install Nginx + Certbot on EC2                  |
| Check hosting info               | EC2 Console or SSH into `i-08724135da02b9455`   |
| Pause App Runner                 | Safe ✅ — your app runs on EC2, not App Runner  |
| **Don't stop/terminate EC2**     | ⚠️ That WILL take your app offline              |

---

*Guide created for DataScout — EC2 Instance `i-08724135da02b9455` (Region: `us-east-1`)*
