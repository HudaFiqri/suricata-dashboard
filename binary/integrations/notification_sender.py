"""
Notification Sender - Send notifications to Telegram and Discord
"""
import requests
import json
from typing import Dict, Any, Optional


class NotificationSender:
    """Handle sending notifications to various integrations"""

    @staticmethod
    def send_telegram(bot_token: str, chat_id: str, message: str) -> Dict[str, Any]:
        """
        Send message to Telegram

        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID or @channel
            message: Message to send

        Returns:
            Dict with success status and message
        """
        if not bot_token or not chat_id:
            return {
                'success': False,
                'message': 'Bot token and chat ID are required'
            }

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()

            if data.get('ok'):
                return {
                    'success': True,
                    'message': 'Message sent successfully to Telegram'
                }
            else:
                error_msg = data.get('description', 'Unknown error')
                return {
                    'success': False,
                    'message': f'Telegram API error: {error_msg}'
                }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'message': 'Request timeout - Telegram API not responding'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'Connection error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error sending to Telegram: {str(e)}'
            }

    @staticmethod
    def send_discord(webhook_url: str, message: str, title: str = None) -> Dict[str, Any]:
        """
        Send message to Discord via webhook

        Args:
            webhook_url: Discord webhook URL
            message: Message content
            title: Optional embed title

        Returns:
            Dict with success status and message
        """
        if not webhook_url:
            return {
                'success': False,
                'message': 'Webhook URL is required'
            }

        # Discord embed format
        payload = {
            'content': None,
            'embeds': [{
                'title': title or '🔔 Suricata Alert',
                'description': message,
                'color': 16744448  # Orange color
            }]
        }

        try:
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code in [200, 204]:
                return {
                    'success': True,
                    'message': 'Message sent successfully to Discord'
                }
            else:
                return {
                    'success': False,
                    'message': f'Discord webhook error: HTTP {response.status_code}'
                }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'message': 'Request timeout - Discord webhook not responding'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'Connection error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error sending to Discord: {str(e)}'
            }

    @staticmethod
    def format_alert_message(alert_data: Dict[str, Any], template: str = None) -> str:
        """
        Format alert message using template

        Args:
            alert_data: Alert data from Suricata
            template: Custom message template (optional)

        Returns:
            Formatted message string
        """
        # Default template
        if not template:
            template = """🚨 <b>Security Alert</b>

<b>Signature:</b> {signature}
<b>Category:</b> {category}
<b>Severity:</b> {severity}
<b>Source:</b> {src_ip}:{src_port}
<b>Destination:</b> {dest_ip}:{dest_port}
<b>Protocol:</b> {protocol}
<b>Timestamp:</b> {timestamp}"""

        # Extract alert details
        alert = alert_data.get('alert', {})

        # Prepare template variables
        variables = {
            'signature': alert.get('signature', 'Unknown'),
            'category': alert.get('category', 'Unknown'),
            'severity': alert.get('severity', '0'),
            'src_ip': alert_data.get('src_ip', 'N/A'),
            'src_port': alert_data.get('src_port', 'N/A'),
            'dest_ip': alert_data.get('dest_ip', 'N/A'),
            'dest_port': alert_data.get('dest_port', 'N/A'),
            'protocol': alert_data.get('proto', 'N/A'),
            'timestamp': alert_data.get('timestamp', 'N/A')
        }

        # Format message
        try:
            return template.format(**variables)
        except KeyError as e:
            return f"Error formatting message: Missing variable {e}"
