# Site Scanner - Web Scoring and Analysis Tool

A modern web application for analyzing websites, generating scores, and providing detailed insights about web content, SEO, and performance.

## Features

- 🌐 **Web Crawling**: Advanced crawling with Playwright for JavaScript-rendered content
- 📊 **Scoring System**: Content quality, SEO, and performance scoring
- 📸 **Screenshots**: Automatic homepage screenshots
- 📁 **HTML Archive**: Downloadable ZIP archives of crawled content
- 🔍 **Domain Analysis**: WHOIS and IP information lookup
- ⚡ **Async Processing**: Background task processing with Celery
- 🚀 **Fast API**: Modern FastAPI with automatic documentation

## Tech Stack

- **Python 3.12+**: Modern Python with type hints
- **FastAPI**: High-performance web framework
- **Playwright**: Browser automation for JavaScript rendering
- **Celery**: Asynchronous task queue
- **Redis**: Message broker and result backend
- **Poetry**: Dependency management
- **Pydantic**: Data validation and serialization

## Quick Start

### Prerequisites

- Python 3.12 or newer
- Redis server
- Poetry (for dependency management)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd webScoring
   ```

2. **Setup development environment**
   ```bash
   # Create virtual environment and install dependencies
   make setup
   
   # Or manually:
   python3 -m venv .venv
   source .venv/bin/activate
   pip install poetry
   poetry install
   poetry run playwright install chromium
   ```

3. **Start Redis**
   ```bash
   make redis
   # Or manually: redis-server
   ```

4. **Run the application**
   ```bash
   # Start both API and worker
   make dev
   
   # Or start separately:
   make api    # Terminal 1
   make worker # Terminal 2
   ```

5. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc
   - Health check: http://localhost:8000/health

## API Endpoints

### Submit a Scan
```bash
POST /scan
Content-Type: application/json

{
  "url": "https://example.com",
  "max_pages": 10,
  "include_screenshots": true,
  "include_html": true
}
```

### Get Scan Status
```bash
GET /scan/{scan_id}
```

### Download Files
```bash
# Download HTML archive
GET /scan/{scan_id}/html

# Download screenshot
GET /scan/{scan_id}/screenshot
```

### List All Scans
```bash
GET /scans
```

### Delete Scan
```bash
DELETE /scan/{scan_id}
```

## Usage Examples

### Using curl

1. **Submit a scan request**
   ```bash
   curl -X POST "http://localhost:8000/scan" \
        -H "Content-Type: application/json" \
        -d '{
          "url": "https://example.com",
          "max_pages": 5,
          "include_screenshots": true,
          "include_html": true
        }'
   ```

2. **Check scan status**
   ```bash
   curl "http://localhost:8000/scan/{scan_id}"
   ```

3. **Download screenshot**
   ```bash
   curl -O "http://localhost:8000/scan/{scan_id}/screenshot"
   ```

### Using Python

```python
import requests

# Submit scan
response = requests.post("http://localhost:8000/scan", json={
    "url": "https://example.com",
    "max_pages": 10
})
scan_id = response.json()["scan_id"]

# Check status
status = requests.get(f"http://localhost:8000/scan/{scan_id}")
print(status.json())

# Download files when completed
if status.json()["status"] == "completed":
    # Download screenshot
    screenshot = requests.get(f"http://localhost:8000/scan/{scan_id}/screenshot")
    with open("screenshot.png", "wb") as f:
        f.write(screenshot.content)
    
    # Download HTML archive
    html_archive = requests.get(f"http://localhost:8000/scan/{scan_id}/html")
    with open("html_archive.zip", "wb") as f:
        f.write(html_archive.content)
```

## Development

### Available Commands

```bash
make help          # Show all available commands
make dev           # Start API and worker
make api           # Start only API server
make worker        # Start only Celery worker
make lint          # Run code linting
make format        # Format code
make test          # Run tests
make clean         # Clean temporary files
```

### Code Quality

The project uses:
- **Ruff**: Fast Python linter
- **Black**: Code formatter
- **Pre-commit**: Git hooks for code quality

```bash
# Format code
make format

# Check code quality
make lint

# Install pre-commit hooks
poetry run pre-commit install
```

### Testing

```bash
# Run tests
make test

# Run with coverage
poetry run pytest --cov=app
```

## Configuration

### Environment Variables

Create a `.env` file for configuration:

```env
# Redis configuration
REDIS_URL=redis://localhost:6379/0

# API configuration
API_HOST=0.0.0.0
API_PORT=8000

# Crawler configuration
MAX_PAGES=10
DEFAULT_TIMEOUT=30000
```

### Celery Configuration

Celery is configured in `app/tasks.py` with:
- Redis as broker and result backend
- 30-minute task timeout
- Progress tracking enabled

## Project Structure

```
site_scanner/
├── app/
│   ├── __init__.py
│   ├── api.py              # FastAPI endpoints
│   ├── crawler.py          # Web crawling logic
│   ├── tasks.py            # Celery background tasks
│   └── models.py           # Pydantic models
├── screenshots/            # Generated screenshots
├── .venv/                  # Virtual environment
├── pyproject.toml          # Poetry configuration
├── Makefile               # Development commands
├── Dockerfile             # Container configuration
└── README.md              # This file
```

## Deployment

### Docker

```bash
# Build image
docker build -t site-scanner .

# Run with Redis
docker-compose up -d
```

### Production

For production deployment:

1. Use a proper database (PostgreSQL, MongoDB)
2. Configure Redis for persistence
3. Set up monitoring (Prometheus, Grafana)
4. Use a reverse proxy (Nginx)
5. Configure SSL certificates
6. Set up logging and error tracking

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Create an issue on GitHub
- Check the API documentation at `/docs`
- Review the logs for debugging information 