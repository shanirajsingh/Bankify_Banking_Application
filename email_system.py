import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
import threading

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def send_email(to, subject, body):
    sender_email_id = EMAIL_USER
    sender_pwd = EMAIL_PASS
    try:
        msg = MIMEMultipart()
        msg["From"] = sender_email_id
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        s = smtplib.SMTP("smtp.gmail.com", 587)
        s.starttls()
        s.login(sender_email_id, sender_pwd.strip())
        s.send_message(msg)
        s.quit()
        print(f"Email sent to {to}")
        return True
    except Exception as e:
        print("Email sending failed:", e)
        return False

def send_async_email(to, subject, body):
    """Send email in a background thread"""
    threading.Thread(target=send_email, args=(to, subject, body)).start()

def otp_genrater(user_id, subject, email_text):
    otp = random.randint(100000, 999999)
    body = f"{otp} {email_text}"
    send_async_email(user_id, subject, body)
    print(f"OTP sent to {user_id}: {otp}")
    return otp

def send_email_attachment(email_id, account_number, user_name, pin):
    subject = "Your Account Credentials"
    email_text = f"""
Dear {user_name},
Welcome to Bankify Application!
Your account has been successfully created. Please find your login credentials below:
User Name: {user_name}
Account Number: {account_number}
Password: {pin}

Best regards,
Bankify App Team
"""
    return send_async_email(email_id, subject, email_text)

def send_account_statement(user, filepath):
    subject = "Bank Account Statement"
    email_text = f"""
Dear {user.user_name},
You requested for your bank account statement. Please find the statement attached.

Best regards,
Bankify App Team
"""
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = user.email_name
        msg["Subject"] = subject
        msg.attach(MIMEText(email_text, "plain"))

        with open(filepath, "rb") as f:
            attachment = MIMEApplication(f.read(), _subtype="txt")
            attachment.add_header("Content-Disposition", "attachment",
                                   filename=os.path.basename(filepath))
            msg.attach(attachment)

        s = smtplib.SMTP("smtp.gmail.com", 587)
        s.starttls()
        s.login(EMAIL_USER, EMAIL_PASS.strip())
        s.send_message(msg)
        s.quit()
        print("Statement sent")
        return True
    except Exception as e:
        print("Email sending failed:", e)
        return False
