Investment-Analysis
<p align="center">
  <b>一个面向投资研究与组合分析的全栈项目</b><br/>
  <span>前端：Next.js + TypeScript + Tailwind CSS</span><br/>
  <span>后端：FastAPI + Pydantic + Python 科学计算栈</span>
</p>
---
项目简介
　　`Investment-Analysis` 是一个面向投资研究、基金组合分析与情景模拟的全栈项目。它的目标不是做一个简单的“行情展示网页”，而是构建一套具有研究工作台属性的系统：一方面能够从市场、情绪、组合、单基金、情景模拟等多个角度对投资对象进行结构化分析；另一方面能够将分析结果导出成适合进一步研究、汇报或 AI 继续处理的结构化内容。
　　整个项目采用前后端分离架构。前端负责页面展示、交互逻辑、导入导出入口与状态切换；后端负责所有金融指标计算、组合暴露分析、情景模拟、OCR/CSV 导入解析以及统一 API 输出。项目设计时特别强调“复杂分析逻辑必须放在后端，前端只负责展示”，这样可以避免口径不一致的问题。
　　如果你准备把这个项目作为课程项目、作品集项目、面试项目或者后续继续扩展的工程基础，那么建议你先完整阅读本文档，再开始运行。
---
核心功能
　　本项目当前的主要模块包括以下几个部分：
　　1. 市场总览（Market Overview）  
　　用于回答“今天市场发生了什么”。页面展示主要指数、板块轮动、主力资金流、市场广度以及市场解释摘要。
　　2. 风险情绪（Risk Sentiment）  
　　通过短期和中长期双仪表盘压缩展示市场风险状态，并提供因子拆解与时间序列分析。
　　3. 基金组合（Portfolio Analysis）  
　　包含组合看穿、组合诊断与 AI 导出三个主要标签，可展示组合摘要、行业/风格/市场暴露、基金重叠热力图、风险偏差与优化建议。
　　4. 单基金研究（Fund Research）  
　　围绕某一只基金输出基金概览、风险收益画像、持仓与风格画像、与当前组合的关系以及结论建议。
　　5. 情景模拟（Scenario / Statistical Simulation）  
　　支持统计模拟和情景冲击模拟，输出收益分布热力图、理论最优/最差回报曲线和情景敏感度表。
　　6. 导入与设置（Import / Settings）  
　　支持基金代码导入、截图导入、CSV 导入，并提供风险画像、默认视角、导出偏好等设置。
---
技术栈
前端
　　前端基于以下技术：
　　1. `Next.js`：用于构建 React 应用与页面路由。  
　　2. `TypeScript`：提升类型安全性与可维护性。  
　　3. `Tailwind CSS`：快速构建页面样式。  
　　4. `React Query`：负责异步请求、缓存与状态管理。  
　　5. `Axios`：负责向后端发起 HTTP 请求。
后端
　　后端基于以下技术：
　　1. `FastAPI`：构建 REST API。  
　　2. `Pydantic`：进行请求/响应数据校验。  
　　3. `NumPy / Pandas / SciPy`：执行金融数据分析与模拟计算。  
　　4. `Uvicorn`：运行 ASGI 服务。  
　　5. 预留 `Redis / Celery / PostgreSQL` 等扩展方向，但当前压缩包中主要是本地开发版本。
---
项目结构说明
　　根目录主要结构如下：
```text
Investment-Analysis/
├── backend/                     # FastAPI 后端
│   ├── app.py                   # 后端入口，注册所有 API 路由
│   ├── sample_data.py           # 示例/合成数据，用于本地演示
│   ├── __init__.py
│   └── routers/                 # 各模块 API
│       ├── system.py            # 系统初始化接口
│       ├── market.py            # 市场总览接口
│       ├── sentiment.py         # 风险情绪接口
│       ├── portfolio.py         # 组合分析接口
│       ├── fund.py              # 单基金研究接口
│       ├── simulation.py        # 情景模拟接口
│       ├── import_api.py        # 导入接口
│       ├── export_api.py        # 导出接口
│       └── settings.py          # 设置接口
│
├── frontend/                    # Next.js 前端
│   ├── pages/                   # 页面路由
│   │   ├── index.tsx
│   │   ├── overview.tsx
│   │   ├── sentiment.tsx
│   │   ├── portfolio.tsx
│   │   ├── simulation.tsx
│   │   ├── import.tsx
│   │   ├── settings.tsx
│   │   └── fund/
│   │       ├── index.tsx
│   │       └── [code].tsx
│   │
│   ├── components/              # 通用组件
│   │   ├── Layout.tsx
│   │   ├── Sidebar.tsx
│   │   ├── TopBar.tsx
│   │   ├── MarketSelector.tsx
│   │   ├── TimeWindowSelector.tsx
│   │   ├── PortfolioSelector.tsx
│   │   ├── ExportButton.tsx
│   │   └── ResearchModeSwitch.tsx
│   │
│   ├── styles/
│   │   └── globals.css
│   │
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── postcss.config.js
│   └── tailwind.config.js
│
├── data_collection.py           # 早期/基础数据抓取模块
├── data_analysis.py             # 早期/基础指标计算模块
├── portfolio_optimization.py    # 早期/基础组合优化模块
├── visualizations.py            # 早期/基础可视化模块
├── main.py                      # 早期/基础脚本入口
├── requirements.txt             # Python 依赖（需补充 FastAPI 相关）
├── description                  # 项目描述文件
└── README.md                    # 当前文档
```
　　需要特别说明的是：根目录下的 `data_collection.py`、`data_analysis.py`、`portfolio_optimization.py`、`visualizations.py`、`main.py` 更接近“早期分析脚本模块”；而真正驱动网页系统的是 `backend/` 与 `frontend/` 这两个目录。
---
环境要求
Python 环境要求
　　推荐使用：
Python `3.10` 或 `3.11`
　　不建议过低版本，否则某些类型语法、依赖兼容性会出问题。
Node.js 环境要求
　　推荐使用：
Node.js `18.x` 或 `20.x`
npm `9.x` 或以上
　　因为前端是 Next.js 项目，所以必须安装 Node.js。只安装 Python 是不够的。
---
运行前环境检测
　　在真正安装依赖和启动之前，建议先做环境检测。下面把 Windows、Linux、macOS 都分别写清楚。
1. 检查 Python 是否可用
Windows（PowerShell / PyCharm Terminal）
```powershell
python --version
pip --version
```
Linux / macOS
```bash
python3 --version
pip3 --version
```
　　如果没有输出版本号，而是提示命令找不到，那么说明你还没有正确安装 Python，或者没有把 Python 加到环境变量里。
2. 检查 Node.js 是否可用
Windows / Linux / macOS
```bash
node -v
npm -v
```
　　如果这里报错，说明前端无法启动，你需要先安装 Node.js。
3. 检查当前终端是否已经进入虚拟环境
Windows PowerShell
　　如果已经激活虚拟环境，终端前面通常会出现类似：
```text
(.venv) PS C:\Users\YourName\Desktop\Investment-Analysis>
```
Linux / macOS
　　通常会显示：
```text
(.venv) user@machine:~/Investment-Analysis$
```
　　如果没有 `(.venv)` 前缀，则说明当前终端还没有进入虚拟环境。
---
安装与运行总览
　　整个项目需要启动 两个服务：
　　1. 后端 FastAPI：默认运行在 `http://127.0.0.1:8000`  
　　2. 前端 Next.js：默认运行在 `http://localhost:3000`
　　你需要同时启动两者，然后在浏览器中访问前端地址，才能看到完整网页效果。
---
Windows + PyCharm 运行指南（强烈推荐先看）
　　如果你当前和我对话时的环境一样，是：
Windows
PyCharm
PyCharm 自带 Terminal / PowerShell
　　那么你最应该按这一节操作。
第一步：用 PyCharm 打开项目
　　在 PyCharm 中选择：
```text
File -> Open
```
　　然后打开整个 `Investment-Analysis` 根目录，而不是只打开 `backend` 或 `frontend` 某一个子目录。
第二步：创建 Python 虚拟环境
　　你可以用两种方式。
方式 A：用 PyCharm 图形界面创建（推荐）
　　进入：
```text
File -> Settings -> Project -> Python Interpreter
```
　　点击右上角齿轮，选择新建虚拟环境，路径建议设为：
```text
.venv
```
　　创建完成后，PyCharm 会自动把它绑定到当前项目。
方式 B：用 PyCharm Terminal 手动创建
　　在项目根目录执行：
```powershell
python -m venv .venv
```
第三步：激活虚拟环境
Windows PowerShell（PyCharm 默认常见情况）
```powershell
.venv\Scripts\activate
```
Windows CMD
```cmd
.venv\Scripts\activate.bat
```
　　注意：
　　在 Windows 下不要写：
```bash
source .venv/bin/activate
```
　　因为这是 Linux/macOS 的命令，在 PowerShell 里一定会报错。
　　同样，在 Windows 下不要写：
```bash
python3 -m venv .venv
```
　　因为很多 Windows 环境里只有 `python`，没有 `python3`。
第四步：安装后端依赖
　　项目当前 `requirements.txt` 里主要是早期分析模块依赖，所以你还需要额外安装 FastAPI 运行依赖。建议执行：
```powershell
pip install -r requirements.txt
pip install fastapi uvicorn pydantic python-multipart
```
　　如果你后续需要做更稳定的依赖管理，建议把这些包正式写回 `requirements.txt`。
第五步：启动后端
　　在项目根目录执行：
```powershell
uvicorn backend.app:app --reload --port 8000
```
　　如果启动成功，你可以在浏览器里打开：
```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
```
　　其中 `/docs` 是 FastAPI 自动生成的 API 文档页面。
第六步：安装前端依赖
　　打开一个新的终端标签页，进入前端目录：
```powershell
cd frontend
npm install
```
　　如果这里报 Node.js 相关错误，请先确认前面“环境检测”步骤已经通过。
第七步：补充 Next.js 类型文件（如果缺失）
　　如果 `frontend` 目录下没有 `next-env.d.ts` 文件，请手动新建这个文件，内容如下：
```ts
/// <reference types="next" />
/// <reference types="next/image-types/global" />

// NOTE: This file should not be edited
```
　　这一步是为了避免 TypeScript / Next.js 的类型报错。
第八步：启动前端
　　在 `frontend` 目录下执行：
```powershell
npm run dev
```
　　启动成功后，在浏览器访问：
```text
http://localhost:3000
```
第九步：确认前后端联通
　　如果你能打开前端页面，但页面显示“加载失败”或者控制台出现接口 404，那么通常不是前端没起来，而是前端请求没有正确转发到后端。
　　当前项目中，前端很多地方直接请求：
```ts
/api/v1/...
```
　　这意味着前端默认会向自己的 `3000` 端口请求，而不是 `8000` 端口的 FastAPI。
　　因此你需要做二选一处理：
方案 A：直接给 Axios 配置后端地址（最简单）
　　在前端代码里把：
```ts
axios.get('/api/v1/system/bootstrap')
```
　　改成：
```ts
axios.get('http://127.0.0.1:8000/api/v1/system/bootstrap')
```
　　其它 `axios.get('/api/v1/...')`、`axios.post('/api/v1/...')` 同理。
方案 B：配置 Next.js 代理转发（更工程化）
　　在 `frontend/next.config.js` 中加入：
```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://127.0.0.1:8000/api/v1/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
```
　　然后重启前端。
　　建议：本地演示阶段优先用方案 A，简单直接。
---
Linux 运行指南
1. 创建虚拟环境
```bash
python3 -m venv .venv
```
2. 激活虚拟环境
```bash
source .venv/bin/activate
```
3. 安装后端依赖
```bash
pip install -r requirements.txt
pip install fastapi uvicorn pydantic python-multipart
```
4. 启动后端
```bash
uvicorn backend.app:app --reload --port 8000
```
5. 启动前端
```bash
cd frontend
npm install
npm run dev
```
6. 打开浏览器
```text
http://localhost:3000
```
---
macOS 运行指南
　　macOS 的操作和 Linux 基本一致。
1. 创建虚拟环境
```bash
python3 -m venv .venv
```
2. 激活虚拟环境
```bash
source .venv/bin/activate
```
3. 安装后端依赖
```bash
pip install -r requirements.txt
pip install fastapi uvicorn pydantic python-multipart
```
4. 启动后端
```bash
uvicorn backend.app:app --reload --port 8000
```
5. 启动前端
```bash
cd frontend
npm install
npm run dev
```
6. 在浏览器访问
```text
http://localhost:3000
```
---
一键启动脚本
　　为了减少重复输入命令，下面给出可以直接放进项目根目录的启动脚本。
Windows 一键启动脚本：`start_windows.bat`
```bat
@echo off
echo [1/3] Activating virtual environment...
call .venv\Scripts\activate

echo [2/3] Starting backend...
start cmd /k "uvicorn backend.app:app --reload --port 8000"

echo [3/3] Starting frontend...
start cmd /k "cd frontend && npm run dev"

echo Done.
echo Backend: http://127.0.0.1:8000
echo Frontend: http://localhost:3000
pause
```
　　使用方式：双击运行，或者在命令行中执行：
```cmd
start_windows.bat
```
Windows PowerShell 版本：`start_windows.ps1`
```powershell
Write-Host "[1/3] Activating virtual environment..."
& .\.venv\Scripts\Activate.ps1

Write-Host "[2/3] Starting backend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "uvicorn backend.app:app --reload --port 8000"

Write-Host "[3/3] Starting frontend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "Done."
Write-Host "Backend: http://127.0.0.1:8000"
Write-Host "Frontend: http://localhost:3000"
```
　　如果 PowerShell 不允许执行脚本，请先运行：
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
Linux / macOS 一键启动脚本：`start_unix.sh`
```bash
#!/usr/bin/env bash

echo "[1/3] Activating virtual environment..."
source .venv/bin/activate

echo "[2/3] Starting backend..."
uvicorn backend.app:app --reload --port 8000 &
BACKEND_PID=$!

echo "[3/3] Starting frontend..."
cd frontend || exit 1
npm run dev &
FRONTEND_PID=$!

echo "Done."
echo "Backend: http://127.0.0.1:8000"
echo "Frontend: http://localhost:3000"

wait $BACKEND_PID $FRONTEND_PID
```
　　使用前先赋予执行权限：
```bash
chmod +x start_unix.sh
./start_unix.sh
```
---
常见错误排查（务必看）
　　这一节非常重要，因为你现在已经遇到了其中一部分问题。
1. `source : 无法将“source”项识别为 cmdlet`
现象
　　在 Windows PowerShell 中执行：
```bash
source .venv/bin/activate
```
　　报错找不到 `source`。
原因
　　`source` 是 Linux/macOS 的 shell 命令，PowerShell 不支持。
解决方法
　　在 Windows PowerShell 中使用：
```powershell
.venv\Scripts\activate
```
---
2. `python3 : 无法识别`
现象
　　在 Windows 中执行：
```bash
python3 -m venv .venv
```
　　报错。
原因
　　Windows 默认通常只有 `python` 命令，而没有 `python3`。
解决方法
```powershell
python -m venv .venv
```
---
3. `pydantic.errors.PydanticUserError: const is removed, use Literal instead`
现象
　　启动后端时，`simulation.py` 报：
```text
`const` is removed, use `Literal` instead
```
原因
　　项目代码中使用了 Pydantic v1 的旧写法，而当前环境里安装的是 Pydantic v2。
解决方法
　　打开文件：
```text
backend/routers/simulation.py
```
　　将：
```python
from pydantic import BaseModel, Field
```
　　改为：
```python
from typing import Literal
from pydantic import BaseModel, Field
```
　　并把：
```python
mode: str = Field("statistical", const=True)
```
　　改成：
```python
mode: Literal["statistical"] = "statistical"
```
　　把：
```python
mode: str = Field("scenario", const=True)
```
　　改成：
```python
mode: Literal["scenario"] = "scenario"
```
---
4. FastAPI 启动时报 `ModuleNotFoundError: No module named 'fastapi'`
原因
　　说明你还没有安装 FastAPI。
解决方法
```bash
pip install fastapi uvicorn pydantic python-multipart
```
---
5. 页面能打开，但数据加载失败 / 404
原因
　　前端请求 `/api/v1/...` 时，请求发给了 `localhost:3000`，而后端实际运行在 `127.0.0.1:8000`。
解决方法
　　给 Axios 设置 `baseURL`，或者在 `next.config.js` 里配置 `rewrites` 代理。
---
6. `node` / `npm` 命令找不到
原因
　　没有安装 Node.js，或者环境变量没有配置好。
解决方法
　　安装 Node.js LTS 版本，然后重新打开终端执行：
```bash
node -v
npm -v
```
---
7. PowerShell 不允许执行脚本
现象
　　执行 `Activate.ps1` 或 `start_windows.ps1` 时被系统拦截。
解决方法
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
　　然后重新打开 PowerShell。
---
8. `next-env.d.ts` 缺失导致前端类型错误
解决方法
　　在 `frontend/` 目录下新建文件：
```text
next-env.d.ts
```
　　内容为：
```ts
/// <reference types="next" />
/// <reference types="next/image-types/global" />

// NOTE: This file should not be edited
```
---
9. Pydantic v2 的 `.dict()` 警告
原因
　　项目里部分地方仍然使用旧写法：
```python
obj.dict()
```
解决方法
　　建议替换为：
```python
obj.model_dump()
```
　　虽然不一定立刻导致程序崩溃，但从兼容性角度应尽早替换。
---
开发建议
　　如果你准备继续维护这个项目，而不是只做一次演示，建议你做以下改进：
　　1. 统一依赖文件  
　　把 `fastapi`、`uvicorn`、`pydantic` 等后端依赖正式写入 `requirements.txt`，避免每次手动补装。
　　2. 增加前端 API 配置层  
　　不要在页面组件中直接写死 `axios.get('http://127.0.0.1:8000/...')`，建议统一封装一个 `api.ts`。
　　3. 增加 `.env` 文件  
　　将后端地址、前端端口等信息抽到环境变量中，便于开发/生产切换。
　　4. 增加 CI/CD 与测试  
　　后端建议添加 `pytest`，前端建议添加 `Jest` / `Playwright`，并通过 GitHub Actions 自动化测试。
　　5. 补齐正式数据源接入  
　　当前后端主要使用合成数据和演示逻辑，后续如需实用化，需要接入真实行情、基金持仓、新闻与 OCR 数据源。
---
开发者说明
　　当前压缩包更接近“可演示的工程骨架 + 核心页面原型 + 后端接口逻辑”，适合用于：
作品集展示
投研工具原型验证
前后端协同开发模板
继续迭代成完整系统的基础工程
　　如果你的目标是“直接商用”或者“长期稳定部署”，那么还需要继续补充：
完整数据库模型
用户认证与权限
异步任务队列
正式数据源
更严格的异常处理与测试覆盖
---
许可证与说明
　　当前仓库主要用于学习、演示与研究目的。若你接入真实数据源或准备对外部署，请自行确认数据授权、接口许可与相关法律合规要求。
---
最后说明
　　如果你当前的运行环境是 Windows + PyCharm，请记住最关键的三点：
　　第一，创建虚拟环境用：
```powershell
python -m venv .venv
```
　　第二，激活虚拟环境用：
```powershell
.venv\Scripts\activate
```
　　第三，不要在 PowerShell 里写：
```bash
source .venv/bin/activate
python3 -m venv .venv
```
　　因为这两条是 Linux/macOS 的命令，不适用于 Windows。
　　如果你先把后端启动成功，再把前端启动成功，最后处理好前端到后端的请求转发，那么这个项目就可以在浏览器端看到完整效果。
