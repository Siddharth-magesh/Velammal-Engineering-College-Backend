const express = require('express');
const { MongoClient } = require('mongodb');
const session = require('express-session');
const dotenv = require('dotenv');
const bodyParser = require('body-parser');
const bcrypt = require('bcrypt');
const { v4: uuidv4 } = require('uuid');
const { ObjectId } = require('mongodb');

dotenv.config({quiet: true});

const app = express();
const port = process.env.PORT || 5000;

app.use(bodyParser.json());
app.use(express.json());
app.use(session({
    secret: process.env.SESSION_SECRET || '12345678',
    resave: false,
    saveUninitialized: true,
    cookie: {
        secure: false,
        maxAge: 24 * 60 * 60 * 1000
    }
}));

const mongoUri = process.env.MONGO_URI;
const dbName = process.env.DB_NAME;
const client = new MongoClient(mongoUri);
let db;

async function connectToDatabase() {
    try {
        await client.connect();
        db = client.db(dbName);
        console.log("Connected to MongoDB");
        await createCollectionIfNotExists(db);
    } catch (error) {
        console.error("MongoDB connection error:", error);
    }
}
connectToDatabase();

app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});

async function createCollectionIfNotExists(db) {
    try {
        const collections = await db.listCollections().toArray();
        const collectionNames = collections.map(col => col.name);
        if (!collectionNames.includes('admin_details')) {
            await db.createCollection('admin_details');
            console.log("Collection 'admin_details' created");
        }
        if (!collectionNames.includes('temp')) {
            await db.createCollection('temp');
            console.log("Collection 'temp' created");
        }
        if (!collectionNames.includes('admin_archive')) {
            await db.createCollection('admin_archive');
            console.log("Collection 'admin_archive' created");
        }
    } catch (error) {
        console.error("Error creating collections:", error);
    }
}

// Middleware factory: accepts one or more access keys and returns a middleware function
function verifyAdminAccess(...requiredAccessKeys) {
    return (req, res, next) => {
        if (!req.session || !req.session.admin_auth) {
            return res.status(401).json({ error: 'Unauthorized: Admin not logged in' });
        }

        const sectors = req.session.authenticated_sectors || {};

        const hasAccess = requiredAccessKeys.every(key => sectors[key] === true);

        if (!hasAccess) {
            return res.status(403).json({
                error: `Forbidden: Missing required access rights (${requiredAccessKeys.join(', ')})`
            });
        }
        next();
    };
}

const loginAttempts = new Map();
const MAX_ATTEMPTS = 10;
const BLOCK_DURATION = 10 * 60 * 1000; // 10 minutes

// Get all approval requests by status
app.get('/api/fetch_admin_requests', async (req, res) => {
    if (
        !req.session ||
        !req.session.admin_auth ||
        !req.session.authenticated_sectors ||
        req.session.authenticated_sectors.approval_access !== true
    ) {
        return res.status(403).json({ error: 'Unauthorized: approval access denied' });
    }
    const { status } = req.body;

    const validStatuses = ['pending', 'approved', 'declined'];
    const statusFilter = status?.toLowerCase();

    if (!statusFilter || !validStatuses.includes(statusFilter)) {
        return res.status(400).json({ error: 'Invalid or missing status. Must be one of: pending, approved, declined' });
    }

    try {
        const requests = await db.collection('temp')
            .find({ status: statusFilter })
            .sort({ date_time: -1 })
            .toArray();

        res.json({ requests });
    } catch (error) {
        console.error('Error fetching approval requests:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

//Admin Login
app.post('/api/admin_login', async (req, res) => {
    let { username, password } = req.body;
    username = username?.trim().toLowerCase();
    if (!username || !password) {
        return res.status(400).json({ error: 'Username and password are required' });
    }
    const ip = req.ip;
    const now = Date.now();
    const attempt = loginAttempts.get(ip) || { count: 0, time: now };

    if (attempt.count >= MAX_ATTEMPTS && now - attempt.time < BLOCK_DURATION) {
        return res.status(429).json({ error: 'Too many login attempts. Please try again later.' });
    }

    try {
        const user = await db.collection('admin_details').findOne({ username });

        if (!user) {
            loginAttempts.set(ip, {
                count: attempt.count + 1,
                time: attempt.time
            });
            return res.status(401).json({ error: 'Invalid username or password' });
        }

        if (user.status && user.status.toLowerCase() !== 'active') {
            return res.status(403).json({ error: 'Account is inactive or blocked. Contact admin.' });
        }

        const isPasswordValid = await bcrypt.compare(password, user.password);
        if (!isPasswordValid) {
            loginAttempts.set(ip, {
                count: attempt.count + 1,
                time: attempt.time
            });
            return res.status(401).json({ error: 'Invalid username or password' });
        }

        loginAttempts.delete(ip);

        req.session.username = user.username;
        req.session.authenticated_sectors = user.authenticated_sectors || [];
        req.session.admin_auth = true;

        res.json({ message: 'Login successful', username: user.username });

    } catch (error) {
        console.error("Login error:", error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

//Admin SignUp
app.post('/api/admin_signup', async (req, res) => {
    if (
        !req.session ||
        !req.session.admin_auth ||
        !req.session.authenticated_sectors ||
        req.session.authenticated_sectors.signup_access !== true
    ) {
        return res.status(403).json({ error: 'Unauthorized: signup access denied' });
    }
    let { username, password, authenticated_sectors } = req.body;

    username = username?.trim().toLowerCase();
    if (!username || !password || typeof authenticated_sectors !== 'object') {
        return res.status(400).json({ error: 'Username, password, and authenticated_sectors are required' });
    }

    try {
        const existingUser = await db.collection('admin_details').findOne({ username });
        if (existingUser) {
            return res.status(409).json({ error: 'Username already exists' });
        }

        const hashedPassword = await bcrypt.hash(password, 10);

        const newUser = {
            username,
            password: hashedPassword,
            authenticated_sectors,
            status: 'active',
            createdAt: new Date()
        };

        await db.collection('admin_details').insertOne(newUser);

        res.status(201).json({ message: 'Signup successful' });

    } catch (error) {
        console.error('Signup error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Landing Page Update
app.post('/api/update_landing_page', verifyAdminAccess('landing_page_access'), async (req, res) => {
    try {
        const { metadata, collection, category, type, title } = req.body;
        const admin_id = req.session.username;

        if (!metadata || !collection || !type || !title || !category) {
            return res.status(400).json({ error: 'Missing required fields in request body' });
        }

        const dbCollection = db.collection(collection);
        const existingDoc = await dbCollection.findOne({});

        if (!existingDoc || !existingDoc.landing_page_details) {
            return res.status(404).json({ error: 'Landing page details not found' });
        }

        const originalLandingPageDetails = existingDoc.landing_page_details;

        const originalFields = {};
        for (const key in metadata) {
            originalFields[key] = originalLandingPageDetails[key] ?? null;
        }

        const tempDoc = {
            unique_id: uuidv4(),
            action_target_id: existingDoc._id,
            metadata: { landing_page_details: metadata },
            original_data: { landing_page_details: originalFields },
            type,
            collection_name: collection,
            category,
            admin_id,
            title,
            status: 'pending',
            date: new Date().toISOString(),
            reviewed_by: null,
            reviewed_notes: null
        };

        await db.collection('temp').insertOne(tempDoc);

        return res.status(200).json({
            message: 'Landing page update request submitted for approval',
            request_id: tempDoc.unique_id,
            changes: metadata
        });

    } catch (err) {
        console.error('Error updating landing page:', err);
        return res.status(500).json({ error: 'Internal server error' });
    }
});

//Superior Admin Review
app.post('/api/review_landing_page_request', verifyAdminAccess('landing_page_access'), async (req, res) => {
    try {
        const { unique_id, decision_by, reviewed_notes, actions } = req.body;

        if (!unique_id || !decision_by || !actions) {
            return res.status(400).json({ error: 'Missing required fields' });
        }

        const tempCollection = db.collection('temp');
        const landingPageCollection = db.collection('landing_page_details');
        const adminArchiveCollection = db.collection('admin_archive');

        const requestDoc = await tempCollection.findOne({ unique_id });
        if (!requestDoc) return res.status(404).json({ error: 'Request not found' });

        const { metadata, action_target_id } = requestDoc;

        const approvedUpdates = {};
        const rejectedFields = [];

        for (const section in actions) {
            if (!metadata[section]) continue;

            for (const field in actions[section]) {
                const decision = actions[section][field];
                const value = metadata[section][field];

                if (decision === 'approve') {
                    approvedUpdates[`${section}.${field}`] = value;
                } else if (decision === 'reject') {
                    rejectedFields.push(`${section}.${field}`);
                }
            }
        }

        let updateStatus = 'rejected';

        if (Object.keys(approvedUpdates).length > 0) {
            await landingPageCollection.updateOne(
                { _id: new ObjectId(action_target_id) },
                { $set: approvedUpdates }
            );
            updateStatus = rejectedFields.length === 0 ? 'approved' : 'partially_approved';
        }

        const updatedRequest = {
            ...requestDoc,
            reviewed_by: decision_by,
            reviewed_notes: reviewed_notes || '',
            status: 'managed',
            actions
        };

        await tempCollection.updateOne(
            { unique_id },
            { $set: { reviewed_by: decision_by, reviewed_notes, status: 'managed', actions } }
        );

        await adminArchiveCollection.insertOne(updatedRequest);
        await tempCollection.deleteOne({ unique_id });

        return res.status(200).json({
            message: `Request ${updateStatus.replace('_', ' ')} and archived successfully.`,
            approved_fields: approvedUpdates,
            rejected_fields: rejectedFields
        });

    } catch (err) {
        console.error('Error processing landing page request review:', err);
        return res.status(500).json({ error: 'Internal server error' });
    }
});
