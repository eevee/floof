from __future__ import unicode_literals

import floof.model as model
from floof.model import meta

# XXX The idea here is that we generate random junk data to use (and print the
# seed at the start of a test run), ensuring over time that the actual format
# of data doesn't break the app.  Like really slow fuzzing.
# But, for now, the constant values below were determined to be sufficiently
# random.

def sim_user():
    user = model.User(
        name = 'sim',
        role_id = 1,
        resource = model.Resource(type=u'users'),
    )
    meta.Session.add(user)
    return user

def sim_artwork(user):
    artwork = model.MediaImage(
        title = 'dummy image',
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
    meta.Session.add(artwork)
    return artwork

def sim_tag():
    tag = model.Tag(name=u'foo')
    meta.Session.add(tag)
    return tag
