const express = require('express');
const { MongoClient } = require('mongodb');

const app = express();
const port = 5000;

const uri = "mongodb://localhost:27017";  // Replace with your MongoDB connection string
const client = new MongoClient(uri);
const dbName = "VEC";    

// Academi calender
 app.get('/api/academic', async (req, res) => {
      try {
        const db = client.db(dbName);
        const collection = db.collection('academic_calender');

        // Fetch the calendar document
        const calendar = await collection.findOne();

        if (!calendar || !calendar.year || calendar.year.length === 0) {
          return res.status(404).json({ message: 'No calendar data found' });
        }

        res.status(200).json(calendar);
      } catch (error) {
        console.error('❌ Error fetching calendar:', error);
        res.status(500).json({ error: 'Internal Server Error' });
      }
    });

//about_placement
    app.get('/api/about_placement', async (req, res) => {
      try {
        const db = client.db(dbName);
        const collection = db.collection('about_placement');

        const aboutData = await collection.findOne();

        if (!aboutData || Object.keys(aboutData).length === 0) {
          return res.status(404).json({ message: 'No about placement data found' });
        }

        res.status(200).json(aboutData);
      } catch (error) {
        console.error('❌ Error fetching about placement data:', error);
        res.status(500).json({ error: 'Internal Server Error' });
      }
    });

app.get('/api/about_us', async (req, res) => {
    const db = client.db(dbName);
    const collection = db.collection('about_us');

    try {
        const announcements = await collection.find({}).toArray();
        if (announcements.length === 0) {
            return res.status(404).json({ message: 'No announcements found' });
        }
        res.status(200).json(announcements);
    } catch (error) {
        console.error('❌ Error fetching announcements:', error);
        res.status(500).json({ error: 'Error fetching announcements' });
    }
});


app.get('/api/admission', async (req, res) => {
    const db = client.db(dbName);
    const collection = db.collection('admission');

    try {
        const announcements = await collection.find({}).toArray();
        if (announcements.length === 0) {
            return res.status(404).json({ message: 'No admission found' });
        }
        res.status(200).json(announcements);
    } catch (error) {
        console.error('❌ Error fetching admission:', error);
        res.status(500).json({ error: 'Error fetching admission' });
    }
});

app.get('/api/organization_chart', async (req, res) => {
    const db = client.db(dbName);
    const collection = db.collection('organization_chart');

    try {
        const announcements = await collection.find({}).toArray();
        if (announcements.length === 0) {
            return res.status(404).json({ message: 'No organization chart found' });
        }
        res.status(200).json(announcements);
    } catch (error) {
        console.error('❌ Error fetching organization chart:', error);
        res.status(500).json({ error: 'Error fetching organization chart' });
    }
});


app.get('/api/downloads', async (req, res) => {
    const db = client.db(dbName);
    const collection = db.collection('downloads');

    try {
        const announcements = await collection.find({}).toArray();
        if (announcements.length === 0) {
            return res.status(404).json({ message: 'No downloads found' });
        }
        res.status(200).json(announcements);
    } catch (error) {
        console.error('❌ Error fetching downloads:', error);
        res.status(500).json({ error: 'Error fetching downloads' });
    }
});

app.get('/api/hostel_menu', async (req, res) => {
    const db = client.db(dbName);
    const collection = db.collection('hostel_menu');

    try {
        const announcements = await collection.find({}).toArray();
        if (announcements.length === 0) {
            return res.status(404).json({ message: 'No announcements found' });
        }
        res.status(200).json(announcements);
    } catch (error) {
        console.error('❌ Error fetching announcements:', error);
        res.status(500).json({ error: 'Error fetching announcements' });
    }
});

app.get('/api/help_desk', async (req, res) => {
    const db = client.db(dbName);
    const collection = db.collection('help_desk');

    try {
        const announcements = await collection.find({}).toArray();
        if (announcements.length === 0) {
            return res.status(404).json({ message: 'No announcements found' });
        }
        res.status(200).json(announcements);
    } catch (error) {
        console.error('❌ Error fetching announcements:', error);
        res.status(500).json({ error: 'Error fetching announcements' });
    }
});



app.listen(port, () => {
    console.log(`🚀 Server running at http://localhost:${port}`);
});