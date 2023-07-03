from typing import (
    Optional,
    List,
    Any,
    Union
)
import enum
from pydantic import BaseModel


class ValidationError(BaseModel):
    field: str
    message: str


class SuccessResponse(BaseModel):
    success: bool = True
    data: Optional[Any]


class ListData(BaseModel):
    total: int
    limit: int
    page: int
    items: List[Any]


class ErrorResponse(BaseModel):
    success: bool = False
    error: Optional[str]
    validation_error: Optional[List[ValidationError]]
    debug: Optional[str]


class UpdateErrorResponse(BaseModel):
    success: bool = False
    errors: List[Any]


class OperatorType(str, enum.Enum):
    EQ = 'eq'
    NEQ = 'neq'
    LT = 'lt'
    LTE = 'lte'
    GT = 'gt'
    GTE = 'gte'
    IN = 'in'
    LIKE = 'like'
    ILIKE = 'ilike'
    ARRAY = 'array'


class Filter(BaseModel):
    field: str
    operator: OperatorType
    value: Any


class OrderType(str, enum.Enum):
    ASC = 'ASC'
    DESC = 'DESC'


class Order(BaseModel):
    field: str
    operator: OrderType


class Lookup(BaseModel):
    limit: Optional[int] = None
    page: Optional[int] = None
    offset: Optional[int] = None
    order: Optional[List[Order]] = None
    filters: List[Filter] = []
