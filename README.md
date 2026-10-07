# Notes Making API

A backend REST API for creating and managing notes, built with **Python and FastAPI**.

The application provides note CRUD operations, user registration and login with JWT authentication, SQLite database storage using SQLAlchemy, and optional image/file uploads using ImageKit.

## 🚀 Features

- Create notes
- View all notes
- View a specific note by ID
- Delete a note by ID
- Delete a note by title
- Delete all notes
- User registration
- User login
- JWT access token generation
- Password hashing and verification
- Optional image/file uploads
- Cloud file storage using ImageKit
- SQLite database
- SQLAlchemy ORM
- Pydantic data validation
- Interactive API documentation with Swagger UI

## 🛠️ Tech Stack

- **Python**
- **FastAPI** — REST API framework
- **SQLAlchemy** — ORM
- **SQLite** — Database
- **Pydantic** — Data validation
- **JWT** — Authentication
- **ImageKit** — Cloud file storage
- **Uvicorn** — ASGI server
- **uv** — Python project and dependency management

## 📂 Project Structure

```text
notes-api/
│
├── core.py              # FastAPI application and API endpoints
├── main.py              # Application entry point
├── database.py          # Database configuration and sessions
├── models.py            # SQLAlchemy database models
├── schemas.py           # Pydantic schemas
├── security.py          # Password hashing and JWT authentication
├── image.py             # ImageKit configuration
│
├── pyproject.toml       # Project dependencies and configuration
├── uv.lock              # Locked dependency versions
├── .python-version      # Python version
├── .gitignore           # Files excluded from Git
└── README.md            # Project documentation
