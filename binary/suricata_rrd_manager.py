import os
import time
import subprocess
from typing import Dict, Any, List
import json

class SuricataRRDManager:
    """Manager for RRDtool-based metrics collection and graphing"""

    def __init__(self, rrd_directory: str = "/var/lib/suricata/rrd", log_directory: str = "/var/log/suricata"):
        self.rrd_directory = rrd_directory
        self.log_directory = log_directory

        # Create RRD directory if not exists
        os.makedirs(self.rrd_directory, exist_ok=True)

        # RRD file paths
        self.ssh_rrd = os.path.join(self.rrd_directory, "ssh_alerts.rrd")
        self.http_rrd = os.path.join(self.rrd_directory, "http_alerts.rrd")
        self.dns_rrd = os.path.join(self.rrd_directory, "dns_alerts.rrd")
        self.total_rrd = os.path.join(self.rrd_directory, "total_alerts.rrd")

        # Initialize RRD databases
        self._init_rrd_databases()

    def _init_rrd_databases(self):
        """Initialize RRD databases if they don't exist"""
        rrd_files = {
            'ssh': self.ssh_rrd,
            'http': self.http_rrd,
            'dns': self.dns_rrd,
            'total': self.total_rrd
        }

        for name, rrd_file in rrd_files.items():
            if not os.path.exists(rrd_file):
                self._create_rrd(rrd_file, name)

    def _create_rrd(self, rrd_file: str, name: str):
        """Create a new RRD database"""
        try:
            cmd = [
                'rrdtool', 'create', rrd_file,
                '--step', '60',  # 1 minute intervals
                'DS:alerts:GAUGE:120:0:U',  # Data source: alerts count
                'RRA:AVERAGE:0.5:1:1440',   # 1 min avg for 24 hours
                'RRA:AVERAGE:0.5:5:2016',   # 5 min avg for 7 days
                'RRA:AVERAGE:0.5:60:744',   # 1 hour avg for 31 days
                'RRA:MAX:0.5:1:1440',       # 1 min max for 24 hours
                'RRA:MAX:0.5:5:2016',       # 5 min max for 7 days
                'RRA:MAX:0.5:60:744'        # 1 hour max for 31 days
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"Created RRD database: {rrd_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error creating RRD {rrd_file}: {e.stderr.decode()}")
        except Exception as e:
            print(f"Error creating RRD {rrd_file}: {e}")

    def update_metrics(self):
        """Update RRD databases with current metrics from logs"""
        try:
            # Count alerts from eve.json
            eve_log = os.path.join(self.log_directory, "eve.json")

            if not os.path.exists(eve_log):
                return {'success': False, 'message': 'Eve log not found'}

            # Count alerts by type (last 60 seconds worth)
            counts = self._count_recent_alerts(eve_log)

            # Update RRD databases
            timestamp = 'N'  # Use current time

            self._update_rrd(self.ssh_rrd, timestamp, counts.get('ssh', 0))
            self._update_rrd(self.http_rrd, timestamp, counts.get('http', 0))
            self._update_rrd(self.dns_rrd, timestamp, counts.get('dns', 0))
            self._update_rrd(self.total_rrd, timestamp, counts.get('total', 0))

            return {'success': True, 'counts': counts}

        except Exception as e:
            return {'success': False, 'message': str(e)}

    def _count_recent_alerts(self, eve_log: str, window_seconds: int = 60) -> Dict[str, int]:
        """Count alerts from eve.json in the last N seconds"""
        counts = {'ssh': 0, 'http': 0, 'dns': 0, 'total': 0}
        current_time = time.time()

        try:
            # Read last N lines (approximate)
            cmd = ['tail', '-n', '1000', eve_log]
            result = subprocess.run(cmd, capture_output=True, text=True)

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                try:
                    event = json.loads(line)

                    # Check if it's an alert
                    if event.get('event_type') != 'alert':
                        continue

                    # Check timestamp
                    timestamp_str = event.get('timestamp', '')
                    # Parse timestamp if needed (simplified here)

                    counts['total'] += 1

                    # Categorize by protocol/signature
                    alert = event.get('alert', {})
                    signature = alert.get('signature', '').lower()

                    if 'ssh' in signature:
                        counts['ssh'] += 1
                    elif 'http' in signature or 'web' in signature:
                        counts['http'] += 1
                    elif 'dns' in signature:
                        counts['dns'] += 1

                except json.JSONDecodeError:
                    continue

        except Exception as e:
            print(f"Error counting alerts: {e}")

        return counts

    def _update_rrd(self, rrd_file: str, timestamp: str, value: int):
        """Update a single RRD database"""
        try:
            cmd = ['rrdtool', 'update', rrd_file, f'{timestamp}:{value}']
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"Error updating RRD {rrd_file}: {e.stderr.decode()}")
        except Exception as e:
            print(f"Error updating RRD {rrd_file}: {e}")

    def generate_graph(self, metric: str = 'ssh', timespan: str = '1h') -> Dict[str, Any]:
        """Generate a graph for a specific metric"""
        rrd_files = {
            'ssh': self.ssh_rrd,
            'http': self.http_rrd,
            'dns': self.dns_rrd,
            'total': self.total_rrd
        }

        rrd_file = rrd_files.get(metric, self.ssh_rrd)

        if not os.path.exists(rrd_file):
            return {'success': False, 'message': 'RRD file not found'}

        # Generate graph
        graph_file = os.path.join(self.rrd_directory, f'{metric}_{timespan}.png')

        try:
            # Map timespan to rrdtool format
            timespan_map = {
                '1h': '3600',
                '6h': '21600',
                '24h': '86400',
                '7d': '604800',
                '30d': '2592000'
            }

            seconds = timespan_map.get(timespan, '3600')

            cmd = [
                'rrdtool', 'graph', graph_file,
                '--start', f'-{seconds}',
                '--end', 'now',
                '--width', '800',
                '--height', '300',
                '--title', f'{metric.upper()} Alerts - Last {timespan}',
                '--vertical-label', 'Alerts/min',
                f'DEF:alerts={rrd_file}:alerts:AVERAGE',
                'LINE2:alerts#0000FF:Alerts',
                'GPRINT:alerts:LAST:Current\\:%8.0lf',
                'GPRINT:alerts:AVERAGE:Average\\:%8.0lf',
                'GPRINT:alerts:MAX:Maximum\\:%8.0lf'
            ]

            subprocess.run(cmd, check=True, capture_output=True)

            return {'success': True, 'graph_path': graph_file}

        except subprocess.CalledProcessError as e:
            return {'success': False, 'message': f'Error generating graph: {e.stderr.decode()}'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def get_graph_data(self, metric: str = 'ssh', timespan: str = '1h') -> Dict[str, Any]:
        """Get data points for graphing (alternative to RRD graph)"""
        rrd_files = {
            'ssh': self.ssh_rrd,
            'http': self.http_rrd,
            'dns': self.dns_rrd,
            'total': self.total_rrd
        }

        rrd_file = rrd_files.get(metric, self.ssh_rrd)

        if not os.path.exists(rrd_file):
            return {'success': False, 'message': 'RRD file not found'}

        try:
            timespan_map = {
                '1h': '3600',
                '6h': '21600',
                '24h': '86400',
                '7d': '604800',
                '30d': '2592000'
            }

            seconds = timespan_map.get(timespan, '3600')

            cmd = [
                'rrdtool', 'fetch', rrd_file, 'AVERAGE',
                '--start', f'-{seconds}',
                '--end', 'now'
            ]

            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            # Parse output
            lines = result.stdout.strip().split('\n')
            data_points = []

            for line in lines[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 2:
                    timestamp = int(parts[0].rstrip(':'))
                    value = parts[1]

                    if value != 'nan':
                        data_points.append({
                            'timestamp': timestamp,
                            'value': float(value)
                        })

            return {'success': True, 'data': data_points}

        except subprocess.CalledProcessError as e:
            return {'success': False, 'message': f'Error fetching data: {e.stderr.decode()}'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
