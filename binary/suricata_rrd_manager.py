import os
import time
import subprocess
from typing import Dict, Any, List
import json

try:
    import rrdtool
    HAS_RRDTOOL = True
except ImportError:
    HAS_RRDTOOL = False
    print("WARNING: python-rrdtool not installed. Monitoring features will be disabled.")

class SuricataRRDManager:
    """Manager for RRDtool-based metrics collection and graphing"""

    def __init__(self, rrd_directory: str = "/var/lib/suricata/rrd", log_directory: str = "/var/log/suricata"):
        self.rrd_directory = rrd_directory
        self.log_directory = log_directory
        self.enabled = HAS_RRDTOOL

        if not self.enabled:
            return

        # Create RRD directory if not exists
        try:
            os.makedirs(self.rrd_directory, exist_ok=True)
        except Exception as e:
            print(f"Error creating RRD directory: {e}")
            self.enabled = False
            return

        # RRD file paths
        self.ssh_rrd = os.path.join(self.rrd_directory, "ssh_alerts.rrd")
        self.http_rrd = os.path.join(self.rrd_directory, "http_alerts.rrd")
        self.dns_rrd = os.path.join(self.rrd_directory, "dns_alerts.rrd")
        self.total_rrd = os.path.join(self.rrd_directory, "total_alerts.rrd")

        # Initialize RRD databases
        self._init_rrd_databases()

    def _init_rrd_databases(self):
        """Initialize RRD databases if they don't exist"""
        if not self.enabled:
            return

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
        """Create a new RRD database using Python rrdtool"""
        if not self.enabled:
            return

        try:
            rrdtool.create(
                rrd_file,
                '--step', '60',  # 1 minute intervals
                'DS:alerts:GAUGE:120:0:U',  # Data source: alerts count
                'RRA:AVERAGE:0.5:1:1440',   # 1 min avg for 24 hours
                'RRA:AVERAGE:0.5:5:2016',   # 5 min avg for 7 days
                'RRA:AVERAGE:0.5:60:744',   # 1 hour avg for 31 days
                'RRA:MAX:0.5:1:1440',       # 1 min max for 24 hours
                'RRA:MAX:0.5:5:2016',       # 5 min max for 7 days
                'RRA:MAX:0.5:60:744'        # 1 hour max for 31 days
            )
            print(f"Created RRD database: {rrd_file}")
        except Exception as e:
            print(f"Error creating RRD {rrd_file}: {e}")

    def update_metrics(self):
        """Update RRD databases with current metrics from logs"""
        if not self.enabled:
            return {'success': False, 'message': 'RRDtool not available'}

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
        """Update a single RRD database using Python rrdtool"""
        if not self.enabled:
            return

        try:
            rrdtool.update(rrd_file, f'{timestamp}:{value}')
        except Exception as e:
            print(f"Error updating RRD {rrd_file}: {e}")

    def generate_graph(self, metric: str = 'ssh', timespan: str = '1h') -> Dict[str, Any]:
        """Generate a graph for a specific metric using Python rrdtool"""
        if not self.enabled:
            return {'success': False, 'message': 'RRDtool not available'}

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
            # Map timespan to seconds
            timespan_map = {
                '1h': 3600,
                '6h': 21600,
                '24h': 86400,
                '7d': 604800,
                '30d': 2592000
            }

            seconds = timespan_map.get(timespan, 3600)

            rrdtool.graph(
                graph_file,
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
            )

            return {'success': True, 'graph_path': graph_file}

        except Exception as e:
            return {'success': False, 'message': f'Error generating graph: {e}'}

    def get_graph_data(self, metric: str = 'ssh', timespan: str = '1h') -> Dict[str, Any]:
        """Get data points for graphing using Python rrdtool"""
        if not self.enabled:
            return {'success': False, 'message': 'RRDtool not available'}

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
                '1h': 3600,
                '6h': 21600,
                '24h': 86400,
                '7d': 604800,
                '30d': 2592000
            }

            seconds = timespan_map.get(timespan, 3600)

            # Fetch data from RRD
            result = rrdtool.fetch(
                rrd_file,
                'AVERAGE',
                '--start', f'-{seconds}',
                '--end', 'now'
            )

            # Parse result: (start, end, step), (data_source_names,), data_points
            (start_time, end_time, step), ds_names, data_points = result

            data = []
            current_time = start_time

            for point in data_points:
                if point[0] is not None:  # Skip None values
                    data.append({
                        'timestamp': int(current_time),
                        'value': float(point[0])
                    })
                current_time += step

            return {'success': True, 'data': data}

        except Exception as e:
            return {'success': False, 'message': f'Error fetching data: {e}'}
