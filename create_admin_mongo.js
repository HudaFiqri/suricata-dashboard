// MongoDB script to create admin user
// Run with: mongosh suricata create_admin_mongo.js

// Switch to suricata database
db = db.getSiblingDB('suricata');

// Check if admin user already exists
const existingUser = db.users.findOne({ username: 'admin' });

if (existingUser) {
    print('✓ Admin user already exists');
    print('  Username: admin');
    print('  User ID: ' + existingUser._id);
} else {
    // Create admin user with bcrypt hash of 'admin'
    // Hash generated with: bcrypt.hashpw('admin'.encode(), bcrypt.gensalt()).decode()
    const result = db.users.insertOne({
        username: 'admin',
        email: 'admin@localhost',
        password_hash: '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5oDhHvYMQKJGe', // 'admin'
        role: 'admin',
        is_active: true,
        created_at: new Date(),
        updated_at: new Date()
    });

    print('✓ Admin user created successfully');
    print('  Username: admin');
    print('  Password: admin');
    print('  Role: admin');
    print('  User ID: ' + result.insertedId);
}
