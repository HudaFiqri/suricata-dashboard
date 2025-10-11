/**
 * Host Configuration Module
 * Extracted from config.html
 */

const HostConfig = (function() {
    'use strict';

let hostConfig = {};

function openHostModal() {
    $('#host-error').addClass('d-none').removeClass('alert-warning').addClass('alert-danger').text('');
    $('#host-success').addClass('d-none').text('');
    $('#host-container').html('<p class="text-muted text-center"><i class="fas fa-spinner fa-spin"></i> Loading host configuration...</p>');
    $('#hostModal').modal('show');
    loadHostConfig();
}

function loadHostConfig() {
    $.ajax({
        url: '/api/suricata-config/host',
        method: 'GET',
        success: function(data) {
            if (data.success) {
                if (data.warning) {
                    $('#host-error').removeClass('d-none').removeClass('alert-danger').addClass('alert-warning').text(data.warning);
                } else {
                    $('#host-error').addClass('d-none').removeClass('alert-warning').addClass('alert-danger');
                }
                hostConfig = data.host || {};
                renderHost(hostConfig);
            } else {
                $('#host-error').removeClass('d-none').removeClass('alert-warning').addClass('alert-danger').text(data.message || 'Failed to load host configuration');
                $('#host-container').html('');
            }
        },
        error: function(xhr) {
            const message = (xhr.responseJSON && xhr.responseJSON.message) || 'Failed to load host configuration';
            $('#host-error').removeClass('d-none').removeClass('alert-warning').addClass('alert-danger').text(message);
            $('#host-container').html('');
        }
    });
}

function renderHost(config) {
    hostConfig = config || {};

    const hashSize = hostConfig['hash-size'] || 4096;
    const prealloc = hostConfig['prealloc'] || 1000;
    const memcap = hostConfig['memcap'] || '32mb';

    let html = '<div class="row g-3">';

    html += `
        <div class="col-md-4">
            <label class="form-label"><i class="fas fa-hashtag"></i> Hash Size</label>
            <input type="number" min="1" class="form-control" id="host-hash-size" value="${escapeHtml(hashSize)}" placeholder="4096">
            <small class="text-muted">Hash table size for host tracking (higher = more memory, better performance)</small>
        </div>`;

    html += `
        <div class="col-md-4">
            <label class="form-label"><i class="fas fa-database"></i> Preallocate Hosts</label>
            <input type="number" min="0" class="form-control" id="host-prealloc" value="${escapeHtml(prealloc)}" placeholder="1000">
            <small class="text-muted">Number of host structures to preallocate at startup</small>
        </div>`;

    html += `
        <div class="col-md-4">
            <label class="form-label"><i class="fas fa-memory"></i> Memory Cap</label>
            <input type="text" class="form-control" id="host-memcap" value="${escapeHtml(memcap)}" placeholder="32mb">
            <small class="text-muted">Maximum memory for host table (e.g., 32mb, 64mb, 128mb)</small>
        </div>`;

    html += '</div>';

    // Additional info section
    html += '<div class="mt-4">';
    html += '<h6 class="border-bottom pb-2"><i class="fas fa-info-circle"></i> Host Table Information</h6>';
    html += '<div class="row mt-3">';
    html += '<div class="col-md-12">';
    html += '<p class="text-muted small mb-2"><strong>What is Host Table?</strong></p>';
    html += '<p class="text-muted small">The host table tracks IP addresses and their associated metadata (OS, services, etc.). This is used for:</p>';
    html += '<ul class="text-muted small">';
    html += '<li>OS detection and policy application</li>';
    html += '<li>Service detection and protocol analysis</li>';
    html += '<li>Performance optimization based on host characteristics</li>';
    html += '</ul>';
    html += '</div>';
    html += '</div>';
    html += '</div>';

    $('#host-container').html(html);
}

function saveHostConfig() {
    $('#host-error').addClass('d-none').removeClass('alert-warning').addClass('alert-danger').text('');
    $('#host-success').addClass('d-none').text('');

    const $btn = $('#save-host-btn');
    const originalHtml = $btn.html();
    $btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Saving...');

    const payload = Object.assign({}, hostConfig || {});

    const hashSizeRaw = $('#host-hash-size').val().trim();
    if (hashSizeRaw) {
        const parsed = parseInt(hashSizeRaw, 10);
        payload['hash-size'] = Number.isNaN(parsed) ? hashSizeRaw : parsed;
    } else {
        delete payload['hash-size'];
    }

    const preallocRaw = $('#host-prealloc').val().trim();
    if (preallocRaw) {
        const parsed = parseInt(preallocRaw, 10);
        payload['prealloc'] = Number.isNaN(parsed) ? preallocRaw : parsed;
    } else {
        delete payload['prealloc'];
    }

    const memcap = $('#host-memcap').val().trim();
    if (memcap) {
        payload['memcap'] = memcap;
    } else {
        delete payload['memcap'];
    }

    $.ajax({
        url: '/api/suricata-config/host',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ host: payload }),
        success: function(data) {
            if (data.success) {
                hostConfig = payload;
                $('#host-success').removeClass('d-none').text(data.message || 'Configuration saved.');
                setTimeout(function() {
                    $('#hostModal').modal('hide');
                }, 1200);
            } else {
                $('#host-error').removeClass('d-none').removeClass('alert-warning').addClass('alert-danger').text(data.message || 'Failed to save host configuration');
            }
        },
        error: function(xhr) {
            const message = (xhr.responseJSON && xhr.responseJSON.message) || 'Failed to save host configuration';
            $('#host-error').removeClass('d-none').removeClass('alert-warning').addClass('alert-danger').text(message);
        },
        complete: function() {
            $btn.prop('disabled', false).html(originalHtml);
        }
    });
}

$('#save-host-btn').off('click').on('click', saveHostConfig);


    // Public API
    return {
        init: function() {
            console.log('Host module initialized');
        }
    };
})();

// Initialize when document is ready
$(document).ready(function() {
    HostConfig.init();
});
