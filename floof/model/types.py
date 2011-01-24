import pytz
import re
from socket import AF_INET, AF_INET6, inet_ntop, inet_pton
from sqlalchemy import types

class TZDateTime(types.TypeDecorator):
    impl = types.DateTime

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value.astimezone(pytz.utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value.replace(tzinfo=pytz.utc)


class Timezone(types.TypeDecorator):
    @staticmethod
    def impl():
        return types.String(64)

    def process_bind_param(self, value, engine):
        if value is None:
            return None
        return value.zone

    def process_result_value(self, value, engine):
        if value is None:
            return pytz.utc
        return pytz.timezone(value)

# XXX: I need to check whether this actually gives any great gains over
# using a string.
# XXX: According to the Python docs, socket.inet_pton only works on *nix
# XXX: I have not actually tested this with IPv6
class IPAddr(types.TypeDecorator):
    impl = types.LargeBinary(length=16)

    def __init__(self):
        pass

    def process_bind_param(self, value, engine):
        if value is None:
            return None
        elif '.' in value:
            return inet_pton(AF_INET, value)
        else:
            return inet_pton(AF_INET6, value)

    def process_result_value(self, value, engine):
        if value is None:
            return None
        elif len(value) == 4:
            return inet_ntop(AF_INET, value)
        else:
            return inet_ntop(AF_INET6, value)

    def is_mutable(self):
        return False

__all__ = ['IPAddr', 'TZDateTime', 'Timezone']
