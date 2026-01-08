# Pydantic Models in FastAPI

## Table of Contents
- [Basic Models](#basic-models)
- [Field Validation](#field-validation)
- [Nested Models](#nested-models)
- [Model Inheritance](#model-inheritance)
- [Model Config](#model-config)
- [Custom Validators](#custom-validators)
- [Computed Fields](#computed-fields)
- [Common Patterns](#common-patterns)

---

## Basic Models

```python
from pydantic import BaseModel
from datetime import datetime

class User(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool = True
    created_at: datetime | None = None
```

---

## Field Validation

```python
from pydantic import BaseModel, Field, EmailStr

class User(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)
    email: EmailStr
    password: str = Field(min_length=8)
    tags: list[str] = Field(default_factory=list)

    # With descriptions (shown in OpenAPI docs)
    bio: str = Field(
        default="",
        max_length=500,
        description="User biography",
        examples=["Software developer from NYC"]
    )

# Numeric constraints
price: float = Field(gt=0)           # greater than
rating: int = Field(ge=1, le=5)      # between 1-5
discount: float = Field(ge=0, lt=1)  # 0 to <1

# String constraints
code: str = Field(pattern=r"^[A-Z]{3}$")  # regex
```

---

## Nested Models

```python
from pydantic import BaseModel

class Address(BaseModel):
    street: str
    city: str
    country: str
    zip_code: str

class User(BaseModel):
    name: str
    address: Address
    tags: list[str] = []

# Usage
user = User(
    name="John",
    address={"street": "123 Main", "city": "NYC", "country": "USA", "zip_code": "10001"},
    tags=["admin", "verified"]
)
```

---

## Model Inheritance

```python
from pydantic import BaseModel

# Base with common fields
class ItemBase(BaseModel):
    name: str
    description: str | None = None
    price: float

# For creation (no ID yet)
class ItemCreate(ItemBase):
    pass

# For updates (all optional)
class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None

# For responses (includes ID)
class Item(ItemBase):
    id: int

    model_config = {"from_attributes": True}  # For ORM
```

---

## Model Config

```python
from pydantic import BaseModel, ConfigDict

class User(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,     # Strip whitespace
        str_min_length=1,              # No empty strings
        from_attributes=True,          # ORM mode (SQLAlchemy)
        extra="forbid",                # Error on extra fields
        # extra="ignore",              # Ignore extra fields
        populate_by_name=True,         # Allow field aliases
        use_enum_values=True,          # Use enum values not names
    )

    id: int
    name: str
```

---

## Custom Validators

```python
from pydantic import BaseModel, field_validator, model_validator

class User(BaseModel):
    name: str
    password: str
    password_confirm: str

    # Single field validator
    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.title()

    # Multiple fields
    @field_validator("password", "password_confirm")
    @classmethod
    def passwords_not_empty(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    # Model-level validation (access all fields)
    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self
```

---

## Computed Fields

```python
from pydantic import BaseModel, computed_field

class Rectangle(BaseModel):
    width: float
    height: float

    @computed_field
    @property
    def area(self) -> float:
        return self.width * self.height

r = Rectangle(width=3, height=4)
print(r.area)  # 12.0
print(r.model_dump())  # {"width": 3, "height": 4, "area": 12.0}
```

---

## Common Patterns

### Request/Response separation
```python
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    # No password in response

    model_config = {"from_attributes": True}
```

### Partial updates (PATCH)
```python
class ItemUpdate(BaseModel):
    name: str | None = None
    price: float | None = None

@app.patch("/items/{id}")
def update_item(id: int, item: ItemUpdate):
    stored = get_item(id)
    update_data = item.model_dump(exclude_unset=True)
    updated = stored.model_copy(update=update_data)
    return save_item(id, updated)
```

### Generic response wrapper
```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class Response(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    message: str = ""

@app.get("/users/{id}", response_model=Response[User])
def get_user(id: int):
    user = find_user(id)
    return Response(success=True, data=user)
```
