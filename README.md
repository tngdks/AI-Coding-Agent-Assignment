# AI Coding Agent Assignment

## Overview

This project implements an AI-powered coding agent in Python that can understand an existing software repository, generate an execution plan, implement a requested product feature, validate its work, and summarize the completed changes.

The target repository used for this assignment is the **Node Easy Notes** application.

The agent was given only the following product request:

> **"Improve the application so users can better organise and search their notes."**

Without additional guidance, the agent explored the repository, identified the relevant files, implemented the required enhancements, preserved the existing CRUD functionality, and generated documentation describing its work.

---

# Features Implemented

The AI agent enhanced the Node Easy Notes application by adding:

- ✅ Note Categories
- ✅ Note Tags
- ✅ Search by title and content
- ✅ Category-based filtering
- ✅ Sorting by title
- ✅ Sorting by creation date
- ✅ Combined search, filtering, and sorting through query parameters

Example:

```
GET /notes?search=meeting&category=Work&sortBy=title
```

---

# Architecture

The AI Coding Agent is modular and organized into independent components.

```
agent/
│
├── main.py
├── explorer.py
├── repository_analyzer.py
├── planner.py
├── context_builder.py
├── prompts.py
├── llm.py
├── modifier.py
├── validator.py
├── summarizer.py
├── logger.py
├── config.py
├── tools.py
└── utils.py
```

## Component Responsibilities

### Repository Explorer

Scans the repository and builds an overview of the project structure.

---

### Repository Analyzer

Analyzes dependencies, architecture, and identifies files relevant to the requested feature.

---

### Context Builder

Collects only the required project files and prepares the context provided to the language model.

---

### Planner

Generates an execution plan before making modifications.

---

### LLM Interface

Provides an abstraction layer for interacting with the configured language model.

---

### Modifier

Applies the planned code changes while preserving existing functionality.

---

### Validator

Performs validation after modifications and verifies that the repository remains functional.

---

### Summarizer

Generates human-readable documentation describing the completed implementation.

---

# Agent Workflow

The agent follows this workflow:

1. Explore the repository
2. Analyze project structure
3. Identify relevant files
4. Build context
5. Generate execution plan
6. Modify the codebase
7. Validate changes
8. Generate summary and reports

---

# Repository Exploration

Before making changes, the agent automatically analyzes the repository.

The exploration phase identifies:

- Controllers
- Models
- Routes
- Configuration files
- Dependencies
- Overall project structure

Only the files relevant to the requested task are included in the LLM context to reduce unnecessary tokens while maintaining implementation quality.

---

# Implementation Details

The existing CRUD functionality was preserved.

The following enhancements were added:

## Categories

Each note can now belong to a category.

Example:

```json
{
  "category": "Work"
}
```

---

## Tags

Each note supports multiple tags.

Example:

```json
{
  "tags": ["AI", "Assignment"]
}
```

---

## Search

Notes can be searched using the existing endpoint.

Example:

```
GET /notes?search=meeting
```

The search checks both:

- Title
- Content

---

## Category Filtering

Example:

```
GET /notes?category=Work
```

---

## Sorting

Alphabetical:

```
GET /notes?sortBy=title
```

Newest first:

```
GET /notes?sortBy=createdAt
```

---

## Combined Queries

Search, filtering and sorting can be combined.

Example:

```
GET /notes?search=AI&category=Work&sortBy=title
```

---

# Validation

The modified application was validated by:

- Starting the Node.js application
- Connecting to MongoDB
- Creating notes
- Retrieving notes
- Updating notes
- Deleting notes
- Testing search functionality
- Testing category filtering
- Testing sorting

Existing CRUD functionality continues to work correctly.

---

# Dependency Compatibility

During validation, the original sample project was found to use an older version of Mongoose and the MongoDB Node.js driver that was incompatible with the latest MongoDB Community Server.

To restore compatibility, the project dependencies and MongoDB connection configuration were updated to work with the current Mongoose and MongoDB driver APIs while preserving the application's existing behavior.

This ensured successful application startup, database connectivity, and functional CRUD operations on modern MongoDB installations.

---

# Assumptions

- The target repository follows a standard MVC architecture.
- MongoDB is available during execution.
- The requested product improvement should be implemented while preserving backward compatibility.
- Existing API endpoints should continue to function without breaking changes.

---

# Trade-offs

The implementation extends the existing `/notes` endpoint using query parameters instead of introducing multiple new endpoints.

Benefits of this approach:

- Preserves backward compatibility
- Minimizes code changes
- Keeps the REST API simple
- Reduces maintenance complexity

---

# Technologies Used

### AI Agent

- Python 3.11+
- OpenAI LLM
- Modular Agent Architecture

### Target Application

- Node.js
- Express.js
- MongoDB
- Mongoose

---

# How to Run

## 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd <repository-name>
```

---

## 2. Configure Environment

Update the `.env` file with your OpenAI API key and project settings.

Example:

```env
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o
TARGET_REPO_PATH=./node-easy-notes-app
```

---

## 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Run the AI Agent

```bash
python -m agent.main
```

---

## 5. Run the Target Application

```bash
cd node-easy-notes-app

npm install

npm start
```

---

# Generated Outputs

The AI agent generates the following reports:

- `plan.md`
- `repository_map.md`
- `dependency_analysis.md`
- `change_impact.md`
- `validation_report.md`
- `summary.md`

---

# Screen Recording

Google Drive Link:

**<Add your Google Drive link here>**

---

# Future Improvements

Potential enhancements include:

- Semantic search using vector embeddings
- Automatic tag generation
- Natural language note search
- Repository caching for faster analysis
- Multi-file parallel modification
- Automatic rollback when validation fails
- Support for additional programming languages

---

# Author

**Devendra Sharma**
