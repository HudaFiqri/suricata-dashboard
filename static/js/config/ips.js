/**
 * IPS/Preventive Configuration Module
 * Extracted from config.html
 */

const IpsConfig = (function() {
    'use strict';

let ipsConfig = {};

function openIpsModal() {
    $('#ips-error').addClass('d-none').removeClass('alert-warning').addClass('alert-danger').text('');
    $('#ips-success').addClass('d-none').text('');
    $('#ips-container').html('<p class="text-muted text-center"><i class="fas fa-spinner fa-spin"></i> Loading IPS configuration...</p>');
    $('#ipsModal').modal('show');
    loadIpsConfig();
}

function loadIpsConfig() {
    $.ajax({
        url: '/api/suricata-config/ips',
        method: 'GET',
        success: function(data) {
            if (data.success) {
                if (data.warning) {
                    $('#ips-error').removeClass('d-none').removeClass('alert-danger').addClass('alert-warning').text(data.warning);
                } else {
                    $('#ips-error').addClass('d-none').removeClass('alert-warning').addClass('alert-danger');
                }
                ipsConfig = data.ips || {};
                renderIps(ipsConfig);
            } else {
                $('#ips-error').removeClass('d-none').removeClass('alert-warning').addClass('alert-danger').text(data.message || 'Failed to load IPS configuration');
                $('#ips-container').html('');
            }
        },
        error: function(xhr) {
            const message = (xhr.responseJSON && xhr.responseJSON.message) || 'Failed to load IPS configuration';
            $('#ips-error').removeClass('d-none').removeClass('alert-warning').addClass('alert-danger').text(message);
            $('#ips-container').html('');
        }
    });
}

function renderIps(config) {
    ipsConfig = config || {};

    const actionOrder = ipsConfig['action-order'] || ['pass', 'drop', 'reject', 'alert'];
    const defaultAction = ipsConfig['default-rule-action'] || 'alert';
    const afPacketCopyMode = ipsConfig['af-packet-copy-mode'] || '';
    const afPacketCopyIface = ipsConfig['af-packet-copy-iface'] || '';

    let html = '<div class="row g-3">';

    // Default Rule Action
    html += `
        <div class="col-md-6">
            <label class="form-label"><i class="fas fa-exclamation-circle"></i> Default Rule Action</label>
            <select class="form-select" id="ips-default-action">
                ${['alert', 'drop', 'reject', 'pass'].map(action =>
                    `<option value="${action}"${action === defaultAction ? ' selected' : ''}>${action.toUpperCase()}</option>`
                ).join('')}
            </select>
            <small class="text-muted">Default action for rules without explicit action</small>
        </div>`;

    // Action Order
    html += `
        <div class="col-md-6">
            <label class="form-label"><i class="fas fa-list-ol"></i> Action Order Priority</label>
            <input type="text" class="form-control" id="ips-action-order" value="${escapeHtml(actionOrder.join(', '))}" placeholder="pass, drop, reject, alert">
            <small class="text-muted">Action priority order (comma-separated)</small>
        </div>`;

    html += '</div>';

    // AF-Packet IPS Mode Section
    html += '<div class="mt-4">';
    html += '<h6 class="border-bottom pb-2"><i class="fas fa-network-wired"></i> AF-Packet IPS Mode</h6>';
    html += '<div class="row g-3 mt-2">';

    html += `
        <div class="col-md-6">
            <label class="form-label">Copy Mode</label>
            <select class="form-select" id="ips-copy-mode">
                <option value="">Disabled (IDS Mode)</option>
                <option value="ips"${afPacketCopyMode === 'ips' ? ' selected' : ''}>IPS (Inline Mode)</option>
                <option value="tap"${afPacketCopyMode === 'tap' ? ' selected' : ''}>TAP (Copy Mode)</option>
            </select>
            <small class="text-muted">Enable IPS mode for AF-Packet interface</small>
        </div>`;

    html += `
        <div class="col-md-6">
            <label class="form-label">Copy Interface</label>
            <input type="text" class="form-control" id="ips-copy-iface" value="${escapeHtml(afPacketCopyIface)}" placeholder="eth1">
            <small class="text-muted">Destination interface for IPS copy mode</small>
        </div>`;

    html += '</div>';
    html += '</div>';

    // Information Section
    html += '<div class="mt-4">';
    html += '<h6 class="border-bottom pb-2"><i class="fas fa-info-circle"></i> IPS Mode Information</h6>';
    html += '<div class="row mt-3">';
    html += '<div class="col-md-12">';
    html += '<ul class="text-muted small mb-0">';
    html += '<li><strong>ALERT:</strong> Only log the event (IDS mode - passive)</li>';
    html += '<li><strong>DROP:</strong> Block the packet silently (IPS mode - active)</li>';
    html += '<li><strong>REJECT:</strong> Block and send reset/unreachable (IPS mode - active)</li>';
    html += '<li><strong>PASS:</strong> Allow the packet explicitly</li>';
    html += '</ul>';
    html += '<div class="alert alert-danger mt-3 mb-0">';
    html += '<i class="fas fa-exclamation-triangle"></i> <strong>Important:</strong> Enabling IPS mode requires proper network configuration. Incorrect settings may cause network disruption.';
    html += '</div>';
    html += '</div>';
    html += '</div>';
    html += '</div>';

    $('#ips-container').html(html);
}

function saveIpsConfig() {
    $('#ips-error').addClass('d-none').removeClass('alert-warning').addClass('alert-danger').text('');
    $('#ips-success').addClass('d-none').text('');

    const $btn = $('#save-ips-btn');
    const originalHtml = $btn.html();
    $btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Saving...');

    const payload = Object.assign({}, ipsConfig || {});

    // Default action
    payload['default-rule-action'] = $('#ips-default-action').val();

    // Action order
    const actionOrderRaw = $('#ips-action-order').val().trim();
    if (actionOrderRaw) {
        payload['action-order'] = actionOrderRaw.split(',').map(s => s.trim()).filter(s => s);
    } else {
        payload['action-order'] = ['pass', 'drop', 'reject', 'alert'];
    }

    // AF-Packet copy mode
    const copyMode = $('#ips-copy-mode').val();
    if (copyMode) {
        payload['af-packet-copy-mode'] = copyMode;
        payload['af-packet-copy-iface'] = $('#ips-copy-iface').val().trim();
    } else {
        delete payload['af-packet-copy-mode'];
        delete payload['af-packet-copy-iface'];
    }

    $.ajax({
        url: '/api/suricata-config/ips',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ ips: payload }),
        success: function(data) {
            if (data.success) {
                ipsConfig = payload;
                $('#ips-success').removeClass('d-none').text(data.message || 'Configuration saved.');
                setTimeout(function() {
                    $('#ipsModal').modal('hide');
                }, 1200);
            } else {
                $('#ips-error').removeClass('d-none').removeClass('alert-warning').addClass('alert-danger').text(data.message || 'Failed to save IPS configuration');
            }
        },
        error: function(xhr) {
            const message = (xhr.responseJSON && xhr.responseJSON.message) || 'Failed to save IPS configuration';
            $('#ips-error').removeClass('d-none').removeClass('alert-warning').addClass('alert-danger').text(message);
        },
        complete: function() {
            $btn.prop('disabled', false).html(originalHtml);
        }
    });
}

$('#save-ips-btn').off('click').on('click', saveIpsConfig);


    // Public API
    return {
        init: function() {
            console.log('IPS/Preventive module initialized');
        }
    };
})();

// Initialize when document is ready
$(document).ready(function() {
    IpsConfig.init();
});
