from pydantic import BaseModel
from typing import Optional


class ClientInfo(BaseModel):

    client_ip: Optional[str]
    user_agent: Optional[str]
    device_name: Optional[str]