/**
 * Packet Capture Configuration Module
 * Manages packet capture configuration for AF-Packet, AF-XDP, DPDK, and PCAP
 */

const PacketCaptureConfig = (function() {
    'use strict';

    // Private variables
    let currentCaptureType = 'af-packet';
    let packetCaptureConfig = {};

    /**
     * Open Packet Capture Modal
     * @param {string} captureType - Type of capture (af-packet, af-xdp, dpdk, pcap)
     */
    function openModal(captureType = 'af-packet') {
        currentCaptureType = captureType;
        clearFeedback('packet-capture-error', 'packet-capture-success');
        $('#capture-type-selector').val(captureType);
        showLoading(
            'packet-capture-container',
            'Loading packet capture configuration...'
        );
        $('#packetCaptureModal').modal('show');
        loadConfig(captureType);
    }

    /**
     * Load packet capture configuration
     * @param {string} captureType - Type of capture
     */
    function loadConfig(captureType) {
        apiGet(
            `/api/suricata-config/packet-capture/${captureType}`,
            function(data) {
                if (data.success) {
                    if (data.warning) {
                        showWarning('packet-capture-error', data.warning);
                    }
                    packetCaptureConfig = data.config || {};
                    renderConfig(captureType, packetCaptureConfig);
                } else {
                    showError(
                        'packet-capture-error',
                        data.message || 'Failed to load configuration'
                    );
                    $('#packet-capture-container').html('');
                }
            },
            function(message) {
                showError('packet-capture-error', message);
                $('#packet-capture-container').html('');
            }
        );
    }

    /**
     * Render packet capture configuration form
     * @param {string} captureType - Type of capture
     * @param {object} config - Configuration object
     */
    function renderConfig(captureType, config) {
        packetCaptureConfig = config || {};
        let html = '<div class="row g-3">';

        switch(captureType) {
            case 'af-packet':
                html += renderAfPacketFields(config);
                break;
            case 'af-xdp':
                html += renderAfXdpFields(config);
                break;
            case 'dpdk':
                html += renderDpdkFields(config);
                break;
            case 'pcap':
                html += renderPcapFields(config);
                break;
        }

        html += '</div>';
        $('#packet-capture-container').html(html);
    }

    /**
     * Render AF-Packet configuration fields
     */
    function renderAfPacketFields(config) {
        const interfaceName = config.interface || '';
        const threads = config.threads || 'auto';
        const clusterId = config['cluster-id'] !== undefined
            ? config['cluster-id'] : 99;
        const clusterType = config['cluster-type'] || 'cluster_flow';
        const defrag = toBoolean(config.defrag, true);
        const useMmap = toBoolean(config['use-mmap'], true);
        const tpacketV3 = toBoolean(config['tpacket-v3'], true);
        const promisc = toBoolean(config.promisc, true);

        return `
            <div class="col-md-6">
                <label class="form-label">Interface</label>
                <input type="text" class="form-control"
                    id="capture-interface"
                    value="${escapeHtml(interfaceName)}"
                    placeholder="eth0">
                <small class="text-muted">
                    Network interface for AF-Packet capture.
                </small>
            </div>
            <div class="col-md-6">
                <label class="form-label">Threads</label>
                <input type="text" class="form-control"
                    id="capture-threads"
                    value="${escapeHtml(threads)}"
                    placeholder="auto">
                <small class="text-muted">
                    Number of reader threads (use <code>auto</code>)
                </small>
            </div>
            <div class="col-md-6">
                <label class="form-label">Cluster ID</label>
                <input type="number" class="form-control"
                    id="capture-cluster-id"
                    value="${escapeHtml(clusterId)}"
                    placeholder="99">
            </div>
            <div class="col-md-6">
                <label class="form-label">Cluster Type</label>
                <select class="form-select" id="capture-cluster-type">
                    ${['cluster_flow', 'cluster_cpu', 'cluster_qm']
                        .map(opt => `<option value="${opt}"${
                            opt === clusterType ? ' selected' : ''
                        }>${opt}</option>`).join('')}
                </select>
            </div>
            <div class="col-md-12">
                <div class="row">
                    ${renderCheckbox(
                        'capture-defrag',
                        'Enable Defrag',
                        defrag
                    )}
                    ${renderCheckbox(
                        'capture-use-mmap',
                        'Use mmap()',
                        useMmap
                    )}
                    ${renderCheckbox(
                        'capture-tpacket-v3',
                        'TPACKET v3',
                        tpacketV3
                    )}
                    ${renderCheckbox(
                        'capture-promisc',
                        'Promiscuous Mode',
                        promisc
                    )}
                </div>
            </div>
        `;
    }

    /**
     * Render checkbox field
     */
    function renderCheckbox(id, label, checked) {
        return `
            <div class="col-md-3">
                <div class="form-check form-switch">
                    <input type="checkbox" class="form-check-input"
                        id="${id}" ${checked ? 'checked' : ''}>
                    <label class="form-check-label" for="${id}">
                        ${label}
                    </label>
                </div>
            </div>
        `;
    }

    /**
     * Render AF-XDP configuration fields
     */
    function renderAfXdpFields(config) {
        const interfaceName = config.interface || '';
        const threads = config.threads || 'auto';
        const busyPoll = toBoolean(config['enable-busy-poll'], true);
        const busyPollTime = config['busy-poll-time'] || 20;
        const busyPollBudget = config['busy-poll-budget'] || 64;

        return `
            <div class="col-md-6">
                <label class="form-label">Interface</label>
                <input type="text" class="form-control"
                    id="capture-interface"
                    value="${escapeHtml(interfaceName)}"
                    placeholder="eth0">
                <small class="text-muted">
                    Network interface for AF-XDP capture.
                </small>
            </div>
            <div class="col-md-6">
                <label class="form-label">Threads</label>
                <input type="text" class="form-control"
                    id="capture-threads"
                    value="${escapeHtml(threads)}"
                    placeholder="auto">
                <small class="text-muted">Number of reader threads.</small>
            </div>
            <div class="col-md-4">
                <label class="form-label">Busy Poll Time</label>
                <input type="number" class="form-control"
                    id="capture-busy-poll-time"
                    value="${escapeHtml(busyPollTime)}"
                    placeholder="20">
                <small class="text-muted">Microseconds to busy poll.</small>
            </div>
            <div class="col-md-4">
                <label class="form-label">Busy Poll Budget</label>
                <input type="number" class="form-control"
                    id="capture-busy-poll-budget"
                    value="${escapeHtml(busyPollBudget)}"
                    placeholder="64">
                <small class="text-muted">Packets to process per poll.</small>
            </div>
            <div class="col-md-4">
                <div class="form-check form-switch mt-4">
                    <input type="checkbox" class="form-check-input"
                        id="capture-busy-poll" ${busyPoll ? 'checked' : ''}>
                    <label class="form-check-label" for="capture-busy-poll">
                        Enable Busy Poll
                    </label>
                </div>
            </div>
        `;
    }

    /**
     * Render DPDK configuration fields
     */
    function renderDpdkFields(config) {
        const procType = config['eal-params']
            ? config['eal-params']['proc-type'] || 'primary'
            : 'primary';
        const interfaces = config.interfaces || [];
        const firstInterface = interfaces.length > 0 ? interfaces[0] : {};

        const interfacePCI = firstInterface.interface || '0000:3b:00.0';
        const threads = firstInterface.threads || 'auto';
        const promisc = toBoolean(firstInterface.promisc, true);
        const multicast = toBoolean(firstInterface.multicast, true);
        const checksumChecks = toBoolean(
            firstInterface['checksum-checks'],
            true
        );
        const checksumOffload = toBoolean(
            firstInterface['checksum-checks-offload'],
            true
        );
        const mtu = firstInterface.mtu || 1500;
        const mempoolSize = firstInterface['mempool-size'] || 65535;
        const mempoolCacheSize = firstInterface['mempool-cache-size'] || 257;
        const rxDescriptors = firstInterface['rx-descriptors'] || 1024;
        const txDescriptors = firstInterface['tx-descriptors'] || 1024;
        const copyMode = firstInterface['copy-mode'] || 'none';
        const copyIface = firstInterface['copy-iface'] || 'none';

        return `
            <div class="col-md-12">
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    <strong>DPDK configuration is advanced.</strong>
                    Ensure your system has DPDK properly installed.
                </div>
            </div>

            <!-- EAL Parameters -->
            <div class="col-md-12">
                <h6 class="border-bottom pb-2">
                    <i class="fas fa-cogs"></i> EAL Parameters
                </h6>
            </div>
            <div class="col-md-6">
                <label class="form-label">Process Type</label>
                <select class="form-select" id="capture-proc-type">
                    <option value="primary"${
                        procType === 'primary' ? ' selected' : ''
                    }>Primary</option>
                    <option value="secondary"${
                        procType === 'secondary' ? ' selected' : ''
                    }>Secondary</option>
                </select>
                <small class="text-muted">DPDK EAL process type.</small>
            </div>

            <!-- Interface Configuration -->
            <div class="col-md-12 mt-3">
                <h6 class="border-bottom pb-2">
                    <i class="fas fa-network-wired"></i>
                    Interface Configuration
                </h6>
            </div>
            <div class="col-md-6">
                <label class="form-label">
                    PCIe Address <span class="text-danger">*</span>
                </label>
                <input type="text" class="form-control"
                    id="capture-pci-address"
                    value="${escapeHtml(interfacePCI)}"
                    placeholder="0000:3b:00.0">
                <small class="text-muted">
                    PCIe address (use <code>lspci | grep Ethernet</code>)
                </small>
            </div>
            <div class="col-md-6">
                <label class="form-label">Threads</label>
                <input type="text" class="form-control"
                    id="capture-threads"
                    value="${escapeHtml(threads)}"
                    placeholder="auto">
                <small class="text-muted">
                    Number of RX/TX queues
                </small>
            </div>

            <!-- Network Settings -->
            <div class="col-md-12 mt-3">
                <h6 class="border-bottom pb-2">
                    <i class="fas fa-sliders-h"></i> Network Settings
                </h6>
            </div>
            <div class="col-md-4">
                <label class="form-label">MTU</label>
                <input type="number" class="form-control"
                    id="capture-mtu"
                    value="${escapeHtml(mtu)}"
                    placeholder="1500">
                <small class="text-muted">Maximum Transmission Unit</small>
            </div>
            <div class="col-md-4">
                <div class="form-check form-switch mt-4">
                    <input type="checkbox" class="form-check-input"
                        id="capture-promisc" ${promisc ? 'checked' : ''}>
                    <label class="form-check-label" for="capture-promisc">
                        Promiscuous Mode
                    </label>
                </div>
            </div>
            <div class="col-md-4">
                <div class="form-check form-switch mt-4">
                    <input type="checkbox" class="form-check-input"
                        id="capture-multicast" ${multicast ? 'checked' : ''}>
                    <label class="form-check-label" for="capture-multicast">
                        Multicast
                    </label>
                </div>
            </div>

            <!-- Checksum Settings -->
            <div class="col-md-6">
                <div class="form-check form-switch">
                    <input type="checkbox" class="form-check-input"
                        id="capture-checksum-checks"
                        ${checksumChecks ? 'checked' : ''}>
                    <label class="form-check-label"
                        for="capture-checksum-checks">
                        Checksum Validation
                    </label>
                </div>
                <small class="text-muted">
                    Enable checksum validation by Suricata
                </small>
            </div>
            <div class="col-md-6">
                <div class="form-check form-switch">
                    <input type="checkbox" class="form-check-input"
                        id="capture-checksum-offload"
                        ${checksumOffload ? 'checked' : ''}>
                    <label class="form-check-label"
                        for="capture-checksum-offload">
                        Checksum Offload
                    </label>
                </div>
                <small class="text-muted">
                    Offload checksum validation to NIC
                </small>
            </div>

            <!-- Memory Settings -->
            <div class="col-md-12 mt-3">
                <h6 class="border-bottom pb-2">
                    <i class="fas fa-memory"></i> Memory Pool Settings
                </h6>
            </div>
            <div class="col-md-6">
                <label class="form-label">Mempool Size</label>
                <input type="number" class="form-control"
                    id="capture-mempool-size"
                    value="${escapeHtml(mempoolSize)}"
                    placeholder="65535">
                <small class="text-muted">
                    Number of elements in mbuf pool (optimum: 2^n - 1)
                </small>
            </div>
            <div class="col-md-6">
                <label class="form-label">Mempool Cache Size</label>
                <input type="number" class="form-control"
                    id="capture-mempool-cache-size"
                    value="${escapeHtml(mempoolCacheSize)}"
                    placeholder="257">
                <small class="text-muted">
                    Cache size (≤ 512 and ≤ mempool-size/1.5)
                </small>
            </div>

            <!-- Descriptors -->
            <div class="col-md-12 mt-3">
                <h6 class="border-bottom pb-2">
                    <i class="fas fa-layer-group"></i> Ring Descriptors
                </h6>
            </div>
            <div class="col-md-6">
                <label class="form-label">RX Descriptors</label>
                <input type="number" class="form-control"
                    id="capture-rx-descriptors"
                    value="${escapeHtml(rxDescriptors)}"
                    placeholder="1024">
                <small class="text-muted">Number of receive descriptors</small>
            </div>
            <div class="col-md-6">
                <label class="form-label">TX Descriptors</label>
                <input type="number" class="form-control"
                    id="capture-tx-descriptors"
                    value="${escapeHtml(txDescriptors)}"
                    placeholder="1024">
                <small class="text-muted">Number of transmit descriptors</small>
            </div>

            <!-- IPS Mode -->
            <div class="col-md-12 mt-3">
                <h6 class="border-bottom pb-2">
                    <i class="fas fa-shield-alt"></i> IPS Mode
                </h6>
            </div>
            <div class="col-md-6">
                <label class="form-label">Copy Mode</label>
                <select class="form-select" id="capture-copy-mode">
                    <option value="none"${
                        copyMode === 'none' ? ' selected' : ''
                    }>None (IDS Mode)</option>
                    <option value="tap"${
                        copyMode === 'tap' ? ' selected' : ''
                    }>TAP (Forward All + Alerts)</option>
                    <option value="ips"${
                        copyMode === 'ips' ? ' selected' : ''
                    }>IPS (Forward + Drop)</option>
                </select>
                <small class="text-muted">
                    IPS mode for inline deployment
                </small>
            </div>
            <div class="col-md-6">
                <label class="form-label">Copy Interface</label>
                <input type="text" class="form-control"
                    id="capture-copy-iface"
                    value="${escapeHtml(copyIface)}"
                    placeholder="0000:3b:00.1">
                <small class="text-muted">
                    PCIe address of second interface (for IPS mode)
                </small>
            </div>

            <div class="col-md-12 mt-3">
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    <strong>Memory Calculation:</strong>
                    Required hugepages ≈ (mempool-size × MTU) bytes per interface
                </div>
            </div>
        `;
    }

    /**
     * Render PCAP configuration fields
     */
    function renderPcapFields(config) {
        const interfaceName = config.interface || '';

        return `
            <div class="col-md-12">
                <label class="form-label">Interface</label>
                <input type="text" class="form-control"
                    id="capture-interface"
                    value="${escapeHtml(interfaceName)}"
                    placeholder="eth0">
                <small class="text-muted">
                    Network interface for PCAP capture.
                </small>
            </div>
            <div class="col-md-12">
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    PCAP is the legacy packet capture method.
                    Consider using AF-Packet or AF-XDP for better performance.
                </div>
            </div>
        `;
    }

    /**
     * Save packet capture configuration
     */
    function saveConfig() {
        clearFeedback('packet-capture-error', 'packet-capture-success');

        const $btn = $('#save-packet-capture-btn');
        const originalHtml = setButtonLoading($btn, true);

        const payload = {};
        const captureType = currentCaptureType;

        if (captureType === 'af-packet') {
            payload.interface = $('#capture-interface').val().trim();
            payload.threads = $('#capture-threads').val().trim() || 'auto';
            const clusterId = parseInt($('#capture-cluster-id').val(), 10);
            if (!isNaN(clusterId)) payload['cluster-id'] = clusterId;
            payload['cluster-type'] = $('#capture-cluster-type').val();
            payload.defrag = $('#capture-defrag').is(':checked');
            payload['use-mmap'] = $('#capture-use-mmap').is(':checked');
            payload['tpacket-v3'] = $('#capture-tpacket-v3').is(':checked');
            payload.promisc = $('#capture-promisc').is(':checked');
        } else if (captureType === 'af-xdp') {
            payload.interface = $('#capture-interface').val().trim();
            payload.threads = $('#capture-threads').val().trim() || 'auto';
            payload['enable-busy-poll'] =
                $('#capture-busy-poll').is(':checked');
            const busyPollTime =
                parseInt($('#capture-busy-poll-time').val(), 10);
            if (!isNaN(busyPollTime)) {
                payload['busy-poll-time'] = busyPollTime;
            }
            const busyPollBudget =
                parseInt($('#capture-busy-poll-budget').val(), 10);
            if (!isNaN(busyPollBudget)) {
                payload['busy-poll-budget'] = busyPollBudget;
            }
        } else if (captureType === 'dpdk') {
            payload['eal-params'] = {
                'proc-type': $('#capture-proc-type').val()
            };

            const interfaceConfig = {
                'interface': $('#capture-pci-address').val().trim()
                    || '0000:3b:00.0',
                'threads': $('#capture-threads').val().trim() || 'auto',
                'promisc': $('#capture-promisc').is(':checked'),
                'multicast': $('#capture-multicast').is(':checked'),
                'checksum-checks':
                    $('#capture-checksum-checks').is(':checked'),
                'checksum-checks-offload':
                    $('#capture-checksum-offload').is(':checked'),
            };

            const mtu = parseInt($('#capture-mtu').val(), 10);
            if (!isNaN(mtu)) interfaceConfig.mtu = mtu;

            const mempoolSize =
                parseInt($('#capture-mempool-size').val(), 10);
            if (!isNaN(mempoolSize)) {
                interfaceConfig['mempool-size'] = mempoolSize;
            }

            const mempoolCacheSize =
                parseInt($('#capture-mempool-cache-size').val(), 10);
            if (!isNaN(mempoolCacheSize)) {
                interfaceConfig['mempool-cache-size'] = mempoolCacheSize;
            }

            const rxDescriptors =
                parseInt($('#capture-rx-descriptors').val(), 10);
            if (!isNaN(rxDescriptors)) {
                interfaceConfig['rx-descriptors'] = rxDescriptors;
            }

            const txDescriptors =
                parseInt($('#capture-tx-descriptors').val(), 10);
            if (!isNaN(txDescriptors)) {
                interfaceConfig['tx-descriptors'] = txDescriptors;
            }

            interfaceConfig['copy-mode'] = $('#capture-copy-mode').val();
            interfaceConfig['copy-iface'] =
                $('#capture-copy-iface').val().trim() || 'none';

            payload.interfaces = [interfaceConfig];
        } else if (captureType === 'pcap') {
            payload.interface = $('#capture-interface').val().trim();
        }

        apiPost(
            `/api/suricata-config/packet-capture/${captureType}`,
            { config: payload },
            function(data) {
                if (data.success) {
                    packetCaptureConfig = payload;
                    showSuccess(
                        'packet-capture-success',
                        data.message || 'Configuration saved.'
                    );
                    setTimeout(function() {
                        $('#packetCaptureModal').modal('hide');
                    }, 1200);
                } else {
                    showError(
                        'packet-capture-error',
                        data.message || 'Failed to save configuration'
                    );
                }
                setButtonLoading($btn, false, originalHtml);
            },
            function(message) {
                showError('packet-capture-error', message);
                setButtonLoading($btn, false, originalHtml);
            }
        );
    }

    /**
     * Initialize module
     */
    function init() {
        // Capture type selector change handler
        $('#capture-type-selector').on('change', function() {
            const captureType = $(this).val();
            currentCaptureType = captureType;
            loadConfig(captureType);
        });

        // Save button handler
        $('#save-packet-capture-btn').off('click').on('click', saveConfig);
    }

    // Public API
    return {
        init: init,
        openModal: openModal,
        saveConfig: saveConfig
    };
})();

// Initialize when document is ready
$(document).ready(function() {
    PacketCaptureConfig.init();
});

// Expose global function for backward compatibility
function openPacketCaptureModal(captureType) {
    PacketCaptureConfig.openModal(captureType);
}
