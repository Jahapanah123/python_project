from fastapi import FastAPI

from app.api.auth_handler import router as auth_router
from app.api.todo_handler import router as todo_router


app = FastAPI(title="Todo API")


app.include_router(auth_router)
app.include_router(todo_router)



@app.get("/")
def health_check():
    return {"status": "API is running!"}