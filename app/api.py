import uuid
import os
import zipfile
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .models import (
    ScanRequest, ScanResponse, ScanResult, ScanListResponse, ScanStatus
)
from .tasks import scan_site, get_scan_result, get_all_scans, delete_scan

# Get base URL from environment
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Initialize FastAPI app
app = FastAPI(
    title="Site Scanner API",
    description="Web scoring and site analysis tool",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def enrich_scan_result_with_download_links(scan_result: ScanResult) -> ScanResult:
    """Add download links to scan result if files are available"""
    if scan_result.status == ScanStatus.COMPLETED:
        if scan_result.has_screenshot:
            scan_result.screenshot_download_url = f"{BASE_URL}/scan/{scan_result.scan_id}/screenshot"
        if scan_result.has_html_archive:
            scan_result.html_archive_download_url = f"{BASE_URL}/scan/{scan_result.scan_id}/html"
            scan_result.html_content_url = f"{BASE_URL}/scan/{scan_result.scan_id}/html-content"
    return scan_result


def create_html_archive(html_content: Dict[str, str]) -> Optional[bytes]:
    """Create a ZIP archive from HTML content dictionary"""
    if not html_content:
        return None
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for url, html in html_content.items():
            # Create a safe filename
            filename = url.replace('://', '_').replace('/', '_').replace(':', '_')
            if len(filename) > 100:
                filename = filename[:100]
            filename = f"{filename}.html"
            
            zip_file.writestr(filename, html)
    
    return zip_buffer.getvalue()


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Site Scanner API",
        "version": "1.0.0",
        "endpoints": {
            "POST /scan": "Submit a new scan request",
            "GET /scan/{id}": "Get scan result or status",
            "GET /scan/{id}/html": "Download HTML archive",
            "GET /scan/{id}/html-content": "Get HTML content as JSON",
            "GET /scan/{id}/screenshot": "Download screenshot",
            "GET /scans": "List all scans",
            "DELETE /scan/{id}": "Delete a scan"
        }
    }


@app.post("/scan", response_model=ScanResponse)
async def create_scan(scan_request: ScanRequest, background_tasks: BackgroundTasks):
    """Submit a new scan request"""
    try:
        # Generate unique scan ID
        scan_id = str(uuid.uuid4())
        
        # Create initial scan result
        scan_result = ScanResult(
            scan_id=scan_id,
            url=str(scan_request.url),
            status=ScanStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        # Start background task
        task = scan_site.delay(
            scan_id=scan_id,
            url=str(scan_request.url),
            max_pages=scan_request.max_pages,
            include_screenshots=scan_request.include_screenshots,
            include_html=scan_request.include_html
        )
        
        return ScanResponse(
            scan_id=scan_id,
            status=ScanStatus.PENDING,
            message="Scan request submitted successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create scan: {str(e)}")


@app.get("/scan/{scan_id}", response_model=ScanResult)
async def get_scan(scan_id: str):
    """Get scan result or status"""
    scan_result = get_scan_result(scan_id)
    
    if not scan_result:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Enrich with download links
    return enrich_scan_result_with_download_links(scan_result)


@app.get("/scan/{scan_id}/html")
async def download_html(scan_id: str):
    """Download HTML archive as ZIP file"""
    scan_result = get_scan_result(scan_id)
    
    if not scan_result:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if scan_result.status != ScanStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Scan not completed yet")
    
    if not hasattr(scan_result, '_crawler_data') or not scan_result._crawler_data.get("html_content"):
        raise HTTPException(status_code=404, detail="HTML content not available")
    
    try:
        # Create HTML archive from stored data
        html_archive = create_html_archive(scan_result._crawler_data["html_content"])
        
        if not html_archive:
            raise HTTPException(status_code=404, detail="HTML archive could not be created")
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(html_archive),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=scan_{scan_id}_html.zip"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create HTML archive: {str(e)}")


@app.get("/scan/{scan_id}/screenshot")
async def download_screenshot(scan_id: str):
    """Download screenshot image"""
    scan_result = get_scan_result(scan_id)
    
    if not scan_result:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if scan_result.status != ScanStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Scan not completed yet")
    
    if not hasattr(scan_result, '_crawler_data') or not scan_result._crawler_data.get("screenshot_path"):
        raise HTTPException(status_code=404, detail="Screenshot not available")
    
    screenshot_path = scan_result._crawler_data["screenshot_path"]
    
    if not os.path.exists(screenshot_path):
        raise HTTPException(status_code=404, detail="Screenshot file not found")
    
    return FileResponse(
        screenshot_path,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename=scan_{scan_id}_screenshot.png"}
    )


@app.get("/scan/{scan_id}/html-content")
async def get_html_content(scan_id: str):
    """Get HTML content as JSON for easy consumption"""
    scan_result = get_scan_result(scan_id)
    
    if not scan_result:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if scan_result.status != ScanStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Scan not completed yet")
    
    if not hasattr(scan_result, '_crawler_data') or not scan_result._crawler_data.get("html_content"):
        raise HTTPException(status_code=404, detail="HTML content not available")
    
    html_content = scan_result._crawler_data["html_content"]
    
    return {
        "scan_id": scan_id,
        "url": scan_result.url,
        "pages_count": len(html_content),
        "html_content": html_content,
        "crawled_at": scan_result.completed_at.isoformat() if scan_result.completed_at else None
    }


@app.get("/scans", response_model=ScanListResponse)
async def list_scans():
    """List all scans"""
    scans = get_all_scans()
    # Enrich each scan with download links
    enriched_scans = [enrich_scan_result_with_download_links(scan) for scan in scans]
    return ScanListResponse(scans=enriched_scans, total=len(enriched_scans))


@app.delete("/scan/{scan_id}")
async def delete_scan_endpoint(scan_id: str):
    """Delete a scan"""
    success = delete_scan(scan_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return {"message": "Scan deleted successfully"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Import datetime at the top level
from datetime import datetime 