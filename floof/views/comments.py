# encoding: utf8
import logging

from pyramid.httpexceptions import HTTPBadRequest, HTTPSeeOther
from pyramid.exceptions import NotFound
from pyramid.view import view_config
from sqlalchemy.sql import func
from sqlalchemy.orm.exc import NoResultFound

from floof import model
from floof.lib.gallery import GallerySieve
from floof.model import meta

log = logging.getLogger(__name__)

# XXX
from floof.views.art import CommentForm

@view_config(
    route_name='comments.list',
    request_method='GET',
    renderer='comments/view.mako')
def view_discussion(discussion, request):
    """Show an entire comment thread."""
    # TODO show all ancestors + entire tree + discussee somehow
    return dict(
        comment=None,
        discussion=discussion,

        comment_ancestors=None,
        comment_descendants=discussion.comments,
        comment_form=CommentForm(),
    )

@view_config(
    route_name='comments.view',
    request_method='GET',
    renderer='comments/view.mako')
def view_single_thread(comment, request):
    """Show the comment thread starting at a single comment."""
    # TODO show all ancestors + entire tree + discussee somehow
    return dict(
        comment=comment,
        discussion=comment.discussion,

        comment_ancestors=comment.ancestors_query.all(),
        comment_descendants=comment.descendants_query.all(),
        comment_form=CommentForm(),
    )


@view_config(
    route_name='comments.write',
    permission='comments.add',
    request_method='GET',
    renderer='comments/write.mako')
def reply_to_discussion(discussion, request):
    """Show a form for writing a comment.  Either top-level or a reply to
    another comment.
    """
    # XXX this is oddly identical to the stuff above!
    return dict(
        comment=None,
        discussion=discussion,

        comment_ancestors=None,
        comment_descendants=discussion.comments,
        comment_form=CommentForm(),
    )

@view_config(
    route_name='comments.reply',
    permission='comments.add',
    request_method='GET',
    renderer='comments/write.mako')
def reply_to_comment(comment, request):
    """Show a form for writing a comment.  Either top-level or a reply to
    another comment.
    """
    # XXX this is oddly identical to the stuff above!
    return dict(
        comment=comment,
        discussion=comment.discussion,

        comment_ancestors=comment.ancestors_query.all(),
        comment_descendants=comment.descendants_query.all(),
        comment_form=CommentForm(),
    )

@view_config(
    route_name='comments.write',
    permission='comments.add',
    request_method='POST',
    renderer='comments/write.mako')
@view_config(
    route_name='comments.reply',
    permission='comments.add',
    request_method='POST',
    renderer='comments/write.mako')
# XXX split me up
def reply_to_discussion_commit(discussion_or_comment, request):
    """Add a comment"""
    if isinstance(discussion_or_comment, model.Discussion):
        discussion = discussion_or_comment
        comment = None
    elif isinstance(discussion_or_comment, model.Comment):
        discussion = discussion_or_comment.discussion
        comment = discussion_or_comment

    comment_form = CommentForm(request.POST)
    if not comment_form.validate():
        # TODO
        return HTTPBadRequest()

    # Re-get the discussion with a separate query for locking purposes
    # XXX necessary?
    discussion = meta.Session.query(model.Discussion) \
        .with_lockmode('update') \
        .get(discussion.id)

    # XXX put this all in the Comment constructor?
    if comment:
        righter_comments = meta.Session.query(model.Comment) \
            .with_parent(discussion)
        righter_comments \
            .filter(model.Comment.left > comment.right) \
            .update({ 'left': model.Comment.left + 2 })
        righter_comments \
            .filter(model.Comment.right > comment.right) \
            .update({ 'right': model.Comment.right + 2 })

        new_comment_left = comment.right
        new_comment_right = comment.right + 1

        comment.right += 2
        meta.Session.add(comment)

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
        author=request.user,
        content=comment_form.message.data,
        left=new_comment_left,
        right=new_comment_right,
    )

    discussion.comment_count += 1
    meta.Session.add(new_comment)
    meta.Session.add(discussion)
    meta.Session.flush()  # Need to get the new comment's id

    # Redirect to the new comment
    return HTTPSeeOther(
        location=request.route_url('comments.view', comment=new_comment, _anchor="comment-{0}".format(new_comment.id)))
