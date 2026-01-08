import os

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, create_engine, Session, select
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DB_URL")

app = FastAPI()

if not DATABASE_URL:
    raise RuntimeError("DB_URL is not set in environment variables")

engine = create_engine(DATABASE_URL, echo=True)


#DB Structure/Tables + same used at API level
class Todo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = Field(default=None)


def get_session():
    with Session(engine) as session:
        yield session


@app.post("/createTodo")
def create_todo(todo: Todo, session: Session = Depends(get_session)):
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


@app.get("/allTodo")
def all_todo(session: Session = Depends(get_session)):
    todos = session.exec(select(Todo)).all()
    return todos


@app.get("/todo/{todo_id}")
def todo_by_id(todo_id: int, session: Session = Depends(get_session)):
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


class TodoUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


@app.put("/todo/{todo_id}")
def update_todo(todo_id: int, todo_update: TodoUpdate, session: Session = Depends(get_session)):
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if todo_update.title is not None:
        todo.title = todo_update.title
    if todo_update.description is not None:
        todo.description = todo_update.description
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


@app.delete("/todo/{todo_id}")
def delete_todo(todo_id: int, session: Session = Depends(get_session)):
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    session.delete(todo)
    session.commit()
    return {"message": "Todo deleted successfully"}



# class CreateTodo(BaseModel):
#     title: str
#     description: str | None
#     status: str

# class UpdateTodo(BaseModel):
#     title: str
#     description: str | None
#     status: str









# def create_tables():
#     print("Trying to create tables")
#     SQLModel.metadata.create_all(engine)
#     print("Table Function Completed")


# create_tables() 