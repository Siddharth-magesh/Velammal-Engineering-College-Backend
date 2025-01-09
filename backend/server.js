const express = require('express');
const { MongoClient } = require('mongodb');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 5000;

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

app.get("/", (req, res) => {
    res.send("Welcome to the Node.js MongoDB API!");
});

//Department Details
app.get('/api/department/:id', async (req, res) => {
    const departmentId = parseInt(req.params.id); 
    const db = client.db(dbName);
    const collection = db.collection('vision_and_mission');

    try {
        const result = await collection.findOne({ department_id: departmentId });
        if (result) {
            res.json(result);
        } else {
            res.status(404).json({ error: "Department not found" });
        }
    } catch (error) {
        console.error("❌ Error fetching department data:", error);
        res.status(500).json({ error: "Error fetching data" });
    }
});

// Head Of Department Details
app.get('/api/hod/:department_id', async (req, res) => {
    const departmentId = req.params.department_id;
    const db = client.db(dbName);
    const hodsCollection = db.collection('hods');

    try {
        const hod = await hodsCollection.findOne({
            Unique_id: { $regex: `VEC-${departmentId}-` }
        });

        if (hod) {
            res.json({
                Name: hod.Name,
                Unique_id: hod.Unique_id,
                Qualification: hod.Qualification,
                Hod_message: hod.Hod_message,
                Image: hod.Image,
                Social_media_links: hod.Social_media_links
            });
        } else {
            res.status(404).json({ error: "HOD not found for this department." });
        }
    } catch (error) {
        console.error("❌ Error fetching HOD details:", error);
        res.status(500).json({ error: "Error fetching HOD details" });
    }
});

//Staff Details
app.get('/api/staff/:deptId', async (req, res) => {
    const deptId = req.params.deptId;
    const db = client.db(dbName);
    const collection = db.collection('staff_details');

    try {
        const staffDetails = await collection.find(
            { unique_id: { $regex: `^VEC-${deptId}-` } }, 
            {
                projection: {
                    Name: 1,
                    Designation: 1,
                    Photo: 1,
                    "Google Scholar Profile": 1,
                    "Research Gate": 1,
                    "Orchid Profile": 1,
                    "Publon Profile": 1,
                    "Scopus Author Profile": 1,
                    "LinkedIn Profile": 1,
                    _id: 0, 
                }
            }
        ).toArray();

        if (staffDetails.length > 0) {
            res.status(200).json(staffDetails);
        } else {
            res.status(404).json({ message: 'No staff found for the given department ID.' });
        }
    } catch (error) {
        console.error("❌ Error fetching staff details:", error);
        res.status(500).json({ error: "Error fetching staff details" });
    }
});

//Infrastructure
app.get('/api/infrastructure/:deptId', async (req, res) => {
    const deptId = parseInt(req.params.deptId);
    const db = client.db(dbName);
    const collection = db.collection('infrastructure');

    try {
        const result = await collection.findOne({ dept_id: deptId });

        if (result) {
            res.status(200).json(result);
        } else {
            res.status(404).json({ error: "No infrastructure details found for the given department ID." });
        }
    } catch (error) {
        console.error("Error fetching infrastructure details:", error);
        res.status(500).json({ error: "Error fetching infrastructure details" });
    }
});

//Student Records
app.get('/api/student-activities/:deptId', async (req, res) => {
    const deptId = parseInt(req.params.deptId);
    const db = client.db(dbName);
    const collection = db.collection('student_activities');

    try {
        const result = await collection.findOne({ dept_id: deptId });

        if (result) {
            res.status(200).json(result);
        } else {
            res.status(404).json({ error: "No student activities found for the given department ID." });
        }
    } catch (error) {
        console.error("Error fetching student activities:", error);
        res.status(500).json({ error: "Error fetching student activities" });
    }
});

// Support Staff Details
app.get('/api/support-staff/:deptId', async (req, res) => {
    const deptId = req.params.deptId;
    const db = client.db(dbName);
    const collection = db.collection('support_staffs');

    try {
        const result = await collection.findOne({
            "supporting_staff.Unique_id": { $regex: `^VEC-${deptId}-` }
        });

        if (result && result.supporting_staff.length > 0) {
            const filteredStaff = result.supporting_staff.filter(staff =>
                staff.Unique_id.startsWith(`VEC-${deptId}-`)
            );
            res.status(200).json(filteredStaff);
        } else {
            res.status(404).json({ message: 'No support staff found for the given department ID.' });
        }
    } catch (error) {
        console.error("❌ Error fetching support staff details:", error);
        res.status(500).json({ error: "Error fetching support staff details" });
    }
});

// MOUs Details Endpoint
app.get('/api/mous/:deptId/:uniqueId?', async (req, res) => {
    const { deptId, uniqueId } = req.params;
    const db = client.db(dbName);
    const collection = db.collection('MOUs');

    try {
        const departmentData = await collection.findOne({
            "VEC.Departments": deptId
        });

        if (!departmentData) {
            return res.status(404).json({ message: "Department not found" });
        }

        const department = departmentData.VEC.find(dept => dept.Departments === deptId);

        if (!department) {
            return res.status(404).json({ message: "Department not found" });
        }
        if (uniqueId) {
            const filteredMOUs = department.MOUs.filter(mou =>
                mou.unique_id.toString() === uniqueId
            );

            if (filteredMOUs.length > 0) {
                return res.status(200).json(filteredMOUs);
            } else {
                return res.status(404).json({ message: "No MOU found with the provided unique_id or year." });
            }
        }
        const uniqueIdsList = department.MOUs.map(mou => mou.unique_id);
        return res.status(200).json({ unique_ids: uniqueIdsList });

    } catch (error) {
        console.error("❌ Error fetching MOUs:", error);
        res.status(500).json({ error: "Error fetching MOUs" });
    }
});

// Department Activities Endpoint
app.get('/api/department_activities/:deptId', async (req, res) => {
    const { deptId } = req.params;
    const db = client.db(dbName);
    const collection = db.collection('department_activities');

    try {
        const departmentData = await collection.findOne({ dept_id: deptId });

        if (!departmentData) {
            return res.status(404).json({ message: "Department not found" });
        }

        const sortedActivities = departmentData.dept_activities.sort((a, b) => {
            const dateA = new Date(a.date);
            const dateB = new Date(b.date);
            return dateB - dateA;
        });

        return res.status(200).json(sortedActivities);

    } catch (error) {
        console.error("❌ Error fetching department activities:", error);
        res.status(500).json({ error: "Error fetching department activities" });
    }
});

// Curriculum 
app.get('/api/curriculum/:deptId', async (req, res) => {
    const { deptId } = req.params;
    const db = client.db(dbName);
    const collection = db.collection('curriculum');

    try {
        const departmentData = await collection.findOne({ dept_id: deptId });
        if (!departmentData) {
            return res.status(404).json({ message: "Department not found" });
        }
        res.status(200).json(departmentData);

    } catch (error) {
        console.error("❌ Error fetching curriculum data:", error);
        res.status(500).json({ error: "Error fetching curriculum data" });
    }
});

//Research Data
app.get('/api/fetch-research-data/:dept_id/:year', async (req, res) => {
    const { dept_id, year } = req.params;

    if (!dept_id || !year) {
        return res.status(400).json({ error: 'Both dept_id and year are required' });
    }

    const db = client.db(dbName);
    const collection = db.collection('research_data');

    try {
        const result = await collection.find({
            dept_id: dept_id,
            "data.data.year": year
        }).toArray();

        if (result.length === 0) {
            return res.status(404).json({ message: 'No research data found for the given department and year' });
        }

        res.status(200).json(result);
    } catch (error) {
        console.error("❌ Error fetching research data:", error);
        res.status(500).json({ error: "Error fetching research data" });
    }
});

app.listen(port, () => {
    console.log(`🚀 Server running at http://localhost:${port}`);
});