from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GrantLeaseRequest(_message.Message):
    __slots__ = ("name", "owner", "ttl_ms")
    NAME_FIELD_NUMBER: _ClassVar[int]
    OWNER_FIELD_NUMBER: _ClassVar[int]
    TTL_MS_FIELD_NUMBER: _ClassVar[int]
    name: str
    owner: str
    ttl_ms: int
    def __init__(self, name: _Optional[str] = ..., owner: _Optional[str] = ..., ttl_ms: _Optional[int] = ...) -> None: ...

class GrantLeaseResponse(_message.Message):
    __slots__ = ("granted", "message", "fencing_token", "owner", "deadline_unix_ms")
    GRANTED_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    FENCING_TOKEN_FIELD_NUMBER: _ClassVar[int]
    OWNER_FIELD_NUMBER: _ClassVar[int]
    DEADLINE_UNIX_MS_FIELD_NUMBER: _ClassVar[int]
    granted: bool
    message: str
    fencing_token: int
    owner: str
    deadline_unix_ms: int
    def __init__(self, granted: _Optional[bool] = ..., message: _Optional[str] = ..., fencing_token: _Optional[int] = ..., owner: _Optional[str] = ..., deadline_unix_ms: _Optional[int] = ...) -> None: ...

class RenewLeaseRequest(_message.Message):
    __slots__ = ("name", "owner", "fencing_token", "ttl_ms")
    NAME_FIELD_NUMBER: _ClassVar[int]
    OWNER_FIELD_NUMBER: _ClassVar[int]
    FENCING_TOKEN_FIELD_NUMBER: _ClassVar[int]
    TTL_MS_FIELD_NUMBER: _ClassVar[int]
    name: str
    owner: str
    fencing_token: int
    ttl_ms: int
    def __init__(self, name: _Optional[str] = ..., owner: _Optional[str] = ..., fencing_token: _Optional[int] = ..., ttl_ms: _Optional[int] = ...) -> None: ...

class RenewLeaseResponse(_message.Message):
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

class RevokeLeaseRequest(_message.Message):
    __slots__ = ("name", "owner", "fencing_token")
    NAME_FIELD_NUMBER: _ClassVar[int]
    OWNER_FIELD_NUMBER: _ClassVar[int]
    FENCING_TOKEN_FIELD_NUMBER: _ClassVar[int]
    name: str
    owner: str
    fencing_token: int
    def __init__(self, name: _Optional[str] = ..., owner: _Optional[str] = ..., fencing_token: _Optional[int] = ...) -> None: ...

class RevokeLeaseResponse(_message.Message):
    __slots__ = ("revoked", "message")
    REVOKED_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    revoked: bool
    message: str
    def __init__(self, revoked: _Optional[bool] = ..., message: _Optional[str] = ...) -> None: ...

class ListLeasesRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class LeaseInfo(_message.Message):
    __slots__ = ("name", "owner", "fencing_token", "granted_unix_ms", "deadline_unix_ms")
    NAME_FIELD_NUMBER: _ClassVar[int]
    OWNER_FIELD_NUMBER: _ClassVar[int]
    FENCING_TOKEN_FIELD_NUMBER: _ClassVar[int]
    GRANTED_UNIX_MS_FIELD_NUMBER: _ClassVar[int]
    DEADLINE_UNIX_MS_FIELD_NUMBER: _ClassVar[int]
    name: str
    owner: str
    fencing_token: int
    granted_unix_ms: int
    deadline_unix_ms: int
    def __init__(self, name: _Optional[str] = ..., owner: _Optional[str] = ..., fencing_token: _Optional[int] = ..., granted_unix_ms: _Optional[int] = ..., deadline_unix_ms: _Optional[int] = ...) -> None: ...

class ListLeasesResponse(_message.Message):
    __slots__ = ("leases",)
    LEASES_FIELD_NUMBER: _ClassVar[int]
    leases: _containers.RepeatedCompositeFieldContainer[LeaseInfo]
    def __init__(self, leases: _Optional[_Iterable[_Union[LeaseInfo, _Mapping]]] = ...) -> None: ...
