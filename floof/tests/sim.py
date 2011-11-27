from __future__ import unicode_literals

import random
import string

from floof import model

# XXX The idea here is that we generate random junk data to use (and print the
# seed at the start of a test run), ensuring over time that the actual format
# of data doesn't break the app.  Like really slow fuzzing.
# But, for now, the constant values below were determined to be sufficiently
# random.

def sim_user(role='user'):
    role_id = model.session.query(model.Role).filter_by(name=role).one().id
    user = model.User(
        name = 'sim_' + ''.join(random.choice(string.letters) for n in range(10)),
        role_id = role_id,
        resource = model.Resource(type=u'users'),
    )
    model.session.add(user)
    return user

def sim_artwork(user):
    artwork = model.MediaImage(
        title = ''.join(random.choice(string.letters) for i in xrange(10)),
        hash = '123',
        uploader = user,
        original_filename = 'dummy.jpg',
        mime_type = 'image/jpeg',
        file_size = 1234,
        resource = model.Resource(type=u'artwork'),

        height = 100,
        width = 100,
        number_of_colors = 256,
    )
    model.session.add(artwork)
    return artwork

def sim_tag():
    tag = model.Tag(name=u'foo')
    model.session.add(tag)
    return tag
