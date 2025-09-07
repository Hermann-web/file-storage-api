# Simple File Storage API

A lightweight FastAPI-based file storage service with UUID-based file management and SQLite database storage.

## 🚀 Features

- **Simple Upload**: Single endpoint to upload files with email and label
- **UUID Security**: Public/private UUID system for secure file access
- **Proper MIME Types**: Automatic content type detection and proper HTTP headers
- **SQLite Database**: Lightweight database for metadata storage
- **Path Safety**: Modern pathlib usage for cross-platform compatibility
- **File Management**: Upload, download, info retrieval, and deletion endpoints

## 📁 Project Structure

```
simple-file-storage/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── files/              # Upload directory (auto-created)
├── files.db            # SQLite database (auto-created)
├── README.md           # This file
└── deploy.md           # Deployment guide
```

## 🛠️ API Endpoints

### Upload File
```http
POST /api/upload
Content-Type: multipart/form-data

email: user@example.com
label: s5Transcripts
file: [file data]
```

### Download File
```http
GET /download/{public_id}
```

### File Information
```http
GET /api/file-info/{public_id}
```

### Delete File
```http
DELETE /api/file/{public_id}
```

### Health Check
```http
GET /health
```

## 💾 Database Schema

```sql
files:
├── public_id (PRIMARY KEY)     # UUID for public access
├── private_id                  # UUID for server filename
├── email                       # User email
├── label                       # File label (e.g., "s5Transcripts")
├── original_filename           # Original filename
├── file_extension             # File extension (.pdf, .docx, etc.)
├── content_type               # MIME type
├── file_size                  # File size in bytes
└── created_at                 # Timestamp
```

## 🔧 Local Development

### Prerequisites
- Python 3.8+
- pip or uv (recommended)

### Quick Start with uv (Recommended)

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone and setup**:
   ```bash
   git clone <your-repo>
   cd simple-file-storage
   ```

3. **Install dependencies**:
   ```bash
   uv pip install -r requirements.txt
   ```

4. **Run development server**:
   ```bash
   uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Alternative: Traditional pip

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run development server**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### With micromamba (as mentioned)

```bash
micromamba run uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🌐 Access the API

- **API Base**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc

## 📝 Usage Examples

### cURL Examples

**Upload a file**:
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "email=student@etu.univh2c.ma" \
  -F "label=resume" \
  -F "file=@resume.pdf"
```

**Download a file**:
```bash
curl -O -J "http://localhost:8000/download/{public_id}"
```

**Get file info**:
```bash
curl "http://localhost:8000/api/file-info/{public_id}"
```

### JavaScript/TypeScript Integration

```typescript
// Upload file
const formData = new FormData();
formData.append('email', 'user@etu.univh2c.ma');
formData.append('label', 's5Transcripts');
formData.append('file', fileInput.files[0]);

const response = await fetch('/api/upload', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('File URL:', result.public_url);
```

## 🔒 Security Notes

- Files are stored with UUID-based filenames to prevent direct access
- Public IDs are required to download files
- CORS is configured for development (adjust for production)
- No authentication implemented (add as needed)

## 📂 File Storage

- Files are stored in the `files/` directory
- Filenames use private UUIDs with original extensions
- Directory is created automatically on startup
- File metadata is stored in SQLite database

## ⚡ Performance Considerations

- SQLite is suitable for development and small-scale production
- For high-volume production, consider PostgreSQL
- File storage is local (consider cloud storage for production)
- No file size limits implemented (add as needed)

## 🐛 Troubleshooting

**Port already in use**:
```bash
# Change port
uvicorn main:app --port 8001
```

**Permission errors on files/ directory**:
```bash
chmod 755 files/
```

**Database locked error**:
- Ensure no other instances are running
- Delete `files.db` to reset (loses all data)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details