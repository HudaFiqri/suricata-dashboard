"""
Statistics API
Get aggregated statistics and metrics
"""

from flask import request, jsonify
from datetime import datetime, timedelta
from binary.dashboard.api import api
from binary.dashboard.api.auth import require_auth
from binary.dashboard.models import Agent, AgentStatistic
from binary.dashboard.database import get_pg_session, get_mongo_db
import logging

logger = logging.getLogger(__name__)

@api.route('/stats/<int:agent_id>', methods=['GET'])
@require_auth
def get_agent_stats(agent_id):
    """Get agent statistics"""
    session = get_pg_session()

    # Query parameters
    from_time = request.args.get('from')
    to_time = request.args.get('to')
    interval = request.args.get('interval', '1hour')

    # Default to last 24 hours
    if not from_time:
        from_dt = datetime.utcnow() - timedelta(hours=24)
    else:
        from_dt = datetime.fromisoformat(from_time)

    if not to_time:
        to_dt = datetime.utcnow()
    else:
        to_dt = datetime.fromisoformat(to_time)

    # Get statistics
    stats = session.query(AgentStatistic).filter(
        AgentStatistic.agent_id == agent_id,
        AgentStatistic.bucket_interval == interval,
        AgentStatistic.bucket_time >= from_dt,
        AgentStatistic.bucket_time <= to_dt
    ).order_by(AgentStatistic.bucket_time.asc()).all()

    return jsonify({
        'success': True,
        'agent_id': agent_id,
        'interval': interval,
        'from': from_dt.isoformat(),
        'to': to_dt.isoformat(),
        'data': [s.to_dict() for s in stats]
    })

@api.route('/stats/summary', methods=['GET'])
@require_auth
def get_dashboard_summary():
    """Get dashboard summary across all agents"""
    session = get_pg_session()
    mongo_db = get_mongo_db()

    # Agent summary
    total_agents = session.query(Agent).count()
    online_agents = session.query(Agent).filter_by(status='online').count()
    offline_agents = total_agents - online_agents

    # Event summary (last 24h from MongoDB)
    last_24h = datetime.utcnow() - timedelta(hours=24)

    try:
        # Total events
        total_events_24h = mongo_db.events.count_documents({
            'timestamp': {'$gte': last_24h}
        })

        # Alerts
        total_alerts_24h = mongo_db.events.count_documents({
            'event_type': 'alert',
            'timestamp': {'$gte': last_24h}
        })

        # Top signatures
        top_signatures = list(mongo_db.events.aggregate([
            {'$match': {'event_type': 'alert', 'timestamp': {'$gte': last_24h}}},
            {'$group': {
                '_id': '$indexed.signature_id',
                'signature': {'$first': '$indexed.signature'},
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]))

    except Exception as e:
        logger.error(f"MongoDB query failed: {e}")
        total_events_24h = 0
        total_alerts_24h = 0
        top_signatures = []

    # Calculate average CPU (from cached health metrics)
    agents_with_metrics = session.query(Agent).filter(
        Agent.status == 'online',
        Agent.health_metrics != None
    ).all()

    total_cpu = 0
    agent_count = 0

    for agent in agents_with_metrics:
        if agent.health_metrics and 'cpu_percent' in agent.health_metrics:
            total_cpu += agent.health_metrics['cpu_percent']
            agent_count += 1

    avg_cpu = round(total_cpu / agent_count, 2) if agent_count > 0 else 0

    return jsonify({
        'success': True,
        'summary': {
            'total_agents': total_agents,
            'online_agents': online_agents,
            'offline_agents': offline_agents,
            'total_events_24h': total_events_24h,
            'total_alerts_24h': total_alerts_24h,
            'avg_cpu_usage': avg_cpu,
            'top_signatures': [
                {'signature_id': s['_id'], 'signature': s.get('signature', 'Unknown'), 'count': s['count']}
                for s in top_signatures
            ]
        }
    })
