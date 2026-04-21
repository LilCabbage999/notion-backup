# Notion Backup Tool

通过 Notion API 将笔记页面自动备份为 Markdown 格式，支持 GitHub Actions 定时执行。

## 功能特性

- 自动备份所有 Notion 页面为 Markdown 格式
- 完整支持所有 Notion Block 类型（标题、列表、代码块、表格、公式、折叠块等）
- 递归备份子页面，按层级组织目录
- 保留最新两份备份，自动清理旧备份
- 支持 GitHub Actions 定时备份
- 支持本地手动执行

## 前置条件

### 1. 创建 Notion Integration

1. 访问 [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. 点击 **"New integration"**
3. 填写名称（如 `notion-backup`），选择关联的 Workspace
4. 点击 **"Submit"**，复制生成的 **Internal Integration Token**（以 `ntn_` 或 `secret_` 开头）

### 2. 分享页面给 Integration

在 Notion 中，打开需要备份的页面，点击右上角 **"..."** → **"Connections"** → 搜索并添加你创建的 Integration。

> 注意：Integration 只能访问明确分享给它的页面。如需备份所有页面，请在顶级页面或 Workspace 级别进行分享。

## 安装

```bash
git clone https://github.com/LilCabbage999/notion-backup.git
cd notion-backup
pip install -r requirements.txt
```

## 使用方法

### 方式一：本地运行

1. 复制环境变量文件：

```bash
cp .env.example .env
```

2. 编辑 `.env`，填入你的 Notion Token：

```
NOTION_TOKEN=ntn_your_token_here
```

3. 执行备份：

```bash
python main.py
```

也可以通过命令行参数指定：

```bash
python main.py --token ntn_your_token --backup-dir ./my-backups --retention 3 -v
```

### 方式二：GitHub Actions 定时备份

1. 将代码推送到 GitHub 仓库
2. 进入仓库 **Settings** → **Secrets and variables** → **Actions**
3. 添加 Repository Secret：
   - `NOTION_TOKEN`: 你的 Notion Integration Token
4. GitHub Actions 会在每天北京时间凌晨 2:00 自动执行备份
5. 也可以在 **Actions** 页面手动触发 **"Run workflow"**

## 配置项

| 环境变量 | 命令行参数 | 说明 | 默认值 |
|----------|-----------|------|--------|
| `NOTION_TOKEN` | `--token` | Notion Integration Token（必填） | - |
| `BACKUP_DIR` | `--backup-dir` | 备份文件根目录 | `./backups` |
| `RETENTION_COUNT` | `--retention` | 保留备份份数 | `2` |

## 备份文件结构

```
backups/
├── backup_2026-04-01/
│   ├── 我的工作空间/
│   │   ├── 项目计划_2026-04-01.md
│   │   ├── 项目计划_2026-04-01_attachments/  # 该页面的附件
│   │   │   ├── abc123.jpg
│   │   │   └── def456.png
│   │   ├── 学习笔记/
│   │   │   ├── Python 学习_2026-04-01.md
│   │   │   ├── Python 学习_2026-04-01_attachments/
│   │   │   └── 读书笔记_2026-04-01.md
│   │   └── 会议记录_2026-04-01.md
│   └── 个人日记_2026-04-01.md
└── backup_2026-03-31/
    └── ...
```

**附件存储规则**：每个页面的附件保存在 `{页面名称}_{日期}_attachments/` 子文件夹中，便于管理和查找。

## 支持的 Block 类型

基础文本：段落、标题（H1-H4）、**折叠标题（转为普通标题）**、无序/有序列表、**折叠列表（保留内容）**、待办事项、引用、分割线、Callout

富文本：粗体、斜体、删除线、下划线、行内代码、高亮、颜色、链接

媒体嵌入：图片（下载到页面专属附件文件夹）、视频、文件、PDF、书签、Embed、Figma、音频、Tweet、Gist

数据库：子页面、子数据库、表格

布局：分栏、同步块

高级：代码块（带语言标注）、公式（LaTeX）、表格、面包屑导航、目录

> **注意**：折叠标题和折叠列表会直接转换为普通 Markdown 格式，保留所有内容，但不再具有折叠交互功能。

## 合法合规

- 仅使用 Notion 官方 API
- 遵守 Notion API 使用条款和速率限制
- 仅备份用户主动分享给 Integration 的页面
