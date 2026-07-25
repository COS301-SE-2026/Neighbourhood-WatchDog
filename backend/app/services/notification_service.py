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
SENDER_EMAIL = os.getenv('SMTP_SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SMTP_APP_PASSWORD')
RECIPIENT_EMAIL = os.getenv('SMTP_RECIPIENT_EMAIL')


def build_alert_email(alert_type: str, camera_name: str, location: str,
                      risk_level: str = "HIGH", dashboard_url: str | None = None) -> str:
    timestamp = datetime.datetime.now().strftime("%d %b %Y · %H:%M")
    
    cta_row = ""
    if dashboard_url:
        cta_row = f"""
            <tr>
              <td style="padding-top: 32px;">
                <table role="presentation" cellspacing="0" cellpadding="0">
                  <tr>
                    <td align="center" bgcolor="#10B981">
                      <a href="{dashboard_url}" 
                         style="display: inline-block; padding: 14px 28px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 13px; font-weight: bold; color: #000000; text-decoration: none; letter-spacing: 0.5px; text-transform: uppercase;">
                        Review Footage &rarr;
                      </a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>"""

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WatchDog Alert</title>
</head>
<body style="margin: 0; padding: 0; background-color: #000000; -webkit-font-smoothing: antialiased;">
  
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: #000000; padding: 40px 20px;">
    <tr>
      <td align="center">
        
        <!-- Main Card: Darker, subtle border, sharp edges -->
        <table role="presentation" width="500" cellpadding="0" cellspacing="0" style="background-color: #0a0a0a; border: 1px solid #1f1f1f;">
          
          <!-- Industrial Top Accent -->
          <tr>
            <td style="height: 4px; background-color: #10B981; line-height: 4px; font-size: 4px;">&nbsp;</td>
          </tr>

          <!-- Single Padded Content Area -->
          <tr>
            <td style="padding: 40px;">
              
              <!-- App Header -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 32px;">
                <tr>
                  <td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #ffffff; font-size: 14px; font-weight: 700; letter-spacing: 2px;">
                    <span style="color: #10B981; margin-right: 4px;">&#9632;</span> WATCHDOG
                  </td>
                  <td align="right" style="font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, monospace; color: #555555; font-size: 12px;">
                    {timestamp}
                  </td>
                </tr>
              </table>

              <!-- Alert Headline -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 32px;">
                <tr>
                  <td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
                    <div style="color: #10B981; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 8px;">
                      {risk_level} Priority Alert
                    </div>
                    <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600; line-height: 1.2; letter-spacing: -0.5px;">
                      {alert_type}
                    </h1>
                  </td>
                </tr>
              </table>

              <!-- Divider -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 24px;">
                <tr><td style="border-top: 1px solid #1f1f1f;"></td></tr>
              </table>

              <!-- Clean Data Grid -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <!-- Left Column -->
                  <td width="50%" valign="top" style="padding-right: 20px;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #666666; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; padding-bottom: 4px;">
                          Camera Source
                        </td>
                      </tr>
                      <tr>
                        <td style="font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, monospace; color: #ffffff; font-size: 14px;">
                          {camera_name}
                        </td>
                      </tr>
                    </table>
                  </td>
                  
                  <!-- Right Column -->
                  <td width="50%" valign="top">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #666666; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; padding-bottom: 4px;">
                          Zone Location
                        </td>
                      </tr>
                      <tr>
                        <td style="font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, monospace; color: #ffffff; font-size: 14px;">
                          {location}
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- CTA Row -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                {cta_row}
              </table>

            </td>
          </tr>
          
          <!-- Minimal Footer -->
          <tr>
            <td style="padding: 0 40px 32px 40px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #444444; font-size: 11px; border-top: 1px solid #1f1f1f; padding-top: 24px;">
                    System generated by WatchDog Security Node. Do not reply to this email.
                  </td>
                </tr>
              </table>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

def send_alert_email(alert_type: str, camera_name: str, location: str,
                      risk_level: str = "HIGH", dashboard_url: str | None = None):
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        subject = f"Critical Alert: {alert_type} at {location}"
        plain_body = (
            f"{alert_type} detected at {camera_name} ({location}).\n"
            f"Risk level: {risk_level}\n"
            f"Please review footage and confirm the response."
        )

        msg = MIMEMultipart('alternative')
        msg['From'] = f"Neighbourhood WatchDog <{SENDER_EMAIL}>"
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject

        msg.attach(MIMEText(plain_body, 'plain'))
        msg.attach(MIMEText(build_alert_email(alert_type, camera_name, location, risk_level, dashboard_url), 'html'))

        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        print('Critical alert email sent successfully!')

        server.quit()
    except Exception as e:
        print('Error sending alert email:', e)


def main():

    send_alert_email(
        alert_type="Weapon Detected",
        camera_name="CAM 03",
        location="Front Gate",
        risk_level="HIGH",
        dashboard_url="https://neighbourhoodwatchdog.co.za/alerts",
    )


if __name__ == '__main__':
    main()