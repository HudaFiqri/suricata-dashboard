/**
 * Remote Config Fetch Helper
 * Fetch configuration directly from remote agent
 */

// Global variable to store current agent ID (set from page)
let currentAgentId = null;

/**
 * Fetch config from remote agent
 */
async function fetchConfigFromAgent(agentId, configPath = '/etc/suricata/suricata.yaml') {
    if (!agentId) {
        console.error('Agent ID is required');
        return null;
    }

    try {
        // Step 1: Send command to agent to fetch config
        const response = await fetch(`/api/v1/configs/${agentId}/fetch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('jwt_token') || ''}`
            },
            body: JSON.stringify({
                path: configPath
            })
        });

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error || 'Failed to initiate config fetch');
        }

        const commandId = result.command_id;
        console.log(`Config fetch initiated. Command ID: ${commandId}`);

        // Step 2: Poll for command result
        const configContent = await pollCommandResult(commandId, 30000); // 30 second timeout

        return configContent;

    } catch (error) {
        console.error('Error fetching config from agent:', error);
        throw error;
    }
}

/**
 * Poll command result until completed
 */
async function pollCommandResult(commandId, timeoutMs = 30000) {
    const startTime = Date.now();
    const pollInterval = 1000; // Poll every 1 second

    while (Date.now() - startTime < timeoutMs) {
        try {
            const response = await fetch(`/api/v1/commands/${commandId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('jwt_token') || ''}`
                }
            });

            const result = await response.json();

            if (!result.success) {
                throw new Error('Failed to get command status');
            }

            const command = result.command;

            // Check if command completed
            if (command.status === 'completed') {
                if (command.result && command.result.success) {
                    console.log('Config fetched successfully from agent');
                    return command.result.content;
                } else {
                    throw new Error(command.result?.message || 'Command failed');
                }
            } else if (command.status === 'failed') {
                throw new Error(command.error_message || 'Command failed');
            }

            // Wait before next poll
            await sleep(pollInterval);

        } catch (error) {
            console.error('Error polling command:', error);
            throw error;
        }
    }

    throw new Error('Command timeout - agent did not respond in time');
}

/**
 * Load and display config from agent
 */
async function loadConfigFromAgent(agentId) {
    // Show loading indicator
    showLoadingIndicator('Fetching configuration from agent...');

    try {
        const configContent = await fetchConfigFromAgent(agentId);

        // Parse YAML
        const configData = jsyaml.load(configContent);

        // Hide loading
        hideLoadingIndicator();

        // Display success message
        showSuccessMessage('Configuration loaded from agent successfully!');

        return configData;

    } catch (error) {
        hideLoadingIndicator();
        showErrorMessage(`Failed to load config: ${error.message}`);
        throw error;
    }
}

/**
 * Helper: Sleep function
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Helper: Show loading indicator
 */
function showLoadingIndicator(message = 'Loading...') {
    // Remove existing
    hideLoadingIndicator();

    const loader = $(`
        <div id="config-loader" class="alert alert-info d-flex align-items-center">
            <div class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <span>${message}</span>
        </div>
    `);

    $('.card-body').first().prepend(loader);
}

/**
 * Helper: Hide loading indicator
 */
function hideLoadingIndicator() {
    $('#config-loader').remove();
}

/**
 * Helper: Show success message
 */
function showSuccessMessage(message) {
    const alert = $(`
        <div class="alert alert-success alert-dismissible fade show" role="alert">
            <i class="fas fa-check-circle"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `);

    $('.card-body').first().prepend(alert);

    // Auto-dismiss after 3 seconds
    setTimeout(() => {
        alert.alert('close');
    }, 3000);
}

/**
 * Helper: Show error message
 */
function showErrorMessage(message) {
    const alert = $(`
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="fas fa-exclamation-triangle"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `);

    $('.card-body').first().prepend(alert);
}

/**
 * Example: Auto-fetch config when page loads if agent ID is available
 */
$(document).ready(function() {
    // Check if agent ID is in URL params
    const urlParams = new URLSearchParams(window.location.search);
    const agentId = urlParams.get('agent_id');

    if (agentId) {
        currentAgentId = agentId;
        console.log(`Agent ID detected: ${agentId}`);

        // Auto-fetch config from agent
        loadConfigFromAgent(agentId).then(configData => {
            console.log('Config loaded:', configData);
            // You can now use configData to populate modals
        }).catch(error => {
            console.error('Failed to auto-load config:', error);
        });
    }
});
