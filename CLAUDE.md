# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RAG-ST is a full-stack **Retrieval-Augmented Generation (RAG)** application with:
- **Backend**: FastAPI-based REST API with async-first architecture
- **Frontend**: Next.js 14 application with TypeScript, Redux Toolkit, and Ant Design

## Working with Claude Code

### Package Management Rules

**⚠️ IMPORTANT: When `npm install` or `uv sync` is needed, PAUSE and let the user run these commands locally.**

Due to sandbox restrictions:
- ❌ Do NOT run `npm install` or `uv sync` commands - they will fail with network errors
- ❌ Do NOT attempt to start dev servers in background - port binding is blocked
- ✅ DO provide the exact commands needed for the user to run
- ✅ DO continue with all other development work (code changes, builds, etc.)

**Example workflow:**
```bash
# When you need to install packages, provide the command like this:
# User should run:
# npm install lucide-react react-syntax-highlighter @types/react-syntax-highlighter
```

After providing the command, wait for the user to confirm installation is complete before proceeding with tasks that require those packages.

### What Works in Sandbox

- ✅ Read/write files in working directory
- ✅ Run builds (`npm run build`, `uv run python -m ...`)
- ✅ Git operations
- ✅ Most code editing and refactoring
- ✅ Type checking and linting

### What Requires User Action

- 🚫 `npm install` / `npm add` / `npm uninstall`
- 🚫 `uv sync` / `uv add` / `uv remove`
- 🚫 Starting dev servers (`npm run dev`, `uvicorn`)
- 🚫 Operations requiring network ports

## Development Commands

### Backend (FastAPI)

Uses `uv` as the package manager:
```bash
# Install dependencies
uv sync

# Run development server with hot reload
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Initialize database and create test user (admin/admin123)
uv run python -m backend.init_db
```

### Frontend (Next.js)

```bash
cd front

# Install dependencies
npm install

# Run development server (http://localhost:3000)
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Architecture

### Backend Structure

```
backend/
├── main.py                 # FastAPI app entry point
├── init_db.py              # Database initialization
├── common/                 # Shared utilities
│   ├── base_router.py      # Custom API router with auth
│   ├── context.py          # Request context management (contextvars)
│   ├── entity/             # Pydantic schemas
│   ├── middlewares/        # Custom middleware
│   ├── orm/                # Database ORM base classes
│   └── utils.py            # Shared utilities
├── models/                 # SQLAlchemy models
├── router/web/             # API endpoints (user management)
└── services/               # Business logic layer
```

#### Key Backend Patterns
Only GET and POST are allowed; use POST for any updates or deletions. Avoid path parameters whenever possible.

**Custom Router (`common/base_router.py`)**
- `ApiRouter` extends FastAPI's `APIRouter` with built-in authentication
- All routes require JWT authentication by default
- Use `ApiRouter(auth=False)` for public routers
- Use `dependencies=NO_AUTH` for individual public routes
- Automatically initializes `RequestContext` with database session

**ORM Mixins (`common/orm/base_model.py`)**
All models inherit from:
- `Base` - SQLAlchemy declarative base
- `TimestampMixin` - Adds `id` and `create_time` fields
- `BaseModelMixin` - Provides CRUD class methods: `create()`, `get_by_id()`, `get_all()`, `get_by_filter()`, `update_by_id()`, `delete_by_id()`, `count()`, `exists()`

**⚠️ CRITICAL: Session Commit Rules**

`BaseModelMixin` methods **only call `flush()`, NOT `commit()`**. You MUST manually commit after updates:

```python
# ❌ WRONG - Changes won't be saved!
await User.update_by_id(user_id, username="new_name")

# ✅ CORRECT - Always commit after update_by_id
async with use_test_session(session):
    await User.update_by_id(user_id, username="new_name")
    await session.commit()  # REQUIRED!
```

**Background/Async Tasks**:
Async tasks (like `asyncio.create_task()`) run without request context. Create their own session:

```python
async def background_task(document_id: int):
    from common.orm.db import AsyncSessionLocal
    from common import use_test_session

    async with AsyncSessionLocal() as session:
        try:
            async with use_test_session(session):
                await Document.update_by_id(document_id, progress=50)
                await session.commit()  # REQUIRED after each update!
        finally:
            await session.close()
```

See `backend/services/document_service.py:_process_document_async` for a complete example.

**Request Context (`common/context.py`)**
- Uses `contextvars` for request-scoped data
- `RequestContext` stores session, user_id, path, method
- Models access database session via `BaseModelMixin.get_session()`
- `use_test_session(session)` - Context manager for test scripts

**Test Scripts Session Pattern**

All test scripts MUST be in the `backend/` directory and use the correct session pattern:

```python
# In backend/test_xxx.py
from common.orm.db import AsyncSessionLocal
from common import use_test_session

async def test_something():
    async with AsyncSessionLocal() as session:
        try:
            async with use_test_session(session):
                user = await User.create(username="test")
                await session.commit()  # Required after create

                user = await User.get_by_id(user.id)

                await User.update_by_id(user.id, username="updated")
                await session.commit()  # Required after update_by_id!
        finally:
            await session.close()
```

**Key points:**
- Test scripts should live in `backend/` directory
- Use `AsyncSessionLocal()` to create sessions
- Always wrap model operations with `use_test_session(session)`
- **CRITICAL**: Call `await session.commit()` after `create()`, `update_by_id()`, `delete_by_id()`
- Always close the session in `finally` block
- Check `backend/test_document_processing.py` for a complete example

**JSON Handling**
Always use `orjson` for JSON operations:
```python
import orjson
orjson.dumps(obj, option=orjson.OPT_NON_STR_KEYS).decode('utf-8')
orjson.loads(body)
```

### Frontend Structure

```
front/src/
├── app/                    # Next.js App Router
│   ├── (auth)/login/       # Login page (public route)
│   ├── dashboard/          # Protected dashboard routes
│   │   ├── page.tsx        # Dashboard home
│   │   ├── layout.tsx      # Shared dashboard layout
│   │   ├── chat/           # Chat interface
│   │   ├── knowledge-bases/ # Knowledge base management
│   │   └── profile/        # User profile
│   ├── layout.tsx          # Root layout with providers
│   ├── providers.tsx       # Redux + Ant Design providers
│   ├── middleware.ts       # Route protection middleware
│   └── page.tsx            # Home page (redirects based on auth)
├── components/
│   ├── auth/               # ProtectedRoute component
│   ├── chat/               # ChatInterface, MessageBubble, ChatInput
│   ├── document/           # DocumentUpload, DocumentCard
│   ├── knowledge-base/     # KnowledgeBaseCard, CreateModal
│   └── layout/             # AppSidebar, AppHeader
├── lib/
│   ├── api/                # API client with mock support
│   ├── hooks/              # Custom React hooks
│   ├── store/              # Redux store configuration
│   │   ├── store.ts        # Store config (no JSX)
│   │   ├── StoreProvider.tsx # JSX component
│   │   └── slices/         # Redux slices
│   ├── types/              # TypeScript type definitions
│   └── utils/              # Token management, utilities
└── middleware.ts           # Next.js middleware for auth
```

#### Key Frontend Patterns

**Redux Toolkit Setup**
- Store configuration split into `store.ts` (no JSX) and `StoreProvider.tsx` (JSX)
- Main slices: `authSlice`, `knowledgeBaseSlice`, `chatSlice`
- Serializable check ignores chat message actions

**Custom Hooks**
- `useAuth()` - Authentication state and actions
- `useChat()` - Chat with streaming responses
- `useKnowledgeBases()` - Knowledge base CRUD
- `useDocuments()` - Document management

**API Client**
- Axios-based with request/response interceptors
- Auto-injects JWT token from localStorage
- Mock API support via `NEXT_PUBLIC_USE_MOCK_API` environment variable
- Streaming chat using async generators

**File Naming Convention**
- Files with JSX must use `.tsx` extension
- Files without JSX use `.ts` extension

**Route Structure**
- `dashboard/` folder (not `(dashboard)`) - routes appear in URL
- All dashboard routes are protected by middleware
- Routes: `/dashboard`, `/dashboard/knowledge-bases`, `/dashboard/chat`, `/dashboard/profile`

### Backend API Response Format

All endpoints return `BaseResponse[T]`:
```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### Frontend Environment Variables

`front/.env.local`:
- `NEXT_PUBLIC_API_URL` - Backend API URL (default: `http://localhost:8000`)
- `NEXT_PUBLIC_USE_MOCK_API` - Use mock API responses (default: `true`)

## Adding New Features

### Backend: Adding a New Model

1. **Create Model** in `models/`:
```python
from common.orm.base_model import Base, TimestampMixin, BaseModelMixin

class MyModel(Base, TimestampMixin, BaseModelMixin):
    __tablename__ = "my_model"
    name: Mapped[str] = mapped_column(String(100))
    # ... other fields
```

2. **Create Schemas** in `common/entity/schemas/`:
```python
class MyModelCreateRequest(BaseModel):
    name: str

class MyModelResponse(BaseModel):
    id: int
    name: str
    create_time: datetime
```

3. **Create Service** in `services/`:
```python
class MyModelService:
    @staticmethod
    async def create(data: MyModelCreateRequest) -> MyModelResponse:
        instance = await MyModel.create(**data.dict())
        return MyModelResponse.from_orm(instance)
```

4. **Create Router** in `router/web/`:
```python
from common.base_router import ApiRouter, NO_AUTH

router = ApiRouter(prefix="/api/v1/my-model", tags=["my-model"])

@router.post("", response_model=BaseResponse[MyModelResponse], dependencies=NO_AUTH)
async def create_item(request: MyModelCreateRequest):
    result = await MyModelService.create(request)
    return BaseResponse(code=0, message="success", data=result)
```

5. **Register Router** in `router/__init__.py` and `main.py`

### Frontend: Adding a New Page

1. **Create Page** in `app/dashboard/feature-name/page.tsx`:
```tsx
'use client';

export default function FeaturePage() {
  return <div>Feature Content</div>;
}
```

2. **Add Navigation Item** in `components/layout/AppSidebar.tsx`:
```tsx
const menuItems = [
  // ...
  { key: '/dashboard/feature-name', icon: <Icon />, label: 'Feature Name' },
];
```

3. **Create API Client** in `lib/api/feature.ts`:
```typescript
export const featureApi = {
  list: async () => apiClient.get<BaseResponse<Item[]>>('/api/v1/feature'),
  // ... other methods
};
```

## Configuration

### Backend Environment Variables
- `DATABASE_URL` - SQLite database path (default: `sqlite+aiosqlite:///./app.db`)
- `JWT_SECRET` - JWT signing secret
- `JWT_ALGORITHM` - JWT algorithm (default: `HS256`)
- `DEBUG` - Enable debug mode and SQL logging

### Frontend Environment Variables
- `NEXT_PUBLIC_API_URL` - Backend API URL (default: `http://localhost:8000`)
- `NEXT_PUBLIC_USE_MOCK_API` - Use mock API (default: `true`)

## Current Implementation Status

**Implemented:**
- ✅ User authentication (login, logout, profile)
- ✅ JWT-based authentication
- ✅ Frontend dashboard layout
- ✅ Chat interface with Socket.IO streaming
- ✅ Knowledge base management (CRUD with Chroma vector DB)
- ✅ Document management (upload, process, vectorize)
- ✅ RAG chat with Ollama (qwen2.5:7b)
- ✅ Embedding with Ollama (nomic-embed-text)

**Not Yet Implemented:**
- ❌ Milvus vector database (use Chroma for now)

## Important Rules

### SQLAlchemy Models

**NEVER use `relationship()` or import other models in model files.** This causes circular import issues.

- ❌ Don't do this:
```python
from models.document import Document

class KnowledgeBase(Base):
    documents: Mapped[list["Document"]] = relationship("Document", ...)
```

- ✅ Instead, if you need to join with other tables, use raw SQL or explicit queries in the service layer:
```python
# In service layer
from models.document import Document
from models.knowledge_base import KnowledgeBase

stmt = select(KnowledgeBase).join(Document, KnowledgeBase.id == Document.knowledge_base_id)
```

**Model files should only import from:**
- `sqlalchemy.orm` (Mapped, mapped_column)
- `sqlalchemy` (types like String, Integer, Text, ForeignKey, select, func)
- `typing` (Optional, TYPE_CHECKING)
- `common.orm` (Base, TimestampMixin, BaseModelMixin)
- `common.config` (if needed)

**All cross-model queries must be done in the service layer, not in the model itself.**

### Import Statement Rules

**All import statements should be at the top of the file, unless encountering circular dependencies.**

- ✅ Standard practice - imports at the top:
```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from common.orm.base_model import Base, TimestampMixin

class MyModel(Base, TimestampMixin):
    pass
```

- ⚠️ Exception - local imports for circular dependencies:
```python
# Only use local imports when necessary to avoid circular imports
async def some_function():
    from models.other_model import OtherModel  # Local import
    # ... use OtherModel
```

**When to use local imports:**
- Breaking circular dependencies between modules
- Lazy imports in async functions to avoid startup overhead (rare)
- Type hints inside `if TYPE_CHECKING:` blocks

**Otherwise, always keep imports at the top of the file for better readability and performance.**
