"""
SQLAlchemy Models for Suricata Dashboard
PostgreSQL database models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, TIMESTAMP, JSON
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import relationship
from binary.dashboard.database import Base

# ============================================================================
# AGENT MODEL
# ============================================================================

class Agent(Base):
    __tablename__ = 'agents'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    hostname = Column(String(255), nullable=False)
    ip_address = Column(INET)

    # Authentication
    token_hash = Column(String(512), nullable=False)
    encryption_key = Column(String(512), nullable=False)

    # Metadata
    tags = Column(JSONB, default=[])
    version = Column(String(50))

    # Suricata Info
    suricata_version = Column(String(50))
    suricata_pid = Column(Integer)

    # Status
    status = Column(String(50), default='pending', index=True)
    last_seen = Column(DateTime(timezone=True))
    last_event_at = Column(DateTime(timezone=True))

    # Health Metrics (cached)
    health_metrics = Column(JSONB)

    # System Info
    system_info = Column(JSONB)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    configs = relationship('AgentConfig', back_populates='agent', cascade='all, delete-orphan')
    commands = relationship('AgentCommand', back_populates='agent', cascade='all, delete-orphan')
    statistics = relationship('AgentStatistic', back_populates='agent', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}', status='{self.status}')>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'hostname': self.hostname,
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'tags': self.tags,
            'version': self.version,
            'suricata_version': self.suricata_version,
            'suricata_pid': self.suricata_pid,
            'status': self.status,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'last_event_at': self.last_event_at.isoformat() if self.last_event_at else None,
            'health_metrics': self.health_metrics,
            'system_info': self.system_info,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# ============================================================================
# AGENT CONFIG MODEL
# ============================================================================

class AgentConfig(Base):
    __tablename__ = 'agent_configs'

    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id', ondelete='CASCADE'), nullable=False, index=True)

    # Config Content
    config_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64))

    # Versioning
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True, index=True)

    # Validation
    is_valid = Column(Boolean, default=True)
    validation_errors = Column(Text)

    # Status
    applied_at = Column(DateTime(timezone=True))
    status = Column(String(50), default='draft')

    # Metadata
    changed_by = Column(String(255))
    change_notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent = relationship('Agent', back_populates='configs')

    def __repr__(self):
        return f"<AgentConfig(id={self.id}, agent_id={self.agent_id}, type='{self.config_type}', version={self.version})>"

    def to_dict(self):
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'config_type': self.config_type,
            'content': self.content,
            'content_hash': self.content_hash,
            'version': self.version,
            'is_active': self.is_active,
            'is_valid': self.is_valid,
            'validation_errors': self.validation_errors,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None,
            'status': self.status,
            'changed_by': self.changed_by,
            'change_notes': self.change_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# ============================================================================
# AGENT COMMAND MODEL
# ============================================================================

class AgentCommand(Base):
    __tablename__ = 'agent_commands'

    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id', ondelete='CASCADE'), nullable=False, index=True)

    # Command Details
    command_type = Column(String(100), nullable=False)
    parameters = Column(JSONB)

    # Status
    status = Column(String(50), default='pending', index=True)

    # Result
    result = Column(JSONB)
    error_message = Column(Text)

    # Timing
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    sent_at = Column(DateTime(timezone=True))
    acknowledged_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    timeout_at = Column(DateTime(timezone=True))

    # Metadata
    created_by = Column(String(255))
    priority = Column(Integer, default=5)

    # Relationships
    agent = relationship('Agent', back_populates='commands')

    def __repr__(self):
        return f"<AgentCommand(id={self.id}, agent_id={self.agent_id}, type='{self.command_type}', status='{self.status}')>"

    def to_dict(self):
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'command_type': self.command_type,
            'parameters': self.parameters,
            'status': self.status,
            'result': self.result,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'timeout_at': self.timeout_at.isoformat() if self.timeout_at else None,
            'created_by': self.created_by,
            'priority': self.priority
        }

# ============================================================================
# AGENT STATISTICS MODEL
# ============================================================================

class AgentStatistic(Base):
    __tablename__ = 'agent_statistics'

    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id', ondelete='CASCADE'), nullable=False, index=True)

    # Time bucket
    bucket_time = Column(DateTime(timezone=True), nullable=False, index=True)
    bucket_interval = Column(String(20), nullable=False, index=True)

    # Metrics
    metrics = Column(JSONB, nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    agent = relationship('Agent', back_populates='statistics')

    def __repr__(self):
        return f"<AgentStatistic(id={self.id}, agent_id={self.agent_id}, interval='{self.bucket_interval}')>"

    def to_dict(self):
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'bucket_time': self.bucket_time.isoformat() if self.bucket_time else None,
            'bucket_interval': self.bucket_interval,
            'metrics': self.metrics,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# ============================================================================
# USER MODEL
# ============================================================================

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True)
    password_hash = Column(String(512), nullable=False)

    # Roles
    role = Column(String(50), default='viewer')

    # API Access
    api_key_hash = Column(String(512))

    # Permissions
    permissions = Column(JSONB, default={})

    # Status
    is_active = Column(Boolean, default=True, index=True)
    last_login = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'permissions': self.permissions,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# ============================================================================
# AUDIT LOG MODEL
# ============================================================================

class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True)

    # Who
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), index=True)
    username = Column(String(255))
    agent_id = Column(Integer, ForeignKey('agents.id', ondelete='SET NULL'), index=True)

    # What
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50))
    resource_id = Column(Integer)

    # Details
    details = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)

    # When
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', user='{self.username}')>"

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'agent_id': self.agent_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# ============================================================================
# USER SESSION MODEL
# ============================================================================

class UserSession(Base):
    __tablename__ = 'user_sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Session Info
    session_token = Column(String(512), unique=True, nullable=False, index=True)

    # Client Info
    ip_address = Column(INET)
    user_agent = Column(Text)
    device_type = Column(String(50))  # 'desktop', 'mobile', 'tablet'
    browser = Column(String(100))
    os = Column(String(100))

    # Status
    is_active = Column(Boolean, default=True, index=True)

    # Timing
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    last_activity = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    expires_at = Column(DateTime(timezone=True), index=True)
    logged_out_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'user_agent': self.user_agent,
            'device_type': self.device_type,
            'browser': self.browser,
            'os': self.os,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'logged_out_at': self.logged_out_at.isoformat() if self.logged_out_at else None
        }
