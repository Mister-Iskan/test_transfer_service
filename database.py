from typing import Any

users_db: dict[int, dict[str, Any]] = {}

balances_db: dict[int, dict[str, float]] = {}


class IDCounter:
    def __init__(self):
        self._user_id = 0
        self._balance_id = 0

    def get_next_user_id(self) -> int:
        self._user_id += 1
        return self._user_id

    def get_next_balance_id(self) -> int:
        self._balance_id += 1
        return self._balance_id


id_counter = IDCounter()
