from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class WatchRequest(_message.Message):
    __slots__ = ("event_types", "last_seq", "topics")
    EVENT_TYPES_FIELD_NUMBER: _ClassVar[int]
    LAST_SEQ_FIELD_NUMBER: _ClassVar[int]
    TOPICS_FIELD_NUMBER: _ClassVar[int]
    event_types: _containers.RepeatedScalarFieldContainer[str]
    last_seq: int
    topics: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, event_types: _Optional[_Iterable[str]] = ..., last_seq: _Optional[int] = ..., topics: _Optional[_Iterable[str]] = ...) -> None: ...

class WatchResponse(_message.Message):
    __slots__ = ("type", "source", "payload", "timestamp_unix_ms", "seq")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_UNIX_MS_FIELD_NUMBER: _ClassVar[int]
    SEQ_FIELD_NUMBER: _ClassVar[int]
    type: str
    source: str
    payload: bytes
    timestamp_unix_ms: int
    seq: int
    def __init__(self, type: _Optional[str] = ..., source: _Optional[str] = ..., payload: _Optional[bytes] = ..., timestamp_unix_ms: _Optional[int] = ..., seq: _Optional[int] = ...) -> None: ...
