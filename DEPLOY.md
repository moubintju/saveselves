# Vercel 部署指南

## 部署步骤

### 1. 准备 Git 仓库
```bash
# 初始化 Git 仓库
git init

# 添加所有文件
git add .

# 创建初始提交
git commit -m "Initial commit: Stock screener for Vercel"

# 连接到 GitHub 仓库 (创建新仓库后)
git remote add origin https://github.com/your-username/your-repo-name.git
git push -u origin main
```

### 2. 部署到 Vercel

#### 方法一：通过 Vercel CLI
```bash
# 安装 Vercel CLI
npm i -g vercel

# 登录 Vercel
vercel login

# 部署
vercel

# 生产环境部署
vercel --prod
```

#### 方法二：通过 Vercel 网站
1. 访问 [vercel.com](https://vercel.com)
2. 使用 GitHub 账号登录
3. 点击 "New Project"
4. 选择你的 GitHub 仓库
5. Vercel 会自动检测到 `vercel.json` 配置并部署

### 3. 环境变量配置 (如需要)
在 Vercel 仪表板中设置环境变量：
- 进入项目设置
- 点击 "Environment Variables"
- 添加需要的环境变量

### 4. 部署后验证
- 访问 Vercel 提供的 URL
- 测试股票筛选功能
- 检查日志输出

## 注意事项

### Vercel 限制
- **超时限制**: Vercel Hobby 计划函数最长执行时间为 10 秒
- **内存限制**: 默认 1024MB 内存
- **并发限制**: 有并发请求限制
- **文件系统**: 只读文件系统，不能写入文件

### 性能优化建议
1. **缓存数据**: 考虑使用外部数据库或缓存服务
2. **分页处理**: 大量股票数据建议分批处理
3. **异步处理**: 长时间任务考虑使用队列系统
4. **CDN 优化**: 静态资源通过 Vercel CDN 加速

### 故障排查
- 查看 Vercel 函数日志
- 检查 `vercel.json` 配置
- 确认 Python 依赖正确安装
- 监控函数执行时间

## 项目结构
```
touzi2/
├── vercel.json              # Vercel 配置文件
├── .gitignore              # Git 忽略文件
├── DEPLOY.md               # 部署指南
└── stock_screener/
    ├── app.py              # Vercel 入口文件 (适配版)
    ├── main.py             # 原本地运行版本
    ├── stock_screener.py   # 核心筛选逻辑
    ├── data_fetcher.py     # 数据获取模块
    ├── requirements.txt    # Python 依赖
    ├── static/             # 静态文件
    └── templates/          # HTML 模板
```

## 成本考虑
- **Vercel Hobby**: 免费，有使用限制
- **Vercel Pro**: $20/月，更高限额
- 如果数据请求频繁，考虑升级计划或使用缓存服务