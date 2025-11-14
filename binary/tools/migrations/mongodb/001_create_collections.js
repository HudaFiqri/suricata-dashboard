// MongoDB Collections Setup
// Migration: 001
// Description: Create collections for events, logs, and PCAP captures

use suricata;

// ============================================================================
// EVENTS COLLECTION (Time-series)
// ============================================================================

db.createCollection("events", {
    timeseries: {
        timeField: "timestamp",
        metaField: "agent_id",
        granularity: "seconds"
    }
});

print("✓ Created 'events' collection with time-series optimization");

// ============================================================================
// LOGS COLLECTION
// ============================================================================

db.createCollection("logs");

print("✓ Created 'logs' collection");

// ============================================================================
// PCAP_CAPTURES COLLECTION
// ============================================================================

db.createCollection("pcap_captures");

print("✓ Created 'pcap_captures' collection");

print("\nCollections created successfully!");
print("Run 002_create_indexes.js next to create indexes.");
