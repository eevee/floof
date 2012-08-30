from pyramid import testing
from browserid import LocalVerifier
from browserid.tests.support import patched_supportdoc_fetching, make_assertion
from webob.multidict import MultiDict

from floof.routing import configure_routing
from floof.tests import UnitTests
from floof.tests import sim


OLD_ASSERTION_ADDR = 'floof-throwaway@leptic.net'
OLD_ASSERTION = """
eyJhbGciOiJSUzI1NiJ9.eyJwdWJsaWMta2V5Ijp7ImFsZ29yaXRobSI6IkRTIiwieSI6Im
RhNmE3MTRhZWYzMDFlNmYzODVlMzJiNDIwMWRhMzAyZmQ0YmJlZTEyZmY4MDc0ZmQ1MDNjY
zg4MDRkNjUyMDA0ZmU0MzBiYjUzYTI5ZTg4YWJjY2U1YmViODc4NjI4ZDRjOGQzMTcyNDIz
ZmZiYWM2OTFkNjU2MDBkMjVhOGY1MTM0NmRlMDMzMzczZjg1ZWY2ZmU0NzRjOWI3ZTFhMWV
jZDBlZjE3MjBiMTBkODZkNjA1YzMzMWRlMWYxMThkNzliMjFjN2JkZjgxYjdhN2JmNDIxNm
EwZTJjZGMxZTY5ZGFiNmU0ZDc2M2I5YTY0NTAyNGJmMGM2YTQxYWQ5YWUiLCJwIjoiZmY2M
DA0ODNkYjZhYmZjNWI0NWVhYjc4NTk0YjM1MzNkNTUwZDlmMWJmMmE5OTJhN2E4ZGFhNmRj
MzRmODA0NWFkNGU2ZTBjNDI5ZDMzNGVlZWFhZWZkN2UyM2Q0ODEwYmUwMGU0Y2MxNDkyY2J
hMzI1YmE4MWZmMmQ1YTViMzA1YThkMTdlYjNiZjRhMDZhMzQ5ZDM5MmUwMGQzMjk3NDRhNT
E3OTM4MDM0NGU4MmExOGM0NzkzMzQzOGY4OTFlMjJhZWVmODEyZDY5YzhmNzVlMzI2Y2I3M
GVhMDAwYzNmNzc2ZGZkYmQ2MDQ2MzhjMmVmNzE3ZmMyNmQwMmUxNyIsInEiOiJlMjFlMDRm
OTExZDFlZDc5OTEwMDhlY2FhYjNiZjc3NTk4NDMwOWMzIiwiZyI6ImM1MmE0YTBmZjNiN2U
2MWZkZjE4NjdjZTg0MTM4MzY5YTYxNTRmNGFmYTkyOTY2ZTNjODI3ZTI1Y2ZhNmNmNTA4Yj
kwZTVkZTQxOWUxMzM3ZTA3YTJlOWUyYTNjZDVkZWE3MDRkMTc1ZjhlYmY2YWYzOTdkNjllM
TEwYjk2YWZiMTdjN2EwMzI1OTMyOWU0ODI5YjBkMDNiYmM3ODk2YjE1YjRhZGU1M2UxMzA4
NThjYzM0ZDk2MjY5YWE4OTA0MWY0MDkxMzZjNzI0MmEzODg5NWM5ZDViY2NhZDRmMzg5YWY
xZDdhNGJkMTM5OGJkMDcyZGZmYTg5NjIzMzM5N2EifSwicHJpbmNpcGFsIjp7ImVtYWlsIj
oiZmxvb2YtdGhyb3dhd2F5QGxlcHRpYy5uZXQifSwiaWF0IjoxMzQwMzYyOTA1ODEwLCJle
HAiOjEzNDA0NDkzMDU4MTAsImlzcyI6ImJyb3dzZXJpZC5vcmcifQ.LtqQpeHiqMJ1goQD4
MN89SbZCs6vK1K_JVVsDCqTrw446uWQtjVg72muVwqPDy3jWD5CbZ8aIrILULTvB_zzllvV
lrD-xVABUgJBwSOTZ1UWSZxs2REkEMtkW5-VeM4pLl2tyDcIhR220YYAW58G6Mmjm70Jib_
39IPdJfbSMRI46eSznWqFdgU7jUFCvW8D7ocakzN8gGOgbrdRw0Ic8MKwqdRDwYeXZVbm_6
rsQ4eM3cuTyNoQ2FW0RhDJWg7MaKYPYa51j1kLkBISxNQlkaztNqAb1Qxm__dooor7c8lD0
5p9XmpSFNNQWRATIgeu2x-hhKCud2XSnbAb-5OIbg~eyJhbGciOiJEUzEyOCJ9.eyJleHAi
OjEzNDAzNjMwMjU3OTYsImF1ZCI6Imh0dHBzOi8vbG9jYWxob3N0In0.3Z_lYt6eKJBeDaj
mAhJT9oXw1X4dJqxpEmKLz7pJuZ1HT-zuHyWdAg
""".replace("\n", "").strip()


class TestAccountViews(UnitTests):

    def setUp(self):
        super(TestAccountViews, self).setUp()
        configure_routing(self.config)

    def _make_request(self):
        request = testing.DummyRequest()
        request.context = testing.DummyResource()
        request.params = MultiDict()

        def flash(msg, *args, **kwargs):
            queue = kwargs.get('queue', '')
            allow_duplicate = kwargs.get('allow_duplicate', True)
            storage = request.session.setdefault('_f_' + queue, [])
            if allow_duplicate or (msg not in storage):
                storage.append(msg)
        request.session.flash = flash

        return request

    def test_account_login_browserid(self):
        from floof.views.account import account_login_browserid as view

        def verify(request, next_url, flash_msg):
            response = view(request.context, request)
            flashes = request.session['_f_']
            assert len(flashes) == 1
            assert flash_msg in flashes[0]
            assert response['redirect-to'] == next_url

        audience = 'https://localhost'
        self.config.add_settings({'auth.browserid.audience': audience})
        request = self._make_request()
        request.method = 'POST'
        request.user = sim.sim_user(credentials=[('browserid', OLD_ASSERTION_ADDR)])

        # Test failures

        trials = (
            (None, 'unspecified error'),
            ('', 'unspecified error'),
            (self._randstr(), 'unspecified error'),
            (OLD_ASSERTION, 'signature was invalid')
        )

        for a, f in trials:
            request.POST = MultiDict({'assertion': a})
            verify(request,
                   next_url=request.route_url('account.login'),
                   flash_msg=f)
            request.session.clear()

        # Test success

        email = self._randstr() + '@example.com'
        verifier = LocalVerifier([audience], warning=False)
        a = make_assertion(email, audience)

        request.POST = MultiDict({'assertion': a})
        request.user = sim.sim_user(credentials=[('browserid', email)])
        request.environ['paste.testing'] = True
        request.environ['tests.auth.browserid.verifier'] = verifier
        request.environ['tests.auth.browserid.audience'] = audience
        with patched_supportdoc_fetching():
            verify(request,
                   next_url=request.route_url('root'),
                   flash_msg='Re-authentication successful')
