# encoding: utf8
from __future__ import division

from math import sqrt

from sqlalchemy.orm.interfaces import AttributeExtension

def wilson_score(n, total):
    """Given a number of normalized [-1, 1] ratings and their total, calculates
    the expected score, using the Wilson score interval.  Blah, blah, math."""
    # See: http://www.evanmiller.org/how-not-to-sort-by-average-rating.html
    # And: http://amix.dk/blog/post/19588
    # This is slightly modified, as the given formula is normally for binary
    # data; i.e., ratings are 0 or 1.  Ours are normalized to [0, 1], then
    # unnormalized back to [-1, 1].
    phat = (total / n + 1) / 2  # normalize [-n, n] to [0, 1]
    # Confidence, as quantile of the SND.  z = 1.0 → 85%; z = 1.6 → 95%.
    z = 1.03643337714489

    print n, total, phat, z
    score = (
        (phat + z**2 / (2 * n) - z * sqrt(
            (phat * (1 - phat) + z**2 / (4 * n)) / n))
        / (1 + z**2 / n)
    )

    return score * 2 - 1  # denormalize [0, 1] to [-1, 1]

def recalc_wilson_score(artwork):
    if artwork.rating_count:
        artwork.rating_score = wilson_score(
            artwork.rating_count, artwork.rating_sum)
    else:
        artwork.rating_score = None

class RatingAttributeExtension(AttributeExtension):
    """AttributeExtension to act on the change of a rating.  Updates
       the rating_sum of the artwork"""

    active_history = True

    def append(self, state, value, initiator):
        return value

    def remove(self, state, value, initiator):
        return value

    def set(self, state, rating, oldrating, initiator):
        """Update the rating sum of the artwork"""
        rating_obj = state.obj()
        artwork = rating_obj.artwork
        if artwork:
            artwork.rating_sum = artwork.rating_sum - oldrating + rating
            recalc_wilson_score(artwork)
        return rating

class ArtworkRatingsAttributeExtension(AttributeExtension):
    """AttributeExtension to act on the addition or removal of a rating to
       a piece of art.  Updates the rating_* columns"""

    active_history = True

    def append(self, state, rating_obj, initiator):
        artwork = state.obj()
        artwork.rating_count += 1
        artwork.rating_sum += rating_obj.rating
        recalc_wilson_score(artwork)

        return rating_obj

    def remove(self, state, rating_obj, initiator):
        artwork = state.obj()
        artwork.rating_count -= 1
        artwork.rating_sum -= rating_obj.rating
        recalc_wilson_score(artwork)

        return rating_obj

    def set(self, state, rating_obj, oldrating_obj, initiator):
        artwork = state.obj()
        artwork.rating_sum = (
            artwork.rating_sum - oldrating_obj.rating + rating_obj.rating)
        recalc_wilson_score(artwork)

        return rating_obj

