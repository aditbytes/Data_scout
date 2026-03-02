# 🖥️ DataScout — EC2 Monitoring & Logs Guide (Manual)

> Complete guide to SSH into your EC2, check logs, monitor app health, and troubleshoot issues.

> **Instance ID:** `i-08724135da02b9455` | **IP:** `13.221.158.225` | **Region:** `us-east-1`

---

## 1. SSH Into Your EC2

```bash
# From your local machine (make sure you're in the Data_scout directory)
ssh -i datascout-key.pem ec2-user@13.221.158.225
```

> [!TIP]
> If you get a "permission denied" error on the key file, run:
> ```bash
> chmod 400 datascout-key.pem
> ```

---

## 2. Check App Status

```bash
# Is the DataScout service running?
sudo systemctl status datascout.service
```

**What to look for:**
- `Active: active (running)` ✅ → App is running
- `Active: failed` ❌ → App crashed — check logs below
- `Active: inactive (dead)` ⚠️ → App is stopped

**Start / Stop / Restart the app:**
```bash
sudo systemctl start datascout.service      # Start
sudo systemctl stop datascout.service       # Stop
sudo systemctl restart datascout.service    # Restart (use after code changes)
```

---

## 3. Check App Logs (Streamlit / DataScout)

### Live Logs (real-time — follow mode)
```bash
# Watch logs as they appear in real-time (Ctrl+C to stop)
sudo journalctl -u datascout.service -f
```

### Recent Logs (last 50 / 100 lines)
```bash
sudo journalctl -u datascout.service -n 50      # Last 50 lines
sudo journalctl -u datascout.service -n 100     # Last 100 lines
```

### Logs from Today Only
```bash
sudo journalctl -u datascout.service --since today
```

### Logs from a Specific Time Range
```bash
# Last 1 hour
sudo journalctl -u datascout.service --since "1 hour ago"

# Last 30 minutes
sudo journalctl -u datascout.service --since "30 min ago"

# Specific date/time range
sudo journalctl -u datascout.service --since "2026-03-01 18:00:00" --until "2026-03-01 22:00:00"
```

### Search Logs for Errors
```bash
# Find all ERROR lines
sudo journalctl -u datascout.service | grep -i "error"

# Find all WARNING lines
sudo journalctl -u datascout.service | grep -i "warning"

# Find all EXCEPTION lines
sudo journalctl -u datascout.service | grep -i "exception"

# Find Bedrock-related logs
sudo journalctl -u datascout.service | grep -i "bedrock"
```

### Export Logs to a File
```bash
sudo journalctl -u datascout.service --since today > /tmp/datascout-logs.txt
```

---

## 4. Check the Service Configuration

```bash
# View the full systemd service file
sudo systemctl cat datascout.service

# Or directly
cat /etc/systemd/system/datascout.service
```

This shows: working directory, start command, environment variables, user, etc.

---

## 5. Check Environment Variables

```bash
# View env vars set in the service file
sudo systemctl cat datascout.service | grep -i "environment"

# Or check .env file if used
cat /home/ec2-user/Data_scout/.env 2>/dev/null || echo "No .env file found"
```

**Expected variables:**

| Variable | Value |
|----------|-------|
| `AWS_REGION` | `us-east-1` |
| `S3_BUCKET` | `datascout-storage` |
| `BEDROCK_AGENT_ID` | `2V8KLCC97S` |
| `BEDROCK_AGENT_ALIAS_ID` | `ADO5CA4VCF` |
| `DYNAMODB_TABLE` | `datascout-queries` |
| `API_GATEWAY_URL` | `https://r19ewjwx53.execute-api.us-east-1.amazonaws.com/prod` |

---

## 6. Check System Resources

### CPU & Memory Usage
```bash
# Quick overview
free -h                  # Memory usage
top -bn1 | head -20      # CPU + process usage (snapshot)
htop                     # Interactive monitor (if installed)
```

### Disk Space
```bash
df -h                    # Disk usage by partition
du -sh /home/ec2-user/*  # Size of each folder in home
```

### Running Processes
```bash
# Is Streamlit actually running?
ps aux | grep streamlit

# What's using port 8501?
ss -tlnp | grep 8501
```

---

## 7. Check Network & Connectivity

### Is Port 8501 Open?
```bash
ss -tlnp | grep 8501
# Expected: LISTEN  0  128  0.0.0.0:8501
```

### Test Outbound Connectivity (to AWS services)
```bash
# Can the EC2 reach S3?
aws s3 ls s3://datascout-storage/ --region us-east-1

# Can the EC2 reach DynamoDB?
aws dynamodb describe-table --table-name datascout-queries --region us-east-1

# Can the EC2 reach Bedrock?
aws bedrock-agent get-agent --agent-id 2V8KLCC97S --region us-east-1

# Can the EC2 reach API Gateway?
curl -s https://r19ewjwx53.execute-api.us-east-1.amazonaws.com/prod/health
```

### Check Security Group (from AWS Console or CLI)
```bash
aws ec2 describe-security-groups \
  --group-ids sg-082aa58b3782b109b \
  --region us-east-1 \
  --query "SecurityGroups[0].IpPermissions" \
  --output table
```

---

## 8. Check EC2 Instance Details

### From Inside EC2 (via SSH)
```bash
# Instance metadata
curl -s http://169.254.169.254/latest/meta-data/instance-id
curl -s http://169.254.169.254/latest/meta-data/instance-type
curl -s http://169.254.169.254/latest/meta-data/public-ipv4
curl -s http://169.254.169.254/latest/meta-data/ami-id
curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone
```

### From AWS Console
1. Go to **EC2** → **Instances** → click `i-08724135da02b9455`
2. Tabs to check:
   - **Details** → Instance type, public IP, AMI, key pair
   - **Security** → Security group, IAM role
   - **Networking** → Public/private IP, VPC, subnet
   - **Storage** → EBS volumes attached
   - **Monitoring** → CPU, network, disk CloudWatch graphs
   - **Status checks** → System & instance health

### From AWS CLI (your local terminal)
```bash
aws ec2 describe-instances \
  --instance-ids i-08724135da02b9455 \
  --region us-east-1 \
  --query "Reservations[0].Instances[0].{State:State.Name, IP:PublicIpAddress, Type:InstanceType, AZ:Placement.AvailabilityZone}" \
  --output table
```

---

## 9. Check CloudWatch Logs (AWS Console)

1. Go to **CloudWatch** → **Log Groups**
2. Search for any log group containing "datascout"
3. Click the log group → click a **log stream** → view entries

### EC2 System Logs (from Console)
1. Go to **EC2** → **Instances** → select your instance
2. **Actions** → **Monitor and troubleshoot** → **Get system log**
3. This shows boot-time logs (useful if instance won't start)

---

## 10. Check CloudWatch Metrics (AWS Console)

1. Go to **EC2** → **Instances** → click `i-08724135da02b9455`
2. Click the **"Monitoring"** tab
3. View graphs for:

| Metric                 | What It Shows                          |
|------------------------|----------------------------------------|
| **CPU Utilization**    | How much CPU the instance is using     |
| **Network In/Out**     | Data transfer in bytes                 |
| **Disk Read/Write Ops**| Storage I/O operations                 |
| **Status Checks**      | System & instance health (should be ✅) |

---

## 11. Update & Redeploy Code on EC2

If you push code changes to GitHub and want to update EC2:

```bash
# SSH into EC2
ssh -i datascout-key.pem ec2-user@13.221.158.225

# Go to project directory
cd /home/ec2-user/Data_scout

# Pull latest code
git pull origin main

# Install any new dependencies
pip install -r requirements.txt

# Restart the app
sudo systemctl restart datascout.service

# Verify it's running
sudo systemctl status datascout.service
```

---

## 12. Troubleshooting Quick Reference

| Problem | Command to Debug |
|---------|-----------------|
| App not loading | `sudo systemctl status datascout.service` |
| App crashed | `sudo journalctl -u datascout.service -n 100` |
| Port not listening | `ss -tlnp \| grep 8501` |
| Can't SSH in | Check Security Group allows port 22 from your IP |
| Out of disk space | `df -h` and `du -sh /home/ec2-user/*` |
| High CPU | `top` or `htop` |
| Can't reach AWS services | `aws s3 ls` (check IAM role attached) |
| Need to restart | `sudo systemctl restart datascout.service` |
| See all errors | `sudo journalctl -u datascout.service \| grep -i error` |

---

*Guide for DataScout EC2 Instance `i-08724135da02b9455` — Region: `us-east-1`*
