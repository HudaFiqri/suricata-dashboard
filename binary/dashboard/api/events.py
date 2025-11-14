"""
Event Ingestion API
Receive events from agents and store in MongoDB
"""

from flask import request, jsonify
from datetime import datetime, timedelta
from binary.dashboard.api import api
from binary.dashboard.api.auth import require_agent_auth
from binary.dashboard.database import get_mongo_db
from binary.dashboard.models import Agent
from binary.dashboard.database import get_pg_session
import logging

logger = logging.getLogger(__name__)

@api.route('/events/batch', methods=['POST'])
@require_agent_auth
def receive_event_batch():
    """
    Receive batch of events from agent
    Stores in MongoDB for high-volume time-series data
    """
    data = request.get_json()

    agent_id = request.agent_id
    events = data.get('events', [])

    if not events:
        return jsonify({
            'success': False,
            'error': 'No events provided'
        }), 400

    # Get MongoDB
    mongo_db = get_mongo_db()

    # Prepare events for insertion
    processed_events = []
    failed = 0

    for event in events:
        try:
            # Parse timestamp
            timestamp_str = event.get('timestamp')
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.utcnow()

            # Build MongoDB document
            doc = {
                'agent_id': agent_id,
                'agent_name': request.agent.name,
                'event_type': event.get('event_type'),
                'timestamp': timestamp,
                'raw_event': event.get('data', event),
                'indexed': event.get('indexed', {}),
                'received_at': datetime.utcnow(),
                'expire_at': datetime.utcnow() + timedelta(days=90)  # TTL
            }

            processed_events.append(doc)

        except Exception as e:
            logger.error(f"Failed to process event: {e}")
            failed += 1

    # Bulk insert to MongoDB
    if processed_events:
        try:
            result = mongo_db.events.insert_many(processed_events, ordered=False)
            inserted = len(result.inserted_ids)
        except Exception as e:
            logger.error(f"MongoDB insert failed: {e}")
            inserted = 0
            failed = len(processed_events)
    else:
        inserted = 0

    # Update agent last_event_at
    if inserted > 0:
        session = get_pg_session()
        agent = session.query(Agent).filter_by(id=agent_id).first()
        if agent:
            agent.last_event_at = datetime.utcnow()
            session.commit()

    logger.debug(f"Agent {agent_id}: Received {len(events)}, Processed {inserted}, Failed {failed}")

    return jsonify({
        'success': True,
        'received': len(events),
        'processed': inserted,
        'failed': failed
    })

@api.route('/events/stream', methods=['POST'])
@require_agent_auth
def receive_event_stream():
    """
    Single event endpoint (for WebSocket fallback or testing)
    """
    data = request.get_json()

    agent_id = request.agent_id

    # Get MongoDB
    mongo_db = get_mongo_db()

    try:
        # Parse timestamp
        timestamp_str = data.get('timestamp')
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            timestamp = datetime.utcnow()

        # Build document
        doc = {
            'agent_id': agent_id,
            'agent_name': request.agent.name,
            'event_type': data.get('event_type'),
            'timestamp': timestamp,
            'raw_event': data.get('data', data),
            'indexed': data.get('indexed', {}),
            'received_at': datetime.utcnow(),
            'expire_at': datetime.utcnow() + timedelta(days=90)
        }

        # Insert
        result = mongo_db.events.insert_one(doc)

        return jsonify({
            'success': True,
            'event_id': str(result.inserted_id)
        })

    except Exception as e:
        logger.error(f"Failed to insert event: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
