---
name: send-outlook-mail
description: Send an email using the locally installed Microsoft Outlook application via PowerShell COM automation. Use this skill whenever the user asks to send an email, send a mail, compose a message, email someone, or any variation of "send" + "mail/email/message". Always use this skill even if the user only provides partial mail details - it will prompt for any missing fields and check environment variables before asking.
---

# Outlook App Send Mail

Sends an email through Microsoft Outlook on this computer. No technical knowledge needed - just provide who to send to, a subject, and your message.

## Before You Start

- Microsoft Outlook must be installed on this computer and you must be signed in.
- That's it!

---

## How It Works

### Step 1 - Collect the email details

Ask the user for the following. Only **To**, **Subject**, and **Body** are required - the rest are optional.

| What           | Required? | What to ask for                                       |
|----------------|-----------|-------------------------------------------------------|
| **To**         | Yes       | Who should receive the email (email address)          |
| **Subject**    | Yes       | What is the email about (subject line)                |
| **Body**       | Yes       | What should the email say                             |
| **Cc**         | No        | Anyone else to copy on the email                      |
| **Bcc**        | No        | Anyone to secretly copy (they won't be visible)       |
| **Attachments**| No        | Any files to attach (just ask for the file path)      |
| **BodyFormat** | No        | How the body is formatted - default is **html**       |
| **SenderAlias**| No        | Send from a different email address (if you have one) |

### Step 2 - Fill in any blanks

Before asking the user, check if any of these are already saved as environment variables:

| Field          | Environment Variable        |
|----------------|-----------------------------|
| To             | `OUTLOOK_MAIL_TO`           |
| Subject        | `OUTLOOK_MAIL_SUBJECT`      |
| Body           | `OUTLOOK_MAIL_BODY`         |
| Cc             | `OUTLOOK_MAIL_CC`           |
| Bcc            | `OUTLOOK_MAIL_BCC`          |
| SenderAlias    | `OUTLOOK_SENDER_ALIAS`      |
| BodyFormat     | `OUTLOOK_MAIL_BODY_FORMAT`  |

If a required field is still missing, ask the user - combine all missing fields into **one single question** to keep it simple.

Example: *"To send your email I just need: who to send it to (To), a Subject, and the message (Body). What are these?"*

Once everything is gathered, give a quick one-line summary and confirm before sending.

### Step 3 - Send the email

Run the script at `scripts/send-outlook-mail.ps1` in a PowerShell terminal like this:

```powershell
.\send-outlook-mail.ps1 `
  -To "recipient@example.com" `
  -Subject "Hello" `
  -Body "<p>Your message here</p>" `
  -Cc "cc@example.com" `
  -Bcc "bcc@example.com" `
  -Attachments "C:\path\to\file.pdf" `
  -BodyFormat "html" `
  -SenderAlias "alias@mycompany.com"
```

> Only include optional fields (Cc, Bcc, Attachments, SenderAlias) if the user provided them.
> Default `BodyFormat` is **html** - only change it if the user specifically asks for plain text.

### Step 4 - Let the user know what happened

- **Success (exit code 0):** Tell the user simply - *"Your email has been sent!"*
- **Error:** Show the error message in plain language and guide the user to fix it (see Troubleshooting below).

---

## Pre-Set Variables (Optional)

If the same details are used often, they can be saved so you don't have to type them every time:

```powershell
# Run these once in PowerShell to save your defaults
$env:OUTLOOK_MAIL_TO             = "recipient@example.com"
$env:OUTLOOK_MAIL_SUBJECT        = "My Default Subject"
$env:OUTLOOK_MAIL_BODY           = "<p>My default message</p>"
$env:OUTLOOK_MAIL_CC             = ""
$env:OUTLOOK_MAIL_BCC            = ""
$env:OUTLOOK_SENDER_ALIAS        = ""
$env:OUTLOOK_MAIL_BODY_FORMAT    = "html"
```

---

## Troubleshooting

| What went wrong | Why it happened | How to fix it |
|-----------------|-----------------|---------------|
| `Cannot create ActiveX object` | Outlook is not installed or not set up properly | Make sure Outlook is installed, then run `outlook.exe /regserver` |
| `Access denied` error | Outlook blocked the script with a security prompt | A pop-up may have appeared in Outlook - click **Allow** |
| `No default mail profile` | You're not signed into Outlook | Open Outlook and sign in first |
| `Send on behalf of` error | You don't have permission to send from that alias | Check with your IT team that the alias is authorised |
| Email stuck in Outbox | Outlook is offline or not syncing | Make sure Outlook is open and connected to the internet |
