const Note = require('../models/note.model.js');

// Create and Save a new Note
exports.create = (req, res) => {
    if(!req.body.content) {
        return res.status(400).send({
            message: "Note content can not be empty"
        });
    }

    const note = new Note({
        title: req.body.title || "Untitled Note", 
        content: req.body.content,
        category: req.body.category || "General",
        tags: req.body.tags || []
    });

    note.save()
    .then(data => {
        res.send(data);
    }).catch(err => {
        res.status(500).send({
            message: err.message || "Some error occurred while creating the Note."
        });
    });
};

// Retrieve and return all notes from the database.
exports.findAll = (req, res) => {
    const { search, category, sortBy } = req.query;
    let queryCondition = {};

    if (category) {
        queryCondition.category = category;
    }

    if (search) {
        queryCondition.$or = [
            { title: { $regex: search, $options: 'i' } },
            { content: { $regex: search, $options: 'i' } }
        ];
    }

    let sortCondition = { updatedAt: -1 };
    if (sortBy === 'title') {
        sortCondition = { title: 1 };
    } else if (sortBy === 'createdAt') {
        sortCondition = { createdAt: -1 };
    }

    Note.find(queryCondition)
    .sort(sortCondition)
    .then(notes => {
        res.send(notes);
    }).catch(err => {
        res.status(500).send({
            message: err.message || "Some error occurred while retrieving notes."
        });
    });
};

// Find a single note with a noteId
exports.findOne = (req, res) => {
    Note.findById(req.params.noteId)
    .then(note => {
        if(!note) {
            return res.status(404).send({
                message: "Note not found with id " + req.params.noteId
            });            
        }
        res.send(note);
    }).catch(err => {
        if(err.kind === 'ObjectId') {
            return res.status(404).send({
                message: "Note not found with id " + req.params.noteId
            });                
        }
        return res.status(500).send({
            message: "Error retrieving note with id " + req.params.noteId
        });
    });
};

// Update a note identified by the noteId in the request
exports.update = (req, res) => {
    if(!req.body.content) {
        return res.status(400).send({
            message: "Note content can not be empty"
        });
    }

    const updateFields = {
        title: req.body.title || "Untitled Note",
        content: req.body.content
    };

    if (req.body.category !== undefined) updateFields.category = req.body.category;
    if (req.body.tags !== undefined) updateFields.tags = req.body.tags;

    Note.findByIdAndUpdate(req.params.noteId, updateFields, {new: true})
    .then(note => {
        if(!note) {
            return res.status(404).send({
                message: "Note not found with id " + req.params.noteId
            });
        }
        res.send(note);
    }).catch(err => {
        if(err.kind === 'ObjectId') {
            return res.status(404).send({
                message: "Note not found with id " + req.params.noteId
            });                
        }
        return res.status(500).send({
            message: "Error updating note with id " + req.params.noteId
        });
    });
};

// Delete a note with the specified noteId in the request
exports.delete = (req, res) => {
    Note.findByIdAndRemove(req.params.noteId)
    .then(note => {
        if(!note) {
            return res.status(404).send({
                message: "Note not found with id " + req.params.noteId
            });
        }
        res.send({message: "Note deleted successfully!"});
    }).catch(err => {
        if(err.kind === 'ObjectId' || err.name === 'NotFound') {
            return res.status(404).send({
                message: "Note not found with id " + req.params.noteId
            });                
        }
        return res.status(500).send({
            message: "Could not delete note with id " + req.params.noteId
        });
    });
};