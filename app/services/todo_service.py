import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.todo import TodoCreate, TodoUpdate
from app.services.protocol import TodoRepositoryProto
from utils import errors


class TodoService:
    def __init__(self, repo: TodoRepositoryProto, session: AsyncSession):
        self.repo = repo
        self.session = session

    async def create_task(self, data: TodoCreate, user_id: uuid.UUID):
        clean_title = data.title.strip()
        if clean_title == "":
            raise errors.ValidationError("Title cannot be empty")
        
        existing = await self.repo.get_by_title(title=clean_title, user_id=user_id)
        if existing:
            raise errors.ConflictError(f"task with title '{existing.title}' already exists")
        
        data.title = clean_title
        todo = await self.repo.create(data, user_id)
        await self.session.commit()
        await self.session.refresh(todo)
        return todo

    async def get_task(self, todo_id: int, user_id: uuid.UUID):
        if todo_id <= 0:
            raise errors.ValidationError("ID must be positive")
        task = await self.repo.get_by_id(todo_id, user_id)
        if not task:
            raise errors.NotFoundError(f"Task {todo_id} not found")
        return task

    async def list_tasks(self, skip: int = 0, limit: int = 10, user_id: uuid.UUID = None):
        if skip < 0 or limit <= 0:
            raise errors.ValidationError("Skip must be non-negative and limit must be positive")
        if user_id is None:
            raise errors.ValidationError("User ID is required")
        safe_limit = min(limit, 100)
        return await self.repo.get_multi(skip=skip, limit=safe_limit, user_id=user_id)

    async def update_task(self, todo_id: int, data: TodoUpdate, user_id: uuid.UUID):
        task = await self.get_task(todo_id, user_id)
        
        if data.title is not None:
            clean_title = data.title.strip()
            if clean_title == "":
                raise errors.ValidationError("Title cannot be empty")
            
            existing = await self.repo.get_by_title(title=clean_title, user_id=user_id)
            if existing and existing.id != todo_id:
                raise errors.ConflictError(f"A task with {existing.title} already exists")
            data.title = clean_title
            
        if data.description is not None:
            clean_description = data.description.strip()
            if len(clean_description) > 500:
                raise errors.ValidationError("Description cannot be longer than 500 characters")
            data.description = clean_description
            
        updated_task = await self.repo.update(task, data)
        await self.session.commit()
        return updated_task
     
    async def remove_task(self, todo_id: int, user_id: uuid.UUID):
        task = await self.get_task(todo_id, user_id)
        await self.repo.delete(task)
        await self.session.commit()
        return {"message": f"Task {todo_id} deleted successfully"}