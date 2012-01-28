from cStringIO import StringIO
import hashlib

# PIL is an unholy fucking abomination that can't even be imported right
try:
    import Image
except ImportError:
    from PIL import Image


HASH_BUFFER_SIZE = 524288  # .5 MiB

MIMETYPE_MAP = {
    u'image/png': 'PNG',
    u'image/gif': 'GIF',
    u'image/jpeg':'JPEG',
}
"""Map from mimetypes to PIL `format` names."""

SUPPORTED_MIMETYPES = tuple(MIMETYPE_MAP.keys())


def dump_image_to_buffer(image, mimetype):
    """Dump the image into a StringIO buffer.

    The given `mimetype` is translated into the appropriate PIL format name.

    """
    buf = StringIO()
    image.save(buf, MIMETYPE_MAP[mimetype])
    buf.seek(0)
    return buf


def get_number_of_colors(image):
    """Does what it says on the tin.

    This attempts to return the number of POSSIBLE colors in the image, not the
    number of colors actually used.  In the case of a paletted image, PIL is
    often limited to only returning the actual number of colors.  But that's
    usually what we mean for palettes, so eh.

    But full-color images will always return 16777216.  Alpha doesn't count, so
    RGBA is still 24-bit color.
    """
    # See http://www.pythonware.com/library/pil/handbook/concepts.htm for list
    # of all possible PIL modes
    mode = image.mode
    if mode == '1':
        return 2
    elif mode == 'L':
        return 256
    elif mode == 'P':
        # This is sort of (a) questionable and (b) undocumented, BUT:
        # palette.getdata() returns a tuple of mode and raw bytes.  The raw
        # bytes are rgb encoded as three bytes each, so its length is three
        # times the number of palette entries.
        palmode, paldata = image.palette.getdata()
        return len(paldata) / 3
    elif mode in ('RGB', 'RGBA', 'CMYK', 'YCbCr', 'I', 'F',
        'LA', 'RGBX', 'RGBa'):
        return 2 ** 24
    else:
        raise ValueError("Unknown palette mode, argh!")


def scaled_dimensions(image, max_size):
    """Scale an image's dimensions so they do not exceed `max_size`.

    `image` is a floof MediaImage ORM object;
    `max_size` is an integer in pixels.

    Returns a (width, height) tuple in pixels.

    """
    max_dim = max(image.width, image.height)

    if max_dim <= max_size:
        return image.width, image.height

    scaling = 1.0 * max_size / max_dim
    width = int(image.width * scaling)
    height = int(image.height * scaling)
    return width, height


def unscaled_coords(image, max_size, coords):
    """Unscale co-ordinates from a scaled image to corresponding co-ordinates
    on the original image.

    Parameters

       `image`
          The original image, as a floof MediaImage ORM object.

       `max_size`
          The maximum size used when the image was scaled (such as with
          :func:`scaled_dimensions`), as an integer in pixels.

       `coords` any iterable of numeric coordinates.

    Returns `coords` scaled to the original image.

    """
    max_dim = max(image.width, image.height)

    if max_dim <= max_size:
        return coords

    scaling = 1.0 * max_dim / max_size
    return map(lambda x: int(x * scaling), coords)


def image_hash(fileobj):
    """Return a (hash, size) tuple of the `fileobj`.

    The size is in bytes and the hash is the SHA-256 hex digest.

    """
    hasher = hashlib.sha256()
    file_size = 0

    while True:
        buf = fileobj.read(HASH_BUFFER_SIZE)
        if not buf:
            break

        file_size += len(buf)
        hasher.update(buf)

    return hasher.hexdigest().decode('ascii'), file_size


def thumbnailify(image, size, crop_coords=None, max_aspect_ratio=2.0,
                 enlarge=False):
    """Resizes and optionally crops a given image.

    Parameters:

       `image`
          The PIL Image on which to operate; a modified copy of this image will
          be returned.

       `size`
          The desired size of the image in either width or height.  That is,
          the image will be resized so that the largest dimension is equal to
          `size`.  If both dimensions are equal or smaller, the image will only
          be resized if `enlage` is ``True``.
          Will crop automatically to maintain the `max_aspect_ratio`.

       `crop_coords`
          Defaults to ``None``.  If specified, it is a PIL-style (left, top,
          right, bottom) 4-tuple describing how to crop the image.  if
          `max_aspect_ratio` is not ``None``, then the right or bottom value
          may be reduced to maintain the ratio.

       `max_aspect_ratio`
          Defaults to ``2.0``.  The ratio is expressed as the size of the
          larger dimension (height or width) divided by the smaller.  If not
          ``None``, then it will be enforced by cropping the lower or right
          portions of the image.

       `enlarge`
          Defaults to ``False``.  If false, then an image that has neither its
          width nor height exceeding `size` will not be rescaled.

    """
    max_aspect_ratio *= 1.0  # coerce into float

    if max_aspect_ratio <= 0:
        raise ValueError('max_aspect_ratio must be greater than 0')

    if crop_coords:
        left, top, right, bottom = crop_coords
        width = right - left
        height = bottom - top
        orig_width, orig_height = image.size

        # For now, enforce that a image is only cropped within its own bounds.
        # PIL (intentionally) doesn't do this, but we want to avoid bogus input
        # yielding super-massive RAM-devouring "cropped" images.
        if left < 0:
            raise ValueError('Cannot crop beyond left-most bounds of image')
        if top < 0:
            raise ValueError('Cannot crop beyond upper bounds of image')
        if left + width > orig_width:
            raise ValueError('Cannot crop beyond right-most bounds of image')
        if top + height > orig_height:
            raise ValueError('Cannot crop beyond lower bounds of image')
    else:
        left = 0
        top = 0
        width, height = image.size

    if max_aspect_ratio is not None:
        # Restrict the aspect ratio
        height = min(height, int(width * max_aspect_ratio))
        width = min(width, int(height * max_aspect_ratio))

    cropped_image = image.crop((left, top, left + width, top + height))

    if not enlarge and width <= size and height <= size:
        # No need to resize
        return cropped_image

    # Resize necessary
    if width > height:
        new_size = (size, height * size // width)
    else:
        new_size = (width * size // height, size)

    return cropped_image.resize(new_size, Image.ANTIALIAS)
