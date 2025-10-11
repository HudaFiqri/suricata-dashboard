/**
 * Configuration Utilities
 * Helper functions for configuration management
 */

/**
 * Escape HTML to prevent XSS attacks
 * @param {*} value - Value to escape
 * @returns {string} Escaped HTML string
 */
function escapeHtml(value) {
    if (value === null || value === undefined) {
        return '';
    }
    const str = String(value);
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return str.replace(/[&<>"']/g, m => map[m]);
}

/**
 * Convert value to boolean
 * @param {*} value - Value to convert
 * @param {boolean} fallback - Fallback value
 * @returns {boolean} Boolean value
 */
function toBoolean(value, fallback = false) {
    if (value === undefined || value === null) {
        return fallback;
    }
    if (typeof value === 'boolean') {
        return value;
    }
    if (typeof value === 'string') {
        const lower = value.toLowerCase();
        return lower === 'true' || lower === 'yes' || lower === '1';
    }
    return Boolean(value);
}

/**
 * Show loading state in container
 * @param {string} containerId - Container element ID
 * @param {string} message - Loading message
 */
function showLoading(containerId, message = 'Loading configuration...') {
    $(`#${containerId}`).html(
        `<p class="text-muted text-center">
            <i class="fas fa-spinner fa-spin"></i> ${message}
        </p>`
    );
}

/**
 * Show error message
 * @param {string} errorId - Error element ID
 * @param {string} message - Error message
 */
function showError(errorId, message) {
    $(`#${errorId}`)
        .removeClass('d-none alert-warning')
        .addClass('alert-danger')
        .text(message);
}

/**
 * Show warning message
 * @param {string} warningId - Warning element ID
 * @param {string} message - Warning message
 */
function showWarning(warningId, message) {
    $(`#${warningId}`)
        .removeClass('d-none alert-danger')
        .addClass('alert-warning')
        .text(message);
}

/**
 * Show success message
 * @param {string} successId - Success element ID
 * @param {string} message - Success message
 */
function showSuccess(successId, message) {
    $(`#${successId}`)
        .removeClass('d-none')
        .text(message);
}

/**
 * Hide element
 * @param {string} elementId - Element ID to hide
 */
function hideElement(elementId) {
    $(`#${elementId}`).addClass('d-none');
}

/**
 * Clear feedback messages
 * @param {string} errorId - Error element ID
 * @param {string} successId - Success element ID
 */
function clearFeedback(errorId, successId) {
    hideElement(errorId);
    hideElement(successId);
    $(`#${errorId}`).removeClass('alert-warning').addClass('alert-danger').text('');
    $(`#${successId}`).text('');
}

/**
 * Set button loading state
 * @param {jQuery} $button - Button element
 * @param {boolean} isLoading - Loading state
 * @param {string} originalHtml - Original button HTML
 * @returns {string} Current button HTML
 */
function setButtonLoading($button, isLoading, originalHtml = null) {
    if (isLoading) {
        const html = $button.html();
        $button.prop('disabled', true)
               .html('<i class="fas fa-spinner fa-spin"></i> Saving...');
        return html;
    } else {
        $button.prop('disabled', false)
               .html(originalHtml);
        return null;
    }
}

/**
 * Make AJAX GET request with error handling
 * @param {string} url - API endpoint URL
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
function apiGet(url, onSuccess, onError) {
    $.ajax({
        url: url,
        method: 'GET',
        success: onSuccess,
        error: function(xhr) {
            const message = (xhr.responseJSON && xhr.responseJSON.message)
                || `Failed to load from ${url}`;
            if (onError) onError(message, xhr);
        }
    });
}

/**
 * Make AJAX POST request with error handling
 * @param {string} url - API endpoint URL
 * @param {object} data - Data to send
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
function apiPost(url, data, onSuccess, onError) {
    $.ajax({
        url: url,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: onSuccess,
        error: function(xhr) {
            const message = (xhr.responseJSON && xhr.responseJSON.message)
                || `Failed to save to ${url}`;
            if (onError) onError(message, xhr);
        }
    });
}

/**
 * Run a lightweight self-check for the configuration page.
 * Verifies global handlers and a few API endpoints, then prints a summary
 * into an alert container with id `self-check-result` if present.
 */
function runConfigSelfCheck() {
    const checks = [];
    const add = (name, ok, extra = '') => checks.push({ name, ok, extra });

    // Global deps
    add('jQuery ($)', typeof window.$ === 'function');
    add('Bootstrap (modal)', !!(window.bootstrap && bootstrap.Modal));

    // Global handlers used by cards
    const globals = [
        'openPacketCaptureModal', 'openAppLayerModal', 'openOutputsModal',
        'openLoggingModal', 'openDetectionModal', 'openVarsModal',
        'openStreamModal', 'openHostModal', 'openIpsModal', 'openInterfaceModal',
        'openIntegrationModal'
    ];
    globals.forEach(fn => add(fn, typeof window[fn] === 'function'));

    // DOM presence checks for modals (without opening)
    const modals = [
        '#packetCaptureModal', '#appLayerModal', '#outputsModal', '#loggingModal',
        '#detectionModal', '#varsModal', '#streamModal', '#hostModal', '#ipsModal',
        '#interfaceModal'
    ];
    modals.forEach(sel => add(`DOM ${sel}`, document.querySelector(sel) !== null));

    // Minimal API pings
    const endpoints = [
        '/api/suricata-config/app-layer',
        '/api/suricata-config/outputs'
    ];

    const requests = endpoints.map(url =>
        $.get(url)
            .then(() => ({ url, ok: true }))
            .catch(() => ({ url, ok: false }))
    );

    const $out = $('#self-check-result');
    if ($out.length) {
        $out.removeClass('d-none alert-danger alert-success')
            .addClass('alert-info')
            .html('<i class="fas fa-spinner fa-spin"></i> Running self-check...');
    }

    return Promise.all(requests).then(results => {
        const all = checks.concat(results.map(r => ({ name: `GET ${r.url}` , ok: r.ok })));
        const failed = all.filter(i => !i.ok);
        const okCount = all.length - failed.length;

        let html = '';
        if (failed.length === 0) {
            html = `<i class=\"fas fa-check-circle\"></i> Self-check passed (${okCount}/${all.length}).`;
        } else {
            html = `<i class=\"fas fa-exclamation-triangle\"></i> Self-check found issues (${okCount}/${all.length} ok).`;
            html += '<ul class="mb-0 mt-2">' + failed.map(f => `<li>${escapeHtml(f.name)}</li>`).join('') + '</ul>';
        }

        if ($out.length) {
            $out.removeClass('alert-info')
                .addClass(failed.length ? 'alert-danger' : 'alert-success')
                .html(html);
        } else {
            // Fallback to console
            console[(failed.length ? 'error' : 'log')](html);
        }

        return { ok: failed.length === 0, details: all };
    });
}
