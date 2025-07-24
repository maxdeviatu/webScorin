from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import uuid


class ScanStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL to scan")
    max_pages: Optional[int] = Field(10, description="Maximum number of pages to crawl")
    include_screenshots: Optional[bool] = Field(True, description="Include screenshots in results")
    include_html: Optional[bool] = Field(True, description="Include HTML content in results")


class ScanResponse(BaseModel):
    scan_id: str = Field(..., description="Unique scan identifier")
    status: ScanStatus = Field(..., description="Current scan status")
    message: str = Field(..., description="Status message")


class ScanResult(BaseModel):
    scan_id: str
    url: str
    status: ScanStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    # Crawling results
    pages_crawled: int = 0
    total_links: int = 0
    external_links: int = 0
    internal_links: int = 0
    
    # Domain information
    domain_info: Optional[Dict[str, Any]] = None
    ip_info: Optional[Dict[str, Any]] = None
    
    # Content analysis
    content_score: Optional[float] = None
    seo_score: Optional[float] = None
    performance_score: Optional[float] = None
    
    # Files
    has_screenshot: bool = False
    has_html_archive: bool = False
    
    # Download links
    screenshot_download_url: Optional[str] = None
    html_archive_download_url: Optional[str] = None
    html_content_url: Optional[str] = None
    
    # Error information
    error_message: Optional[str] = None


class ScanListResponse(BaseModel):
    scans: List[ScanResult]
    total: int 