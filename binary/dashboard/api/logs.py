"""
Log Ingestion API
Receive log entries from agents
"""

from flask import request, jsonify
from datetime import datetime, timedelta
from binary.dashboard.api import api
from binary.dashboard.api.auth import require_agent_auth
from binary.dashboard.database import get_mongo_db
import logging

logger = logging.getLogger(__name__)

@api.route('/logs/batch', methods=['POST'])
@require_agent_auth
def receive_log_batch():
    """Receive batch of log entries from agent"""
    data = request.get_json()

    agent_id = request.agent_id
    logs = data.get('logs', [])

    if not logs:
        return jsonify({'success': False, 'error': 'No logs provided'}), 400

    # Get MongoDB
    mongo_db = get_mongo_db()

    # Prepare logs
    processed_logs = []

    for log in logs:
        try:
            # Parse timestamp
            timestamp_str = log.get('timestamp')
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.utcnow()

            # Build document
            doc = {
                'agent_id': agent_id,
                'agent_name': request.agent.name,
                'log_type': log.get('log_type', 'suricata'),
                'level': log.get('level', 'INFO'),
                'timestamp': timestamp,
                'message': log.get('message', ''),
                'raw_line': log.get('raw_line', ''),
                'structured': log.get('structured', {}),
                'received_at': datetime.utcnow(),
                'expire_at': datetime.utcnow() + timedelta(days=30)  # 30 days TTL
            }

            processed_logs.append(doc)

        except Exception as e:
            logger.error(f"Failed to process log: {e}")

    # Bulk insert
    if processed_logs:
        try:
            result = mongo_db.logs.insert_many(processed_logs, ordered=False)
            inserted = len(result.inserted_ids)
        except Exception as e:
            logger.error(f"MongoDB log insert failed: {e}")
            inserted = 0
    else:
        inserted = 0

    return jsonify({
        'success': True,
        'received': len(logs),
        'inserted': inserted
    })
