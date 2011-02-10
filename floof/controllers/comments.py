import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from floof.lib.base import BaseController, render
from floof.lib.decorators import user_must
from floof.lib.helpers import redirect
from floof import model
from floof.model import meta

log = logging.getLogger(__name__)

class CommentsController(BaseController):

    def _get_discussion(self, subcontroller, id, comment_id=None):
        """Returns `discussion`, `comment`.

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

        return discussion, comment

    def view(self, subcontroller, id, title=None, comment_id=None):
        """Show an entire comment thread."""
        c.discussion, c.comment = self._get_discussion(
            subcontroller, id, comment_id)

        # Fetch the parent hierarchy, for context, and the entire subtree
        if c.comment:
            c.comment_ancestors = c.comment.ancestors_query.all()
            c.comment_descendants = c.comment.descendants_query.all()
        else:
            c.comment_ancestors = None

            # No comment selected; show everything
            c.comment_descendants = c.discussion.comments

        c.comment_form = self.CommentForm()
        # TODO show all ancestors + entire tree + discussee somehow
        return render('/comments/view.mako')

    @user_must('comments.add')
    def write(self, subcontroller, id, title=None, comment_id=None):
        """Show a form for writing a comment.  Either top-level or a reply to
        another comment.
        """
        c.discussion, c.comment = self._get_discussion(
            subcontroller, id, comment_id)

        # Fetch the parent hierarchy, for context, and the entire subtree
        if c.comment:
            c.comment_ancestors = c.comment.ancestors_query.all()
            c.comment_descendants = c.comment.descendants_query.all()
        else:
            c.comment_ancestors = None

            # No comment selected; show everything
            c.comment_descendants = c.discussion.comments

        c.comment_form = self.CommentForm()
        return render('/comments/write.mako')

    @user_must('comments.add')
    def write_commit(self, subcontroller, id, title=None, comment_id=None):
        """Add a comment"""
        discussion, comment = self._get_discussion(subcontroller, id, comment_id)

        c.comment_form = self.CommentForm(request.params)
        if not c.comment_form.validate():
            # TODO
            abort(401)

        # Re-get the discussion with a separate query for locking purposes
        discussion = meta.Session.query(model.Discussion) \
            .with_lockmode('update') \
            .get(discussion.id)

        # XXX put this all in the Comment constructor?
        if comment_id:
            parent_comment = meta.Session.query(model.Comment).get(comment_id)
            if not parent_comment:
                abort(404)

            righter_comments = meta.Session.query(model.Comment) \
                .with_parent(discussion)
            righter_comments \
                .filter(model.Comment.left > parent_comment.right) \
                .update({ 'left': model.Comment.left + 2 })
            righter_comments \
                .filter(model.Comment.right > parent_comment.right) \
                .update({ 'right': model.Comment.right + 2 })

            new_comment_left = parent_comment.right
            new_comment_right = parent_comment.right + 1

            parent_comment.right += 2
            meta.Session.add(parent_comment)

        else:
            max_right, = meta.Session.query(func.max(model.Comment.right)) \
                .with_parent(discussion) \
                .one()

            if max_right is None:
                # FIRST POST LOLOL no seriously default to 1 and 2.
                max_right = 0

            new_comment_left = max_right + 1
            new_comment_right = max_right + 2

        new_comment = model.Comment(
            discussion=discussion,
            author=c.user,
            content=c.comment_form.message.data,
            left=new_comment_left,
            right=new_comment_right,
        )

        discussion.comment_count += 1
        meta.Session.add(new_comment)
        meta.Session.add(discussion)
        meta.Session.commit()

        # Redirect to the new comment
        redirect(url(controller=subcontroller, action='view',
                     id=id, title=title,
                     anchor="comment-{0}".format(new_comment.id)))
