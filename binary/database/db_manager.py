from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json

from .models import Base, Alert, Log, Statistics


class DatabaseManager:
    """
    Database manager with support for SQLite, MySQL, and PostgreSQL
    """

    def __init__(self, db_type: str = 'sqlite', db_config: Optional[Dict[str, str]] = None):
        """
        Initialize database manager

        Args:
            db_type: Database type ('sqlite', 'mysql', 'postgresql')
            db_config: Database configuration dict with keys:
                - For SQLite: {'path': '/path/to/db.sqlite'}
                - For MySQL: {'host': 'localhost', 'port': 3306, 'user': 'root',
                             'password': 'pass', 'database': 'suricata'}
                - For PostgreSQL: {'host': 'localhost', 'port': 5432, 'user': 'postgres',
                                  'password': 'pass', 'database': 'suricata'}
        """
        self.db_type = db_type.lower() if db_type else 'sqlite'
        self.db_config = db_config or {}
        self.fallback_active = False
        self.original_db_type = self.db_type

        # If db_type is empty or sqlite with no config, use local storage silently
        if not db_type or (self.db_type == 'sqlite' and not self.db_config):
            self.db_type = 'sqlite'
            self.db_url = 'sqlite:///suricata.db'

            self.engine = create_engine(
                self.db_url,
                connect_args={'check_same_thread': False},
                poolclass=StaticPool,
                echo=False
            )

            print(f"✓ Database connected: local")
        else:
            # Create database URL
            self.db_url = self._create_db_url()

            # Try to create engine and connect
            try:
                # Create engine
                if self.db_type == 'sqlite':
                    self.engine = create_engine(
                        self.db_url,
                        connect_args={'check_same_thread': False},
                        poolclass=StaticPool,
                        echo=False
                    )
                else:
                    self.engine = create_engine(
                        self.db_url,
                        pool_pre_ping=True,
                        pool_recycle=3600,
                        echo=False
                    )

                # Test connection
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))

                print(f"✓ Database connected: {self.db_type.upper()}")

            except Exception as e:
                print(f"✗ Failed to connect to {self.db_type.upper()}: {e}")
                print("→ Falling back to local storage...")

                # Fallback to SQLite
                self.fallback_active = True
                self.db_type = 'sqlite'
                self.db_url = 'sqlite:///suricata_fallback.db'

                self.engine = create_engine(
                    self.db_url,
                    connect_args={'check_same_thread': False},
                    poolclass=StaticPool,
                    echo=False
                )

                print(f"✓ Database connected: local (fallback)")

        # Create session factory
        self.Session = scoped_session(sessionmaker(bind=self.engine))

        # Create tables
        self._create_tables()

    def _create_db_url(self) -> str:
        """Create database URL based on type and config"""
        if self.db_type == 'sqlite':
            db_path = self.db_config.get('path', 'suricata.db')
            return f'sqlite:///{db_path}'

        elif self.db_type == 'mysql':
            host = self.db_config.get('host', 'localhost')
            port = self.db_config.get('port', 3306)
            user = self.db_config.get('user', 'root')
            password = self.db_config.get('password', '')
            database = self.db_config.get('database', 'suricata')
            return f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4'

        elif self.db_type == 'postgresql':
            host = self.db_config.get('host', 'localhost')
            port = self.db_config.get('port', 5432)
            user = self.db_config.get('user', 'postgres')
            password = self.db_config.get('password', '')
            database = self.db_config.get('database', 'suricata')
            return f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}'

        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

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
        return {
            'type': self.db_type,
            'original_type': self.original_db_type,
            'fallback_active': self.fallback_active,
            'url': self.db_url.split('@')[0] if '@' in self.db_url else self.db_url,  # Hide password
            'connected': self._test_connection()
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
