import math
import sys

from floof import model
from floof.model.extensions import weighted_summation
from sqlalchemy.sql import func, select

from bootstrap import bootstrap_floof


if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
    print 'usage: python {0} config-file.ini#app-name'.format(sys.argv[0])
    sys.exit(1)

settings = bootstrap_floof(sys.argv[1])

# Build the Dirichlet smoothing/scoring function
# See floof.model.extensions.dirichlet_score for why we do each step
prior = model.extensions.DIRICHLET_PRIOR
prior_sum = weighted_summation(prior)
prior_count = sum(prior)

p = (prior_sum / prior_count + 1) / 2
exp = math.log(0.5, p)

score = func.sum(model.ArtworkRating.rating) + prior_sum
score /= func.count(model.ArtworkRating.rating) + prior_count
# Convert range from [-1, 1] to [0, 1], scale, then convert back to [-1, 1]
score = 2 * func.power((score + 1) / 2.0, exp) - 1

# Apply the scoring function to each artwork
artwork = model.Artwork.__table__
artwork_ratings = model.ArtworkRating.__table__
q = artwork.update().values(
    rating_score=func.coalesce(
        select([score]).
        where(artwork.c.id==artwork_ratings.c.artwork_id).
        group_by(artwork_ratings.c.artwork_id).
        as_scalar(), 0),
    rating_count=func.coalesce(
        select([func.count('*')]).
        where(artwork.c.id==artwork_ratings.c.artwork_id).
        group_by(artwork_ratings.c.artwork_id).
        as_scalar(), 0),
)
model.session.execute(q)
model.session.commit()
