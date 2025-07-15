const express = require('express');
const { MongoClient } = require('mongodb');
const session = require('express-session');
const dotenv = require('dotenv');
const bodyParser = require('body-parser');
const bcrypt = require('bcrypt');
const { v4: uuidv4 } = require('uuid');
const { ObjectId } = require('mongodb');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const AWS = require('aws-sdk');
const sharp = require('sharp');
const mime = require('mime-types');

dotenv.config({quiet: true});

// Suppress AWS SDK maintenance warning
process.removeAllListeners('warning');
process.on('warning', (warning) => {
  if (!warning.message.includes('AWS SDK for JavaScript (v2) is in maintenance mode')) {
    console.warn(warning);
  }
});

const app = express();
const port = process.env.PORT || 5000;

const BASE_UPLOAD_PATH = path.join(__dirname, 'static', 'TEMP');

function ensureDirectoryExists(dirPath) {
    if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
    }
}

const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        const relativeDestination = req.body.destination || req.destination;
        if (!relativeDestination) {
            return cb(new Error("Missing 'destination' in request"));
        }
        const absolutePath = path.join(BASE_UPLOAD_PATH, relativeDestination);
        if (!absolutePath.startsWith(BASE_UPLOAD_PATH)) {
            return cb(new Error("Invalid upload destination"));
        }
        ensureDirectoryExists(absolutePath);
        cb(null, absolutePath);
    },

    filename: function (req, file, cb) {
        const filename = req.filename; // Always prefer backend-injected name
        if (!filename) {
            return cb(new Error("Missing 'filename' in request"));
        }
        const extension = path.extname(file.originalname);
        const finalName = `${filename}${extension}`;
        cb(null, finalName);
    }
});

const upload = multer({ storage });

AWS.config.update({
  region: process.env.AWS_REGION,
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
});

const s3 = new AWS.S3();

s3.listBuckets((err, data) => {
  if (err) {
    console.error('AWS S3 connection failed:', err.message);
  } else {
    console.log('Connected to AWS S3');
  }
});

async function uploadFileToS3FromPath(localFilePath) {
  try {
    const fileExt = path.extname(localFilePath).toLowerCase();
    const isImage = ['.jpg', '.jpeg', '.png'].includes(fileExt.toLowerCase());

    if (!fs.existsSync(localFilePath)) {
      throw new Error(`File does not exist: ${localFilePath}`);
    }

    const fileBuffer = fs.readFileSync(localFilePath);
    let finalBuffer = fileBuffer;
    let contentType = mime.lookup(fileExt) || 'application/octet-stream';

    let finalKey = localFilePath.replace(/^static[\/\\]TEMP[\/\\]/, 'static/').replace(/\\/g, '/');

    if (isImage) {
      finalBuffer = await sharp(fileBuffer)
        .webp({ quality: 80 })
        .toBuffer();
      contentType = 'image/webp';
      finalKey = finalKey.replace(fileExt, '.webp');
    }

    const params = {
      Bucket: process.env.AWS_S3_NAME,
      Key: finalKey,
      Body: finalBuffer,
      ContentType: contentType,
      ACL: 'public-read',
    };

    const result = await s3.upload(params).promise();

    console.log('Uploaded to S3:', result.Location);
    return {
      s3Path: `/${finalKey}`,
      url: result.Location,
    };
  } catch (error) {
    console.error('S3 Upload Failed:', error.message);
    throw error;
  }
}

module.exports = uploadFileToS3FromPath;

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
app.post('/api/update_landing_page_details', verifyAdminAccess('landing_page_access'), async (req, res) => {
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

//Superior Admin Review for landing page details
app.post('/api/review_landing_page_request', verifyAdminAccess('landing_page_access'), async (req, res) => {
    try {
        const { unique_id, reviewed_notes, actions } = req.body;

        if (!unique_id || !actions) {
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
            reviewed_by: req.session.username,
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

// Update Department Banner
app.post(
    '/api/update_department_banner',
    async (req, res, next) => {
    try {
        const { type, existing_id } = req.body;

        const dbCollection = db.collection('landing_page_details');
        const existingDoc = await dbCollection.findOne({});
        if (!existingDoc) {
            return res.status(404).json({ error: 'Landing page document not found' });
        }

        const departmentBanners = existingDoc.department_banner || [];

        if (type === 'add') {
            const newIndex = departmentBanners.length + 1;
            const paddedIndex = String(newIndex).padStart(3, '0');
            req.filename = paddedIndex;
            req.body.destination = 'images/banner/';
        } else if (type === 'update') {
            const idx = departmentBanners.findIndex(b => b.dept === existing_id);
            if (idx === -1) {
                return res.status(404).json({ error: 'Department banner not found' });
            }
            const currentBanner = departmentBanners[idx];
            const pathParts = currentBanner.banner_image.split('/');
            const existingFilename = pathParts[pathParts.length - 1].split('.')[0]; // '003'
            req.filename = existingFilename;
            req.body.destination = 'images/banner/';
        } else if (type === 'delete') {
            return next();
        } else {
            return res.status(400).json({ error: 'Invalid type specified' });
        }
        next();
    } catch (err) {
        console.error('Error injecting filename/destination:', err);
        return res.status(500).json({ error: 'Internal server error' });
    }
    },
    upload.single('banner_image'),
    verifyAdminAccess('landing_page_access'),
    async (req, res) => {
        try {
            const { metadata, type, title, existing_id } = req.body;
            const admin_id = req.session.username;

            if (!metadata || !type || !title ) {
                return res.status(400).json({ error: 'Missing required fields in request body' });
            }

            const dbCollection = db.collection('landing_page_details');
            const existingDoc = await dbCollection.findOne({});
            if (!existingDoc) {
                return res.status(404).json({ error: 'Landing page document not found' });
            }

            const departmentBanners = existingDoc.department_banner || [];

            if (type === 'add') {
                const uploadedFile = req.file;
                //if (!uploadedFile) {
                  //  return res.status(400).json({ error: 'Banner image file is required' });
                //}

                const paddedIndex = req.filename;
                let bannerImagePath = metadata.banner_image || '';
                if (uploadedFile) {
                    bannerImagePath = `/static${uploadedFile.path.split('/static')[1]}`.replace(/\\/g, '/');
                }
                const redirectURL = `/dept/${paddedIndex}`;

                const newDeptBanner = {
                    ...metadata,
                    banner_image: bannerImagePath,
                    redirect_url: redirectURL
                };

                const tempDoc = {
                    unique_id: uuidv4(),
                    action_target_id: null,
                    metadata: {department_banner : newDeptBanner },
                    original_data: {department_banner : null},
                    type,
                    collection_name: 'landing_page_details',
                    category: 'department_banner',
                    admin_id,
                    title,
                    status: 'pending',
                    date: new Date().toISOString(),
                    reviewed_by: null,
                    reviewed_notes: null
                };

                await db.collection('temp').insertOne(tempDoc);

                return res.status(200).json({
                    message: 'Department banner add request submitted for approval',
                    request_id: tempDoc.unique_id,
                    banner_preview: newDeptBanner
                });
            }

            else if (type === 'update') {
                const idx = departmentBanners.findIndex(b => b.dept === existing_id);
                if (idx === -1) {
                    return res.status(404).json({ error: 'Department banner not found' });
                }

                const currentBanner = departmentBanners[idx];
                const originalFields = {};

                for (const key in metadata) {
                    originalFields[key] = currentBanner[key] ?? null;
                }

                if (req.file) {
                    const newImagePath = `/static${req.file.path.split('/static')[1]}`.replace(/\\/g, '/');
                    metadata.banner_image = newImagePath;
                }

                const updatedBanner = { ...metadata };

                const tempDoc = {
                    unique_id: uuidv4(),
                    action_target_id: existingDoc._id,
                    metadata: { department_banner: metadata },
                    original_data: {department_banner : originalFields},
                    type,
                    collection_name: 'landing_page_details',
                    category: 'department_banner',
                    admin_id,
                    title,
                    status: 'pending',
                    date: new Date().toISOString(),
                    reviewed_by: null,
                    reviewed_notes: null
                };

                await db.collection('temp').insertOne(tempDoc);

                return res.status(200).json({
                    message: 'Department banner update request submitted for approval',
                    request_id: tempDoc.unique_id,
                    banner_preview: updatedBanner
                });
            }

            else if (type === 'delete') {
                const bannerToDelete = departmentBanners.find(b => b.dept === existing_id);

                if (!bannerToDelete) {
                    return res.status(404).json({ error: 'Department banner not found' });
                }

                const tempDoc = {
                    unique_id: uuidv4(),
                    action_target_id: existingDoc._id,
                    metadata: {},
                    original_data: { department_banner : bannerToDelete},
                    type,
                    collection_name: 'landing_page_details',
                    category: 'department_banner',
                    admin_id,
                    title,
                    status: 'pending',
                    date: new Date().toISOString(),
                    reviewed_by: null,
                    reviewed_notes: null
                };

                await db.collection('temp').insertOne(tempDoc);

                return res.status(200).json({
                    message: 'Department banner delete request submitted for approval',
                    request_id: tempDoc.unique_id,
                    deleted_banner: bannerToDelete
                });
            }

            return res.status(400).json({ error: 'Invalid type. Must be "add", "update", or "delete"' });
        } catch (err) {
            console.error('Error updating department banner:', err);
            return res.status(500).json({ error: 'Internal server error' });
        }
    }
);

//Superior Admin Review for Department Banner
app.post('/api/review_department_banner_request', verifyAdminAccess('landing_page_access'), async (req, res) => {
    try {
        const payload = req.body.superior_payload;
        if (!Array.isArray(payload) || payload.length === 0) {
            return res.status(400).json({ error: 'Invalid or empty superior_payload' });
        }

        const tempCollection = db.collection('temp');
        const landingPageCollection = db.collection('landing_page_details');
        const adminArchiveCollection = db.collection('admin_archive');
        const username = req.session.username;

        const results = [];

        for (const review of payload) {
            const { unique_id, reviewed_notes, actions } = review;
            const requestDoc = await tempCollection.findOne({ unique_id });

            if (!requestDoc) {
                results.push({ unique_id, status: 'failed', reason: 'Request not found' });
                continue;
            }

            const { type, metadata, original_data, action_target_id } = requestDoc;
            let updateResult = null;
            let finalStatus = 'rejected';
            const approvedFields = {};
            const rejectedFields = [];

            if (type === 'add') {
                const section = 'department_banner';
                const sectionData = metadata[section];
                const sectionActions = actions[section];

                const approvedBanner = {};
                for (const field in sectionActions) {
                    if (sectionActions[field] === 'approve') {
                        if (field === 'banner_image') {
                        try {
                            const uploadResult = await uploadFileToS3FromPath(sectionData[field]);
                            approvedBanner[field] = uploadResult.s3Path;
                        } catch (err) {
                            rejectedFields.push(`${section}.${field}`);
                            continue;
                        }
                        } else {
                        approvedBanner[field] = sectionData[field];
                        }
                    } else {
                        rejectedFields.push(`${section}.${field}`);
                    }
                }

                if (Object.keys(approvedBanner).length > 0) {
                    await landingPageCollection.updateOne({}, {
                        $push: { department_banner: approvedBanner }
                    });
                    approvedFields[section] = approvedBanner;
                    finalStatus = rejectedFields.length === 0 ? 'approved' : 'partially_approved';
                }

            } else if (type === 'update') {
                const section = 'department_banner';
                const sectionData = metadata[section];
                const sectionActions = actions[section];
                const deptToUpdate = original_data[section]?.dept;

                if (!deptToUpdate) {
                    results.push({ unique_id, status: 'failed', reason: 'Original department not found' });
                    continue;
                }

                const doc = await landingPageCollection.findOne({});
                const banners = doc?.department_banner || [];
                const bannerIndex = banners.findIndex(b => b.dept === deptToUpdate);

                if (bannerIndex === -1) {
                    results.push({ unique_id, status: 'failed', reason: 'Matching department not found in live data' });
                    continue;
                }

                const updates = {};
                for (const field in sectionActions) {
                    if (sectionActions[field] === 'approve') {
                        if (field === 'banner_image') {
                        try {
                            const uploadResult = await uploadFileToS3FromPath(sectionData[field]);
                            updates[`department_banner.${bannerIndex}.${field}`] = uploadResult.s3Path;
                        } catch (err) {
                            rejectedFields.push(`${section}.${field}`);
                            continue;
                        }
                        } else {
                        updates[`department_banner.${bannerIndex}.${field}`] = sectionData[field];
                        }
                    } else {
                        rejectedFields.push(`${section}.${field}`);
                    }
                }

                if (Object.keys(updates).length > 0) {
                    await landingPageCollection.updateOne({}, { $set: updates });
                    approvedFields[section] = updates;
                    finalStatus = rejectedFields.length === 0 ? 'approved' : 'partially_approved';
                }

            } else if (type === 'delete') {
                const section = 'department_banner';
                const sectionActions = actions[section];
                if (sectionActions.delete_department === 'approve') {
                    const deptToDelete = original_data[section]?.dept;

                    if (!deptToDelete) {
                        results.push({ unique_id, status: 'failed', reason: 'Department info missing for delete' });
                        continue;
                    }

                    await landingPageCollection.updateOne({}, {
                        $pull: {
                            department_banner: { dept: deptToDelete }
                        }
                    });

                    approvedFields[section] = { delete_department: deptToDelete };
                    finalStatus = 'approved';
                } else {
                    rejectedFields.push('department_banner.delete_department');
                }
            } else {
                results.push({ unique_id, status: 'failed', reason: 'Unknown request type' });
                continue;
            }

            // Archive the decision
            const archiveDoc = {
                ...requestDoc,
                reviewed_by: username,
                reviewed_notes: reviewed_notes || '',
                status: 'managed',
                actions
            };

            await adminArchiveCollection.insertOne(archiveDoc);
            await tempCollection.deleteOne({ unique_id });

            results.push({
                unique_id,
                status: finalStatus,
                approved_fields: approvedFields,
                rejected_fields: rejectedFields
            });
        }

        return res.status(200).json({
            message: 'Review process completed',
            results
        });

    } catch (err) {
        console.error('Error reviewing department banner requests:', err);
        return res.status(500).json({ error: 'Internal server error' });
    }
});
