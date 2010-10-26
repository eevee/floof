import pytz
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

__all__ = ['TZDateTime', 'Timezone']
