from datetime import datetime
from typing import Optional, List
from models.base import (
    SuccessResponse,
    ListData,
)
from pydantic import (
    BaseModel,
    Field
)


class BaseUser(BaseModel):
    id: int = 0
    en: Optional[bool]
    name: Optional[str] = ''
    email: Optional[str] = ''
    ctime: Optional[datetime] = Field(None, nullable=True)
    atime: Optional[datetime] = Field(None, nullable=True)
    dtime: Optional[datetime] = Field(None, nullable=True)

    @property
    def is_authenticated(self):
        return bool(self.id)


class Anonymous(BaseUser):
    pass


class User(BaseUser):
    pass


class NewUser(BaseModel):
    en: Optional[bool]
    name: Optional[str]
    email: Optional[str]
    atime: Optional[datetime]
    dtime: Optional[datetime]


class UsersListData(ListData):
    items: List[User] = []


class UsersSuccessResponse(SuccessResponse):
    data: User


class UsersListSuccessResponse(SuccessResponse):
    data: UsersListData


class UsersRatingGist(BaseModel):
    x: int
    y: int


class UsersRatingGistSuccessResponse(SuccessResponse):
    data: List[UsersRatingGist]
