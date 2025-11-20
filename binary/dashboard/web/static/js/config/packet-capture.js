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
            `/api/v1/agents/${window.AGENT_ID}/config/packet-capture/${captureType}`,
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
        const mmapLocked = toBoolean(config['mmap-locked'], true);
        const tpacketV3 = toBoolean(config['tpacket-v3'], true);
        const ringSize = config['ring-size'] || 2048;
        const blockSize = config['block-size'] || 32768;
        const blockTimeout = config['block-timeout'] || 10;
        const useEmergencyFlush = toBoolean(config['use-emergency-flush'], true);
        const bufferSize = config['buffer-size'] || 32768;
        const disablePromisc = toBoolean(config['disable-promisc'], false);
        const checksumChecks = config['checksum-checks'] || 'kernel';
        const bpfFilter = config['bpf-filter'] || '';
        const copyMode = config['copy-mode'] || '';
        const copyIface = config['copy-iface'] || '';

        return `
            <!-- Basic Settings -->
            <div class="col-md-12">
                <h6 class="border-bottom pb-2">
                    <i class="fas fa-network-wired"></i> Basic Settings
                </h6>
            </div>
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

            <!-- Cluster Settings -->
            <div class="col-md-12 mt-3">
                <h6 class="border-bottom pb-2">
                    <i class="fas fa-server"></i> Cluster Settings
                </h6>
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

            <!-- Ring Buffer Settings -->
            <div class="col-md-12 mt-3">
                <h6 class="border-bottom pb-2">
                    <i class="fas fa-ring"></i> Ring Buffer Settings
                </h6>
            </div>
            <div class="col-md-4">
                <label class="form-label">Ring Size</label>
                <input type="number" class="form-control"
                    id="capture-ring-size"
                    value="${escapeHtml(ringSize)}"
                    placeholder="2048">
                <small class="text-muted">Number of packets in ring</small>
            </div>
            <div class="col-md-4">
                <label class="form-label">Block Size</label>
                <input type="number" class="form-control"
                    id="capture-block-size"
                    value="${escapeHtml(blockSize)}"
                    placeholder="32768">
                <small class="text-muted">Block size in bytes (tpacket_v3)</small>
            </div>
            <div class="col-md-4">
                <label class="form-label">Block Timeout (ms)</label>
                <input type="number" class="form-control"
                    id="capture-block-timeout"
                    value="${escapeHtml(blockTimeout)}"
                    placeholder="10">
                <small class="text-muted">Timeout for incomplete blocks</small>
            </div>

            <!-- Buffer Settings -->
            <div class="col-md-12 mt-3">
                <h6 class="border-bottom pb-2">
                    <i class="fas fa-memory"></i> Buffer Settings
                </h6>
            </div>
            <div class="col-md-6">
                <label class="form-label">Buffer Size</label>
                <input type="number" class="form-control"
                    id="capture-buffer-size"
                    value="${escapeHtml(bufferSize)}"
                    placeholder="32768">
                <small class="text-muted">Receive buffer size in bytes</small>
            </div>
            <div class="col-md-6">
                <label class="form-label">Checksum Checks</label>
                <select class="form-select" id="capture-checksum-checks">
                    ${['kernel', 'yes', 'no', 'auto']
                        .map(opt => `<option value="${opt}"${
                            opt === checksumChecks ? ' selected' : ''
                        }>${opt}</option>`).join('')}
                </select>
                <small class="text-muted">Checksum validation mode</small>
            </div>

            <!-- Filter Settings -->
            <div class="col-md-12 mt-3">
                <h6 class="border-bottom pb-2">
                    <i class="fas fa-filter"></i> Filter & IPS Settings
                </h6>
            </div>
            <div class="col-md-12">
                <label class="form-label">BPF Filter</label>
                <input type="text" class="form-control"
                    id="capture-bpf-filter"
                    value="${escapeHtml(bpfFilter)}"
                    placeholder="port 80 or udp">
                <small class="text-muted">Berkeley Packet Filter expression (optional)</small>
            </div>
            <div class="col-md-6">
                <label class="form-label">Copy Mode</label>
                <select class="form-select" id="capture-copy-mode">
                    <option value=""${copyMode === '' ? ' selected' : ''}>None</option>
                    <option value="ips"${copyMode === 'ips' ? ' selected' : ''}>IPS</option>
                    <option value="tap"${copyMode === 'tap' ? ' selected' : ''}>TAP</option>
                </select>
                <small class="text-muted">IPS/TAP mode for packet forwarding</small>
            </div>
            <div class="col-md-6">
                <label class="form-label">Copy Interface</label>
                <input type="text" class="form-control"
                    id="capture-copy-iface"
                    value="${escapeHtml(copyIface)}"
                    placeholder="eth1">
                <small class="text-muted">Target interface for copy mode</small>
            </div>

            <!-- Feature Toggles -->
            <div class="col-md-12 mt-3">
                <h6 class="border-bottom pb-2">
                    <i class="fas fa-toggle-on"></i> Feature Toggles
                </h6>
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
                        'capture-mmap-locked',
                        'Lock Memory Map',
                        mmapLocked
                    )}
                    ${renderCheckbox(
                        'capture-tpacket-v3',
                        'TPACKET v3',
                        tpacketV3
                    )}
                    ${renderCheckbox(
                        'capture-use-emergency-flush',
                        'Emergency Flush',
                        useEmergencyFlush
                    )}
                    ${renderCheckbox(
                        'capture-disable-promisc',
                        'Disable Promiscuous',
                        disablePromisc
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
        const interfaceName = config.interface || 'default';
        const threads = config.threads || 'auto';
        const disablePromisc = toBoolean(config['disable-promisc'], false);
        const forceXdpMode = config['force-xdp-mode'] || 'none';
        const forceBindMode = config['force-bind-mode'] || 'none';
        const memUnaligned = toBoolean(config['mem-unaligned'], false);
        const busyPoll = toBoolean(config['enable-busy-poll'], true);
        const busyPollTime = config['busy-poll-time'] || 20;
        const busyPollBudget = config['busy-poll-budget'] || 64;
        const groFlushTimeout = config['gro-flush-timeout'] || 2000000;
        const napiDeferHardIrq = config['napi-defer-hard-irq'] || 2;

        return `
            <!-- Basic Settings -->
            <div class="col-md-12">
                <h6 class="border-bottom pb-2">
                    <i class="fas fa-network-wired"></i> Basic Settings
                </h6>
            </div>
            <div class="col-md-6">
                <label class="form-label">Interface</label>
                <input type="text" class="form-control"
                    id="capture-interface"
                    value="${escapeHtml(interfaceName)}"
                    placeholder="default">
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
                <small class="text-muted">Number of reader threads (auto = cores or RX queues).</small>
            </div>

            <!-- XDP Mode Settings -->
            <div class="col-md-12 mt-3">
                <h6 class="border-bottom pb-2">
                    <i class="fas fa-cogs"></i> XDP Mode Settings
                </h6>
            </div>
            <div class="col-md-6">
                <label class="form-label">Force XDP Mode</label>
                <select class="form-select" id="capture-force-xdp-mode">
                    ${['none', 'drv', 'skb']
                        .map(opt => `<option value="${opt}"${
                            opt === forceXdpMode ? ' selected' : ''
                        }>${opt.toUpperCase()}</option>`).join('')}
                </select>
                <small class="text-muted">XDP mode: DRV (driver), SKB (generic), or None (auto)</small>
            </div>
            <div class="col-md-6">
                <label class="form-label">Force Bind Mode</label>
                <select class="form-select" id="capture-force-bind-mode">
                    ${['none', 'zero', 'copy']
                        .map(opt => `<option value="${opt}"${
                            opt === forceBindMode ? ' selected' : ''
                        }>${opt === 'none' ? 'None (Auto)' : opt === 'zero' ? 'Zero-Copy' : 'Copy'}</option>`).join('')}
                </select>
                <small class="text-muted">Socket bind mode (zero-copy or copy)</small>
            </div>

            <!-- Busy Polling Settings -->
            <div class="col-md-12 mt-3">
                <h6 class="border-bottom pb-2">
                    <i class="fas fa-clock"></i> Busy Polling Settings
                </h6>
            </div>
            <div class="col-md-4">
                <label class="form-label">Busy Poll Time (μs)</label>
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

            <!-- NAPI Settings -->
            <div class="col-md-12 mt-3">
                <h6 class="border-bottom pb-2">
                    <i class="fas fa-microchip"></i> NAPI Context Settings
                </h6>
            </div>
            <div class="col-md-6">
                <label class="form-label">GRO Flush Timeout</label>
                <input type="number" class="form-control"
                    id="capture-gro-flush-timeout"
                    value="${escapeHtml(groFlushTimeout)}"
                    placeholder="2000000">
                <small class="text-muted">GRO flush timeout in nanoseconds</small>
            </div>
            <div class="col-md-6">
                <label class="form-label">NAPI Defer Hard IRQ</label>
                <input type="number" class="form-control"
                    id="capture-napi-defer-hard-irq"
                    value="${escapeHtml(napiDeferHardIrq)}"
                    placeholder="2">
                <small class="text-muted">Defer hard IRQ count for NAPI</small>
            </div>

            <!-- Feature Toggles -->
            <div class="col-md-12 mt-3">
                <h6 class="border-bottom pb-2">
                    <i class="fas fa-toggle-on"></i> Feature Toggles
                </h6>
            </div>
            <div class="col-md-12">
                <div class="row">
                    ${renderCheckbox(
                        'capture-disable-promisc',
                        'Disable Promiscuous Mode',
                        disablePromisc
                    )}
                    ${renderCheckbox(
                        'capture-mem-unaligned',
                        'Unaligned Memory (requires hugepages)',
                        memUnaligned
                    )}
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
        const interfaceName = config.interface || 'eth0';
        const bufferSize = config['buffer-size'] || 16777216;
        const bpfFilter = config['bpf-filter'] || '';
        const checksumChecks = config['checksum-checks'] || 'auto';
        const threads = config.threads || 16;
        const promisc = toBoolean(config.promisc, true);
        const snaplen = config.snaplen || 1518;

        return `
            <!-- Basic Settings -->
            <div class="col-md-12">
                <h6 class="border-bottom pb-2">
                    <i class="fas fa-network-wired"></i> Basic Settings
                </h6>
            </div>
            <div class="col-md-6">
                <label class="form-label">Interface</label>
                <input type="text" class="form-control"
                    id="capture-interface"
                    value="${escapeHtml(interfaceName)}"
                    placeholder="eth0">
                <small class="text-muted">
                    Network interface for PCAP capture.
                </small>
            </div>
            <div class="col-md-6">
                <label class="form-label">Threads</label>
                <input type="number" class="form-control"
                    id="capture-threads"
                    value="${escapeHtml(threads)}"
                    placeholder="16">
                <small class="text-muted">
                    Number of capture threads (typically 16)
                </small>
            </div>

            <!-- Buffer Settings -->
            <div class="col-md-12 mt-3">
                <h6 class="border-bottom pb-2">
                    <i class="fas fa-memory"></i> Buffer Settings
                </h6>
            </div>
            <div class="col-md-6">
                <label class="form-label">Buffer Size</label>
                <input type="number" class="form-control"
                    id="capture-buffer-size"
                    value="${escapeHtml(bufferSize)}"
                    placeholder="16777216">
                <small class="text-muted">Total ring memory (> 1% of bandwidth)</small>
            </div>
            <div class="col-md-6">
                <label class="form-label">Snaplen</label>
                <input type="number" class="form-control"
                    id="capture-snaplen"
                    value="${escapeHtml(snaplen)}"
                    placeholder="1518">
                <small class="text-muted">Maximum bytes per packet (defaults to MTU)</small>
            </div>

            <!-- Checksum & Filter Settings -->
            <div class="col-md-12 mt-3">
                <h6 class="border-bottom pb-2">
                    <i class="fas fa-filter"></i> Checksum & Filter Settings
                </h6>
            </div>
            <div class="col-md-6">
                <label class="form-label">Checksum Checks</label>
                <select class="form-select" id="capture-checksum-checks">
                    ${['auto', 'yes', 'no']
                        .map(opt => `<option value="${opt}"${
                            opt === checksumChecks ? ' selected' : ''
                        }>${opt}</option>`).join('')}
                </select>
                <small class="text-muted">Checksum validation mode</small>
            </div>
            <div class="col-md-6">
                <div class="form-check form-switch mt-4">
                    <input type="checkbox" class="form-check-input"
                        id="capture-promisc" ${promisc ? 'checked' : ''}>
                    <label class="form-check-label" for="capture-promisc">
                        Promiscuous Mode
                    </label>
                </div>
            </div>
            <div class="col-md-12">
                <label class="form-label">BPF Filter</label>
                <input type="text" class="form-control"
                    id="capture-bpf-filter"
                    value="${escapeHtml(bpfFilter)}"
                    placeholder="tcp and port 25">
                <small class="text-muted">Berkeley Packet Filter expression (optional)</small>
            </div>

            <div class="col-md-12 mt-3">
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    <strong>Note:</strong> PCAP is the legacy packet capture method.
                    Consider using AF-Packet or AF-XDP for better performance on Linux.
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

            const ringSize = parseInt($('#capture-ring-size').val(), 10);
            if (!isNaN(ringSize)) payload['ring-size'] = ringSize;

            const blockSize = parseInt($('#capture-block-size').val(), 10);
            if (!isNaN(blockSize)) payload['block-size'] = blockSize;

            const blockTimeout = parseInt($('#capture-block-timeout').val(), 10);
            if (!isNaN(blockTimeout)) payload['block-timeout'] = blockTimeout;

            const bufferSize = parseInt($('#capture-buffer-size').val(), 10);
            if (!isNaN(bufferSize)) payload['buffer-size'] = bufferSize;

            payload['checksum-checks'] = $('#capture-checksum-checks').val();
            payload['bpf-filter'] = $('#capture-bpf-filter').val().trim();
            payload['copy-mode'] = $('#capture-copy-mode').val();
            payload['copy-iface'] = $('#capture-copy-iface').val().trim();

            payload.defrag = $('#capture-defrag').is(':checked');
            payload['use-mmap'] = $('#capture-use-mmap').is(':checked');
            payload['mmap-locked'] = $('#capture-mmap-locked').is(':checked');
            payload['tpacket-v3'] = $('#capture-tpacket-v3').is(':checked');
            payload['use-emergency-flush'] = $('#capture-use-emergency-flush').is(':checked');
            payload['disable-promisc'] = $('#capture-disable-promisc').is(':checked');
        } else if (captureType === 'af-xdp') {
            payload.interface = $('#capture-interface').val().trim();
            payload.threads = $('#capture-threads').val().trim() || 'auto';

            payload['disable-promisc'] = $('#capture-disable-promisc').is(':checked');
            payload['force-xdp-mode'] = $('#capture-force-xdp-mode').val();
            payload['force-bind-mode'] = $('#capture-force-bind-mode').val();
            payload['mem-unaligned'] = $('#capture-mem-unaligned').is(':checked');
            payload['enable-busy-poll'] = $('#capture-busy-poll').is(':checked');

            const busyPollTime = parseInt($('#capture-busy-poll-time').val(), 10);
            if (!isNaN(busyPollTime)) {
                payload['busy-poll-time'] = busyPollTime;
            }

            const busyPollBudget = parseInt($('#capture-busy-poll-budget').val(), 10);
            if (!isNaN(busyPollBudget)) {
                payload['busy-poll-budget'] = busyPollBudget;
            }

            const groFlushTimeout = parseInt($('#capture-gro-flush-timeout').val(), 10);
            if (!isNaN(groFlushTimeout)) {
                payload['gro-flush-timeout'] = groFlushTimeout;
            }

            const napiDeferHardIrq = parseInt($('#capture-napi-defer-hard-irq').val(), 10);
            if (!isNaN(napiDeferHardIrq)) {
                payload['napi-defer-hard-irq'] = napiDeferHardIrq;
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

            const threads = parseInt($('#capture-threads').val(), 10);
            if (!isNaN(threads)) payload.threads = threads;

            const bufferSize = parseInt($('#capture-buffer-size').val(), 10);
            if (!isNaN(bufferSize)) payload['buffer-size'] = bufferSize;

            const snaplen = parseInt($('#capture-snaplen').val(), 10);
            if (!isNaN(snaplen)) payload.snaplen = snaplen;

            payload['checksum-checks'] = $('#capture-checksum-checks').val();
            payload['bpf-filter'] = $('#capture-bpf-filter').val().trim();
            payload.promisc = $('#capture-promisc').is(':checked');
        }

        apiPost(
            `/api/v1/agents/${window.AGENT_ID}/config/packet-capture/${captureType}`,
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
