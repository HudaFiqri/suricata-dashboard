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
