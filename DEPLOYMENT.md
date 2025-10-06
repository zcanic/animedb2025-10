# 部署指南

## Vercel 部署步骤

### 1. 准备GitHub仓库

```bash
# 初始化Git仓库
cd animedb2025-10
git init
git add .
git commit -m "Initial commit: AnimeDB application"

# 连接到GitHub仓库
git remote add origin https://github.com/zcanic/animedb2025-10.git
git branch -M main
git push -u origin main
```

### 2. Vercel 部署

1. 访问 [Vercel](https://vercel.com)
2. 使用GitHub账号登录
3. 点击 "New Project"
4. 选择 `zcanic/animedb2025-10` 仓库
5. 配置项目设置：
   - **Framework Preset**: Other
   - **Build Command**: (留空)
   - **Output Directory**: (留空)
   - **Install Command**: `pip install -r requirements.txt`
6. 点击 "Deploy"

### 3. 环境变量（可选）

如果需要在生产环境配置额外的环境变量，可以在Vercel项目的Settings > Environment Variables中添加。

## 本地开发

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动开发服务器

```bash
# 启动后端服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 访问应用
# 后端API: http://localhost:8000/api/anime
# 前端界面: http://localhost:8000
```

### 测试API

```bash
# 测试API端点
curl http://localhost:8000/api/anime
curl http://localhost:8000/api/stats
```

## 项目结构

```
animedb2025-10/
├── main.py                 # FastAPI后端主文件
├── requirements.txt        # Python依赖
├── vercel.json            # Vercel部署配置
├── .gitignore             # Git忽略文件
├── README.md              # 项目说明
├── DEPLOYMENT.md          # 部署指南
└── frontend/              # 前端文件
    ├── index.html         # 主页面
    ├── styles.css         # 样式文件
    └── script.js          # JavaScript逻辑
```

## 功能特性

- ✅ 完整的动漫数据库（14,257条记录）
- ✅ 实时搜索和筛选
- ✅ 多种排序方式
- ✅ 响应式设计
- ✅ 分页加载
- ✅ 统计数据展示
- ✅ Vercel一键部署

## 注意事项

1. **首次部署**：数据库会在应用启动时自动初始化
2. **性能优化**：已为常用查询字段创建索引
3. **数据安全**：原始CSV文件不会被修改，数据库为只读模式
4. **内存使用**：使用分页查询避免内存溢出

## 故障排除

### 常见问题

1. **部署失败**
   - 检查 `requirements.txt` 中的依赖是否正确
   - 确认 `vercel.json` 配置正确

2. **数据库初始化失败**
   - 确保CSV文件路径正确
   - 检查文件编码是否为UTF-8

3. **前端无法访问API**
   - 检查CORS配置
   - 确认API端点URL正确

### 技术支持

如有问题，请检查：
- Vercel部署日志
- 浏览器开发者工具控制台
- 后端服务器日志