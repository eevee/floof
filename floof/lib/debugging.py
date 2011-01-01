"""Support for hackers; not so useful for everyone else.

Some of this functionality IS used even in production, e.g. for the timing
statistics in the footer.

Stolen shamelessly from spline.  Which is okay, because I wrote that.
"""

from collections import defaultdict
from datetime import datetime, timedelta
import traceback

from pylons import tmpl_context as c
from sqlalchemy.interfaces import ConnectionProxy

class SQLATimerProxy(ConnectionProxy):
    """Simple connection proxy that keeps track of total time spent querying.
    """
    # props: http://techspot.zzzeek.org/?p=31
    def cursor_execute(self, execute, cursor, statement, parameters, context, executemany):
        try:
            return execute(cursor, statement, parameters, context)
        finally:
            try:
                c.timer.sql_queries += 1
            except (TypeError, AttributeError):
                # Might happen if SQL is run before Pylons is done starting
                pass

    def execute(self, conn, execute, clauseelement, *args, **kwargs):
        now = datetime.now()
        try:
            return execute(clauseelement, *args, **kwargs)
        finally:
            try:
                delta = datetime.now() - now
                c.timer.sql_time += delta
            except (TypeError, AttributeError):
                pass

class SQLAQueryLogProxy(SQLATimerProxy):
    """Extends the above to also log a summary of exactly what queries were
    executed, what userland code triggered them, and how long each one took.
    """
    def cursor_execute(self, execute, cursor, statement, parameters, context, executemany):
        now = datetime.now()
        try:
            super(SQLAQueryLogProxy, self).cursor_execute(
                execute, cursor, statement, parameters, context, executemany)
        finally:
            try:
                # Find who spawned this query.  Rewind up the stack until we
                # escape from sqlalchemy code -- including this file, which
                # contains proxy stuff
                caller = '(unknown)'
                for frame_file, frame_line, frame_func, frame_code in \
                    reversed(traceback.extract_stack()):

                    if __file__.startswith(frame_file) \
                        or '/sqlalchemy/' in frame_file:

                        continue

                    # OK, this is it
                    caller = "{0}:{1} in {2}".format(
                        frame_file, frame_line, frame_func)
                    break

                c.timer.sql_query_log[statement].append(dict(
                    parameters=parameters,
                    time=datetime.now() - now,
                    caller=caller,
                ))
            except (TypeError, AttributeError):
                pass

class ResponseTimer(object):
    """Nearly trivial class, used for tracking how long the page took to
    create.

    Properties are `total_time`, `sql_time`, and `sql_queries`.

    In SQL debug mode, `sql_query_log` is also populated.  Its keys are
    queries; values are dicts of parameters, time, and caller.
    """

    def __init__(self):
        self._start_time = datetime.now()
        self._total_time = None

        self.from_cache = None

        # SQLAlchemy will add to these using the above proxy class; see
        # spline.config.environment
        self.sql_time = timedelta()
        self.sql_queries = 0
        self.sql_query_log = defaultdict(list)

    @property
    def total_time(self):
        # Calculate and save the total render time as soon as this is accessed
        if self._total_time is None:
            self._total_time = datetime.now() - self._start_time
        return self._total_time
