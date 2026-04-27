import secrets
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, FRONTEND_URL


def send_reset_email(to_email: str, token: str, base_url: str = "") -> None:
    frontend = base_url or FRONTEND_URL
    reset_url = f"{frontend}/reset-password?token={token}"
    subject = "分组大师 - 重置密码"
    body = f"""您好，

您正在为分组大师账号申请重置密码。请点击以下链接设置新密码（30分钟内有效）：

{reset_url}

如果您没有申请重置密码，请勿理会此邮件。

分组大师团队
"""

    msg = MIMEMultipart()
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


def generate_token() -> str:
    return secrets.token_urlsafe(32)
