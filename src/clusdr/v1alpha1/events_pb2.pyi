from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class PublishEventRequest(_message.Message):
    __slots__ = ("topic", "payload", "event_id", "source", "relay")
    TOPIC_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    RELAY_FIELD_NUMBER: _ClassVar[int]
    topic: str
    payload: bytes
    event_id: str
    source: str
    relay: bool
    def __init__(self, topic: _Optional[str] = ..., payload: _Optional[bytes] = ..., event_id: _Optional[str] = ..., source: _Optional[str] = ..., relay: _Optional[bool] = ...) -> None: ...

class PublishEventResponse(_message.Message):
    __slots__ = ("accepted", "message", "event_id", "type")
    ACCEPTED_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    accepted: bool
    message: str
    event_id: str
    type: str
    def __init__(self, accepted: _Optional[bool] = ..., message: _Optional[str] = ..., event_id: _Optional[str] = ..., type: _Optional[str] = ...) -> None: ...
