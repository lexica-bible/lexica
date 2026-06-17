#!/usr/bin/env python3
"""Tiny provider-agnostic SMTP sender.

Shared by the password-reset flow (views_notes) and the nightly health-check email
(scripts/health_check.py). Deliberately imports nothing from Flask/core so a
standalone script can use it too.

Config comes from environment variables (set in the PythonAnywhere WSGI for the web
app — see CLAUDE.md "Deployment" — or a repo-root .env for the scheduled task):

  SMTP_HOST      e.g. smtp.resend.com
  SMTP_PORT      e.g. 587   (STARTTLS; use 465 for implicit TLS)
  SMTP_USER      e.g. resend            (Resend's SMTP username is literally "resend")
  SMTP_PASS      e.g. the Resend API key (re_...)
  MAIL_FROM      From: header, e.g.  Lexica <noreply@lexica.bible>
  MAIL_REPLY_TO  optional Reply-To

If SMTP_HOST / SMTP_PASS / MAIL_FROM aren't all present, mail_configured() is False
and send_email() is a no-op returning False — so a deploy before the keys are set
never errors; the feature just stays off (same lazy pattern as Google sign-in).
"""
import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formatdate, make_msgid, parseaddr

log = logging.getLogger("bible.mail")


def _cfg():
    return {
        "host": (os.environ.get("SMTP_HOST") or "").strip(),
        "port": int((os.environ.get("SMTP_PORT") or "587").strip() or 587),
        "user": (os.environ.get("SMTP_USER") or "").strip(),
        "pw":   os.environ.get("SMTP_PASS") or "",
        "from": (os.environ.get("MAIL_FROM") or "").strip(),
        "reply_to": (os.environ.get("MAIL_REPLY_TO") or "").strip(),
    }


def mail_configured() -> bool:
    """True only when enough is set to actually send (host + password + From)."""
    c = _cfg()
    return bool(c["host"] and c["pw"] and c["from"])


def send_email(to: str, subject: str, text: str, html: str | None = None) -> bool:
    """Send one email (plain text, optional HTML alternative). Returns True on
    success. NEVER raises — logs and returns False — so a send failure can't turn a
    web request into a 500 or crash the nightly script."""
    c = _cfg()
    if not (c["host"] and c["pw"] and c["from"]):
        log.warning("send_email skipped — SMTP not configured")
        return False
    if not to or not subject:
        return False
    addr = parseaddr(c["from"])[1]
    domain = addr.split("@")[-1] if "@" in addr else None

    msg = EmailMessage()
    msg["From"] = c["from"]
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=domain) if domain else make_msgid()
    if c["reply_to"]:
        msg["Reply-To"] = c["reply_to"]
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")

    try:
        ctx = ssl.create_default_context()
        if c["port"] == 465:
            with smtplib.SMTP_SSL(c["host"], c["port"], timeout=20, context=ctx) as s:
                if c["user"]:
                    s.login(c["user"], c["pw"])
                s.send_message(msg)
        else:
            with smtplib.SMTP(c["host"], c["port"], timeout=20) as s:
                s.starttls(context=ctx)
                if c["user"]:
                    s.login(c["user"], c["pw"])
                s.send_message(msg)
        return True
    except Exception as exc:
        log.warning("send_email failed: %s", exc)
        return False
