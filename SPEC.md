# Notion Backup Tool - 规格说明

## 1. 项目概述

| 项目 | 说明 |
|------|------|
| 项目名称 | notion-backup |
| 项目类型 | Python CLI 工具 + GitHub Actions 定时任务 |
| 核心功能 | 通过 Notion API 将笔记页面备份为 Markdown 格式 |
| 开发语言 | Python 3.9+ |
| 定时方式 | GitHub Actions (cron) |
| 存储方式 | 本地 / GitHub 仓库 |

## 2. 技术栈

- **Python 3.9+**
- **notion-client**: Notion 官方 Python SDK
- **python-dotenv**: 环境变量管理
- **GitHub Actions**: CI/CD 定时任务

## 3. 功能需求

### 3.1 Notion API 集成

- 使用 Notion Integration Token 进行身份验证
- 获取用户授权访问的所有页面列表
- 递归遍历所有子页面（支持多层嵌套）

### 3.2 Markdown 转换

- 将 Notion 页面内容（Block）转换为 Markdown 格式
- 支持的块类型（完整覆盖 Notion API 所有 Block 类型）：

  **基础文本块：**
  - 段落 (paragraph)
  - 标题 (heading_1 / heading_2 / heading_3)
  - 折叠标题 (toggle_heading_1 / toggle_heading_2 / toggle_heading_3) → 转为 `<details><summary>` HTML 标签
  - 无序列表 (bulleted_list_item)
  - 有序列表 (numbered_list_item)
  - 折叠列表 (toggle) → 转为 `<details><summary>` HTML 标签
  - 待办事项 (to_do) → 转为 `- [ ]` / `- [x]`
  - 引用 (quote)
  - 分割线 (divider)
  - 呼吸提示 / 分隔线 (callout) → 转为引用块 + emoji 图标

  **富文本格式：**
  - 粗体 (bold)
  - 斜体 (italic)
  - 删除线 (strikethrough)
  - 下划线 (underline)
  - 行内代码 (code)
  - 高亮 (highlight) → 转为 `==高亮==`（需 Markdown 扩展支持）
  - 颜色 (color) → 保留文本，忽略颜色
  - 链接 (link)

  **媒体与嵌入块：**
  - 图片 (image) → `![alt](url)`
  - 视频 (video) → 保留外部链接
  - 文件 (file) → `[filename](url)`
  - PDF (pdf) → `[filename](url)`
  - 书签 (bookmark) → `[title](url)`
  - 嵌入 (embed) → `[title](url)`
  - Figma 嵌入 (figma) → `[Figma](url)`
  - 音频 (audio) → `[audio](url)`
  - 推文嵌入 (tweet) → `[Tweet](url)`
  - Gist 嵌入 (gist) → `[Gist](url)`

  **数据库相关块：**
  - 子页面 (child_page) → 递归处理为独立 .md 文件
  - 子数据库 (child_database) → 记录为链接占位符
  - 表格行 (table_row) → Markdown 表格

  **布局块：**
  - 分栏 (column_list / column) → 顺序排列内容
  - 同步块 (synced_block) → 输出同步内容

  **高级块：**
  - 代码块 (code) → 带语言标注的围栏代码块
  - 公式 / 数学表达式 (equation) → LaTeX 格式 `$$...$$` / `$...$`
  - 面包屑导航 (breadcrumb) → 忽略（仅 UI 元素）
  - 表格 (table) → Markdown 表格
  - 表格_of_contents (table_of_contents) → 忽略（动态生成内容）
- 在 Markdown 文件头部添加 YAML front matter（标题、创建时间、最后编辑时间、Notion URL）

### 3.3 备份策略

- **覆盖策略**: 每次备份生成新的日期目录，保留最新两份备份
- **备份目录命名**: `backup_YYYY-MM-DD/` 格式
- **Markdown 文件命名**: `页面原标题_YYYY-MM-DD.md` 格式（如 `项目计划_2026-04-01.md`）
- **目录结构**: 按页面层级组织子目录
- **自动清理**: 备份完成后自动删除超过保留份数的旧备份

### 3.4 GitHub Actions 定时任务

- 使用 cron 表达式设置定时触发（默认每天北京时间凌晨 2:00）
- 支持手动触发 (workflow_dispatch)
- 自动安装 Python 依赖并执行备份
- 自动将备份文件提交到 GitHub 仓库

## 4. 项目结构

```
notion-backup/
├── notion_backup/
│   ├── __init__.py
│   ├── client.py           # Notion API 客户端封装
│   ├── converter.py        # Block -> Markdown 转换器
│   └── backup.py           # 备份核心逻辑（获取页面、保存文件、清理旧备份）
├── .github/
│   └── workflows/
│       └── backup.yml      # GitHub Actions workflow
├── .env.example            # 环境变量示例
├── .gitignore
├── requirements.txt        # Python 依赖
├── main.py                 # CLI 入口
├── SPEC.md                 # 本文件
├── TASKS.md                # 任务清单
└── README.md               # 使用说明
```

## 5. 配置项

### 环境变量

| 变量名 | 说明 | 必需 | 默认值 |
|--------|------|------|--------|
| `NOTION_TOKEN` | Notion Integration Token | 是 | - |
| `BACKUP_DIR` | 备份文件根目录 | 否 | `./backups` |
| `RETENTION_COUNT` | 保留备份份数 | 否 | `2` |

### GitHub Secrets

| 密钥名 | 说明 |
|--------|------|
| `NOTION_TOKEN` | Notion Integration Token |

## 6. 备份文件格式

### 目录结构示例

```
backups/
├── backup_2026-04-01/
│   ├── 我的工作空间/
│   │   ├── 项目计划_2026-04-01.md
│   │   ├── 学习笔记/
│   │   │   ├── Python 学习_2026-04-01.md
│   │   │   └── 读书笔记_2026-04-01.md
│   │   └── 会议记录_2026-04-01.md
│   └── 个人日记_2026-04-01.md
└── backup_2026-03-31/
    └── ...
```

### Markdown 文件格式

```markdown
---
title: 页面标题
created_time: 2026-04-01T00:00:00.000Z
last_edited_time: 2026-04-01T12:00:00.000Z
notion_url: https://www.notion.so/xxxxx
---

# 页面标题

页面正文内容...
```

## 7. 错误处理

| 场景 | 处理方式 |
|------|----------|
| Token 无效或过期 | 终止执行，输出明确错误信息 |
| API 请求失败 | 自动重试，最多 3 次，间隔 5 秒 |
| API 限流 (429) | 根据 Retry-After 头等待后重试 |
| 页面无权限访问 | 跳过该页面，记录警告日志 |
| 网络超时 | 等待后重试 |
| 文件写入失败 | 输出错误信息，跳过该文件 |

## 8. 合法合规

- 仅使用 Notion 官方 API（https://developers.notion.com）
- 遵守 Notion API 使用条款和速率限制
- 仅备份用户主动分享给 Integration 的页面
- 备份文件存储在用户自己的本地或 GitHub 仓库中
- 不存储、不传输任何敏感信息（Token 通过环境变量/Secrets 管理）

## 9. 依赖包

```
notion-client>=2.2.0
python-dotenv>=1.0.0
```
