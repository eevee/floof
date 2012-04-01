"""Developer-only functionality.

Currently, just an extra panel for pyramid_debugtoolbar.
"""

from pyramid_debugtoolbar.panels import DebugPanel

_ = lambda x: x

class SessionDebugPanel(DebugPanel):
    """Show information on the current session, including stuff about the user.
    """

    name = 'Session'
    has_content = True

    def nav_title(self):
        return _(u'Session')

    def nav_subtitle(self):
        if self.request.user:
            return u"<{0}>".format(self.request.user.name)
        else:
            return _(u'Logged out')

    def url(self):
        return u''

    def title(self):
        return _(u'Session')

    def content(self):
        scope = dict(
            request=self.request,
        )
        return self.render(
            'floof:templates/session_panel.dbtmako',
            scope, self.request)
