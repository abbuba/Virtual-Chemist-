import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_otp_email(receiver_email: str, otp_code: str, username: str) -> bool:
    """
    Connects to the SMTP server and sends a 6-digit OTP code to the user.
    """
    sender_email = os.getenv("SMTP_USER")
    sender_password = os.getenv("SMTP_PASS")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))

    # Fallback for development if email credentials aren't provided
    if not sender_email or not sender_password:
        print(f"\n[DEV MODE] Email bypassed. OTP for {username} is: {otp_code}\n")
        return True

    # Construct the email message
    message = MIMEMultipart("alternative")
    message["Subject"] = "Your Virtual Chemist Login Code"
    message["From"] = sender_email
    message["To"] = receiver_email

    # The body of the email
    text = f"""
    Hello {username},

    Your Virtual Chemist login code is: {otp_code}

    This code will expire in 5 minutes. If you did not request this, please ignore this email.
    """
    message.attach(MIMEText(text, "plain"))

    try:
        # Connect to the server securely
        with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as server:
            server.starttls() # Upgrades the connection to a secure TLS encryption
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print(f"OTP successfully sent to {receiver_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False