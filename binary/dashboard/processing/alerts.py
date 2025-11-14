"""
Alert Engine
Rule-based alerting for critical events
"""

import logging
from datetime import datetime
from binary.dashboard.database import get_pg_session, get_mongo_db
from binary.dashboard.models import Agent

logger = logging.getLogger(__name__)

class AlertRule:
    """Single alert rule"""

    def __init__(self, rule_id, name, condition, severity='medium', enabled=True):
        self.rule_id = rule_id
        self.name = name
        self.condition = condition
        self.severity = severity
        self.enabled = enabled

    def matches(self, event):
        """Check if event matches this rule"""
        if not self.enabled:
            return False

        try:
            # Evaluate condition
            return self._evaluate_condition(event)
        except Exception as e:
            logger.error(f"Rule {self.rule_id} evaluation failed: {e}")
            return False

    def _evaluate_condition(self, event):
        """Evaluate rule condition against event"""

        # Example conditions:
        # - severity == 1 (critical alerts)
        # - signature_id in [list]
        # - src_ip matches pattern
        # - dest_port == 22 and event_type == 'ssh'

        condition_type = self.condition.get('type')

        if condition_type == 'severity':
            threshold = self.condition.get('threshold', 1)
            event_severity = event.get('indexed', {}).get('severity')
            if event_severity is not None:
                return event_severity <= threshold

        elif condition_type == 'signature_id':
            allowed_ids = self.condition.get('ids', [])
            event_sig_id = event.get('indexed', {}).get('signature_id')
            if event_sig_id:
                return event_sig_id in allowed_ids

        elif condition_type == 'event_type':
            allowed_types = self.condition.get('types', [])
            return event.get('event_type') in allowed_types

        elif condition_type == 'port':
            port = self.condition.get('port')
            direction = self.condition.get('direction', 'dest')  # 'src' or 'dest'

            event_port = event.get('indexed', {}).get(f'{direction}_port')
            if event_port:
                return event_port == port

        return False

class AlertEngine:
    """Process events and trigger alerts based on rules"""

    def __init__(self):
        self.rules = []
        self._load_default_rules()

    def _load_default_rules(self):
        """Load default alert rules"""

        # Rule 1: Critical severity alerts
        self.rules.append(AlertRule(
            rule_id='critical_severity',
            name='Critical Severity Alerts',
            condition={'type': 'severity', 'threshold': 1},
            severity='critical'
        ))

        # Rule 2: SSH brute force attempts
        self.rules.append(AlertRule(
            rule_id='ssh_bruteforce',
            name='SSH Brute Force Detection',
            condition={'type': 'port', 'port': 22, 'direction': 'dest'},
            severity='high'
        ))

        # Rule 3: Known malware signatures
        # self.rules.append(AlertRule(
        #     rule_id='malware_detected',
        #     name='Malware Signature Detected',
        #     condition={'type': 'signature_id', 'ids': [2100498, 2100366]},  # Example ET malware sids
        #     severity='critical'
        # ))

    def process_event(self, event):
        """
        Process a single event through alert rules

        Args:
            event: Event dict from agent

        Returns:
            List of triggered alert dicts (empty if no matches)
        """
        triggered = []

        for rule in self.rules:
            if rule.matches(event):
                alert = self._create_alert(rule, event)
                triggered.append(alert)
                self._store_alert(alert)

        return triggered

    def _create_alert(self, rule, event):
        """Create alert dict from rule and event"""
        return {
            'rule_id': rule.rule_id,
            'rule_name': rule.name,
            'severity': rule.severity,
            'agent_id': event.get('agent_id'),
            'agent_name': event.get('agent_name'),
            'event_id': str(event.get('_id')) if '_id' in event else None,
            'event_type': event.get('event_type'),
            'timestamp': event.get('timestamp'),
            'triggered_at': datetime.utcnow(),
            'details': {
                'signature': event.get('raw_event', {}).get('alert', {}).get('signature'),
                'signature_id': event.get('indexed', {}).get('signature_id'),
                'src_ip': event.get('indexed', {}).get('src_ip'),
                'dest_ip': event.get('indexed', {}).get('dest_ip'),
                'proto': event.get('indexed', {}).get('proto')
            }
        }

    def _store_alert(self, alert):
        """Store alert in database"""
        try:
            db = get_mongo_db()

            # Add TTL
            from datetime import timedelta
            alert['expire_at'] = datetime.utcnow() + timedelta(days=90)

            db.alerts.insert_one(alert)
            logger.info(f"Alert stored: {alert['rule_name']} from {alert['agent_name']}")

        except Exception as e:
            logger.error(f"Failed to store alert: {e}")

    def get_recent_alerts(self, agent_id=None, hours=24, limit=100):
        """
        Get recent alerts

        Args:
            agent_id: Filter by agent (None = all)
            hours: Time window
            limit: Max results

        Returns:
            List of alert dicts
        """
        try:
            db = get_mongo_db()

            from datetime import timedelta

            query = {
                'triggered_at': {'$gte': datetime.utcnow() - timedelta(hours=hours)}
            }

            if agent_id:
                query['agent_id'] = agent_id

            alerts = list(db.alerts.find(query).sort('triggered_at', -1).limit(limit))

            # Convert ObjectId to string
            for alert in alerts:
                alert['_id'] = str(alert['_id'])
                if 'triggered_at' in alert:
                    alert['triggered_at'] = alert['triggered_at'].isoformat()
                if 'timestamp' in alert:
                    alert['timestamp'] = alert['timestamp'].isoformat()

            return alerts

        except Exception as e:
            logger.error(f"Failed to get recent alerts: {e}")
            return []

    def add_rule(self, rule):
        """Add custom alert rule"""
        self.rules.append(rule)

    def remove_rule(self, rule_id):
        """Remove alert rule"""
        self.rules = [r for r in self.rules if r.rule_id != rule_id]

    def get_rules(self):
        """Get all rules"""
        return [
            {
                'rule_id': r.rule_id,
                'name': r.name,
                'condition': r.condition,
                'severity': r.severity,
                'enabled': r.enabled
            }
            for r in self.rules
        ]

# Global alert engine instance
alert_engine = AlertEngine()

__all__ = ['AlertEngine', 'AlertRule', 'alert_engine']
