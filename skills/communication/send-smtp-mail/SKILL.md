---
name: send-smtp-mail
description: Send an email directly via an SMTP server using Python (no Outlook required). Use this skill whenever the user asks to send an email via SMTP, send mail using an SMTP server, send email with Gmail/Outlook.com/Office365/custom SMTP, send mail without Outlook, or any variation of "send" + "mail/email" + any SMTP-related context. Always use this skill even if the user only provides partial details - it will prompt for any missing fields and check environment variables before asking.
---

# SMTP Send Mail

Sends an email directly through any SMTP server (Gmail, Outlook.com, Office 365, or your own mail server) using Python's built-in `smtplib`. No Outlook installation and no third-party packages required — only Python 3.6+ needed.

## Before You Start

- Python 3.6 or later must be installed (`python --version` to check).
- You need an SMTP server address, port, and valid credentials.
- For **Gmail**: enable "App Passwords" (requires 2FA) and use `smtp.gmail.com:587`.
- For **Outlook.com / Hotmail**: use `smtp.office365.com:587`.
- For **Office 365 (work)**: use `smtp.office365.com:587` with your work credentials.
- That's it — no `pip install` needed!

---

## How It Works

### Step 1 - Collect the email & server details

Ask the user for the following. **SmtpServer**, **SmtpPort**, **Username**, **Password**, **From**, **To**, **Subject**, and **Body** are required - the rest are optional.

| What              | Required? | What to ask for                                                   |
|-------------------|-----------|-------------------------------------------------------------------|
| **SmtpServer**    | Yes       | SMTP server hostname (e.g. `smtp.gmail.com`)                      |
| **SmtpPort**      | Yes       | SMTP port (usually `587` for TLS, `465` for SSL, `25` unencrypted)|
| **Username**      | Yes       | Login username for the SMTP server (usually your email address)   |
| **Password**      | Yes       | SMTP password or app password                                     |
| **From**          | Yes       | Sender email address                                              |
| **To**            | Yes       | Recipient email address(es) — separate multiple with `;`          |
| **Subject**       | Yes       | Subject line                                                      |
| **Body**          | Yes       | Email body content                                                |
| **Cc**            | No        | CC recipient(s) — separate multiple with `;`                      |
| **Bcc**           | No        | BCC recipient(s) — separate multiple with `;`                     |
| **Attachments**   | No        | File path(s) to attach — separate multiple with `,`               |
| **BodyFormat**    | No        | `html` (default) or `plain`                                       |
| **UseSsl**        | No        | `true` (default) or `false` — whether to use TLS/SSL              |

### Step 2 - Fill in any blanks

Before asking the user, check if any of these are already saved as environment variables:

| Field          | Environment Variable          |
|----------------|-------------------------------|
| SmtpServer     | `SMTP_SERVER`                 |
| SmtpPort       | `SMTP_PORT`                   |
| Username       | `SMTP_USERNAME`               |
| Password       | `SMTP_PASSWORD`               |
| From           | `SMTP_FROM`                   |
| To             | `SMTP_MAIL_TO`                |
| Subject        | `SMTP_MAIL_SUBJECT`           |
| Body           | `SMTP_MAIL_BODY`              |
| Cc             | `SMTP_MAIL_CC`                |
| Bcc            | `SMTP_MAIL_BCC`               |
| BodyFormat     | `SMTP_MAIL_BODY_FORMAT`       |
| UseSsl         | `SMTP_USE_SSL`                |

If required fields are still missing after checking env vars, ask the user — combine all missing fields into **one single question**.

Example: *"To send via SMTP I need: the SMTP server, port, your username & password, the From address, To, Subject, and Body. What are these?"*

Once everything is gathered, give a quick one-line summary (omitting the password) and confirm before sending.

Example: *"Sending via smtp.gmail.com:587 (TLS) from alice@gmail.com to bob@example.com — 'Hello there'. Go ahead?"*

### Step 3 - Send the email

Run the script at `scripts/send-smtp-mail.py` in a terminal like this:

```bash
python send-smtp-mail.py \
  --smtp-server smtp.gmail.com \
  --smtp-port 587 \
  --username you@gmail.com \
  --password your-app-password \
  --from-addr you@gmail.com \
  --to recipient@example.com \
  --subject "Hello" \
  --body "<p>Your message here</p>" \
  --cc cc@example.com \
  --bcc bcc@example.com \
  --attachments "C:/path/to/file.pdf" \
  --body-format html \
  --use-ssl true
```

> Only include optional flags (`--cc`, `--bcc`, `--attachments`) if the user provided them.
> Default `--body-format` is **html**. Default `--use-ssl` is **true**.

### Step 4 - Report the result

- **Success (exit code 0):** Tell the user simply — *"Your email has been sent!"*
- **Error:** Show the error in plain language and guide the user with the Troubleshooting table below.

---

## Pre-Set Variables (Optional)

Save your SMTP defaults so you don't have to re-enter them every time.

**Windows (PowerShell):**
```powershell
$env:SMTP_SERVER           = "smtp.gmail.com"
$env:SMTP_PORT             = "587"
$env:SMTP_USERNAME         = "you@gmail.com"
$env:SMTP_PASSWORD         = "your-app-password"
$env:SMTP_FROM             = "you@gmail.com"
$env:SMTP_MAIL_TO          = "recipient@example.com"
$env:SMTP_MAIL_BODY_FORMAT = "html"
$env:SMTP_USE_SSL          = "true"
```

**macOS / Linux (bash/zsh):**
```bash
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="you@gmail.com"
export SMTP_PASSWORD="your-app-password"
export SMTP_FROM="you@gmail.com"
export SMTP_MAIL_TO="recipient@example.com"
export SMTP_MAIL_BODY_FORMAT="html"
export SMTP_USE_SSL="true"
```

---

## Common SMTP Server Settings

| Provider            | Server                    | Port  | Notes                                      |
|---------------------|---------------------------|-------|--------------------------------------------|
| Gmail               | `smtp.gmail.com`          | 587   | Requires an App Password (not your login)  |
| Outlook.com/Hotmail | `smtp.office365.com`      | 587   | Use your full Microsoft account email      |
| Office 365 (work)   | `smtp.office365.com`      | 587   | Use your work email + password             |
| Yahoo               | `smtp.mail.yahoo.com`     | 587   | Requires an App Password                   |
| Amazon SES          | `email-smtp.<region>.amazonaws.com` | 587 | Use SES SMTP credentials           |
| Custom / local      | Your server address       | 25/587| Depends on your mail server config         |

---

## Troubleshooting

| What went wrong                              | Why it happened                                          | How to fix it                                                          |
|----------------------------------------------|----------------------------------------------------------|------------------------------------------------------------------------|
| `Authentication failed`                      | Wrong username or password                               | Double-check credentials; use an App Password for Gmail/Yahoo          |
| `The SMTP server requires a secure connection` | Port/SSL mismatch                                       | Try port 587 with `UseSsl true`, or port 465 with SSL                  |
| `Connection timed out`                        | Wrong server address or port blocked by firewall        | Verify server/port; contact IT if on a corporate network               |
| `Mailbox unavailable` / `550`                 | "From" address not authorised for this SMTP account     | Make sure `-From` matches your authenticated account                   |
| `Certificate validation failed`               | SSL cert issue on custom servers                        | Ensure your server has a valid cert, or check with your mail admin     |
| Email not received                            | Delivered to spam or delayed                            | Check the recipient's spam folder; wait a few minutes and retry        |
