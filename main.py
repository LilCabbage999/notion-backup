import os
import sys
import argparse
import logging

from dotenv import load_dotenv

from notion_backup.client import NotionClientWrapper
from notion_backup.backup import BackupManager


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    parser = argparse.ArgumentParser(description="Notion Backup Tool - Backup Notion pages to Markdown")
    parser.add_argument("--token", type=str, default=None, help="Notion Integration Token")
    parser.add_argument("--backup-dir", type=str, default=None, help="Backup directory path")
    parser.add_argument("--retention", type=int, default=None, help="Number of backups to keep")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    setup_logging(args.verbose)
    load_dotenv()

    token = args.token or os.environ.get("NOTION_TOKEN")
    if not token:
        print("Error: NOTION_TOKEN is required. Set it via --token, environment variable, or .env file.")
        sys.exit(1)

    backup_dir = args.backup_dir or os.environ.get("BACKUP_DIR", "./backups")
    retention_count = args.retention or int(os.environ.get("RETENTION_COUNT", "2"))

    try:
        notion_client = NotionClientWrapper(token)
        backup_manager = BackupManager(
            notion_client=notion_client,
            backup_dir=backup_dir,
            retention_count=retention_count,
        )
        backup_manager.run()
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Backup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
