"""
Notification system for sending digest summaries via Slack and Email.

This module provides functionality to send weekly digest summaries to various
channels including Slack webhooks and email notifications.
"""

from __future__ import annotations
import json
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional
import requests

logger = logging.getLogger(__name__)

class NotificationSender:
    """Base class for sending notifications."""
    
    def __init__(self):
        self.enabled = True
    
    def send(self, content: str, title: str = "Weekly Digest") -> bool:
        """
        Send notification with content.
        
        Args:
            content: Notification content
            title: Notification title
            
        Returns:
            True if sent successfully, False otherwise
        """
        raise NotImplementedError

class SlackNotifier(NotificationSender):
    """Slack notification sender using webhooks."""
    
    def __init__(self, webhook_url: str, channel: Optional[str] = None):
        """
        Initialize Slack notifier.
        
        Args:
            webhook_url: Slack webhook URL
            channel: Optional channel override
        """
        super().__init__()
        self.webhook_url = webhook_url
        self.channel = channel
    
    def send(self, content: str, title: str = "Weekly Digest") -> bool:
        """Send notification to Slack."""
        try:
            # Truncate content if too long (Slack has limits)
            if len(content) > 3000:
                content = content[:2900] + "\n... (truncated)"
            
            payload = {
                "text": f"📚 {title}",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"📚 {title}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": content
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
                            }
                        ]
                    }
                ]
            }
            
            if self.channel:
                payload["channel"] = self.channel
            
            response = requests.post(self.webhook_url, json=payload, timeout=30)
            response.raise_for_status()
            
            logger.info("Slack notification sent successfully")
            return True
            
        except (requests.RequestException, ValueError, KeyError) as e:
            logger.error("Failed to send Slack notification: %s", e)
            return False
    
    def send_digest_summary(self, digest_path: Path) -> bool:
        """Send a summary of the weekly digest."""
        try:
            if not digest_path.exists():
                logger.error(f"Digest file not found: {digest_path}")
                return False
            
            content = digest_path.read_text(encoding='utf-8')
            summary = self._extract_summary(content)
            
            return self.send(summary, "📊 Weekly Research Digest")
            
        except (FileNotFoundError, UnicodeDecodeError, requests.RequestException) as e:
            logger.error("Failed to send digest summary: %s", e)
            return False
    
    def _extract_summary(self, digest_content: str) -> str:
        """Extract a concise summary from the digest."""
        lines = digest_content.split('\n')
        summary_lines = []
        
        # Extract key information
        for line in lines:
            line = line.strip()
            if line.startswith('**Summary**:'):
                summary_lines.append(line)
            elif line.startswith('## ') and not line.startswith('## 📋'):
                # Section headers (but not table of contents)
                summary_lines.append(f"📂 {line[3:]}")
            elif line.startswith('### ') and len(summary_lines) < 10:
                # Paper titles (limit to avoid spam)
                summary_lines.append(f"📄 {line[4:]}")
        
        if not summary_lines:
            # Fallback: first few lines
            summary_lines = lines[:5]
        
        return '\n'.join(summary_lines[:15])  # Limit to 15 lines

class EmailNotifier(NotificationSender):
    """Email notification sender using SMTP."""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, 
                 password: str, from_email: str, to_emails: List[str]):
        """
        Initialize email notifier.
        
        Args:
            smtp_server: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
            from_email: Sender email address
            to_emails: List of recipient email addresses
        """
        super().__init__()
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
    
    def send(self, content: str, title: str = "Weekly Digest") -> bool:
        """Send email notification."""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"📚 {title} - {datetime.now().strftime('%Y-%m-%d')}"
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            
            # Create HTML version
            html_content = f"""
            <html>
            <body>
                <h2>📚 {title}</h2>
                <div style="white-space: pre-wrap; font-family: monospace;">
{content}
                </div>
                <hr>
                <p><small>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}</small></p>
            </body>
            </html>
            """
            
            # Create plain text version
            text_content = f"{title}\n\n{content}\n\nGenerated on {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
            
            # Attach both versions
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email notification sent to {len(self.to_emails)} recipients")
            return True
            
        except (smtplib.SMTPException, OSError, ValueError) as e:
            logger.error("Failed to send email notification: %s", e)
            return False
    
    def send_digest_attachment(self, digest_path: Path) -> bool:
        """Send digest as email attachment."""
        try:
            if not digest_path.exists():
                logger.error(f"Digest file not found: {digest_path}")
                return False
            
            from email.mime.base import MIMEBase
            from email import encoders
            
            msg = MIMEMultipart()
            msg['Subject'] = f"📊 Weekly Research Digest - {datetime.now().strftime('%Y-%m-%d')}"
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            
            # Email body
            body = f"""
            Hi,
            
            Please find attached this week's research digest.
            
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
            
            Best regards,
            AI Reading Lab
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach digest file
            with open(digest_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {digest_path.name}'
            )
            msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Digest email sent to {len(self.to_emails)} recipients")
            return True
            
        except (smtplib.SMTPException, OSError, FileNotFoundError) as e:
            logger.error("Failed to send digest email: %s", e)
            return False

class NotificationManager:
    """Manager for multiple notification channels."""
    
    def __init__(self):
        self.notifiers: List[NotificationSender] = []
    
    def add_slack_notifier(self, webhook_url: str, channel: Optional[str] = None):
        """Add Slack notifier."""
        notifier = SlackNotifier(webhook_url, channel)
        self.notifiers.append(notifier)
        logger.info("Slack notifier added")
    
    def add_email_notifier(self, smtp_server: str, smtp_port: int, username: str,
                          password: str, from_email: str, to_emails: List[str]):
        """Add email notifier."""
        notifier = EmailNotifier(smtp_server, smtp_port, username, password, from_email, to_emails)
        self.notifiers.append(notifier)
        logger.info("Email notifier added for %d recipients", len(to_emails))
    
    def send_notification(self, content: str, title: str = "Weekly Digest") -> Dict[str, bool]:
        """
        Send notification to all configured channels.
        
        Returns:
            Dictionary mapping notifier type to success status
        """
        results = {}
        
        for notifier in self.notifiers:
            notifier_type = type(notifier).__name__
            try:
                success = notifier.send(content, title)
                results[notifier_type] = success
            except (ValueError, RuntimeError, ConnectionError) as e:
                logger.error("Notifier %s failed: %s", notifier_type, e)
                results[notifier_type] = False
        
        return results
    
    def send_digest_notifications(self, digest_path: Path) -> Dict[str, bool]:
        """Send digest notifications to all channels."""
        results = {}
        
        for notifier in self.notifiers:
            notifier_type = type(notifier).__name__
            try:
                if isinstance(notifier, SlackNotifier):
                    success = notifier.send_digest_summary(digest_path)
                elif isinstance(notifier, EmailNotifier):
                    success = notifier.send_digest_attachment(digest_path)
                else:
                    # Fallback to generic send
                    content = digest_path.read_text(encoding='utf-8')
                    success = notifier.send(content, "Weekly Research Digest")
                
                results[notifier_type] = success
                
            except (ValueError, RuntimeError, ConnectionError, FileNotFoundError) as e:
                logger.error("Notifier %s failed: %s", notifier_type, e)
                results[notifier_type] = False
        
        return results

def create_notification_manager_from_config(config_path: Path) -> NotificationManager:
    """Create notification manager from configuration file."""
    manager = NotificationManager()
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Add Slack notifiers
        for slack_config in config.get('slack', []):
            manager.add_slack_notifier(
                webhook_url=slack_config['webhook_url'],
                channel=slack_config.get('channel')
            )
        
        # Add email notifiers
        for email_config in config.get('email', []):
            manager.add_email_notifier(
                smtp_server=email_config['smtp_server'],
                smtp_port=email_config['smtp_port'],
                username=email_config['username'],
                password=email_config['password'],
                from_email=email_config['from_email'],
                to_emails=email_config['to_emails']
            )
        
        logger.info("Loaded %d notification channels", len(manager.notifiers))
        
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        logger.error("Failed to load notification config: %s", e)
    
    return manager
