/**
 * Variables Configuration Module
 * Extracted from config.html
 */

const VarsConfig = (function() {
    'use strict';

function openVarsModal() {
    $('#vars-error').addClass('d-none').removeClass('alert-warning').addClass('alert-danger').text('');
    $('#vars-success').addClass('d-none').text('');
    $('#vars-container').html('<p class="text-muted text-center"><i class="fas fa-spinner fa-spin"></i> Loading variables...</p>');
    $('#varsModal').modal('show');
    loadVarsConfig();
}

function loadVarsConfig() {
    $.ajax({
        url: '/api/suricata-config/vars',
        method: 'GET',
        success: function(data) {
            if (data.success) {
                if (data.warning) {
                    $('#vars-error').removeClass('d-none').removeClass('alert-danger').addClass('alert-warning').text(data.warning);
                } else {
                    $('#vars-error').addClass('d-none').removeClass('alert-warning').addClass('alert-danger');
                }
                varsConfig = data.vars || {};
                renderVars(varsConfig);
            } else {
                $('#vars-error').removeClass('d-none').removeClass('alert-warning').addClass('alert-danger').text(data.message || 'Failed to load variables');
                $('#vars-container').html('');
            }
        },
        error: function(xhr) {
            const message = (xhr.responseJSON && xhr.responseJSON.message) || 'Failed to load variables';
            $('#vars-error').removeClass('d-none').removeClass('alert-warning').addClass('alert-danger').text(message);
            $('#vars-container').html('');
        }
    });
}

function renderVars(config) {
    varsConfig = config || {};
    const entries = Object.entries(varsConfig);

    let html = '<div class="table-responsive">';
    html += '<table class="table table-sm align-middle">';
    html += '<thead><tr><th style="width: 30%">Name</th><th>Value</th><th style="width: 40px" class="text-center">&nbsp;</th></tr></thead>';
    html += '<tbody id="vars-table-body"></tbody>';
    html += '</table>';
    html += '</div>';
    html += '<button type="button" class="btn btn-outline-primary btn-sm" id="add-var-row"><i class="fas fa-plus"></i> Add Variable</button>';
    html += '<small class="text-muted d-block mt-2">Values accept plain strings or JSON objects/arrays for complex definitions.</small>';

    $('#vars-container').html(html);

    const $tbody = $('#vars-table-body');
    if (entries.length === 0) {
        addVarRow();
    } else {
        entries.forEach(([name, value]) => {
            addVarRow(name, valueToDisplay(value));
        });
    }

    $('#add-var-row').off('click').on('click', function() {
        addVarRow();
    });

    $tbody.off('click', '.remove-var-row').on('click', '.remove-var-row', function() {
        $(this).closest('tr').remove();
    });
}

function addVarRow(name = '', value = '') {
    const $tbody = $('#vars-table-body');
    if (!$tbody.length) {
        return;
    }
    const rowHtml = `
        <tr class="var-row">
            <td>
                <input type="text" class="form-control var-name" value="${escapeHtml(name)}" placeholder="VAR_NAME">
            </td>
            <td>
                <textarea class="form-control var-value" rows="2" placeholder="Value (string or JSON)">${escapeHtml(value)}</textarea>
            </td>
            <td class="text-center">
                <button type="button" class="btn btn-sm btn-outline-danger remove-var-row" title="Remove"><i class="fas fa-times"></i></button>
            </td>
        </tr>`;
    $tbody.append(rowHtml);
}

function valueToDisplay(value) {
    if (value === null || value === undefined) {
        return '';
    }
    if (typeof value === 'object') {
        try {
            return JSON.stringify(value, null, 2);
        } catch (err) {
            return String(value);
        }
    }
    return String(value);
}

function parseVarValue(raw) {
    if (raw === null || raw === undefined) {
        return '';
    }
    const trimmed = raw.trim();
    if (!trimmed) {
        return '';
    }
    if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
        try {
            return JSON.parse(trimmed);
        } catch (err) {
            throw new Error('Invalid JSON value: ' + err.message);
        }
    }
    return trimmed;
}

function saveVarsConfig() {
    $('#vars-error').addClass('d-none').removeClass('alert-warning').addClass('alert-danger').text('');
    $('#vars-success').addClass('d-none').text('');

    const $btn = $('#save-vars-btn');
    const originalHtml = $btn.html();
    $btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Saving...');

    const result = {};
    let hasError = false;
    let errorMessage = '';

    $('#vars-table-body tr').each(function() {
        const name = $(this).find('.var-name').val().trim();
        const valueRaw = $(this).find('.var-value').val();

        if (!name) {
            return;
        }

        try {
            result[name] = parseVarValue(valueRaw || '');
        } catch (err) {
            hasError = true;
            errorMessage = err.message || 'Invalid value';
            return false; // break
        }
    });

    if (hasError) {
        $('#vars-error').removeClass('d-none').removeClass('alert-warning').addClass('alert-danger').text(errorMessage);
        $btn.prop('disabled', false).html(originalHtml);
        return;
    }

    if (Object.keys(result).length === 0) {
        $('#vars-error').removeClass('d-none').removeClass('alert-warning').addClass('alert-danger').text('Please define at least one variable before saving.');
        $btn.prop('disabled', false).html(originalHtml);
        return;
    }

    $.ajax({
        url: '/api/suricata-config/vars',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ vars: result }),
        success: function(data) {
            if (data.success) {
                varsConfig = result;
                $('#vars-success').removeClass('d-none').text(data.message || 'Variables saved successfully.');
                setTimeout(function() {
                    $('#varsModal').modal('hide');
                }, 1200);
            } else {
                $('#vars-error').removeClass('d-none').removeClass('alert-warning').addClass('alert-danger').text(data.message || 'Failed to save variables');
            }
        },
        error: function(xhr) {
            const message = (xhr.responseJSON && xhr.responseJSON.message) || 'Failed to save variables';
            $('#vars-error').removeClass('d-none').removeClass('alert-warning').addClass('alert-danger').text(message);
        },
        complete: function() {
            $btn.prop('disabled', false).html(originalHtml);
        }
    });
}

$('#save-af-packet-btn').off('click').on('click', saveAfPacketConfig);
$('#save-stream-btn').off('click').on('click', saveStreamConfig);
$('#save-vars-btn').off('click').on('click', saveVarsConfig);

$('#save-detection-btn').click(saveDetectionConfig);


    // Public API
    return {
        init: function() {
            console.log('Variables module initialized');
        },
        openModal: openVarsModal
    };
})();

// Initialize when document is ready
$(document).ready(function() {
    VarsConfig.init();
});

// Expose global function for compatibility with template click handlers
function openVarsModal() {
    if (VarsConfig && typeof VarsConfig.openModal === 'function') {
        VarsConfig.openModal();
    }
}
