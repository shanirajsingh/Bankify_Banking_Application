import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os


EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def otp_genrater(user_id, subject, email_text):
    sender_email_id = EMAIL_USER
    sender_pwd = EMAIL_PASS   # Gmail App Password
    reciver_email_id = user_id

    otp = random.randint(100000, 999999)
    body = f"{otp} {email_text}"

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email_id
        msg['To'] = reciver_email_id
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login(sender_email_id, sender_pwd.strip())
        s.send_message(msg)
        s.quit()

        print(f"OTP sent to {reciver_email_id}: {otp}")
        return otp
    except Exception as e:
        print("Email sending failed:", e)
        return None

def send_email_attachment(email_id, account_number, user_name, pin):
    sender_email_id = EMAIL_USER  # Change
    sender_pwd = EMAIL_PASS        # Change
    reciver_email_id = email_id
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
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email_id
        msg['To'] = reciver_email_id
        msg['Subject'] = subject
        msg.attach(MIMEText(email_text, 'plain'))
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login(sender_email_id, sender_pwd.strip())
        s.send_message(msg)
        print(f"emailSent {account_number}")
        return True
    except Exception as e:
        print(e)
        return

def send_account_statement(user, filepath):
    sender_email_id = EMAIL_USER  # Change
    sender_pwd = EMAIL_PASS                         # Change
    reciver_email_id = user.email_name
    subject = f"Bank Account Statement"
    email_text = f"""
Dear {user.user_name},
You requested for your bank account statement. Please find the statement attached.

Best regards,
Bankify App Team
"""
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email_id
        msg['To'] = reciver_email_id
        msg['Subject'] = subject
        msg.attach(MIMEText(email_text, 'plain'))

        with open(filepath, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype='txt')
            attachment.add_header('Content-Disposition', 'attachment',
                                   filename=os.path.basename(filepath))
            msg.attach(attachment)

        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login(sender_email_id, sender_pwd.strip())
        s.send_message(msg)
        s.quit()
        print(f"emailSent")
        return True
    except Exception as e:
        print(e)
        return
