"""
SMTP Email Notifier for Kalshi 15-Minute Crypto Prediction Markets.
Dispatches formatted HTML and Plain Text alert emails to danelujapare@gmail.com when streak >= 4.
"""

import os
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

DEFAULT_RECIPIENT = "danelujapare@gmail.com"


class EmailNotifier:
    """SMTP Email Alert Dispatcher."""

    def __init__(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        sender_email: Optional[str] = None,
        default_recipient: str = DEFAULT_RECIPIENT,
    ):
        self.smtp_server = smtp_server or os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(smtp_port or os.getenv("SMTP_PORT", "587"))
        self.smtp_username = smtp_username or os.getenv("SMTP_USERNAME", "")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD", "")
        self.sender_email = sender_email or os.getenv("SENDER_EMAIL") or self.smtp_username
        self.default_recipient = default_recipient or os.getenv("RECIPIENT_EMAIL") or DEFAULT_RECIPIENT

    def is_configured(self) -> bool:
        """Checks if SMTP credentials are fully provided."""
        return bool(self.smtp_server and self.smtp_username and self.smtp_password)

    def send_email(self, subject: str, body_text: str, body_html: str, recipient: Optional[str] = None) -> bool:
        """
        Sends an email using configured SMTP parameters.
        Returns True if successful, False otherwise.
        """
        target_email = recipient or self.default_recipient
        if not target_email:
            print("[Email] Error: No recipient email specified.")
            return False

        if not self.is_configured():
            print(f"[Email] Notice: SMTP credentials not set. Email notification to '{target_email}' logged (dry-run mode).")
            print(f"        Subject: {subject}")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender_email
        msg["To"] = target_email

        part_text = MIMEText(body_text, "plain", "utf-8")
        part_html = MIMEText(body_html, "html", "utf-8")

        msg.attach(part_text)
        msg.attach(part_html)

        try:
            if self.smtp_port == 465:
                # SSL Connection
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=10) as server:
                    server.login(self.smtp_username, self.smtp_password)
                    server.sendmail(self.sender_email, [target_email], msg.as_string())
            else:
                # TLS Connection (Port 587 / 25)
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(self.smtp_username, self.smtp_password)
                    server.sendmail(self.sender_email, [target_email], msg.as_string())

            print(f"[Email] Successfully sent alert email to '{target_email}'.")
            return True
        except Exception as e:
            print(f"[Email] Failed to send email to '{target_email}': {e}")
            return False

    def send_streak_alert(
        self,
        asset: str,
        streak_length: int,
        direction: str,
        ticker: str,
        close_time: str,
        p_reversal: Optional[float] = None,
        recipient: Optional[str] = None,
    ) -> bool:
        """Formulates and dispatches a high-priority streak alert email."""
        dir_upper = direction.upper()
        emoji = "🚀" if direction.lower() == "up" else "🔻"
        bg_color = "#22c55e" if direction.lower() == "up" else "#ef4444"
        text_color = "#ffffff"

        subject = f"{emoji} STREAK ALERT: {asset} hit {streak_length} consecutive {dir_upper} intervals!"

        p_rev_str = f"{p_reversal * 100:.1f}%" if p_reversal is not None else "Elevated (~54-60%)"

        # Plain Text Version
        body_text = (
            f"KALSHI CRYPTO STREAK ALERT\n"
            f"============================\n"
            f"Asset: {asset}\n"
            f"Streak Length: {streak_length} consecutive intervals\n"
            f"Direction: {dir_upper}\n"
            f"Latest Ticker: {ticker}\n"
            f"Interval Close: {close_time}\n"
            f"Conditional Reversal Probability: {p_rev_str}\n\n"
            f"This is an automated 24/7 alert from your Kalshi Crypto Streak Monitor.\n"
        )

        # Rich HTML Version
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
            .card {{ max-width: 600px; margin: 0 auto; background: #1e293b; border-radius: 12px; overflow: hidden; border: 1px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
            .header {{ background-color: {bg_color}; color: {text_color}; padding: 20px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 22px; font-weight: 800; }}
            .content {{ padding: 24px; }}
            .badge {{ display: inline-block; padding: 6px 12px; background: {bg_color}; color: {text_color}; border-radius: 20px; font-weight: bold; font-size: 14px; margin-bottom: 15px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            td {{ padding: 12px; border-bottom: 1px solid #334155; font-size: 14px; }}
            td.label {{ font-weight: bold; color: #94a3b8; width: 40%; }}
            td.value {{ color: #f8fafc; font-family: monospace; font-size: 15px; }}
            .footer {{ background: #0f172a; padding: 15px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #1e293b; }}
          </style>
        </head>
        <body>
          <div class="card">
            <div class="header">
              <h1>{emoji} STREAK ALERT: {asset} ({streak_length} {dir_upper})</h1>
            </div>
            <div class="content">
              <p style="font-size: 16px; margin-top: 0;">
                The Kalshi 15-minute prediction market for <strong>{asset}</strong> has reached a trend streak of <strong>{streak_length} consecutive {dir_upper} intervals</strong>.
              </p>
              <table>
                <tr>
                  <td class="label">Crypto Asset</td>
                  <td class="value"><strong>{asset}</strong></td>
                </tr>
                <tr>
                  <td class="label">Streak Length</td>
                  <td class="value"><span class="badge">{streak_length} Intervals ({dir_upper})</span></td>
                </tr>
                <tr>
                  <td class="label">Direction</td>
                  <td class="value" style="color: {bg_color}; font-weight: bold;">{dir_upper}</td>
                </tr>
                <tr>
                  <td class="label">Market Ticker</td>
                  <td class="value">{ticker}</td>
                </tr>
                <tr>
                  <td class="label">Interval Close</td>
                  <td class="value">{close_time}</td>
                </tr>
                <tr>
                  <td class="label">P(Reversal | Streak={streak_length})</td>
                  <td class="value" style="color: #fbbf24; font-weight: bold;">{p_rev_str}</td>
                </tr>
              </table>
            </div>
            <div class="footer">
              Kalshi 15-Minute Crypto Streak Real-Time Monitor • Sent 24/7 to {recipient or self.default_recipient}
            </div>
          </div>
        </body>
        </html>
        """

        return self.send_email(subject, body_text, body_html, recipient=recipient)

    def send_test_email(self, recipient: Optional[str] = None) -> bool:
        """Dispatches a test verification email."""
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        target = recipient or self.default_recipient
        subject = f"✅ Kalshi Crypto Streak Monitor Test Email ({now_str})"
        body_text = f"This is a test verification email from your 24/7 Kalshi Crypto Streak Monitor for {target}."
        body_html = f"""
        <html>
          <body style="font-family: sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px;">
            <div style="max-width: 500px; margin: 0 auto; background: #1e293b; padding: 20px; border-radius: 8px;">
              <h2 style="color: #22c55e; margin-top: 0;">✅ Test Email Verified</h2>
              <p>Your 24/7 Kalshi Crypto Streak Alert System is active and configured for <strong>{target}</strong>.</p>
              <p style="font-size: 12px; color: #94a3b8;">Sent at {now_str}</p>
            </div>
          </body>
        </html>
        """
        return self.send_email(subject, body_text, body_html, recipient=target)
