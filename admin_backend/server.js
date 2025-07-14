const express = require('express');
const { MongoClient } = require('mongodb');
const session = require('express-session');
const dotenv = require('dotenv');
const bodyParser = require('body-parser');
const bcrypt = require('bcrypt');
const { v4: uuidv4 } = require('uuid');

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
    } catch (error) {
        console.error("Error creating collections:", error);
    }
}

async function AdminApproval({
  action_target_id = null,
  meta_data,
  original_data = null,
  type,
  collection_name,
  admin_id,
  db,
  request_reason = null
}) {
  if (!meta_data || !type || !collection_name || !admin_id) {
    return { success: false, error: 'Missing required fields' };
  }

  const tempCollection = db.collection('temp');

  const newOperation = {
    unique_id: uuidv4(),
    action_target_id,
    meta_data,
    original_data,
    type: type.toLowerCase(),
    collection_name,
    status: 'pending',
    admin_id,
    reviewed_by: null,
    review_notes: null,
    request_reason,
    date_time: new Date()
  };

  try {
    await tempCollection.insertOne(newOperation);
    return { success: true, message: 'Operation queued for approval' };
  } catch (error) {
    console.error('Error queuing operation:', error);
    return { success: false, error: 'Failed to queue operation' };
  }
}

const loginAttempts = new Map();
const MAX_ATTEMPTS = 10;
const BLOCK_DURATION = 10 * 60 * 1000; // 10 minutes

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