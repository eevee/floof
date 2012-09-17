# encoding: utf8
from __future__ import division

import logging
import math

log = logging.getLogger(__name__)

DIRICHLET_PRIOR = [2, 2, 2]  # default; set by floof.model.initialize


def weighted_summation(dist):
    assert len(dist) == 3
    return sum([p * float(i) for p, i in zip(dist, xrange(-1, 2))])


def dirichlet_score(artwork, add=None, sub=None, prior=None):
    if not prior:
        prior = DIRICHLET_PRIOR
    prior_sum = weighted_summation(prior)
    prior_count = sum(prior)

    # This add/sub business is necessary as artwork.rating_sum won't include
    # any changes until after its event hooks (the functions below) finish,
    # but the event hooks call this function.
    if add is not None:
        prior_sum += add
    if sub is not None:
        prior_sum -= sub

    # Since our ratings are already stored as -1/0/1 and the only fudging we
    # perform we do through the prior, we cheat by summing & counting the
    # ratings rather than counting each category.
    score = ((artwork.rating_sum or 0) + prior_sum) / (artwork.rating_count + prior_count)

    # The score defaults to 0.  We want new art to start in the middle of the
    # pack, so scale the score so that the unajusted prior would yield 0.
    p = (weighted_summation(prior) / sum(prior) + 1) / 2
    exp = math.log(0.5, p)
    score = ((score + 1) / 2.0) ** exp * 2 - 1

    artwork.rating_score = score
    return score


def artwork_ratings_set_rating(artwork_rating, rating, oldrating, initiator):
    artwork = artwork_rating.artwork
    if artwork:
        dirichlet_score(artwork, add=rating, sub=oldrating)


def artwork_append_ratings(artwork, rating_obj, initiator):
    artwork.recount_ratings()
    artwork.rating_count += 1
    dirichlet_score(artwork, add=rating_obj.rating)


def artwork_remove_ratings(artwork, rating_obj, initiator):
    artwork.recount_ratings()
    artwork.rating_count -= 1
    dirichlet_score(artwork, sub=rating_obj.rating)


def artwork_set_ratings(artwork, rating_obj, oldrating_obj, initiator):
    dirichlet_score(artwork, add=rating_obj.rating, sub=oldrating_obj.rating)
