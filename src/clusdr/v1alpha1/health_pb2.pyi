from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class HealthRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthResponse(_message.Message):
    __slots__ = ("node_id", "cluster_id", "role", "healthy")
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    CLUSTER_ID_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    HEALTHY_FIELD_NUMBER: _ClassVar[int]
    node_id: str
    cluster_id: str
    role: str
    healthy: bool
    def __init__(self, node_id: _Optional[str] = ..., cluster_id: _Optional[str] = ..., role: _Optional[str] = ..., healthy: _Optional[bool] = ...) -> None: ...
