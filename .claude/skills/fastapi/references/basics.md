# FastAPI Basics

## Table of Contents
- [Installation](#installation)
- [Hello World](#hello-world)
- [Path Parameters](#path-parameters)
- [Query Parameters](#query-parameters)
- [Request Body](#request-body)
- [HTTP Methods](#http-methods)
- [Response Models](#response-models)
- [Status Codes](#status-codes)

---

## Installation

```bash
pip install "fastapi[standard]"
```

Includes: uvicorn, pydantic, starlette, python-multipart, httpx, jinja2.

For minimal install: `pip install fastapi uvicorn`

---

## Hello World

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}
```

Run: `uvicorn main:app --reload`

---

## Path Parameters

```python
@app.get("/items/{item_id}")
def read_item(item_id: int):  # Auto-validated as int
    return {"item_id": item_id}

# Multiple path params
@app.get("/users/{user_id}/items/{item_id}")
def get_user_item(user_id: int, item_id: str):
    return {"user_id": user_id, "item_id": item_id}

# Enum path params
from enum import Enum

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

@app.get("/models/{model_name}")
def get_model(model_name: ModelName):
    return {"model_name": model_name.value}
```

---

## Query Parameters

```python
# Basic query params (after path params in function)
@app.get("/items")
def read_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}
# URL: /items?skip=0&limit=10

# Optional query params
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}

# Required query params (no default)
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str):  # q is required
    return {"item_id": item_id, "q": q}

# Query param validation
from fastapi import Query

@app.get("/items")
def read_items(
    q: str | None = Query(default=None, min_length=3, max_length=50),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, le=100)
):
    return {"q": q, "skip": skip, "limit": limit}
```

---

## Request Body

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = False

@app.post("/items")
def create_item(item: Item):
    return {"item_name": item.name, "price": item.price}

# Body + path + query
@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item, q: str | None = None):
    result = {"item_id": item_id, **item.model_dump()}
    if q:
        result["q"] = q
    return result
```

---

## HTTP Methods

```python
@app.get("/items")           # Read
@app.post("/items")          # Create
@app.put("/items/{id}")      # Full update
@app.patch("/items/{id}")    # Partial update
@app.delete("/items/{id}")   # Delete
@app.options("/items")       # CORS preflight
@app.head("/items")          # Headers only
```

---

## Response Models

```python
from pydantic import BaseModel

class ItemIn(BaseModel):
    name: str
    price: float
    password: str  # Sensitive

class ItemOut(BaseModel):
    name: str
    price: float
    # password excluded

@app.post("/items", response_model=ItemOut)
def create_item(item: ItemIn):
    return item  # password auto-filtered

# Exclude unset/defaults
@app.get("/items/{id}", response_model=Item, response_model_exclude_unset=True)
def read_item(id: int):
    return items[id]
```

---

## Status Codes

```python
from fastapi import status

@app.post("/items", status_code=status.HTTP_201_CREATED)
def create_item(item: Item):
    return item

@app.delete("/items/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(id: int):
    return None

# Common codes
# 200 OK (default)
# 201 Created
# 204 No Content
# 400 Bad Request
# 401 Unauthorized
# 403 Forbidden
# 404 Not Found
# 422 Unprocessable Entity (validation error)
# 500 Internal Server Error
```
