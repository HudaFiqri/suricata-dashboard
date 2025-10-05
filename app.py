from flask import Flask, render_template, request, jsonify, send_file
from binary import SuricataFrontendController, SuricataRRDManager, DatabaseManager
from config import Config
import threading
import time

app = Flask(__name__)

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
if Config.DB_TYPE == 'sqlite':
    db_config = {'path': Config.DB_PATH}
elif Config.DB_TYPE == 'mysql':
    db_config = {
        'host': Config.DB_HOST,
        'port': Config.DB_PORT,
        'user': Config.DB_USER,
        'password': Config.DB_PASSWORD,
        'database': Config.DB_NAME
    }
elif Config.DB_TYPE == 'postgresql':
    db_config = {
        'host': Config.DB_HOST,
        'port': Config.DB_PORT,
        'user': Config.DB_USER,
        'password': Config.DB_PASSWORD,
        'database': Config.DB_NAME
    }

db_manager = DatabaseManager(db_type=Config.DB_TYPE, db_config=db_config)

# Background thread to update RRD metrics
def update_rrd_metrics():
    while True:
        try:
            rrd_manager.update_metrics()
        except Exception as e:
            print(f"Error updating RRD metrics: {e}")
        time.sleep(60)  # Update every minute

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
        # Try to get fast.log first
        logs = controller.log_manager.get_fast_log(100)

        # If empty, try eve.json
        if not logs:
            eve_logs = controller.log_manager.get_eve_log(100)
            if eve_logs:
                # Convert eve.json to readable format
                logs = [f"[{log.get('event_type', 'unknown')}] {log.get('timestamp', '')} - {log.get('alert', {}).get('signature', str(log))}" for log in eve_logs]

        return jsonify({'logs': logs if logs else []})
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
    alerts = db_manager.get_alerts(limit=limit, category=category)
    return jsonify({'alerts': [alert.to_dict() for alert in alerts]})

@app.route('/api/database/stats')
def api_database_stats():
    stats = db_manager.get_latest_stats()
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=Config.FLASK_DEBUG, host=Config.FLASK_HOST, port=Config.FLASK_PORT, use_debugger=False, use_reloader=True)