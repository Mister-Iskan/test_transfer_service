import uvicorn
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from database import users_db, balances_db, id_counter

from schemas import UserCreate, UserResponse, TransferObject, BulkUserCreationResponse, SkippedUser
from services import Users, Transfer, BusinessLogicError

app = FastAPI()


@app.post("/users", response_model=BulkUserCreationResponse, status_code=status.HTTP_200_OK)
def create_users(users_to_create: list[UserCreate]):  # Принимаем список
    """
    Создает одного или нескольких пользователей из переданного списка.
    Если пользователь с таким email уже существует, он пропускается.
    Возвращает отчет о созданных и пропущенных пользователях.
    """
    created_users_list = []
    skipped_users_list = []

    existing_emails = {user["email"] for user in users_db.values()}

    for user_data in users_to_create:
        if user_data.email in existing_emails:
            skipped_users_list.append(
                SkippedUser(
                    email=user_data.email,
                    reason="Email already registered."
                )
            )
            continue

        new_user_id = id_counter.get_next_user_id()
        new_balance_id = id_counter.get_next_balance_id()

        balances_db[new_balance_id] = {"balance": user_data.balance}
        users_db[new_user_id] = {
            "name": user_data.name,
            "email": user_data.email,
            "balance_id": new_balance_id
        }

        created_users_list.append(
            UserResponse(
                id=new_user_id,
                name=user_data.name,
                email=user_data.email,
                balance=user_data.balance
            )
        )

        existing_emails.add(user_data.email)

    return BulkUserCreationResponse(
        created_users=created_users_list,
        skipped_users=skipped_users_list
    )


@app.get("/users", response_model=list[UserResponse])
def get_users():
    user_sequence = Users()
    return user_sequence.all()


@app.post("/transfer", status_code=status.HTTP_200_OK)
def make_transfer(transfer_data: TransferObject):
    try:
        transfer_operation = Transfer(transfer_data)
        transfer_operation.execute()
        return {"message": "Transfer successful"}
    except BusinessLogicError as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

