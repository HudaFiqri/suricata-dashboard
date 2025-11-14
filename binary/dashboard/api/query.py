"""
Query API
Search and query events and logs from MongoDB
"""

from flask import request, jsonify
from datetime import datetime, timedelta
from binary.dashboard.api import api
from binary.dashboard.api.auth import require_auth
from binary.dashboard.database import get_mongo_db
import logging

logger = logging.getLogger(__name__)

@api.route('/query/events', methods=['POST'])
@require_auth
def query_events():
    """Query events from MongoDB"""
    data = request.get_json()

    mongo_db = get_mongo_db()

    # Build query
    query = {}

    # Agent filter
    if 'agent_id' in data:
        query['agent_id'] = data['agent_id']

    # Event type filter
    if 'event_type' in data:
        query['event_type'] = data['event_type']

    # Time range
    from_time = data.get('from')
    to_time = data.get('to')

    if from_time or to_time:
        time_query = {}
        if from_time:
            time_query['$gte'] = datetime.fromisoformat(from_time)
        if to_time:
            time_query['$lte'] = datetime.fromisoformat(to_time)
        query['timestamp'] = time_query

    # Additional filters
    filters = data.get('filters', {})

    if 'src_ip' in filters:
        query['indexed.src_ip'] = {'$regex': filters['src_ip']}

    if 'dest_ip' in filters:
        query['indexed.dest_ip'] = {'$regex': filters['dest_ip']}

    if 'signature_id' in filters:
        query['indexed.signature_id'] = filters['signature_id']

    if 'severity' in filters:
        if isinstance(filters['severity'], list):
            query['indexed.severity'] = {'$in': filters['severity']}
        else:
            query['indexed.severity'] = filters['severity']

    # Sorting
    sort_field = data.get('sort', {}).get('field', 'timestamp')
    sort_order = -1 if data.get('sort', {}).get('order', 'desc') == 'desc' else 1

    # Pagination
    limit = data.get('limit', 100)
    offset = data.get('offset', 0)

    try:
        # Count total
        total = mongo_db.events.count_documents(query)

        # Execute query
        events = list(mongo_db.events.find(query)
                     .sort(sort_field, sort_order)
                     .skip(offset)
                     .limit(limit))

        # Convert ObjectId to string
        for event in events:
            event['_id'] = str(event['_id'])
            if 'timestamp' in event:
                event['timestamp'] = event['timestamp'].isoformat()
            if 'received_at' in event:
                event['received_at'] = event['received_at'].isoformat()

        return jsonify({
            'success': True,
            'total': total,
            'events': events
        })

    except Exception as e:
        logger.error(f"Query failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/query/logs', methods=['POST'])
@require_auth
def query_logs():
    """Query logs from MongoDB"""
    data = request.get_json()

    mongo_db = get_mongo_db()

    # Build query
    query = {}

    if 'agent_id' in data:
        query['agent_id'] = data['agent_id']

    if 'level' in data:
        query['level'] = data['level']

    # Time range
    from_time = data.get('from')
    to_time = data.get('to')

    if from_time or to_time:
        time_query = {}
        if from_time:
            time_query['$gte'] = datetime.fromisoformat(from_time)
        if to_time:
            time_query['$lte'] = datetime.fromisoformat(to_time)
        query['timestamp'] = time_query

    # Text search
    search = data.get('search')
    if search:
        query['$text'] = {'$search': search}

    # Pagination
    limit = data.get('limit', 100)
    offset = data.get('offset', 0)

    try:
        # Count total
        total = mongo_db.logs.count_documents(query)

        # Execute query
        logs = list(mongo_db.logs.find(query)
                   .sort('timestamp', -1)
                   .skip(offset)
                   .limit(limit))

        # Convert ObjectId to string
        for log in logs:
            log['_id'] = str(log['_id'])
            if 'timestamp' in log:
                log['timestamp'] = log['timestamp'].isoformat()
            if 'received_at' in log:
                log['received_at'] = log['received_at'].isoformat()

        return jsonify({
            'success': True,
            'total': total,
            'logs': logs
        })

    except Exception as e:
        logger.error(f"Log query failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
