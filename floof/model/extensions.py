from sqlalchemy.orm.interfaces import AttributeExtension

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
        if not (rating_obj.artwork is None):
            art = rating_obj.artwork
            art.rating_sum = art.rating_sum - oldrating + rating
        return rating

class ArtworkRatingsAttributeExtension(AttributeExtension):
    """AttributeExtension to act on the addition or removal of a rating to
       a piece of art.  Updates the rating_sum and num_ratings"""

    active_history = True

    def append(self, state, rating_obj, initiator):
        art = state.obj()
        art.rating_sum = art.rating_sum + rating_obj.rating
        art.num_ratings = art.num_ratings + 1

        return rating_obj

    def remove(self, state, rating_obj, initiator):
        art = state.obj()
        art.rating_sum = art.rating_sum - rating_obj.rating
        art.num_ratings = art.num_ratings - 1

        return rating_obj

    def set(self, state, rating_obj, oldrating_obj, initiator):
        art = state.obj()
        art.rating_sum = art.rating_sum - oldrating_obj.rating + rating_obj.rating
        return rating_obj

