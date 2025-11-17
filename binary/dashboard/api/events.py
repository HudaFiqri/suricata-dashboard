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
from cryptography.fernet import Fernet
import base64
import json
import logging

logger = logging.getLogger(__name__)


def decrypt_agent_payload(agent, encrypted_data: str) -> dict:
    """
    Decrypt payload from agent using agent's encryption key

    Args:
        agent: Agent object (from database)
        encrypted_data: Base64-encoded encrypted string

    Returns:
        Decrypted dictionary
    """
    try:
        # Get encryption key from agent
        encryption_key = agent.get('encryption_key') if isinstance(agent, dict) else agent.encryption_key

        if not encryption_key:
            raise ValueError("Agent has no encryption key configured")

        # Initialize crypto helper (handles double base64 encoding from agent)
        from binary.bin.agent.crypto import AgentCrypto
        crypto = AgentCrypto(encryption_key)

        # Decrypt using the same method as agent encryption
        return crypto.decrypt_json(encrypted_data)

    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise


@api.route('/events', methods=['POST'])
@require_agent_auth
def ingest_encrypted_events():
    """
    Ingest encrypted events from agent

    Expects encrypted payload:
    {
        "encrypted": "base64_encoded_encrypted_data"
    }

    Decrypted payload contains:
    {
        "events": [...]
    }
    """
    data = request.get_json()

    if not data or 'encrypted' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing encrypted payload'
        }), 400

    try:
        # Get agent from request (set by require_agent_auth)
        agent_id = request.agent_id
        agent = request.agent

        # Decrypt payload
        decrypted = decrypt_agent_payload(agent, data['encrypted'])

        # Extract events
        events = decrypted.get('events', [])

        if not events:
            return jsonify({
                'success': True,
                'inserted': 0,
                'message': 'No events to process'
            })

        # Store events in MongoDB
        db = get_mongo_db()

        # Prepare events for insertion
        processed_events = []
        for event in events:
            # Parse timestamp
            timestamp_str = event.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except:
                    timestamp = datetime.utcnow()
            else:
                timestamp = datetime.utcnow()

            # Build document
            doc = {
                'agent_id': agent_id,
                'event_type': event.get('event_type'),
                'timestamp': timestamp,
                'raw_event': event,
                'received_at': datetime.utcnow(),
                'expire_at': datetime.utcnow() + timedelta(days=90)  # TTL index
            }
            processed_events.append(doc)

        # Insert events
        result = db.events.insert_many(processed_events)
        inserted_count = len(result.inserted_ids)

        logger.info(f"Ingested {inserted_count} encrypted events from agent {agent_id}")

        return jsonify({
            'success': True,
            'inserted': inserted_count
        }), 201

    except Exception as e:
        logger.error(f"Failed to ingest encrypted events: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
