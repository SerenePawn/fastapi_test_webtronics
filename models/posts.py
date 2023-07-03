from pydantic import (
    BaseModel,
    Field
)
from typing import Optional
from decimal import Decimal
from models.base import SuccessResponse
from datetime import datetime


class Post(BaseModel):
    id: int
    en: bool
    owner_id: int
    name: str
    content: str
    likes: int
    dislikes: int
    ctime: datetime  # creation time
    atime: Optional[datetime]  # updating time
    dtime: Optional[datetime]  # deleting time


class CachedPost(BaseModel):
    id: int
    owner_id: int
    likes: int = 0
    dislikes: int = 0


class NewPost(BaseModel):
    name: str
    content: str


class UpdatePost(BaseModel):
    name: str
    content: str


class PostSuccessResponse(SuccessResponse):
    data: Post


class PostListSuccessResponse(SuccessResponse):
    data: list[Post]  # in production this API needs pagination
