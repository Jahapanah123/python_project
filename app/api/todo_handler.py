from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.queue.email_publisher import EmailPublisher
from app.repository.todo_repo import TodoRepository
from app.schemas.todo import TodoCreate, TodoUpdate
from app.services.todo_service import TodoService
from utils import errors


router = APIRouter(prefix="/todos", tags=["Todos"])


def get_email_publisher() -> EmailPublisher:
    return EmailPublisher()


def get_todo_service(
    db: AsyncSession = Depends(get_db),
    email_publisher: EmailPublisher = Depends(get_email_publisher),
) -> TodoService:
    repo = TodoRepository(db)
    return TodoService(repo, email_publisher)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_todo(
    payload: TodoCreate,
    current_user: User = Depends(get_current_user),
    service: TodoService = Depends(get_todo_service),
):
    try:
        return await service.create_todo(payload, current_user.id)
    except errors.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except errors.ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/{todo_id}")
async def read_todo(
    todo_id: int,
    current_user: User = Depends(get_current_user),
    service: TodoService = Depends(get_todo_service),
):
    try:
        return await service.get_task(todo_id, current_user.id)
    except errors.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except errors.NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/")
async def read_todos(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    service: TodoService = Depends(get_todo_service),
):
    try:
        return await service.list_tasks(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
        )
    except errors.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{todo_id}")
async def update_todo(
    todo_id: int,
    payload: TodoUpdate,
    current_user: User = Depends(get_current_user),
    service: TodoService = Depends(get_todo_service),
):
    try:
        return await service.update_task(todo_id, payload, current_user.id)
    except errors.NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except errors.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except errors.ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{todo_id}", status_code=status.HTTP_200_OK)
async def delete_todo(
    todo_id: int,
    current_user: User = Depends(get_current_user),
    service: TodoService = Depends(get_todo_service),
):
    try:
        return await service.remove_task(todo_id, current_user.id)
    except errors.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except errors.NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{todo_id}/complete", status_code=status.HTTP_200_OK)
async def complete_todo(
    todo_id: int,
    current_user: User = Depends(get_current_user),
    service: TodoService = Depends(get_todo_service),
):
    print("CUrrent user:", current_user.id, current_user.email)
    try:
        return await service.complete_todo(
            todo_id=todo_id,
            user_id=current_user.id,
            user_email=current_user.email,
        )
    except errors.NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))