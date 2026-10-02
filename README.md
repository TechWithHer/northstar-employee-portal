```markdown
# Northstar Employee Records Portal
### AWS Cloud & DevOps Implementation Case Study

> **Confidentiality & Data Privacy Notice**
>
> This project is based on a real-world client implementation. The repository has been recreated and sanitized for portfolio and technical demonstration purposes.
>
> To protect client confidentiality and personal data, the actual client name, employee information, credentials, infrastructure identifiers, and other identifying information have not been disclosed.
>
> **Northstar Logistics Pte. Ltd.** is a fictional organization name used solely for this case study. Employee records used in the demonstration are synthetic.
>
> The implementation presented here demonstrates the technical architecture, Cloud/DevOps practices, deployment approach, security controls, and operational concepts used in the project, while taking client confidentiality and applicable data-protection considerations, including Singapore's PDPA, into account.

---

## 1. Project Overview

The **Northstar Employee Records Portal (NERP)** is an anonymized representation of a real-world employee records management implementation.

The objective was not simply to host a web application, but to build a structured AWS environment around it with clear separation between the application and database layers, controlled network access, secure credential management, automated application startup, reverse proxying, CI/CD, monitoring, and operational troubleshooting.

The application provides basic employee record management capabilities while keeping the database isolated from direct Internet access.

### Key Engineering Areas

- AWS VPC architecture
- Public/private subnet separation
- EC2 application and database tiers
- Security Groups and controlled network access
- Flask/Jinja web application
- Private MySQL database
- AWS Secrets Manager
- IAM role-based AWS access
- Gunicorn application server
- systemd process management
- Nginx reverse proxy
- Git and GitHub source control
- GitHub Actions CI/CD
- Amazon CloudWatch monitoring
- Linux troubleshooting and service operations

---

# 2. High-Level Architecture

```text
                           INTERNET
                              │
                              │ HTTP/HTTPS
                              ▼
                     Internet Gateway
                     "WorldConnection"
                              │
                              ▼
┌─────────────────────────────────────────────────────┐
│                  Rabbit World VPC                   │
│                     10.0.0.0/18                     │
│                                                     │
│  ┌──────────────────────────────┐                   │
│  │     Locality1 - PUBLIC       │                   │
│  │        10.0.0.0/19           │                   │
│  │                              │                   │
│  │          HOUSE EC2           │                   │
│  │              │               │                   │
│  │          Nginx :80           │                   │
│  │              │               │                   │
│  │       127.0.0.1:5000         │                   │
│  │              │               │                   │
│  │          Gunicorn            │                   │
│  │         3 Workers            │                   │
│  │              │               │                   │
│  │              ▼               │                   │
│  │        Flask + Jinja         │                   │
│  └──────────────┬───────────────┘                   │
│                 │                                   │
│                 │ TCP 3306                          │
│                 ▼                                   │
│  ┌──────────────────────────────┐                   │
│  │     Locality2 - PRIVATE      │                   │
│  │        10.0.32.0/19          │                   │
│  │                              │                   │
│  │       WAREHOUSE EC2          │                   │
│  │              │               │                   │
│  │            MySQL             │                   │
│  │              │               │                   │
│  │       WAREHOUSE_APP          │                   │
│  └──────────────────────────────┘                   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

# 3. Network Architecture

The AWS environment uses a custom VPC with separate public and private network tiers.

## VPC

```text
Name: Rabbit World
CIDR: 10.0.0.0/18
```

The VPC provides the isolated network boundary for the application.

## Public Subnet

```text
Name: Locality1
CIDR: 10.0.0.0/19
```

The public subnet contains the application server:

```text
House
```

The subnet uses a route table with Internet connectivity through the Internet Gateway.

## Private Subnet

```text
Name: Locality2
CIDR: 10.0.32.0/19
```

The private subnet contains the database server:

```text
Warehouse
```

The database is not intended to be directly accessible from the public Internet.

## Internet Gateway

```text
WorldConnection
```

The Internet Gateway provides Internet connectivity to resources using the public routing configuration.

## Routing

### Public Route Table — `SecurityGuard1`

```text
10.0.0.0/18 → local
0.0.0.0/0   → WorldConnection
```

### Private Route Table — `SecurityGuard2`

The private application tier relies on VPC-local routing for communication with the application server.

```text
10.0.0.0/18 → local
```

This allows communication between the application and database tiers without exposing MySQL directly to the Internet.

---

# 4. Security Group Design

Security Groups provide resource-level traffic control.

## Application Security Group

```text
Entry_rules_1
```

Required inbound access includes:

| Port | Purpose | Source |
|---|---|---|
| 22 | SSH Administration | Restricted administrator IP |
| 80 | HTTP | Internet |
| 443 | HTTPS / future TLS support | Internet |

Gunicorn port `5000` is **not exposed publicly**.

## Database Security Group

```text
Entry_rules_2
```

MySQL traffic is allowed on:

```text
TCP 3306
```

from the application Security Group.

Conceptually:

```text
Internet ──X──> MySQL :3306

House ─────────> Warehouse :3306
```

This ensures the application can communicate with the database while preventing direct public database access.

---

# 5. Application Layer

The employee portal is implemented using:

- Python
- Flask
- Jinja2
- PyMySQL
- HTML
- CSS

The application provides CRUD-style employee management functionality:

```text
Search Employee
View Employees
Add Employee
Edit Employee
Delete Employee
```

### Repository Structure

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
├── requirements.txt
└── README.md
```

Jinja templates provide the presentation layer while Flask handles routing and application logic.

---

# 6. Database Layer

MySQL runs on the private `Warehouse` EC2 instance.

```text
Database: WAREHOUSE_APP
Table: employees
```

Example sanitized schema:

```sql
CREATE TABLE employees (
    employee_id INT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(30),
    department VARCHAR(100),
    job_role VARCHAR(100),
    location VARCHAR(100),
    employment_status VARCHAR(20),
    joining_date DATE
);
```

All employee records represented in this repository or portfolio demonstration are synthetic and do not represent actual client employees.

The application communicates with MySQL using PyMySQL and parameterized SQL queries.

---

# 7. Secrets Management

Database credentials are not hardcoded in the application.

They are maintained in AWS Secrets Manager under a sanitized secret name:

```text
northstar/prod/database
```

The secret provides application configuration such as:

```text
host
username
password
database
```

The application retrieves the secret at runtime using the AWS SDK for Python (`boto3`).

```text
Flask Application
       │
       ▼
   IAM Role
       │
       ▼
AWS Secrets Manager
       │
       ▼
Database Credentials
       │
       ▼
    PyMySQL
       │
       ▼
Warehouse MySQL
```

No database passwords should be committed to the repository.

---

# 8. IAM and AWS Authentication

The application EC2 instance uses an IAM role:

```text
Northstar-House-App-Role
```

A dedicated policy:

```text
Northstar-House-Database-Secret-Read
```

allows the application to retrieve the required database secret.

The design avoids storing long-lived AWS access keys on the EC2 instance.

Instead:

```text
EC2 Instance
     │
     ▼
IAM Instance Role
     │
     ▼
Temporary AWS Credentials
     │
     ▼
AWS Secrets Manager
```

This provides a cleaner and more secure authentication mechanism for AWS service access.

---

# 9. Application Server — Gunicorn

During initial development, the Flask development server was sufficient to validate the application.

For the deployed environment, the application is served using **Gunicorn**, a Python WSGI application server.

```text
Gunicorn
   │
   ├── Worker 1
   ├── Worker 2
   └── Worker 3
          │
          ▼
        Flask
```

Gunicorn runs with three workers and listens only on the EC2 instance's loopback interface:

```bash
gunicorn --workers 3 --bind 127.0.0.1:5000 app:app
```

Using:

```text
127.0.0.1:5000
```

means Gunicorn is available to Nginx on the same server but is not directly exposed through the instance's network interface.

---

# 10. Process Management with systemd

Running Gunicorn manually would require an administrator to reconnect to the server and restart the application whenever the EC2 instance restarted.

To remove this dependency, Gunicorn is managed using a systemd service:

```text
northstar.service
```

The service provides:

- Automatic application startup
- Application restart capability
- Process supervision
- Boot-time startup
- Centralized service logging

The application lifecycle becomes:

```text
EC2 Starts
    │
    ▼
systemd
    │
    ▼
northstar.service
    │
    ▼
Gunicorn
    │
    ▼
Flask
```

Useful operational commands include:

```bash
sudo systemctl status northstar
sudo systemctl restart northstar
sudo journalctl -u northstar
sudo journalctl -u northstar -f
```

---

# 11. Nginx Reverse Proxy

Nginx provides the public-facing web-server layer.

Nginx listens on standard HTTP port:

```text
80
```

and forwards requests internally to Gunicorn:

```text
127.0.0.1:5000
```

Request flow:

```text
Browser
   │
   │ HTTP :80
   ▼
Nginx
   │
   │ proxy_pass
   ▼
127.0.0.1:5000
   │
   ▼
Gunicorn
   │
   ▼
Flask
```

Users therefore access the application using the standard web endpoint rather than connecting directly to the Gunicorn application server.

This also provides an additional security boundary:

```text
Internet
   │
   │ :80
   ▼
Nginx
   │
   │ localhost only
   ▼
Gunicorn :5000
```

TCP port `5000` is not exposed through the application Security Group.

---

# 12. End-to-End Request Flow

A typical request passes through multiple infrastructure and application layers:

```text
User
 │
 ▼
Internet
 │
 ▼
Internet Gateway
 │
 ▼
Public Subnet
 │
 ▼
Application Security Group
 │
 ▼
House EC2
 │
 ▼
Nginx :80
 │
 ▼
Gunicorn 127.0.0.1:5000
 │
 ▼
Flask / Jinja
 │
 ├──────────────► IAM Role
 │                    │
 │                    ▼
 │             Secrets Manager
 │                    │
 │             DB Credentials
 │                    │
 ▼                    │
PyMySQL ◄─────────────┘
 │
 │ TCP :3306
 ▼
VPC Local Routing
 │
 ▼
Database Security Group
 │
 ▼
Warehouse EC2
 │
 ▼
MySQL
 │
 ▼
WAREHOUSE_APP
 │
 ▼
employees
```

The database response returns through the application, where Flask processes the result and Jinja renders the web page.

---

# 13. CI/CD Pipeline

The application source is maintained using Git and GitHub.

GitHub Actions provides the CI/CD workflow.

```text
Developer
    │
    │ git push
    ▼
GitHub Repository
    │
    ▼
GitHub Actions
    │
    ├── Checkout Code
    │
    ├── Configure Python
    │
    ├── Install Dependencies
    │
    ├── Validate/Test
    │
    └── Continue only if CI succeeds
    │
    ▼
Deployment
    │
    ▼
House EC2
    │
    ├── Update Application
    ├── Install/Update Dependencies
    ├── Restart northstar.service
    └── Verify Application
```

Sensitive deployment information is maintained using GitHub Actions secrets rather than being committed to source control.

### Deployment Evolution

Originally:

```text
Developer
   │
   ▼
git push
   │
   ▼
GitHub

Manual:
SSH → git pull → restart application
```

Final workflow:

```text
Developer
   │
   ▼
git push
   │
   ▼
GitHub
   │
   ▼
CI Validation
   │
   ▼
Automated Deployment
   │
   ▼
Application Restart
   │
   ▼
Verification
```

This provides a repeatable deployment process and reduces manual operational steps.

---

# 14. Monitoring & Operations

The project uses multiple levels of operational visibility.

## Application Service

```bash
sudo systemctl status northstar
```

## Application Logs

```bash
sudo journalctl -u northstar
```

Live logs can be followed using:

```bash
sudo journalctl -u northstar -f
```

## Nginx

Nginx access and error logs provide visibility into web requests and reverse-proxy failures.

## AWS Monitoring

Amazon CloudWatch provides infrastructure monitoring for AWS resources.

Monitoring focuses on operational signals such as:

- EC2 CPU utilization
- Instance health
- Application/service availability
- Infrastructure resource utilization
- Defined alarm thresholds

This provides visibility across both the application and infrastructure layers.

---

# 15. Troubleshooting & Operational Learning

A major objective of this implementation was understanding how to troubleshoot an application across multiple infrastructure layers.

The troubleshooting methodology used throughout the project was:

```text
Observe
   │
   ▼
Identify the failing layer
   │
   ▼
Inspect status/logs
   │
   ▼
Form a hypothesis
   │
   ▼
Validate
   │
   ▼
Apply the fix
   │
   ▼
Retest
```

Issues encountered during implementation included:

- VPC and routing configuration
- Security Group connectivity
- Private database connectivity
- MySQL service availability
- Secrets Manager configuration
- IAM authorization
- Application configuration
- Gunicorn startup
- systemd service configuration
- Nginx reverse proxy configuration
- Public application port exposure

### Example: Gunicorn/systemd Failure

After modifying the Gunicorn binding configuration, the service failed.

The first diagnostic step was:

```bash
sudo systemctl status northstar
```

The service showed:

```text
Active: failed
```

Application logs were then inspected:

```bash
sudo journalctl -u northstar -n 30 --no-pager
```

The logs revealed:

```text
Error: No application module specified.
```

The issue was traced to the Gunicorn `ExecStart` definition in the systemd service.

After correcting the service configuration:

```bash
sudo systemctl daemon-reload
sudo systemctl restart northstar
```

the application returned to:

```text
Active: active (running)
```

This demonstrated the importance of identifying the failing layer before making unrelated networking or infrastructure changes.

---

# 16. Security Controls

The implementation applies several security principles.

### Network Segmentation

```text
Application Tier → Public Subnet
Database Tier    → Private Subnet
```

### Database Isolation

MySQL is not exposed to the public Internet.

Only the application tier is permitted to connect to TCP `3306`.

### Application Server Isolation

Gunicorn listens on:

```text
127.0.0.1:5000
```

rather than the EC2 instance's externally reachable interface.

### Restricted Public Ports

The application Security Group does not expose TCP `5000`.

External application traffic enters through Nginx.

### Secrets Management

Database credentials are retrieved from AWS Secrets Manager rather than being stored directly in application source code.

### IAM Roles

The EC2 application server uses an IAM instance role instead of long-lived AWS credentials.

### Least Privilege

The application IAM policy is scoped to the AWS permissions required by the application.

### Administrative Access

SSH access is restricted to approved administrative sources rather than being universally accessible.

---

# 17. Technology Stack

| Layer | Technology |
|---|---|
| Cloud Platform | AWS |
| Network | Amazon VPC |
| Compute | Amazon EC2 |
| Network Security | Security Groups |
| AWS Authorization | IAM |
| Secrets | AWS Secrets Manager |
| Application | Python / Flask |
| Templates | Jinja2 |
| Database | MySQL |
| Database Client | PyMySQL |
| Application Server | Gunicorn |
| Web Server | Nginx |
| Linux Service Management | systemd |
| Source Control | Git / GitHub |
| CI/CD | GitHub Actions |
| Monitoring | Amazon CloudWatch |
| Operating System | Ubuntu Linux |

---

# 18. Architecture Responsibilities

Each component has a clearly defined responsibility.

```text
Nginx
  └── Handles incoming web traffic
             │
             ▼
Gunicorn
  └── Runs the Python application
             │
             ▼
Flask
  └── Implements application logic
             │
             ▼
PyMySQL
  └── Communicates with MySQL
```

Supporting infrastructure:

```text
systemd
  └── Manages the Gunicorn process

IAM
  └── Controls AWS authorization

Secrets Manager
  └── Protects database credentials

Security Groups
  └── Control network traffic

GitHub Actions
  └── Automates CI/CD

CloudWatch
  └── Provides infrastructure monitoring
```

The architecture deliberately separates responsibilities instead of exposing or combining every component into a single layer.

---

# 19. Key DevOps Learnings

This implementation reinforced that deploying an application involves significantly more than making the application code run.

A production-style request crosses multiple layers:

```text
Code
  ↓
Application Framework
  ↓
Application Server
  ↓
Process Manager
  ↓
Web Server
  ↓
Operating System
  ↓
Network
  ↓
Security Controls
  ↓
Cloud Infrastructure
  ↓
Database
  ↓
Monitoring
  ↓
Deployment Automation
```

A problem at any layer can affect application availability.

The key operational skill is therefore not only knowing individual AWS or Linux services, but being able to trace a request across the architecture, identify the failing layer, use logs and monitoring to validate the problem, and restore service systematically.

---

# 20. Final Architecture

```text
                         Developer
                             │
                          git push
                             │
                             ▼
                          GitHub
                             │
                             ▼
                    GitHub Actions
                       CI / CD
                             │
                             ▼
──────────────────────────── AWS ───────────────────────────

                          Internet
                             │
                             ▼
                    Internet Gateway
                    WorldConnection
                             │
                             ▼
               ┌─────────────────────────┐
               │      Rabbit World       │
               │      10.0.0.0/18        │
               │                         │
               │   PUBLIC - Locality1    │
               │                         │
               │      Entry_rules_1      │
               │             │           │
               │             ▼           │
               │           HOUSE         │
               │             │           │
               │        Nginx :80        │
               │             │           │
               │     127.0.0.1:5000      │
               │             │           │
               │         Gunicorn        │
               │        3 Workers        │
               │             │           │
               │           Flask         │
               │             │           │
               │       ┌─────┴─────┐     │
               │       │           │     │
               │       ▼           ▼     │
               │     IAM       Secrets   │
               │     Role      Manager   │
               │                   │     │
               │             Credentials │
               │                   │     │
               │                   ▼     │
               │                PyMySQL   │
               │                   │     │
               │              TCP :3306  │
               │                   │     │
               │                   ▼     │
               │ PRIVATE - Locality2     │
               │                   │     │
               │             Entry_rules_2
               │                   │     │
               │                   ▼     │
               │               WAREHOUSE │
               │                   │     │
               │                 MySQL   │
               │                   │     │
               │             WAREHOUSE_APP
               │                         │
               └─────────────────────────┘
```

---

## Disclaimer

This repository is a **sanitized portfolio representation of a real-world client implementation**.

`Northstar Logistics Pte. Ltd.`, employee identities, employee records, resource names, IP addresses, account information, credentials, and other identifying information presented for demonstration purposes are fictional, synthetic, anonymized, or recreated.

No client confidential information or actual employee personal data is intended to be published in this repository.

The repository is intended solely to demonstrate Cloud, AWS, DevOps, Linux, deployment, security, CI/CD, monitoring, and troubleshooting practices.
```