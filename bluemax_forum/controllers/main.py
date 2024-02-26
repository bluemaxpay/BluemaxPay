# -*- coding: utf-8 -*-
# Part of kanakinfosystems. See LICENSE file for full copyright and licensing details.
import werkzeug.exceptions
import werkzeug.urls
import werkzeug.wrappers
from odoo import SUPERUSER_ID, http, tools, _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.exceptions import AccessError, UserError
from odoo.http import request


class WebsiteDiscussionForum(http.Controller):
    _post_per_page = 10
    _user_per_page = 30

    @http.route(['/discussion/forum'], type='http', auth="public", website=True, sitemap=True)
    def forum(self, **kwargs):
        domain = request.website.website_domain()
        forums = request.env['discussion.forum'].search(domain)
        return request.render("bluemax_forum.discussion_forum_all", {
            'forums': forums
        })

    def sitemap_forum(env, rule, qs):
        Forum = env['discussion.forum']
        dom = sitemap_qs2dom(qs, '/discussion/forum', Forum._rec_name)
        dom += env['website'].get_current_website().website_domain()
        for f in Forum.search(dom):
            loc = '/discussion/forum/%s' % slug(f)
            if not qs or qs.lower() in loc:
                yield {'loc': loc}

    def _prepare_user_values(self, **kwargs):
        kwargs.pop('edit_translations', None) # avoid nuking edit_translations
        values = {
            'user': request.env.user,
            'is_public_user': request.website.is_public_user(),
            'validation_email_sent': request.session.get('validation_email_sent', False),
            'validation_email_done': request.session.get('validation_email_done', False),
        }
        values.update({
            'header': kwargs.get('header', dict()),
            'searches': kwargs.get('searches', dict()),
        })
        if kwargs.get('forum'):
            values['forum'] = kwargs.get('forum')
        elif kwargs.get('forum_id'):
            values['forum'] = request.env['discussion.forum'].browse(int(kwargs.pop('forum_id')))
        forum = values.get('forum')
        if forum and forum is not True and not request.env.user._is_public():
            def _get_my_other_forums():
                post_domain = expression.OR(
                    [[('create_uid', '=', request.uid)]]
                )
                return request.env['discussion.forum'].search(expression.AND([
                    request.website.website_domain(),
                    [('id', '!=', forum.id)],
                    [('post_ids', 'any', post_domain)]
                ]))
            values['my_other_forums'] = tools.lazy(_get_my_other_forums)
        else:
            values['my_other_forums'] = request.env['discussion.forum']
        return values

    def _get_forum_post_search_options(self, forum=None, filters=None, my=None, create_uid=False, include_answers=False, **post):
        return {
            'allowFuzzy': not post.get('noFuzzy'),
            'create_uid': create_uid,
            'displayDescription': False,
            'displayDetail': False,
            'displayExtraDetail': False,
            'displayExtraLink': False,
            'displayImage': False,
            'filters': filters,
            'forum': str(forum.id) if forum else None,
            'include_answers': include_answers,
            'my': my,
        }

    @http.route(['/discussion/forum/all',
                 '/discussion/forum/all/page/<int:page>',
                 '/discussion/forum/<model("discussion.forum"):forum>',
                 '/discussion/forum/<model("discussion.forum"):forum>/page/<int:page>',
                 ], type='http', auth="public", website=True, sitemap=sitemap_forum)
    def questions(self, forum=None, tag=None, page=1, filters='all', my=None, sorting=None, search='', create_uid=False, include_answers=False, **post):
        Post = request.env['discussion.forum.post']

        author = request.env['res.users'].browse(int(create_uid))

        if author == request.env.user:
            my = 'mine'
        if sorting:
            # check that sorting is valid
            # retro-compatibility for V8 and google links
            try:
                sorting = werkzeug.urls.url_unquote_plus(sorting)
                Post._order_to_sql(sorting, None)
            except (UserError, ValueError):
                sorting = False

        if not sorting:
            sorting = 'anchor desc, create_date desc'

        options = self._get_forum_post_search_options(
            forum=forum,
            filters=filters,
            my=my,
            create_uid=author.id,
            include_answers=include_answers,
            my_profile=request.env.user == author,
            **post
        )
        question_count, details, fuzzy_search_term = request.website._search_with_fuzzy(
            "forum_posts_only", search, limit=page * self._post_per_page, order=sorting, options=options)
        question_ids = details[0].get('results', Post)
        question_ids = question_ids[(page - 1) * self._post_per_page:page * self._post_per_page]

        if not forum:
            url = '/discussion/forum/all'
        else:
            url = f"/discussion/forum/{slug(forum)}"

        pager = tools.lazy(lambda: request.website.pager(
            url=url, total=question_count, page=page, step=self._post_per_page,
            scope=self._post_per_page, url_args={}))

        values = self._prepare_user_values(forum=forum, searches=post)
        values.update({
            'author': author,
            'edit_in_backend': True,
            'question_ids': question_ids,
            'question_count': question_count,
            'search_count': question_count,
            'pager': pager,
            'filters': filters,
            'my': my,
            'sorting': sorting,
            'search': fuzzy_search_term or search,
            'original_search': fuzzy_search_term and search,
        })

        if forum:
            values['main_object'] = forum
        return request.render("bluemax_forum.discussion_forum_page", values)

    @http.route(['/discussion/forum/<model("discussion.forum"):forum>/ask'], type='http', auth="user", website=True)
    def forum_post(self, forum, **post):
        user = request.env.user
        if not user.email or not tools.single_email_re.match(user.email):
            return request.redirect("/discussion/forum/%s/user/%s/edit?email_required=1" % (slug(forum), request.session.uid))
        values = self._prepare_user_values(forum=forum, searches={}, new_question=True)
        return request.render("bluemax_forum.new_question", values)

    @http.route(['/discussion/forum/<model("discussion.forum"):forum>/new',
                '/discussion/forum/<model("discussion.forum"):forum>/<model("discussion.forum.post"):post_parent>/reply'],
                type='http', auth="user", methods=['POST'], website=True)
    def post_create(self, forum, post_parent=None, **post):
        if post.get('content', '') == '<p><br></p>':
            return request.render('http_routing.http_error', {
                'status_code': _('Bad Request'),
                'status_message': post_parent and _('Reply should not be empty.') or _('Question should not be empty.')
            })

        # post_tag_ids = forum._tag_to_write_vals(post.get('post_tags', ''))
        # if forum.has_pending_post:
        #     return request.redirect("/forum/%s/ask" % slug(forum))
        new_question = request.env['discussion.forum.post'].create({
            'forum_id': forum.id,
            'name': post.get('post_name') or (post_parent and 'Re: %s' % (post_parent.name or '')) or '',
            'content': post.get('content', False),
            'parent_id': post_parent and post_parent.id or False,
            'reply_parent_id': int(post.get('reply_parent_id')) if post.get('reply_parent_id', False) else False

        })
        if not post_parent:
            new_question.last_reply_uid = request.env.user.id
        if post_parent:
            post_parent._update_last_activity()
            post_parent.with_user(SUPERUSER_ID).last_reply_uid = request.env.user.id
        return request.redirect(f'discussion/forum/{slug(forum)}/{slug(post_parent) if post_parent else new_question.id}')


    @http.route(['''/discussion/forum/<model("discussion.forum"):forum>/<model("discussion.forum.post", "[('forum_id','=',forum.id),('parent_id','=',False)]"):question>''',
        '''/discussion/forum/<model("discussion.forum"):forum>/<model("discussion.forum.post", "[('forum_id','=',forum.id),('parent_id','=',False)]"):question>/page/<int:page>''',
        '''/discussion/forum/<model("discussion.forum"):forum>/<model("discussion.forum.post", "[('forum_id','=',forum.id),('parent_id','=',False)]"):question>/last/<string:last>'''],
                type='http', auth="public", website=True, sitemap=True)
    def question(self, forum, question, page=1, last=None, **post):
        user = request.env.user
        if question.parent_id:
            redirect_url = "/discussion/forum/%s/%s" % (slug(forum), slug(question.parent_id))
            return request.redirect(redirect_url, 301)
        filters = 'question'
        values = self._prepare_user_values(forum=forum, searches=post)

        schilds_ids = question.child_ids
        childs_ids = schilds_ids[(page - 1) * self._post_per_page:page * self._post_per_page]
        url = f'/discussion/forum/{slug(forum)}/{slug(question)}'
        pager = tools.lazy(lambda: request.website.pager(
            url=url, total=len(schilds_ids), page=page, step=self._post_per_page))
        total_pages = len(schilds_ids) // self._post_per_page  # Integer division to get total pages
        if last == 'post':
            redirect_url = ''
            last_url = pager.get('page_end').get('url')
            if schilds_ids:
                lastmsg_id = schilds_ids[-1:]
                redirect_url = last_url + '#post_message_'+ str(lastmsg_id.id)
            else:
                redirect_url = last_url + '#post_message_'+ str(question.id)
            return request.redirect(redirect_url)
        if total_pages == 0:
            total_pages = 1
        if len(schilds_ids) % self._post_per_page != 0:  # If there are remaining items
            total_pages += 1  # Increment total pages by 1
        values.update({
            'main_object': question,
            'question': question,
            'filters': filters,
            'pager': pager,
            'childs_post_ids':childs_ids,
            'page':page,
            'total_posts': len(schilds_ids),
            'reversed': reversed,
            'total_pages': total_pages
        })
        if (request.httprequest.referrer or "").startswith(request.httprequest.url_root):
            values['has_back_button_url'] = True

        # increment view counter
        question.sudo()._set_viewed()

        return request.render("bluemax_forum.post_description_full", values)

    @http.route('/discussion/forum/<model("discussion.forum"):forum>/post/<model("discussion.forum.post"):post>/save', type='http', auth="user", methods=['POST'], website=True)
    def post_save(self, forum, post, **kwargs):
        vals = {
            'content': kwargs.get('content'),
        }

        if 'post_name' in kwargs:
            if not kwargs.get('post_name').strip():
                return request.render('http_routing.http_error', {
                    'status_code': _('Bad Request'),
                    'status_message': _('Title should not be empty.')
                })

            vals['name'] = kwargs.get('post_name')
        post.write(vals)
        question = post.parent_id if post.parent_id else post
        return request.redirect("/discussion/forum/%s/%s" % (slug(forum), slug(question)))

    @http.route(['/open/edit/post/popup'], type="json", auth="user", methods=['POST'], website=True)
    def edit_post(self, post_id=None, **kw):
        values = {}
        user = request.env.user
        uid = user.id
        question = request.env['discussion.forum.post'].search([('id', '=', int(post_id))])
        forum = question.forum_id
        action_url = f"/discussion/forum/{ slug(forum) }/post/{slug(question)}/save"
        values['ReplyPopup'] = request.env['ir.ui.view']._render_template('bluemax_forum.reply_post_popup_main', {
            'post_name': question.name,
            'user': user,
            'question': question,
            'forum': forum,
            'action_url': action_url,
            'request': request,
            'is_edit_post_open': True
        })
        return values

    @http.route(['/open/reply/post/popup'], type="json", auth="user", methods=['POST'], website=True)
    def reply_post(self, post_id=None, **kw):
        values = {}
        user = request.env.user
        uid = user.id
        question = request.env['discussion.forum.post'].search([('id', '=', int(post_id))])
        forum = question.forum_id
        reply_post_id = kw.get('reply_post_id', False)
        action_url = f"/discussion/forum/{ slug(forum) }/{slug(question)}/reply"
        values['ReplyPopup'] = request.env['ir.ui.view']._render_template('bluemax_forum.reply_post_popup_main', {
            'user': user,
            'question': question,
            'forum': forum,
            'action_url': action_url,
            'request': request,
            'reply_post_id': reply_post_id,
            'is_edit_post_open': False
        })
        return values

    @http.route(['/discussion/forum/post/anchor'], type="json", auth="user", methods=['POST'], website=True)
    def anchore_post(self, post_id=None, **kw):
        if not request.env.user.has_group('bluemax_forum.group_moderator'):
            raise AccessError(_('Opps! Only Moderator can anchor post'))
        values = {}
        user = request.env.user
        uid = user.id
        question = request.env['discussion.forum.post'].search([('id', '=', int(post_id))])
        question._update_anchor_post()
        return {
            'success':True
        }

    @http.route('/discussion/forum/<model("discussion.forum"):forum>/question/<model("discussion.forum.post"):question>/delete', type='http', auth="user", methods=['POST', 'GET'], website=True)
    def question_delete(self, forum, question, **kwarg):
        if not request.env.user.has_group('bluemax_forum.group_moderator'):
            raise AccessError(_('Opps! Only Moderator can delete post'))
        url = ''
        if question.parent_id:
            url = '/discussion/forum/%s/%s' %(slug(forum), slug(question.parent_id))
        else:
            url = "/discussion/forum/%s" % (slug(forum))
        question.active = False
        return request.redirect(url)

    @http.route('/discussion/forum/<model("discussion.forum"):forum>/question/<model("discussion.forum.post"):question>/close', type='http', auth="user", methods=['POST', 'GET'], website=True)
    def question_close(self, forum, question, **post):
        if not request.env.user.has_group('bluemax_forum.group_moderator'):
            raise AccessError(_('Opps! Only Moderator can close thread'))
        question.close()
        return request.redirect("/discussion/forum/%s/%s" % (slug(forum), slug(question)))

    @http.route('/discussion/forum/<model("discussion.forum"):forum>/question/<model("discussion.forum.post"):question>/reopen', type='http', auth="user", methods=['POST', 'GET'], website=True)
    def question_reopen(self, forum, question, **post):
        if not request.env.user.has_group('bluemax_forum.group_moderator'):
            raise AccessError(_('Opps! Only Moderator can reopen post'))
        question.reopen()
        return request.redirect("/discussion/forum/%s/%s" % (slug(forum), slug(question)))

    @http.route('/discussion/forum/<model("discussion.forum"):forum>/question/<model("discussion.forum.post"):question>/delete_posts_and_ban_user', type='http', auth="user", methods=['POST', 'GET'], website=True)
    def question_delete_posts_and_ban_user(self, forum, question, **post):
        if not request.env.user.has_group('bluemax_forum.group_moderator'):
            raise AccessError(_('Opps! Only Moderator can delete all post and ban user.'))
        user = question.create_uid
        posts = request.env['discussion.forum.post'].search([('create_uid', '=', user.id)])
        posts.write({'active': False})
        user.with_user(SUPERUSER_ID).active = False
        return request.redirect("/discussion/forum/%s" % (slug(forum)))
