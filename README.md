# Docs Search & RAG Chat

An AI-powered Document Search and Retrieval-Augmented Generation (RAG) Chat application built with a **Django REST API** backend and a modern **Vue 3 + TypeScript** frontend.

Upload PDF documents, automatically index them using vector embeddings (`pgvector`), and interact with your knowledge base via an intelligent chat interface.

---

## 🚀 System Architecture

```
                      +-------------------------------------------------+
                      |              Vue 3 + Vite Frontend              |
                      |  - Pinia Stores (Auth, Chat, Documents)         |
                      |  - Tailwind CSS v4 + Reka UI Component System   |
                      +------------------------+------------------------+
                                               |
                                               | REST API (JSON / JWT)
                                               v
                      +-------------------------------------------------+
                      |               Django REST Backend               |
                      |  - Django 5.2 REST Framework                    |
                      |  - Djoser Authentication (JWT)                  |
                      |  - DRF Spectacular (OpenAPI 3 / Swagger)        |
                      +------------------------+------------------------+
                                               |
                                               | pgvector Cosine Distance
                                               v
                      +-------------------------------------------------+
                      |         PostgreSQL Database + pgvector          |
                      |  - Documents & Chunks (1536-dim embeddings)     |
                      |  - User Accounts & Chat Session Histories       |
                      +-------------------------------------------------+
```

---

## ✨ Features

- **📄 Document Upload & Processing**: Upload PDF documents with automatic chunking and vector storage.
- **🔍 Vector Similarity Search**: Powered by PostgreSQL's `pgvector` extension for efficient cosine similarity queries.
- **💬 Interactive RAG Chat**: Context-aware chat interface querying document chunks to answer questions.
- **🔒 Authentication**: Full User Registration, Login, and JWT Token Management via Djoser.
- **📚 Interactive API Specs**: Embedded Swagger UI auto-generated with `drf-spectacular`.
- **🎨 Responsive UI**: Clean dashboard built with Vue 3 Composition API (`<script setup>`), Tailwind CSS v4, Lucide icons, and Reka UI primitives.

---

## 🛠️ Tech Stack

### Backend
- **Framework**: Python 3.12+, Django 5.2
- **API**: Django REST Framework (DRF)
- **Database**: PostgreSQL with [`pgvector`](https://github.com/pgvector/pgvector-python) extension
- **Auth**: [Djoser](https://djoser.readthedocs.io/) + SimpleJWT
- **API Documentation**: [drf-spectacular](https://drf-spectacular.readthedocs.io/) (OpenAPI 3.0)

### Frontend
- **Framework**: Vue 3 (Composition API, `<script setup>`)
- **Language**: TypeScript
- **Build Tool**: Vite 8
- **State Management**: Pinia
- **Router**: Vue Router
- **Styling**: Tailwind CSS v4, Reka UI, Lucide Vue Next

---

## 📂 Project Structure

```
docs-search/
├── app/                        # Django Backend Project
│   ├── chat/                   # Chat sessions & messaging models, serializers, views
│   │   ├── models.py           # ChatSession, Message models
│   │   ├── serializers.py      # REST serializers
│   │   └── views.py            # ChatSessionViewSet & RAG message handler
│   ├── docs/                   # Document storage & vector chunks app
│   │   ├── models.py           # Document, DocumentChunk (VectorField 1536-dim)
│   │   ├── serializers.py      # Document & Chunk serializers
│   │   └── views.py            # DocumentViewSet & vector search action
│   ├── settings.py             # Database, DRF, JWT, media uploads settings
│   └── urls.py                 # API router and OpenAPI documentation endpoints
├── frontend/                   # Vue 3 Frontend Application
│   ├── src/
│   │   ├── components/         # Auth, Chat, Document dropzone, & UI components
│   │   ├── layouts/            # Main application layout wrappers
│   │   ├── stores/             # Pinia stores (auth, chat, documents)
│   │   ├── types/              # TypeScript interfaces
│   │   ├── App.vue             # Root component
│   │   └── main.ts             # Vue initialization
│   ├── package.json            # Node dependencies and scripts
│   └── vite.config.ts          # Vite configuration
├── uploads/                    # User-uploaded document files directory
└── manage.py                   # Django CLI utility
```

---

## 🌐 Django REST API Specification

The Django backend exposes the following RESTful API endpoints under `/api/v1/`:

### 🔐 Authentication (`/api/v1/auth/`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/users/` | Register a new user |
| `POST` | `/api/v1/auth/jwt/create/` | Obtain JWT access and refresh token pair |
| `POST` | `/api/v1/auth/jwt/refresh/` | Refresh JWT access token |
| `GET` | `/api/v1/auth/users/me/` | Retrieve current authenticated user details |

### 📄 Documents API (`/api/v1/documents/`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/documents/` | List all uploaded documents |
| `POST` | `/api/v1/documents/` | Upload a new PDF document (`multipart/form-data`) |
| `GET` | `/api/v1/documents/{id}/` | Retrieve document metadata and chunks |
| `DELETE` | `/api/v1/documents/{id}/` | Delete a document |
| `POST` | `/api/v1/documents/search/` | Perform similarity search on chunks using embedding vector |

#### Vector Search Payload Example:
```json
POST /api/v1/documents/search/
{
  "embedding": [0.012, -0.043, 0.089, ...]
}
```

### 💬 Chat API (`/api/v1/chat/`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/chat/` | List all chat sessions |
| `POST` | `/api/v1/chat/` | Create a new chat session |
| `GET` | `/api/v1/chat/{id}/` | Fetch session history (messages) |
| `POST` | `/api/v1/chat/{id}/send-message/` | Send message and execute RAG pipeline |

#### Send Message Payload & Response:
```json
// POST /api/v1/chat/{id}/send-message/
{
  "content": "What is the summary of the quarterly financial report?"
}
```

---

## 📖 OpenAPI / Swagger Documentation

Interactive API documentation is generated automatically:
- **Swagger UI**: `http://localhost:8000/api/docs/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

---

## ⚙️ Installation & Setup

### Prerequisites
- **Python**: 3.10 or higher
- **Node.js**: v18+ & `npm`
- **PostgreSQL**: Version 15+ with `pgvector` extension enabled

---

### 1. Database Setup

Ensure PostgreSQL is running and create the database with vector extension:

```sql
CREATE DATABASE docs_db;
\c docs_db;
CREATE EXTENSION IF NOT EXISTS vector;
```

---

### 2. Backend Setup (Django)

1. Navigate to project root:
   ```bash
   cd docs-search
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install required Python packages:
   ```bash
   pip install django djangorestframework psycopg2-binary pgvector djoser drf-spectacular
   ```

4. Configure database settings in `app/settings.py` (if different from default `localhost:5433`).

5. Run database migrations:
   ```bash
   python manage.py migrate
   ```

6. Start Django development server:
   ```bash
   python manage.py runserver 8000
   ```
   The backend API will be available at `http://localhost:8000/api/v1/`.

---

### 3. Frontend Setup (Vue 3 + Vite)

1. Open a new terminal and navigate to `frontend`:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

4. Access the application in your web browser at:
   ```
   http://localhost:5173
   ```

---

## 🧪 Verification & Building

- **Frontend Type Check & Production Build**:
  ```bash
  cd frontend
  npm run build
  ```
- **Backend Admin Interface**:
  ```bash
  python manage.py createsuperuser
  # Access at http://localhost:8000/admin/
  ```

---

## 📝 License

This project is licensed under the MIT License.
