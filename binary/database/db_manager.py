from sqlalchemy import func, text
from sqlalchemy.orm import sessionmaker, scoped_session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import hashlib

from .models import Base, Alert, Log, Statistics, TrafficStats
from .mysql import create_mysql_engine
from .postgresql import create_postgresql_engine


class DatabaseManager:
    """Database manager with support for MySQL and PostgreSQL."""

    SUPPORTED_DB_TYPES = ('mysql', 'postgresql')

    def __init__(self, db_type: str = 'postgresql', db_config: Optional[Dict[str, str]] = None):
        """Initialize database manager."""
        normalized_type = (db_type or '').strip().lower()
        if normalized_type not in self.SUPPORTED_DB_TYPES:
            raise ValueError(f"Unsupported database type: {db_type}")

        if not db_config:
            raise ValueError('Database configuration is required for SQL backends.')

        self.db_type = normalized_type
        self.original_db_type = self.db_type
        self.db_config = db_config

        self.engine = None
        self.db_url = ''

        self._initialize_database()

        self.Session = scoped_session(sessionmaker(bind=self.engine))
        self._create_tables()

    ENGINE_FACTORIES = {
        'mysql': create_mysql_engine,
        'postgresql': create_postgresql_engine,
    }

    def _initialize_database(self):
        """Create an engine for the configured SQL backend."""
        factory = self.ENGINE_FACTORIES.get(self.db_type)
        if not factory:
            raise ValueError(f"Unsupported database type: {self.db_type}")

        try:
            self.db_url, self.engine = factory(self.db_config)
            print(f"[OK] Database connected: {self.db_type.upper()}")
        except Exception as exc:
            raise RuntimeError(f"Failed to connect to {self.db_type.upper()}: {exc}") from exc

    def _create_tables(self):
        """Create all tables"""
        try:
            Base.metadata.create_all(self.engine)
        except Exception as e:
            print(f"Error creating tables: {e}")

    def get_session(self):
        """Get a new database session"""
        return self.Session()

    def close(self):
        """Close database connection"""
        self.Session.remove()
        self.engine.dispose()

    def get_db_info(self) -> Dict[str, Any]:
        """Get database connection information"""
        # Hash the database URL with MD5 for security
        url_hash = hashlib.md5(self.db_url.encode()).hexdigest()

        return {
            'type': self.db_type,
            'original_type': self.original_db_type,
            'url': url_hash,  # MD5 hashed URL
            'connected': self._test_connection(),
        }

    def _test_connection(self) -> bool:
        """Test if database connection is alive"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    # ==================== Alert Operations ====================

    def add_alert(self, alert_data: Dict[str, Any]) -> Optional[Alert]:
        """Add a new alert to database"""
        session = self.get_session()
        try:
            alert = Alert(
                timestamp=alert_data.get('timestamp', datetime.utcnow()),
                signature=alert_data.get('signature'),
                signature_id=alert_data.get('signature_id'),
                category=alert_data.get('category'),
                severity=alert_data.get('severity'),
                protocol=alert_data.get('protocol'),
                src_ip=alert_data.get('src_ip'),
                src_port=alert_data.get('src_port'),
                dest_ip=alert_data.get('dest_ip'),
                dest_port=alert_data.get('dest_port'),
                payload=alert_data.get('payload'),
                extra_data=json.dumps(alert_data.get('extra_data', {}))
            )
            session.add(alert)
            session.commit()
            return alert
        except Exception as e:
            session.rollback()
            print(f"Error adding alert: {e}")
            return None
        finally:
            session.close()

    def get_alerts(self, limit: int = 100, offset: int = 0,
                   category: Optional[str] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None) -> List[Alert]:
        """Get alerts with optional filtering"""
        session = self.get_session()
        try:
            query = session.query(Alert)

            if category:
                query = query.filter(Alert.category == category)

            if start_time:
                query = query.filter(Alert.timestamp >= start_time)

            if end_time:
                query = query.filter(Alert.timestamp <= end_time)

            alerts = query.order_by(Alert.timestamp.desc()).limit(limit).offset(offset).all()
            return alerts
        except Exception as e:
            print(f"Error getting alerts: {e}")
            return []
        finally:
            session.close()

    def get_alert_count(self, category: Optional[str] = None,
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None) -> int:
        """Get count of alerts with optional filtering"""
        session = self.get_session()
        try:
            query = session.query(func.count(Alert.id))

            if category:
                query = query.filter(Alert.category == category)

            if start_time:
                query = query.filter(Alert.timestamp >= start_time)

            if end_time:
                query = query.filter(Alert.timestamp <= end_time)

            count = query.scalar()
            return count or 0
        except Exception as e:
            print(f"Error getting alert count: {e}")
            return 0
        finally:
            session.close()

    # ==================== Log Operations ====================

    def add_log(self, log_data: Dict[str, Any]) -> Optional[Log]:
        """Add a new log entry"""
        session = self.get_session()
        try:
            log = Log(
                timestamp=log_data.get('timestamp', datetime.utcnow()),
                event_type=log_data.get('event_type'),
                log_level=log_data.get('log_level'),
                message=log_data.get('message'),
                source=log_data.get('source'),
                extra_data=json.dumps(log_data.get('extra_data', {}))
            )
            session.add(log)
            session.commit()
            return log
        except Exception as e:
            session.rollback()
            print(f"Error adding log: {e}")
            return None
        finally:
            session.close()

    def get_logs(self, limit: int = 100, offset: int = 0,
                event_type: Optional[str] = None) -> List[Log]:
        """Get logs with optional filtering"""
        session = self.get_session()
        try:
            query = session.query(Log)

            if event_type:
                query = query.filter(Log.event_type == event_type)

            logs = query.order_by(Log.timestamp.desc()).limit(limit).offset(offset).all()
            return logs
        except Exception as e:
            print(f"Error getting logs: {e}")
            return []
        finally:
            session.close()

    # ==================== Statistics Operations ====================

    def add_statistic(self, stat_data: Dict[str, Any]) -> Optional[Statistics]:
        """Add a new statistic entry"""
        session = self.get_session()
        try:
            stat = Statistics(
                timestamp=stat_data.get('timestamp', datetime.utcnow()),
                metric_name=stat_data.get('metric_name'),
                metric_value=stat_data.get('metric_value'),
                metric_type=stat_data.get('metric_type', 'gauge'),
                category=stat_data.get('category'),
                extra_data=json.dumps(stat_data.get('extra_data', {}))
            )
            session.add(stat)
            session.commit()
            return stat
        except Exception as e:
            session.rollback()
            print(f"Error adding statistic: {e}")
            return None
        finally:
            session.close()

    def get_statistics(self, category: Optional[str] = None,
                      metric_name: Optional[str] = None,
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None,
                      limit: int = 1000) -> List[Statistics]:
        """Get statistics with optional filtering"""
        session = self.get_session()
        try:
            query = session.query(Statistics)

            if category:
                query = query.filter(Statistics.category == category)

            if metric_name:
                query = query.filter(Statistics.metric_name == metric_name)

            if start_time:
                query = query.filter(Statistics.timestamp >= start_time)

            if end_time:
                query = query.filter(Statistics.timestamp <= end_time)

            stats = query.order_by(Statistics.timestamp.desc()).limit(limit).all()
            return stats
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return []
        finally:
            session.close()

    def get_latest_stats(self, categories: List[str] = None) -> Dict[str, float]:
        """Get latest statistics for each category"""
        session = self.get_session()
        try:
            if not categories:
                categories = ['ssh', 'http', 'dns', 'total']

            result = {}
            for category in categories:
                stat = session.query(Statistics).filter(
                    Statistics.category == category
                ).order_by(Statistics.timestamp.desc()).first()

                if stat:
                    result[category] = stat.metric_value
                else:
                    result[category] = 0.0

            return result
        except Exception as e:
            print(f"Error getting latest stats: {e}")
            return {cat: 0.0 for cat in (categories or ['ssh', 'http', 'dns', 'total'])}
        finally:
            session.close()

    # ==================== Cleanup Operations ====================

    def cleanup_old_data(self, days: int = 30):
        """Delete data older than specified days"""
        session = self.get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Delete old alerts
            deleted_alerts = session.query(Alert).filter(
                Alert.timestamp < cutoff_date
            ).delete()

            # Delete old logs
            deleted_logs = session.query(Log).filter(
                Log.timestamp < cutoff_date
            ).delete()

            # Delete old statistics
            deleted_stats = session.query(Statistics).filter(
                Statistics.timestamp < cutoff_date
            ).delete()

            session.commit()

            return {
                'alerts_deleted': deleted_alerts,
                'logs_deleted': deleted_logs,
                'statistics_deleted': deleted_stats
            }
        except Exception as e:
            session.rollback()
            print(f"Error cleaning up old data: {e}")
            return None
        finally:
            session.close()

    # ==================== Traffic Stats Operations ====================

    def add_traffic_stats(self, stats_data: Dict[str, Any]) -> Optional[TrafficStats]:
        """Add aggregated traffic statistics"""
        session = self.get_session()
        try:
            stats = TrafficStats(
                timestamp=stats_data.get('timestamp', datetime.utcnow()),
                protocol=stats_data.get('protocol'),
                packet_count=stats_data.get('packet_count', 0),
                byte_count=stats_data.get('byte_count', 0),
                flow_count=stats_data.get('flow_count', 0),
                alert_count=stats_data.get('alert_count', 0),
                interval_seconds=stats_data.get('interval_seconds', 60)
            )
            session.add(stats)
            session.commit()
            return stats
        except Exception as e:
            session.rollback()
            print(f"Error adding traffic stats: {e}")
            return None
        finally:
            session.close()

    def get_traffic_stats(self, protocol: Optional[str] = None,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         limit: int = 1000) -> List[TrafficStats]:
        """Get traffic statistics with optional filtering"""
        session = self.get_session()
        try:
            query = session.query(TrafficStats)

            if protocol:
                query = query.filter(TrafficStats.protocol == protocol.upper())

            if start_time:
                query = query.filter(TrafficStats.timestamp >= start_time)

            if end_time:
                query = query.filter(TrafficStats.timestamp <= end_time)

            stats = query.order_by(TrafficStats.timestamp.desc()).limit(limit).all()
            return stats
        except Exception as e:
            print(f"Error getting traffic stats: {e}")
            return []
        finally:
            session.close()

    def get_latest_traffic_stats(self) -> Dict[str, int]:
        """Get latest traffic statistics for each protocol"""
        session = self.get_session()
        try:
            result = {}
            protocols = ['TCP', 'UDP', 'ICMP']

            for proto in protocols:
                stat = session.query(TrafficStats).filter(
                    TrafficStats.protocol == proto
                ).order_by(TrafficStats.timestamp.desc()).first()

                if stat:
                    result[proto.lower()] = {
                        'packet_count': stat.packet_count,
                        'flow_count': stat.flow_count,
                        'alert_count': stat.alert_count,
                        'byte_count': stat.byte_count,
                        'timestamp': stat.timestamp
                    }
                else:
                    result[proto.lower()] = {
                        'packet_count': 0,
                        'flow_count': 0,
                        'alert_count': 0,
                        'byte_count': 0,
                        'timestamp': None
                    }

            return result
        except Exception as e:
            print(f"Error getting latest traffic stats: {e}")
            return {}
        finally:
            session.close()

    def reset_traffic_stats(self) -> int:
        """Reset all traffic statistics - delete all records"""
        session = self.get_session()
        try:
            count = session.query(TrafficStats).count()
            session.query(TrafficStats).delete()
            session.commit()
            print(f"[DB] Reset traffic stats: {count} records deleted")
            return count
        except Exception as e:
            session.rollback()
            print(f"Error resetting traffic stats: {e}")
            raise
        finally:
            session.close()
