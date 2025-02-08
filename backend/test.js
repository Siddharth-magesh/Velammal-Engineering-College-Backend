const express = require('express');
const { MongoClient } = require('mongodb');
const session = require('express-session');
require('dotenv').config();
const bcrypt = require('bcrypt');
const { v4: uuidv4 } = require('uuid');

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

async function connectToDatabase() {
    try {
        await client.connect();
        console.log("✅ Connected to MongoDB");
    } catch (error) {
        console.error("❌ MongoDB connection error:", error);
    }
}
connectToDatabase();

// Login Route
app.post('/api/login', async (req, res) => {
    try {
        const db = client.db(dbName);
        const { registration_number, password, type } = req.body;
        if (!registration_number || !password || !type) {
            return res.status(400).json({ error: "All fields (registration_number, password, type) are required" });
        }
        let collectionName;
        if (type === "student") {
            collectionName = "student_database";
        } else if (type === "warden") {
            collectionName = "warden_database";
        } else if (type === "superior") {
            collectionName = "superior_warden_database";
        } else {
            return res.status(400).json({ error: "Invalid user type" });
        }
        const collection = db.collection(collectionName);
        const user = await collection.findOne({ registration_number });
        if (!user) {
            return res.status(404).json({ error: 'User Not Found' });
        }
        const isMatch = await bcrypt.compare(password, user.password);
        if (!isMatch) {
            return res.status(401).json({ error: "Invalid credentials" });
        }
        req.session.auth = false;
        req.session.wardenauth = false;
        req.session.superiorauth = false;
        if (type === "student") {
            req.session.auth = true;
        } else if (type === "warden") {
            req.session.wardenauth = true;
        } else if (type === "superior") {
            req.session.superiorauth = true;
        }
        req.session.registration_number = registration_number;
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

//Verify Student using mobile number
app.get('/api/verify_student', async (req, res) => {
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

//submit pass
app.post('/api/submit_pass', async (req, res) => {
    const accountSid = "AC2d825693a3e1207c1998b6a2a99dd5d2";
    const authToken = "2b702fcdd117c2c8e817d51f1eacb75f";
    const twilioPhoneNumber = "+16203019504";

    const twilioClient = require('twilio')(accountSid, authToken);

    try {
        await client.connect();
        const db = client.db(dbName);
        const PassCollection = db.collection('pass_details');
        const studentDatabase = db.collection('student_database');

        const {
            mobile_number, name, department_name, year, room_no, registration_number, admission_no,
            block_name, pass_type, from, to, place_to_visit,
            reason_type, reason_for_visit, file_path
        } = req.body;

        if (!mobile_number) {
            return res.status(400).json({ error: "Mobile number is required" });
        }

        const pass_id = uuidv4();
        const PassData = {
            pass_id,
            name,
            dept: department_name,
            year,
            room_no,
            registration_number,
            admin_number: admission_no,
            blockname: block_name,
            passtype: pass_type,
            from: new Date(from),
            to: new Date(to),
            place_to_visit,
            reason_type,
            reason_for_visit,
            file_path: file_path || null,
            barcode_path: null,
            parent_approval: false,
            wardern_approval: false,
            superior_wardern: false,
            barcode_status: false,
            exit_time: null,
            re_entry_time: null,
            delay_status: false,
            draft_status: true,
            request_completed: false,
            request_time: new Date(),
            expiry_status: false,
            request_date_time: new Date()
        };

        await PassCollection.insertOne(PassData);
        const student = await studentDatabase.findOne({ phone_number_student: mobile_number });
        if (!student) {
            return res.status(404).json({ error: "Student record not found" });
        }

        const parentPhoneNumber = student.phone_number_parent;
        const approvalUrl = `http://localhost:5000/api/parent_accept/${pass_id}`;
        const rejectionUrl = `http://localhost:5000/api/parent_not_accept${pass_id}`;
        const smsMessage = `
            Pass_id : ${pass_id}
            ${name} has requested a pass to visit ${place_to_visit} for ${reason_for_visit} 
            from ${from} to ${to}.
            
            ✅ Approve: ${approvalUrl}
            ❌ Reject: ${rejectionUrl}
        `;
        await twilioClient.messages.create({
            body: smsMessage,
            from: twilioPhoneNumber,
            to: parentPhoneNumber
        });

        res.status(201).json({ message: "Visitor pass submitted and SMS sent to parent" });

    } catch (error) {
        console.error("❌ Error:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

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

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
