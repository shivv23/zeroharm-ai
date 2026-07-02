import json
import logging
import os
import smtplib
import time
from datetime import datetime
from email.message import EmailMessage
from urllib.request import Request, urlopen
from urllib.error import URLError

logger = logging.getLogger("zeroharm-alert")


def _retry(max_attempts=3, delay=1.0, backoff=2.0):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    if attempt < max_attempts - 1:
                        sleep_time = delay * (backoff ** attempt)
                        logger.warning(f"{fn.__name__} failed (attempt {attempt+1}/{max_attempts}): {e}, retrying in {sleep_time:.1f}s")
                        time.sleep(sleep_time)
            logger.error(f"{fn.__name__} failed after {max_attempts} attempts: {last_exc}")
        return wrapper
    return decorator

SEVERITY_EMOJI = {
    "critical": ":rotating_light:",
    "high": ":warning:",
    "warning": ":large_yellow_circle:",
    "info": ":information_source:",
    "normal": ":white_check_mark:",
}

SEVERITY_COLOR = {
    "critical": "#FF0000",
    "high": "#FFA500",
    "warning": "#FFFF00",
    "info": "#1E90FF",
    "normal": "#00FF00",
}

DEFAULT_CONFIG = {
    "slack": {"enabled": False, "webhook_url": ""},
    "email": {"enabled": False, "smtp_server": "", "smtp_port": 587, "smtp_user": "", "smtp_pass": "", "to": ""},
    "sms": {"enabled": False, "twilio_account_sid": "", "twilio_auth_token": "", "twilio_from": "", "to": ""},
    "dispatch_rules": {
        "critical": {"slack": True, "email": True, "sms": True},
        "high": {"slack": True, "email": True, "sms": False},
        "warning": {"slack": True, "email": False, "sms": False},
        "info": {"slack": False, "email": False, "sms": False},
    },
}


class AlertDispatcher:
    def __init__(self, config_path=None):
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
        self.smtp_server = os.getenv("SMTP_SERVER", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_pass = os.getenv("SMTP_PASS", "")
        self.alert_email_to = os.getenv("ALERT_EMAIL_TO", "")
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.twilio_from = os.getenv("TWILIO_FROM", "")
        self.alert_sms_to = os.getenv("ALERT_SMS_TO", "")
        self.dispatch_rules = self._load_rules(config_path)

    def _load_rules(self, config_path):
        config_path = config_path or os.path.join(os.path.dirname(__file__), "config", "alert_channels.json")
        try:
            with open(config_path) as f:
                cfg = json.load(f)
            return cfg.get("dispatch_rules", DEFAULT_CONFIG["dispatch_rules"])
        except Exception:
            return dict(DEFAULT_CONFIG["dispatch_rules"])

    def _active_channels(self, severity):
        rules = self.dispatch_rules.get(severity, {})
        channels = []
        if rules.get("slack") and self.slack_webhook_url:
            channels.append("slack")
        if rules.get("email") and self.smtp_server and self.alert_email_to:
            channels.append("email")
        if rules.get("sms") and self.twilio_account_sid and self.twilio_from and self.alert_sms_to:
            channels.append("sms")
        return channels

    def _format_message(self, alert_data):
        ts = alert_data.get("timestamp", datetime.now().isoformat())
        sev = alert_data.get("severity", "info")
        score = alert_data.get("risk_score", "N/A")
        zone = alert_data.get("zone", "unknown")
        msg = alert_data.get("message", "")
        return (
            f"[ZeroHarm AI Alert] {sev.upper()}\n"
            f"Time: {ts}\n"
            f"Severity: {sev}\n"
            f"Risk Score: {score}\n"
            f"Zone: {zone}\n"
            f"Details: {msg}"
        )

    @_retry(max_attempts=3, delay=1.0, backoff=2.0)
    def send_slack(self, webhook_url, message, severity):
        color = SEVERITY_COLOR.get(severity, "#808080")
        emoji = SEVERITY_EMOJI.get(severity, ":bell:")
        payload = json.dumps({
            "attachments": [{
                "color": color,
                "title": f"{emoji} ZeroHarm AI Alert - {severity.upper()}",
                "text": message,
                "footer": "ZeroHarm AI Safety Platform",
                "ts": datetime.now().timestamp(),
            }]
        }).encode()
        req = Request(webhook_url, data=payload, headers={"Content-Type": "application/json"})
        try:
            urlopen(req, timeout=10)
        except URLError as e:
            logger.error(f"Slack send failed: {e}")

    @_retry(max_attempts=3, delay=1.0, backoff=2.0)
    def send_email(self, smtp_config, to, subject, body):
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = smtp_config.get("smtp_user", "")
        msg["To"] = to
        msg.set_content(body)
        try:
            with smtplib.SMTP(smtp_config.get("smtp_server", ""), smtp_config.get("smtp_port", 587), timeout=15) as server:
                server.starttls()
                server.login(smtp_config.get("smtp_user", ""), smtp_config.get("smtp_pass", ""))
                server.send_message(msg)
        except Exception as e:
            logger.error(f"Email send failed: {e}")

    @_retry(max_attempts=3, delay=1.0, backoff=2.0)
    def send_sms(self, twilio_config, to, message):
        try:
            from twilio.rest import Client
        except ImportError:
            logger.warning("Twilio not installed, skipping SMS")
            return
        sid = twilio_config.get("account_sid", "")
        token = twilio_config.get("auth_token", "")
        twilio_from = twilio_config.get("from", "")
        if not sid or not token or not twilio_from:
            logger.warning("Twilio config incomplete, skipping SMS")
            return
        try:
            client = Client(sid, token)
            client.messages.create(body=message[:1600], from_=twilio_from, to=to)
        except Exception as e:
            logger.error(f"SMS send failed: {e}")

    def dispatch(self, alert_data):
        severity = alert_data.get("severity", "info")
        channels = self._active_channels(severity)
        if not channels:
            return
        formatted = self._format_message(alert_data)
        subject = f"[ZeroHarm AI] {severity.upper()} Alert - Risk Score: {alert_data.get('risk_score', 'N/A')}"
        if "slack" in channels:
            self.send_slack(self.slack_webhook_url, formatted, severity)
        if "email" in channels:
            smtp_cfg = {
                "smtp_server": self.smtp_server,
                "smtp_port": self.smtp_port,
                "smtp_user": self.smtp_user,
                "smtp_pass": self.smtp_pass,
            }
            self.send_email(smtp_cfg, self.alert_email_to, subject, formatted)
        if "sms" in channels:
            twilio_cfg = {
                "account_sid": self.twilio_account_sid,
                "auth_token": self.twilio_auth_token,
                "from": self.twilio_from,
            }
            self.send_sms(twilio_cfg, self.alert_sms_to, formatted)
