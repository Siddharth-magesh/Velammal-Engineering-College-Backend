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

const app = express();
const port = process.env.PORT || 6000;

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
            query = { unique_id: registration_number };
        } else if (type === "superior") {
            collectionName = "warden_database";
            query = { unique_id: registration_number };
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
            } 
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: "Internal Server Error" });
    }
});

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
app.get('/api/verify_student', async (req, res) => {
    if (!req.session || req.session.studentauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }

    const db = client.db(dbName);
    const usersCollection = db.collection('student_database');
    const { phone_number_student } = req.body;
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
app.post('/api/submit_pass_parent_approval', async (req, res) => {
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
            reason_type, reason_for_visit, file_path
        } = req.body;

        if (!mobile_number) {
            return res.status(400).json({ error: "Mobile number is required" });
        }

        const existingPassCheck = await PassCollection.findOne({
            mobile_number,
            request_completed: false,
            expiry_status: false,
            parent_sms_sent_status: false
        });

        const student = await studentDatabase.findOne({ phone_number_student: mobile_number });

        if (!student) {
            return res.status(404).json({ error: "Student record not found" });
        }

        const parentPhoneNumber = student.phone_number_parent;

        if (existingPassCheck) {
            await sendParentApprovalSMS(parentPhoneNumber, name, place_to_visit, reason_for_visit, from, to, existingPassCheck.pass_id);
            await PassCollection.updateOne(
                { pass_id: existingPassCheck.pass_id },
                { $set: { parent_sms_sent_status: true } }
            );
            return res.status(200).json({ message: "SMS sent to parent successfully" });
        }

        const existingPass = await PassCollection.findOne({
            mobile_number,
            request_completed: false,
            expiry_status: false,
            parent_sms_sent_status: true
        });

        if (existingPass) {
            return res.status(200).json({ message: "SMS already sent to parent" });
        }

        const pass_id = uuidv4();
        const PassData = {
            pass_id,
            name,
            mobile_number,
            dept: department_name,
            year,
            room_no,
            registration_number,
            blockname: block_name,
            passtype: pass_type,
            from: new Date(from),
            to: new Date(to),
            place_to_visit,
            reason_type,
            reason_for_visit,
            file_path: file_path || null,
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
            authorised_Security_id : null,
            authorised_warden_id : null
        };

        await PassCollection.insertOne(PassData);
        await sendParentApprovalSMS(parentPhoneNumber, name, place_to_visit, reason_for_visit, from, to, pass_id);
        await PassCollection.updateOne(
            { pass_id },
            { $set: { parent_sms_sent_status: true } }
        );

        res.status(201).json({ message: "Visitor pass submitted and SMS sent to parent" });

    } catch (error) {
        console.error("❌ Error:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

// Endpoint to submit pass with warden and superior approval request
app.post('/api/submit_pass_warden_approval', async (req, res) => {
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
            reason_type, reason_for_visit, file_path
        } = req.body;

        if (!mobile_number) {
            return res.status(400).json({ error: "Mobile number is required" });
        }

        const existingPassCheck = await PassCollection.findOne({
            mobile_number,
            request_completed: false,
            expiry_status: false,
        });

        const student = await studentDatabase.findOne({ phone_number_student: mobile_number });

        if (!student) {
            return res.status(404).json({ error: "Student record not found" });
        }

        if (existingPassCheck) {
            return res.status(200).json({ message: "Notified Warden about the Request" });
        }

        const pass_id = uuidv4();
        const PassData = {
            pass_id,
            name,
            mobile_number,
            dept: department_name,
            year,
            room_no,
            registration_number,
            blockname: block_name,
            passtype: pass_type,
            from: new Date(from),
            to: new Date(to),
            place_to_visit,
            reason_type,
            reason_for_visit,
            file_path: file_path || null,
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
            authorised_Security_id : null,
            authorised_warden_id : null
        };

        await PassCollection.insertOne(PassData);
        res.status(201).json({ message: "Visitor pass submitted and Notified Warden" });

    } catch (error) {
        console.error("❌ Error:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

// Save draft endpoint
app.post('/api/save_draft', async (req, res) => {
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
            reason_type, reason_for_visit, file_path
        } = req.body;

        if (!mobile_number) {
            return res.status(400).json({ error: "Mobile number is required" });
        }

        const student = await studentDatabase.findOne({ phone_number_student: mobile_number });

        if (!student) {
            return res.status(404).json({ error: "Student record not found" });
        }

        const existingDraft = await DraftsCollection.findOne({ registration_number });

        const PassData = {
            pass_id: existingDraft ? existingDraft.pass_id : uuidv4(),
            name,
            mobile_number,
            dept: department_name,
            year,
            room_no,
            registration_number,
            blockname: block_name,
            passtype: pass_type,
            from: new Date(from),
            to: new Date(to),
            place_to_visit,
            reason_type,
            reason_for_visit,
            file_path: file_path || null,
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
            authorised_Security_id : null,
            authorised_warden_id : null
        };

        if (existingDraft) {
            // Replace the existing draft with the new one
            await DraftsCollection.updateOne(
                { registration_number },
                { $set: PassData }
            );
            return res.status(200).json({ message: "Draft updated successfully" });
        } else {
            // Insert new draft
            await DraftsCollection.insertOne(PassData);
            return res.status(201).json({ message: "Visitor pass saved in the draft" });
        }

    } catch (error) {
        console.error("❌ Error:", error);
        res.status(500).json({ error: "Internal server error" });
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

        let warden = await wardensCollection.findOne({ primary_year: student.year, active: true });
        if (!warden) {
            warden = await wardensCollection.findOne({ secondary_year: student.year, active: true });
        }
        if (!warden) {
            return res.status(403).json({ message: 'No active warden found for this student year' });
        }

        await requestsCollection.insertOne({ 
            registration_number, 
            name : student.name,
            requested_foodtype: newFoodType, 
            status: 'Pending', 
            year: student.year, 
            assigned_warden: warden.warden_name
        });

        res.status(200).json({ message: 'Request submitted for approval', requested_foodtype: newFoodType });
    } catch (error) {
        console.error('❌ Error processing request:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Warden fetches pending requests
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

        const primary_year = warden.primary_year;
        const requests = await requestsCollection.find({ year: primary_year }).toArray();

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
            await requestsCollection.deleteOne({ registration_number, name });
            return res.status(200).json({ message: 'Food type change approved', newFoodType: request.requested_foodtype });
        } else if (action === "decline") {
            await requestsCollection.deleteOne({ registration_number, name });
            return res.status(200).json({ message: 'Food type change request declined' });
        } else {
            return res.status(400).json({ error: 'Invalid action' });
        }
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
        const { registration_number, room_number, phone_number_student, phone_number_parent } = req.body;

        await client.connect();
        const db = client.db(dbName);
        const studentCollection = db.collection('student_database');
        const tempRequestCollection = db.collection('profile_change_requests'); 
        const profile = await studentCollection.findOne({ registration_number });
        if (!profile) {
            return res.status(404).json({ error: "Profile not found" });
        }
        const fromData = {
            room_number: profile.room_number,
            phone_number_student: profile.phone_number_student,
            phone_number_parent: profile.phone_number_parent
        };
        const toData = {
            room_number: room_number || profile.room_number,
            phone_number_student: phone_number_student || profile.phone_number_student,
            phone_number_parent: phone_number_parent || profile.phone_number_parent
        };
        const updateRequest = {
            registration_number,
            room_number: toData.room_number,
            year:profile.year,
            phone_number_student: toData.phone_number_student,
            phone_number_parent: toData.phone_number_parent,
            from_data: fromData,
            to_data: toData,
            edit_status: 'Pending',
            created_at: new Date()
        };
        await tempRequestCollection.insertOne(updateRequest);
        await studentCollection.updateOne(
            { registration_number },
            { $set: { edit_status: 'Pending' } }
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

//Supirior wardern fetch for profile
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

        const primary_year = warden.primary_year;
        const requests = await requestsCollection.find({ year: primary_year }).toArray();

        res.status(200).json({ requests });
    } catch (error) {
        console.error('❌ Error fetching requests:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

//Superior warden Profile update handling
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

        if (action === "approve") {
            await studentCollection.updateOne(
                { registration_number: updateRequest.registration_number },
                {
                    $set: {
                        room_number: updateRequest.room_number,
                        phone_number_student: updateRequest.phone_number_student,
                        phone_number_parent: updateRequest.phone_number_parent,
                        edit_status: "Approved"
                    }
                }
            );
            await tempRequestCollection.updateOne(
                { registration_number },
                {
                    $set: {
                        edit_status: "Approved"
                    }
                }
            );
            res.json({
                message: "Request approved and profile updated",
                approved_by: warden.name
            });
        } else if (action === "reject") {
            await tempRequestCollection.updateOne(
                { registration_number },
                {
                    $set: {
                        edit_status: "Rejected"
                    }
                }
            );
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
        
        const student_data = await studentCollection.find({ year: year }).toArray();
       
        if (student_data.length === 0) {
            return res.status(404).json({ message: "No data found" });
        }
        
        res.json({ students: student_data });
    } catch (err) {
        console.error("❌ Error:", err);
        res.status(500).json({ error: "Server error" });
}
});

//to fetch all the request passes by the student
app.get('/api/get_student_pass', async (req, res) => {
    if (!req.session || req.session.studentauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }
    try {
        const student_unique_id = req.session.unique_number;
        await client.connect();
        const db = client.db(dbName);
        const passCollection = db.collection("pass_details");
        
        const passes = await passCollection.find({ registration_number: student_unique_id }).toArray();
        
        if (passes.length === 0) {
            return res.status(404).json({ message: "No passes found" });
        }
        
        res.json({ passes });
    } catch (err) {
        console.error("❌ Error:", err);
        res.status(500).json({ error: "Server error" });
    }
});

//fetch all the pending passes for the warden
app.get('/api/pending_passes', async (req, res) => {
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
        
        const pendingPasses = await passCollection.find({ request_completed: false, year: warden_primary_year }).toArray();
        
        if (pendingPasses.length === 0) {
            return res.status(404).json({ message: "No pending passes found" });
        }
        
        res.json({ pendingPasses });
    } catch (err) {
        console.error("❌ Error:", err);
        res.status(500).json({ error: "Server error" });
    }
});

//Warden Accept Endpoint
app.post('/api/warden_accept', async (req, res) => {
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
        if (passData.wardern_approval !== null) {
            return res.status(400).json({
                message: `The Following wardern ${passData.authorised_warden_id} have already ${passData.wardern_approval ? "approved" : "rejected"} this request. If you haven't approved this request, please contact the warden.`,
            });
        }
        if (warden_data.primary_year !== passData.year) {
            return res.status(400).json({ error: "Warden is accessing the wrong year" });
        }

        const student_registration_number = passData.registration_number;
        const qrPath = await generateQR(pass_id, student_registration_number);
        await passCollection.updateOne(
            { pass_id: pass_id },
            { $set: { wardern_approval: true, qrcode_path: qrPath, qrcode_status: true , authorised_warden_id : warden_unique_id } }
        );

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

        if (warden_data.primary_year !== passData.year) {
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

//Superior Warden Accept Endpoint
app.post('/api/superior_accept', async (req, res) => {
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
        const student_registration_number = passData.registration_number;
        const qrPath = await generateQR(pass_id, student_registration_number);
        await passCollection.updateOne(
            { pass_id: pass_id },
            { $set: { superior_wardern_approval: true, qrcode_path: qrPath, qrcode_status: true , authorised_warden_id : superior_unique_id } }
        );

        res.status(200).json({ message: "Warden approval updated successfully", qrcode_path: qrPath });

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
        const studentCollection = db.collection("student_database");
        const vegCount = await studentCollection.countDocuments({ foodtype: "Veg" });
        const nonVegCount = await studentCollection.countDocuments({ foodtype: "Non-Veg" });

        res.json({ 
            veg_count: vegCount, 
            non_veg_count: nonVegCount 
        });
    } catch (err) {
        console.error("❌ Error:", err);
        res.status(500).json({ error: "Server error" });
    }
});

//fetch student passes
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
            .find({ 
                registration_number: student_unique_id
            })
            .sort({ request_date_time: -1 })
            .toArray();

        if (passes.length === 0) {
            return res.status(404).json({ message: "No passes found" });
        }
        let pendingPass = passes.find(pass => !pass.request_completed);
        let completedPasses = passes.filter(pass => pass.request_completed);
        let sortedPasses = pendingPass ? [pendingPass, ...completedPasses] : completedPasses;

        res.json({ passes: sortedPasses });
    } catch (err) {
        console.error("❌ Error:", err);
        res.status(500).json({ error: "Server error" });
    }
});

//fetch warden data for superior
app.get('/api/get_warden_list', async (req, res) => { 
    if (!req.session || req.session.superiorauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }
    try {
        await client.connect();
        const db = client.db(dbName);
        const wardenCollection = db.collection("warden_database");

        const wardens = await wardenCollection
            .find({}, {projection: {password: 0 }}) 
            .sort({ category: 1 }) 
            .toArray();

        if (wardens.length === 0) {
            return res.status(404).json({ message: "No wardens found" });
        }
        const headWardens = wardens.filter(w => w.category === "head");
        const otherWardens = wardens.filter(w => w.category !== "head");
        res.json({ wardens: [...headWardens, ...otherWardens] });
    } catch (err) {
        console.error("❌ Error:", err);
        res.status(500).json({ error: "Server error" });
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

//security accept
app.post('/api/security_accept', async (req, res) => {
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

        const security_id = req.session.unique_number;
        const exitTime = new Date();

        const updateResult = await passCollection.updateOne(
            { pass_id: pass_id },
            { 
                $set: { 
                    exit_time: exitTime,
                    authorised_Security_id: security_id 
                }
            }
        );

        if (updateResult.matchedCount === 0) {
            return res.status(404).json({ error: "Pass not found" });
        }
        res.status(200).json({
            message: "Exit time updated successfully",
            pass_id: pass_id,
            exit_time: exitTime,
            authorised_Security_id: security_id
        });

    } catch (error) {
        console.error("❌ Error updating exit time:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

//security Decline
app.post('/api/security_decline', async (req, res) => {
    if (!req.session || req.session.securityauth !== true) {
        return res.status(401).json({ error: "Unauthorized access" });
    }

    try {
        const db = client.db(dbName);
        const passCollection = db.collection("pass_details");

        const { pass_id } = req.body;
        if (!pass_id) {
            return res.status(400).json({ error: "Pass ID is required" });
        }

        const security_id = req.session.unique_number;
        const updateResult = await passCollection.updateOne(
            { pass_id: pass_id },
            { 
                $set: { 
                    exit_time: null,
                    authorised_Security_id: security_id,
                }
            }
        );

        if (updateResult.matchedCount === 0) {
            return res.status(404).json({ error: "Pass not found" });
        }

        res.status(200).json({
            message: "Pass request declined successfully",
            pass_id: pass_id,
            exit_time: null,
            authorised_Security_id: security_id
        });

    } catch (error) {
        console.error("❌ Error declining pass request:", error);
        res.status(500).json({ error: "Internal server error" });
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
