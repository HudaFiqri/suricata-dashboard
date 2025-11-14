// MongoDB Indexes Setup
// Migration: 002
// Description: Create indexes for optimal query performance

use suricata;

// ============================================================================
// EVENTS COLLECTION INDEXES
// ============================================================================

print("Creating indexes for 'events' collection...");

// Agent + Time (most common query)
db.events.createIndex({ agent_id: 1, timestamp: -1 });
print("  ✓ agent_id + timestamp");

// Agent + Event Type + Time
db.events.createIndex({ agent_id: 1, event_type: 1, timestamp: -1 });
print("  ✓ agent_id + event_type + timestamp");

// Source IP + Time
db.events.createIndex({ "indexed.src_ip": 1, timestamp: -1 });
print("  ✓ indexed.src_ip + timestamp");

// Destination IP + Time
db.events.createIndex({ "indexed.dest_ip": 1, timestamp: -1 });
print("  ✓ indexed.dest_ip + timestamp");

// Signature ID + Time (for alert queries)
db.events.createIndex({ "indexed.signature_id": 1, timestamp: -1 });
print("  ✓ indexed.signature_id + timestamp");

// Severity + Time (for alert filtering)
db.events.createIndex({ "indexed.severity": 1, timestamp: -1 });
print("  ✓ indexed.severity + timestamp");

// General timestamp index
db.events.createIndex({ timestamp: -1 });
print("  ✓ timestamp");

// TTL index for auto-deletion (90 days retention)
db.events.createIndex(
    { expire_at: 1 },
    { expireAfterSeconds: 0 }
);
print("  ✓ expire_at (TTL)");

// Text search index
db.events.createIndex({
    "raw_event.alert.signature": "text",
    "indexed.src_ip": "text",
    "indexed.dest_ip": "text"
});
print("  ✓ text search index");

// ============================================================================
// LOGS COLLECTION INDEXES
// ============================================================================

print("\nCreating indexes for 'logs' collection...");

// Agent + Time
db.logs.createIndex({ agent_id: 1, timestamp: -1 });
print("  ✓ agent_id + timestamp");

// Level + Time
db.logs.createIndex({ level: 1, timestamp: -1 });
print("  ✓ level + timestamp");

// General timestamp
db.logs.createIndex({ timestamp: -1 });
print("  ✓ timestamp");

// TTL index (30 days retention for logs)
db.logs.createIndex(
    { expire_at: 1 },
    { expireAfterSeconds: 0 }
);
print("  ✓ expire_at (TTL)");

// Text search
db.logs.createIndex({ message: "text" });
print("  ✓ text search on message");

// ============================================================================
// PCAP_CAPTURES COLLECTION INDEXES
// ============================================================================

print("\nCreating indexes for 'pcap_captures' collection...");

// Agent + Start Time
db.pcap_captures.createIndex({ agent_id: 1, started_at: -1 });
print("  ✓ agent_id + started_at");

// Status
db.pcap_captures.createIndex({ status: 1 });
print("  ✓ status");

// ============================================================================
// VALIDATION
// ============================================================================

print("\n" + "=".repeat(60));
print("Index Creation Summary:");
print("=".repeat(60));

print("\nEvents indexes:");
db.events.getIndexes().forEach(function(idx) {
    print("  - " + idx.name);
});

print("\nLogs indexes:");
db.logs.getIndexes().forEach(function(idx) {
    print("  - " + idx.name);
});

print("\nPCAP Captures indexes:");
db.pcap_captures.getIndexes().forEach(function(idx) {
    print("  - " + idx.name);
});

print("\n✓ All indexes created successfully!");
