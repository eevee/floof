from floof import model
from floof.model import meta
from floof.tests import *
import floof.tests.openidspoofer as oidspoof
import floof.tests.sim as sim

PORT = 19614
DATA_PATH = '/tmp'

class TestControlsController(TestController):
    
    @classmethod
    def setup_class(cls):
        """Creates a user to be used as a fake login."""
        cls.user = sim.sim_user()
        meta.Session.commit()

        # Force a refresh of the user, to get id populated
        # XXX surely there's a better way!
        meta.Session.refresh(cls.user)


    def test_index(self):
        response = self.app.get(
                url(controller='controls', action='index'),
                extra_environ={'tests.user_id': self.user.id},
                )
        # Test response...

    def test_openids(self):
        response = self.app.get(
                url(controller='controls', action='openid'),
                extra_environ={'tests.user_id': self.user.id},
                )
        # Test response...

    def test_openids_add_del(self):
        test_openids = [
                u'flooftest1',
                u'flooftest2',
                ]
        responses = []

        spoofer = oidspoof.OpenIDSpoofer('localhost', PORT, DATA_PATH)

        # Test adding two OpenID identities
        for user in test_openids:
            spoofer.update(user=user, accept=True)
            response_begin = self.app.post(
                    url(controller='controls', action='openid'),
                    params=[
                        ('add_openid', u'Add OpenID'),
                        ('new_openid', u'localhost:{0}/id/{1}'.format(PORT, user)),
                    ],
                    extra_environ={'tests.user_id': self.user.id},
                    )
            location = response_begin.headers['location']
            path, params = spoofer.spoof(location)
            assert path is not None
            response_end = self.app.get(
                    path,
                    params=params,
                    extra_environ={'tests.user_id': self.user.id},
                    )
            assert response_end.status == '200 OK'
            responses.append(response_end)
        assert 'http://localhost:{0}/id/flooftest1</label>'.format(PORT) in responses[0], 'Addition of OpenID identity URL failed.'
        assert 'http://localhost:{0}/id/flooftest2</label>'.format(PORT) not in responses[0], 'App appears to have guessed our next OpenID URL....'
        assert 'http://localhost:{0}/id/flooftest1</label>'.format(PORT) in responses[1], 'Addition of OpenID identity URL was not retained.'
        assert 'http://localhost:{0}/id/flooftest2</label>'.format(PORT) in responses[1], 'Addition of second OpenID identity URL failed.'

        # Test denial of double-entries
        response_begin = self.app.post(
                url(controller='controls', action='openid'),
                params=[
                    ('add_openid', u'Add OpenID'),
                    ('new_openid', u'localhost:{0}/id/{1}'.format(PORT, test_openids[1])),
                ],
                extra_environ={'tests.user_id': self.user.id},
                )
        location = response_begin.headers['location']
        path, params = spoofer.spoof(location)
        assert path is not None
        response_end = self.app.get(
                path,
                params=params,
                extra_environ={'tests.user_id': self.user.id},
                )
        assert 'can already authenticate with that OpenID' in response_end

        # Test deletion
        oid = meta.Session.query(model.IdentityURL) \
                .filter_by(url='http://localhost:{0}/id/flooftest2'.format(PORT)) \
                .one()
        response = self.app.post(
                url(controller='controls', action='openid'),
                params=[
                    ('del_openids', u'Delete Selected Identities'),
                    ('openids', oid.id),
                ],
                extra_environ={'tests.user_id': self.user.id},
                )
        assert 'http://localhost:{0}/id/flooftest1</label>'.format(PORT) in response, 'An OpenID identity URL that should have been found was not.'
        assert 'http://localhost:{0}/id/flooftest2</label>'.format(PORT) not in response, 'Deletion of OpenID identity URL failed.'

        # Test rejection of deletion of final OpenID URL
        q = meta.Session.query(model.IdentityURL).filter_by(user_id=self.user.id)
        assert q.count() < 2, 'Test user has more that one OpenID URL, when they should not.'
        assert q.count() > 0, 'Test user no OpenID URLs, when they should have one.'
        oid = q.one()
        response = self.app.post(
                url(controller='controls', action='openid'),
                params=[
                    ('del_openids', u'Delete Selected Identities'),
                    ('openids', oid.id),
                ],
                extra_environ={'tests.user_id': self.user.id},
                )
        assert 'http://localhost:{0}/id/flooftest1</label>'.format(PORT) in response, 'Test user\'s final OpenID URL was deleted.  It should not have been.'
        assert 'http://localhost:{0}/id/flooftest2</label>'.format(PORT) not in response, 'Found an OpenID identity URL that should not have been.'

