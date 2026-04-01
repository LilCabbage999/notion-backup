import time
import os
import hashlib
import logging
from typing import Optional
import requests

from notion_client import Client

logger = logging.getLogger(__name__)


class NotionClientWrapper:
    def __init__(self, token: str):
        self.client = Client(auth=token)
        self._verify_token()

    def _verify_token(self):
        try:
            self.client.users.me()
            logger.info("Notion token verified successfully")
        except Exception as e:
            raise ValueError(f"Invalid Notion token: {e}") from e

    def _request_with_retry(self, func, max_retries: int = 3, delay: int = 5):
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                error_msg = str(e)
                if "rate_limited" in error_msg or "429" in error_msg:
                    retry_after = delay * (attempt + 1)
                    logger.warning(f"Rate limited, waiting {retry_after}s before retry (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_after)
                elif attempt < max_retries - 1:
                    logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(delay)
                else:
                    raise
        return None

    def search_all_pages(self):
        logger.info("Searching for all accessible pages...")
        all_pages = []
        has_more = True
        start_cursor = None

        while has_more:
            def _search():
                params = {
                    "filter": {"property": "object", "value": "page"},
                    "page_size": 100,
                }
                if start_cursor:
                    params["start_cursor"] = start_cursor
                return self.client.search(**params)

            response = self._request_with_retry(_search)
            if not response:
                break

            results = response.get("results", [])
            all_pages.extend(results)
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")

            logger.info(f"Fetched {len(results)} pages (total: {len(all_pages)})")

        logger.info(f"Total pages found: {len(all_pages)}")
        return all_pages

    def get_page(self, page_id: str):
        def _get():
            return self.client.pages.retrieve(page_id=page_id)
        return self._request_with_retry(_get)

    def get_block_children(self, block_id: str):
        all_blocks = []
        has_more = True
        start_cursor = None

        while has_more:
            def _get_children():
                params = {"block_id": block_id, "page_size": 100}
                if start_cursor:
                    params["start_cursor"] = start_cursor
                return self.client.blocks.children.list(**params)

            response = self._request_with_retry(_get_children)
            if not response:
                break

            results = response.get("results", [])
            all_blocks.extend(results)
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")

        return all_blocks

    def get_page_title(self, page: dict) -> str:
        properties = page.get("properties", {})
        for key, value in properties.items():
            if value.get("type") == "title":
                title_parts = value.get("title", [])
                return "".join(part.get("plain_text", "") for part in title_parts)
        return "Untitled"

    def get_page_metadata(self, page: dict) -> dict:
        return {
            "id": page.get("id", ""),
            "title": self.get_page_title(page),
            "created_time": page.get("created_time", ""),
            "last_edited_time": page.get("last_edited_time", ""),
            "url": page.get("url", ""),
        }

    def download_image(self, url: str, attachments_dir: str) -> str:
        if not url:
            return url
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            content = response.content
            ext = self._get_image_extension(response.headers.get("content-type", ""))
            
            filename = hashlib.md5(url.encode()).hexdigest()[:16] + ext
            filepath = os.path.join(attachments_dir, filename)
            
            if not os.path.exists(filepath):
                os.makedirs(attachments_dir, exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(content)
                logger.debug(f"Downloaded image: {filename}")
            
            return filename
        except Exception as e:
            logger.warning(f"Failed to download image from {url}: {e}")
            return url
    
    def _get_image_extension(self, content_type: str) -> str:
        ext_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "image/svg+xml": ".svg",
        }
        return ext_map.get(content_type, ".jpg")
