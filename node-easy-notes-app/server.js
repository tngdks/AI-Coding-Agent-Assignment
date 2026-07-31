const express = require('express');
const bodyParser = require('body-parser');

// Create Express app
const app = express();

// Parse application/x-www-form-urlencoded
app.use(bodyParser.urlencoded({ extended: true }));

// Parse application/json
app.use(bodyParser.json());

// Configure database
const dbConfig = require('./config/database.config.js');
const mongoose = require('mongoose');

// Connect to MongoDB
mongoose
    .connect(dbConfig.url)
    .then(() => {
        console.log("Successfully connected to the database");
    })
    .catch((err) => {
        console.error("Could not connect to the database. Exiting now...", err);
        process.exit(1);
    });

// Default route
app.get('/', (req, res) => {
    res.json({
        message: "Welcome to EasyNotes application. Take notes quickly. Organize and keep track of all your notes."
    });
});

// Notes routes
require('./app/routes/note.routes.js')(app);

// Start server
const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
    console.log(`Server is listening on port ${PORT}`);
});