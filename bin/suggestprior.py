import sys

from floof import model
from sqlalchemy.sql import func

from bootstrap import bootstrap_floof


if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
    print 'usage: python {0} config-file.ini#app-name'.format(sys.argv[0])
    sys.exit(1)

settings = bootstrap_floof(sys.argv[1])

print 'Calculating mean number of down / neutral / up votes per artwork...'

rating = model.ArtworkRating.rating
artwork_id = model.ArtworkRating.artwork_id

sq = model.session.query(
    artwork_id,
    rating.label('rating'),
    func.count(rating).label('count'),
).group_by(artwork_id, rating).subquery()

q = model.session.query(
    sq.c.rating,
    func.avg(sq.c.count),
).group_by(sq.c.rating)

prior = dict(x for x in q.all())
p = [str(round(prior.get(float(i), 0), 3)) for i in range(-1, 2)]
total = model.session.query(rating).count()
print 'scoring.prior =', ' '.join(p), ' # (n = {0})'.format(total)
