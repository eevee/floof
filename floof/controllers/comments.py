import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from floof.lib.base import BaseController, render
from floof import model
from floof.model import meta

log = logging.getLogger(__name__)

class CommentsController(BaseController):

    def _get_discussion(self, subcontroller, id, comment_id=None):
        """Returns `discussee`, `discussion`, `comment`.

        `discussee` is the object to which the discussion is attached: e.g., an
        artwork.

        `comment` may be None.
        """
        # XXX both of these should eagerload the discussion
        # Fetch the attached object
        if subcontroller == 'art':
            table = model.Artwork
        else:
            abort(404)

        discussee = meta.Session.query(table).get(id)
        if not discussee:
            abort(404)

        # Fetch discussion and comment, if applicable
        discussion = discussee.discussion

        if comment_id:
            comment = meta.Session.query(model.Comment).get(comment_id)
            if comment.discussion != discussion:
                abort(404)
        else:
            comment = None

        return discussee, discussion, comment

    def view(self, subcontroller, id, title=None, comment_id=None):
        """Show an entire comment thread."""
        discussee, discussion, comment = self._get_discussion(
            subcontroller, id, comment_id)

        # Grab all parents, to provide context.  Ancestors are any comments
        # whose left and right contain this comment's left.
        c.comment_ancestry = meta.Session.query(model.Comment) \
            .with_parent(discussion) \
            .filter(model.Comment.left < comment.left) \
            .filter(model.Comment.right > comment.left) \
            .order_by(model.Comment.left.asc()) \
            .all()

        # Pull the comment subtree.  Descendants are any comments with a left
        # (or right) between comment.left and comment.right.
        c.comment_subtree = meta.Session.query(model.Comment) \
            .with_parent(discussion) \
            .filter(model.Comment.left.between(comment.left, comment.right)) \
            .order_by(model.Comment.left.asc()) \
            .all()

        c.artwork = discussee  # XXX AUGH; used in comments_lib
        # TODO show all ancestors + entire tree + discussee somehow
        return render('/comments/view.mako')

    def write_commit(self, subcontroller, id, title=None):
        discussee, discussion, comment = self._get_discussion(subcontroller, id)

        c.comment_form = self.CommentForm(request.params)
        if not c.comment_form.validate():
            # TODO
            abort(401)

        # Re-get the discussion with a separate query for locking purposes
        discussion = meta.Session.query(model.Discussion) \
            .with_lockmode('update') \
            .get(discussion.id)

        # TODO put this in the Comment constructor?
        max_right, = meta.Session.query(func.max(model.Comment.right)) \
            .with_parent(discussion) \
            .one()

        new_comment = model.Comment(
            discussion=discussion,
            author=c.user,
            content=c.comment_form.message.data,
            left=max_right + 1,
            right=max_right + 2,
        )

        discussion.comment_count += 1
        meta.Session.add(discussion)
        meta.Session.commit()

        # Redirect to the new comment
        redirect(url(controller=subcontroller, action='view',
                     id=id, title=title,
                     anchor="comment-{0}".format(new_comment.id)))
