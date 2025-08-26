from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Схема для создания пользователя."""
    name: str
    email: str
    balance: float = Field(..., ge=0)


class UserResponse(BaseModel):
    """Схема для ответа с данными пользователя."""
    id: int
    name: str
    email: str
    balance: float


class TransferObject(BaseModel):
    """Схема для выполнения перевода."""
    from_user_id: int
    to_user_id: int
    amount: float = Field(..., gt=0)


class SkippedUser(BaseModel):
    """Схема для пользователя, который не был создан."""
    email: str
    reason: str


class BulkUserCreationResponse(BaseModel):
    """Схема ответа для пакетного создания пользователей."""
    created_users: list[UserResponse]
    skipped_users: list[SkippedUser]
