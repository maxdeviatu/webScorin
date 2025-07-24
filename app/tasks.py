import os
import json
from datetime import datetime
from typing import Dict, Any
from celery import Celery
from .crawler import SiteCrawler
from .models import ScanStatus, ScanResult

# Initialize Celery
celery_app = Celery(
    "site_scanner",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Redis storage for scan results
import json
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)


@celery_app.task(bind=True)
def scan_site(self, scan_id: str, url: str, max_pages: int = 10, 
              include_screenshots: bool = True, include_html: bool = True) -> Dict[str, Any]:
    """
    Background task to scan a website
    """
    try:
        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Starting scan..."}
        )
        
        # Initialize scan result
        scan_result = ScanResult(
            scan_id=scan_id,
            url=url,
            status=ScanStatus.PROCESSING,
            created_at=datetime.utcnow()
        )
        # Store in Redis
        scan_dict = scan_result.model_dump()
        scan_dict['created_at'] = scan_dict['created_at'].isoformat()
        redis_client.setex(f"scan:{scan_id}", 3600, json.dumps(scan_dict))
        
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 10, "total": 100, "status": "Initializing crawler..."}
        )
        
        # Create crawler and perform scan
        crawler = SiteCrawler(
            max_pages=max_pages,
            include_screenshots=include_screenshots,
            include_html=include_html
        )
        
        self.update_state(
            state="PROGRESS",
            meta={"current": 20, "total": 100, "status": "Crawling website..."}
        )
        
        # Run the crawler (this is async, so we need to handle it properly)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            crawl_results = loop.run_until_complete(crawler.crawl_site(url))
        finally:
            loop.close()
        
        self.update_state(
            state="PROGRESS",
            meta={"current": 80, "total": 100, "status": "Processing results..."}
        )
        
        # Check for errors
        if "error" in crawl_results:
            scan_result.status = ScanStatus.FAILED
            scan_result.error_message = crawl_results["error"]
            scan_result.completed_at = datetime.utcnow()
            scan_dict = scan_result.model_dump()
            scan_dict['created_at'] = scan_dict['created_at'].isoformat()
            scan_dict['completed_at'] = scan_dict['completed_at'].isoformat()
            redis_client.setex(f"scan:{scan_id}", 3600, json.dumps(scan_dict))
            
            return {
                "status": "FAILED",
                "error": crawl_results["error"]
            }
        
        # Update scan result with crawl data
        scan_result.status = ScanStatus.COMPLETED
        scan_result.completed_at = datetime.utcnow()
        scan_result.pages_crawled = crawl_results.get("pages_crawled", 0)
        scan_result.total_links = crawl_results.get("total_links", 0)
        scan_result.internal_links = crawl_results.get("internal_links", 0)
        scan_result.external_links = crawl_results.get("external_links", 0)
        scan_result.domain_info = crawl_results.get("domain_info")
        scan_result.ip_info = crawl_results.get("ip_info")
        scan_result.content_score = crawl_results.get("content_score")
        scan_result.seo_score = crawl_results.get("seo_score")
        scan_result.performance_score = crawl_results.get("performance_score")
        scan_result.has_screenshot = bool(crawl_results.get("screenshot_path"))
        scan_result.has_html_archive = bool(crawl_results.get("html_content"))
        
        # Store additional data for file downloads
        scan_result._crawler_data = {
            "screenshot_path": crawl_results.get("screenshot_path"),
            "html_content": crawl_results.get("html_content", {}),
            "crawler": crawler
        }
        
        scan_dict = scan_result.model_dump()
        scan_dict['created_at'] = scan_dict['created_at'].isoformat()
        scan_dict['completed_at'] = scan_dict['completed_at'].isoformat()
        redis_client.setex(f"scan:{scan_id}", 3600, json.dumps(scan_dict))
        # Store crawler data separately
        redis_client.setex(f"crawler_data:{scan_id}", 3600, json.dumps({
            "screenshot_path": crawl_results.get("screenshot_path"),
            "html_content": crawl_results.get("html_content", {})
        }))
        
        self.update_state(
            state="SUCCESS",
            meta={"current": 100, "total": 100, "status": "Scan completed successfully"}
        )
        
        return {
            "status": "SUCCESS",
            "scan_id": scan_id,
            "message": "Scan completed successfully"
        }
        
    except Exception as e:
        # Update scan result with error
        scan_data = redis_client.get(f"scan:{scan_id}")
        if scan_data:
            scan_result = ScanResult(**json.loads(scan_data))
            scan_result.status = ScanStatus.FAILED
            scan_result.error_message = str(e)
            scan_result.completed_at = datetime.utcnow()
            scan_dict = scan_result.model_dump()
            scan_dict['created_at'] = scan_dict['created_at'].isoformat()
            scan_dict['completed_at'] = scan_dict['completed_at'].isoformat()
            redis_client.setex(f"scan:{scan_id}", 3600, json.dumps(scan_dict))
        
        return {
            "status": "FAILED",
            "error": str(e)
        }


def get_scan_result(scan_id: str) -> ScanResult:
    """Get scan result by ID"""
    scan_data = redis_client.get(f"scan:{scan_id}")
    if scan_data:
        scan_result = ScanResult(**json.loads(scan_data))
        # Load crawler data if available
        crawler_data = redis_client.get(f"crawler_data:{scan_id}")
        if crawler_data:
            scan_result._crawler_data = json.loads(crawler_data)
        return scan_result
    return None


def get_all_scans() -> list[ScanResult]:
    """Get all scan results"""
    scans = []
    for key in redis_client.keys("scan:*"):
        scan_data = redis_client.get(key)
        if scan_data:
            scans.append(ScanResult(**json.loads(scan_data)))
    return scans


def delete_scan(scan_id: str) -> bool:
    """Delete a scan result"""
    scan_key = f"scan:{scan_id}"
    crawler_key = f"crawler_data:{scan_id}"
    if redis_client.exists(scan_key):
        redis_client.delete(scan_key)
        redis_client.delete(crawler_key)
        return True
    return False 