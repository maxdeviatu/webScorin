# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Site Scanner is a web scoring and analysis tool built with Python 3.12+, FastAPI, and Playwright. It provides asynchronous web crawling, content analysis, and scoring capabilities using Celery for background task processing.

## Development Commands

### Environment Setup
```bash
make setup              # Complete development environment setup (install deps + playwright)
make install-deps       # Install Python dependencies with Poetry
make install-playwright # Install Playwright chromium browser
```

### Running the Application
```bash
make dev                # Start both API server and Celery worker
make api                # Start only FastAPI server (port 8000)
make worker             # Start only Celery worker
make redis              # Start Redis server (required for Celery)
make redis-stop         # Stop Redis server
```

### Code Quality and Testing
```bash
make lint               # Run ruff linting
make format             # Format code with black
make test               # Run pytest tests
```

### Utilities
```bash
make clean              # Clean temporary files (__pycache__, screenshots, etc.)
make logs               # Show Celery logs
make help               # Show all available commands
```

## Architecture

### Core Components

1. **FastAPI Application** (`app/api.py`)
   - RESTful API endpoints for scan operations
   - Handles file downloads (screenshots, HTML archives)
   - CORS enabled for frontend integration

2. **Background Task Processing** (`app/tasks.py`)
   - Celery-based asynchronous processing
   - In-memory scan result storage (production should use database)
   - Task progress tracking and status updates

3. **Web Crawler** (`app/crawler.py`)
   - Playwright-based headless browser automation
   - Extracts links, takes screenshots, collects HTML content
   - Generates content, SEO, and performance scores
   - Domain and IP information lookup

4. **Data Models** (`app/models.py`)
   - Pydantic models for request/response validation
   - ScanStatus enum for tracking scan states
   - Structured data models for scan results

### Key Dependencies
- **FastAPI**: Web framework and API documentation
- **Celery + Redis**: Asynchronous task queue and message broker
- **Playwright**: Browser automation and JavaScript rendering
- **Poetry**: Dependency management and virtual environment

### API Endpoints
- `POST /scan` - Submit new scan request
- `GET /scan/{scan_id}` - Get scan status/results
- `GET /scan/{scan_id}/screenshot` - Download screenshot
- `GET /scan/{scan_id}/html` - Download HTML archive
- `GET /scans` - List all scans
- `DELETE /scan/{scan_id}` - Delete scan

### File Structure
```
app/
├── api.py              # FastAPI endpoints and middleware
├── tasks.py            # Celery background tasks
├── crawler.py          # Playwright web crawling logic
└── models.py           # Pydantic data models
```

## Development Notes

### Testing
- Uses pytest with async support (`pytest-asyncio`)
- Coverage reporting configured in pyproject.toml
- Test paths: `tests/` directory

### Code Quality
- **Ruff**: Python linting with comprehensive rule set
- **Black**: Code formatting (line length: 88)
- Target Python version: 3.12

### Docker Support
- Dockerfile available for containerization
- docker-compose.yml for Redis integration

### Environment Variables
Create `.env` file for configuration:
```env
REDIS_URL=redis://localhost:6379/0
API_HOST=0.0.0.0
API_PORT=8000
MAX_PAGES=10
DEFAULT_TIMEOUT=30000
```

## Important Implementation Details

- Scan results are stored in-memory (`scan_results` dict in tasks.py) - replace with database for production
- Screenshots saved to `screenshots/` directory
- HTML archives created as ZIP files in memory
- Celery tasks have 30-minute timeout limit
- Browser viewport set to 1920x1080 for consistent screenshots