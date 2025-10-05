"""
Web Routes - HTML page routes
"""
from flask import render_template


class WebRoutes:
    """Web routes for HTML pages"""

    def __init__(self, app, controller, config):
        self.app = app
        self.controller = controller
        self.config = config
        self._register_routes()
        self._register_context_processor()

    def _register_routes(self):
        """Register all web routes"""
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/monitoring', 'monitoring', self.monitoring_dashboard)
        self.app.add_url_rule('/monitor', 'monitor', self.monitor)
        self.app.add_url_rule('/rrd', 'rrd', self.rrd_graphs)
        self.app.add_url_rule('/logs', 'logs', self.logs)
        self.app.add_url_rule('/rules', 'rules', self.rules)
        self.app.add_url_rule('/config', 'config', self.config_page)
        self.app.add_url_rule('/services', 'services', self.services)

    def _register_context_processor(self):
        """Register template context processor for global variables"""
        @self.app.context_processor
        def inject_globals():
            return {
                'dashboard_name': self.config.DASHBOARD_NAME
            }

    def index(self):
        """Home page"""
        status = self.controller.get_status()
        return render_template('index.html', status=status)

    def monitoring_dashboard(self):
        """Monitoring dashboard page"""
        return render_template('monitoring.html')

    def logs(self):
        """Logs page"""
        return render_template('logs.html')

    def rules(self):
        """Rules page"""
        return render_template('rules.html')

    def config_page(self):
        """Config page"""
        return render_template('config.html')

    def services(self):
        """Services page"""
        status = self.controller.get_status()
        return render_template('services.html', status=status)

    def monitor(self):
        """Monitor page"""
        return render_template('monitor.html')

    def rrd_graphs(self):
        """RRD Graphs page"""
        return render_template('rrd.html')
