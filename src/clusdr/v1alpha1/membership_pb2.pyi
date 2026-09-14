from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Member(_message.Message):
    __slots__ = ("id", "address", "status", "leader", "role")
    ID_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    LEADER_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    id: str
    address: str
    status: str
    leader: bool
    role: str
    def __init__(self, id: _Optional[str] = ..., address: _Optional[str] = ..., status: _Optional[str] = ..., leader: _Optional[bool] = ..., role: _Optional[str] = ...) -> None: ...

class ListMembersRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ListMembersResponse(_message.Message):
    __slots__ = ("members",)
    MEMBERS_FIELD_NUMBER: _ClassVar[int]
    members: _containers.RepeatedCompositeFieldContainer[Member]
    def __init__(self, members: _Optional[_Iterable[_Union[Member, _Mapping]]] = ...) -> None: ...

class GetLeaderRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetLeaderResponse(_message.Message):
    __slots__ = ("leader_id", "address")
    LEADER_ID_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    leader_id: str
    address: str
    def __init__(self, leader_id: _Optional[str] = ..., address: _Optional[str] = ...) -> None: ...
