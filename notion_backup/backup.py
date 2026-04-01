import os
import re
import shutil
import logging
from datetime import datetime
from typing import Optional

from .client import NotionClientWrapper
from .converter import BlockConverter

logger = logging.getLogger(__name__)


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


class BackupManager:
    def __init__(self, notion_client: NotionClientWrapper, backup_dir: str = "./backups", retention_count: int = 2):
        self.client = notion_client
        self.backup_dir = os.path.abspath(backup_dir)
        self.retention_count = retention_count
        self.converter = BlockConverter(notion_client=self.client)
        self.backup_date = datetime.now().strftime("%Y-%m-%d")
        self.backup_path = os.path.join(self.backup_dir, f"backup_{self.backup_date}")
        self.attachments_path = os.path.join(self.backup_path, "attachments")
        self.stats = {"pages": 0, "errors": 0, "skipped": 0}

    def run(self):
        logger.info(f"Starting backup to: {self.backup_path}")
        os.makedirs(self.backup_path, exist_ok=True)

        pages = self.client.search_all_pages()
        if not pages:
            logger.warning("No pages found to backup")
            return

        processed_ids = set()
        for page in pages:
            page_id = page.get("id", "")
            if page_id in processed_ids:
                continue
            processed_ids.add(page_id)
            try:
                self._backup_page(page, self.backup_path)
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"Failed to backup page {page_id}: {e}")

        self._cleanup_old_backups()

        logger.info(
            f"Backup completed: {self.stats['pages']} pages backed up, "
            f"{self.stats['errors']} errors, {self.stats['skipped']} skipped"
        )

    def _backup_page(self, page: dict, parent_dir: str):
        metadata = self.client.get_page_metadata(page)
        title = sanitize_filename(metadata["title"])

        filename = f"{title}_{self.backup_date}.md"
        filepath = os.path.join(parent_dir, filename)

        blocks = self.client.get_block_children(metadata["id"])
        converter = BlockConverter(notion_client=self.client, attachments_path=self.attachments_path)
        markdown_body = converter.convert_blocks_to_markdown(blocks)
        front_matter = converter.generate_front_matter(metadata)

        content = f"{front_matter}{markdown_body}"

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        self.stats["pages"] += 1
        logger.info(f"Backed up: {title} -> {filepath}")

        child_pages = [b for b in blocks if b.get("type") == "child_page"]
        if child_pages:
            child_dir = os.path.join(parent_dir, title)
            os.makedirs(child_dir, exist_ok=True)
            for child_block in child_pages:
                child_page_id = child_block.get("id", "")
                try:
                    child_page = self.client.get_page(child_page_id)
                    self._backup_page(child_page, child_dir)
                except Exception as e:
                    self.stats["errors"] += 1
                    logger.error(f"Failed to backup child page {child_page_id}: {e}")

    def _cleanup_old_backups(self):
        if not os.path.exists(self.backup_dir):
            return

        backup_dirs = []
        for entry in os.listdir(self.backup_dir):
            full_path = os.path.join(self.backup_dir, entry)
            if os.path.isdir(full_path) and entry.startswith("backup_"):
                backup_dirs.append((entry, full_path))

        backup_dirs.sort(key=lambda x: x[0], reverse=True)

        if len(backup_dirs) > self.retention_count:
            for _, old_path in backup_dirs[self.retention_count:]:
                logger.info(f"Removing old backup: {old_path}")
                shutil.rmtree(old_path, ignore_errors=True)
