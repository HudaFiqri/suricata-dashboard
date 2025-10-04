from flask import Flask, render_template, request, jsonify, send_file
from binary import SuricataFrontendController, SuricataRRDManager
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
    log_directory=Config.SURICATA_LOG_DIR
)

# Background thread to update RRD metrics
def update_rrd_metrics():
    while True:
        try:
            rrd_manager.update_metrics()
        except Exception as e:
            print(f"Error updating RRD metrics: {e}")
        time.sleep(60)  # Update every minute

# Start background thread
rrd_thread = threading.Thread(target=update_rrd_metrics, daemon=True)
rrd_thread.start()

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
        logs = controller.log_manager.get_fast_log(100)
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'error': str(e)})

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

if __name__ == '__main__':
    app.run(debug=Config.FLASK_DEBUG, host=Config.FLASK_HOST, port=Config.FLASK_PORT)