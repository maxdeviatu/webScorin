import asyncio
import zipfile
import io
import os
from typing import Dict, Any, List, Optional, Set
from urllib.parse import urljoin, urlparse
import tldextract
import validators
from datetime import datetime
import json

from playwright.async_api import async_playwright, Browser, Page
import whois
from ipwhois import IPWhois
import socket


class SiteCrawler:
    def __init__(self, max_pages: int = 10, include_screenshots: bool = True, include_html: bool = True):
        self.max_pages = max_pages
        self.include_screenshots = include_screenshots
        self.include_html = include_html
        self.crawled_urls: Set[str] = set()
        self.all_links: Set[str] = set()
        self.internal_links: Set[str] = set()
        self.external_links: Set[str] = set()
        self.html_content: Dict[str, str] = {}
        self.screenshot_path: Optional[str] = None
        
    async def crawl_site(self, url: str) -> Dict[str, Any]:
        """Main crawling method using Playwright"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Set viewport for consistent screenshots
                await page.set_viewport_size({"width": 1920, "height": 1080})
                
                # Navigate to the main page
                await page.goto(url, wait_until="networkidle")
                
                # Take screenshot if requested
                if self.include_screenshots:
                    self.screenshot_path = f"screenshots/{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    os.makedirs("screenshots", exist_ok=True)
                    await page.screenshot(path=self.screenshot_path, full_page=True)
                
                # Get all links from the page
                links = await self._extract_links(page, url)
                self.all_links.update(links)
                
                # Categorize links
                base_domain = tldextract.extract(url).registered_domain
                for link in links:
                    if tldextract.extract(link).registered_domain == base_domain:
                        self.internal_links.add(link)
                    else:
                        self.external_links.add(link)
                
                # Crawl internal pages (limited by max_pages)
                await self._crawl_internal_pages(page, browser, url, base_domain)
                
                await browser.close()
                
                return self._compile_results(url)
                
        except Exception as e:
            return {"error": str(e)}
    
    async def _extract_links(self, page: Page, base_url: str) -> List[str]:
        """Extract all links from a page"""
        links = await page.eval_on_selector_all("a[href]", """
            (elements) => elements.map(el => el.href).filter(href => href && !href.startsWith('javascript:'))
        """)
        
        # Filter and normalize links
        valid_links = []
        for link in links:
            if validators.url(link):
                valid_links.append(link)
            elif link.startswith('/'):
                valid_links.append(urljoin(base_url, link))
        
        return valid_links
    
    async def _crawl_internal_pages(self, page: Page, browser: Browser, base_url: str, base_domain: str):
        """Crawl internal pages up to max_pages limit"""
        pages_to_crawl = list(self.internal_links)[:self.max_pages - 1]  # -1 for main page
        
        for link in pages_to_crawl:
            if len(self.crawled_urls) >= self.max_pages:
                break
                
            try:
                new_page = await browser.new_page()
                await new_page.goto(link, wait_until="networkidle", timeout=10000)
                
                # Store HTML content if requested
                if self.include_html:
                    html = await new_page.content()
                    self.html_content[link] = html
                
                # Extract more links
                new_links = await self._extract_links(new_page, base_url)
                self.all_links.update(new_links)
                
                # Update link categorization
                for new_link in new_links:
                    if tldextract.extract(new_link).registered_domain == base_domain:
                        self.internal_links.add(new_link)
                    else:
                        self.external_links.add(new_link)
                
                self.crawled_urls.add(link)
                await new_page.close()
                
            except Exception as e:
                print(f"Error crawling {link}: {e}")
                continue
    
    def _compile_results(self, url: str) -> Dict[str, Any]:
        """Compile crawling results"""
        return {
            "url": url,
            "pages_crawled": len(self.crawled_urls) + 1,  # +1 for main page
            "total_links": len(self.all_links),
            "internal_links": len(self.internal_links),
            "external_links": len(self.external_links),
            "crawled_urls": list(self.crawled_urls),
            "screenshot_path": self.screenshot_path,
            "html_content": self.html_content if self.include_html else {},
            "domain_info": self._get_domain_info(url),
            "ip_info": self._get_ip_info(url),
            "content_score": self._calculate_content_score(),
            "seo_score": self._calculate_seo_score(),
            "performance_score": self._calculate_performance_score()
        }
    
    def _get_domain_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get domain registration information"""
        try:
            domain = tldextract.extract(url).registered_domain
            w = whois.whois(domain)
            return {
                "domain": domain,
                "registrar": w.registrar,
                "creation_date": w.creation_date.isoformat() if w.creation_date else None,
                "expiration_date": w.expiration_date.isoformat() if w.expiration_date else None,
                "status": w.status
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_ip_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get IP address information"""
        try:
            domain = tldextract.extract(url).registered_domain
            ip = socket.gethostbyname(domain)
            ipwhois = IPWhois(ip)
            result = ipwhois.lookup_whois()
            return {
                "ip": ip,
                "asn": result.get("asn"),
                "asn_description": result.get("asn_description"),
                "country": result.get("asn_country_code"),
                "org": result.get("org")
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_content_score(self) -> float:
        """Calculate content quality score"""
        # Simple scoring based on number of pages and links
        score = 0.0
        
        # More pages = better content
        score += min(len(self.crawled_urls) / 10.0, 1.0) * 30
        
        # More internal links = better internal structure
        score += min(len(self.internal_links) / 50.0, 1.0) * 40
        
        # Balance between internal and external links
        total_links = len(self.all_links)
        if total_links > 0:
            internal_ratio = len(self.internal_links) / total_links
            score += internal_ratio * 30
        
        return min(score, 100.0)
    
    def _calculate_seo_score(self) -> float:
        """Calculate SEO score"""
        score = 0.0
        
        # More pages = better SEO
        score += min(len(self.crawled_urls) / 10.0, 1.0) * 25
        
        # More total links = better SEO
        score += min(len(self.all_links) / 100.0, 1.0) * 25
        
        # Good balance of internal/external links
        total_links = len(self.all_links)
        if total_links > 0:
            internal_ratio = len(self.internal_links) / total_links
            if 0.3 <= internal_ratio <= 0.7:
                score += 50
            else:
                score += (1 - abs(0.5 - internal_ratio)) * 50
        
        return min(score, 100.0)
    
    def _calculate_performance_score(self) -> float:
        """Calculate performance score (placeholder)"""
        # This would typically include metrics like load time, page size, etc.
        # For now, return a basic score based on content
        return min(self._calculate_content_score() * 0.8, 100.0)
    
    def create_html_archive(self) -> Optional[bytes]:
        """Create a ZIP archive of HTML content"""
        if not self.html_content:
            return None
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for url, html in self.html_content.items():
                # Create a safe filename
                filename = url.replace('://', '_').replace('/', '_').replace(':', '_')
                if len(filename) > 100:
                    filename = filename[:100]
                filename = f"{filename}.html"
                
                zip_file.writestr(filename, html)
        
        return zip_buffer.getvalue() 