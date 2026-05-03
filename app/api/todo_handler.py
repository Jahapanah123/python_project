from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.repository.todo_repo import TodoRepository
from app.services.todo_service import TodoService
from app.schemas.todo import TodoCreate, TodoUpdate
from utils import errors

router = APIRouter(prefix="/todos", tags=["Todos"])

# Dependency Injection 
def get_todo_service(db: Session = Depends(get_db)) -> TodoService:
    #Repository ko DB session diya
    repo = TodoRepository(db)
    #  Service ko Repo inject kiya
    return TodoService(repo)

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_todo(payload: TodoCreate, service: TodoService = Depends(get_todo_service)):
    try:
        return service.create_task(payload)
    except errors.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except errors.ConflictError as e: # Catch the specific error raised in service
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/{todo_id}")
def read_todo(todo_id: int, service: TodoService = Depends(get_todo_service)):
    try:
        return service.get_task(todo_id)
    except errors.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except errors.NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/")
def read_todos(skip: int = 0, limit: int = 10, service: TodoService = Depends(get_todo_service)):
    try : 
        return service.list_tasks(skip=skip, limit=limit)
    except errors.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{todo_id}")
def update_todo(todo_id: int, payload: TodoUpdate, service: TodoService = Depends(get_todo_service)):
    try:
        return service.update_task(todo_id, payload)
    except errors.NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except errors.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except errors.ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=500, detail= "internal server error")
    
@router.delete("/{todo_id}", status_code=status.HTTP_200_OK)
def delete_todo(todo_id: int, service: TodoService = Depends(get_todo_service)):
    try:
        service.remove_task(todo_id)
        return{"message": " deleted successfully"}
    except errors.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except errors.NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))