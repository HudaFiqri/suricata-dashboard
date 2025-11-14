/**
 * Outputs Configuration Module
 * Extracted from config.html
 */

const OutputsConfig = (function() {
    'use strict';

let outputsConfig = {};

function openOutputsModal() {
    $('#outputs-error').addClass('d-none').text('');
    $('#outputs-success').addClass('d-none').text('');
    loadOutputsConfig();
    $('#outputsModal').modal('show');
}

function loadOutputsConfig() {
    $('#outputs-container').html('<p class="text-muted"><i class="fas fa-spinner fa-spin"></i> Loading outputs...</p>');

    $.get('/api/suricata-config/outputs', function(data) {
        if (data.success) {
            outputsConfig = data.outputs || {};

            // Show warning if using defaults
            if (data.warning) {
                $('#outputs-container').html('<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> ' + data.warning + '</div>');
                setTimeout(function() {
                    renderOutputs(outputsConfig);
                }, 1000);
            } else {
                renderOutputs(outputsConfig);
            }
        } else {
            $('#outputs-container').html('<div class="alert alert-danger"><i class="fas fa-times-circle"></i> Failed to load outputs: ' + data.message + '</div>');
        }
    }).fail(function(xhr) {
        const message = (xhr.responseJSON && xhr.responseJSON.message) || 'Failed to connect to API';
        $('#outputs-container').html('<div class="alert alert-danger"><i class="fas fa-times-circle"></i> ' + message + '</div>');
    });
}

function renderOutputs(outputs) {
    let html = '<div class="row">';

    // Common outputs with descriptions
    const outputDefs = {
        'eve-log': {
            name: 'EVE JSON Log',
            description: 'Main event log in JSON format',
            icon: 'file-alt'
        },
        'fast': {
            name: 'Fast Alert Log',
            description: 'Simple one-line alert format',
            icon: 'bolt'
        },
        'stats': {
            name: 'Statistics Log',
            description: 'Performance and traffic statistics',
            icon: 'chart-bar'
        },
        'unified2-alert': {
            name: 'Unified2 Alert',
            description: 'Legacy alert format',
            icon: 'database'
        },
        'http-log': {
            name: 'HTTP Log',
            description: 'Dedicated HTTP transaction log',
            icon: 'globe'
        },
        'tls-log': {
            name: 'TLS Log',
            description: 'TLS/SSL handshake details',
            icon: 'lock'
        },
        'dns-log': {
            name: 'DNS Log',
            description: 'DNS queries and responses',
            icon: 'network-wired'
        },
        'pcap-log': {
            name: 'PCAP Log',
            description: 'Full packet capture',
            icon: 'save'
        }
    };

    Object.keys(outputDefs).forEach(function(outputKey) {
        const def = outputDefs[outputKey];
        const config = outputs[outputKey] || {};
        const enabled = config.enabled === 'yes' || config.enabled === true;

        html += '<div class="col-md-6 mb-3">';
        html += '  <div class="card' + (enabled ? ' border-success' : '') + '">';
        html += '    <div class="card-body">';
        html += '      <div class="form-check form-switch">';
        html += '        <input class="form-check-input output-toggle" type="checkbox" id="output-' + outputKey + '" data-output="' + outputKey + '"' + (enabled ? ' checked' : '') + '>';
        html += '        <label class="form-check-label" for="output-' + outputKey + '">';
        html += '          <i class="fas fa-' + def.icon + ' me-2"></i>';
        html += '          <strong>' + def.name + '</strong>';
        html += '        </label>';
        html += '      </div>';
        html += '      <small class="text-muted">' + def.description + '</small>';
        html += '    </div>';
        html += '  </div>';
        html += '</div>';
    });

    html += '</div>';

    $('#outputs-container').html(html);
}

function saveOutputsConfig() {
    const $btn = $('#save-outputs-btn');
    const originalHtml = $btn.html();
    $btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-2"></span>Saving...');

    $('#outputs-error').addClass('d-none').text('');
    $('#outputs-success').addClass('d-none').text('');

    // Collect output states
    const outputs = {};
    $('.output-toggle').each(function() {
        const outputName = $(this).data('output');
        const enabled = $(this).is(':checked');
        outputs[outputName] = { enabled: enabled };
    });

    $.ajax({
        url: '/api/suricata-config/outputs',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ outputs: outputs }),
        success: function(data) {
            if (data.success) {
                $('#outputs-success').removeClass('d-none').text(data.message);
                setTimeout(function() {
                    $('#outputsModal').modal('hide');
                }, 1500);
            } else {
                $('#outputs-error').removeClass('d-none').text(data.message);
            }
        },
        error: function(xhr) {
            const message = (xhr.responseJSON && xhr.responseJSON.message) || 'Failed to save configuration';
            $('#outputs-error').removeClass('d-none').text(message);
        },
        complete: function() {
            $btn.prop('disabled', false).html(originalHtml);
        }
    });
}

$('#save-outputs-btn').click(saveOutputsConfig);

// Logging Modal Functions
function openLoggingModal() {
    $('#loggingModal').modal('show');
    loadLoggingConfig();
}

function loadLoggingConfig() {
    $('#logging-error').addClass('d-none');
    $('#logging-success').addClass('d-none');
    $('#logging-container').html('<div class="text-center"><i class="fas fa-spinner fa-spin fa-2x"></i><p class="mt-2">Loading logging configuration...</p></div>');

    $.ajax({
        url: '/api/suricata-config/logging',
        method: 'GET',
        success: function(data) {
            if (data.success) {
                if (data.warning) {
                    $('#logging-error').removeClass('d-none').removeClass('alert-danger').addClass('alert-warning').text(data.warning);
                }
                renderLogging(data.logging || data.config || {});
            } else {
                $('#logging-error').removeClass('d-none').text(data.message || 'Failed to load logging configuration');
                $('#logging-container').html('');
            }
        },
        error: function(xhr) {
            const message = (xhr.responseJSON && xhr.responseJSON.message) || 'Failed to load logging configuration';
            $('#logging-error').removeClass('d-none').text(message);
            $('#logging-container').html('');
        }
    });
}

function renderLogging(config) {
    let html = '<div class="row">';

    // Default log level
    html += '<div class="col-md-6 mb-3">';
    html += '<label class="form-label"><i class="fas fa-level-up-alt"></i> Default Log Level</label>';
    html += '<select class="form-select" id="logging-default-level">';
    const levels = ['error', 'warning', 'notice', 'info', 'debug'];
    const currentLevel = config['default-log-level'] || 'notice';
    levels.forEach(function(level) {
        const selected = level === currentLevel ? ' selected' : '';
        html += '<option value="' + level + '"' + selected + '>' + level.toUpperCase() + '</option>';
    });
    html += '</select>';
    html += '</div>';

    // Default log format
    html += '<div class="col-md-6 mb-3">';
    html += '<label class="form-label"><i class="fas fa-file-code"></i> Default Log Format</label>';
    html += '<input type="text" class="form-control" id="logging-default-format" value="' + (config['default-log-format'] || '[%i] %t - (%f:%l) <%d> (%n) -- %m') + '">';
    html += '</div>';

    html += '</div>';

    // Outputs section
    html += '<h6 class="mt-3 mb-3"><i class="fas fa-terminal"></i> Logging Outputs</h6>';
    html += '<div class="row">';

    const outputs = config.outputs || [];
    const outputTypes = ['console', 'file', 'syslog'];

    outputTypes.forEach(function(outputType) {
        let outputConfig = null;
        outputs.forEach(function(out) {
            if (out[outputType]) {
                outputConfig = out[outputType];
            }
        });

        const enabled = outputConfig && (outputConfig.enabled === 'yes' || outputConfig.enabled === true);

        html += '<div class="col-md-4 mb-3">';
        html += '<div class="card h-100">';
        html += '<div class="card-body">';
        html += '<h6 class="card-title">';
        html += '<div class="form-check form-switch">';
        html += '<input class="form-check-input logging-output-toggle" type="checkbox" data-output="' + outputType + '"' + (enabled ? ' checked' : '') + '>';
        html += '<label class="form-check-label text-capitalize"><strong>' + outputType + '</strong></label>';
        html += '</div>';
        html += '</h6>';

        // Output-specific settings
        if (outputType === 'file') {
            const filename = (outputConfig && outputConfig.filename) || '/var/log/suricata/suricata.log';
            html += '<div class="mt-2"><label class="form-label small">Filename</label>';
            html += '<input type="text" class="form-control form-control-sm" id="logging-file-filename" value="' + filename + '"></div>';
        } else if (outputType === 'syslog') {
            const facility = (outputConfig && outputConfig.facility) || 'local5';
            html += '<div class="mt-2"><label class="form-label small">Facility</label>';
            html += '<input type="text" class="form-control form-control-sm" id="logging-syslog-facility" value="' + facility + '"></div>';
        }

        html += '</div></div></div>';
    });

    html += '</div>';

    $('#logging-container').html(html);
}

function saveLoggingConfig() {
    $('#logging-error').addClass('d-none');
    $('#logging-success').addClass('d-none');

    const $btn = $('#save-logging-btn');
    const originalHtml = $btn.html();
    $btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Saving...');

    const config = {
        'default-log-level': $('#logging-default-level').val(),
        'default-log-format': $('#logging-default-format').val(),
        outputs: []
    };

    $('.logging-output-toggle').each(function() {
        const $toggle = $(this);
        const outputType = $toggle.data('output');
        const enabled = $toggle.is(':checked');

        let outputConfig = {
            enabled: enabled ? 'yes' : 'no'
        };

        if (outputType === 'file') {
            outputConfig.filename = $('#logging-file-filename').val();
        } else if (outputType === 'syslog') {
            outputConfig.facility = $('#logging-syslog-facility').val();
        }

        const output = {};
        output[outputType] = outputConfig;
        config.outputs.push(output);
    });

    $.ajax({
        url: '/api/suricata-config/logging',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ logging: config }),
        success: function(data) {
            if (data.success) {
                $('#logging-success').removeClass('d-none').text(data.message);
                setTimeout(function() {
                    $('#loggingModal').modal('hide');
                }, 1500);
            } else {
                $('#logging-error').removeClass('d-none').text(data.message);
            }
        },
        error: function(xhr) {
            const message = (xhr.responseJSON && xhr.responseJSON.message) || 'Failed to save configuration';
            $('#logging-error').removeClass('d-none').text(message);
        },
        complete: function() {
            $btn.prop('disabled', false).html(originalHtml);
        }
    });
}

$('#save-logging-btn').click(saveLoggingConfig);

// Detection Modal Functions
function openDetectionModal() {
    $('#detectionModal').modal('show');
    loadDetectionConfig();
}

function loadDetectionConfig() {
    $('#detection-error').addClass('d-none');
    $('#detection-success').addClass('d-none');
    $('#detection-container').html('<div class="text-center"><i class="fas fa-spinner fa-spin fa-2x"></i><p class="mt-2">Loading detection configuration...</p></div>');

    $.ajax({
        url: '/api/suricata-config/detection',
        method: 'GET',
        success: function(data) {
            if (data.success) {
                if (data.warning) {
                    $('#detection-error').removeClass('d-none').removeClass('alert-danger').addClass('alert-warning').text(data.warning);
                }
                renderDetection(data.detection || data.config || {});
            } else {
                $('#detection-error').removeClass('d-none').text(data.message || 'Failed to load detection configuration');
                $('#detection-container').html('');
            }
        },
        error: function(xhr) {
            const message = (xhr.responseJSON && xhr.responseJSON.message) || 'Failed to load detection configuration';
            $('#detection-error').removeClass('d-none').text(message);
            $('#detection-container').html('');
        }
    });
}

function renderDetection(config) {
    let html = '<div class="row">';

    // Detection profile
    html += '<div class="col-md-6 mb-3">';
    html += '<label class="form-label"><i class="fas fa-shield-alt"></i> Detection Profile</label>';
    html += '<select class="form-select" id="detection-profile">';
    const profiles = ['low', 'medium', 'high', 'custom'];
    const currentProfile = (config.detect && config.detect.profile) || 'medium';
    profiles.forEach(function(profile) {
        const selected = profile === currentProfile ? ' selected' : '';
        html += '<option value="' + profile + '"' + selected + '>' + profile.toUpperCase() + '</option>';
    });
    html += '</select>';
    html += '<small class="text-muted">Detection profile determines inspection depth</small>';
    html += '</div>';

    // MPM Algorithm
    html += '<div class="col-md-6 mb-3">';
    html += '<label class="form-label"><i class="fas fa-search"></i> Pattern Matching Algorithm</label>';
    html += '<select class="form-select" id="detection-mpm-algo">';
    const algos = ['auto', 'ac', 'ac-bs', 'hs'];
    const currentAlgo = config['mpm-algo'] || 'auto';
    algos.forEach(function(algo) {
        const selected = algo === currentAlgo ? ' selected' : '';
        html += '<option value="' + algo + '"' + selected + '>' + algo.toUpperCase() + '</option>';
    });
    html += '</select>';
    html += '<small class="text-muted">Pattern matching algorithm (auto recommended)</small>';
    html += '</div>';

    html += '</div>';

    // Threading section
    if (config.threading) {
        html += '<h6 class="mt-3 mb-3"><i class="fas fa-microchip"></i> Threading Configuration</h6>';
        html += '<div class="row">';

        html += '<div class="col-md-6 mb-3">';
        html += '<label class="form-label">Detect Threads</label>';
        html += '<input type="number" class="form-control" id="detection-detect-threads" value="' + (config.threading['detect-thread-ratio'] || 1.5) + '" step="0.5" min="0.5">';
        html += '<small class="text-muted">Detection thread ratio (multiplier of CPU cores)</small>';
        html += '</div>';

        html += '</div>';
    }

    // Profiling section
    html += '<h6 class="mt-3 mb-3"><i class="fas fa-chart-line"></i> Profiling</h6>';
    html += '<div class="row">';

    const profilingEnabled = config.profiling && (config.profiling.rules && config.profiling.rules.enabled === 'yes');
    html += '<div class="col-md-12 mb-3">';
    html += '<div class="form-check form-switch">';
    html += '<input class="form-check-input" type="checkbox" id="detection-profiling-enabled"' + (profilingEnabled ? ' checked' : '') + '>';
    html += '<label class="form-check-label">Enable Rule Profiling</label>';
    html += '</div>';
    html += '<small class="text-muted">Profile rule performance (may impact performance)</small>';
    html += '</div>';

    html += '</div>';

    $('#detection-container').html(html);
}

function saveDetectionConfig() {
    $('#detection-error').addClass('d-none');
    $('#detection-success').addClass('d-none');

    const $btn = $('#save-detection-btn');
    const originalHtml = $btn.html();
    $btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Saving...');

    const config = {
        detect: {
            profile: $('#detection-profile').val()
        },
        'mpm-algo': $('#detection-mpm-algo').val(),
        threading: {
            'detect-thread-ratio': parseFloat($('#detection-detect-threads').val())
        },
        profiling: {
            rules: {
                enabled: $('#detection-profiling-enabled').is(':checked') ? 'yes' : 'no',
                filename: 'rule_perf.log',
                append: 'yes'
            }
        }
    };

    $.ajax({
        url: '/api/suricata-config/detection',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ detection: config }),
        success: function(data) {
            if (data.success) {
                $('#detection-success').removeClass('d-none').text(data.message);
                setTimeout(function() {
                    $('#detectionModal').modal('hide');
                }, 1500);
            } else {
                $('#detection-error').removeClass('d-none').text(data.message);
            }
        },
        error: function(xhr) {
            const message = (xhr.responseJSON && xhr.responseJSON.message) || 'Failed to save configuration';
            $('#detection-error').removeClass('d-none').text(message);
        },
        complete: function() {
            $btn.prop('disabled', false).html(originalHtml);
        }
    });
}




    // Public API
    return {
        init: function() {
            console.log('Outputs module initialized');
        },
        openModal: openOutputsModal,
        openLogging: openLoggingModal,
        openDetection: openDetectionModal
    };
})();

// Initialize when document is ready
$(document).ready(function() {
    OutputsConfig.init();
});

// Expose global functions for compatibility with template click handlers
function openOutputsModal() {
    if (OutputsConfig && typeof OutputsConfig.openModal === 'function') {
        OutputsConfig.openModal();
    }
}

function openLoggingModal() {
    if (OutputsConfig && typeof OutputsConfig.openLogging === 'function') {
        OutputsConfig.openLogging();
    }
}

function openDetectionModal() {
    if (OutputsConfig && typeof OutputsConfig.openDetection === 'function') {
        OutputsConfig.openDetection();
    }
}
