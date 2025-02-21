// pass analysis 2
app.get("/pass_analysis", async (req, res) => {
    if (!req.session || req.session.wardenauth !== true) {
        return res.status(401).json({ error: "Unauthorized Access" });
    }
    try {
        await client.connect();
        const db = client.db(dbName);
        const collection = db.collection("pass_details");

        const { type } = req.query;
        if (!type) {
            return res.status(400).json({ error: "Missing 'type' parameter in query" });
        }
        const now = new Date();
        const formattedDate = now.toISOString().split("T")[0];
        const formattedTime = now.toISOString().split("T")[1];
        const formattedTimeWithOffset = `T${formattedTime.slice(0, -1)}+00:00`;
        const firstMeasureCount = await collection.countDocuments({
            passtype: type,
            $or: [
                { 
                    from: { $lte: new Date() },
                    to: { $gte: new Date() }
                },
                { 
                    from: { 
                        $gte: new Date(`${formattedDate}T00:00:00.000Z`), 
                        $lt: new Date(`${formattedDate}T23:59:59.999Z`) 
                    }
                },
                { 
                    to: { 
                        $gte: new Date(`${formattedDate}T00:00:00.000Z`), 
                        $lt: new Date(`${formattedDate}T23:59:59.999Z`) 
                    }
                }
            ]
        });
        
        const secondMeasureCount = await collection.countDocuments({
            passtype: type,
            to: { 
                $gte: new Date(`${formattedDate}T00:00:00.000Z`), 
                $lt: new Date(`${formattedDate}T23:59:59.999Z`)
              }
        });
        const thirdMeasureCount = await collection.countDocuments({
            passtype: type,
            to: { $lt: new Date(`${formattedDate}T23:59:59.999Z`) },
            re_entry_time: { $in: [null, ""] }
        });
        const reasonTypeAggregation = await collection.aggregate([
            {
                $match: {
                    passtype: type,
                    $or: [
                        { 
                            from: { 
                                $lte: new Date(`${formattedDate}T23:59:59.999Z`) 
                            }, 
                            to: { 
                                $gte: new Date(`${formattedDate}T00:00:00.000Z`) 
                            } 
                        }
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
            activePassesCount: firstMeasureCount,
            toFieldMatchCount: secondMeasureCount,
            overduePassesCount: thirdMeasureCount,
            reasonTypeCounts
        });

    } catch (error) {
        console.error("Error fetching pass analysis:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
});

// pass analysis 3
app.get("/pass_analysis_by_date", async (req, res) => {
    if (!req.session || req.session.wardenauth !== true) {
        return res.status(401).json({ error: "Unauthorized Access" });
    }
    try {
        await client.connect();
        const db = client.db(dbName);
        const collection = db.collection("pass_details");
        const { type, date } = req.query;
        if (!type) {
            return res.status(400).json({ error: "Missing 'type' parameter in query" });
        }
        if (!date) {
            return res.status(400).json({ error: "Missing 'date' parameter in query" });
        }
        const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
        if (!dateRegex.test(date)) {
            return res.status(400).json({ error: "Invalid date format. Use 'YYYY-MM-DD'." });
        }
        const formattedDate = date; 
        const now = new Date();
        const formattedTime = now.toISOString().split("T")[1];
        const formattedTimeWithOffset = `T${formattedTime.slice(0, -1)}+00:00`;
        const firstMeasureCount = await collection.countDocuments({
            passtype: type,
            $or: [
                { 
                    from: { $lte: new Date() },
                    to: { $gte: new Date() }
                },
                { 
                    from: { 
                        $gte: new Date(`${formattedDate}T00:00:00.000Z`), 
                        $lt: new Date(`${formattedDate}T23:59:59.999Z`) 
                    }
                },
                { 
                    to: { 
                        $gte: new Date(`${formattedDate}T00:00:00.000Z`), 
                        $lt: new Date(`${formattedDate}T23:59:59.999Z`) 
                    }
                }
            ]
        });
        
        const secondMeasureCount = await collection.countDocuments({
            passtype: type,
            to: { 
                $gte: new Date(`${formattedDate}T00:00:00.000Z`), 
                $lt: new Date(`${formattedDate}T23:59:59.999Z`)
              }
        });
        const thirdMeasureCount = await collection.countDocuments({
            passtype: type,
            to: { $lt: new Date(`${formattedDate}T23:59:59.999Z)`),
            re_entry_time: { $in: [null, ""] }
        }
        });
        const reasonTypeAggregation = await collection.aggregate([
            {
                $match: {
                    passtype: type,
                    $or: [
                        { 
                            from: { 
                                $lte: new Date(`${formattedDate}T23:59:59.999Z`) 
                            }, 
                            to: { 
                                $gte: new Date(`${formattedDate}T00:00:00.000Z`) 
                            } 
                        }
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
            activePassesCount: firstMeasureCount,
            toFieldMatchCount: secondMeasureCount,
            overduePassesCount: thirdMeasureCount,
            reasonTypeCounts
        });

    } catch (error) {
        console.error("Error fetching pass analysis:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
});