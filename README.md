# Northstar Employee Records Portal

A sanitized portfolio representation of a real-world client
implementation, demonstrating AWS networking, secure application
deployment, CI/CD, database isolation, secrets management, and
infrastructure monitoring.

> **Confidentiality & Data Privacy Notice**
>
> This project is based on a real-world client implementation and has
> been recreated and sanitized for portfolio and technical demonstration
> purposes. The actual client name, employee information, credentials,
> infrastructure identifiers, and other identifying information are not
> disclosed.
>
> **Northstar Logistics Pte. Ltd.** is a fictional alias used for this
> portfolio version. All employee records shown in the project are
> synthetic. The implementation is presented with client
> confidentiality, security, and applicable Singapore data-protection
> considerations in mind.

------------------------------------------------------------------------

## 1. Project Overview

Northstar Employee Records Portal (NERP) is a small internal
employee-management application deployed on AWS.

The project was built to demonstrate the complete operational path of an
application rather than only application development:

-   AWS VPC and subnet design
-   Public and private workload separation
-   Security Group-based access control
-   Linux administration
-   Nginx reverse proxy
-   Gunicorn application server
-   Flask/Jinja application deployment
-   MySQL database connectivity
-   AWS IAM roles
-   AWS Secrets Manager
-   GitHub Actions CI/CD
-   CloudWatch monitoring and SNS alerting
-   Infrastructure troubleshooting and security cleanup

The application supports employee search and basic CRUD operations
against a MySQL database.

------------------------------------------------------------------------

## 2. Architecture

``` text
                              INTERNET
                                  |
                                  | HTTP :80
                                  v
                         Internet Gateway
                         "WorldConnection"
                                  |
                                  v
+------------------------------------------------------------------+
|                    Rabbit World VPC                               |
|                       10.0.0.0/18                                 |
|                                                                  |
|   +----------------------------+                                  |
|   | Public Subnet: Locality1   |                                  |
|   |                            |                                  |
|   |          House EC2         |                                  |
|   |              |             |                                  |
|   |           Nginx :80        |                                  |
|   |              |             |                                  |
|   |       127.0.0.1:5000       |                                  |
|   |              |             |                                  |
|   |          Gunicorn          |                                  |
|   |              |             |                                  |
|   |          Flask/Jinja       |                                  |
|   +--------------|-------------+                                  |
|                  |                                                |
|                  | Private VPC traffic                            |
|                  | TCP :3306                                     |
|                  v                                                |
|   +----------------------------+                                  |
|   | Private Subnet: Locality2  |                                  |
|   |                            |                                  |
|   |        Warehouse EC2       |                                  |
|   |              |             |                                  |
|   |         MySQL :3306        |                                  |
|   |              |             |                                  |
|   |       WAREHOUSE_APP        |                                  |
|   +----------------------------+                                  |
|                                                                  |
+------------------------------------------------------------------+

House IAM Role
      |
      +------> AWS Secrets Manager
               northstar/prod/database

Developer
   |
   | git push
   v
GitHub
   |
   v
GitHub Actions
   |
   +--> CI validation
   |
   +--> CD via SSH --> House --> restart northstar.service

House EC2
   |
   v
Amazon CloudWatch
   |
   v
High CPU Alarm
   |
   v
Amazon SNS --> Email notification
```

------------------------------------------------------------------------

## 3. AWS Network Design

### VPC

The application is deployed inside a dedicated VPC:

``` text
Rabbit World
CIDR: 10.0.0.0/18
```

The VPC is divided into public and private subnets.

### Public Subnet --- Locality1

`House`, the application server, resides in the public subnet.

Its route table contains the VPC local route and a default route through
the Internet Gateway:

``` text
10.0.0.0/18 -> local
0.0.0.0/0   -> Internet Gateway
```

This allows the web server to receive Internet traffic.

### Private Subnet --- Locality2

`Warehouse`, the database server, resides in the private subnet.

Its final route table contains only:

``` text
10.0.0.0/18 -> local
```

The database subnet therefore has no active default Internet route in
the final project configuration.

A NAT Gateway was evaluated during the project but removed because it
was unnecessary for the final application path and introduced additional
cost. A stale NAT blackhole route was also removed during infrastructure
cleanup.

------------------------------------------------------------------------

## 4. Security Groups

### House --- Entry_rules_1

House accepts public HTTP traffic for the application.

``` text
TCP 80 -> Internet
```

SSH access is currently required by the GitHub-hosted CI/CD deployment
workflow. This is documented as a current lab limitation and is
discussed under **Known Limitations and Production Improvements**.

Gunicorn port `5000` is **not exposed through the Security Group**.

### Warehouse --- Entry_rules_2

The final database Security Group permits only MySQL traffic from
resources associated with the House Security Group:

``` text
TCP 3306
Source: Entry_rules_1
```

The database is therefore not directly exposed to the Internet.

Temporary SSH, HTTPS, EC2 Instance Connect, and other experimental
inbound rules were removed during the final security cleanup.

------------------------------------------------------------------------

## 5. Application Stack

The application stack on House is:

``` text
Nginx
  |
  v
Gunicorn
  |
  v
Flask
  |
  v
Jinja templates
  |
  v
PyMySQL
```

### Nginx

Nginx is the public-facing web server and listens on port `80`.

Requests are reverse proxied to:

``` text
127.0.0.1:5000
```

### Gunicorn

Gunicorn runs the Flask application with three workers:

``` text
gunicorn --workers 3 --bind 127.0.0.1:5000 app:app
```

Binding Gunicorn to `127.0.0.1` means it is accessible only locally from
House and cannot be reached directly from the Internet.

Three workers are sufficient for the scope and traffic of this portfolio
implementation. Production worker sizing should be based on CPU, memory,
request characteristics, concurrency, database connections, and
load-testing results.

### systemd

Gunicorn is managed by a systemd service named:

``` text
northstar.service
```

This provides:

-   automatic application startup
-   process supervision
-   automatic restart
-   centralized service status
-   journal-based logging

Useful operational commands include:

``` bash
sudo systemctl status northstar
sudo systemctl restart northstar
sudo journalctl -u northstar
sudo journalctl -u northstar -f
```

------------------------------------------------------------------------

## 6. Database

The database runs on the private `Warehouse` EC2 instance using MySQL.

Database:

``` text
WAREHOUSE_APP
```

The `employees` table stores synthetic employee records for the
portfolio implementation.

Example schema:

``` sql
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

The application uses parameterized SQL queries when interacting with
employee records.

------------------------------------------------------------------------

## 7. Secrets Management and IAM

Database credentials are not stored directly in the Flask source code.

They are stored in AWS Secrets Manager:

``` text
northstar/prod/database
```

The secret contains the database connection information required by the
application.

House uses an EC2 IAM role:

``` text
Northstar-House-App-Role
```

with a scoped policy that allows the application to retrieve the
required database secret.

The authentication flow is:

``` text
House EC2
   |
   | assumes IAM role automatically
   v
Northstar-House-App-Role
   |
   | secretsmanager:GetSecretValue
   v
AWS Secrets Manager
   |
   v
Database credentials
   |
   v
Flask / PyMySQL
   |
   v
Warehouse :3306
```

No `aws configure` credentials or long-lived AWS access keys are
required by the application.

------------------------------------------------------------------------

## 8. End-to-End Request Flow

When a user searches for an employee:

``` text
Browser
   |
   | HTTP :80
   v
Internet Gateway
   |
   v
Entry_rules_1
   |
   v
House
   |
   v
Nginx :80
   |
   | reverse proxy
   v
127.0.0.1:5000
   |
   v
Gunicorn
   |
   v
Flask
   |
   +------> IAM Role ------> Secrets Manager
   |
   | TCP :3306
   v
Entry_rules_2
   |
   v
Warehouse
   |
   v
MySQL
   |
   v
Employee record
   |
   v
Flask -> Jinja -> Gunicorn -> Nginx -> Browser
```

House-to-Warehouse database traffic remains inside the VPC and uses the
VPC local route. It does not require an Internet Gateway, NAT Gateway,
or the VPC endpoints that were evaluated earlier in the project.

------------------------------------------------------------------------

## 9. CI/CD with GitHub Actions

The repository uses GitHub Actions to validate and deploy changes pushed
to the `main` branch.

### Continuous Integration

The CI job:

1.  checks out the repository
2.  creates a clean Ubuntu runner
3.  installs Python 3.12
4.  installs application dependencies
5.  validates `app.py` using Python bytecode compilation

``` text
git push
   |
   v
GitHub Actions
   |
   v
Checkout
   |
   v
Python 3.12
   |
   v
Install dependencies
   |
   v
python -m py_compile app.py
```

The CI runner is intentionally not given production database access
merely to perform syntax validation.

### Continuous Deployment

Deployment runs only after CI succeeds.

``` text
CI success
   |
   v
GitHub Actions
   |
   | SSH
   v
House
   |
   v
git pull origin main
   |
   v
restart northstar.service
   |
   v
verify service is active
```

Repository secrets are used for deployment configuration:

``` text
EC2_HOST
EC2_USER
EC2_SSH_KEY
```

The private SSH key is stored as a GitHub Actions secret rather than
committed to the repository.

### CI/CD Troubleshooting Performed

During implementation, the deployment pipeline exposed two useful
operational failures:

**GitHub runner could not reach House on TCP 22**

The deployment failed during `ssh-keyscan`. Investigation showed that
the Security Group allowed SSH only from the administrator's IP and not
from the GitHub-hosted runner.

**SSH private key failed with `error in libcrypto`**

Network connectivity was working, but authentication failed because the
multiline private key stored in the GitHub secret had not been
reconstructed correctly. Replacing the secret with the complete OpenSSH
private key, including its original line breaks, resolved the issue.

------------------------------------------------------------------------

## 10. Monitoring and Alerting

Amazon CloudWatch is used for basic EC2 infrastructure monitoring.

The project uses the standard EC2 `CPUUtilization` metric with basic
monitoring.

A CloudWatch alarm named:

``` text
Northstar-House-High-CPU
```

is configured to enter the alarm state when:

``` text
CPUUtilization > 70%
for 2 consecutive 5-minute periods
```

Notification flow:

``` text
House EC2
   |
   v
CloudWatch CPUUtilization
   |
   | > 70% for 2 x 5 min
   v
CloudWatch Alarm
   |
   v
SNS topic: northstar-alerts
   |
   v
Email notification
```

Detailed EC2 monitoring was intentionally not enabled because one-minute
infrastructure metrics were not necessary for the scope of this project.

Application and service troubleshooting currently uses systemd journal
logs and Nginx logs rather than a centralized CloudWatch Logs pipeline.

------------------------------------------------------------------------

## 11. Infrastructure Cleanup

The project included several networking experiments while evaluating
private-instance administration and outbound connectivity.

Before finalizing the architecture, unused resources and rules were
reviewed and removed.

Cleanup included:

-   removing unused SSM interface endpoints
-   removing the unused `ssmmessages` interface endpoint
-   removing the EC2 Instance Connect Endpoint
-   deleting the previously created NAT Gateway
-   removing the stale NAT `blackhole` route
-   removing unnecessary Warehouse SSH rules
-   removing unnecessary Warehouse HTTPS rules
-   removing temporary EC2 Instance Connect-related access
-   removing the unused public HTTPS Security Group rule because TLS was
    not configured
-   verifying the application after the cleanup

This left the final application path significantly simpler:

``` text
Internet
   |
   v
House :80
   |
   | private VPC traffic :3306
   v
Warehouse
   |
   v
MySQL
```

------------------------------------------------------------------------

## 12. Security Controls

The final implementation demonstrates multiple security layers rather
than relying on a single control.

### Network isolation

The database resides in a private subnet without an active Internet
default route.

### Security Group references

Warehouse accepts MySQL traffic only from the House Security Group.

### Restricted application server

Gunicorn listens only on:

``` text
127.0.0.1:5000
```

and port 5000 is not exposed publicly.

### Reverse proxy

Nginx is the public application entry point rather than exposing the
Flask development server or Gunicorn directly.

### IAM role authentication

House accesses AWS Secrets Manager through an IAM role rather than
static AWS credentials.

### Secrets Manager

Database credentials are retrieved at runtime rather than hardcoded into
the application.

### Parameterized SQL

Application database operations use parameterized SQL queries.

### Repository security review

Git history was checked for:

-   the earlier development database password
-   OpenSSH/private-key material
-   AWS access-key patterns
-   AWS secret-access-key patterns

No matches were found during the final review.

------------------------------------------------------------------------

## 13. Troubleshooting Experience

A major goal of this project was to understand failure paths rather than
only create a working architecture.

Issues investigated during the implementation included:

-   EC2 connectivity and routing
-   Security Group source rules
-   public versus private subnet behaviour
-   NAT Gateway cost and routing
-   stale blackhole routes
-   VPC endpoint connectivity
-   MySQL connectivity across subnets
-   application failures when the database instance was stopped
-   Secrets Manager JSON/key mismatch
-   IAM permissions
-   Gunicorn configuration
-   malformed systemd `ExecStart`
-   Nginx reverse proxy configuration
-   GitHub Actions runner SSH reachability
-   malformed multiline SSH private-key secrets
-   unnecessary infrastructure and Security Group rules

The troubleshooting approach used throughout the project was to follow
the request path layer by layer:

``` text
DNS / address
   |
Routing
   |
Security Group
   |
Listening port
   |
Process/service
   |
Application
   |
Credentials/IAM
   |
Database/dependency
```

------------------------------------------------------------------------

## 14. Technology Stack

  -----------------------------------------------------------------------
  Area                                Technology
  ----------------------------------- -----------------------------------
  Cloud                               AWS

  Networking                          VPC, Subnets, Route Tables,
                                      Internet Gateway, Security Groups

  Compute                             Amazon EC2

  OS                                  Ubuntu 24.04 LTS

  Web Server                          Nginx

  Application Server                  Gunicorn

  Application                         Python, Flask, Jinja

  Database                            MySQL

  DB Client                           PyMySQL

  Secrets                             AWS Secrets Manager

  Identity                            AWS IAM Role

  Monitoring                          Amazon CloudWatch

  Alerting                            Amazon SNS

  CI/CD                               GitHub Actions

  Service Management                  systemd

  Version Control                     Git / GitHub
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 15. Project Structure

``` text
northstar-employee-portal/
├── .github/
│   └── workflows/
│       └── deploy.yml
├── static/
│   └── style.css
├── templates/
│   ├── add.html
│   ├── base.html
│   ├── delete.html
│   ├── edit.html
│   ├── employees.html
│   └── home.html
├── app.py
├── README.md
└── requirements.txt
```

------------------------------------------------------------------------

## 16. Known Limitations and Production Improvements

This repository demonstrates the architecture and operational concepts
in a controlled portfolio environment. It should not be interpreted as a
complete production reference architecture.

### HTTPS

The current application is served over HTTP on port 80.

For production, TLS should be implemented and public application traffic
should use HTTPS on port 443, with HTTP redirected to HTTPS.

A common production evolution would be:

``` text
Internet
   |
   | HTTPS :443
   v
Application Load Balancer
   |
   v
Private application instances
```

### CI/CD SSH exposure

The current GitHub-hosted deployment workflow requires inbound SSH
connectivity to House. For the lab, this resulted in broader SSH network
exposure than would be desirable in production.

A production implementation should avoid broadly exposed administrative
SSH and use a more controlled deployment path, such as a
private/self-hosted runner, AWS-native deployment mechanisms, or another
restricted management channel.

### High availability

Northstar currently uses single application and database EC2 instances.

A production architecture would typically distribute workloads across
multiple Availability Zones and could use:

``` text
Internet
   |
   v
ALB
  / \
 /   \
App  App
AZ-A AZ-B
  \   /
   \ /
 RDS Multi-AZ
```

### Database management

The portfolio implementation intentionally uses MySQL on EC2 to
demonstrate private-subnet connectivity and database administration.

A production workload could use Amazon RDS depending on operational,
availability, backup, scaling, and cost requirements.

### Infrastructure as Code

The current version was built manually to strengthen understanding of
AWS networking and troubleshooting.

A future iteration could reproduce the architecture using Terraform with
reusable modules, remote state, and environment separation.

### Observability

Current monitoring focuses on EC2 CPU utilization and SNS notification.

A production observability design could additionally include:

-   centralized application and Nginx logs
-   memory and disk metrics
-   HTTP latency and error-rate metrics
-   dashboards
-   additional infrastructure alarms
-   application health checks

------------------------------------------------------------------------

## 17. Key Engineering Takeaways

This project reinforced several practical Cloud/DevOps principles:

**A route provides a path; a Security Group decides whether traffic is
allowed.**

**Opening a Security Group port does not create a service. A process
still needs to be listening on that port.**

**A private subnet does not need NAT for communication with another
subnet in the same VPC.**

**Public application traffic and private database traffic should have
different security boundaries.**

**IAM roles are preferable to long-lived AWS access keys for workloads
running on EC2.**

**Secrets should be retrieved securely rather than embedded in
application source code.**

**CI and CD are separate concerns: validate first, deploy only after
validation succeeds.**

**Monitoring turns a running system into an operable system.**

**Removing unused infrastructure is part of engineering, not an
afterthought.**

Most importantly, successful deployment is not the end of the work.
Understanding the complete request path makes troubleshooting much more
systematic:

``` text
User
 -> Network
 -> Security
 -> Web server
 -> Application server
 -> Application
 -> IAM / Secrets
 -> Database
 -> Response
```

------------------------------------------------------------------------

## 18. Disclaimer

This repository is a sanitized portfolio recreation based on a
real-world client implementation.

`Northstar Logistics Pte. Ltd.` and the employee records used in this
repository are fictional/synthetic. Real client names, personal data,
credentials, AWS account identifiers, production IP addresses, and other
identifying information are intentionally excluded.

The repository is intended solely to demonstrate Cloud/DevOps
architecture, implementation, security, deployment, monitoring, and
troubleshooting practices.
