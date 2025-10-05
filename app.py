from flask import Flask, render_template, request, jsonify, send_file
from binary import SuricataFrontendController, SuricataRRDManager, DatabaseManager
from config import Config
import threading
import time
import os

app = Flask(__name__)

# Ensure application directories exist
try:
    os.makedirs(Config.APP_DATA_DIR, exist_ok=True)
    os.makedirs(Config.APP_LOG_DIR, exist_ok=True)
    print(f"✓ Application directories initialized:")
    print(f"  - Data: {Config.APP_DATA_DIR}")
    print(f"  - Logs: {Config.APP_LOG_DIR}")
except Exception as e:
    print(f"⚠ Warning: Could not create application directories: {e}")

# Initialize Suricata Frontend Controller with config
controller = SuricataFrontendController(
    binary_path=Config.SURICATA_BINARY_PATH,
    config_path=Config.SURICATA_CONFIG_PATH,
    rules_directory=Config.SURICATA_RULES_DIR,
    log_directory=Config.SURICATA_LOG_DIR
)

# Initialize RRD Manager
rrd_manager = SuricataRRDManager(
    rrd_directory=Config.RRD_DIR,
    log_directory=Config.SURICATA_LOG_DIR
)

# Initialize Database Manager
db_config = {}
if Config.DB_TYPE == 'mysql':
    db_config = {
        'host': Config.DB_HOST,
        'port': Config.DB_PORT,
        'user': Config.DB_USER,
        'password': Config.DB_PASSWORD,
        'database': Config.DB_NAME,
    }
elif Config.DB_TYPE == 'postgresql':
    db_config = {
        'host': Config.DB_HOST,
        'port': Config.DB_PORT,
        'user': Config.DB_USER,
        'password': Config.DB_PASSWORD,
        'database': Config.DB_NAME,
    }
else:
    raise ValueError(f"Unsupported database type: {Config.DB_TYPE}")

db_manager = DatabaseManager(db_type=Config.DB_TYPE, db_config=db_config)

# Background thread to update RRD metrics
def update_rrd_metrics():
    while True:
        try:
            rrd_manager.update_metrics()
        except Exception as e:
            print(f"Error updating RRD metrics: {e}")
        time.sleep(60)  # Update every minute

# Background thread to sync alerts from eve.json to database
def sync_alerts_to_database():
    """Import alerts from eve.json to database"""
    import json
    import math
    from datetime import datetime

    last_position = 0

    while True:
        try:
            eve_log_path = f"{Config.SURICATA_LOG_DIR}/eve.json"

            try:
                with open(eve_log_path, 'r') as f:
                    # Seek to last position
                    f.seek(last_position)

                    for line in f:
                        try:
                            event = json.loads(line.strip())

                            # Only process alert events
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

                                db_manager.add_alert(alert_data)

                        except json.JSONDecodeError:
                            continue

                    # Update position
                    last_position = f.tell()

            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"[ALERT-SYNC] Error reading eve.json: {e}")

        except Exception as e:
            print(f"[ALERT-SYNC] Error: {e}")

        time.sleep(5)  # Check every 5 seconds

# Statistics synchronization thread
def sync_stats_to_database():
    """Import statistics from Suricata stats.log into the database."""
    import json
    import math
    from datetime import datetime

    stats_log_path = os.path.join(Config.SURICATA_LOG_DIR, 'stats.log')
    last_position = 0

    def iter_metrics(prefix: str, payload):
        if isinstance(payload, dict):
            for key, value in payload.items():
                new_prefix = f"{prefix}.{key}" if prefix else key
                yield from iter_metrics(new_prefix, value)
        elif isinstance(payload, list):
            for index, value in enumerate(payload):
                list_prefix = f"{prefix}.{index}" if prefix else str(index)
                yield from iter_metrics(list_prefix, value)
        elif isinstance(payload, (int, float)):
            yield prefix, float(payload)

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

                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    stats_payload = None
                    if isinstance(event, dict):
                        if isinstance(event.get('stats'), dict):
                            stats_payload = event.get('stats')
                        elif isinstance(event.get('event'), dict) and isinstance(event['event'].get('stats'), dict):
                            stats_payload = event['event']['stats']

                    if not isinstance(stats_payload, dict):
                        continue

                    timestamp_value = event.get('timestamp') or event.get('time')
                    try:
                        metric_timestamp = datetime.fromisoformat(timestamp_value.replace('Z', '+00:00')) if timestamp_value else datetime.utcnow()
                    except (ValueError, AttributeError):
                        metric_timestamp = datetime.utcnow()

                    metric_type = event.get('event_type', 'stats')

                    for metric_name, metric_value in iter_metrics('', stats_payload):
                        if not metric_name:
                            continue
                        if not math.isfinite(metric_value):
                            continue
                        category = metric_name.split('.', 1)[0]

                        db_manager.add_statistic({
                            'timestamp': metric_timestamp,
                            'metric_name': metric_name,
                            'metric_value': metric_value,
                            'metric_type': metric_type,
                            'category': category,
                            'extra_data': event,
                        })

                last_position = stats_file.tell()

        except FileNotFoundError:
            last_position = 0
        except Exception as err:
            print(f"[STATS-SYNC] Error processing stats.log: {err}")

        time.sleep(10)


# Database retention cleanup thread
def database_retention_worker():
    """Periodically purge old records based on configured retention."""
    cleanup_interval = 3600  # one hour

    while True:
        try:
            retention_days = getattr(Config, 'DB_RETENTION_DAYS', 0)
            if retention_days and retention_days > 0:
                result = db_manager.cleanup_old_data(days=retention_days)
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


# Auto-restart monitor thread
def auto_restart_monitor():
    """Monitor Suricata and auto-restart if crashed"""
    retry_count = 0
    last_status = None

    while True:
        try:
            if Config.AUTO_RESTART_ENABLED:
                status = controller.get_status()
                is_running = status.get('running', False)

                # Check if Suricata crashed
                if not is_running and last_status and last_status.get('running', False):
                    print(f"[AUTO-RESTART] Suricata crashed! Retry count: {retry_count}/{Config.AUTO_RESTART_MAX_RETRIES}")

                    if retry_count < Config.AUTO_RESTART_MAX_RETRIES:
                        print("[AUTO-RESTART] Attempting to restart Suricata...")
                        result = controller.restart()

                        if result.get('success'):
                            print("[AUTO-RESTART] Suricata restarted successfully")
                            retry_count += 1
                        else:
                            print(f"[AUTO-RESTART] Failed to restart: {result.get('message')}")
                    else:
                        print(f"[AUTO-RESTART] Max retries ({Config.AUTO_RESTART_MAX_RETRIES}) reached. Stopping auto-restart.")

                # Reset retry count if running
                if is_running:
                    retry_count = 0

                last_status = status

        except Exception as e:
            print(f"[AUTO-RESTART] Error in monitor: {e}")

        time.sleep(Config.AUTO_RESTART_CHECK_INTERVAL)

# Start background threads
rrd_thread = threading.Thread(target=update_rrd_metrics, daemon=True)
rrd_thread.start()

# Start alert sync thread
alert_sync_thread = threading.Thread(target=sync_alerts_to_database, daemon=True)
alert_sync_thread.start()
print("[ALERT-SYNC] Alert synchronization enabled - Monitoring eve.json")

# Start statistics sync thread
stats_sync_thread = threading.Thread(target=sync_stats_to_database, daemon=True)
stats_sync_thread.start()
print("[STATS-SYNC] Statistics synchronization enabled - Monitoring stats.log")

if Config.DB_RETENTION_DAYS > 0:
    cleanup_thread = threading.Thread(target=database_retention_worker, daemon=True)
    cleanup_thread.start()
    print(f"[DB-CLEANUP] Retention worker active (retention: {Config.DB_RETENTION_DAYS} days)")
else:
    print("[DB-CLEANUP] Retention worker disabled (DB_RETENTION_DAYS=0)")

if Config.AUTO_RESTART_ENABLED:
    restart_thread = threading.Thread(target=auto_restart_monitor, daemon=True)
    restart_thread.start()
    print(f"[AUTO-RESTART] Monitoring enabled (max retries: {Config.AUTO_RESTART_MAX_RETRIES}, check interval: {Config.AUTO_RESTART_CHECK_INTERVAL}s)")

@app.route('/')
def index():
    status = controller.get_status()
    return render_template('index.html', status=status)

@app.route('/api/status')
def api_status():
    return jsonify(controller.get_status())

@app.route('/api/start', methods=['POST'])
def api_start():
    return jsonify(controller.start())

@app.route('/api/stop', methods=['POST'])
def api_stop():
    return jsonify(controller.stop())

@app.route('/api/restart', methods=['POST'])
def api_restart():
    return jsonify(controller.restart())

@app.route('/api/reload-rules', methods=['POST'])
def api_reload_rules():
    return jsonify(controller.reload_rules())

@app.route('/logs')
def logs():
    return render_template('logs.html')

@app.route('/api/logs')
def api_logs():
    try:
        # Read directly from eve.json
        eve_logs = controller.log_manager.get_eve_log(100)

        if eve_logs:
            # Convert eve.json to readable format
            formatted_logs = []
            for log in eve_logs:
                event_type = log.get('event_type', 'unknown')
                timestamp = log.get('timestamp', '')

                if event_type == 'alert':
                    alert = log.get('alert', {})
                    signature = alert.get('signature', 'Unknown')
                    severity = alert.get('severity', 0)
                    src_ip = log.get('src_ip', '')
                    dest_ip = log.get('dest_ip', '')
                    proto = log.get('proto', '')
                    formatted_logs.append(f"[ALERT] {timestamp} - {signature} | {src_ip} -> {dest_ip} [{proto}] (Severity: {severity})")
                elif event_type == 'stats':
                    formatted_logs.append(f"[STATS] {timestamp} - Statistics Update")
                elif event_type == 'flow':
                    src_ip = log.get('src_ip', '')
                    src_port = log.get('src_port', '')
                    dest_ip = log.get('dest_ip', '')
                    dest_port = log.get('dest_port', '')
                    proto = log.get('proto', '')

                    # Detect common services by port
                    service = ''
                    if dest_port == 22 or src_port == 22:
                        service = 'SSH'
                    elif dest_port == 80 or src_port == 80:
                        service = 'HTTP'
                    elif dest_port == 443 or src_port == 443:
                        service = 'HTTPS'
                    elif dest_port == 53 or src_port == 53:
                        service = 'DNS'
                    elif dest_port == 67 or dest_port == 68 or src_port == 67 or src_port == 68:
                        service = 'DHCP'
                    elif dest_port == 21 or src_port == 21:
                        service = 'FTP'
                    elif dest_port == 25 or src_port == 25:
                        service = 'SMTP'

                    service_str = f" ({service})" if service else ''
                    formatted_logs.append(f"[FLOW] {timestamp} - {src_ip}:{src_port} -> {dest_ip}:{dest_port} [{proto}]{service_str}")
                elif event_type == 'http':
                    http = log.get('http', {})
                    hostname = http.get('hostname', '')
                    url = http.get('url', '')
                    formatted_logs.append(f"[HTTP] {timestamp} - {hostname}{url}")
                elif event_type == 'dns':
                    dns = log.get('dns', {})
                    query = dns.get('rrname', '')
                    formatted_logs.append(f"[DNS] {timestamp} - Query: {query}")
                elif event_type == 'ssh':
                    ssh = log.get('ssh', {})
                    src_ip = log.get('src_ip', '')
                    dest_ip = log.get('dest_ip', '')
                    formatted_logs.append(f"[SSH] {timestamp} - {src_ip} -> {dest_ip}")
                elif event_type == 'tls':
                    tls = log.get('tls', {})
                    sni = tls.get('sni', '')
                    formatted_logs.append(f"[TLS] {timestamp} - SNI: {sni}")
                else:
                    formatted_logs.append(f"[{event_type.upper()}] {timestamp}")

            return jsonify({'logs': formatted_logs})
        else:
            return jsonify({'logs': []})

    except Exception as e:
        return jsonify({'error': str(e), 'logs': []})

@app.route('/rules')
def rules():
    return render_template('rules.html')

@app.route('/api/rules')
def api_rules():
    try:
        rules = controller.rule_manager.get_rule_files()
        return jsonify({'rules': rules})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/config')
def config():
    return render_template('config.html')

@app.route('/services')
def services():
    status = controller.get_status()
    return render_template('services.html', status=status)

@app.route('/monitor')
def monitor():
    return render_template('monitor.html')

@app.route('/api/config')
def api_config():
    try:
        config_data = controller.config.load()
        # Convert config data back to YAML string for display
        import yaml
        config_string = yaml.dump(config_data, default_flow_style=False, indent=2)
        return jsonify({'config': config_string})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/config', methods=['POST'])
def api_save_config():
    try:
        config_content = request.json.get('config', '')
        # Parse YAML and save
        import yaml
        config_data = yaml.safe_load(config_content)
        controller.config.save(config_data)
        return jsonify({'success': True, 'message': 'Configuration saved successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/monitor/data')
def api_monitor_data():
    metric = request.args.get('metric', 'ssh')
    timespan = request.args.get('timespan', '1h')
    result = rrd_manager.get_graph_data(metric, timespan)
    return jsonify(result)

@app.route('/api/monitor/graph/<metric>/<timespan>')
def api_monitor_graph(metric, timespan):
    result = rrd_manager.generate_graph(metric, timespan)
    if result.get('success'):
        return send_file(result['graph_path'], mimetype='image/png')
    else:
        return jsonify(result), 400

@app.route('/api/database/info')
def api_database_info():
    return jsonify(db_manager.get_db_info())

@app.route('/api/database/alerts')
def api_database_alerts():
    limit = request.args.get('limit', 100, type=int)
    category = request.args.get('category', None)
    protocol = request.args.get('protocol', None)

    # Get alerts with filter
    alerts = db_manager.get_alerts(limit=limit, category=category)

    # Additional filter by protocol if specified
    if protocol:
        alerts = [alert for alert in alerts if alert.protocol and alert.protocol.upper() == protocol.upper()]

    return jsonify({'alerts': [alert.to_dict() for alert in alerts]})

@app.route('/api/database/stats')
def api_database_stats():
    stats = db_manager.get_latest_stats()
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=Config.FLASK_DEBUG, host=Config.FLASK_HOST, port=Config.FLASK_PORT, use_debugger=False, use_reloader=True)