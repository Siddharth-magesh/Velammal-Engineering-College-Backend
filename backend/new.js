app.get("/pass_analysis", async (req, res) => {
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

        // Get Current Date & Time in UTC
        const currentTime=new Date();
        const istTime = new Date(currentTime.getTime() + (5.5 * 60 * 60 * 1000));
        const formattedDate = istTime.toISOString().split("T")[0]; // YYYY-MM-DD

        // Convert formatted date back to Date object at 00:00:00 UTC
        const formattedDateStart = new Date(`${formattedDate}T00:00:00.000Z`);
        const formattedDateEnd = new Date(`${formattedDate}T23:59:59.999Z`);

        // Build Year Filter
        let yearFilter;
        if (["1", "2", "3", "4"].includes(year)) {
            yearFilter = { year: parseInt(year) }; // Convert to number
        } else if (year === "overall") {
            yearFilter = { year: { $in: primary_years } };
        } else {
            return res.status(400).json({ error: "Invalid year value." });
        }

        // Common Filters
        const commonFilters = {
            passtype: type,
            gender: warden_handling_gender,
            qrcode_status:true,
            ...yearFilter
        };

        // **First Measure:** Active Passes Count
        const activePassesCount = await collection.countDocuments({
            ...commonFilters,
            $or: [
                { from: { $lte: istTime }, to: { $gte: istTime } }, // Between from and to
                { from: formattedDateStart },
                { to: formattedDateStart }
            ]
        });

        // **Second Measure:** Passes Ending Today
        const toFieldMatchCount = await collection.countDocuments({
            ...commonFilters,
            to: { $gte: formattedDateStart, $lt: formattedDateEnd }
        });

        // **Third Measure:** Overdue Passes Count (Past "to" AND re_entry_time is null)
        const overduePassesCount = await collection.countDocuments({
            ...commonFilters,
            re_entry_time: { $in: [null, ""], $exists: true }, // Ensure it's null or empty
            to: { $lt: istTime } // Already expired
        });

        // **Fourth Measure:** Reason Type Grouped Count
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
            reasonTypeCounts,
            istTime

    });
}catch (error) {
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

        // Get Current Date & Time in UTC
        const currentTime=new Date();
        const istTime = new Date(currentTime.getTime() + (5.5 * 60 * 60 * 1000));
        const formattedDate = date // YYYY-MM-DD

        // Convert formatted date back to Date object at 00:00:00 UTC
        const formattedDateStart = new Date(`${formattedDate}T00:00:00.000Z`);
        const formattedDateEnd = new Date(`${formattedDate}T23:59:59.999Z`);

        // Build Year Filter
        let yearFilter;
        if (["1", "2", "3", "4"].includes(year)) {
            yearFilter = { year: parseInt(year) }; // Convert to number
        } else if (year === "overall") {
            yearFilter = { year: { $in: primary_years } };
        } else {
            return res.status(400).json({ error: "Invalid year value." });
        }

        // Common Filters
        const commonFilters = {
            passtype: type,
            gender: warden_handling_gender,
            qrcode_status:true,
            ...yearFilter
        };

        // **First Measure:** Active Passes Count
        const activePassesCount = await collection.countDocuments({
            ...commonFilters,
            $or: [
                { from: { $lte: istTime }, to: { $gte: istTime } }, // Between from and to
                { from: formattedDateStart },
                { to: formattedDateStart }
            ]
        });

        // **Second Measure:** Passes Ending Today
        const toFieldMatchCount = await collection.countDocuments({
            ...commonFilters,
            to: { $gte: formattedDateStart, $lt: formattedDateEnd }
        });

        // **Third Measure:** Overdue Passes Count (Past "to" AND re_entry_time is null)
        const overduePassesCount = await collection.countDocuments({
            ...commonFilters,
            re_entry_time: { $in: [null, ""], $exists: true }, // Ensure it's null or empty
            to: { $lt: istTime } // Already expired
        });

        // **Fourth Measure:** Reason Type Grouped Count
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

    } catch (error) {
        console.error("Error fetching pass analysis:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
});