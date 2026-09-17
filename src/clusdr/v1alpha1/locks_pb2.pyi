from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class LockRequest(_message.Message):
    __slots__ = ("name", "holder", "ttl_ms")
    NAME_FIELD_NUMBER: _ClassVar[int]
    HOLDER_FIELD_NUMBER: _ClassVar[int]
    TTL_MS_FIELD_NUMBER: _ClassVar[int]
    name: str
    holder: str
    ttl_ms: int
    def __init__(self, name: _Optional[str] = ..., holder: _Optional[str] = ..., ttl_ms: _Optional[int] = ...) -> None: ...

class LockResponse(_message.Message):
    __slots__ = ("acquired", "message", "fencing_token", "holder", "deadline_unix_ms")
    ACQUIRED_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    FENCING_TOKEN_FIELD_NUMBER: _ClassVar[int]
    HOLDER_FIELD_NUMBER: _ClassVar[int]
    DEADLINE_UNIX_MS_FIELD_NUMBER: _ClassVar[int]
    acquired: bool
    message: str
    fencing_token: int
    holder: str
    deadline_unix_ms: int
    def __init__(self, acquired: _Optional[bool] = ..., message: _Optional[str] = ..., fencing_token: _Optional[int] = ..., holder: _Optional[str] = ..., deadline_unix_ms: _Optional[int] = ...) -> None: ...

class TryLockRequest(_message.Message):
    __slots__ = ("name", "holder", "ttl_ms")
    NAME_FIELD_NUMBER: _ClassVar[int]
    HOLDER_FIELD_NUMBER: _ClassVar[int]
    TTL_MS_FIELD_NUMBER: _ClassVar[int]
    name: str
    holder: str
    ttl_ms: int
    def __init__(self, name: _Optional[str] = ..., holder: _Optional[str] = ..., ttl_ms: _Optional[int] = ...) -> None: ...

class TryLockResponse(_message.Message):
    __slots__ = ("acquired", "message", "fencing_token", "holder", "deadline_unix_ms")
    ACQUIRED_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    FENCING_TOKEN_FIELD_NUMBER: _ClassVar[int]
    HOLDER_FIELD_NUMBER: _ClassVar[int]
    DEADLINE_UNIX_MS_FIELD_NUMBER: _ClassVar[int]
    acquired: bool
    message: str
    fencing_token: int
    holder: str
    deadline_unix_ms: int
    def __init__(self, acquired: _Optional[bool] = ..., message: _Optional[str] = ..., fencing_token: _Optional[int] = ..., holder: _Optional[str] = ..., deadline_unix_ms: _Optional[int] = ...) -> None: ...

class UnlockRequest(_message.Message):
    __slots__ = ("name", "holder", "fencing_token")
    NAME_FIELD_NUMBER: _ClassVar[int]
    HOLDER_FIELD_NUMBER: _ClassVar[int]
    FENCING_TOKEN_FIELD_NUMBER: _ClassVar[int]
    name: str
    holder: str
    fencing_token: int
    def __init__(self, name: _Optional[str] = ..., holder: _Optional[str] = ..., fencing_token: _Optional[int] = ...) -> None: ...

class UnlockResponse(_message.Message):
    __slots__ = ("released", "message")
    RELEASED_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    released: bool
    message: str
    def __init__(self, released: _Optional[bool] = ..., message: _Optional[str] = ...) -> None: ...

class LockServiceRenewRequest(_message.Message):
    __slots__ = ("name", "holder", "fencing_token", "ttl_ms")
    NAME_FIELD_NUMBER: _ClassVar[int]
    HOLDER_FIELD_NUMBER: _ClassVar[int]
    FENCING_TOKEN_FIELD_NUMBER: _ClassVar[int]
    TTL_MS_FIELD_NUMBER: _ClassVar[int]
    name: str
    holder: str
    fencing_token: int
    ttl_ms: int
    def __init__(self, name: _Optional[str] = ..., holder: _Optional[str] = ..., fencing_token: _Optional[int] = ..., ttl_ms: _Optional[int] = ...) -> None: ...

class LockServiceRenewResponse(_message.Message):
    __slots__ = ("renewed", "message", "fencing_token", "deadline_unix_ms")
    RENEWED_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    FENCING_TOKEN_FIELD_NUMBER: _ClassVar[int]
    DEADLINE_UNIX_MS_FIELD_NUMBER: _ClassVar[int]
    renewed: bool
    message: str
    fencing_token: int
    deadline_unix_ms: int
    def __init__(self, renewed: _Optional[bool] = ..., message: _Optional[str] = ..., fencing_token: _Optional[int] = ..., deadline_unix_ms: _Optional[int] = ...) -> None: ...

class ListLocksRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class LockInfo(_message.Message):
    __slots__ = ("name", "holder", "fencing_token", "acquired_unix_ms", "deadline_unix_ms")
    NAME_FIELD_NUMBER: _ClassVar[int]
    HOLDER_FIELD_NUMBER: _ClassVar[int]
    FENCING_TOKEN_FIELD_NUMBER: _ClassVar[int]
    ACQUIRED_UNIX_MS_FIELD_NUMBER: _ClassVar[int]
    DEADLINE_UNIX_MS_FIELD_NUMBER: _ClassVar[int]
    name: str
    holder: str
    fencing_token: int
    acquired_unix_ms: int
    deadline_unix_ms: int
    def __init__(self, name: _Optional[str] = ..., holder: _Optional[str] = ..., fencing_token: _Optional[int] = ..., acquired_unix_ms: _Optional[int] = ..., deadline_unix_ms: _Optional[int] = ...) -> None: ...

class ListLocksResponse(_message.Message):
    __slots__ = ("locks",)
    LOCKS_FIELD_NUMBER: _ClassVar[int]
    locks: _containers.RepeatedCompositeFieldContainer[LockInfo]
    def __init__(self, locks: _Optional[_Iterable[_Union[LockInfo, _Mapping]]] = ...) -> None: ...
