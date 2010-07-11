import hashlib
import logging
import random

import magic
import PIL.Image
from pylons import config, request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect_to
from sqlalchemy.orm.exc import NoResultFound
import wtforms.form, wtforms.fields

from floof.lib.base import BaseController, render
from floof.model import filestore, meta
from floof import model

log = logging.getLogger(__name__)

class UploadArtworkForm(wtforms.form.Form):
    file = wtforms.fields.FileField(u'')

class ArtController(BaseController):
    HASH_BUFFER_SIZE = 524288  # half a meg

    def upload(self):
        """Uploads something.  Sort of important, you know."""
        c.form = UploadArtworkForm(request.POST)

        # XXX protect against duplicate files
        # XXX ummm associate an artist and only allow for logged-in users.
        # XXX optipng

        if request.method == 'POST' and c.form.validate():
            # Grab the file
            storage = filestore.get_storage(config)
            uploaded_file = request.POST['file']
            fileobj = uploaded_file.file

            # Figure out mimetype (and if we even support it)
            mimetype = magic.Magic(mime=True).from_buffer(fileobj.read(1024))
            # XXX only one so far...
            if mimetype != 'image/png':
                c.form.file.errors.append("Unrecognized filetype; only PNG is supported at the moment.")
                return render('/art/upload.mako')

            # Open the image
            # XXX surely this can be done more easily
            fileobj.seek(0)
            image = PIL.Image.open(fileobj)
            width, height = image.size
            del image

            # Hash the thing
            hasher = hashlib.sha256()
            file_size = 0
            fileobj.seek(0)
            while True:
                buffer = fileobj.read(self.HASH_BUFFER_SIZE)
                if not buffer:
                    break

                file_size += len(buffer)
                hasher.update(buffer)
            hash = hasher.hexdigest()

            # Store the file.  Reset the file object first!
            fileobj.seek(0)
            storage.put(hash, fileobj)

            # Stuff it all in the db
            general_data = dict(
                title = '',
                hash = hash,
                original_filename = uploaded_file.filename,
                mime_type = mimetype,
                file_size = file_size,
            )
            artwork = model.MediaImage(
                height = height,
                width = width,
                **general_data
            )

            meta.Session.add(artwork)
            meta.Session.commit()
            # XXX include title
            return redirect_to(url(controller='art', action='view', id=artwork.id))

        else:
            return render('/art/upload.mako')

    def gallery(self):
        """Main gallery; provides browsing through absolutely everything we've
        got.
        """
        c.artwork = meta.Session.query(model.Artwork).all()
        return render('/art/gallery.mako')

    def view(self, id):
        """View a single item of artwork."""
        try:
            c.artwork = meta.Session.query(model.Artwork).get(id)
        except NoResultFound:
            abort(404)

        storage = filestore.get_storage(config)
        c.artwork_url = storage.url(c.artwork.hash)

        return render('/art/view.mako')
