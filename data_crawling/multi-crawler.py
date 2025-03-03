import argparse
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress only the specific InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("web_crawler")

# Default configuration
DEFAULT_CONFIG = {
    "headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    },
    "image_min_size_kb": 10,
    "excluded_image_patterns": [".gif", "logo", "icon", "banner", "button"],
    "request_timeout": 30,
    "rate_limit_delay": 2.0,  # seconds between requests
    "output_dir": "crawled_data",
}


def sanitize_filename(url: str) -> str:
    """
    Creates a safe filename from a URL.

    Args:
        url: URL to sanitize

    Returns:
        Safe filename string
    """
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    if not path:
        return parsed.netloc
    # Replace slashes and other invalid characters
    safe_name = path.replace('/', '_').replace('\\', '_')
    # Remove file extensions if present
    if '.' in safe_name:
        parts = safe_name.split('.')
        if parts[-1].lower() in ['html', 'htm', 'php', 'asp']:
            safe_name = '.'.join(parts[:-1])
    return safe_name


def fetch_page(url: str, config: Dict = None) -> Optional[BeautifulSoup]:
    """
    Fetches a web page and returns a BeautifulSoup object.

    Args:
        url: URL to fetch
        config: Configuration dictionary

    Returns:
        BeautifulSoup object or None if the request failed
    """
    if config is None:
        config = DEFAULT_CONFIG

    try:
        logger.info(f"Fetching URL: {url}")
        response = requests.get(
            url,
            headers=config["headers"],
            verify=False,
            timeout=config["request_timeout"]
        )
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch URL: {url}. Error: {e}")
        return None


def clean_html(soup: BeautifulSoup) -> BeautifulSoup:
    """
    Removes unwanted elements from the HTML.

    Args:
        soup: BeautifulSoup object

    Returns:
        Cleaned BeautifulSoup object
    """
    # Define selectors for unwanted elements
    unwanted_selectors = [
        "footer",
        "footer.footer-area",
        ".single-blog-post",
        ".post-thumbnail",
        "nav",
        ".navigation",
        ".sidebar",
        ".ads",
        ".advertisement",
        "script",
        "style",
        ".cookie-notice",
        "#comments",
        ".social-media",
        ".breadcrumbs",
        ".site-header",
        ".menu",
    ]

    # Remove unwanted elements
    for selector in unwanted_selectors:
        for element in soup.select(selector):
            element.decompose()

    return soup


def should_keep_image(img_url: str, config: Dict) -> bool:
    """
    Determines if an image should be kept based on filters.

    Args:
        img_url: Image URL
        config: Configuration dictionary

    Returns:
        Boolean indicating whether to keep the image
    """
    if img_url == "https://hus.vnu.edu.vn/DATA/VIDEO/2019/07/cuu-sinhvien.jpg":
        return False
    # Skip images matching excluded patterns
    if any(pattern in img_url.lower() for pattern in config["excluded_image_patterns"]):
        return False

    # Skip images with invalid or empty URLs
    if not img_url or img_url.startswith("data:"):
        return False

    return True


def check_image_size(img_url: str, config: Dict) -> bool:
    """
    Checks if an image meets the minimum size requirements.

    Args:
        img_url: Image URL
        config: Configuration dictionary

    Returns:
        Boolean indicating whether the image meets size requirements
    """
    try:
        headers = {**config["headers"], "Range": "bytes=0-1024"}
        response = requests.head(
            img_url,
            headers=headers,
            verify=False,
            timeout=config["request_timeout"]
        )

        if "content-length" in response.headers:
            size_kb = int(response.headers["content-length"]) / 1024
            return size_kb >= config["image_min_size_kb"]
        return False
    except requests.exceptions.RequestException as e:
        logger.debug(f"Could not check image size for {img_url}: {e}")
        return False


def extract_content(soup: BeautifulSoup, base_url: str, config: Dict) -> Tuple[List[str], List[str]]:
    """
    Extracts content from HTML.

    Args:
        soup: BeautifulSoup object
        base_url: Base URL for resolving relative links
        config: Configuration dictionary

    Returns:
        Tuple of (content_list, image_urls)
    """
    body = soup.body
    content_list = []
    image_urls = []

    if not body:
        logger.warning("No body element found in HTML")
        return content_list, image_urls

    elements = body.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "table", "img"], recursive=True)

    for element in elements:
        # Process based on element type
        if element.name.startswith('h1') and len(element.name) == 2:
            text = element.get_text(strip=True)
            if text:
                content_list.append(f"Tiêu đề: {text}\n")

        elif element.name == "p":
            # Skip paragraphs inside tables
            if not element.find_parent("table"):
                text = element.get_text(strip=True)
                if text:
                    content_list.append(f"{text}\n")

        elif element.name == "table":
            content_list.append('\n')
            table_data = []

            for row in element.find_all("tr"):
                cells = [cell.get_text(strip=True) for cell in row.find_all(["td", "th"])]
                if any(cells):  # Skip empty rows
                    table_data.append("\t".join(cells))

            if table_data:
                content_list.append("\n".join(table_data) + "\n")

        elif element.name == "img" and element.get("src"):
            # Process image
            img_url = element.get("src")

            # Handle relative URLs
            if not img_url.startswith(('http://', 'https://')):
                img_url = urljoin(base_url, img_url)

            if should_keep_image(img_url, config) and check_image_size(img_url, config):
                content_list.append(f"🖼️ Ảnh: {img_url}\n")
                image_urls.append(img_url)

    return content_list, image_urls


def download_images(image_urls: List[str], output_dir: str, config: Dict) -> List[str]:
    """
    Downloads images from URLs.

    Args:
        image_urls: List of image URLs
        output_dir: Directory to save images
        config: Configuration dictionary

    Returns:
        List of paths to downloaded images
    """
    # Create directory if it doesn't exist
    img_dir = Path(output_dir)
    img_dir.mkdir(parents=True, exist_ok=True)

    downloaded_paths = []

    for i, img_url in enumerate(image_urls):
        # Rate limiting
        if i > 0:
            time.sleep(config["rate_limit_delay"])

        try:
            response = requests.get(
                img_url,
                headers=config["headers"],
                verify=False,
                timeout=config["request_timeout"]
            )
            response.raise_for_status()

            # Determine file extension from Content-Type or URL
            if "content-type" in response.headers and "image" in response.headers["content-type"]:
                ext = response.headers["content-type"].split("/")[-1].split(";")[0]
                if ext == "jpeg":
                    ext = "jpg"
            else:
                ext = img_url.split(".")[-1].lower()
                if ext not in ["jpg", "jpeg", "png", "gif", "webp", "svg"]:
                    ext = "jpg"

            # Save image with sequential numbering
            img_path = img_dir / f"image_{i + 1}.{ext}"
            with open(img_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Downloaded image: {img_url} → {img_path}")
            downloaded_paths.append(str(img_path))

        except Exception as e:
            logger.error(f"Failed to download image {img_url}: {e}")

    return downloaded_paths


def save_content(content_list: List[str], output_file: str) -> None:
    """
    Saves extracted content to a file.

    Args:
        content_list: List of content strings
        output_file: Path to output file
    """
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("".join(content_list))
        logger.info(f"Content saved to {output_file}")
    except IOError as e:
        logger.error(f"Failed to save content to {output_file}: {e}")


def save_metadata(url: str, title: str, content_file: str, image_files: List[str], metadata_file: str) -> None:
    """
    Saves metadata about the crawled page.

    Args:
        url: URL that was crawled
        title: Page title
        content_file: Path to content file
        image_files: List of paths to image files
        metadata_file: Path to metadata file
    """
    metadata = {
        "url": url,
        "title": title,
        "crawl_date": datetime.now().isoformat(),
        "content_file": content_file,
        "image_files": image_files
    }

    try:
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        logger.info(f"Metadata saved to {metadata_file}")
    except IOError as e:
        logger.error(f"Failed to save metadata to {metadata_file}: {e}")


def crawl_url(url: str, config: Dict) -> bool:
    """
    Crawls a single URL and saves the content.

    Args:
        url: URL to crawl
        config: Configuration dictionary

    Returns:
        Boolean indicating success
    """
    try:
        # Fetch and parse page
        soup = fetch_page(url, config)
        if not soup:
            logger.error(f"Failed to fetch page: {url}")
            return False

        # Get page title
        title_tag = soup.find('title')
        page_title = title_tag.get_text(strip=True) if title_tag else "Untitled Page"

        # Create safe filename from URL
        page_id = sanitize_filename(url)

        # Create output directories
        output_base = Path(config["output_dir"])
        page_dir = output_base / page_id
        page_dir.mkdir(parents=True, exist_ok=True)

        # Clean HTML
        soup = clean_html(soup)

        # Extract content
        content_list, image_urls = extract_content(soup, url, config)

        # Ensure we have content
        if not content_list:
            logger.warning(f"No content extracted from {url}")
            content_list = ["Không tìm thấy nội dung.\n"]

        # Save content
        content_file = page_dir / "content.txt"
        save_content(content_list, str(content_file))

        # Download images
        img_dir = page_dir / "images"
        image_files = download_images(image_urls, str(img_dir), config)

        # Save metadata
        metadata_file = page_dir / "metadata.json"
        save_metadata(url, page_title, str(content_file), image_files, str(metadata_file))

        logger.info(f"✅ Successfully crawled: {url}")
        return True

    except Exception as e:
        logger.error(f"Error crawling {url}: {e}", exc_info=True)
        return False


def read_urls_from_file(file_path: str) -> List[str]:
    """
    Reads URLs from a file.

    Args:
        file_path: Path to file containing URLs (one per line)

    Returns:
        List of URLs
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    except IOError as e:
        logger.error(f"Failed to read URLs from {file_path}: {e}")
        return []


def main():
    """Main function to run the web crawler."""
    parser = argparse.ArgumentParser(description="Multi-URL Web Crawler")
    parser.add_argument("--urls", type=str, nargs='+',
                        help="URLs to crawl")
    parser.add_argument("--urls-file", type=str,
                        help="File containing URLs to crawl (one per line)")
    parser.add_argument("--output-dir", type=str, default="crawled_data",
                        help="Directory to save crawled data")
    parser.add_argument("--min-img-size", type=int, default=10,
                        help="Minimum image size in KB")
    parser.add_argument("--timeout", type=int, default=30,
                        help="Request timeout in seconds")
    parser.add_argument("--delay", type=float, default=2.0,
                        help="Delay between requests in seconds")

    args = parser.parse_args()

    # Configure crawler
    config = DEFAULT_CONFIG.copy()
    config["image_min_size_kb"] = args.min_img_size
    config["request_timeout"] = args.timeout
    config["rate_limit_delay"] = args.delay
    config["output_dir"] = args.output_dir

    # Get URLs to crawl
    urls_to_crawl = []
    if args.urls:
        urls_to_crawl.extend(args.urls)
    if args.urls_file:
        urls_to_crawl.extend(read_urls_from_file(args.urls_file))

    # If no URLs provided, use default examples

    if not urls_to_crawl:
        urls_to_crawl = [
            "https://hus.vnu.edu.vn/gioi-thieu/co-cau-to-chuc/du-an-va-cong-ty.html",
            "https://hus.vnu.edu.vn/gioi-thieu/co-cau-to-chuc/phong-ban-chuc-nang.html",
        ]

    # Create output directory
    Path(config["output_dir"]).mkdir(parents=True, exist_ok=True)

    # Crawl each URL
    success_count = 0
    for url in urls_to_crawl:
        if crawl_url(url, config):
            success_count += 1
        # Add delay between crawls
        if url != urls_to_crawl[-1]:  # Don't delay after the last URL
            time.sleep(config["rate_limit_delay"])

    # Summary
    logger.info(f"Crawl completed. Successfully crawled {success_count}/{len(urls_to_crawl)} URLs.")
    logger.info(f"Results saved to {os.path.abspath(config['output_dir'])}")

    return 0 if success_count == len(urls_to_crawl) else 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)