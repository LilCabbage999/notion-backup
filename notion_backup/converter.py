import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BlockConverter:
    IGNORED_TYPES = {"breadcrumb", "table_of_contents"}
    TOGGLE_TYPES = {"toggle", "toggle_heading_1", "toggle_heading_2", "toggle_heading_3"}

    def __init__(self, notion_client=None, attachments_path=None, page_title=None):
        self._client = notion_client
        self._attachments_path = attachments_path
        self._page_title = page_title

    def convert_rich_text(self, rich_text_list: list) -> str:
        if not rich_text_list:
            return ""
        parts = []
        for rt in rich_text_list:
            plain_text = rt.get("plain_text", "")
            href = rt.get("href")
            annotations = rt.get("annotations", {})

            if not plain_text:
                continue

            formatted = plain_text

            if annotations.get("code"):
                formatted = f"`{formatted}`"
            if annotations.get("bold"):
                formatted = f"**{formatted}**"
            if annotations.get("italic"):
                formatted = f"*{formatted}*"
            if annotations.get("strikethrough"):
                formatted = f"~~{formatted}~~"
            if annotations.get("underline"):
                formatted = f"<u>{formatted}</u>"
            if annotations.get("highlight"):
                formatted = f"=={formatted}=="

            if href:
                formatted = f"[{formatted}]({href})"

            parts.append(formatted)

        return "".join(parts)

    def convert_block(self, block: dict) -> str:
        block_type = block.get("type", "")
        block_data = block.get(block_type, {})

        if block_type in self.IGNORED_TYPES:
            return ""

        handler = getattr(self, f"_convert_{block_type}", None)
        if handler:
            return handler(block, block_data)

        logger.debug(f"Unknown block type: {block_type}, skipping")
        return ""

    def _convert_paragraph(self, block: dict, data: dict) -> str:
        rich_text = self.convert_rich_text(data.get("rich_text", []))
        children = self._get_block_children(block)
        if children:
            child_md = self._convert_children(children)
            return f"{rich_text}\n\n{child_md}" if rich_text else child_md
        return f"{rich_text}\n\n" if rich_text else "\n"

    def _convert_heading_1(self, block: dict, data: dict) -> str:
        rich_text = self.convert_rich_text(data.get("rich_text", []))
        children = self._get_block_children(block)
        result = f"# {rich_text}\n\n"
        if children:
            result += self._convert_children(children)
        return result

    def _convert_heading_2(self, block: dict, data: dict) -> str:
        rich_text = self.convert_rich_text(data.get("rich_text", []))
        children = self._get_block_children(block)
        result = f"## {rich_text}\n\n"
        if children:
            result += self._convert_children(children)
        return result

    def _convert_heading_3(self, block: dict, data: dict) -> str:
        rich_text = self.convert_rich_text(data.get("rich_text", []))
        children = self._get_block_children(block)
        result = f"### {rich_text}\n\n"
        if children:
            result += self._convert_children(children)
        return result

    def _convert_heading_4(self, block: dict, data: dict) -> str:
        rich_text = self.convert_rich_text(data.get("rich_text", []))
        children = self._get_block_children(block)
        result = f"#### {rich_text}\n\n"
        if children:
            result += self._convert_children(children)
        return result

    def _convert_toggle_heading_1(self, block: dict, data: dict) -> str:
        """折叠一级标题直接转为普通一级标题"""
        rich_text = self.convert_rich_text(data.get("rich_text", []))
        children = self._get_block_children(block)
        result = f"# {rich_text}\n\n"
        if children:
            result += self._convert_children(children)
        return result

    def _convert_toggle_heading_2(self, block: dict, data: dict) -> str:
        """折叠二级标题直接转为普通二级标题"""
        rich_text = self.convert_rich_text(data.get("rich_text", []))
        children = self._get_block_children(block)
        result = f"## {rich_text}\n\n"
        if children:
            result += self._convert_children(children)
        return result

    def _convert_toggle_heading_3(self, block: dict, data: dict) -> str:
        """折叠三级标题直接转为普通三级标题"""
        rich_text = self.convert_rich_text(data.get("rich_text", []))
        children = self._get_block_children(block)
        result = f"### {rich_text}\n\n"
        if children:
            result += self._convert_children(children)
        return result

    def _convert_toggle(self, block: dict, data: dict) -> str:
        """折叠列表直接转为普通段落，保留子内容"""
        rich_text = self.convert_rich_text(data.get("rich_text", []))
        children = self._get_block_children(block)
        result = f"{rich_text}\n\n" if rich_text else ""
        if children:
            result += self._convert_children(children)
        return result

    def _convert_bulleted_list_item(self, block: dict, data: dict) -> str:
        rich_text = self.convert_rich_text(data.get("rich_text", []))
        children = self._get_block_children(block)
        if children:
            child_md = self._convert_children(children)
            return f"- {rich_text}\n  {child_md}" if rich_text else f"-\n  {child_md}"
        return f"- {rich_text}\n" if rich_text else "-\n"

    def _convert_numbered_list_item(self, block: dict, data: dict) -> str:
        rich_text = self.convert_rich_text(data.get("rich_text", []))
        children = self._get_block_children(block)
        if children:
            child_md = self._convert_children(children)
            return f"1. {rich_text}\n   {child_md}" if rich_text else f"1.\n   {child_md}"
        return f"1. {rich_text}\n" if rich_text else "1.\n"

    def _convert_to_do(self, block: dict, data: dict) -> str:
        rich_text = self.convert_rich_text(data.get("rich_text", []))
        checked = data.get("checked", False)
        checkbox = "[x]" if checked else "[ ]"
        children = self._get_block_children(block)
        if children:
            child_md = self._convert_children(children)
            return f"- [{checkbox}] {rich_text}\n  {child_md}" if rich_text else f"- [{checkbox}]\n  {child_md}"
        return f"- [{checkbox}] {rich_text}\n" if rich_text else f"- [{checkbox}]\n"

    def _convert_code(self, block: dict, data: dict) -> str:
        rich_text = self.convert_rich_text(data.get("rich_text", []))
        language = data.get("language", "plain text")
        return f"```{language}\n{rich_text}\n```\n\n"

    def _convert_quote(self, block: dict, data: dict) -> str:
        rich_text = self.convert_rich_text(data.get("rich_text", []))
        children = self._get_block_children(block)
        lines = rich_text.split("\n")
        quoted = "\n".join(f"> {line}" for line in lines)
        result = f"{quoted}\n"
        if children:
            child_md = self._convert_children(children)
            child_lines = child_md.strip().split("\n")
            for line in child_lines:
                result += f"> {line}\n"
        return result + "\n"

    def _convert_callout(self, block: dict, data: dict) -> str:
        rich_text = self.convert_rich_text(data.get("rich_text", []))
        icon = data.get("icon") or {}
        emoji = ""
        if icon.get("type") == "emoji":
            emoji = icon.get("emoji", "")
        children = self._get_block_children(block)
        lines = rich_text.split("\n")
        quoted = "\n".join(f"> {emoji} {line}" if line else ">" for line in lines)
        result = f"{quoted}\n"
        if children:
            child_md = self._convert_children(children)
            child_lines = child_md.strip().split("\n")
            for line in child_lines:
                result += f"> {line}\n"
        return result + "\n"

    def _convert_divider(self, block: dict, data: dict) -> str:
        return "---\n\n"

    def _convert_image(self, block: dict, data: dict) -> str:
        file_info = data.get("file", {}) or data.get("external", {})
        url = file_info.get("url", "")
        caption = self.convert_rich_text(data.get("caption", []))
        alt = caption if caption else "image"
        
        image_url = url
        if self._client and self._attachments_path and url:
            filename = self._client.download_image(url, self._attachments_path)
            if filename != url:
                # 使用相对于 Markdown 文件的路径
                if self._page_title:
                    attachments_folder = f"{self._page_title}_attachments"
                    image_url = f"{attachments_folder}/{filename}"
                else:
                    image_url = f"attachments/{filename}"
        
        return f"![{alt}]({image_url})\n\n"

    def _convert_video(self, block: dict, data: dict) -> str:
        file_info = data.get("file", {}) or data.get("external", {})
        url = file_info.get("url", "")
        caption = self.convert_rich_text(data.get("caption", []))
        label = caption if caption else "Video"
        return f"[{label}]({url})\n\n"

    def _convert_file(self, block: dict, data: dict) -> str:
        file_info = data.get("file", {}) or data.get("external", {})
        url = file_info.get("url", "")
        caption = self.convert_rich_text(data.get("caption", []))
        label = caption if caption else "File"
        return f"[{label}]({url})\n\n"

    def _convert_pdf(self, block: dict, data: dict) -> str:
        file_info = data.get("file", {}) or data.get("external", {})
        url = file_info.get("url", "")
        caption = self.convert_rich_text(data.get("caption", []))
        label = caption if caption else "PDF"
        return f"[{label}]({url})\n\n"

    def _convert_bookmark(self, block: dict, data: dict) -> str:
        url = data.get("url", "")
        caption = self.convert_rich_text(data.get("caption", []))
        label = caption if caption else url
        return f"[{label}]({url})\n\n"

    def _convert_embed(self, block: dict, data: dict) -> str:
        url = data.get("url", "")
        caption = self.convert_rich_text(data.get("caption", []))
        label = caption if caption else "Embed"
        return f"[{label}]({url})\n\n"

    def _convert_figma(self, block: dict, data: dict) -> str:
        url = data.get("url", "")
        return f"[Figma]({url})\n\n"

    def _convert_audio(self, block: dict, data: dict) -> str:
        file_info = data.get("file", {}) or data.get("external", {})
        url = file_info.get("url", "")
        caption = self.convert_rich_text(data.get("caption", []))
        label = caption if caption else "Audio"
        return f"[{label}]({url})\n\n"

    def _convert_tweet(self, block: dict, data: dict) -> str:
        url = data.get("url", "")
        return f"[Tweet]({url})\n\n"

    def _convert_gist(self, block: dict, data: dict) -> str:
        url = data.get("url", "")
        return f"[Gist]({url})\n\n"

    def _convert_equation(self, block: dict, data: dict) -> str:
        expression = data.get("expression", "")
        return f"${expression}$\n\n"

    def _convert_table(self, block: dict, data: dict) -> str:
        table_width = data.get("table_width", 1)
        has_column_header = data.get("has_column_header", False)
        has_row_header = data.get("has_row_header", False)
        children = self._get_block_children(block)

        if not children:
            return ""

        rows = []
        for child in children:
            cells = child.get("table_row", {}).get("cells", [])
            row = [self.convert_rich_text(cell) for cell in cells]
            rows.append(row)

        if not rows:
            return ""

        md_lines = []
        for i, row in enumerate(rows):
            md_lines.append("| " + " | ".join(row) + " |")
            if i == 0 and has_column_header:
                md_lines.append("| " + " | ".join(["---"] * len(row)) + " |")

        return "\n".join(md_lines) + "\n\n"

    def _convert_table_row(self, block: dict, data: dict) -> str:
        return ""

    def _convert_child_page(self, block: dict, data: dict) -> str:
        title = data.get("title", "")
        if isinstance(title, list):
            title = self.convert_rich_text(title)
        return f"\n> [Sub-page: {title}]\n\n"

    def _convert_child_database(self, block: dict, data: dict) -> str:
        title = data.get("title", "")
        if isinstance(title, list):
            title = self.convert_rich_text(title)
        return f"\n> [Database: {title}]\n\n"

    def _convert_column_list(self, block: dict, data: dict) -> str:
        children = self._get_block_children(block)
        if children:
            return self._convert_children(children)
        return ""

    def _convert_column(self, block: dict, data: dict) -> str:
        children = self._get_block_children(block)
        if children:
            return self._convert_children(children)
        return ""

    def _convert_synced_block(self, block: dict, data: dict) -> str:
        synced_from = data.get("synced_from", None)
        children = self._get_block_children(block)
        if children:
            return self._convert_children(children)
        if synced_from:
            return "\n> [Synced Block]\n\n"
        return ""

    def _convert_link_preview(self, block: dict, data: dict) -> str:
        url = data.get("url", "")
        return f"[Link Preview]({url})\n\n"

    def _convert_link_to_page(self, block: dict, data: dict) -> str:
        page_id = data.get("page_id", "")
        return f"\n> [Link to Page: {page_id}]\n\n"

    def _convert_external_object(self, block: dict, data: dict) -> str:
        return ""

    def _convert_mention(self, block: dict, data: dict) -> str:
        return ""

    def _convert_template(self, block: dict, data: dict) -> str:
        rich_text = self.convert_rich_text(data.get("rich_text", []))
        children = self._get_block_children(block)
        result = f"[Template: {rich_text}]\n\n"
        if children:
            result += self._convert_children(children)
        return result

    def _get_block_children(self, block: dict) -> list:
        children = block.get("children", [])
        if children:
            return children
        if block.get("has_children") and self._client:
            block_id = block.get("id", "")
            try:
                children = self._client.get_block_children(block_id)
                logger.debug(f"Fetched {len(children)} children for block {block_id[:12]}")
                return children
            except Exception as e:
                logger.warning(f"Failed to fetch children for block {block_id[:12]}: {e}")
        return []

    def _convert_children(self, children: list) -> str:
        parts = []
        for child in children:
            md = self.convert_block(child)
            if md:
                parts.append(md)
        return "".join(parts)

    def convert_blocks_to_markdown(self, blocks: list) -> str:
        return self._convert_children(blocks)

    def generate_front_matter(self, metadata: dict) -> str:
        lines = [
            "---",
            f"title: {metadata.get('title', 'Untitled')}",
            f"created_time: {metadata.get('created_time', '')}",
            f"last_edited_time: {metadata.get('last_edited_time', '')}",
            f"notion_url: {metadata.get('url', '')}",
            "---",
            "",
        ]
        return "\n".join(lines)
