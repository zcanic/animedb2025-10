# AnimeDB 2025

一个基于Vercel部署的动漫数据库应用，支持筛选、排序、搜索等功能。

## 技术栈

- **后端**: FastAPI + SQLite
- **前端**: HTML + CSS + JavaScript (Vanilla)
- **部署**: Vercel
- **数据库**: SQLite (轻量级)

## 功能特性

- 🔍 动漫搜索和筛选
- 📊 多种排序方式
- 🎯 年份、评分、收藏数筛选
- 📱 响应式设计
- ⚡ 快速查询性能

## 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动后端
uvicorn main:app --reload

# 访问前端
打开 frontend/index.html
```

## 部署

项目已配置Vercel部署，推送到GitHub后可在Vercel中自动部署。

## 数据来源

数据来源于BGM.tv动漫数据库，包含14,257条动漫记录。