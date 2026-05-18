# HMS — Mini Hospital Management System

A Django-based hospital management web application with doctor availability management, patient appointment booking, Google Calendar integration, and a separate serverless email notification service.

---

## Setup and Run

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | python.org |
| PostgreSQL | 14+ | postgresql.org |
| Node.js | 18+ | nodejs.org |
| npm | 9+ | bundled with Node |

---

### Step 1 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

---

### Step 2 — Create PostgreSQL database

Open your PostgreSQL shell or pgAdmin and run:

```sql
CREATE DATABASE hms_db;
```

If your PostgreSQL user/password differs from the defaults (`postgres`/`postgres`), update the `.env` file in Step 4.

---

### Step 3 — Set up the Django backend

```bash
# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

---

### Step 4 — Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:
- `DB_PASSWORD` — your PostgreSQL password
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — from Google Cloud Console (see Step 6)
- `SMTP_USER` / `SMTP_PASSWORD` — your Gmail address and App Password (see Step 7)

Load environment variables before running Django. On Windows (PowerShell):

```powershell
Get-Content .env | ForEach-Object {
    if ($_ -match "^([^#][^=]+)=(.*)$") {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}
```

On macOS/Linux:

```bash
export $(grep -v '^#' .env | xargs)
```

---

### Step 5 — Run Django migrations and start server

```bash
cd hms
python manage.py migrate
python manage.py createsuperuser   # optional, for admin access
python manage.py runserver
```

Django is now running at **http://localhost:8000**

---

### Step 6 — Set up Google Calendar API (OAuth2)

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or select an existing one)
3. Enable the **Google Calendar API**
4. Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
5. Set Application type to **Web application**
6. Add Authorized redirect URI: `http://localhost:8000/accounts/google/callback/`
7. Copy `Client ID` and `Client Secret` into your `.env` file
8. Go to **OAuth consent screen** → add your Gmail address as a test user

After logging into HMS, click **"Connect Google Calendar"** in the nav bar to authorize. This enables automatic calendar event creation on booking confirmation.

---

### Step 7 — Configure Gmail SMTP for email notifications

1. Enable 2-Step Verification on your Google account
2. Go to **myaccount.google.com → Security → App Passwords**
3. Create an App Password for "Mail"
4. Put your Gmail address in `SMTP_USER` and the App Password in `SMTP_PASSWORD` in `.env`

---

### Step 8 — Set up and run the serverless email service

In a **new terminal window**:

```bash
# Install serverless framework globally
npm install -g serverless

# Install serverless-offline plugin
cd email-service
npm install serverless-offline --save-dev

# Set SMTP environment variables (copy from .env)
# Windows PowerShell:
$env:SMTP_USER="your@gmail.com"
$env:SMTP_PASSWORD="your-app-password"
$env:FROM_EMAIL="your@gmail.com"

# macOS/Linux:
export SMTP_USER="your@gmail.com"
export SMTP_PASSWORD="your-app-password"
export FROM_EMAIL="your@gmail.com"

# Start serverless-offline
serverless offline
```

The email service is now running at **http://localhost:3000**

---

### Running the full system

You need **two terminal windows** running simultaneously:

| Terminal | Command | URL |
|----------|---------|-----|
| 1 — Django | `cd hms && python manage.py runserver` | http://localhost:8000 |
| 2 — Email | `cd email-service && serverless offline` | http://localhost:3000 |

---

### VS Code Setup Tips

1. Open the project folder in VS Code: `File → Open Folder → select hms-project/`
2. Install the **Python** extension (Microsoft)
3. Select the virtual environment: `Ctrl+Shift+P → Python: Select Interpreter → venv`
4. Open two integrated terminals (`Ctrl+` `` ` `` → split terminal icon)
5. Run Django in terminal 1 and the email service in terminal 2

---

## System Architecture

### Component Overview

```
┌─────────────────────────────┐        ┌──────────────────────────────┐
│   Django HMS Backend        │  HTTP  │  Serverless Email Service    │
│   localhost:8000            │ POST ──▶  localhost:3000              │
│                             │        │  (serverless-offline)        │
│  ┌─────────┐ ┌──────────┐  │        │                              │
│  │ Doctor  │ │ Patient  │  │        │  handler.py                  │
│  │  App    │ │  App     │  │        │  - SIGNUP_WELCOME            │
│  └─────────┘ └──────────┘  │        │  - BOOKING_CONFIRMATION      │
│  ┌───────────────────────┐  │        └──────────────────────────────┘
│  │   Appointments App    │  │
│  │  (race-safe booking)  │  │        ┌──────────────────────────────┐
│  └───────────────────────┘  │ OAuth2 │  Google Calendar API         │
│  ┌───────────────────────┐  │ ──────▶│  (calendar.events.insert)   │
│  │  Accounts / Auth App  │  │        └──────────────────────────────┘
│  └───────────────────────┘  │
│                             │        ┌──────────────────────────────┐
│   PostgreSQL Database       │        │  PostgreSQL (local)          │
│   (via Django ORM)          │ ──────▶│  hms_db                     │
└─────────────────────────────┘        └──────────────────────────────┘
```

### Data Model

**User** (custom `AbstractUser`)
- Fields: `email` (login), `username`, `role` (`doctor`|`patient`), `google_access_token`, `google_refresh_token`, `google_token_expiry`

**DoctorProfile** — OneToOne → User
- Fields: `specialty`, `bio`

**AvailabilitySlot** — ForeignKey → DoctorProfile
- Fields: `date`, `start_time`, `end_time`, `is_booked`
- Constraint: `unique_together = ('doctor', 'date', 'start_time')` prevents duplicate slots

**PatientProfile** — OneToOne → User
- Fields: `date_of_birth`, `phone`

**Appointment** — OneToOne → AvailabilitySlot, ForeignKey → PatientProfile
- Fields: `booked_at`, `patient_calendar_event_id`, `doctor_calendar_event_id`
- The `OneToOneField` on slot is the database-level guarantee that a slot can only ever have one appointment

### Role-Based Access

Access control uses a custom decorator pattern (`doctors/decorators.py`):
- `@doctor_required` — wraps any view that only a doctor may access; redirects patients with an error message
- `@patient_required` — wraps any view that only a patient may access; redirects doctors with an error message

All data queries are also scoped by `request.user`: doctors can only read/write their own `DoctorProfile` and its related `AvailabilitySlot` rows. Patients can only read their own `PatientProfile` and related `Appointment` rows.

### Email Service Integration

When a Django view needs to send an email, it calls `accounts/email_service.py`, which makes an HTTP POST to `http://localhost:3000/email/send` (the serverless function running via serverless-offline). The body contains a `trigger` string and a `payload` dict. Email failures are caught and logged — they do not crash the main request.

### Google Calendar Integration

After a user connects their Google account (OAuth2 flow at `/accounts/google/`), tokens are stored on the `User` model. On booking confirmation, `appointments/calendar_service.py` builds credentials, refreshes them if expired, then calls `calendar.events().insert()` for both the doctor's and patient's calendars. Calendar failures are also non-blocking.

---

## The Design Decision

### Problem: Race Condition in Slot Booking

When two patients attempt to book the same slot simultaneously, a naive implementation reads `is_booked=False` for both, then both create an `Appointment`. One booking must win; the other must be rejected cleanly.

**Option A — Application-level check only**

Read `is_booked`, if `False` set it to `True` and create the appointment. Fast to implement, but fails under concurrency: both requests can read `is_booked=False` before either writes, creating a double-booking.

**Option B — Database-level lock with `SELECT FOR UPDATE`**

Wrap the check-and-update in a `transaction.atomic()` block and use `select_for_update()` to acquire a row-level lock on the slot before reading `is_booked`. The first request to reach the lock wins; the second waits, then sees `is_booked=True` and rejects cleanly.

**Why I chose Option B:**

Option A has a real, reproducible failure mode under load. Any two requests that arrive within milliseconds of each other will both pass the check. A hospital booking system where double-bookings silently succeed is not acceptable — it breaks patient trust and creates operational problems.

`SELECT FOR UPDATE` is the correct primitive for this pattern. It pushes the serialisation guarantee down to the database, which is the only component that can actually enforce it. The cost is a brief lock on one row — acceptable for a booking flow where correctness matters more than throughput.

The `OneToOneField` on `Appointment → AvailabilitySlot` serves as a second line of defence at the schema level. Even if a bug bypassed the application lock, the database unique constraint would reject the second insert and surface an `IntegrityError`, which the view catches and converts to a user-facing message.

**The position:** Use the database for what databases are built for. Application-level state checks under concurrency are a known failure pattern. `SELECT FOR UPDATE` + a unique constraint is not over-engineering — it is the minimum correct implementation.

---

## Limitations

### What would break in production

**1. OAuth2 token storage**
Google access tokens are stored in plaintext in the `User` table. In production, tokens must be encrypted at rest (e.g. using `django-fernet-fields` or a secrets manager). A database breach currently exposes all calendar tokens.

**2. Single serverless function process**
`serverless-offline` runs a single Node.js process that invokes the Python handler in-process. Real AWS Lambda runs each invocation in isolation with its own process. Error isolation, cold starts, and concurrency behaviour will differ.

**3. Session-based auth does not scale horizontally**
Django's default session backend stores sessions in the database. Multiple Django instances would share the same DB session store, which works but creates a bottleneck. A production system would use Redis-backed sessions or JWT.

**4. No email queue / retry**
Email failures are swallowed and logged. In production, a failed email send should be retried — via SQS dead-letter queues (on Lambda) or Celery with Redis (on Django). The current implementation silently drops failed notifications.

**5. Google Calendar token refresh is synchronous and in-request**
Token refresh happens during the booking request, adding latency. In production this should be handled as a background task.

**First fix in production:** Encrypt the OAuth2 tokens. A calendar integration that exposes refresh tokens in a plaintext DB column is a serious security vulnerability. Everything else is a scalability or reliability concern; this is a security one.
