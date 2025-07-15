const express = require('express');
const { MongoClient } = require('mongodb');

const app = express();
const port = 5000;

const uri = "mongodb://localhost:27017";  // Replace with your MongoDB connection string
const client = new MongoClient(uri);
const dbName = "VEC";    

//programmes_list
app.get('/api/programmes_list', async (req, res) => {
    const db = client.db("NEW_VEC");
    const collection = db.collection('programmes_list');

    try {
        const announcements = await collection.find({}).toArray();
        if (announcements.length === 0) {
            return res.status(404).json({ message: 'No programmes list found' });
        }
        res.status(200).json(announcements);
    } catch (error) {
        console.error('❌ Error fetching programmes list:', error);
        res.status(500).json({ error: 'Error fetching programmes list' });
    }
});
//Department_list
app.get('/api/departments_list', async (req, res) => {
    const db = client.db(dbName);
    const collection = db.collection('departments_list');

    try {
        const announcements = await collection.find({}).toArray();
        if (announcements.length === 0) {
            return res.status(404).json({ message: 'No announcements found' });
        }
        res.status(200).json(announcements);
    } catch (error) {
        console.error('❌ Error fetching announcements:', error);
        res.status(500).json({ error: 'Error fetching announcements' });
    }
});


app.listen(port, () => {
    console.log(`🚀 Server running at http://localhost:${port}`);
});