from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Alert(Base):
    """Model for Suricata alerts"""
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    signature = Column(String(255), index=True)
    signature_id = Column(Integer)
    category = Column(String(100), index=True)
    severity = Column(Integer)
    protocol = Column(String(20), index=True)
    src_ip = Column(String(45), index=True)
    src_port = Column(Integer)
    dest_ip = Column(String(45), index=True)
    dest_port = Column(Integer)
    payload = Column(Text, nullable=True)
    extra_data = Column(Text, nullable=True)  # JSON string for additional data

    def __repr__(self):
        return f"<Alert(id={self.id}, signature='{self.signature}', timestamp={self.timestamp})>"

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'signature': self.signature,
            'signature_id': self.signature_id,
            'category': self.category,
            'severity': self.severity,
            'protocol': self.protocol,
            'src_ip': self.src_ip,
            'src_port': self.src_port,
            'dest_ip': self.dest_ip,
            'dest_port': self.dest_port,
            'payload': self.payload,
            'extra_data': self.extra_data
        }


class Log(Base):
    """Model for general Suricata logs"""
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String(50), index=True)
    log_level = Column(String(20))
    message = Column(Text)
    source = Column(String(100))
    extra_data = Column(Text, nullable=True)  # JSON string

    def __repr__(self):
        return f"<Log(id={self.id}, event_type='{self.event_type}', timestamp={self.timestamp})>"

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'event_type': self.event_type,
            'log_level': self.log_level,
            'message': self.message,
            'source': self.source,
            'extra_data': self.extra_data
        }


class Statistics(Base):
    """Model for Suricata statistics metrics"""
    __tablename__ = 'statistics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metric_name = Column(String(100), index=True)
    metric_value = Column(Float)
    metric_type = Column(String(50))  # e.g., 'counter', 'gauge', 'rate'
    category = Column(String(50), index=True)  # e.g., 'ssh', 'http', 'dns', 'total'
    extra_data = Column(Text, nullable=True)  # JSON string

    def __repr__(self):
        return f"<Statistics(id={self.id}, metric_name='{self.metric_name}', value={self.metric_value})>"

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'metric_type': self.metric_type,
            'category': self.category,
            'extra_data': self.extra_data
        }


class TrafficStats(Base):
    """Model for aggregated traffic statistics (for RRD)"""
    __tablename__ = 'traffic_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    protocol = Column(String(20), index=True)  # TCP, UDP, ICMP, etc
    packet_count = Column(Integer, default=0)
    byte_count = Column(Integer, default=0)
    flow_count = Column(Integer, default=0)
    alert_count = Column(Integer, default=0)
    interval_seconds = Column(Integer, default=60)  # Aggregation interval

    def __repr__(self):
        return f"<TrafficStats(protocol='{self.protocol}', packets={self.packet_count}, timestamp={self.timestamp})>"

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'protocol': self.protocol,
            'packet_count': self.packet_count,
            'byte_count': self.byte_count,
            'flow_count': self.flow_count,
            'alert_count': self.alert_count,
            'interval_seconds': self.interval_seconds
        }
