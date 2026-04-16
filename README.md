# Investment-Analysis

一个面向**投资研究、基金组合分析与情景模拟**的全栈项目。  
前端使用 **Next.js + TypeScript + Tailwind CSS**，后端使用 **FastAPI + Pydantic + Python 科学计算栈**。

---

## 1. 项目简介

`Investment-Analysis` 的目标不是做一个简单的行情展示网页，而是构建一套更接近“研究工作台”的系统。它希望同时解决两类问题：

1. 从**市场、情绪、组合、单基金、情景模拟**等多个维度，对投资对象进行结构化分析。
2. 将分析结果整理为**可继续研究、可汇报、可导出、可交给 AI 进一步处理**的结构化内容。

整个项目采用**前后端分离架构**：

- 前端负责页面展示、交互逻辑、导入导出入口与状态切换。
- 后端负责金融指标计算、组合暴露分析、情景模拟、OCR / CSV 导入解析以及统一 API 输出。

项目设计时强调一条原则：

> 复杂分析逻辑必须放在后端，前端只负责展示。  
> 这样可以避免不同页面、不同组件之间的统计口径不一致。

如果你准备把这个项目作为课程项目、作品集项目、面试项目，或者后续继续扩展的工程基础，建议先完整阅读本文档，再开始运行。

---

## 2. 核心功能

### 2.1 市场总览（Market Overview）

用于回答“今天市场发生了什么”。页面会展示：

- 主要指数
- 板块轮动
- 主力资金流
- 市场广度
- 市场解释摘要

### 2.2 风险情绪（Risk Sentiment）

通过短期和中长期双仪表盘压缩展示市场风险状态，并提供：

- 因子拆解
- 情绪时间序列分析
- 因子贡献说明

### 2.3 基金组合（Portfolio Analysis）

包含三个核心标签：

- 组合看穿
- 组合诊断
- AI 导出

支持展示：

- 组合摘要
- 行业 / 风格 / 市场暴露
- 基金重叠热力图
- 风险偏差与优化建议

### 2.4 单基金研究（Fund Research）

围绕某一只基金输出：

- 基金概览
- 风险收益画像
- 持仓与风格画像
- 与当前组合的关系
- 研究结论

### 2.5 情景模拟（Scenario / Statistical Simulation）

支持：

- 统计模拟
- 情景冲击模拟

输出结果包括：

- 收益分布热力图
- 理论最优 / 最差回报曲线
- 情景敏感度表

### 2.6 导入与设置（Import / Settings）

支持：

- 基金代码导入
- 截图导入
- CSV 导入
- 风险画像设置
- 默认视角设置
- 导出偏好设置

---

## 3. 技术栈

### 3.1 前端

前端主要使用以下技术：

- **Next.js**：用于页面路由和 React 应用构建
- **TypeScript**：提升类型安全性与可维护性
- **Tailwind CSS**：快速构建页面样式
- **React Query**：负责异步请求、缓存与状态管理
- **Axios**：负责向后端发起 HTTP 请求

### 3.2 后端

后端主要使用以下技术：

- **FastAPI**：构建 REST API
- **Pydantic**：进行请求 / 响应数据校验
- **NumPy / Pandas / SciPy**：执行金融分析与模拟计算
- **Uvicorn**：运行 ASGI 服务

> 当前项目更偏向本地开发 / 演示版本。  
> `Redis / Celery / PostgreSQL` 等能力在设计上预留了扩展方向，但压缩包内未完整落地。

---

## 4. 项目结构说明

项目根目录主要结构如下：

```text
Investment-Analysis/
├── backend/                     # FastAPI 后端
│   ├── app.py                   # 后端入口，注册所有 API 路由
│   ├── sample_data.py           # 示例/合成数据，用于本地演示
│   ├── __init__.py
│   └── routers/                 # 各模块 API
│       ├── system.py
│       ├── market.py
│       ├── sentiment.py
│       ├── portfolio.py
│       ├── fund.py
│       ├── simulation.py
│       ├── import_api.py
│       ├── export_api.py
│       └── settings.py
│
├── frontend/                    # Next.js 前端
│   ├── pages/
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
│   ├── components/
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
└── README.md
```

### 4.1 关于目录的额外说明

根目录下的这几个文件：

- `data_collection.py`
- `data_analysis.py`
- `portfolio_optimization.py`
- `visualizations.py`
- `main.py`

更接近**早期分析脚本模块**。真正驱动网页系统的是：

- `backend/`
- `frontend/`

也就是说，如果你的目标是在浏览器中看到页面效果，那么重点不是运行 `main.py`，而是同时启动前后端服务。

---

## 5. 环境要求

### 5.1 Python

推荐版本：

- **Python 3.10**
- **Python 3.11**

不建议使用过低版本，否则可能出现类型语法或依赖兼容性问题。

### 5.2 Node.js

推荐版本：

- **Node.js 18.x** 或 **20.x**
- **npm 9.x** 或以上

> 由于前端是 Next.js 项目，所以必须安装 Node.js。  
> 只安装 Python 不足以运行完整网页。

---

## 6. 运行前环境检测

在真正安装依赖和启动之前，建议先做环境检测。

### 6.1 检查 Python 是否可用

#### Windows（PowerShell / PyCharm Terminal）

```powershell
python --version
pip --version
```

#### Linux / macOS

```bash
python3 --version
pip3 --version
```

如果没有输出版本号，而是提示命令找不到，说明你还没有正确安装 Python，或者没有把 Python 加入环境变量。

### 6.2 检查 Node.js 是否可用

Windows / Linux / macOS 都可以执行：

```bash
node -v
npm -v
```

如果这里报错，说明前端无法启动，你需要先安装 Node.js。

### 6.3 检查当前终端是否已经进入虚拟环境

#### Windows PowerShell

如果已经激活虚拟环境，终端前面通常会出现类似：

```text
(.venv) PS C:\Users\YourName\Desktop\Investment-Analysis>
```

#### Linux / macOS

通常会显示：

```text
(.venv) user@machine:~/Investment-Analysis$
```

如果没有 `(.venv)` 前缀，则说明当前终端还没有进入虚拟环境。

---

## 7. 安装与运行总览

整个项目需要启动 **两个服务**：

1. **后端 FastAPI**：默认运行在 `http://127.0.0.1:8000`
2. **前端 Next.js**：默认运行在 `http://localhost:3000`

你需要同时启动两者，然后在浏览器中访问前端地址，才能看到完整网页效果。

---

## 8. Windows + PyCharm 运行指南

如果你当前环境是：

- Windows
- PyCharm
- PyCharm 自带 Terminal / PowerShell

那么建议严格按下面步骤操作。

### 8.1 用 PyCharm 打开项目

在 PyCharm 中选择：

```text
File -> Open
```

然后打开整个 `Investment-Analysis` 根目录，而不是只打开 `backend` 或 `frontend` 某个子目录。

### 8.2 创建 Python 虚拟环境

你可以用两种方式。

#### 方式 A：用 PyCharm 图形界面创建（推荐）

进入：

```text
File -> Settings -> Project -> Python Interpreter
```

点击右上角齿轮，创建新的虚拟环境，路径建议设置为：

```text
.venv
```

#### 方式 B：用 PyCharm Terminal 手动创建

在项目根目录执行：

```powershell
python -m venv .venv
```

### 8.3 激活虚拟环境

#### Windows PowerShell

```powershell
.venv\Scripts\activate
```

#### Windows CMD

```cmd
.venv\Scripts\activate.bat
```

> **注意**
>
> 在 Windows 下不要写：
>
> ```bash
> source .venv/bin/activate
> ```
>
> 因为这是 Linux / macOS 的命令，在 PowerShell 中会直接报错。
>
> 同样，在 Windows 下不要写：
>
> ```bash
> python3 -m venv .venv
> ```
>
> 因为很多 Windows 环境里默认只有 `python`，没有 `python3`。

### 8.4 安装后端依赖

当前项目的 `requirements.txt` 主要覆盖了早期分析模块，后端运行网页系统还需要额外安装 FastAPI 相关依赖。

建议执行：

```powershell
pip install -r requirements.txt
pip install fastapi uvicorn pydantic python-multipart
```

### 8.5 启动后端

在项目根目录执行：

```powershell
uvicorn backend.app:app --reload --port 8000
```

如果启动成功，可以打开：

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`

其中 `/docs` 是 FastAPI 自动生成的 API 文档页面。

### 8.6 安装前端依赖

打开一个**新的终端标签页**，进入前端目录：

```powershell
cd frontend
npm install
```

### 8.7 补充 Next.js 类型文件（如果缺失）

如果 `frontend` 目录下没有 `next-env.d.ts`，请手动新建该文件，内容如下：

```ts
/// <reference types="next" />
/// <reference types="next/image-types/global" />

// NOTE: This file should not be edited
```

### 8.8 启动前端

在 `frontend` 目录下执行：

```powershell
npm run dev
```

然后在浏览器中访问：

- `http://localhost:3000`

### 8.9 确认前后端联通

如果前端页面可以打开，但页面显示“加载失败”或者浏览器控制台中出现接口 404，那么通常是：

- 前端已经启动
- 后端已经启动
- 但前端请求没有正确转发到后端

当前项目中，前端很多地方直接请求：

```ts
/api/v1/...
```

这意味着请求默认会打到 `localhost:3000`，而不是 `127.0.0.1:8000`。

你需要二选一处理。

#### 方案 A：直接给 Axios 配置后端地址（最简单）

把：

```ts
axios.get('/api/v1/system/bootstrap')
```

改成：

```ts
axios.get('http://127.0.0.1:8000/api/v1/system/bootstrap')
```

其它 `axios.get('/api/v1/...')`、`axios.post('/api/v1/...')` 同理。

#### 方案 B：配置 Next.js 代理转发（更工程化）

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

> 建议本地演示阶段优先使用方案 A，简单直接。

---

## 9. Linux 运行指南

### 9.1 创建虚拟环境

```bash
python3 -m venv .venv
```

### 9.2 激活虚拟环境

```bash
source .venv/bin/activate
```

### 9.3 安装后端依赖

```bash
pip install -r requirements.txt
pip install fastapi uvicorn pydantic python-multipart
```

### 9.4 启动后端

```bash
uvicorn backend.app:app --reload --port 8000
```

### 9.5 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 9.6 打开浏览器

访问：

- `http://localhost:3000`

---

## 10. macOS 运行指南

macOS 的操作和 Linux 基本一致。

### 10.1 创建虚拟环境

```bash
python3 -m venv .venv
```

### 10.2 激活虚拟环境

```bash
source .venv/bin/activate
```

### 10.3 安装后端依赖

```bash
pip install -r requirements.txt
pip install fastapi uvicorn pydantic python-multipart
```

### 10.4 启动后端

```bash
uvicorn backend.app:app --reload --port 8000
```

### 10.5 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 10.6 打开浏览器

访问：

- `http://localhost:3000`

---

## 11. 一键启动脚本

为了减少重复输入命令，下面给出可以直接放进项目根目录的启动脚本。

### 11.1 Windows 一键启动脚本：`start_windows.bat`

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

使用方式：

```cmd
start_windows.bat
```

### 11.2 Windows PowerShell 版本：`start_windows.ps1`

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

### 11.3 Linux / macOS 一键启动脚本：`start_unix.sh`

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

## 12. 常见错误排查

这一节非常重要，因为运行问题大多集中在这里。

### 12.1 `source : 无法将“source”项识别为 cmdlet`

#### 现象

在 Windows PowerShell 中执行：

```bash
source .venv/bin/activate
```

报错找不到 `source`。

#### 原因

`source` 是 Linux / macOS 的 shell 命令，PowerShell 不支持。

#### 解决方法

在 Windows PowerShell 中使用：

```powershell
.venv\Scripts\activate
```

---

### 12.2 `python3 : 无法识别`

#### 现象

在 Windows 中执行：

```bash
python3 -m venv .venv
```

报错。

#### 原因

Windows 默认通常只有 `python` 命令，而没有 `python3`。

#### 解决方法

```powershell
python -m venv .venv
```

---

### 12.3 `pydantic.errors.PydanticUserError: const is removed, use Literal instead`

#### 现象

启动后端时，`simulation.py` 报：

```text
`const` is removed, use `Literal` instead
```

#### 原因

项目代码中使用了 Pydantic v1 的旧写法，而当前环境安装的是 Pydantic v2。

#### 解决方法

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

再把：

```python
mode: str = Field("scenario", const=True)
```

改成：

```python
mode: Literal["scenario"] = "scenario"
```

---

### 12.4 `ModuleNotFoundError: No module named 'fastapi'`

#### 原因

说明你还没有安装 FastAPI。

#### 解决方法

```bash
pip install fastapi uvicorn pydantic python-multipart
```

---

### 12.5 页面能打开，但数据加载失败 / 404

#### 原因

前端请求 `/api/v1/...` 时，请求发给了 `localhost:3000`，而后端实际运行在 `127.0.0.1:8000`。

#### 解决方法

给 Axios 设置 `baseURL`，或者在 `next.config.js` 里配置 `rewrites` 代理。

---

### 12.6 `node` / `npm` 命令找不到

#### 原因

没有安装 Node.js，或者环境变量没有配置好。

#### 解决方法

安装 Node.js LTS 版本，然后重新打开终端执行：

```bash
node -v
npm -v
```

---

### 12.7 PowerShell 不允许执行脚本

#### 现象

执行 `Activate.ps1` 或 `start_windows.ps1` 时被系统拦截。

#### 解决方法

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

然后重新打开 PowerShell。

---

### 12.8 `next-env.d.ts` 缺失导致前端类型错误

#### 解决方法

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

### 12.9 Pydantic v2 的 `.dict()` 警告

#### 原因

项目里部分地方仍然使用旧写法：

```python
obj.dict()
```

#### 解决方法

建议替换为：

```python
obj.model_dump()
```

虽然不一定立刻导致程序崩溃，但从兼容性角度应尽早替换。

---

## 13. 开发建议

如果你准备继续维护这个项目，而不是只做一次演示，建议做以下改进：

### 13.1 统一依赖文件

把 `fastapi`、`uvicorn`、`pydantic` 等后端依赖正式写入 `requirements.txt`，避免每次手动补装。

### 13.2 增加前端 API 配置层

不要在页面组件中直接写死：

```ts
axios.get('http://127.0.0.1:8000/...')
```

建议统一封装一个 `api.ts`。

### 13.3 增加 `.env` 文件

将后端地址、前端端口等信息抽到环境变量中，便于开发 / 生产环境切换。

### 13.4 增加 CI/CD 与测试

- 后端建议添加 `pytest`
- 前端建议添加 `Jest` / `Playwright`
- 通过 GitHub Actions 做自动化测试

### 13.5 补齐正式数据源接入

当前后端主要使用合成数据和演示逻辑，后续如需实用化，需要接入：

- 真实行情
- 基金持仓
- 新闻数据
- OCR 数据源

---

## 14. 开发者说明

当前压缩包更接近于：

- 可演示的工程骨架
- 核心页面原型
- 后端接口逻辑

它适合用于：

- 作品集展示
- 投研工具原型验证
- 前后端协同开发模板
- 继续迭代成完整系统的基础工程

如果你的目标是“直接商用”或者“长期稳定部署”，那么还需要继续补充：

- 完整数据库模型
- 用户认证与权限
- 异步任务队列
- 正式数据源
- 更严格的异常处理与测试覆盖

---

## 15. 许可证与说明

当前仓库主要用于学习、演示与研究目的。  
如果你接入真实数据源或准备对外部署，请自行确认数据授权、接口许可与相关法律合规要求。

---

## 16. 最后说明

如果你当前的运行环境是 **Windows + PyCharm**，请记住最关键的三点：

1. 创建虚拟环境用：

```powershell
python -m venv .venv
```

2. 激活虚拟环境用：

```powershell
.venv\Scripts\activate
```

3. 不要在 PowerShell 里写：

```bash
source .venv/bin/activate
python3 -m venv .venv
```

因为这两条是 Linux / macOS 的命令，不适用于 Windows。

只要你先把后端启动成功，再把前端启动成功，最后处理好前端到后端的请求转发，这个项目就可以在浏览器中看到完整效果。
