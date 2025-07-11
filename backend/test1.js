const express = require('express');
const { MongoClient } = require('mongodb');

const app = express();
const port = 5000;

const uri = "mongodb://localhost:27017";  // Replace with your MongoDB connection string
const client = new MongoClient(uri);
const dbName = "NEW_VEC";    

app.get('/api/patents', async (req, res) => {
    try {
        await client.connect();
        const db = client.db(dbName);
        const collection = db.collection('overall_patent');  // Replace with your collection name

        const patentData = await collection.find({}).toArray();
        if (patentData.length === 0) {
            return res.status(404).json({ message: 'No patent data found' });
        }
        res.status(200).json(patentData);

    } catch (error) {
        console.error('❌ Error fetching patent data:', error);
        res.status(500).json({ error: 'Error fetching patent data' });
    } finally {
        await client.close();
    }
});

app.listen(port, () => {
    console.log(`🚀 Server running at http://localhost:${port}`);
});