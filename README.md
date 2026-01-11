# RAG-ST

个人知识库应用，基于 RAG（检索增强生成）技术实现智能问答。

> 使用 Claude Code 编程开发

## 技术栈

**后端**
- FastAPI + SQLAlchemy
- Chroma 向量数据库
- Ollama (qwen2.5:7b / nomic-embed-text)

**前端**
- Next.js 14 + TypeScript
- Redux Toolkit + Ant Design
- Socket.IO 流式响应

## 快速开始

```bash
# 后端（需要 Ollama 服务运行中）
uv sync
uv run python -m backend.init_db  # 初始化数据库 (admin/admin123)
uv run uvicorn backend.main:app --reload --port 8000

# 前端
cd front
npm install
npm run dev
```

访问 http://localhost:3000

## 功能

- 知识库管理（CRUD）
- 文档上传与向量化
- RAG 智能问答（流式响应）

详细文档见 [CLAUDE.md](./CLAUDE.md)
