from typing import Union
from pydantic import BaseModel, field_validator

from swarmauri.standard.messages.concrete.SystemMessage import SystemMessage
from swarmauri.core.agents.IAgentSystemContext import IAgentSystemContext


class AgentSystemContextMixin(IAgentSystemContext, BaseModel):
    system_context:  Union[SystemMessage, str]

    @field_validator('system_context', mode='before')
    def set_system_context(cls, value: Union[str, SystemMessage]) -> SystemMessage:
        if isinstance(value, str):
            return SystemMessage(content=value)
        return value