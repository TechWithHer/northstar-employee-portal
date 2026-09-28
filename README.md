# Rabbit World — What We Built & Why | Complete Documentation

### 1. Created the VPC

**`Rabbit World`**

```text
CIDR: 10.0.0.0/18
```

This is our isolated AWS network where the application and database will live.

---

### 2. Created two subnets

| Subnet      | CIDR           | Purpose              |
| ----------- | -------------- | -------------------- |
| `Locality1` | `10.0.0.0/19`  | Public / application |
| `Locality2` | `10.0.32.0/19` | Private / database   |

We don't want the database directly exposed to the internet. So two subnets within one VPC. Availability zones will be the same

---

### 3. Created Internet Gateway

**`WorldConnection`**

Attached to `Rabbit World`.

**Why:** Provides a path between the VPC and the public internet.

---

### 4. Created public route table

**`SecurityGuard1`**

Routes:

```text
10.0.0.0/18 → local
0.0.0.0/0   → WorldConnection
```

Associated with:

**`Locality1`**

**Why:** This makes `Locality1` a **public subnet** from a routing perspective.

---

### 5. Created private route table

**`SecurityGuard2`**

Initially:

```text
10.0.0.0/18 → local
```

Later:

```text
0.0.0.0/0 → SecretStreet
```

Associated with:

**`Locality2`**

**Why:** The local route allows communication inside the VPC.

The NAT route allows private resources to **initiate outbound internet traffic** without becoming publicly reachable.

---

# Security Groups

### 6. `Entry_rules_1` — House (EC2 Instance in Public Subnet)

Inbound:

```text
SSH   22  → your IP
HTTP  80  → 0.0.0.0/0
HTTPS 443 → 0.0.0.0/0
```

**Why:** House is our public-facing application server.

---

### 7. `Entry_rules_2` — Warehouse

Inbound:

```text
MySQL 3306 → Entry_rules_1
```

**Why:** We deliberately said:

> Only the application server should be able to talk to the database.

Not:

```text
0.0.0.0/0 → 3306
```

That's an important security design decision.

---

# EC2

### 8. Created `House`

Public EC2 in:

```text
Locality1
```

Private IP:

```text
10.0.13.249
```

Public IP:

```text
13.206.186.228
```

**Why:** This represents our application server.

You successfully SSH'd into it.

**What that proved:**

```text
Internet
   ↓
IGW
   ↓
SecurityGuard1
   ↓
Locality1
   ↓
House
```

was working.

---

### 9. Created `Warehouse`

Private EC2 in:

```text
Locality2
```

Private IP:

```text
10.0.55.176
```

**No public IP.**

**Why:** This represents our database server.

We intentionally don't expose it directly to the internet.

---

# The NAT Problem

### 10. SSM initially didn't work

Warehouse was private and initially had **no internet route**.

SSM couldn't communicate with AWS Systems Manager.

We created:

**`SecretStreet` — NAT Gateway**

in the public subnet.

Then:

```text
SecurityGuard2

0.0.0.0/0
      ↓
SecretStreet
      ↓
WorldConnection
      ↓
Internet
```

**What helped:** Adding the NAT route.

After that, **SSM connected successfully.** 🎉

---

### 11. We proved NAT was actually working

From Warehouse:

```bash
curl https://checkip.amazonaws.com
```

returned:

```text
13.232.133.242
```

That's the NAT Gateway's public IP.

**This was an excellent test.**

It proved:

```text
Warehouse
   ↓
NAT Gateway
   ↓
Internet
```

was working.

And the outside world sees the **NAT IP**, not Warehouse's private IP.

---

# MySQL

### 12. Installed MySQL on Warehouse

```bash
sudo apt update
sudo apt install mysql-server -y
```

Then checked:

```bash
sudo systemctl status mysql
```

Result:

```text
active (running)
```

So MySQL was running.

---

### 13. Found our first MySQL networking issue

We ran:

```bash
sudo ss -lntp | grep 3306
```

Initially:

```text
127.0.0.1:3306
```

That meant:

> MySQL accepts connections only from Warehouse itself.

Even though AWS networking was allowing traffic, MySQL itself was refusing network connections.

---

### 14. Fixed MySQL listening address

Changed:

```text
bind-address = 127.0.0.1
```

to:

```text
bind-address = 0.0.0.0
```

Restarted MySQL.

Then:

```bash
sudo ss -lntp | grep 3306
```

showed:

```text
0.0.0.0:3306
```

**What this proved:**

MySQL is now willing to accept connections arriving through the network interface.

---

# The Most Important Test

### 15. Tested House → Warehouse

From House:

```bash
nc -zv 10.0.55.176 3306
```

Result:

**Succeeded.** ✅

This is a big milestone.

It proved:

```text
House
 ↓
SecurityGuard1
 ↓
VPC local routing
 ↓
Entry_rules_2
 ↓
Warehouse
 ↓
MySQL :3306
```

is working.

So at this point **our VPC networking is fundamentally working.**

---

# Actual MySQL Login Error

### 16. Installed MySQL client on House

The first installation failed with:

```text
404 Not Found
```

because the Ubuntu package index was stale.

We ran:

```bash
sudo apt update
```

Then installed the client successfully.

---

### 17. Tried actual MySQL login

From House:

```bash
mysql -h 10.0.55.176 -u root -p
```

Got:

```text
ERROR 1130 (HY000):
Host '10.0.13.249' is not allowed to connect
```

This was **another useful distinction**.

It means:

> House successfully reached MySQL, but MySQL rejected the `root` account from House.

So:

**Network connectivity = working**

**MySQL authentication/authorization = not configured yet**

We haven't fixed this part yet.

---

# Then SSM Started Acting Up Again

### 18. SSM later became `Connection lost`

Fleet Manager showed:

```text
Warehouse
Running
Connection lost
```

And SSM Agent reported errors involving:

```text
unable to acquire credentials
AccessDeniedException
RequestManagedInstanceRoleToken
```

We checked:

* Warehouse has `Warehouse-SSM-Role` ✅
* Role has `AmazonSSMManagedInstanceCore` ✅
* Role is attached to Warehouse ✅
* `SecurityGuard2` associated with Locality2 ✅
* `0.0.0.0/0 → NAT` exists ✅
* NAT Gateway is `Available` ✅

So **we have not yet established the exact cause of the SSM outage.**

---

# Our Troubleshooting Detour

Because we didn't want to sit around waiting for SSM, we created:

**`my-rabbit-endpoint`**

an **EC2 Instance Connect Endpoint**.

**Why?**

It gives us another way to reach the private `Warehouse` without giving Warehouse a public IP.

We put it in:

```text
Locality2
```

Then AWS told us:

> Warehouse's SG doesn't allow TCP/22 from the EICE.

So we added:

```text
SSH 22
Source: EICE security group
```

to `Entry_rules_2`.

That's correct because we **didn't** open SSH to the whole internet.

The endpoint itself shows:

**Available** ✅

But the connection was taking too long, so **we paused rather than continuing to randomly change things.**

---

# Where We Are NOW

Your architecture currently looks like:

```text
                         INTERNET
                             │
                             ▼
                     WorldConnection
                       Internet GW
                             │
                    SecurityGuard1
                             │
                       Locality1
                       PUBLIC SUBNET
                             │
                       ┌─────┴─────┐
                       │           │
                     House      SecretStreet
                  10.0.13.249   NAT Gateway
                       │           │
                       │           │
                       │       Internet
                       │
                       │ TCP 3306
                       ▼
                    Local VPC
                       │
                  SecurityGuard2
                       │
                    Locality2
                  PRIVATE SUBNET
                       │
                  Warehouse
                  10.0.55.176
                       │
                     MySQL
                     :3306
```

And separately:

```text
Your computer
      │
      ▼
my-rabbit-endpoint
      │
      ▼
Warehouse
```

---

## The key lessons you've actually demonstrated

You now have hands-on evidence for these concepts:

**Route table** → decides the path.

**Security Group** → allows/blocks the traffic.

**IGW** → public internet path for the VPC.

**NAT Gateway** → private resource's outbound internet path.

**Private subnet** → doesn't mean "no internet"; it means no direct inbound internet path.

**SSM** → management access without exposing SSH publicly.

**MySQL bind address** → application-level networking can still block traffic even when AWS networking is correct.

**MySQL user/host permissions** → reaching port 3306 does not mean you're authorized to log in.

And that last distinction is exactly where we stopped.

### So when we resume:

**We should NOT rebuild the VPC.**

**We should NOT touch the NAT.**

**We should NOT randomly change IAM.**

Our next logical task is:

> **Fix the MySQL `root` host authorization / create a proper application DB user, then test a real database login from House.**

After that, we'll return to the SSM issue and diagnose it properly rather than chasing it in circles.
