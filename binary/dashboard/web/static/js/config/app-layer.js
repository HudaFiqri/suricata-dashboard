/**
 * App Layer Configuration Module
 * Extracted from config.html
 */

const ApplayerConfig = (function() {
    'use strict';

let appLayerProtocols = {};

function openAppLayerModal() {
    $('#app-layer-error').addClass('d-none').text('');
    $('#app-layer-success').addClass('d-none').text('');
    loadAppLayerConfig();
    $('#appLayerModal').modal('show');
}

function loadAppLayerConfig() {
    $('#app-layer-protocols-container').html('<p class="text-muted"><i class="fas fa-spinner fa-spin"></i> Loading protocols...</p>');

    $.get('/api/suricata-config/app-layer', function(data) {
        if (data.success) {
            appLayerProtocols = data.protocols || {};

            // Show warning if using defaults
            if (data.warning) {
                $('#app-layer-protocols-container').html('<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> ' + data.warning + '</div>');
                setTimeout(function() {
                    renderAppLayerProtocols(appLayerProtocols);
                }, 1000);
            } else {
                renderAppLayerProtocols(appLayerProtocols);
            }
        } else {
            $('#app-layer-protocols-container').html('<div class="alert alert-danger"><i class="fas fa-times-circle"></i> Failed to load protocols: ' + data.message + '</div>');
        }
    }).fail(function(xhr) {
        const message = (xhr.responseJSON && xhr.responseJSON.message) || 'Failed to connect to API';
        $('#app-layer-protocols-container').html('<div class="alert alert-danger"><i class="fas fa-times-circle"></i> ' + message + '</div>');
    });
}

function renderAppLayerProtocols(protocols) {
    let html = '<div class="row">';

    // Common protocols list
    const commonProtocols = ['http', 'tls', 'ssh', 'smtp', 'dns', 'ftp', 'smb', 'dcerpc', 'dhcp', 'nfs', 'tftp', 'ikev2', 'krb5', 'ntp', 'snmp', 'sip', 'rdp', 'rfb', 'mqtt', 'modbus'];

    commonProtocols.forEach(function(protocol) {
        const config = protocols[protocol] || {};
        const enabled = config.enabled === 'yes' || config.enabled === true;

        html += '<div class="col-md-6 mb-3">';
        html += '  <div class="card">';
        html += '    <div class="card-body py-2">';
        html += '      <div class="form-check form-switch">';
        html += '        <input class="form-check-input protocol-toggle" type="checkbox" id="protocol-' + protocol + '" data-protocol="' + protocol + '"' + (enabled ? ' checked' : '') + '>';
        html += '        <label class="form-check-label" for="protocol-' + protocol + '">';
        html += '          <strong>' + protocol.toUpperCase() + '</strong>';
        html += '        </label>';
        html += '      </div>';
        html += '    </div>';
        html += '  </div>';
        html += '</div>';
    });

    html += '</div>';

    $('#app-layer-protocols-container').html(html);
}

function saveAppLayerConfig() {
    const $btn = $('#save-app-layer-btn');
    const originalHtml = $btn.html();
    $btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-2"></span>Saving...');

    $('#app-layer-error').addClass('d-none').text('');
    $('#app-layer-success').addClass('d-none').text('');

    // Collect protocol states
    const protocols = {};
    $('.protocol-toggle').each(function() {
        const protocol = $(this).data('protocol');
        const enabled = $(this).is(':checked');
        protocols[protocol] = { enabled: enabled };
    });

    $.ajax({
        url: '/api/suricata-config/app-layer',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ protocols: protocols }),
        success: function(data) {
            if (data.success) {
                $('#app-layer-success').removeClass('d-none').text(data.message);
                setTimeout(function() {
                    $('#appLayerModal').modal('hide');
                }, 1500);
            } else {
                $('#app-layer-error').removeClass('d-none').text(data.message);
            }
        },
        error: function(xhr) {
            const message = (xhr.responseJSON && xhr.responseJSON.message) || 'Failed to save configuration';
            $('#app-layer-error').removeClass('d-none').text(message);
        },
        complete: function() {
            $btn.prop('disabled', false).html(originalHtml);
        }
    });
}

$('#save-app-layer-btn').click(saveAppLayerConfig);


    // Public API
    return {
        init: function() {
            console.log('App Layer module initialized');
        },
        openModal: openAppLayerModal
    };
})();

// Initialize when document is ready
$(document).ready(function() {
    ApplayerConfig.init();
});

// Expose global function for compatibility with template click handlers
function openAppLayerModal() {
    if (ApplayerConfig && typeof ApplayerConfig.openModal === 'function') {
        ApplayerConfig.openModal();
    }
}
