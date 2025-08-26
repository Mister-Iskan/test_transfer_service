from abc import ABC, abstractmethod
from typing import Any
from fastapi import status

from schemas import TransferObject, UserResponse
from database import users_db, balances_db


class BusinessLogicError(Exception):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.detail = detail
        self.status_code = status_code
        super().__init__(self.detail)


class Sequence(ABC):
    @abstractmethod
    def all(self) -> list[Any]:
        pass


class Users(Sequence):
    def all(self) -> list[UserResponse]:
        result = []
        for user_id, user_data in users_db.items():
            balance_id = user_data["balance_id"]
            balance = balances_db[balance_id]["balance"]
            result.append(
                UserResponse(
                    id=user_id,
                    name=user_data["name"],
                    email=user_data["email"],
                    balance=balance
                )
            )
        return result


class BusinessRule(ABC):
    @abstractmethod
    def is_broken(self) -> bool:
        pass

    @property
    @abstractmethod
    def error_message(self) -> str:
        pass


class RuleValidator:
    def __init__(self, rules: list[BusinessRule]):
        self.rules = rules

    def check(self):
        for rule in self.rules:
            if rule.is_broken():
                raise BusinessLogicError(detail=rule.error_message)


class SufficientBalanceRule(BusinessRule):
    def __init__(self, from_user_balance: float, amount: float):
        self._from_user_balance = from_user_balance
        self._amount = amount

    def is_broken(self) -> bool:
        return self._from_user_balance < self._amount

    @property
    def error_message(self) -> str:
        return "Insufficient balance on the sender's account."


class CannotTransferToSelfRule(BusinessRule):
    def __init__(self, from_user_id: int, to_user_id: int):
        self._from_user_id = from_user_id
        self._to_user_id = to_user_id

    def is_broken(self) -> bool:
        return self._from_user_id == self._to_user_id

    @property
    def error_message(self) -> str:
        return "Sender and receiver cannot be the same user."


class Transfer:
    def __init__(self, transfer_data: TransferObject):
        self.data = transfer_data

    def _validate(self):
        if self.data.from_user_id not in users_db or self.data.to_user_id not in users_db:
            raise BusinessLogicError(
                detail="One or both users not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        from_user_balance_id = users_db[self.data.from_user_id]["balance_id"]
        from_user_balance = balances_db[from_user_balance_id]["balance"]

        rules_to_check = [
            SufficientBalanceRule(from_user_balance, self.data.amount),
            CannotTransferToSelfRule(self.data.from_user_id, self.data.to_user_id)
        ]
        validator = RuleValidator(rules=rules_to_check)
        validator.check()

    def execute(self):
        self._validate()
        from_balance_id = users_db[self.data.from_user_id]["balance_id"]
        to_balance_id = users_db[self.data.to_user_id]["balance_id"]

        balances_db[from_balance_id]["balance"] -= self.data.amount
        balances_db[to_balance_id]["balance"] += self.data.amount
