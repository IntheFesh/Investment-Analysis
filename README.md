# Investment-Analysis

该仓库现在包含 **FastAPI 后端 + Next.js 前端** 两个服务，需分别启动。

## 1) 安装依赖

### 后端
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 前端
```bash
cd frontend
npm install
cp .env.example .env.local
```

## 2) 启动服务

### 启动后端（默认 8000）
```bash
source .venv/bin/activate
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

### 启动前端（默认 3000）
```bash
cd frontend
npm run dev
```

## 3) 对接关系

- 前端通过 `NEXT_PUBLIC_API_BASE_URL` 直连后端。
- 本地开发推荐：`NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`。
- 后端 CORS 默认允许 `http://127.0.0.1:3000` 与 `http://localhost:3000`。

## 4) 快速验链路

先直接访问后端 bootstrap 接口：
```bash
curl http://127.0.0.1:8000/api/v1/system/bootstrap
```
看到 JSON 后再打开前端页面：`http://127.0.0.1:3000`。

## 5) 说明

旧的数据分析脚本（`main.py` 等）仍保留用于离线分析；Web 应用以 `backend/` + `frontend/` 为准。
