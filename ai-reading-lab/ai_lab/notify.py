"""
CLI tool for sending notifications via Slack and Email.
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from .notifications import NotificationManager, create_notification_manager_from_config

def main():
    ap = argparse.ArgumentParser(description='Send notifications via Slack and Email.')
    ap.add_argument('--config', help='Configuration file for notification channels')
    ap.add_argument('--digest', help='Path to weekly digest file')
    ap.add_argument('--message', help='Custom message to send')
    ap.add_argument('--title', default='Weekly Digest', help='Notification title')
    ap.add_argument('--slack-webhook', help='Slack webhook URL')
    ap.add_argument('--slack-channel', help='Slack channel override')
    ap.add_argument('--email-smtp', help='SMTP server')
    ap.add_argument('--email-port', type=int, default=587, help='SMTP port')
    ap.add_argument('--email-user', help='SMTP username')
    ap.add_argument('--email-password', help='SMTP password')
    ap.add_argument('--email-from', help='From email address')
    ap.add_argument('--email-to', nargs='+', help='To email addresses')
    ap.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = ap.parse_args()
    
    # Create notification manager
    manager = NotificationManager()
    
    # Load from config file if provided
    if args.config:
        config_path = Path(args.config)
        if config_path.exists():
            manager = create_notification_manager_from_config(config_path)
        else:
            print(f"Config file not found: {config_path}")
            return
    
    # Add individual notifiers if specified
    if args.slack_webhook:
        manager.add_slack_notifier(args.slack_webhook, args.slack_channel)
    
    if args.email_smtp and args.email_user and args.email_password and args.email_from and args.email_to:
        manager.add_email_notifier(
            smtp_server=args.email_smtp,
            smtp_port=args.email_port,
            username=args.email_user,
            password=args.email_password,
            from_email=args.email_from,
            to_emails=args.email_to
        )
    
    if not manager.notifiers:
        print("No notification channels configured")
        return
    
    # Send notifications
    if args.digest:
        digest_path = Path(args.digest)
        if not digest_path.exists():
            print(f"Digest file not found: {digest_path}")
            return
        
        print(f"Sending digest notifications from: {digest_path}")
        results = manager.send_digest_notifications(digest_path)
        
    elif args.message:
        print("Sending custom message...")
        results = manager.send_notification(args.message, args.title)
        
    else:
        ap.error("Must provide either --digest or --message")
    
    # Report results
    print("\nNotification Results:")
    for notifier_type, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {notifier_type}: {'Success' if success else 'Failed'}")
    
    if args.verbose:
        print(f"\nTotal channels: {len(manager.notifiers)}")
        print(f"Successful: {sum(results.values())}")
        print(f"Failed: {len(results) - sum(results.values())}")

if __name__ == '__main__':
    main()
