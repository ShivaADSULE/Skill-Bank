#!/usr/bin/env python3
"""
send-smtp-mail.py
-----------------
Sends an email via any SMTP server (Gmail, Outlook.com, Office 365,
Amazon SES, or a custom server) using Python's built-in smtplib.
No third-party packages required.

All arguments are optional on the command line. Missing required values
are resolved in priority order:
    1. CLI argument
    2. Environment variable (SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, ...)
    3. Interactive prompt (password is prompted securely)

Usage:
    python send-smtp-mail.py \\
        --smtp-server smtp.gmail.com \\
        --smtp-port 587 \\
        --username you@gmail.com \\
        --password your-app-password \\
        --from-addr you@gmail.com \\
        --to recipient@example.com \\
        --subject "Hello" \\
        --body "<p>Hi there!</p>" \\
        [--cc cc@example.com] \\
        [--bcc bcc@example.com] \\
        [--attachments /path/to/file.pdf] \\
        [--body-format html] \\
        [--use-ssl true]
"""

import argparse
import getpass
import mimetypes
import os
import smtplib
import ssl
import sys
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


# ---------------------------------------------------------------------------
# Helper: resolve a value from CLI arg -> env var -> interactive prompt
# ---------------------------------------------------------------------------
def resolve_param(value, env_var, prompt_label, required=True, default="", is_secret=False):
    if value:
        return value

    env_val = os.environ.get(env_var, "").strip()
    if env_val:
        print(f"  [env] {prompt_label} loaded from ${env_var}", flush=True)
        return env_val

    if not required:
        return default

    hint = f" [{default}]" if default else ""
    if is_secret:
        val = getpass.getpass(f"  Enter {prompt_label}{hint}: ")
    else:
        val = input(f"  Enter {prompt_label}{hint}: ").strip()

    if not val:
        if default:
            return default
        print(f"Error: Required field '{prompt_label}' was not provided.", file=sys.stderr)
        sys.exit(1)

    return val


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Send an email via SMTP (Python, no third-party packages).",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--smtp-server",  default="", help="SMTP server hostname")
    parser.add_argument("--smtp-port",    default="", help="SMTP port (default: 587)")
    parser.add_argument("--username",     default="", help="SMTP login username")
    parser.add_argument("--password",     default="", help="SMTP password / app password")
    parser.add_argument("--from-addr",    default="", help="Sender email address")
    parser.add_argument("--to",           default="", help="Recipient(s), semicolon-separated")
    parser.add_argument("--subject",      default="", help="Email subject line")
    parser.add_argument("--body",         default="", help="Email body (plain text or HTML)")
    parser.add_argument("--cc",           default="", help="CC recipient(s), semicolon-separated")
    parser.add_argument("--bcc",          default="", help="BCC recipient(s), semicolon-separated")
    parser.add_argument("--attachments",  default="", help="Attachment path(s), comma-separated")
    parser.add_argument("--body-format",  default="", help="'html' (default) or 'plain'")
    parser.add_argument("--use-ssl",      default="", help="'true' (default) or 'false'")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Build list of addresses from a semi-colon separated string
# ---------------------------------------------------------------------------
def split_addresses(value):
    return [a.strip() for a in value.split(";") if a.strip()]


# ---------------------------------------------------------------------------
# Attach a file to a MIMEMultipart message
# ---------------------------------------------------------------------------
def attach_file(msg, file_path):
    path = Path(file_path)
    if not path.exists():
        print(f"Error: Attachment not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type:
        main_type, sub_type = mime_type.split("/", 1)
    else:
        main_type, sub_type = "application", "octet-stream"

    with open(path, "rb") as f:
        part = MIMEBase(main_type, sub_type)
        part.set_payload(f.read())

    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment", filename=path.name)
    msg.attach(part)
    print(f"  Attached : {file_path}", flush=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print()
    print("=== SMTP Send Mail ===")

    args = parse_args()

    # Resolve all parameters
    smtp_server  = resolve_param(args.smtp_server, "SMTP_SERVER",           "SMTP server (e.g. smtp.gmail.com)")
    smtp_port    = resolve_param(args.smtp_port,   "SMTP_PORT",             "SMTP port",                          default="587")
    username     = resolve_param(args.username,    "SMTP_USERNAME",         "SMTP username (your email)")
    password     = resolve_param(args.password,    "SMTP_PASSWORD",         "SMTP password / app password",       is_secret=True)
    from_addr    = resolve_param(args.from_addr,   "SMTP_FROM",             "From address")
    to_raw       = resolve_param(args.to,          "SMTP_MAIL_TO",          "To address(es)")
    subject      = resolve_param(args.subject,     "SMTP_MAIL_SUBJECT",     "Subject")
    body         = resolve_param(args.body,        "SMTP_MAIL_BODY",        "Body")
    cc_raw       = resolve_param(args.cc,          "SMTP_MAIL_CC",          "Cc (optional)",         required=False)
    bcc_raw      = resolve_param(args.bcc,         "SMTP_MAIL_BCC",         "Bcc (optional)",        required=False)
    attachments  = resolve_param(args.attachments, "SMTP_MAIL_ATTACHMENTS", "Attachments (optional)", required=False)
    body_format  = resolve_param(args.body_format, "SMTP_MAIL_BODY_FORMAT", "Body format (html/plain)", default="html", required=False)
    use_ssl_str  = resolve_param(args.use_ssl,     "SMTP_USE_SSL",          "Use SSL/TLS (true/false)",  default="true", required=False)

    # Normalise
    port          = int(smtp_port)
    is_html       = body_format.strip().lower() != "plain"
    use_ssl       = use_ssl_str.strip().lower() != "false"
    to_list       = split_addresses(to_raw)
    cc_list       = split_addresses(cc_raw)
    bcc_list      = split_addresses(bcc_raw)
    all_recipients = to_list + cc_list + bcc_list

    # Summary
    print()
    print(f"  Server  : {smtp_server}:{port}  (SSL={use_ssl})")
    print(f"  From    : {from_addr}")
    print(f"  To      : {to_raw}")
    if cc_raw:  print(f"  Cc      : {cc_raw}")
    if bcc_raw: print(f"  Bcc     : {bcc_raw}")
    print(f"  Subject : {subject}")
    print(f"  Format  : {'html' if is_html else 'plain'}")
    print()

    # ---------------------------------------------------------------------------
    # Build the MIME message
    # ---------------------------------------------------------------------------
    subtype = "html" if is_html else "plain"

    if attachments.strip():
        msg = MIMEMultipart()
        msg.attach(MIMEText(body, subtype, "utf-8"))
    else:
        # Simpler single-part message when there are no attachments
        msg = MIMEMultipart()
        msg.attach(MIMEText(body, subtype, "utf-8"))

    msg["From"]    = from_addr
    msg["To"]      = "; ".join(to_list)
    msg["Subject"] = subject
    if cc_list:
        msg["Cc"]  = "; ".join(cc_list)

    # Attachments
    if attachments.strip():
        for file_path in attachments.split(","):
            fp = file_path.strip()
            if fp:
                attach_file(msg, fp)

    # ---------------------------------------------------------------------------
    # Send via SMTP
    # ---------------------------------------------------------------------------
    print("Sending email...", flush=True)

    try:
        if use_ssl:
            # STARTTLS (port 587) or implicit SSL (port 465)
            if port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(smtp_server, port, context=context, timeout=30) as server:
                    server.login(username, password)
                    server.sendmail(from_addr, all_recipients, msg.as_string())
            else:
                context = ssl.create_default_context()
                with smtplib.SMTP(smtp_server, port, timeout=30) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.ehlo()
                    server.login(username, password)
                    server.sendmail(from_addr, all_recipients, msg.as_string())
        else:
            # No encryption
            with smtplib.SMTP(smtp_server, port, timeout=30) as server:
                server.ehlo()
                server.login(username, password)
                server.sendmail(from_addr, all_recipients, msg.as_string())

    except smtplib.SMTPAuthenticationError:
        print("\nError: Authentication failed. Check your username and password.", file=sys.stderr)
        print("Tip: For Gmail/Yahoo, use an App Password, not your account password.", file=sys.stderr)
        sys.exit(1)
    except smtplib.SMTPConnectError as e:
        print(f"\nError: Could not connect to {smtp_server}:{port} — {e}", file=sys.stderr)
        sys.exit(1)
    except smtplib.SMTPException as e:
        print(f"\nSMTP error: {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"\nNetwork error: {e}", file=sys.stderr)
        sys.exit(1)

    print()
    print("Email sent successfully!")
    sys.exit(0)


if __name__ == "__main__":
    main()
