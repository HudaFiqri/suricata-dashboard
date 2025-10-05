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

    def __init__(self, rrd_directory: str = "/var/lib/suricata/rrd", log_directory: str = "/var/log/suricata", db_manager=None):
        self.rrd_directory = rrd_directory
        self.log_directory = log_directory
        self.db_manager = db_manager
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

        # RRD file paths (protocol-based)
        self.tcp_rrd = os.path.join(self.rrd_directory, "tcp_traffic.rrd")
        self.udp_rrd = os.path.join(self.rrd_directory, "udp_traffic.rrd")
        self.icmp_rrd = os.path.join(self.rrd_directory, "icmp_traffic.rrd")
        self.alerts_rrd = os.path.join(self.rrd_directory, "alerts.rrd")

        # Initialize RRD databases
        self._init_rrd_databases()

    def _init_rrd_databases(self):
        """Initialize RRD databases if they don't exist"""
        if not self.enabled:
            return

        rrd_files = {
            'tcp': self.tcp_rrd,
            'udp': self.udp_rrd,
            'icmp': self.icmp_rrd,
            'alerts': self.alerts_rrd
        }

        for name, rrd_file in rrd_files.items():
            if not os.path.exists(rrd_file):
                self._create_rrd(rrd_file, name)
            else:
                print(f"RRD database already exists: {rrd_file}")

    def regenerate_rrd_databases(self):
        """Force regenerate all RRD databases"""
        if not self.enabled:
            return {'success': False, 'message': 'RRDtool not available'}

        rrd_files = {
            'tcp': self.tcp_rrd,
            'udp': self.udp_rrd,
            'icmp': self.icmp_rrd,
            'alerts': self.alerts_rrd
        }

        regenerated = []
        for name, rrd_file in rrd_files.items():
            try:
                # Delete old RRD file if exists
                if os.path.exists(rrd_file):
                    os.remove(rrd_file)
                    print(f"Deleted old RRD database: {rrd_file}")

                # Create new RRD file
                self._create_rrd(rrd_file, name)
                regenerated.append(name)
            except Exception as e:
                print(f"Error regenerating RRD {name}: {e}")

        return {
            'success': True,
            'message': f'Regenerated {len(regenerated)} RRD databases',
            'regenerated': regenerated
        }

    def _create_rrd(self, rrd_file: str, name: str):
        """Create a new RRD database using Python rrdtool"""
        if not self.enabled:
            return

        try:
            if name == 'alerts':
                # Alerts RRD: only count
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
            else:
                # Traffic RRD: flows, packets, bytes
                rrdtool.create(
                    rrd_file,
                    '--step', '60',  # 1 minute intervals
                    'DS:flows:GAUGE:120:0:U',    # Flow count
                    'DS:packets:GAUGE:120:0:U',  # Packet count
                    'DS:bytes:GAUGE:120:0:U',    # Byte count
                    'RRA:AVERAGE:0.5:1:1440',    # 1 min avg for 24 hours
                    'RRA:AVERAGE:0.5:5:2016',    # 5 min avg for 7 days
                    'RRA:AVERAGE:0.5:60:744',    # 1 hour avg for 31 days
                    'RRA:MAX:0.5:1:1440',        # 1 min max for 24 hours
                    'RRA:MAX:0.5:5:2016',        # 5 min max for 7 days
                    'RRA:MAX:0.5:60:744'         # 1 hour max for 31 days
                )
            print(f"Created RRD database: {rrd_file}")
        except Exception as e:
            print(f"Error creating RRD {rrd_file}: {e}")

    def update_metrics(self):
        """Update RRD databases with current metrics from database"""
        if not self.enabled:
            return {'success': False, 'message': 'RRDtool not available'}

        try:
            # Get traffic stats from database
            if self.db_manager:
                stats = self.db_manager.get_latest_traffic_stats()

                if not stats:
                    return {'success': False, 'message': 'No stats available'}

                # Update RRD databases with protocol-specific data
                timestamp = 'N'  # Use current time

                # TCP Traffic
                tcp_data = stats.get('tcp', {})
                tcp_flows = tcp_data.get('flow_count', 0)
                tcp_packets = tcp_data.get('packet_count', 0)
                tcp_bytes = tcp_data.get('byte_count', 0)
                self._update_traffic_rrd(self.tcp_rrd, timestamp, tcp_flows, tcp_packets, tcp_bytes)

                # UDP Traffic
                udp_data = stats.get('udp', {})
                udp_flows = udp_data.get('flow_count', 0)
                udp_packets = udp_data.get('packet_count', 0)
                udp_bytes = udp_data.get('byte_count', 0)
                self._update_traffic_rrd(self.udp_rrd, timestamp, udp_flows, udp_packets, udp_bytes)

                # ICMP Traffic
                icmp_data = stats.get('icmp', {})
                icmp_flows = icmp_data.get('flow_count', 0)
                icmp_packets = icmp_data.get('packet_count', 0)
                icmp_bytes = icmp_data.get('byte_count', 0)
                self._update_traffic_rrd(self.icmp_rrd, timestamp, icmp_flows, icmp_packets, icmp_bytes)

                # Total Alerts (sum from all protocols)
                total_alerts = tcp_data.get('alert_count', 0) + udp_data.get('alert_count', 0) + icmp_data.get('alert_count', 0)
                self._update_rrd(self.alerts_rrd, timestamp, total_alerts)

                return {
                    'success': True,
                    'stats': {
                        'tcp': {'flows': tcp_flows, 'packets': tcp_packets, 'bytes': tcp_bytes},
                        'udp': {'flows': udp_flows, 'packets': udp_packets, 'bytes': udp_bytes},
                        'icmp': {'flows': icmp_flows, 'packets': icmp_packets, 'bytes': icmp_bytes},
                        'alerts': total_alerts
                    }
                }
            else:
                return {'success': False, 'message': 'No database manager configured'}

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
        """Update a single RRD database (for alerts) using Python rrdtool"""
        if not self.enabled:
            return

        try:
            rrdtool.update(rrd_file, f'{timestamp}:{value}')
        except Exception as e:
            print(f"Error updating RRD {rrd_file}: {e}")

    def _update_traffic_rrd(self, rrd_file: str, timestamp: str, flows: int, packets: int, bytes_count: int):
        """Update a traffic RRD database using Python rrdtool"""
        if not self.enabled:
            return

        try:
            rrdtool.update(rrd_file, f'{timestamp}:{flows}:{packets}:{bytes_count}')
        except Exception as e:
            print(f"Error updating traffic RRD {rrd_file}: {e}")

    def generate_graph(self, metric: str = 'tcp', timespan: str = '1h') -> Dict[str, Any]:
        """Generate a graph for a specific metric using Python rrdtool"""
        if not self.enabled:
            return {'success': False, 'message': 'RRDtool not available'}

        rrd_files = {
            'tcp': self.tcp_rrd,
            'udp': self.udp_rrd,
            'icmp': self.icmp_rrd,
            'alerts': self.alerts_rrd
        }

        rrd_file = rrd_files.get(metric, self.tcp_rrd)

        if not os.path.exists(rrd_file):
            return {'success': False, 'message': 'RRD file not found'}

        # Generate graph
        graph_file = os.path.join(self.rrd_directory, f'{metric}_{timespan}.png')

        try:
            # Map timespan to seconds
            timespan_map = {
                '5m': 300,
                '15m': 900,
                '30m': 1800,
                '1h': 3600,
                '6h': 21600,
                '24h': 86400,
                '7d': 604800,
                '30d': 2592000
            }

            seconds = timespan_map.get(timespan, 3600)

            if metric == 'alerts':
                # Alerts graph
                rrdtool.graph(
                    graph_file,
                    '--start', f'-{seconds}',
                    '--end', 'now',
                    '--width', '800',
                    '--height', '300',
                    '--title', f'{metric.upper()} - Last {timespan}',
                    '--vertical-label', 'Alerts/min',
                    f'DEF:alerts={rrd_file}:alerts:AVERAGE',
                    'LINE2:alerts#FF0000:Alerts',
                    'GPRINT:alerts:LAST:Current\\:%8.0lf',
                    'GPRINT:alerts:AVERAGE:Average\\:%8.0lf',
                    'GPRINT:alerts:MAX:Maximum\\:%8.0lf'
                )
            else:
                # Traffic graph (flows, packets, bytes)
                rrdtool.graph(
                    graph_file,
                    '--start', f'-{seconds}',
                    '--end', 'now',
                    '--width', '800',
                    '--height', '300',
                    '--title', f'{metric.upper()} Traffic - Last {timespan}',
                    '--vertical-label', 'Count',
                    f'DEF:flows={rrd_file}:flows:AVERAGE',
                    f'DEF:packets={rrd_file}:packets:AVERAGE',
                    f'DEF:bytes={rrd_file}:bytes:AVERAGE',
                    'LINE2:flows#0000FF:Flows',
                    'GPRINT:flows:LAST:Current\\:%8.0lf',
                    'GPRINT:flows:AVERAGE:Average\\:%8.0lf',
                    'GPRINT:flows:MAX:Maximum\\:%8.0lf\\n',
                    'LINE2:packets#00FF00:Packets',
                    'GPRINT:packets:LAST:Current\\:%8.0lf',
                    'GPRINT:packets:AVERAGE:Average\\:%8.0lf',
                    'GPRINT:packets:MAX:Maximum\\:%8.0lf\\n',
                    'LINE2:bytes#FF00FF:Bytes',
                    'GPRINT:bytes:LAST:Current\\:%8.0lf',
                    'GPRINT:bytes:AVERAGE:Average\\:%8.0lf',
                    'GPRINT:bytes:MAX:Maximum\\:%8.0lf'
                )

            return {'success': True, 'graph_path': graph_file}

        except Exception as e:
            return {'success': False, 'message': f'Error generating graph: {e}'}

    def get_graph_data(self, metric: str = 'tcp', timespan: str = '1h') -> Dict[str, Any]:
        """Get data points for graphing using Python rrdtool"""
        if not self.enabled:
            return {'success': False, 'message': 'RRDtool not available'}

        rrd_files = {
            'tcp': self.tcp_rrd,
            'udp': self.udp_rrd,
            'icmp': self.icmp_rrd,
            'alerts': self.alerts_rrd
        }

        rrd_file = rrd_files.get(metric, self.tcp_rrd)

        if not os.path.exists(rrd_file):
            return {'success': False, 'message': 'RRD file not found'}

        try:
            timespan_map = {
                '5m': 300,
                '15m': 900,
                '30m': 1800,
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
