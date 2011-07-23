"""Support for hackers; not so useful for everyone else.

Some of this functionality IS used even in production, e.g. for the timing
statistics in the footer.

Stolen shamelessly from spline.  Which is okay, because I wrote that.
"""

from collections import defaultdict
from datetime import datetime, timedelta
import traceback

from pyramid.decorator import reify
from pyramid.threadlocal import get_current_request
from sqlalchemy.event import listen


# This uses get_current_request, which is kinda no bueno.  :(  Alas I don't
# have any better ideas as to how to make the request available.
def handle_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    get_current_request().timer._before_cursor_execute()

def handle_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    get_current_request().timer._after_cursor_execute(statement, parameters)

def handle_before_execute(conn, clauseelement, multiparams, params):
    get_current_request().timer._before_execute()

def handle_after_execute(conn, clauseelement, multiparams, params, result):
    get_current_request().timer._after_execute()

def attach_sqlalchemy_listeners(engine, debug=False):
    """Tacks a bunch of stuff onto the given SQLAlchemy engine, for profiling.

    If `debug` is false, the after_cursor handler will be omitted, as it does
    all the heaviest lifting.
    """
    if debug:
        listen(engine, 'before_cursor_execute', handle_before_cursor_execute)
    listen(engine, 'after_cursor_execute', handle_after_cursor_execute)
    listen(engine, 'before_execute', handle_before_execute)
    listen(engine, 'after_execute', handle_after_execute)


class RequestTimer(object):
    """Tracks how long a page took to create.

    Properties are `total_time`, `sql_time`, and `sql_queries`.

    In SQL debug mode, `sql_query_log` is also populated.  Its keys are
    queries; values are dicts of parameters, time, and caller.
    """

    def __init__(self):
        self._start_timestamp = datetime.now()

        # SQLAlchemy will add to these using the above proxy class; see
        # floof.config.environment
        self.sql_time = timedelta()
        # Debug mode only
        self.sql_query_count = 0
        self.sql_query_log = defaultdict(list)

        # Template time, not including SQLAlchemy time
        # Also debug mode only
        self.template_time = timedelta()

    @reify
    def total_time(self):
        """Return the total time elapsed since this object was created."""
        return datetime.now() - self._start_timestamp

    ### These two callbacks just track how much time is taken by plain old SQL.
    ### They track the high-level execute() calls, so they'll catch some
    ### SQLAlchemy time (mostly compilation).  This is a feature.
    _sql_execute_time = None

    def _before_execute(self):
        self._sql_execute_time = datetime.now()

    def _after_execute(self):
        if not self._sql_execute_time:
            warnings.warn("Got to after_execute with no before_execute")
            return
        delta = datetime.now() - self._sql_execute_time
        self._sql_execute_time = None

        self.sql_time += delta

    ### These two callbacks fire around each actual query -- they track the
    ### number of individual queries, and in super-crazy-detail mode also track
    ### every statement made and how long it took.
    _sql_cursor_time = None

    def _before_cursor_execute(self):
        self.sql_query_count += 1
        self._sql_cursor_time = datetime.now()

    def _after_cursor_execute(self, statement, parameters):
        # Find who spawned this query.  Rewind up the stack until we
        # escape from library code -- including this file
        caller = '(unknown)'
        for frame_file, frame_line, frame_func, frame_code in \
            reversed(traceback.extract_stack()):

            if __file__.startswith(frame_file) or '/sqlalchemy/' in frame_file:
                continue

            # OK, this is it
            caller = "{0}:{1} in {2}".format(frame_file, frame_line, frame_func)
            break

        if not self._sql_cursor_time:
            warnings.warn("Got to after_cursor_execute with no before_cursor_execute")
            return
        delta = datetime.now() - self._sql_cursor_time
        self._sql_cursor_time = None

        self.sql_query_log[statement].append(dict(
            parameters=parameters, time=delta, caller=caller))
