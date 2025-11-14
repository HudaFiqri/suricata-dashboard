"""
Event Aggregation
Aggregate events for statistics and analytics
"""

import logging
from datetime import datetime, timedelta
from collections import defaultdict
from binary.dashboard.database import get_mongo_db

logger = logging.getLogger(__name__)

class EventAggregator:
    """Aggregate events for statistics"""

    def __init__(self):
        self.mongo_db = None

    def _get_db(self):
        """Get MongoDB database"""
        if not self.mongo_db:
            self.mongo_db = get_mongo_db()
        return self.mongo_db

    def aggregate_by_type(self, agent_id=None, hours=24):
        """
        Aggregate events by type

        Args:
            agent_id: Filter by specific agent (None = all agents)
            hours: Time window in hours

        Returns:
            Dict with event type counts
        """
        db = self._get_db()

        # Build query
        query = {
            'timestamp': {'$gte': datetime.utcnow() - timedelta(hours=hours)}
        }

        if agent_id:
            query['agent_id'] = agent_id

        # Aggregate pipeline
        pipeline = [
            {'$match': query},
            {'$group': {
                '_id': '$event_type',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}}
        ]

        try:
            results = list(db.events.aggregate(pipeline))
            return {r['_id']: r['count'] for r in results}
        except Exception as e:
            logger.error(f"Aggregation failed: {e}")
            return {}

    def aggregate_by_severity(self, agent_id=None, hours=24):
        """
        Aggregate alerts by severity

        Args:
            agent_id: Filter by specific agent
            hours: Time window

        Returns:
            Dict with severity counts
        """
        db = self._get_db()

        query = {
            'timestamp': {'$gte': datetime.utcnow() - timedelta(hours=hours)},
            'event_type': 'alert'
        }

        if agent_id:
            query['agent_id'] = agent_id

        pipeline = [
            {'$match': query},
            {'$group': {
                '_id': '$indexed.severity',
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id': 1}}
        ]

        try:
            results = list(db.events.aggregate(pipeline))
            return {r['_id']: r['count'] for r in results if r['_id'] is not None}
        except Exception as e:
            logger.error(f"Severity aggregation failed: {e}")
            return {}

    def aggregate_by_agent(self, hours=24):
        """
        Aggregate events by agent

        Returns:
            Dict with agent_id -> event count
        """
        db = self._get_db()

        query = {
            'timestamp': {'$gte': datetime.utcnow() - timedelta(hours=hours)}
        }

        pipeline = [
            {'$match': query},
            {'$group': {
                '_id': '$agent_id',
                'count': {'$sum': 1},
                'agent_name': {'$first': '$agent_name'}
            }},
            {'$sort': {'count': -1}}
        ]

        try:
            results = list(db.events.aggregate(pipeline))
            return {
                r['_id']: {
                    'count': r['count'],
                    'agent_name': r.get('agent_name', 'Unknown')
                }
                for r in results
            }
        except Exception as e:
            logger.error(f"Agent aggregation failed: {e}")
            return {}

    def get_top_signatures(self, agent_id=None, hours=24, limit=10):
        """
        Get top alert signatures

        Returns:
            List of (signature, count) tuples
        """
        db = self._get_db()

        query = {
            'timestamp': {'$gte': datetime.utcnow() - timedelta(hours=hours)},
            'event_type': 'alert'
        }

        if agent_id:
            query['agent_id'] = agent_id

        pipeline = [
            {'$match': query},
            {'$group': {
                '_id': '$raw_event.alert.signature',
                'count': {'$sum': 1},
                'signature_id': {'$first': '$indexed.signature_id'},
                'severity': {'$first': '$indexed.severity'}
            }},
            {'$sort': {'count': -1}},
            {'$limit': limit}
        ]

        try:
            results = list(db.events.aggregate(pipeline))
            return [
                {
                    'signature': r['_id'],
                    'signature_id': r.get('signature_id'),
                    'count': r['count'],
                    'severity': r.get('severity', 3)
                }
                for r in results if r['_id'] is not None
            ]
        except Exception as e:
            logger.error(f"Top signatures query failed: {e}")
            return []

    def get_top_source_ips(self, agent_id=None, hours=24, limit=10):
        """
        Get top source IPs from alerts

        Returns:
            List of (ip, count) dicts
        """
        db = self._get_db()

        query = {
            'timestamp': {'$gte': datetime.utcnow() - timedelta(hours=hours)},
            'event_type': 'alert',
            'indexed.src_ip': {'$exists': True}
        }

        if agent_id:
            query['agent_id'] = agent_id

        pipeline = [
            {'$match': query},
            {'$group': {
                '_id': '$indexed.src_ip',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': limit}
        ]

        try:
            results = list(db.events.aggregate(pipeline))
            return [
                {'ip': r['_id'], 'count': r['count']}
                for r in results
            ]
        except Exception as e:
            logger.error(f"Top source IPs query failed: {e}")
            return []

    def get_timeline(self, agent_id=None, hours=24, interval_minutes=60):
        """
        Get event timeline with specified interval

        Returns:
            List of (timestamp, count) tuples
        """
        db = self._get_db()

        query = {
            'timestamp': {'$gte': datetime.utcnow() - timedelta(hours=hours)}
        }

        if agent_id:
            query['agent_id'] = agent_id

        # Group by time intervals
        pipeline = [
            {'$match': query},
            {'$group': {
                '_id': {
                    '$toDate': {
                        '$subtract': [
                            {'$toLong': '$timestamp'},
                            {'$mod': [
                                {'$toLong': '$timestamp'},
                                interval_minutes * 60 * 1000
                            ]}
                        ]
                    }
                },
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id': 1}}
        ]

        try:
            results = list(db.events.aggregate(pipeline))
            return [
                {
                    'timestamp': r['_id'].isoformat() if r['_id'] else None,
                    'count': r['count']
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Timeline query failed: {e}")
            return []
