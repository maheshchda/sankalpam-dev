"""
Email service for sending verification emails and notifications
Supports SMTP (Gmail, Outlook, custom SMTP servers)
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.config import settings

def send_verification_email(to_email: str, verification_token: str) -> bool:
    """
    Send email verification token to user.
    
    Args:
        to_email: Recipient email address
        verification_token: Verification token to include in email
    
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Get SMTP settings from environment or config
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        email_from = os.getenv("EMAIL_FROM", settings.email_from)
        
        # If no SMTP credentials configured, use development mode (console output)
        if not smtp_user or not smtp_password:
            print(f"\n{'='*60}")
            print(f"DEVELOPMENT MODE - Email Verification")
            print(f"To: {to_email}")
            print(f"Verification Token: {verification_token}")
            print(f"Verification URL: http://localhost:3000/verify?token={verification_token}&type=email")
            print(f"{'='*60}\n")
            return True
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Verify Your Sankalpam Account Email"
        msg['From'] = email_from
        msg['To'] = to_email
        
        # Create email body
        verification_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/verify?token={verification_token}&type=email"
        
        text_content = f"""
Hello,

Please verify your email address for your Sankalpam account.

Your verification token is: {verification_token}

Or click this link to verify: {verification_url}

This token will expire in 7 days.

If you did not create an account, please ignore this email.

Best regards,
Sankalpam Team
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f59e0b; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 5px 5px; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #f59e0b; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .token {{ background-color: #e5e7eb; padding: 10px; border-radius: 5px; font-family: monospace; word-break: break-all; }}
        .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Verify Your Email</h1>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p>Please verify your email address for your Sankalpam account.</p>
            
            <p>Your verification token is:</p>
            <div class="token">{verification_token}</div>
            
            <p style="text-align: center;">
                <a href="{verification_url}" class="button">Verify Email</a>
            </p>
            
            <p><strong>This token will expire in 7 days.</strong></p>
            
            <p>If you did not create an account, please ignore this email.</p>
            
            <div class="footer">
                <p>Best regards,<br>Sankalpam Team</p>
            </div>
        </div>
    </div>
</body>
</html>
"""
        
        # Attach both plain text and HTML versions
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email via SMTP
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        print(f"✅ Verification email sent to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending verification email to {to_email}: {e}")
        # In development, still return True and print to console
        if settings.secret_key == "your-secret-key-change-in-production":
            print(f"\n{'='*60}")
            print(f"DEVELOPMENT MODE - Email Verification (SMTP failed)")
            print(f"To: {to_email}")
            print(f"Verification Token: {verification_token}")
            print(f"Verification URL: http://localhost:3000/verify?token={verification_token}&type=email")
            print(f"{'='*60}\n")
            return True
        return False

def send_password_reset_email(to_email: str, reset_token: str) -> bool:
    """
    Send password reset token to user.
    
    Args:
        to_email: Recipient email address
        reset_token: Password reset token
    
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Get SMTP settings from environment or config
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        email_from = os.getenv("EMAIL_FROM", settings.email_from)
        
        # If no SMTP credentials configured, use development mode
        if not smtp_user or not smtp_password:
            print(f"\n{'='*60}")
            print(f"DEVELOPMENT MODE - Password Reset")
            print(f"To: {to_email}")
            print(f"Reset Token: {reset_token}")
            print(f"{'='*60}\n")
            return True
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Reset Your Sankalpam Password"
        msg['From'] = email_from
        msg['To'] = to_email
        
        reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
        
        text_content = f"""
Hello,

You requested to reset your password for your Sankalpam account.

Your password reset token is: {reset_token}

Or click this link to reset: {reset_url}

This token will expire in 1 hour.

If you did not request a password reset, please ignore this email.

Best regards,
Sankalpam Team
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #dc2626; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 5px 5px; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #dc2626; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .token {{ background-color: #e5e7eb; padding: 10px; border-radius: 5px; font-family: monospace; word-break: break-all; }}
        .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Reset Your Password</h1>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p>You requested to reset your password for your Sankalpam account.</p>
            
            <p>Your password reset token is:</p>
            <div class="token">{reset_token}</div>
            
            <p style="text-align: center;">
                <a href="{reset_url}" class="button">Reset Password</a>
            </p>
            
            <p><strong>This token will expire in 1 hour.</strong></p>
            
            <p>If you did not request a password reset, please ignore this email.</p>
            
            <div class="footer">
                <p>Best regards,<br>Sankalpam Team</p>
            </div>
        </div>
    </div>
</body>
</html>
"""
        
        # Attach both plain text and HTML versions
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email via SMTP
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        print(f"✅ Password reset email sent to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending password reset email to {to_email}: {e}")
        # In development, still return True and print to console
        if settings.secret_key == "your-secret-key-change-in-production":
            print(f"\n{'='*60}")
            print(f"DEVELOPMENT MODE - Password Reset (SMTP failed)")
            print(f"To: {to_email}")
            print(f"Reset Token: {reset_token}")
            print(f"{'='*60}\n")
            return True
        return False
