/** @odoo-module **/

import { markup } from "@odoo/owl";
import dom from "@web/legacy/js/core/dom";
import { cookie } from "@web/core/browser/cookie";;
import { loadWysiwygFromTextarea } from "@web_editor/js/frontend/loadWysiwygFromTextarea";
import publicWidget from "@web/legacy/js/public/public_widget";
import { session } from "@web/session";
import { escape } from "@web/core/utils/strings";
import { _t } from "@web/core/l10n/translation";
import { renderToElement } from "@web/core/utils/render";
publicWidget.registry.websiteDiscussionForum = publicWidget.Widget.extend({
    selector: '.website_discussion_forum',
    events: {
        'click .reply_post_msg': 'OnPostReplyMsg',
        'click .o_wforum_discard_btn': 'remove_popup_class',
        'click .anchor_post_msg_cl': 'OnClickAnchor',
        'click .edit_post_msg_cl': 'OnClickEditPost',
        'click .delete_post_msg_cl': 'OnDeletePost'
    },
    init(options) {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
        this.orm = this.bindService("orm");
        this.notification = this.bindService("notification");
    },
    start: function () {
        var self = this;

        this.lastsearch = [];
        $('#forum_post_list_main').basictable({breakpoint: 768});
        // float-start class messes up the post layout OPW 769721
        $('span[data-oe-model="forum.post"][data-oe-field="content"]').find('img.float-start').removeClass('float-start');

        $('textarea.o_wysiwyg_loader').toArray().forEach((textarea) => {
            var $textarea = $(textarea);
            // var post_id = self.getPostLastId($textarea.attr('id'));
            // var reply_containt = '';
            // if(post_id){
            //     debugger;
            //     var elementExists = $('div[qpost_id="question_post_' + post_id + '"]').length > 0;
            //     if(elementExists){
            //         var parent_containt = $('div[qpost_id="question_post_' + post_id + '"]').html();
            //     }
            // }
            var $form = $textarea.closest('form');
            var hasFullEdit = true;

            var options = {
                toolbarTemplate: 'bluemax_forum.web_editor_toolbar',
                toolbarOptions: {
                    showColors: false,
                    showFontSize: false,
                    showHistory: true,
                    showHeading1: false,
                    showHeading2: false,
                    showHeading3: false,
                    showLink: hasFullEdit,
                    showImageEdit: hasFullEdit,
                },
                recordInfo: {
                    context: self._getContext(),
                    res_model: 'discussion.forum.post',
                    res_id: +window.location.pathname.split('-').slice(-1)[0].split('/')[0],
                },
                resizable: true,
                userGeneratedContent: true,
                height: 350,
            };
            options.allowCommandLink = hasFullEdit;
            options.allowCommandImage = hasFullEdit;
            loadWysiwygFromTextarea(self, $textarea[0], options).then(wysiwyg => {
                // float-start class messes up the post layout OPW 769721
                $form.find('.note-editable').find('img.float-start').removeClass('float-start');
            });
        });
        return this._super.apply(this, arguments);
    },
    remove_popup_class: function(ev){
        $(ev.currentTarget).closest('#reply_post_popup_main').remove();
    },
    getPostLastId(textboxId) {
        // Use regular expression to match the last integer in the ID
        var match = textboxId.match(/\d+$/);
        // If there's a match, return the last integer, otherwise return null
        return match ? parseInt(match[0]) : null;
    },
    OnPostReplyMsg: function(ev){
        if(session.is_website_user){
            window.location.href="/web/login?redirect="+window.location.href;
            return false;
        }
        var self = this;
        var post_id = parseInt($(ev.currentTarget).data('question_post_id'), 10);
        var reply_post_id = parseInt($(ev.currentTarget).data('reply_post_id'), 10);
        this.rpc("/open/reply/post/popup", {
            post_id: post_id,
            reply_post_id: reply_post_id
        }).then((data)=>{
            self.$el.find('#reply_post_popup_main').remove();
            self.$el.append(data['ReplyPopup']);
            // self.$el.find('#post_reply_modal_popup').on('shown.bs.modal', function (e) {
            self.trigger_up('widgets_start_request', {
                $target: self.$el,
            });
            // })
            // self.$el.find('#post_reply_modal_popup').modal('show');
        });
    },
    OnClickAnchor: function(ev){
        var self = this;
        var post_id = parseInt($(ev.currentTarget).data('question_post_id'), 10);
        this.rpc("/discussion/forum/post/anchor", {
            post_id: post_id
        }).then((data)=>{
            this.notification.add(_t("Anchor successfully"), {
                type: "success",
            });
        });
    },
    OnClickEditPost: function(ev){
        var self = this;
        var post_id = parseInt($(ev.currentTarget).data('question_post_id'), 10);
        var reply_post_id = parseInt($(ev.currentTarget).data('reply_post_id'), 10);
        this.rpc("/open/edit/post/popup", {
            post_id: post_id,
        }).then((data)=>{
            self.$el.find('#reply_post_popup_main').remove();
            self.$el.append(data['ReplyPopup']);
            self.trigger_up('widgets_start_request', {
                $target: self.$el,
            });
        });
    },
    OnDeletePost: function(ev){
        
    }
});