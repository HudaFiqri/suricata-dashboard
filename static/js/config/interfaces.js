/**
 * Interface Configuration Module
 * Extracted from config.html
 */

const InterfacesConfig = (function() {
    'use strict';

let systemInterfaces = [];
let configuredInterfaces = [];

function openInterfaceModal() {
    $('#interface-error').addClass('d-none').text('');
    $('#interface-success').addClass('d-none').text('');
    $('#interface-container').html('<p class="text-muted text-center"><i class="fas fa-spinner fa-spin"></i> Loading interfaces...</p>');
    $('#interfaceModal').modal('show');
    loadInterfaceConfig();
}

function loadInterfaceConfig() {
    // Load both system interfaces and configured interfaces
    Promise.all([
        $.get('/api/system/interfaces'),
        $.get('/api/suricata-config/interfaces')
    ]).then(function([sysResult, configResult]) {
        if (sysResult.success) {
            systemInterfaces = sysResult.interfaces || [];
        }
        if (configResult.success) {
            configuredInterfaces = configResult.interfaces || [];
        }
        renderInterfaces();
    }).catch(function(error) {
        $('#interface-error').removeClass('d-none').text('Failed to load interface data');
        $('#interface-container').html('');
    });
}

function renderInterfaces() {
    let html = '';

    // System Interfaces Section
    html += '<h6 class="border-bottom pb-2 mb-3"><i class="fas fa-network-wired"></i> Available System Interfaces</h6>';
    html += '<div class="table-responsive">';
    html += '<table class="table table-sm table-hover">';
    html += '<thead><tr>';
    html += '<th style="width: 30px"><input type="checkbox" id="select-all-interfaces"></th>';
    html += '<th>Interface</th><th>Type</th><th>IPv4</th><th>MAC</th><th>Status</th><th>Config</th>';
    html += '</tr></thead>';
    html += '<tbody>';

    systemInterfaces.forEach(function(iface) {
        const isConfigured = configuredInterfaces.find(c => c.interface === iface.name);
        const isChecked = isConfigured ? 'checked' : '';
        const statusBadge = iface.is_up ? '<span class="badge bg-success">UP</span>' : '<span class="badge bg-secondary">DOWN</span>';

        html += '<tr>';
        html += `<td><input type="checkbox" class="interface-checkbox" data-interface="${escapeHtml(iface.name)}" ${isChecked}></td>`;
        html += `<td><strong>${escapeHtml(iface.name)}</strong></td>`;
        html += `<td><select class="form-select form-select-sm interface-type" data-interface="${escapeHtml(iface.name)}">`;
        html += `<option value="af-packet"${isConfigured && isConfigured.type === 'af-packet' ? ' selected' : ''}>AF-Packet</option>`;
        html += `<option value="af-xdp"${isConfigured && isConfigured.type === 'af-xdp' ? ' selected' : ''}>AF-XDP</option>`;
        html += `<option value="dpdk"${isConfigured && isConfigured.type === 'dpdk' ? ' selected' : ''}>DPDK</option>`;
        html += `<option value="pcap"${isConfigured && isConfigured.type === 'pcap' ? ' selected' : ''}>PCAP</option>`;
        html += `</select></td>`;
        html += `<td class="text-muted small">${iface.ipv4 || '-'}</td>`;
        html += `<td class="text-muted small font-monospace">${iface.mac || '-'}</td>`;
        html += `<td>${statusBadge}</td>`;
        html += `<td><button class="btn btn-sm btn-outline-secondary interface-settings-btn" data-interface="${escapeHtml(iface.name)}" ${!isChecked ? 'disabled' : ''}><i class="fas fa-cog"></i></button></td>`;
        html += '</tr>';
    });

    html += '</tbody>';
    html += '</table>';
    html += '</div>';

    // Info section
    html += '<div class="alert alert-info mt-3 mb-0">';
    html += '<i class="fas fa-info-circle"></i> <strong>Tip:</strong> Select interfaces to monitor, choose capture type (AF-Packet, AF-XDP, DPDK, or PCAP), and click settings to configure advanced options.';
    html += '</div>';

    $('#interface-container').html(html);

    // Event handlers
    $('#select-all-interfaces').on('change', function() {
        $('.interface-checkbox').prop('checked', $(this).is(':checked')).trigger('change');
    });

    $('.interface-checkbox').on('change', function() {
        const $settingsBtn = $(this).closest('tr').find('.interface-settings-btn');
        $settingsBtn.prop('disabled', !$(this).is(':checked'));
    });

    $('.interface-settings-btn').on('click', function() {
        const ifaceName = $(this).data('interface');
        showInterfaceSettings(ifaceName);
    });
}

function showInterfaceSettings(ifaceName) {
    const configured = configuredInterfaces.find(c => c.interface === ifaceName) || {};
    const type = $(`.interface-type[data-interface="${ifaceName}"]`).val();

    let settingsHtml = `<div class="modal-body"><h6>Settings for ${ifaceName} (${type.toUpperCase()})</h6>`;

    if (type === 'af-packet') {
        settingsHtml += '<div class="mb-3">';
        settingsHtml += '<label class="form-label">Threads</label>';
        settingsHtml += `<input type="text" class="form-control" id="iface-threads" value="${configured.threads || 'auto'}" placeholder="auto">`;
        settingsHtml += '</div>';
        settingsHtml += '<div class="mb-3">';
        settingsHtml += '<label class="form-label">Cluster ID</label>';
        settingsHtml += `<input type="number" class="form-control" id="iface-cluster-id" value="${configured['cluster-id'] || 99}">`;
        settingsHtml += '</div>';
        settingsHtml += '<div class="mb-3">';
        settingsHtml += '<label class="form-label">Cluster Type</label>';
        settingsHtml += `<select class="form-select" id="iface-cluster-type">`;
        settingsHtml += `<option value="cluster_flow"${configured['cluster-type'] === 'cluster_flow' ? ' selected' : ''}>Cluster Flow</option>`;
        settingsHtml += `<option value="cluster_cpu"${configured['cluster-type'] === 'cluster_cpu' ? ' selected' : ''}>Cluster CPU</option>`;
        settingsHtml += `<option value="cluster_qm"${configured['cluster-type'] === 'cluster_qm' ? ' selected' : ''}>Cluster QM</option>`;
        settingsHtml += `</select></div>`;
    } else if (type === 'af-xdp') {
        settingsHtml += '<div class="mb-3">';
        settingsHtml += '<label class="form-label">Threads</label>';
        settingsHtml += `<input type="text" class="form-control" id="iface-threads" value="${configured.threads || 'auto'}" placeholder="auto">`;
        settingsHtml += '<small class="text-muted">Number of reader threads</small>';
        settingsHtml += '</div>';
        settingsHtml += '<div class="alert alert-info">';
        settingsHtml += '<i class="fas fa-info-circle"></i> AF-XDP requires kernel 4.18+ and proper XDP support.';
        settingsHtml += '</div>';
    } else if (type === 'dpdk') {
        settingsHtml += '<div class="mb-3">';
        settingsHtml += '<label class="form-label">Threads</label>';
        settingsHtml += `<input type="text" class="form-control" id="iface-threads" value="${configured.threads || 'auto'}" placeholder="auto">`;
        settingsHtml += '<small class="text-muted">Number of reader threads</small>';
        settingsHtml += '</div>';
        settingsHtml += '<div class="alert alert-warning">';
        settingsHtml += '<i class="fas fa-exclamation-triangle"></i> DPDK requires proper DPDK installation and configuration.';
        settingsHtml += '</div>';
    } else if (type === 'pcap') {
        settingsHtml += '<div class="alert alert-info">';
        settingsHtml += '<i class="fas fa-info-circle"></i> PCAP is the legacy packet capture method. No additional settings required.';
        settingsHtml += '</div>';
    }

    settingsHtml += `<button class="btn btn-primary" onclick="saveInterfaceSettings('${ifaceName}', '${type}')">Save</button>`;
    settingsHtml += '</div>';

    // Show in a simple alert (you can make this a separate modal if needed)
    const $row = $(`.interface-settings-btn[data-interface="${ifaceName}"]`).closest('tr');
    if ($row.next('.settings-row').length) {
        $row.next('.settings-row').remove();
    } else {
        $row.after(`<tr class="settings-row"><td colspan="7">${settingsHtml}</td></tr>`);
    }
}

function saveInterfaceSettings(ifaceName, type) {
    const existing = configuredInterfaces.find(c => c.interface === ifaceName);

    const settings = {
        interface: ifaceName,
        type: type,
        enabled: true
    };

    if (type === 'af-packet') {
        settings.threads = $('#iface-threads').val() || 'auto';
        settings['cluster-id'] = parseInt($('#iface-cluster-id').val()) || 99;
        settings['cluster-type'] = $('#iface-cluster-type').val() || 'cluster_flow';
    } else if (type === 'af-xdp' || type === 'dpdk') {
        settings.threads = $('#iface-threads').val() || 'auto';
    } else if (type === 'pcap') {
        // PCAP has no additional settings
    }

    if (existing) {
        Object.assign(existing, settings);
    } else {
        configuredInterfaces.push(settings);
    }

    $(`.interface-settings-btn[data-interface="${ifaceName}"]`).closest('tr').next('.settings-row').remove();
}

function saveInterfaceConfig() {
    $('#interface-error').addClass('d-none').text('');
    $('#interface-success').addClass('d-none').text('');

    const $btn = $('#save-interface-btn');
    const originalHtml = $btn.html();
    $btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Saving...');

    // Collect all selected interfaces
    const interfaces = [];
    $('.interface-checkbox:checked').each(function() {
        const ifaceName = $(this).data('interface');
        const type = $(`.interface-type[data-interface="${ifaceName}"]`).val();
        const existing = configuredInterfaces.find(c => c.interface === ifaceName);

        if (existing) {
            interfaces.push(existing);
        } else {
            // Default settings based on capture type
            const defaultSettings = {
                interface: ifaceName,
                type: type,
                enabled: true
            };

            if (type === 'af-packet') {
                defaultSettings.threads = 'auto';
                defaultSettings['cluster-id'] = 99;
                defaultSettings['cluster-type'] = 'cluster_flow';
            } else if (type === 'af-xdp' || type === 'dpdk') {
                defaultSettings.threads = 'auto';
            }
            // PCAP doesn't need additional settings

            interfaces.push(defaultSettings);
        }
    });

    $.ajax({
        url: '/api/suricata-config/interfaces',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ interfaces: interfaces }),
        success: function(data) {
            if (data.success) {
                $('#interface-success').removeClass('d-none').text(data.message || 'Configuration saved.');
                setTimeout(function() {
                    $('#interfaceModal').modal('hide');
                }, 1200);
            } else {
                $('#interface-error').removeClass('d-none').text(data.message || 'Failed to save interface configuration');
            }
        },
        error: function(xhr) {
            const message = (xhr.responseJSON && xhr.responseJSON.message) || 'Failed to save interface configuration';
            $('#interface-error').removeClass('d-none').text(message);
        },
        complete: function() {
            $btn.prop('disabled', false).html(originalHtml);
        }
    });
}

$('#save-interface-btn').off('click').on('click', saveInterfaceConfig);

    // Public API
    return {
        init: function() {
            console.log('Interface module initialized');
        },
        openModal: openInterfaceModal
    };
})();

// Initialize when document is ready
$(document).ready(function() {
    InterfacesConfig.init();
});

// Expose global function for compatibility with template click handlers
function openInterfaceModal() {
    if (InterfacesConfig && typeof InterfacesConfig.openModal === 'function') {
        InterfacesConfig.openModal();
    }
}
