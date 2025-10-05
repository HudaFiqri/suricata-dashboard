"""
Background Tasks - All daemon threads for monitoring and sync
"""
import os
import json
import time
import threading
from datetime import datetime


class BackgroundTasks:
    """Manages all background tasks for the application"""

    def __init__(self, engine, config):
        self.engine = engine
        self.config = config
        self.threads = []

    def start_all(self):
        """Start all background tasks"""
        # RRD metrics update
        self._start_thread(self._update_rrd_metrics, "RRD Metrics")

        # Alert sync from eve.json to database
        self._start_thread(self._sync_alerts_to_database, "Alert Sync")

        # Statistics sync from stats.log to database
        self._start_thread(self._sync_stats_to_database, "Stats Sync")

        # Database retention cleanup
        if self.config.DB_RETENTION_DAYS > 0:
            self._start_thread(self._database_retention_worker, "DB Cleanup")
            print(f"[DB-CLEANUP] Retention worker active (retention: {self.config.DB_RETENTION_DAYS} days)")
        else:
            print("[DB-CLEANUP] Retention worker disabled (DB_RETENTION_DAYS=0)")

        # Auto-restart monitor
        if self.config.AUTO_RESTART_ENABLED:
            self._start_thread(self._auto_restart_monitor, "Auto-Restart")
            print(f"[AUTO-RESTART] Monitoring enabled (max retries: {self.config.AUTO_RESTART_MAX_RETRIES}, check interval: {self.config.AUTO_RESTART_CHECK_INTERVAL}s)")

    def _start_thread(self, target, name):
        """Start a daemon thread"""
        thread = threading.Thread(target=target, daemon=True, name=name)
        thread.start()
        self.threads.append(thread)

    # ==================== RRD Metrics ====================
    def _update_rrd_metrics(self):
        """Update RRD metrics every minute"""
        while True:
            try:
                self.engine.rrd_manager.update_metrics()
            except Exception as e:
                print(f"Error updating RRD metrics: {e}")
            time.sleep(60)

    # ==================== Alert Sync ====================
    def _sync_alerts_to_database(self):
        """Sync alerts from eve.json to database"""
        last_position = 0
        eve_log_path = f"{self.config.SURICATA_LOG_DIR}/eve.json"

        print("[ALERT-SYNC] Alert synchronization enabled - Monitoring eve.json")

        while True:
            try:
                with open(eve_log_path, 'r') as f:
                    f.seek(last_position)

                    for line in f:
                        try:
                            event = json.loads(line.strip())

                            if event.get('event_type') == 'alert':
                                alert = event.get('alert', {})
                                alert_data = {
                                    'timestamp': datetime.fromisoformat(event.get('timestamp', '').replace('Z', '+00:00')) if event.get('timestamp') else datetime.utcnow(),
                                    'signature': alert.get('signature'),
                                    'signature_id': alert.get('signature_id'),
                                    'category': alert.get('category'),
                                    'severity': alert.get('severity'),
                                    'protocol': event.get('proto'),
                                    'src_ip': event.get('src_ip'),
                                    'src_port': event.get('src_port'),
                                    'dest_ip': event.get('dest_ip'),
                                    'dest_port': event.get('dest_port'),
                                    'payload': event.get('payload'),
                                    'extra_data': json.dumps(event)
                                }
                                self.engine.db_manager.add_alert(alert_data)

                        except json.JSONDecodeError:
                            continue

                    last_position = f.tell()

            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"[ALERT-SYNC] Error: {e}")

            time.sleep(5)

    # ==================== Stats Sync ====================
    def _sync_stats_to_database(self):
        """Sync statistics from stats.log to database"""
        stats_log_path = os.path.join(self.config.SURICATA_LOG_DIR, 'stats.log')
        last_position = 0
        current_timestamp = None

        print("[STATS-SYNC] Statistics synchronization enabled - Monitoring stats.log")

        def _parse_timestamp(line: str):
            try:
                _, value = line.split('Date:', 1)
                ts_str = value.strip().split('(')[0].strip()
                return datetime.strptime(ts_str, '%m/%d/%Y -- %H:%M:%S')
            except Exception:
                return datetime.utcnow()

        while True:
            try:
                if not os.path.exists(stats_log_path):
                    time.sleep(10)
                    continue

                file_size = os.path.getsize(stats_log_path)
                if file_size < last_position:
                    last_position = 0

                with open(stats_log_path, 'r', encoding='utf-8') as stats_file:
                    stats_file.seek(last_position)

                    for raw_line in stats_file:
                        line = raw_line.strip()
                        if not line:
                            continue

                        if line.lower().startswith('date:'):
                            current_timestamp = _parse_timestamp(line)
                            continue

                        if '|' not in line:
                            continue

                        parts = [segment.strip() for segment in line.split('|') if segment.strip()]
                        if len(parts) < 3:
                            continue

                        metric_name, scope, value_token = parts[0], parts[1], parts[2]
                        try:
                            metric_value = float(value_token.split()[0])
                        except ValueError:
                            continue

                        timestamp = current_timestamp or datetime.utcnow()
                        category = metric_name.split('.', 1)[0] if '.' in metric_name else scope.lower()

                        self.engine.db_manager.add_statistic({
                            'timestamp': timestamp,
                            'metric_name': metric_name,
                            'metric_value': metric_value,
                            'metric_type': scope,
                            'category': category,
                            'extra_data': {'scope': scope, 'raw': line},
                        })

                    last_position = stats_file.tell()

            except FileNotFoundError:
                last_position = 0
            except Exception as err:
                print(f"[STATS-SYNC] Error: {err}")

            time.sleep(10)

    # ==================== Database Retention ====================
    def _database_retention_worker(self):
        """Cleanup old database records"""
        cleanup_interval = 3600  # one hour

        while True:
            try:
                retention_days = self.config.DB_RETENTION_DAYS
                if retention_days and retention_days > 0:
                    result = self.engine.db_manager.cleanup_old_data(days=retention_days)
                    if isinstance(result, dict):
                        print(
                            f"[DB-CLEANUP] Retention applied (>{retention_days}d): "
                            f"alerts={result.get('alerts_deleted', 0)}, "
                            f"logs={result.get('logs_deleted', 0)}, "
                            f"statistics={result.get('statistics_deleted', 0)}"
                        )
            except Exception as err:
                print(f"[DB-CLEANUP] Error: {err}")

            time.sleep(cleanup_interval)

    # ==================== Auto-Restart Monitor ====================
    def _auto_restart_monitor(self):
        """Monitor Suricata and auto-restart if crashed"""
        retry_count = 0
        last_status = None

        while True:
            try:
                status = self.engine.controller.get_status()
                is_running = status.get('running', False)

                # Check if Suricata crashed
                if not is_running and last_status and last_status.get('running', False):
                    print(f"[AUTO-RESTART] Suricata crashed! Retry count: {retry_count}/{self.config.AUTO_RESTART_MAX_RETRIES}")

                    if retry_count < self.config.AUTO_RESTART_MAX_RETRIES:
                        print("[AUTO-RESTART] Attempting to restart Suricata...")
                        result = self.engine.controller.restart()

                        if result.get('success'):
                            print("[AUTO-RESTART] Suricata restarted successfully")
                            retry_count += 1
                        else:
                            print(f"[AUTO-RESTART] Failed to restart: {result.get('message')}")
                    else:
                        print(f"[AUTO-RESTART] Max retries ({self.config.AUTO_RESTART_MAX_RETRIES}) reached.")

                # Reset retry count if running
                if is_running:
                    retry_count = 0

                last_status = status

            except Exception as e:
                print(f"[AUTO-RESTART] Error: {e}")

            time.sleep(self.config.AUTO_RESTART_CHECK_INTERVAL)
