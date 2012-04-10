from pyramid import testing
from vep import DummyVerifier
from webob.multidict import MultiDict

from floof.routing import configure_routing
from floof.tests import UnitTests
from floof.tests import sim


OLD_ASSERTION_ADDR = 'floof-throwaway@leptic.net'
OLD_ASSERTION = """
eyJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJicm93c2VyaWQub3JnIiwiZXhwIjoxMzI3MjM3Njg5NjUyLC
JpYXQiOjEzMjcxNTEyODk2NTIsInB1YmxpYy1rZXkiOnsiYWxnb3JpdGhtIjoiRFMiLCJ5IjoiNGNmO
WM2NmQ5YzAwZWNmNDZjMDY0NTUzMjNhMjk0YzgxN2I5NzJkOTkxZDcyYTE4YjgzYWUxY2I4NzhkMGZj
ZTZhMjNlZTJlZmQ5MjYyMmVjNmJmYzM2ZjIyZGMyNTc5MzkyNGI2Mjk1Mjc4NmNmZThiOWYyNzFlZjg
zZTU0NDY4ZGQyYTRlZTA0ZDIwNDliZWM2M2E3N2U1MGQ0MTk1YjExNzhhNGQ1ZTE5MTJmZGQyZTdiOG
U2ZWQ3ODg4MDJiNzRiNjJmZGMxOTEwYjU5OTY4MWU1OWNhMDhmNmQ3Y2MyYTYyNjM5NzEwYTIwZDAyM
jI5OGIwNDE4Y2ZjOTIyMzkwNTdjOWZkODFkZTE5NzQ3Y2NiODQ3MzNlYmZkNGExOTRhYTZiMGMzMDUw
MTA3MThmZGM2MzNhNDJjYWFjMjllYTZjMGYwNTdlYTMzNTIxZDE3YzZlYzA4YWNmZmY2NTc1OTJkYTk
zODE2NmVhNzVkMTllM2U1MzkwYzhmMDJkNzJiMjU5MGMxZGM5YTJhYzQ1M2IyZTA4MDg0MWI5ZWI2Ym
E1NjNiMTYxYjBjYmU1YTI1ZGViOWY5MTVhNjM0M2UzZjRkZGZkNGVlZGE1Yzk4NTVjYzZkMGM4MDllZ
jVmM2ZkZmY4NGM1ODQxZGYzN2Q4NzhjNmNmYjQ0YjYzZjkiLCJwIjoiZDZjNGU1MDQ1Njk3NzU2Yzdh
MzEyZDAyYzIyODljMjVkNDBmOTk1NDI2MWY3YjU4NzYyMTRiNmRmMTA5YzczOGI3NjIyNmIxOTliYjd
lMzNmOGZjN2FjMWRjYzMxNmUxZTdjNzg5NzM5NTFiZmM2ZmYyZTAwY2M5ODdjZDc2ZmNmYjBiOGMwMD
k2YjBiNDYwZmZmYWM5NjBjYTQxMzZjMjhmNGJmYjU4MGRlNDdjZjdlNzkzNGMzOTg1ZTNiM2Q5NDNiN
zdmMDZlZjJhZjNhYzM0OTRmYzNjNmZjNDk4MTBhNjM4NTM4NjJhMDJiYjFjODI0YTAxYjdmYzY4OGU0
MDI4NTI3YTU4YWQ1OGM5ZDUxMjkyMjY2MGRiNWQ1MDViYzI2M2FmMjkzYmM5M2JjZDZkODg1YTE1NzU
3OWQ3ZjUyOTUyMjM2ZGQ5ZDA2YTRmYzNiYzIyNDdkMjFmMWE3MGY1ODQ4ZWIwMTc2NTEzNTM3Yzk4M2
Y1YTM2NzM3ZjAxZjgyYjQ0NTQ2ZThlN2YwZmFiYzQ1N2UzZGUxZDljNWRiYTk2OTY1YjEwYTJhMDU4M
GIwYWQwZjg4MTc5ZTEwMDY2MTA3ZmI3NDMxNGEwN2U2NzQ1ODYzYmM3OTdiNzAwMmViZWMwYjAwMGE5
OGViNjk3NDE0NzA5YWMxN2I0MDEiLCJxIjoiYjFlMzcwZjY0NzJjODc1NGNjZDc1ZTk5NjY2ZWM4ZWY
xZmQ3NDhiNzQ4YmJiYzA4NTAzZDgyY2U4MDU1YWIzYiIsImciOiI5YTgyNjlhYjJlM2I3MzNhNTI0Mj
E3OWQ4ZjhkZGIxN2ZmOTMyOTdkOWVhYjAwMzc2ZGIyMTFhMjJiMTljODU0ZGZhODAxNjZkZjIxMzJjY
mM1MWZiMjI0YjA5MDRhYmIyMmRhMmM3Yjc4NTBmNzgyMTI0Y2I1NzViMTE2ZjQxZWE3YzRmYzc1YjFk
Nzc1MjUyMDRjZDdjMjNhMTU5OTkwMDRjMjNjZGViNzIzNTllZTc0ZTg4NmExZGRlNzg1NWFlMDVmZTg
0NzQ0N2QwYTY4MDU5MDAyYzM4MTlhNzVkYzdkY2JiMzBlMzllZmFjMzZlMDdlMmM0MDRiN2NhOThiMj
YzYjI1ZmEzMTRiYTkzYzA2MjU3MThiZDQ4OWNlYTZkMDRiYTRiMGI3ZjE1NmVlYjRjNTZjNDRiNTBlN
GZiNWJjZTlkN2FlMGQ1NWIzNzkyMjVmZWIwMjE0YTA0YmVkNzJmMzNlMDY2NGQyOTBlN2M4NDBkZjNl
MmFiYjVlNDgxODlmYTRlOTA2NDZmMTg2N2RiMjg5YzY1NjA0NzY3OTlmN2JlODQyMGE2ZGMwMWQwNzh
kZTQzN2YyODBmZmYyZDdkZGYxMjQ4ZDU2ZTFhNTRiOTMzYTQxNjI5ZDZjMjUyOTgzYzU4Nzk1MTA1OD
AyZDMwZDdiY2Q4MTljZjZlZiJ9LCJwcmluY2lwYWwiOnsiZW1haWwiOiJmbG9vZi10aHJvd2F3YXlAb
GVwdGljLm5ldCJ9fQ.P-_r4udeAZJPaFjq6vLUesQ9KtsnnPKA3JJZe91G_aYYBSt0M-HlbNgWLKbAT
W7T-64-VDBAD0cWZfDr1M2QD7z3ZZDjjpHOt1n3v3R6Jn6yOW-xVvQcNeMXw0WMJr_LCx_h06JVkb1i
emCFx-Luc4kce1q4UU8VIIuxGItvsVAvlzXpEHP_jt61VjmOu6-82x0bFaTimTw26yV0x40iQhwAESc
MrS5kvCpnku31DCcC73yERzr10SDXyVbmRgUiSEzo1UBMV8_hvZLZnTn1M015gQDp8QvOHX3wgSH-9f
1Ck2BKFFz4gwcVX5PSR9tyNdwuM6Ym-UHwWWdxY5e0Tw~eyJhbGciOiJEUzI1NiJ9.eyJleHAiOjEzM
jcxNTE0NTIyMTYsImF1ZCI6Imh0dHBzOi8vbG9jYWxob3N0In0.Ji1fIhsI1SNBZDSIC8xDxerFD1F1
LoZKl__ohAiL1Z2q9iPR9cgC9xPEdiPugZqhTQUXAbutPe4RkhedtiPGVQ
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

        audience = 'https://mysite.example.org'
        self.config.add_settings({'auth.browserid.audience': audience})
        request = self._make_request()
        request.method = 'POST'
        request.user = sim.sim_user(credentials=[('browserid', OLD_ASSERTION_ADDR)])

        for a in (None, '', self._randstr(), OLD_ASSERTION):
            request.POST = MultiDict({'assertion': a})
            verify(request,
                   next_url=request.route_url('account.login'),
                   flash_msg='signature was invalid')
            request.session.clear()

        email = self._randstr() + '@example.com'
        verifier = DummyVerifier()
        a = verifier.make_assertion(email, audience)
        request.POST = MultiDict({'assertion': a})
        request.user = sim.sim_user(credentials=[('browserid', email)])
        request.environ['paste.testing'] = True
        request.environ['tests.auth.browserid.verifier'] = verifier
        request.environ['tests.auth.browserid.audience'] = audience
        verify(request,
               next_url=request.route_url('root'),
               flash_msg='Re-authentication successful')
