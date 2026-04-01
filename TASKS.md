# Notion Backup Tool - 任务清单

## 阶段 1: 项目初始化

- [ ] 创建项目目录结构 (`notion_backup/`, `.github/workflows/`)
- [ ] 创建 `requirements.txt`
- [ ] 创建 `.gitignore`
- [ ] 创建 `.env.example`

## 阶段 2: 核心功能开发

- [ ] 实现 `notion_backup/client.py` - Notion API 客户端封装
  - 初始化客户端、验证 Token
  - 搜索所有可访问页面
  - 获取页面内容和子页面
- [ ] 实现 `notion_backup/converter.py` - Block 到 Markdown 转换
  - 解析所有 Notion Block 类型（基础文本、富文本、媒体嵌入、数据库、布局、高级块）
  - 折叠标题/折叠列表 → `<details><summary>` HTML 标签
  - 公式 → LaTeX 格式
  - 表格 → Markdown 表格
  - 生成 YAML front matter
  - 处理富文本格式（粗体、斜体、删除线、下划线、行内代码、高亮、颜色、链接）
- [ ] 实现 `notion_backup/backup.py` - 备份核心逻辑
  - 递归遍历页面树
  - 创建备份目录（按日期命名）
  - 保存 Markdown 文件（按页面层级组织，文件命名格式：`页面原标题_YYYY-MM-DD.md`）
  - 清理旧备份（保留最新两份）
- [ ] 实现 `main.py` - CLI 入口
  - 解析命令行参数
  - 加载环境变量
  - 执行备份流程

## 阶段 3: GitHub Actions 配置

- [ ] 创建 `.github/workflows/backup.yml`
  - 配置 cron 定时触发（每天北京时间凌晨 2:00）
  - 配置手动触发 (workflow_dispatch)
  - 安装 Python 和依赖
  - 执行备份脚本
  - 提交备份文件到仓库

## 阶段 4: 文档

- [ ] 创建 `README.md`
  - 项目介绍
  - 前置条件（创建 Notion Integration）
  - 安装步骤
  - 本地使用方法
  - GitHub Actions 配置方法
  - 备份文件结构说明
