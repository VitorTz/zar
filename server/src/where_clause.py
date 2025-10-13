from typing import Optional, Any, Literal
from asyncpg import Connection


class Clause:

    def __init__(self, key: Optional[Any], clause: str, param: Optional[Any] = None):
        self.key = key
        self.clause = clause
        self.param = param
    

class WhereClauseConstructor:

    def __init__(self, *clauses: Clause):
        self.__clause: list[str] = []
        self.__params: list[Any] = []
        self.__where = ''
        for clause in clauses:
            self.add(clause)
        self.construct()
    
    @property
    def where(self) -> str:
        return self.__where
    
    @property
    def params(self) -> list[Any]:
        return self.__params    
    
    @property
    def params_length(self) -> int:
        return len(self.__params)
    
    async def count(self, query: str, conn: Connection) -> int:
        print(self.params)
        if self.params:
            r = await conn.fetchrow(f"{query} {self.where}", *self.params)
        else:
            r = await conn.fetchrow(f"{query}")
        return dict(r)['total']
    
    def params_extended(self, *params: str) -> list[Any]:
        p = [x for x in self.__params]
        p.extend(params)
        return p
    
    def add(self, clause: Clause):
        if clause.key is not None:
            if clause.param is None: clause.param = clause.key
            self.__clause.append(clause.clause)
            self.__params.append(clause.param)

    def construct(self, gate: Literal['AND', 'OR'] = 'AND') -> None:
        if self.__params:
            self.__clause = [clause.replace("%", f"${i + 1}") for i, clause in enumerate(self.__clause)]
            self.__where = "WHERE " + f" {gate} ".join(self.__clause)
        else:
            self.__where = ''