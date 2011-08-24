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
    """Tracks how long a page took to create.  Splits the time across several
    individual timers, accessible via the `timers` dict.

    Other properties are `total_time`, `sql_time`, and `sql_queries`.

    In SQL debug mode, `sql_query_log` is also populated.  Its keys are
    queries; values are dicts of parameters, time, and caller.
    """
    timer_names = frozenset(('python', 'mako', 'sql'))
    default_timer = 'python'
    assert default_timer in timer_names

    _start_timestamp = None

    def __init__(self):
        self._timer_stack = []
        self.timers = dict((name, timedelta()) for name in self.timer_names)
        self.switch_timer(self.default_timer)

        # Not really timing, but relevant SQLAlchemy stats.  Debug mode only
        self.sql_query_count = 0
        self.sql_query_log = defaultdict(list)

    @reify
    def total_time(self):
        """Stops all timing.  Returns the total time elapsed since this object
        was created.
        """
        self.switch_timer(None)
        return sum(self.timers.itervalues(), timedelta())

    def switch_timer(self, name):
        """Change who to blame for processing time going forward.  Pass `None`
        to stop all timing.

        Don't use this after a `push_timer`, until a corresponding pop.

        Returns the time passed since the last switch.
        """
        assert name in self.timer_names or name is None
        now = datetime.now()
        if self._start_timestamp:
            delta = now - self._start_timestamp
            self.timers[self.current_timer] += delta
        else:
            delta = None

        if name is None:
            self.switch_timer = lambda name: None

        self._start_timestamp = now
        self.current_timer = name
        return delta

    def push_timer(self, name):
        """Temporarily switch timers.  Use `pop_timer` to switch back."""
        self._timer_stack.append(self.current_timer)
        return self.switch_timer(name)

    def pop_timer(self):
        """Undo a `push_timer`."""
        return self.switch_timer(self._timer_stack.pop())

    ### These two callbacks just track how much time is taken by plain old SQL.
    ### They track the high-level execute() calls, so they'll catch some
    ### SQLAlchemy time (mostly compilation).  This is a feature.
    def _before_execute(self):
        self.push_timer('sql')

    def _after_execute(self):
        self.pop_timer()

    ### These two callbacks fire around each actual query -- they track the
    ### number of individual queries, and in super-crazy-detail mode also track
    ### every statement made and how long it took.
    def _before_cursor_execute(self):
        self.sql_query_count += 1
        self.push_timer('sql')

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

        delta = self.pop_timer()
        self.sql_query_log[statement].append(dict(
            parameters=parameters, time=delta, caller=caller))
