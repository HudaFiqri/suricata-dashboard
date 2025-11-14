"""
WebSocket Session Management
Track active connections and provide utilities
"""

from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """Manage WebSocket sessions"""

    def __init__(self):
        self.agent_sessions = {}  # {session_id: agent_info}
        self.ui_sessions = {}     # {session_id: user_info}

    # Agent session management
    def add_agent_session(self, session_id, agent_id, agent_name):
        """Register agent session"""
        self.agent_sessions[session_id] = {
            'agent_id': agent_id,
            'agent_name': agent_name,
            'connected_at': datetime.utcnow()
        }
        logger.info(f"Agent session added: {agent_name} ({session_id})")

    def remove_agent_session(self, session_id):
        """Remove agent session"""
        if session_id in self.agent_sessions:
            agent_info = self.agent_sessions[session_id]
            logger.info(f"Agent session removed: {agent_info['agent_name']} ({session_id})")
            del self.agent_sessions[session_id]

    def get_agent_session(self, session_id):
        """Get agent session info"""
        return self.agent_sessions.get(session_id)

    def get_agent_by_id(self, agent_id):
        """Get agent session by agent_id"""
        for sid, info in self.agent_sessions.items():
            if info['agent_id'] == agent_id:
                return sid, info
        return None, None

    def get_active_agents(self):
        """Get list of active agent sessions"""
        return list(self.agent_sessions.values())

    def get_agent_count(self):
        """Get number of active agent connections"""
        return len(self.agent_sessions)

    # UI session management
    def add_ui_session(self, session_id, user_id, username, role):
        """Register UI session"""
        self.ui_sessions[session_id] = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'connected_at': datetime.utcnow()
        }
        logger.info(f"UI session added: {username} ({session_id})")

    def remove_ui_session(self, session_id):
        """Remove UI session"""
        if session_id in self.ui_sessions:
            user_info = self.ui_sessions[session_id]
            logger.info(f"UI session removed: {user_info['username']} ({session_id})")
            del self.ui_sessions[session_id]

    def get_ui_session(self, session_id):
        """Get UI session info"""
        return self.ui_sessions.get(session_id)

    def get_active_ui_clients(self):
        """Get list of active UI sessions"""
        return list(self.ui_sessions.values())

    def get_ui_count(self):
        """Get number of active UI connections"""
        return len(self.ui_sessions)

    # Statistics
    def get_stats(self):
        """Get session statistics"""
        return {
            'total_connections': len(self.agent_sessions) + len(self.ui_sessions),
            'agent_connections': len(self.agent_sessions),
            'ui_connections': len(self.ui_sessions),
            'active_agents': self.get_active_agents(),
            'active_ui_clients': self.get_active_ui_clients()
        }

    def clear_all(self):
        """Clear all sessions (for testing/shutdown)"""
        logger.warning("Clearing all WebSocket sessions")
        self.agent_sessions.clear()
        self.ui_sessions.clear()

# Global session manager instance
session_manager = SessionManager()

__all__ = ['session_manager', 'SessionManager']
