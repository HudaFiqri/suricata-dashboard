/**
 * Stream Configuration Module
 * Extracted from config.html
 */

const StreamConfig = (function() {
    'use strict';

function openStreamModal() {
    $('#stream-error').addClass('d-none').removeClass('alert-warning').addClass('alert-danger').text('');
    $('#stream-success').addClass('d-none').text('');
    $('#stream-container').html('<p class="text-muted text-center"><i class="fas fa-spinner fa-spin"></i> Loading stream configuration...</p>');
    $('#streamModal').modal('show');
    loadStreamConfig();
}

function loadStreamConfig() {
    $.ajax({
        url: '/api/suricata-config/stream',
        method: 'GET',
        success: function(data) {
            if (data.success) {
                if (data.warning) {
                    $('#stream-error').removeClass('d-none').removeClass('alert-danger').addClass('alert-warning').text(data.warning);
                } else {
                    $('#stream-error').addClass('d-none').removeClass('alert-warning').addClass('alert-danger');
                }
                streamConfig = data.stream || {};
                renderStream(streamConfig);
            } else {
                $('#stream-error').removeClass('d-none').removeClass('alert-warning').addClass('alert-danger').text(data.message || 'Failed to load stream configuration');
                $('#stream-container').html('');
            }
        },
        error: function(xhr) {
            const message = (xhr.responseJSON && xhr.responseJSON.message) || 'Failed to load stream configuration';
            $('#stream-error').removeClass('d-none').removeClass('alert-warning').addClass('alert-danger').text(message);
            $('#stream-container').html('');
        }
    });
}

function renderStream(config) {
    streamConfig = config || {};
    const reassembly = Object.assign({}, streamConfig.reassembly || {});

    const memcap = streamConfig.memcap || '32mb';
    const checksum = streamConfig['checksum-validation'] || 'auto';
    const inlineMode = streamConfig.inline || 'auto';
    const preallocSessions = streamConfig['prealloc-sessions'] !== undefined ? streamConfig['prealloc-sessions'] : '';

    const reassemblyMemcap = reassembly.memcap || '64mb';
    const reassemblyDepth = reassembly.depth || '1mb';
    const reassemblyToServer = reassembly['toserver-chunk-size'] !== undefined ? reassembly['toserver-chunk-size'] : 2560;
    const reassemblyToClient = reassembly['toclient-chunk-size'] !== undefined ? reassembly['toclient-chunk-size'] : 2560;

    let html = '<div class="row g-3">';
    html += `
        <div class="col-md-6">
            <label class="form-label">Stream Memcap</label>
            <input type="text" class="form-control" id="stream-memcap" value="${escapeHtml(memcap)}" placeholder="32mb">
        </div>`;
    html += `
        <div class="col-md-6">
            <label class="form-label">Checksum Validation</label>
            <select class="form-select" id="stream-checksum">
                ${['auto', 'yes', 'no'].map(option => `<option value="${option}"${option === checksum ? ' selected' : ''}>${option.toUpperCase()}</option>`).join('')}
            </select>
        </div>`;
    html += `
        <div class="col-md-6">
            <label class="form-label">Inline Mode</label>
            <select class="form-select" id="stream-inline">
                ${['auto', 'yes', 'no'].map(option => `<option value="${option}"${option === inlineMode ? ' selected' : ''}>${option.toUpperCase()}</option>`).join('')}
            </select>
        </div>`;
    html += `
        <div class="col-md-6">
            <label class="form-label">Prealloc Sessions</label>
            <input type="number" min="0" class="form-control" id="stream-prealloc" value="${escapeHtml(preallocSessions)}" placeholder="4096">
        </div>`;

    html += '<div class="col-12">';
    html += '<h6 class="mt-2"><i class="fas fa-layer-group"></i> Reassembly</h6>';
    html += '<div class="row g-3">';
    html += `
        <div class="col-md-3">
            <label class="form-label">Memcap</label>
            <input type="text" class="form-control" id="stream-reassembly-memcap" value="${escapeHtml(reassemblyMemcap)}" placeholder="64mb">
        </div>`;
    html += `
        <div class="col-md-3">
            <label class="form-label">Depth</label>
            <input type="text" class="form-control" id="stream-reassembly-depth" value="${escapeHtml(reassemblyDepth)}" placeholder="1mb">
        </div>`;
    html += `
        <div class="col-md-3">
            <label class="form-label">To-Server Chunk Size</label>
            <input type="number" min="0" class="form-control" id="stream-reassembly-toserver" value="${escapeHtml(reassemblyToServer)}">
        </div>`;
    html += `
        <div class="col-md-3">
            <label class="form-label">To-Client Chunk Size</label>
            <input type="number" min="0" class="form-control" id="stream-reassembly-toclient" value="${escapeHtml(reassemblyToClient)}">
        </div>`;
    html += '</div>';
    html += '</div>';

    html += '</div>';

    $('#stream-container').html(html);
}

function saveStreamConfig() {
    $('#stream-error').addClass('d-none').removeClass('alert-warning').addClass('alert-danger').text('');
    $('#stream-success').addClass('d-none').text('');

    const $btn = $('#save-stream-btn');
    const originalHtml = $btn.html();
    $btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Saving...');

    const payload = Object.assign({}, streamConfig || {});

    const memcap = $('#stream-memcap').val().trim();
    if (memcap) {
        payload.memcap = memcap;
    } else {
        delete payload.memcap;
    }

    payload['checksum-validation'] = $('#stream-checksum').val();
    payload.inline = $('#stream-inline').val();

    const preallocRaw = $('#stream-prealloc').val().trim();
    if (preallocRaw) {
        const parsed = parseInt(preallocRaw, 10);
        payload['prealloc-sessions'] = Number.isNaN(parsed) ? preallocRaw : parsed;
    } else {
        delete payload['prealloc-sessions'];
    }

    const reassemblyPayload = Object.assign({}, streamConfig && streamConfig.reassembly ? streamConfig.reassembly : {});
    const reassemblyMemcap = $('#stream-reassembly-memcap').val().trim();
    if (reassemblyMemcap) {
        reassemblyPayload.memcap = reassemblyMemcap;
    } else {
        delete reassemblyPayload.memcap;
    }

    const reassemblyDepth = $('#stream-reassembly-depth').val().trim();
    if (reassemblyDepth) {
        reassemblyPayload.depth = reassemblyDepth;
    } else {
        delete reassemblyPayload.depth;
    }

    const reassemblyToServer = $('#stream-reassembly-toserver').val().trim();
    if (reassemblyToServer) {
        const parsedServer = parseInt(reassemblyToServer, 10);
        reassemblyPayload['toserver-chunk-size'] = Number.isNaN(parsedServer) ? reassemblyToServer : parsedServer;
    } else {
        delete reassemblyPayload['toserver-chunk-size'];
    }

    const reassemblyToClient = $('#stream-reassembly-toclient').val().trim();
    if (reassemblyToClient) {
        const parsedClient = parseInt(reassemblyToClient, 10);
        reassemblyPayload['toclient-chunk-size'] = Number.isNaN(parsedClient) ? reassemblyToClient : parsedClient;
    } else {
        delete reassemblyPayload['toclient-chunk-size'];
    }

    payload.reassembly = reassemblyPayload;

    $.ajax({
        url: '/api/suricata-config/stream',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ stream: payload }),
        success: function(data) {
            if (data.success) {
                streamConfig = payload;
                $('#stream-success').removeClass('d-none').text(data.message || 'Configuration saved.');
                setTimeout(function() {
                    $('#streamModal').modal('hide');
                }, 1200);
            } else {
                $('#stream-error').removeClass('d-none').removeClass('alert-warning').addClass('alert-danger').text(data.message || 'Failed to save stream configuration');
            }
        },
        error: function(xhr) {
            const message = (xhr.responseJSON && xhr.responseJSON.message) || 'Failed to save stream configuration';
            $('#stream-error').removeClass('d-none').removeClass('alert-warning').addClass('alert-danger').text(message);
        },
        complete: function() {
            $btn.prop('disabled', false).html(originalHtml);
        }
    });
}


    // Public API
    return {
        init: function() {
            console.log('Stream module initialized');
        }
    };
})();

// Initialize when document is ready
$(document).ready(function() {
    StreamConfig.init();
});
