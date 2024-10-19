from typing import List, Optional

from pydantic import BaseModel, Field
from uuid import UUID


# То, что пользователь присылает для создания
class WannaCreateItem(BaseModel):
    name: str = Field(..., min_length=1, description="Name must be a non-empty string")
    price: float = Field(..., ge=0, description="Price must be a non-negative value")


# Модель для хранения товара
class Item(BaseModel):
    id: UUID
    name: str
    price: float
    deleted: bool = False


# Модель корзины с товарами
class Cart(BaseModel):
    id: UUID
    items: List[UUID] = Field(default_factory=list)


# Товар, который лежит в корзине
class CartInItem(BaseModel):
    id: UUID
    name: str
    quantity: int
    available: bool


# Модель корзины для ответа о корзине
class CartAnswerList(BaseModel):
    id: UUID
    items: List[CartInItem]
    price: float


# Класс на обновление
class UpdateItem(BaseModel):
    name: Optional[str] = Field(None, min_length=1, description="Name must be a non-empty string")
    price: Optional[float] = Field(None, ge=0, description="Price must be a non-negative value")

    class Config:
        extra = "forbid"
