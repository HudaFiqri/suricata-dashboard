"""
Integrations API - Handles notification integrations (Telegram, Discord, etc.)
"""
from flask import jsonify, request


class IntegrationsAPI:
    """API for managing notification integrations"""

    def __init__(self, integration_manager):
        self.integration_manager = integration_manager

    def get_integrations(self):
        """Get all integration settings"""
        try:
            settings = self.integration_manager.get_settings()
            hashes = self.integration_manager.get_hashes()
            response = {'success': True, 'settings': settings}
            if hashes:
                response['hashes'] = hashes
            return jsonify(response)
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    def get_integration(self, integration_name):
        """Get single integration settings"""
        try:
            settings = self.integration_manager.get_integration(integration_name)
            hash_info = self.integration_manager.get_hash(integration_name)
            response = {'success': True, 'settings': settings, 'integration': integration_name.lower()}
            if hash_info:
                response['hash'] = hash_info
            return jsonify(response)
        except ValueError as exc:
            return jsonify({'success': False, 'message': str(exc)}), 404
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    def save_integration(self, integration_name):
        """Save integration configuration"""
        try:
            payload = request.get_json(silent=True) or {}
            settings = self.integration_manager.update_integration(integration_name, payload)
            hash_info = self.integration_manager.get_hash(integration_name)
            response = {'success': True, 'settings': settings, 'integration': integration_name.lower()}
            if hash_info:
                response['hash'] = hash_info
            return jsonify(response)
        except ValueError as exc:
            return jsonify({'success': False, 'message': str(exc)}), 404
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    def test_integration(self, integration_name):
        """Send test message to integration"""
        try:
            from binary.integrations.notification_sender import NotificationSender

            payload = request.get_json(silent=True) or {}
            custom_message = payload.get('message', '')

            # Get integration settings
            settings = self.integration_manager.get_integration(integration_name)

            # Create sample alert data for testing
            sample_alert = {
                'alert': {
                    'signature': 'ET SCAN Potential SSH Brute Force Attack',
                    'category': 'Attempted Administrator Privilege Gain',
                    'severity': 2
                },
                'src_ip': '192.168.1.100',
                'src_port': '54321',
                'dest_ip': '10.0.0.50',
                'dest_port': '22',
                'proto': 'TCP',
                'timestamp': '2024-01-15T10:30:45.123456+0000'
            }

            if integration_name.lower() == 'telegram':
                bot_token = settings.get('bot_token', '')
                chat_id = settings.get('chat_id', '')
                template = settings.get('message_template', '')

                if not bot_token or not chat_id:
                    return jsonify({
                        'success': False,
                        'message': 'Please configure Bot Token and Chat ID first'
                    })

                # Use custom message from request, or template from settings, or default
                if custom_message:
                    message = NotificationSender.format_alert_message(sample_alert, custom_message)
                elif template:
                    message = NotificationSender.format_alert_message(sample_alert, template)
                else:
                    message = "🧪 <b>Test Message from Suricata Dashboard</b>\n\nThis is a test notification to verify your Telegram integration is working correctly."

                result = NotificationSender.send_telegram(bot_token, chat_id, message)
                return jsonify(result)

            elif integration_name.lower() == 'discord':
                webhook_url = settings.get('webhook_url', '')
                template = settings.get('message_template', '')

                if not webhook_url:
                    return jsonify({
                        'success': False,
                        'message': 'Please configure Webhook URL first'
                    })

                # Use custom message from request, or template from settings, or default
                if custom_message:
                    message = NotificationSender.format_alert_message(sample_alert, custom_message)
                    title = "🧪 Test Alert Message"
                elif template:
                    message = NotificationSender.format_alert_message(sample_alert, template)
                    title = "🧪 Test Alert Message"
                else:
                    message = "This is a test notification to verify your Discord integration is working correctly."
                    title = "🧪 Test Message from Suricata Dashboard"

                result = NotificationSender.send_discord(webhook_url, message, title)
                return jsonify(result)

            else:
                return jsonify({
                    'success': False,
                    'message': f'Integration {integration_name} not supported for testing'
                }), 404

        except ValueError as exc:
            return jsonify({'success': False, 'message': str(exc)}), 404
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    def save_template(self, integration_name):
        """Save custom message template for integration"""
        try:
            payload = request.get_json(silent=True) or {}
            template = payload.get('template', '')

            if not template:
                return jsonify({
                    'success': False,
                    'message': 'Template cannot be empty'
                })

            # Update integration with template
            update_payload = {'message_template': template}
            settings = self.integration_manager.update_integration(integration_name, update_payload)

            return jsonify({
                'success': True,
                'message': 'Message template saved successfully',
                'settings': settings
            })

        except ValueError as exc:
            return jsonify({'success': False, 'message': str(exc)}), 404
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
