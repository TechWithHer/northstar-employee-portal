# Northstar Employee Records Portal — Project Stages
## Stage 1 — AWS Network Foundation ✅

We first built the network in which everything would live.

```text
Rabbit World VPC
10.0.0.0/18
│
├── Locality1
│   Public Subnet
│   10.0.0.0/19
│
└── Locality2
    Private Subnet
    10.0.32.0/19
```

Then we added:

```text
Internet Gateway → WorldConnection

Public Route Table → SecurityGuard1
0.0.0.0/0 → Internet Gateway

Private Route Table → SecurityGuard2
```

The important concept you learned here was:

> **Route table decides where traffic can go. Security Group decides whether traffic is allowed.**

---

# Stage 2 — Application and Database Servers ✅

We created two EC2 instances.

```text
PUBLIC SUBNET
    │
    └── House
        Application Server
        10.0.13.249


PRIVATE SUBNET
    │
    └── Warehouse
        Database Server
        10.0.55.176
```

House became the application tier.

Warehouse became the database tier.

So we created our first simple **two-tier architecture**:

```text
Internet
   ↓
House
   ↓
Warehouse
```

---

# Stage 3 — Network Security Between the Tiers ✅

Then we controlled who could communicate with whom.

### House

Security Group:

```text
Entry_rules_1
```

Initially we allowed things such as:

```text
22    SSH
80    HTTP
443   HTTPS
5000  Flask/Gunicorn      ← later removed
```

### Warehouse

Security Group:

```text
Entry_rules_2
```

MySQL:

```text
3306
```

was allowed from the **House Security Group**.

Therefore:

```text
Internet ──X──> Warehouse :3306

House ─────────> Warehouse :3306
```

This was an important AWS security concept:

> Instead of allowing some random IP to reach the database, we can say **resources belonging to this application SG may reach the DB SG**.

---

# Stage 4 — Database Setup ✅

On Warehouse we installed and configured **MySQL**.

Database:

```text
WAREHOUSE_APP
```

Table:

```text
employees
```

We created approximately 100 synthetic employee records.

The Flask application connects using:

```text
PyMySQL
```

So now we had:

```text
House
 Flask
   │
   │ TCP 3306
   ▼
Warehouse
 MySQL
   │
   ▼
WAREHOUSE_APP
```

At this point we proved the **application server could communicate with the private database server**.

---

# Stage 5 — Employee Application ✅

Then we built the actual Northstar Employee Records Portal.

Our application structure became:

```text
northstar-employee-portal/
│
├── static/
│   └── style.css
│
├── templates/
│   ├── add.html
│   ├── base.html
│   ├── delete.html
│   ├── edit.html
│   ├── employees.html
│   └── home.html
│
├── app.py
├── README.md
└── requirements.txt
```

Flask handles the backend.

Jinja handles the HTML templates.

The application supports:

```text
Search
View
Add
Edit
Delete
```

At this stage the application originally ran using:

```bash
python3 app.py
```

and Flask listened on:

```text
0.0.0.0:5000
```

So users accessed:

```text
http://PUBLIC-IP:5000
```

---

# Stage 6 — Secure Database Credentials ✅

Initially the application needed DB connection information.

We did **not** want this sitting permanently in `app.py`.

So we created:

```text
AWS Secrets Manager
        │
        └── northstar/prod/database
```

containing:

```text
host
username
password
database
```

Then we created an IAM role:

```text
Northstar-House-App-Role
```

with the policy:

```text
Northstar-House-Database-Secret-Read
```

and attached the role to House.

The application retrieves its credentials using `boto3`.

So authentication became:

```text
House EC2
   ↓
IAM Role
   ↓
Temporary AWS credentials
   ↓
Secrets Manager
   ↓
DB credentials
   ↓
PyMySQL
   ↓
Warehouse
```

You also verified this with:

```bash
aws sts get-caller-identity
```

without running `aws configure`.

That's important: **no long-lived AWS access key was required on House.**

---

# Stage 7 — Replace Flask Development Server with Gunicorn ✅

Next we asked:

> Flask works. But should Flask's development server be our deployed application server?

No.

So we introduced **Gunicorn**.

Architecture became:

```text
Before:

Browser
   ↓
Flask Development Server


After:

Browser
   ↓
Gunicorn
   ↓
Flask
```

We tested:

```bash
gunicorn --bind 0.0.0.0:5000 app:app
```

Then configured:

```text
3 Gunicorn workers
```

You learned the distinction:

```text
Flask
= application framework

Gunicorn
= application server

Worker
= process capable of handling application requests
```

---

# Stage 8 — systemd Process Management ✅

Then we identified another operational problem.

If you manually start Gunicorn:

```bash
gunicorn ...
```

you don't want deployment operations to depend on someone manually SSHing in and launching the process after every reboot.

So we created:

```text
/etc/systemd/system/northstar.service
```

systemd now manages Gunicorn.

```text
EC2 boots
   ↓
systemd
   ↓
northstar.service
   ↓
Gunicorn
   ↓
Flask
```

We enabled it:

```bash
sudo systemctl enable northstar
```

And learned:

```text
start
= start it now

enable
= start automatically during future boots
```

We can operate it with:

```bash
sudo systemctl status northstar
sudo systemctl restart northstar
```

And troubleshoot using:

```bash
sudo journalctl -u northstar
```

---

# Stage 9 — Nginx Reverse Proxy ✅

Next problem:

Our user was still accessing:

```text
http://PUBLIC-IP:5000
```

We wanted a proper web-server layer.

So we installed **Nginx**.

Initially:

```text
Internet → :80 → Nginx default page

Internet → :5000 → Gunicorn
```

Then we configured Nginx:

```nginx
location / {
    proxy_pass http://127.0.0.1:5000;
}
```

Now:

```text
Browser
   ↓
HTTP :80
   ↓
Nginx
   ↓
Gunicorn :5000
   ↓
Flask
```

Therefore the user accesses:

```text
http://PUBLIC-IP
```

rather than:

```text
http://PUBLIC-IP:5000
```

---

# Stage 10 — Application Server Hardening ✅

Then we noticed something important.

Even though Nginx was supposed to be our entry point, Gunicorn was listening on:

```text
0.0.0.0:5000
```

So we changed it to:

```text
127.0.0.1:5000
```

Meaning:

> Gunicorn accepts connections only from the local House machine.

Now:

```text
Internet
   ↓
:80
   ↓
Nginx
   ↓
localhost:5000
   ↓
Gunicorn
```

Then we removed inbound TCP `5000` from:

```text
Entry_rules_1
```

So we now have **two controls**:

```text
Security Group
doesn't allow :5000 publicly
        +
Gunicorn
doesn't listen externally
```

That's a nice example of **defense in depth**.

And we actually created a failure while changing systemd. 😄

We got:

```text
northstar.service
Active: failed
```

Instead of randomly changing things, we checked:

```bash
sudo journalctl -u northstar -n 30 --no-pager
```

and found:

```text
Error: No application module specified.
```

We traced it to the systemd `ExecStart` formatting, corrected it, reloaded systemd and restored the application.

That troubleshooting episode is worth remembering for interviews.

---

# Stage 11 — Current Architecture ✅

This is where Northstar currently stands:

```text
                     INTERNET
                         │
                         │ :80
                         ▼
                  WorldConnection
                       IGW
                         │
                         ▼
              ┌─────────────────────┐
              │     Locality1       │
              │    PUBLIC SUBNET    │
              │                     │
              │       HOUSE         │
              │         │           │
              │      Nginx          │
              │       :80           │
              │         │           │
              │ 127.0.0.1:5000      │
              │         │           │
              │     Gunicorn        │
              │    3 Workers        │
              │         │           │
              │       Flask         │
              └─────────┬───────────┘
                        │
                        │ TCP 3306
                        ▼
              ┌─────────────────────┐
              │     Locality2       │
              │   PRIVATE SUBNET    │
              │                     │
              │     WAREHOUSE       │
              │         │           │
              │       MySQL         │
              │         │           │
              │   WAREHOUSE_APP     │
              └─────────────────────┘

              Flask
                │
                └── IAM Role
                       ↓
                 Secrets Manager
```

That's our **working application architecture today**.

---

# Stage 12 — CI/CD ⏳ WE STOPPED HERE

Currently deployment is still essentially:

```text
Local machine
     ↓
git push
     ↓
GitHub
     ↓

YOU manually:

SSH → House
     ↓
git pull
     ↓
systemctl restart northstar
```

We started preparing to automate this.

### What we have already completed

On House we generated a **dedicated GitHub Actions SSH key pair**:

```text
github_actions_northstar
github_actions_northstar.pub
```

We added the public key to:

```text
~/.ssh/authorized_keys
```

Then in GitHub Repository Secrets we created:

```text
EC2_SSH_KEY    ✅
EC2_HOST       ✅
EC2_USER       ✅
```

Therefore the authentication groundwork is complete:

```text
GitHub Actions
     │
     │ EC2_SSH_KEY
     ▼
SSH
     │
     ▼
ubuntu@House
```

### EXACTLY WHERE WE STOPPED

We were about to create:

```text
.github/
└── workflows/
    └── deploy.yml
```

We **have not written the CI/CD workflow yet**.

That's our next implementation step.

---

# Stage 13 — CI/CD ⏳ NEXT

Our target is:

```text
Developer
    ↓
git push
    ↓
GitHub
    ↓
GitHub Actions
    ↓
┌───────────────────┐
│        CI         │
│                   │
│ Checkout          │
│ Python setup      │
│ Dependencies      │
│ Validation/tests  │
└─────────┬─────────┘
          │ success
          ▼
┌───────────────────┐
│        CD         │
│                   │
│ SSH → House       │
│ Update code       │
│ Restart service   │
│ Verify            │
└───────────────────┘
```

After this, a successful push can automatically update the application.

---

# Stage 14 — Monitoring ⏳

After CI/CD we'll add only the monitoring necessary for this project's scope.

Think:

```text
EC2 / Application
      ↓
CloudWatch
      ↓
Metrics / Alarm
      ↓
Notification
```

Plus the operational tools we already have:

```text
systemctl
journalctl
Nginx logs
```

We're not building a giant observability platform today.

---

# Stage 15 — Final Validation & Security Sweep ⏳

Before calling Northstar complete, we'll verify:

```text
Application works
Database connectivity works
CRUD works
Nginx works
Gunicorn works
systemd works
CI/CD works
Monitoring works
```

Then inspect the repository for things that should **never** be public:

```text
Passwords
AWS access keys
Private SSH keys
Actual client information
Sensitive employee information
Unnecessary AWS identifiers
Secrets accidentally committed earlier
```

Especially because this is a **sanitized representation of real client work**, that final check matters.

---

# Stage 16 — Documentation & Project Close ⏳

Finally:

```text
README
Architecture
Security decisions
CI/CD
Monitoring
Troubleshooting
Confidentiality notice
```

Then:

```text
Final commit
    ↓
GitHub
    ↓
Tag/release
    ↓
NORTHSTAR V1 COMPLETE 🎯
```

So if you zoom way out, you've essentially moved through:

```text
NETWORK
   ↓
COMPUTE
   ↓
SECURITY
   ↓
DATABASE
   ↓
APPLICATION
   ↓
SECRETS / IAM
   ↓
GUNICORN
   ↓
SYSTEMD
   ↓
NGINX
   ↓
HARDENING
   ↓
CI/CD        ← WE ARE HERE
   ↓
MONITORING
   ↓
VALIDATION
   ↓
DOCUMENTATION
```

That sequence itself is useful to remember in an interview because you can explain Northstar as an **evolution of a deployment**, rather than throwing 15 AWS/Linux buzzwords at the interviewer.

Next, we pick up **exactly at Stage 12: `.github/workflows/deploy.yml`**.

EOF
