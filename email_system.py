import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
# import pandas as pd


def otp_genrater(user_id,subject,email_text):
        #print(email_text)
        sender_email_id = ""
        sender_pwd = ""
        reciver_email_id = user_id
        subject = subject
        otp = random.randint(100000, 999999) #genrate 6 digit otp 
        email_text = (f"{otp} is your One Time Password for Create New Account in Banking Application")
        try:    
            msg = MIMEMultipart()
            msg['From'] = sender_email_id
            msg['To'] = reciver_email_id
            msg['Subject'] = subject
            body = email_text
            msg.attach(MIMEText(body,'plain'))
            s = smtplib.SMTP('smtp.gmail.com', 587)
            s.starttls()
            s.login(sender_email_id, sender_pwd.strip())  
            #logging.info(f"{sender_email_id} - loginSuccessfully")

            s.send_message(msg)
            #logging.info(f"{sender_email_id} - EmailSendSuccessfully")

            print(f"'MessageSent'{otp}")
            return(otp)

        except Exception as e:
            print(e)
            #logging.error(f"{sender_email_id} - Loginfailed: {e}")

def send_email_attachment(email_id, account_number, user_name, pin):
        sender_email_id = "shanirajsinghchouhan@gmail.com"
        sender_pwd = "dzvtoaetrgtvslbu"
        reciver_email_id = email_id
        subject = "Your Account Credentials"
        email_text = f"""
Dear {user_name},
Welcome to Banking Application!
Your account has been successfully created. Please find your login credentials below:
User Name: {user_name}
Account Number: {account_number}
Password: {pin}

Best regards,
MCA Final Year Student
@gmail.com"""
        try:    
            msg = MIMEMultipart()
            msg['From'] = sender_email_id
            msg['To'] = reciver_email_id
            msg['Subject'] = subject
            body = email_text
            msg.attach(MIMEText(body,'plain'))
            s = smtplib.SMTP('smtp.gmail.com', 587)
            s.starttls()
            s.login(sender_email_id, sender_pwd.strip())  
            #logging.info(f"{sender_email_id} - loginSuccessfully")

            s.send_message(msg)
            #logging.info(f"{sender_email_id} - EmailSendSuccessfully")

            print(f"emailSent {account_number}")
            return True

        except Exception as e:
            print(e)
            return
            #logging.error(f"{sender_email_id} - Loginfailed: {e}")

def send_account_statement(user,filepath):
        sender_email_id = "shanirajsinghchouhan@gmail.com"
        sender_pwd = ""
        reciver_email_id = user.email_name
        subject = f"Bank Account Statement"
        email_text = f"""
Dear {user.user_name},
you requsted for your bank account statement, Please find the statement attached with this email.

Best regards,
MCA Final Year Student
@gmail.com"""
        try:    
            msg = MIMEMultipart()
            msg['From'] = sender_email_id
            msg['To'] = reciver_email_id
            msg['Subject'] = subject
            body = email_text
            msg.attach(MIMEText(body,'plain'))

            # fn = filepath
            # with open(fn, 'rb') as f:
            #      attachment = MIMEMultipart(f.read(),_subtype = 'txt')
            #      attachment.add_header('content-Disposition')

            fn = filepath
            # print(fn)
            with open (fn, 'rb') as f:
                attachment = MIMEApplication(f.read(),_subtype ='txt')
                attachment.add_header('Content-Disposition','attachment',filename=os.path.basename(filepath))
                msg.attach(attachment) 

            s = smtplib.SMTP('smtp.gmail.com', 587)
            s.starttls()
            s.login(sender_email_id, sender_pwd.strip())  
            #logging.info(f"{sender_email_id} - loginSuccessfully")

            s.send_message(msg)
            s.quit()
            #logging.info(f"{sender_email_id} - EmailSendSuccessfully")

            print(f"emailSent")
            return True

        except Exception as e:
            print(e)
            return
            #logging.error(f"{sender_email_id} - Loginfailed: {e}")

# send_account_statement('dilip', '/home/dell/Desktop/vs_code_projects/banking_system/test.txt')