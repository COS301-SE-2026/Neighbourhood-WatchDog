import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
import time

import os
import dotenv

dotenv.load_dotenv()


SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = "os.getenv('SMTP_SENDER_EMAIL')"
SENDER_PASSWORD = os.getenv('SMTP_APP_PASSWORD')
RECIPIENT_EMAIL = os.getenv('SMTP_RECIPIENT_EMAIL')




def send_email(subject, body):
    try:
        # Connect to SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        # Compose email message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send email
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        print('Email notification sent successfully!')

        # Close connection
        server.quit()
    except Exception as e:
        print('Error sending email notification:', e)


def main():

    subject = 'Daily Notification'
    body = 'This is your daily notification. Have a great day!'
    send_email(subject, body)


if __name__ == '__main__':
    main()