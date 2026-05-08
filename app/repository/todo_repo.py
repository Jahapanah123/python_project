import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoUpdate


class TodoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, obj_in: TodoCreate, user_id: uuid.UUID) -> Todo:
        db_obj = Todo(
            **obj_in.model_dump(),
            user_id=user_id,
        )

        self.db.add(db_obj)

        await self.db.commit()
        await self.db.refresh(db_obj)

        return db_obj

    async def get_by_id(
        self,
        todo_id: int,
        user_id: uuid.UUID,
    ) -> Todo | None:

        result = await self.db.execute(
            select(Todo).where(
                Todo.id == todo_id,
                Todo.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_multi(
        self,
        skip: int,
        limit: int,
        user_id: uuid.UUID,
    ) -> list[Todo]:

        result = await self.db.execute(
            select(Todo)
            .where(Todo.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def get_by_title(
        self,
        title: str,
        user_id: uuid.UUID,
    ) -> Todo | None:

        result = await self.db.execute(
            select(Todo).where(
                Todo.title == title,
                Todo.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def update(
        self,
        db_obj: Todo,
        obj_in: TodoUpdate,
    ) -> Todo:

        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await self.db.commit()
        await self.db.refresh(db_obj)

        return db_obj

    async def delete(self, db_obj: Todo) -> None:
        await self.db.delete(db_obj)
        await self.db.commit()

    async def mark_completed(
        self,
        todo_id: int,
        user_id: uuid.UUID,
    ) -> Todo | None:

        todo = await self.get_by_id(todo_id, user_id)

        if not todo:
            return None

        todo.is_completed = True

        await self.db.commit()
        await self.db.refresh(todo)

        return todo