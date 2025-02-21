const express = require('express');
const { MongoClient } = require('mongodb');
const session = require('express-session');
require('dotenv').config();
const bcrypt = require('bcrypt');
const { v4: uuidv4 } = require('uuid');
const QRCode = require('qrcode');
const path = require('path');
const fs = require('fs');
const twilio = require('twilio');
const moment = require("moment");
require("moment-timezone");
const multer = require('multer');

const app = express();
const port = process.env.PORT || 6000;

const storagePath = 'D:/Velammal-Engineering-College-Backend/static/student_docs';
if (!fs.existsSync(storagePath)) {
    fs.mkdirSync(storagePath, { recursive: true });
}
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, storagePath);
    },
    filename: function (req, file, cb) {
        if (!req.session || !req.session.unique_number) {
            return cb(new Error("Session unique_number is missing"));
        }

        const uniqueNumber = req.session.unique_number;
        const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
        const extension = path.extname(file.originalname);
        const filename = `${date}-${uniqueNumber}${extension}`;

        cb(null, filename);
    }
});

const upload = multer({ storage: storage });
app.use(express.json());

app.use(
    session({
        secret: '12345678',
        resave: false,
        saveUninitialized: true,
        cookie: {
            secure: false,
            maxAge: 24 * 60 * 60 * 1000
        }
    })
);

const mongoUri = process.env.MONGO_URI;
const dbName = process.env.DB_NAME;
const client = new MongoClient(mongoUri);
const accountSid = process.env.ACCOUNTSID;
const authToken = process.env.AUTHTOKEN;
const twilioPhoneNumber = process.env.TWILIOPHONENUMBER;
const twilioClient = twilio(accountSid, authToken);

async function connectToDatabase() {
    try {
        await client.connect();
        console.log("✅ Connected to MongoDB");
    } catch (error) {
        console.error("❌ MongoDB connection error:", error);
    }
}
connectToDatabase();

//function to generate QR
async function generateQR(pass_id, registration_number) {
    try {
        const baseDir = 'D:/Velammal-Engineering-College-Backend/static/qrcodes'; // Dont forget to change this base dir
        if (!fs.existsSync(baseDir)) {
            fs.mkdirSync(baseDir, { recursive: true });
        }
        const filePath = path.join(baseDir, `${registration_number}.jpeg`);

        await QRCode.toFile(filePath, pass_id, {
            type: 'jpeg',
            width: 300,
            errorCorrectionLevel: 'H'
        });

        return filePath;
    } catch (error) {
        console.error('Error generating QR code:', error);
        throw error;
    }
}

// Function to send SMS
const sendParentApprovalSMS = async (parentPhoneNumber, name, place_to_visit, reason_for_visit, from, to, pass_id) => {
    const approvalUrl = `http://localhost:5000/api/parent_accept/${pass_id}`;
    const rejectionUrl = `http://localhost:5000/api/parent_not_accept/${pass_id}`;    
    const smsMessage = `
    📢 Pass Request Notification

    ${name}, a student of Velammal Engineering College,  
    has requested a pass to visit **${place_to_visit}**  
    for the reason: **${reason_for_visit}**.  

    📅 Duration: ${from} ➝ ${to}  

    Please review and take action:  
    ✅ Approve: ${approvalUrl}  
    ❌ Reject: ${rejectionUrl}  
    `;

    try {
        await twilioClient.messages.create({
            body: smsMessage,
            from: twilioPhoneNumber,
            to: parentPhoneNumber
        });
        console.log("✅ SMS sent successfully to parent");
    } catch (error) {
        console.error("❌ Error sending SMS:", error);
        throw new Error("Failed to send SMS");
    }
};

// Function to send "Reached" SMS to parent
const sendParentReachedSMS = async (parentPhoneNumber, name, reachedTime) => {  
    const smsMessage = `
    📢 Arrival Notification  

    Dear Parent,  

    Your ward **${name}** has safely returned to the hostel.  

    🏡 **Hostel Arrival Time:** ${reachedTime}  

    Thank you,  
    Velammal Engineering College  
    `;
    try {
        await twilioClient.messages.create({
            body: smsMessage,
            from: twilioPhoneNumber,
            to: parentPhoneNumber
        });
        console.log(`✅ SMS sent successfully to parent of ${name}`);
    } catch (error) {
        console.error("❌ Error sending SMS:", error);
        throw new Error("Failed to send SMS");
    }
};

// Login Route
app.post('/api/login', async (req, res) => {
    try {
        await client.connect();
        const db = client.db(dbName);
        const { registration_number, password, type } = req.body;
        if (!registration_number || !password || !type) {
            return res.status(400).json({ error: "All fields (registration_number, password, type) are required" });
        }
        let collectionName;
        if (type === "student") {
            collectionName = "student_database";
            query = { registration_number };
        } else if (type === "warden") {
            collectionName = "warden_database";
            query = { unique_id: registration_number , category : "assistant" };
        } else if (type === "superior") {
            collectionName = "warden_database";
            query = { unique_id: registration_number , category : "head" };
        } else {
            return res.status(400).json({ error: "Invalid user type" });
        }
        const collection = db.collection(collectionName);
        const user = await collection.findOne(query);
        if (!user) {
            return res.status(404).json({ error: 'User Not Found' });
        }
        const isMatch = await bcrypt.compare(password, user.password);
        if (!isMatch) {
            return res.status(401).json({ error: "Invalid credentials" });
        }
        req.session.studentauth = false;
        req.session.wardenauth = false;
        req.session.superiorauth = false;
        if (type === "student") {
            req.session.studentauth = true;
        } else if (type === "warden") {
            req.session.wardenauth = true;
        } else if (type === "superior") {
            req.session.superiorauth = true;
        }
        req.session.unique_number = registration_number;
        res.status(200).json({ 
            message: 'Sign-in successful', 
            user: {
                userid: user.userid,
                name: user.name,
                type
            },
            redirect:`/${type}`
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: "Internal Server Error" });
    }
});

//security login
app.post('/api/security_login', async (req, res) => {
    try {
        await client.connect();
        const db = client.db(dbName);
        const securityCollection = db.collection("security_database");
        const { registration_number, password } = req.body; 
        
        const security_details = await securityCollection.findOne({ unique_id: registration_number });

        if (!security_details) {
            return res.status(401).json({ error: "Invalid credentials" });
        }

        const isMatch = await bcrypt.compare(password, security_details.password);
        if (!isMatch) {
            return res.status(401).json({ error: "Invalid credentials" });
        }

        req.session.securityauth = true;
        req.session.unique_number = registration_number;

        res.status(200).json({ 
            message: 'Sign-in successful', 
            user: {
                userid: security_details.unique_id,
                name: security_details.name,
            } 
        });

    } catch (error) {
        console.error(error);
        res.status(500).json({ error: "Internal Server Error" });
    }
});

//Verify Student using mobile number
app.post('/api/verify_student', async (req, res) => {
    if (!req.session || req.session.studentauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }

    const db = client.db(dbName);
    const usersCollection = db.collection('student_database');
    const { phone_number_student } = req.body;
    const unique_id = req.session.unique_number;
    const user_valid = await usersCollection.findOne({registration_number : unique_id });
    if (!user_valid) {
        return res.status(401).json({ error: "Couldn't Find the User data" });
    }
    if (user_valid.phone_number_student !== phone_number_student) {
        return res.status(401).json({ error: "Enter Valid Mobile number" });
    }
    try {
        const user = await usersCollection.findOne({ phone_number_student: String(phone_number_student) });
        if (!user) {
            return res.status(404).json({ message: "No users Found for that Number" });
        }

        res.status(200).json({
            name: user.name,
            phone_number_student: user.phone_number_student,
            year: user.year,
            department: user.department,
            room_number: user.room_number,
            registration_number: user.registration_number,
            block_name: user.block_name
        });

    } catch (error) {
        console.error("❌ Error verifying mobile number:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

// Endpoint to submit pass with parent approval request
app.post('/api/submit_pass_parent_approval', upload.single('file'), async (req, res) => {
    if (!req.session || req.session.studentauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }

    try {
        await client.connect();
        const db = client.db(dbName);
        const PassCollection = db.collection('pass_details');
        const studentDatabase = db.collection('student_database');

        const {
            mobile_number, name, department_name, year, room_no, registration_number,
            block_name, pass_type, from, to, place_to_visit,
            reason_type, reason_for_visit
        } = req.body;

        if (!mobile_number) {
            return res.status(400).json({ error: "Mobile number is required" });
        }

        const student = await studentDatabase.findOne({ phone_number_student: mobile_number });

        if (!student) {
            return res.status(404).json({ error: "Student record not found" });
        }

        const parentPhoneNumber = student.phone_number_parent;

        const currentDate = new Date();

        if (new Date(from) < currentDate) {
            return res.status(400).json({ error: "From date cannot be in the past" });
        }

        if (new Date(to) < currentDate) {
            return res.status(400).json({ error: "To date cannot be in the past" });
        }

        if (new Date(to) < new Date(from)) {
            return res.status(400).json({ error: "To date cannot be earlier than From date" });
        }

        currentDate.setHours(0, 0, 0, 0);
        const nextDate = new Date(currentDate);
        nextDate.setDate(nextDate.getDate() + 1);

        const activePassCount = await PassCollection.countDocuments({
            mobile_number,
            request_completed: false,
            expiry_status: false,
            request_time: { $gte: currentDate, $lt: nextDate }
        });

        if (activePassCount >= 3) {
            return res.status(400).json({ error: "Maximum of 3 active passes allowed per student for today" });
        }

        let file_path = null;
        if (req.file) {
            file_path = `/Velammal-Engineering-College-Backend/static/student_docs/${req.file.filename}`;
        }
        const yearInt = parseInt(year, 10); 

        const pass_id = uuidv4();
        const PassData = {
            pass_id,
            name,
            mobile_number,
            dept: department_name,
            year: yearInt,
            room_no,
            registration_number,
            gender: student.gender,
            late_count: student.late_count,
            blockname: block_name,
            passtype: pass_type,
            from: new Date(from),
            to: new Date(to),
            place_to_visit,
            reason_type,
            reason_for_visit,
            file_path,
            qrcode_path: null,
            parent_approval: null,
            wardern_approval: null,
            superior_wardern_approval: null,
            parent_sms_sent_status: false,
            qrcode_status: false,
            exit_time: null,
            re_entry_time: null,
            delay_status: false,
            request_completed: false,
            request_time: new Date(),
            expiry_status: false,
            request_date_time: new Date(),
            authorised_Security_id: null,
            authorised_warden_id: null,
            notify_superior: false
        };

        await PassCollection.insertOne(PassData);
        await sendParentApprovalSMS(parentPhoneNumber, name, place_to_visit, reason_for_visit, from, to, pass_id);
        await PassCollection.updateOne(
            { pass_id },
            { $set: { parent_sms_sent_status: true } }
        );

        res.status(201).json({ message: "Visitor pass submitted and SMS sent to parent", file_path });

    } catch (error) {
        console.error("❌ Error:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

// Endpoint to submit pass with warden and superior approval request
app.post('/api/submit_pass_warden_approval', upload.single('file'), async (req, res) => {
    if (!req.session || req.session.studentauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }

    try {
        await client.connect();
        const db = client.db(dbName);
        const PassCollection = db.collection('pass_details');
        const studentDatabase = db.collection('student_database');

        const {
            mobile_number, name, department_name, year, room_no, registration_number,
            block_name, pass_type, from, to, place_to_visit,
            reason_type, reason_for_visit , notify_superior
        } = req.body;

        if (!mobile_number) {
            return res.status(400).json({ error: "Mobile number is required" });
        }

        const currentDate = new Date();
        currentDate.setHours(0, 0, 0, 0);
        const nextDate = new Date(currentDate);
        nextDate.setDate(nextDate.getDate() + 1);

        if (new Date(from) < currentDate) {
            return res.status(400).json({ error: "From date cannot be in the past" });
        }

        if (new Date(to) < currentDate) {
            return res.status(400).json({ error: "To date cannot be in the past" });
        }

        if (new Date(to) < new Date(from)) {
            return res.status(400).json({ error: "To date cannot be earlier than From date" });
        }

        const activePassCount = await PassCollection.countDocuments({
            mobile_number,
            request_completed: false,
            expiry_status: false,
            request_time: { $gte: currentDate, $lt: nextDate }
        });

        if (activePassCount >= 3) {
            return res.status(400).json({ error: "Maximum of 3 active passes allowed per student for today" });
        }
        const student = await studentDatabase.findOne({ phone_number_student: mobile_number });

        if (!student) {
            return res.status(404).json({ error: "Student record not found" });
        }

        let file_path = null;
        if (req.file) {
            file_path = `/Velammal-Engineering-College-Backend/static/student_docs/${req.file.filename}`;
        }
        const yearInt = parseInt(year, 10);

        const notifySuperiorStatus = notify_superior === true ? true : false;

        const pass_id = uuidv4();
        const PassData = {
            pass_id,
            name,
            mobile_number,
            dept: department_name,
            year: yearInt,
            room_no,
            registration_number,
            gender: student.gender,
            late_count: student.late_count,
            blockname: block_name,
            passtype: pass_type,
            from: new Date(from),
            to: new Date(to),
            place_to_visit,
            reason_type,
            reason_for_visit,
            file_path,
            qrcode_path: null,
            parent_approval: null,
            wardern_approval: null,
            superior_wardern_approval: null,
            parent_sms_sent_status: false,
            qrcode_status: false,
            exit_time: null,
            re_entry_time: null,
            delay_status: false,
            request_completed: false,
            request_time: new Date(),
            expiry_status: false,
            request_date_time: new Date(),
            authorised_Security_id: null,
            authorised_warden_id: null,
            notify_superior: notifySuperiorStatus
        };

        await PassCollection.insertOne(PassData);
        res.status(201).json({ message: "Visitor pass submitted and Notified Warden", file_path });

    } catch (error) {
        console.error("❌ Error:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

// Save draft endpoint
app.post('/api/save_draft', upload.single('file'), async (req, res) => {
    if (!req.session || req.session.studentauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }

    try {
        await client.connect();
        const db = client.db(dbName);
        const DraftsCollection = db.collection('drafts_details');
        const studentDatabase = db.collection('student_database');

        const {
            mobile_number, name, department_name, year, room_no, registration_number,
            block_name, pass_type, from, to, place_to_visit,
            reason_type, reason_for_visit
        } = req.body;

        if (!mobile_number) {
            return res.status(400).json({ error: "Mobile number is required" });
        }

        const student = await studentDatabase.findOne({ phone_number_student: mobile_number });

        if (!student) {
            return res.status(404).json({ error: "Student record not found" });
        }
        const currentDate = new Date();
        if (new Date(from) < currentDate) {
            return res.status(400).json({ error: "From date cannot be in the past" });
        }

        if (new Date(to) < currentDate) {
            return res.status(400).json({ error: "To date cannot be in the past" });
        }

        if (new Date(to) < new Date(from)) {
            return res.status(400).json({ error: "To date cannot be earlier than From date" });
        }

        let file_path = null;
        if (req.file) {
            file_path = `/Velammal-Engineering-College-Backend/static/student_docs/${req.file.filename}`;
        }

        const existingDraft = await DraftsCollection.findOne({ registration_number });
        const yearInt = parseInt(year, 10);

        const PassData = {
            pass_id: existingDraft ? existingDraft.pass_id : uuidv4(),
            name,
            mobile_number,
            dept: department_name,
            year: yearInt,
            room_no,
            registration_number,
            gender: student.gender,
            late_count: student.late_count,
            blockname: block_name,
            passtype: pass_type,
            from: new Date(from),
            to: new Date(to),
            place_to_visit,
            reason_type,
            reason_for_visit,
            file_path,
            qrcode_path: null,
            parent_approval: null,
            wardern_approval: null,
            superior_wardern_approval: null,
            parent_sms_sent_status: false,
            qrcode_status: false,
            exit_time: null,
            re_entry_time: null,
            delay_status: false,
            request_completed: false,
            request_time: new Date(),
            expiry_status: false,
            request_date_time: new Date(),
            authorised_Security_id: null,
            authorised_warden_id: null
        };

        if (existingDraft) {
            await DraftsCollection.updateOne(
                { registration_number },
                { $set: PassData }
            );
            return res.status(200).json({ message: "Draft updated successfully" });
        } else {
            await DraftsCollection.insertOne(PassData);
            return res.status(201).json({ message: "Visitor pass saved in the draft" });
        }

    } catch (error) {
        console.error("❌ Error:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

//Students Fetch drafts
app.post('/api/fetch_drafts', async (req, res) => {
    if (!req.session || req.session.studentauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }

    try {
        await client.connect();
        const db = client.db(dbName);
        const DraftsCollection = db.collection("drafts_details");

        const registration_number = req.session.unique_number;
        if (!registration_number) {
            return res.status(400).json({ error: "Registration number is required" });
        }

        const drafts_details = await DraftsCollection.find({ registration_number }).toArray();

        if (!drafts_details || drafts_details.length === 0) {
            return res.status(404).json({ message: "No drafts found for this registration number" });
        }

        res.status(200).json({ drafts: drafts_details });

    } catch (error) {
        console.error("❌ Error fetching drafts:", error);
        return res.status(500).json({ error: "Internal Server Error" });
    }
});

//parent Accept Endpoint
app.post('/api/parent_accept/:pass_id', async (req, res) => {
    try {
        await client.connect();
        const db = client.db(dbName);
        const passCollection = db.collection('pass_details');
        const { pass_id } = req.params;
        if (!pass_id) {
            return res.status(400).json({ error: "pass_id is required" });
        }
        const passData = await passCollection.findOne({ pass_id: pass_id });

        if (!passData) {
            return res.status(404).json({ error: "Pass not found" });
        }
        if (passData.parent_approval !== null) {
            return res.status(400).json({
                message: `You have already ${passData.parent_approval ? "approved" : "rejected"} this request. If you haven't approved this request, please contact the warden.`,
            });
        }
        await passCollection.updateOne(
            { pass_id: pass_id },
            { $set: { parent_approval: true } }
        );
        res.status(200).json({ message: "Parent approval updated successfully" });

    } catch (error) {
        console.error("❌ Error:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

//parent Decline Endpoint
app.post('/api/parent_not_accept/:pass_id', async (req, res) => {
    try {
        await client.connect();
        const db = client.db(dbName);
        const passCollection = db.collection('pass_details');
        const { pass_id } = req.params;
        if (!pass_id) {
            return res.status(400).json({ error: "pass_id is required" });
        }
        const passData = await passCollection.findOne({ pass_id: pass_id });

        if (!passData) {
            return res.status(404).json({ error: "Pass not found" });
        }
        if (passData.parent_approval !== null) {
            return res.status(400).json({
                message: `You have already ${passData.parent_approval ? "approved" : "rejected"} this request. If you haven't approved this request, please contact the warden.`,
            });
        }
        await passCollection.updateOne(
            { pass_id: pass_id },
            { $set: { parent_approval: false } }
        );
        res.status(200).json({ message: "Parent rejection updated successfully" });

    } catch (error) {
        console.error("❌ Error:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

//student request for food type change
app.post('/api/change_food_type', async (req, res) => {
    if (!req.session || req.session.studentauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }
    const registration_number = req.session.unique_number;
    const db = client.db(dbName);
    const studentsCollection = db.collection('student_database');
    const requestsCollection = db.collection('food_change_requests');
    const wardensCollection = db.collection('warden_database');

    try {
        const student = await studentsCollection.findOne({ registration_number });
        if (!student) {
            return res.status(404).json({ message: 'Student not found' });
        }

        const newFoodType = student.foodtype === 'Veg' ? 'Non-Veg' : 'Veg';

        let warden = await wardensCollection.findOne({ 
            primary_year: { $in: [student.year] }, 
            gender: student.gender,
            active: true 
        });
        
        if (!warden) {
            warden = await wardensCollection.findOne({ 
                secondary_year: { $in: [student.year] }, 
                gender: student.gender,
                active: true 
            });
        }        
        if (!warden) {
            return res.status(403).json({ message: 'No active warden found for this student year' });
        }

        await requestsCollection.insertOne({ 
            registration_number, 
            name : student.name,
            previous_foodtype: student.foodtype,
            requested_foodtype: newFoodType, 
            room_number: student.room_number,
            department: student.department,
            gender: student.gender,
            status: null,
            year: student.year, 
            assigned_warden: warden.warden_name
        });
        await studentsCollection.updateOne(
            { registration_number },
            { 
                $set: { edit_status: null },
                $push: {
                    changes: `food_type: ${newFoodType}`
                }
            }
        );        

        res.status(200).json({ message: 'Request submitted for approval', requested_foodtype: newFoodType });
    } catch (error) {
        console.error('❌ Error processing request:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Warden fetches pending food requests
app.get('/api/food_requests_changes', async (req, res) => {
    if (!req.session || req.session.wardenauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }
    try {
        const unique_id = req.session.unique_number;

        if (!unique_id) {
            return res.status(400).json({ error: "warden_unique_id is required" });
        }

        await client.connect();
        const db = client.db(dbName);
        const wardenCollection = db.collection('warden_database');
        const requestsCollection = db.collection('food_change_requests');

        const warden = await wardenCollection.findOne({ unique_id , active:true });

        if (!warden) {
            return res.status(404).json({ error: "Warden not found" });
        }

        const primary_years = warden.primary_year;
        const warder_handling_gender = warden.gender;
        const requests = await requestsCollection.find({ year: { $in: primary_years } , gender: warder_handling_gender }).toArray();

        res.status(200).json({ requests });
    } catch (error) {
        console.error('❌ Error fetching requests:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Warden approves or declines the request
app.post('/api/approve_food_change', async (req, res) => {
    if (!req.session || req.session.wardenauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }

    const { registration_number, name, action } = req.body;
    const db = client.db(dbName);
    const studentsCollection = db.collection('student_database');
    const requestsCollection = db.collection('food_change_requests');

    try {
        const request = await requestsCollection.findOne({ registration_number, name });
        if (!request) {
            return res.status(404).json({ message: 'Request not found' });
        }
        if (action === "approve") {
            await studentsCollection.updateOne(
                { registration_number, name },
                { $set: { foodtype: request.requested_foodtype } }
            );
        }
        await requestsCollection.deleteOne({ registration_number, name });
        const student = await studentsCollection.findOne({ registration_number });
        const changesArray = student?.changes || [];

        const hasOtherChanges = changesArray.some(change =>
            ["name:", "room_number:", "phone_number_student:", "phone_number_parent:"].some(key => change.includes(key))
        );
        let editStatus = hasOtherChanges ? null : action === "approve" ? true : false;

        await studentsCollection.updateOne(
            { registration_number },
            {
                $set: { edit_status: editStatus },
                $pull: { changes: { $regex: `^food_type: ` } }
            }
        );

        return res.status(200).json({
            message: action === "approve"
                ? 'Food type change approved'
                : 'Food type change request declined',
            newFoodType: action === "approve" ? request.requested_foodtype : undefined
        });

    } catch (error) {
        console.error('❌ Error processing request:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

//Requesting for profile update
app.post('/api/request_profile_update', async (req, res) => {
    if (!req.session || req.session.studentauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }
    try {
        const { room_number, phone_number_student, phone_number_parent , name } = req.body;

        await client.connect();
        const db = client.db(dbName);
        const studentCollection = db.collection('student_database');
        const tempRequestCollection = db.collection('profile_change_requests');
        const registration_number = req.session.unique_number;
        const profile = await studentCollection.findOne({ registration_number });
        if (!profile) {
            return res.status(404).json({ error: "Profile not found" });
        }
        const fromData = {
            name: profile.name,
            room_number: profile.room_number,
            phone_number_student: profile.phone_number_student,
            phone_number_parent: profile.phone_number_parent
        };
        const toData = {
            name: name || profile.name,
            room_number: room_number || profile.room_number,
            phone_number_student: phone_number_student || profile.phone_number_student,
            phone_number_parent: phone_number_parent || profile.phone_number_parent
        };
        const changes = [];
        for (const key in fromData) {
            if (fromData[key] !== toData[key]) {
                changes.push(`${key}: ${toData[key]}`);
            }
        }
        const updateRequest = {
            registration_number,
            name: toData.name,
            room_number: toData.room_number,
            year:profile.year,
            department: profile.department,
            phone_number_student: toData.phone_number_student,
            phone_number_parent: toData.phone_number_parent,
            from_data: fromData,
            to_data: toData,
            edit_status: null,
            created_at: new Date(),
            gender: profile.gender
        };
        await tempRequestCollection.insertOne(updateRequest);
        await studentCollection.updateOne(
            { registration_number },
            { 
                $set: { edit_status: null },
                $push: { changes: { $each: changes } }
            }
        );

        res.json({
            message: "Profile update requested. Waiting for approval from wardens.",
            request: updateRequest
        });

    } catch (err) {
        console.error("❌ Error:", err);
        res.status(500).json({ error: "Server error" });
    }
});

//Superior wardern fetch for profile change requests
app.get('/api/profile_request_changes', async (req, res) => {
    if (!req.session || req.session.superiorauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }
    try {
        const unique_id = req.session.unique_number;
        if (!unique_id) {
            return res.status(400).json({ error: "warden_unique_id is required" });
        }

        await client.connect();
        const db = client.db(dbName);
        const wardenCollection = db.collection('warden_database');
        const requestsCollection = db.collection('profile_change_requests');

        const warden = await wardenCollection.findOne({ unique_id , active:true });

        if (!warden) {
            return res.status(404).json({ error: "Warden not found" });
        }

        const primary_year = warden.profile_years;
        const requests = await requestsCollection.find({ year: { $in: primary_year } }).toArray();

        res.status(200).json({ requests });
    } catch (error) {
        console.error('❌ Error fetching requests:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Superior Warden Profile Update Handling
app.post('/api/handle_request', async (req, res) => {
    if (!req.session || req.session.superiorauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }
    const unique_id = req.session.unique_number;
    try {
        const { registration_number, action } = req.body;
        await client.connect();
        const db = client.db(dbName);
        const wardenCollection = db.collection('warden_database');
        const studentCollection = db.collection('student_database');
        const tempRequestCollection = db.collection('profile_change_requests');
        const warden = await wardenCollection.findOne({ unique_id });
        if (!warden) {
            return res.status(404).json({ error: "Warden not found" });
        }
        const updateRequest = await tempRequestCollection.findOne({ registration_number });
        if (!updateRequest) {
            return res.status(404).json({ error: "Request not found" });
        }

        const student = await studentCollection.findOne({ registration_number });
        if (!student) {
            return res.status(404).json({ error: "Student not found" });
        }
        const changesArray = student?.changes || [];
        const hasFoodTypeChange = changesArray.some(change => /^food_type: /.test(change));
        if (action === "approve") {
            await studentCollection.updateOne(
                { registration_number: updateRequest.registration_number },
                {
                    $set: {
                        name: updateRequest.name,
                        room_number: updateRequest.room_number,
                        phone_number_student: updateRequest.phone_number_student,
                        phone_number_parent: updateRequest.phone_number_parent,
                        edit_status: true
                    },
                    $pull: {
                        changes: {
                            $in: [
                                `name: ${updateRequest.name}`,
                                `room_number: ${updateRequest.room_number}`,
                                `phone_number_student: ${updateRequest.phone_number_student}`,
                                `phone_number_parent: ${updateRequest.phone_number_parent}`
                            ]
                        }
                    }
                }
            );
            await tempRequestCollection.updateOne(
                { registration_number },
                { $set: { edit_status: true } }
            );
            if (hasFoodTypeChange) {
                await studentCollection.updateOne(
                    { registration_number },
                    { $set: { edit_status: null } }
                );
            }
            res.json({
                message: "Request approved and profile updated",
                approved_by: warden.name
            });
        } else if (action === "reject") {
            await tempRequestCollection.updateOne(
                { registration_number },
                { $set: { edit_status: false } }
            );
            await studentCollection.updateOne(
                { registration_number: updateRequest.registration_number },
                {
                    $set: { edit_status: false },
                    $pull: {
                        changes: {
                            $in: [
                                `name: ${updateRequest.name}`,
                                `room_number: ${updateRequest.room_number}`,
                                `phone_number_student: ${updateRequest.phone_number_student}`,
                                `phone_number_parent: ${updateRequest.phone_number_parent}`
                            ]
                        }
                    }
                }
            );
            if (hasFoodTypeChange) {
                await studentCollection.updateOne(
                    { registration_number },
                    { $set: { edit_status: null } }
                );
            }
            res.json({
                message: "Request rejected",
                rejected_by: warden.name
            });
        } else {
            return res.status(400).json({ error: "Invalid action" });
        }
        await tempRequestCollection.deleteOne({ registration_number });

    } catch (err) {
        console.error("❌ Error:", err);
        res.status(500).json({ error: "Server error" });
    }
});

//wardern endpoint to fetch the student details
app.get('/api/get_student_details', async (req, res) => {
    if (!req.session || req.session.wardenauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }
    try {
        const warden_unique_id = req.session.unique_number;
        await client.connect();
        const db = client.db(dbName);
        const wardenCollection = db.collection("warden_database");
        const studentCollection = db.collection("student_database");
        const warden = await wardenCollection.findOne({ unique_id : warden_unique_id });
        const year = warden.primary_year;
        if (!warden) {
            return res.status(404).json({ error: "Warden not found" });
        }
        
        const student_data = await studentCollection.find({ year: { $in: year } , gender: warden.gender }).toArray();
       
        if (student_data.length === 0) {
            return res.status(404).json({ message: "No data found" });
        }
        
        res.json({ students: student_data });
    } catch (err) {
        console.error("❌ Error:", err);
        res.status(500).json({ error: "Server error" });
}
});

//fetch all the pending passes for the warden
app.get('/api/fetch_pending_passes_warden', async (req, res) => {
    if (!req.session || req.session.wardenauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }
    try {
        const warden_id = req.session.unique_number;
        await client.connect();
        const db = client.db(dbName);
        const passCollection = db.collection("pass_details");
        const wardenCollection = db.collection("warden_database");

        const warden_data = await wardenCollection.findOne({ unique_id : warden_id });
        const warden_primary_year = warden_data.primary_year;
        
        const pendingPasses = await passCollection.find({ 
            request_completed: false,
            expiry_status: false,
            gender : warden_data.gender,
            qrcode_status: false,
            wardern_approval: null,
            superior_wardern_approval: null,
            notify_superior: false,
            year: { $in: warden_primary_year } 
        }).toArray();

        if (pendingPasses.length === 0) {
            return res.status(404).json({ message: "No pending passes found" });
        }
        
        res.json({ pendingPasses });
    } catch (err) {
        console.error("❌ Error:", err);
        res.status(500).json({ error: "Server error" });
    }
});

// Warden Accept Endpoint
app.post('/api/warden_accept', async (req, res) => {
    if (!req.session || req.session.wardenauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }
    try {
        const warden_unique_id = req.session.unique_number;
        const { pass_id, medical_status } = req.body;
        if (!pass_id) {
            return res.status(400).json({ error: "pass_id is required" });
        }
        await client.connect();
        const db = client.db(dbName);
        const passCollection = db.collection('pass_details');
        const wardenCollection = db.collection('warden_database');

        const warden_data = await wardenCollection.findOne({ unique_id: warden_unique_id });
        if (!warden_data) {
            return res.status(404).json({ error: "Warden not found" });
        }
        const passData = await passCollection.findOne({ pass_id: pass_id });
        if (!passData) {
            return res.status(404).json({ error: "Pass not found" });
        }
        if (passData.wardern_approval !== null) {
            return res.status(400).json({
                message: `The following warden ${passData.authorised_warden_id} has already ${passData.wardern_approval ? "approved" : "rejected"} this request. If you haven't approved this request, please contact the warden.`,
            });
        }
        if (!warden_data.primary_year.includes(passData.year)) {
            return res.status(400).json({ error: "Warden is accessing the wrong year" });
        }

        const student_registration_number = passData.registration_number;
        const qrPath = await generateQR(pass_id, student_registration_number);

        const updateData = {
            wardern_approval: true,
            qrcode_path: qrPath,
            qrcode_status: true,
            authorised_warden_id: warden_unique_id,
        };
        if (medical_status === true) {
            updateData.reason_type = "medical";
        }

        await passCollection.updateOne({ pass_id: pass_id }, { $set: updateData });

        res.status(200).json({ message: "Warden approval updated successfully", qrcode_path: qrPath });

    } catch (error) {
        console.error("❌ Error:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

//Warden Decline Endpoint
app.post('/api/warden_not_accept', async (req, res) => {
    if (!req.session || req.session.wardenauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }
    try {
        const warden_unique_id = req.session.unique_number;
        const { pass_id } = req.body;
        if (!pass_id) {
            return res.status(400).json({ error: "pass_id is required" });
        }
        await client.connect();
        const db = client.db(dbName);
        const passCollection = db.collection('pass_details');
        const wardenCollection = db.collection('warden_database');

        const warden_data = await wardenCollection.findOne({ unique_id: warden_unique_id });
        if (!warden_data) {
            return res.status(404).json({ error: "Warden not found" });
        }
        const passData = await passCollection.findOne({ pass_id: pass_id });
        if (!passData) {
            return res.status(404).json({ error: "Pass not found" });
        }

        if (!warden_data.primary_year.includes(passData.year)) {
            return res.status(400).json({ error: "Warden is accessing the wrong year" });
        }        

        if (passData.wardern_approval !== null) {
            return res.status(400).json({
                message: `The Following wardern ${passData.authorised_warden_id} have already ${passData.wardern_approval ? "approved" : "rejected"} this request. If you haven't approved this request, please contact the warden.`,
            });
        }

        await passCollection.updateOne(
            { pass_id: pass_id },
            { $set: { wardern_approval: false , authorised_warden_id : warden_unique_id} }
        );

        res.status(200).json({ message: "Warden rejection updated successfully" });

    } catch (error) {
        console.error("❌ Error:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

// Superior Warden Accept Endpoint
app.post('/api/superior_accept', async (req, res) => {
    if (!req.session || req.session.superiorauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }
    try {
        const superior_unique_id = req.session.unique_number;
        const { pass_id, medical_status } = req.body;

        if (!pass_id) {
            return res.status(400).json({ error: "pass_id is required" });
        }
        await client.connect();
        const db = client.db(dbName);
        const passCollection = db.collection('pass_details');
        const wardenCollection = db.collection('warden_database');

        const superior_data = await wardenCollection.findOne({ unique_id: superior_unique_id });
        if (!superior_data) {
            return res.status(404).json({ error: "Superior Warden not found" });
        }
        const passData = await passCollection.findOne({ pass_id: pass_id });
        if (!passData) {
            return res.status(404).json({ error: "Pass not found" });
        }
        if (passData.superior_wardern_approval !== null) {
            return res.status(400).json({
                message: `You have already ${passData.superior_wardern_approval ? "approved" : "rejected"} this request. If you haven't approved this request, please contact the warden.`,
            });
        }
        const student_registration_number = passData.registration_number;
        const qrPath = await generateQR(pass_id, student_registration_number);

        const updateData = {
            superior_wardern_approval: true,
            qrcode_path: qrPath,
            qrcode_status: true,
            authorised_warden_id: superior_unique_id,
        };

        if (medical_status === true) {
            updateData.reason_type = "medical";
        }

        await passCollection.updateOne({ pass_id: pass_id }, { $set: updateData });

        res.status(200).json({ message: "Superior Warden approval updated successfully", qrcode_path: qrPath });

    } catch (error) {
        console.error("❌ Error:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

//Superior Warden Decline Endpoint
app.post('/api/superior_decline', async (req, res) => {
    if (!req.session || req.session.superiorauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }
    try {
        const superior_unique_id = req.session.unique_number;
        const { pass_id } = req.body;

        if (!pass_id) {
            return res.status(400).json({ error: "pass_id is required" });
        }
        await client.connect();
        const db = client.db(dbName);
        const passCollection = db.collection('pass_details');
        const wardenCollection = db.collection('warden_database');

        const superior_data = await wardenCollection.findOne({ unique_id: superior_unique_id });
        if (!superior_data) {
            return res.status(404).json({ error: "Superior Warden not found" });
        }
        const passData = await passCollection.findOne({ pass_id: pass_id });
        if (!passData) {
            return res.status(404).json({ error: "Pass not found" });
        }
        if (passData.superior_wardern_approval !== null) {
            return res.status(400).json({
                message: `You have already ${passData.superior_wardern_approval ? "approved" : "rejected"} this request. If you haven't approved this request, please contact the warden.`,
            });
        }
        
        await passCollection.updateOne(
            { pass_id: pass_id },
            { $set: { superior_wardern_approval: false , qrcode_path: null, qrcode_status: false , authorised_warden_id : superior_unique_id } }
        );

        res.status(200).json({ message: "Warden rejection updated successfully" });

    } catch (error) {
        console.error("❌ Error:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

//food type count
app.get('/api/food_count', async (req, res) => { 
    if (!req.session || (!req.session.wardenauth && !req.session.superiorauth)) {
        return res.status(401).json({ error: "Unauthorized access" });
    }

    try {
        await client.connect();
        const db = client.db(dbName);
        const unique_id = req.session.unique_number;
        const wardenCollection = db.collection("warden_database");
        const studentCollection = db.collection("student_database");

        const warden_data = await wardenCollection.findOne({ unique_id });
        const target_years = warden_data.primary_year;

        let foodCounts = {};

        for (const year of target_years) {
            const vegCount = await studentCollection.countDocuments({ foodtype: "Veg", year , gender:warden_data.gender });
            const nonVegCount = await studentCollection.countDocuments({ foodtype: "Non-Veg", year , gender:warden_data.gender });

            foodCounts[year] = { veg_count: vegCount, non_veg_count: nonVegCount };
        }

        res.json(foodCounts);
    } catch (err) {
        console.error("❌ Error:", err);
        res.status(500).json({ error: "Server error" });
    }
});

//warden sidebar
app.get('/api/sidebar_warden', async (req, res) => { 
    if (!req.session || (!req.session.wardenauth && !req.session.superiorauth)) {
        return res.status(401).json({ error: "Unauthorized access" });
    }

    try {
        await client.connect();
        const db = client.db(dbName);
        const wardenCollection = db.collection("warden_database");
        const warden_id = req.session.unique_number;
        const warden_data = await wardenCollection.findOne({ unique_id : warden_id });
        res.json({
            "name" : warden_data.warden_name,
            "primary year" : warden_data.primary_year,
            "Secondary year": warden_data.secondary_year,
            "Phone number": warden_data.phone_number,
            "image_path" : warden_data.image_path,
            "Active Status": warden_data.active
        })
    } catch (err) {
        console.error("❌ Error:", err);
        res.status(500).json({ error: "Server error" });
    }
});

// Fetch student passes in stored date order (recent first) for the student
app.get('/api/get_student_pass', async (req, res) => { 
    if (!req.session || req.session.studentauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }
    try {
        const student_unique_id = req.session.unique_number;
        await client.connect();
        const db = client.db(dbName);
        const passCollection = db.collection("pass_details");

        const passes = await passCollection
            .find({ registration_number: student_unique_id })
            .sort({ request_date_time: -1 })
            .toArray();

        if (passes.length === 0) {
            return res.status(404).json({ message: "No passes found" });
        }

        res.json({ passes });
    } catch (err) {
        console.error("❌ Error:", err);
        res.status(500).json({ error: "Server error" });
    }
});

// Fetch warden data for superior
app.get('/api/fetch_warden_details', async (req, res) => {
    if (!req.session || req.session.superiorauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }

    try {
        await client.connect();
        const db = client.db(dbName);
        const wardenCollection = db.collection("warden_database");

        const warden_details = await wardenCollection.find({ category: "assistant" }).toArray();

        if (!warden_details || warden_details.length === 0) {
            return res.status(404).json({ message: "No assistant wardens found" });
        }

        res.status(200).json({ wardens: warden_details });

    } catch (error) {
        console.error("❌ Error fetching warden details:", error);
        return res.status(500).json({ error: "Internal Server Error" });
    }
});

// Fetch warden details for reallocation
app.post('/api/fetch_warden_details_reallocation', async (req, res) => {
    if (!req.session || req.session.superiorauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }
    try {
        await client.connect();
        const db = client.db(dbName);
        const wardenCollection = db.collection("warden_database");
        const { target_warden_id } = req.body;
        if (!target_warden_id) {
            return res.status(400).json({ error: "Missing target_warden_id" });
        }
        const target_warden_data = await wardenCollection.findOne({ unique_id: target_warden_id });

        if (!target_warden_data) {
            return res.status(404).json({ error: "Target warden not found" });
        }
        const primary_years = target_warden_data.primary_year;
        const target_warden_gender = target_warden_data.gender;
        const warden_details = await wardenCollection.find({
            active: true,
            gender: target_warden_gender,
            category: "assistant",
            unique_id: { $ne: target_warden_id }
        }).toArray();

        const superior_warden_data = await wardenCollection.findOne({ category: "head" });

        if (!superior_warden_data) {
            return res.status(404).json({ error: "Superior warden not found" });
        }
        const superior_warden_name = superior_warden_data.warden_name;

        const warden_names = warden_details.map(warden => warden.warden_name);
        warden_names.push(superior_warden_name);

        res.status(200).json({ warden_names, primary_years });

    } catch (error) {
        console.error("Error fetching warden details:", error);
        return res.status(500).json({ error: "Internal Server Error" });
    }
});

// Warden Inactive status handling
app.post('/api/warden_inactive_status_handling', async (req, res) => {
    if (!req.session || req.session.superiorauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }
    try {
        await client.connect();
        const db = client.db(dbName);
        const wardenCollection = db.collection("warden_database");
        const { warden_name, inactive_warden_id, year } = req.body;
        if (!warden_name || !inactive_warden_id || !year) {
            return res.status(400).json({ error: "Missing warden_name, inactive_warden_id, or year" });
        }
        const warden_details = await wardenCollection.findOne({ warden_name });
        if (!warden_details) {
            return res.status(404).json({ message: "Warden not found" });
        }
        const updateResult = await wardenCollection.updateOne(
            { unique_id: inactive_warden_id },
            { $set: { active: false } }
        );

        if (updateResult.matchedCount === 0) {
            return res.status(404).json({ message: "Inactive warden not found" });
        }
        await wardenCollection.updateOne(
            { warden_name },
            { $addToSet: { primary_year: year } }
        );
        res.json({ message: "Warden status updated and year added successfully" });
    } catch (error) {
        console.error("❌ Error handling warden status:", error);
        return res.status(500).json({ error: "Internal Server Error" });
    }
});

// Warden Active Status Handling
app.post('/api/warden_active_status_handling', async (req, res) => {
    if (!req.session || req.session.superiorauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }

    try {
        await client.connect();
        const db = client.db(dbName);
        const wardenCollection = db.collection("warden_database");
        const { warden_id } = req.body;
        if (!warden_id) {
            return res.status(400).json({ error: "Missing warden_id" });
        }
        const warden_details = await wardenCollection.findOne({ unique_id: warden_id });

        if (!warden_details) {
            return res.status(404).json({ message: "Warden not found" });
        }
        const primary_years = warden_details.primary_year || [];
        await wardenCollection.updateMany(
            { unique_id: { $ne: warden_id } },
            { $pull: { primary_year: { $in: primary_years } } }
        );
        const updateResult = await wardenCollection.updateOne(
            { unique_id: warden_id },
            { $set: { active: true } }
        );

        if (updateResult.matchedCount === 0) {
            return res.status(404).json({ message: "Warden not found or not updated" });
        }
        res.json({ message: "Warden activated and primary years updated successfully" });
    } catch (error) {
        console.error("❌ Error handling warden status:", error);
        return res.status(500).json({ error: "Internal Server Error" });
    }
});

// Update Student Details Endpoint
app.post('/api/update_student_by_warden', async (req, res) => {
    if (!req.session || req.session.superiorauth !== true) { 
        return res.status(401).json({ error: "Unauthorized access" });
    }

    try {
        await client.connect();
        const db = client.db(dbName);
        const studentCollection = db.collection("student_database");

        const { registration_number, ...updateFields } = req.body;

        if (!registration_number) {
            return res.status(400).json({ error: "Registration number is required" });
        }
        const restrictedFields = ["registration_number", "password", "_id"];
        restrictedFields.forEach(field => delete updateFields[field]);

        const updateResult = await studentCollection.updateOne(
            { registration_number: registration_number },
            { $set: updateFields }
        );

        if (updateResult.matchedCount === 0) {
            return res.status(404).json({ error: "Student not found" });
        }

        res.status(200).json({
            message: "Student details updated successfully",
            registration_number: registration_number,
            updated_fields: updateFields
        });

    } catch (error) {
        console.error("❌ Error updating student details:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

// Update Warden Details Endpoint (Only by Superior Warden)
app.post('/api/update_warden_by_superior', upload.single('file'), async (req, res) => {
    if (!req.session || req.session.superiorauth !== true) { 
        return res.status(401).json({ error: "Unauthorized access" });
    }
    try {
        await client.connect();
        const db = client.db(dbName);
        const wardenCollection = db.collection("warden_database");

        let file_path = null;
        if (req.file) {
            file_path = `/Velammal-Engineering-College-Backend/static/warden_docs/${req.file.filename}`;
        }

        const { unique_id, ...updateFields } = req.body;
        if (!unique_id) {
            return res.status(400).json({ error: "Warden unique ID is required" });
        }

        if (file_path) {
            updateFields.file_path = file_path;
        }

        const updateResult = await wardenCollection.updateOne(
            { unique_id: unique_id },
            { $set: updateFields }
        );

        if (updateResult.matchedCount === 0) {
            return res.status(404).json({ error: "Warden not found" });
        }

        res.status(200).json({
            message: "Warden details updated successfully",
            unique_id: unique_id,
            updated_fields: updateFields
        });

    } catch (error) {
        console.error("❌ Error updating warden details:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

//student profile fetch his own profile
app.get('/api/fetch_student_profile', async (req, res) => {
    if (!req.session || req.session.studentauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }
    try {
      await client.connect();
      const db = client.db(dbName);
      const profilesCollection = db.collection("student_database");
      const unique_id = req.session.unique_number;
      const profile = await profilesCollection.findOne({ registration_number: unique_id });
  
      if (!profile) {
        return res.status(404).json({ message: 'Profile not found' });
      }
      return res.status(200).json(profile);
    } catch (error) {
      console.error('❌ Error fetching profile:', error);
      return res.status(500).json({ message: 'Server error' });
    }
  });

//fetch pass details for security
app.post('/api/fetch_pass_details', async (req, res) => {
    if (!req.session || req.session.securityauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }

    try {
        await client.connect();
        const db = client.db(dbName);
        const passCollection = db.collection("pass_details");

        const { pass_unique_id } = req.body;
        if (!pass_unique_id) {
            return res.status(400).json({ message: "Pass ID is required" });
        }

        const pass_data = await passCollection.findOne({ 
            pass_id: pass_unique_id,
            $or: [
                { wardern_approval: true },
                { superior_wardern_approval: true }
            ]
        });
        
        if (!pass_data) {
            return res.status(404).json({ message: "No pass details found for the given ID" });
        }
        return res.status(200).json(pass_data);
    } catch (error) {
        console.error('❌ Error fetching pass details:', error);
        return res.status(500).json({ message: "Server error" });
    }
});

// Security accept endpoint
app.post('/api/security_accept', async (req, res) => {
    if (!req.session || req.session.securityauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }
    try {
        await client.connect();
        const db = client.db(dbName);
        const passCollection = db.collection("pass_details");
        const studentCollection = db.collection("student_database");

        const { pass_id } = req.body;
        if (!pass_id) {
            return res.status(400).json({ error: "Pass ID is required" });
        }
        const pass_details = await passCollection.findOne({ pass_id: pass_id });
        if (!pass_details) {
            return res.status(404).json({ error: "Pass not found" });
        }

        const security_id = req.session.unique_number;
        const student_data = await studentCollection.findOne({ registration_number : pass_details.registration_number});
        if (!pass_details.exit_time) {
            const exitTime = new Date();
            await passCollection.updateOne(
                { pass_id: pass_id },
                { 
                    $set: { 
                        exit_time: exitTime,
                        authorised_Security_id: security_id 
                    }
                }
            );

            return res.status(200).json({
                message: "Exit time updated successfully",
                pass_id: pass_id,
                exit_time: exitTime,
                authorised_Security_id: security_id
            });
        }
        if (pass_details.exit_time && !pass_details.re_entry_time) {
            const reEntryTime = new Date();
            const returnDeadline = new Date(pass_details.to);
            const delayStatus = reEntryTime > returnDeadline;

            let updateFields = {
                re_entry_time: reEntryTime,
                request_completed: true,
                expiry_status: true,
                delay_status: delayStatus
            };
            if (delayStatus) {
                await studentCollection.updateOne(
                    { phone_number_student: pass_details.mobile_number },
                    { $inc: { late_count: 1 } }
                );
            }

            await passCollection.updateOne(
                { pass_id: pass_id },
                { $set: updateFields }
            );
            await sendParentReachedSMS(
                student_data.phone_number_parent, 
                pass_details.name, 
                reEntryTime.toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })
            );

            return res.status(200).json({
                message: "Re-entry time updated successfully",
                pass_id: pass_id,
                re_entry_time: reEntryTime,
                authorised_Security_id: security_id,
                delay_status: delayStatus
            });
        }

    } catch (error) {
        console.error("❌ Error updating security pass:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

// Security Decline Endpoint
app.post('/api/security_decline', async (req, res) => {
    if (!req.session || req.session.securityauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }
    try {
        await client.connect();
        const db = client.db(dbName);
        const passCollection = db.collection("pass_details");

        const { pass_id } = req.body;
        if (!pass_id) {
            return res.status(400).json({ error: "Pass ID is required" });
        }

        const pass_details = await passCollection.findOne({ pass_id: pass_id });
        if (!pass_details) {
            return res.status(404).json({ error: "Pass not found" });
        }

        const security_id = req.session.unique_number;
        let updateFields = { 
            authorised_Security_id: security_id,
            request_completed: true
        };
        if (pass_details.exit_time && !pass_details.re_entry_time) {
            updateFields.re_entry_time = null;
            updateFields.expiry_status = true;
        } else {
            updateFields.exit_time = null;
        }
        const updateResult = await passCollection.updateOne(
            { pass_id: pass_id },
            { $set: updateFields }
        );

        if (updateResult.matchedCount === 0) {
            return res.status(404).json({ error: "Pass not found" });
        }

        res.status(200).json({
            message: "Pass request declined successfully",
            pass_id: pass_id,
            authorised_Security_id: security_id
        });

    } catch (error) {
        console.error("❌ Error declining pass request:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

//warden change food type directly
app.post('/api/warden_change_foodtype', async (req, res) => {
    if (!req.session || req.session.wardenauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }
    const { registration_number } = req.body;

    if (!registration_number) {
        return res.status(400).json({ error: "Registration number is required" });
    }

    try {
        await client.connect();
        const db = client.db(dbName);
        const studentCollection = db.collection("student_database"); 

        const student = await studentCollection.findOne({ registration_number });

        if (!student) {
            return res.status(404).json({ error: "Student not found" });
        }
        const newFoodType = student.foodtype === "Veg" ? "Non-Veg" : "Veg";
        await studentCollection.updateOne(
            { registration_number },
            { $set: { foodtype: newFoodType } }
        );

        res.json({ message: `Food type updated to ${newFoodType}`, foodtype: newFoodType });
    } catch (err) {
        console.error("❌ Error:", err);
        res.status(500).json({ error: "Server error" });
    }
});

// Fetch waiting members name list
app.post("/api/fetch_waiting_members", async (req, res) => {
    if (!req.session || req.session.wardenauth !== true) {
        return res.status(401).json({ error: "Unauthorized Access" });
    }

    try {
        await client.connect();
        const db = client.db(dbName);
        const passCollection = db.collection("pass_details");
        const unique_id = req.session.unique_number;
        const wardenCollection = db.collection("warden_database");
        const warden_data = await wardenCollection.findOne({ unique_id });

        if (!warden_data || !warden_data.primary_year || !Array.isArray(warden_data.primary_year)) {
            return res.status(400).json({ error: "Invalid warden data." });
        }

        const warden_handling_gender = warden_data.gender;
        const { target_year } = req.body;

        let query = {
            re_entry_time: null,
            request_completed: false,
            qrcode_status: true,
            gender: warden_handling_gender,
            exit_time: { $ne: null }
        };

        if (target_year === "overall") {
            query.year = { $in: warden_data.primary_year };
        } else {
            query.year = target_year;
        }

        const waiting_data = await passCollection.find(query).toArray();
        const names = waiting_data.map(member => member.name);

        console.log(names);

        res.status(200).json({ waiting_members: names });
    } catch (error) {
        console.error("Error fetching data:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
});

// Fetch late members name list
app.post("/api/fetch_late_members", async (req, res) => {
    if (!req.session || req.session.wardenauth !== true) {
        return res.status(401).json({ error: "Unauthorized Access" });
    }

    try {
        await client.connect();
        const db = client.db(dbName);
        const unique_id = req.session.unique_number;
        const wardenCollection = db.collection("warden_database");
        const warden_data = await wardenCollection.findOne({ unique_id });

        if (!warden_data || !warden_data.primary_year || !Array.isArray(warden_data.primary_year)) {
            return res.status(400).json({ error: "Invalid warden data." });
        }

        const warden_handling_gender = warden_data.gender;
        const passCollection = db.collection("pass_details");
        const { target_year } = req.body;

        const currentTime = new Date();
        const istTime = new Date(currentTime.getTime() + (5.5 * 60 * 60 * 1000));

        let query = {
            re_entry_time: null,
            request_completed: false,
            qrcode_status:true,
            gender: warden_handling_gender,
            exit_time: { $ne: null }
        };
        if (target_year === "overall") {
            query.year = { $in: warden_data.primary_year };
        } else {
            query.year = target_year;
        }

        const late_members = await passCollection.find(query).toArray();

        const lateList = late_members
            .map(member => {
                if (!member.to) return null;

                const toTime = new Date(member.to);
                if (isNaN(toTime)) return null;

                if (toTime < istTime) {
                    const diffMs = istTime - toTime;
                    const diffMinutes = Math.floor(diffMs / 60000);
                    const hours = Math.floor(diffMinutes / 60);
                    const minutes = diffMinutes % 60;

                    return {
                        name: member.name,
                        late_by: `${hours} hours ${minutes} minutes`
                    };
                }
                return null;
            })
            .filter(member => member !== null);

        res.status(200).json({ late_members: lateList });
    } catch (error) {
        console.error("Error fetching data:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
});

// Analytics - Pass Measures
app.get("/api/pass_measures", async (req, res) => {
    if (!req.session || req.session.wardenauth !== true) {
        return res.status(401).json({ error: "Unauthorized Access" });
    }

    try {
        await client.connect();
        const db = client.db(dbName);
        const collection = db.collection("pass_details");
        const warden_id = req.session.unique_number;
        const wardenCollection = db.collection("warden_database");
        const warden_data = await wardenCollection.findOne({ unique_id: warden_id });

        if (!warden_data || !warden_data.primary_year) {
            return res.status(400).json({ error: "Invalid warden data." });
        }

        const warden_handling_gender = warden_data.gender;
        const primary_years = warden_data.primary_year;
        if (!Array.isArray(primary_years) || primary_years.length === 0) {
            return res.status(400).json({ error: "Primary years must be an array with at least one value." });
        }

        const currentDate = moment().utc().startOf("day").toDate();
        const nextDate = moment().utc().endOf("day").toDate();
        const now = moment().tz("Asia/Kolkata").toDate();

        const passTypes = ["od", "outpass", "staypass", "leave"];
        
        let results = {};
        let overall = {
            exitTimeCount: 0,
            reEntryTimeCount: 0,
            activeOutsideCount: 0,
            overdueReturnCount: 0,
            passTypeCounts: {}
        };

        for (const type of passTypes) {
            overall.passTypeCounts[type] = 0;
        }

        for (const year of primary_years) {
            const yearFilter = { year, gender: warden_handling_gender , qrcode_status:true };

            const exitTimeCount = await collection.countDocuments({
                exit_time: { $gte: currentDate, $lt: nextDate },
                ...yearFilter
            });

            const reEntryTimeCount = await collection.countDocuments({
                re_entry_time: { $gte: currentDate, $lte: nextDate },
                ...yearFilter
            });
            const activeOutsideCount = await collection.countDocuments({
                exit_time: { $exists: true },
                to: { $gt: now },
                ...yearFilter
            });

            const overdueReturnCount = await collection.countDocuments({
                exit_time: { $exists: true },
                to: { $lt: now },
                ...yearFilter
            });

            let passTypeCounts = {};
            for (const type of passTypes) {
                passTypeCounts[type] = await collection.countDocuments({
                    passtype: type,
                    ...yearFilter
                });
                overall.passTypeCounts[type] += passTypeCounts[type];
            }
            results[year] = {
                exitTimeCount,
                reEntryTimeCount,
                activeOutsideCount,
                overdueReturnCount,
                passTypeCounts
            };
            overall.exitTimeCount += exitTimeCount;
            overall.reEntryTimeCount += reEntryTimeCount;
            overall.activeOutsideCount += activeOutsideCount;
            overall.overdueReturnCount += overdueReturnCount;
        }
        results["overall"] = overall;

        res.json({
            primary_years,
            data: results
        });

    } catch (error) {
        console.error("Error fetching data:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
});

//pass analysis 2
app.get("/api/pass_analysis", async (req, res) => {
    if (!req.session || req.session.wardenauth !== true) {
        return res.status(401).json({ error: "Unauthorized Access" });
    }
    try {
        await client.connect();
        const db = client.db(dbName);
        const collection = db.collection("pass_details");

        const { type, year } = req.body;
        if (!type || !year) {
            return res.status(400).json({ error: "Missing 'type' or 'year' parameter in request" });
        }

        const warden_id = req.session.unique_number;
        const wardenCollection = db.collection("warden_database");
        const warden_data = await wardenCollection.findOne({ unique_id: warden_id });

        if (!warden_data || !warden_data.primary_year) {
            return res.status(400).json({ error: "Invalid warden data." });
        }

        const warden_handling_gender = warden_data.gender;
        const primary_years = warden_data.primary_year;
        if (!Array.isArray(primary_years) || primary_years.length === 0) {
            return res.status(400).json({ error: "Primary years must be an array with at least one value." });
        }

        const currentTime=new Date();
        const istTime = new Date(currentTime.getTime() + (5.5 * 60 * 60 * 1000));
        const formattedDate = istTime.toISOString().split("T")[0];

        const formattedDateStart = new Date(`${formattedDate}T00:00:00.000Z`);
        const formattedDateEnd = new Date(`${formattedDate}T23:59:59.999Z`);

        let yearFilter;
        if (year === "overall") {
            yearFilter = { year: { $in: primary_years } };
        } else {
            yearFilter = parseInt(year);
        }
        const commonFilters = {
            passtype: type,
            gender: warden_handling_gender,
            qrcode_status:true,
            ...yearFilter
        };
        const activePassesCount = await collection.countDocuments({
            ...commonFilters,
            from: { $lte: formattedDateEnd },
            to: { $gte: formattedDateStart }
        });
        const toFieldMatchCount = await collection.countDocuments({
            ...commonFilters,
            to: { $gte: formattedDateStart, $lt: formattedDateEnd }
        });

        const overduePassesCount = await collection.countDocuments({
            ...commonFilters,
            re_entry_time: { $in: [null, ""], $exists: true },
            to: { $lt: istTime }
        });

        const reasonTypeAggregation = await collection.aggregate([
            {
                $match: {
                    ...commonFilters,
                    $or: [
                        { from: { $lte: formattedDateEnd }, to: { $gte: formattedDateStart } },
                        { from: formattedDateStart },
                        { to: formattedDateStart }
                    ]
                }
            },
            {
                $group: {
                    _id: {
                        $switch: {
                            branches: [
                                { case: { $eq: [{ $toLower: "$reason_type" }, "medical"] }, then: "Medical" },
                                { case: { $eq: [{ $toLower: "$reason_type" }, "intern"] }, then: "Intern" },
                                { case: { $eq: [{ $toLower: "$reason_type" }, "festival"] }, then: "Festival" },
                                { case: { $eq: [{ $toLower: "$reason_type" }, "semester"] }, then: "Semester" }
                            ],
                            default: "Other"
                        }
                    },
                    count: { $sum: 1 }
                }
            }
        ]).toArray();

        const reasonTypeCounts = reasonTypeAggregation.reduce((acc, item) => {
            acc[item._id] = item.count;
            return acc;
        }, {});

        res.json({
            activePassesCount,
            toFieldMatchCount,
            overduePassesCount,
            reasonTypeCounts
    });
}catch (error) {
        console.error("Error fetching pass analysis:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
});

// pass analysis 3
app.get("/api/pass_analysis_by_date", async (req, res) => {
    
        if (!req.session || req.session.wardenauth !== true) {
            return res.status(401).json({ error: "Unauthorized Access" });
        }
        try {
            await client.connect();
            const db = client.db(dbName);
            const collection = db.collection("pass_details");
    
            const { type, year,date } = req.body;
            if (!type || !year) {
                return res.status(400).json({ error: "Missing 'type' or 'year' parameter in request" });
            }
    
            const warden_id = req.session.unique_number;
            const wardenCollection = db.collection("warden_database");
            const warden_data = await wardenCollection.findOne({ unique_id: warden_id });
    
            if (!warden_data || !warden_data.primary_year) {
                return res.status(400).json({ error: "Invalid warden data." });
            }
    
            const warden_handling_gender = warden_data.gender;
            const primary_years = warden_data.primary_year;
            if (!Array.isArray(primary_years) || primary_years.length === 0) {
                return res.status(400).json({ error: "Primary years must be an array with at least one value." });
            }
    
            const currentTime=new Date();
            const istTime = new Date(currentTime.getTime() + (5.5 * 60 * 60 * 1000));
            const formattedDate = date
    
            const formattedDateStart = new Date(`${formattedDate}T00:00:00.000Z`);
            const formattedDateEnd = new Date(`${formattedDate}T23:59:59.999Z`);
    
            let yearFilter;
            if (year === "overall") {
                yearFilter = { year: { $in: primary_years } };
            } else {
                yearFilter = parseInt(year);
            }
            const commonFilters = {
                passtype: type,
                gender: warden_handling_gender,
                qrcode_status:true,
                ...yearFilter
            };
            const activePassesCount = await collection.countDocuments({
                ...commonFilters,
                from: { $lte: formattedDateEnd },
                to: { $gte: formattedDateStart }
            });
            const toFieldMatchCount = await collection.countDocuments({
                ...commonFilters,
                to: { $gte: formattedDateStart, $lt: formattedDateEnd }
            });
    
            const overduePassesCount = await collection.countDocuments({
                ...commonFilters,
                re_entry_time: { $in: [null, ""], $exists: true },
                to: { $lt: istTime }
            });
    
            const reasonTypeAggregation = await collection.aggregate([
                {
                    $match: {
                        ...commonFilters,
                        $or: [
                            { from: { $lte: formattedDateEnd }, to: { $gte: formattedDateStart } },
                            { from: formattedDateStart },
                            { to: formattedDateStart }
                        ]
                    }
                },
                {
                    $group: {
                        _id: {
                            $switch: {
                                branches: [
                                    { case: { $eq: [{ $toLower: "$reason_type" }, "medical"] }, then: "Medical" },
                                    { case: { $eq: [{ $toLower: "$reason_type" }, "intern"] }, then: "Intern" },
                                    { case: { $eq: [{ $toLower: "$reason_type" }, "festival"] }, then: "Festival" },
                                    { case: { $eq: [{ $toLower: "$reason_type" }, "semester"] }, then: "Semester" }
                                ],
                                default: "Other"
                            }
                        },
                        count: { $sum: 1 }
                    }
                }
            ]).toArray();
    
            const reasonTypeCounts = reasonTypeAggregation.reduce((acc, item) => {
                acc[item._id] = item.count;
                return acc;
            }, {});
    
            res.json({
                activePassesCount,
                toFieldMatchCount,
                overduePassesCount,
                reasonTypeCounts
        });
    }catch (error) {
            console.error("Error fetching pass analysis:", error);
            res.status(500).json({ error: "Internal Server Error" });
        }
    });

// Fetch Warden Active Year
app.get('/api/fetch_warden_year', async (req, res) => {
    if (!req.session || req.session.wardenauth !== true) {
        return res.status(401).json({ error: "Unauthorized Access" });
    }
    try {
        await client.connect();
        const db = client.db(dbName);
        const unique_id = req.session.unique_number;
        const wardenCollection = db.collection("warden_database");

        const warden_data = await wardenCollection.findOne({ unique_id });

        if (!warden_data || !warden_data.primary_year) {
            return res.status(400).json({ error: "Invalid Warden Data" });
        }
        res.json({ primary_years: warden_data.primary_year });
    } catch (error) {
        console.error("Error fetching Warden Years:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
});

// Delete Student or Warden by superior
app.post('/api/delete_student', async (req, res) => {
    if (!req.session || req.session.superiorauth !== true) {
        return res.status(401).json({ error: "Unauthorized Access" });
    }

    const { registration_number, type } = req.body;

    if (!registration_number) {
        return res.status(400).json({ error: "Registration number is required" });
    }

    try {
        await client.connect();
        const db = client.db(dbName);
        const studentDatabase = db.collection("student_database");
        const wardenCollection = db.collection("warden_database");

        let result;

        if (type === "student") {
            result = await studentDatabase.deleteOne({ registration_number });
        } else if (type === "warden") {
            result = await wardenCollection.deleteOne({ unique_id: registration_number });
        } else {
            return res.status(400).json({ error: "Invalid type. Must be 'student' or 'warden'." });
        }

        if (result.deletedCount === 0) {
            return res.status(404).json({ error: "No record found with the given registration number." });
        }

        res.status(200).json({ message: `${type} record deleted successfully.` });

    } catch (error) {
        console.error("❌ Error:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});


// Fetch All passes for superior warden
app.get('/api/fetch_passes_for_superior', async (req, res) => {
    if (!req.session || req.session.superiorauth !== true) {
        return res.status(401).json({ error: "Unauthorized Access" });
    }
    try {
        await client.connect();
        const db = client.db(dbName);
        const passCollection = db.collection("pass_details");

        const passData = await passCollection.find({
            request_completed: false,
            expiry_status: false,
            qrcode_status: false,
            wardern_approval: null,
            superior_wardern_approval: null,
            notify_superior: true
        }).toArray();

        res.status(200).json({ passes: passData });

    } catch (error) {
        console.error("Error fetching passes:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
});

// Fetch All student details for superior warden (sorted)
app.get('/api/fetch_student_details_superior', async (req, res) => {
    if (!req.session || req.session.superiorauth !== true) {
        return res.status(401).json({ error: "Unauthorized Access" });
    }
    try {
        await client.connect();
        const db = client.db(dbName);
        const studentsCollection = db.collection("student_database");
        const student_data = await studentsCollection.find({}).toArray();
        student_data.sort((a, b) => {
            if (b.year !== a.year) {
                return b.year - a.year;
            }
            return a.gender === "Male" ? -1 : 1;
        });

        res.status(200).json({ data: student_data });

    } catch (error) {
        console.error("Error fetching student details:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
});


//logout
app.get('/api/logout', (req, res) => {
    if (req.session) {
        req.session.destroy(err => {
            if (err) {
                return res.status(500).json({ error: "Failed to log out" });
            }
            res.clearCookie('connect.sid');
            return res.json({ message: "Logged out successfully", redirect: "/login" });
        });
    } else {
        return res.status(400).json({ error: "No active session" });
    }
});

//to fetch all the active sessions
app.get('/api/session', (req, res) => {
    if (!req.session) {
        return res.status(500).json({ error: "Session not initialized" });
    }
    res.status(200).json({
        session_data: req.session
    });
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
