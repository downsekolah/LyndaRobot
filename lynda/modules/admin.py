import html
from typing import List

import requests
from telegram import Update, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters, run_async, CallbackContext
from telegram.utils.helpers import mention_html

from lynda import dispatcher, TOKEN
from lynda.modules.disable import DisableAbleCommandHandler
from lynda.modules.helper_funcs.chat_status import bot_admin, can_promote, user_admin, can_pin, connection_status
from lynda.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from lynda.modules.log_channel import loggable


@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def promote(update: Update, context: CallbackContext) -> str:
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    log_message = ""

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return log_message

    try:
        user_member = chat.get_member(user_id)
    except Exception:
        return log_message

    if user_member.status in ['administrator', 'creator']:
        message.reply_text("Jadiin gw admin dulu lah tod")
        return log_message

    if user_id == context.bot.id:
        message.reply_text("Cok gw gabisa promite diri gw jd admin, hadehhh")
        return log_message

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(context.bot.id)

    try:
        context.bot.promoteChatMember(
            chat.id, user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            # can_promote_members=bot_member.can_promote_members,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages)
    except BadRequest as err:
        if err.message == 'User_not_mutual_contact':
            message.reply_text("Gw gabisa promote orang di grup ini, coba cek permission gw.")
        else:
            message.reply_text('Error pas mau promote, mungkin faktor face.')
        return log_message
    context.bot.sendMessage(chat.id, f"Promote jadi berhasil ya tod <b>{user_member.user.first_name or user_id}</b>!",
                    parse_mode=ParseMode.HTML)

    log_message += (f"<b>{html.escape(chat.title)}:</b>\n"
                    "#PROMOTED\n"
                    f"<b>Admoon:</b> {mention_html(user.id, user.first_name)}\n"
                    f"<b>Pengguna pantek:</b> {mention_html(user_member.user.id, user_member.user.first_name)}")

    return log_message


@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def demote(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    log_message = ""

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("Lu bukan user nih..")
        return log_message

    try:
        user_member = chat.get_member(user_id)
    except Exception as e:
        print(e)
        return log_message

    if user_member.status == 'creator':
        message.reply_text("Dia Owner tolo, mana bisa di demote")
        return log_message

    if user_member.status != 'administrator':
        message.reply_text("Gw gabisa demote dia, krn dia yang promote in cok")
        return log_message

    if user_id == context.bot.id:
        message.reply_text("Lu gblk apa gimana? mana bisa gw demote diri gw sendiri")
        return log_message

    try:
        context.bot.promoteChatMember(
            chat.id, user_id,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False)

        context.bot.sendMessage(chat.id, f"aowkoakwoaowkoakw mampos di kudeta <b>{user_member.user.first_name or user_id}</b>!",
                        parse_mode=ParseMode.HTML)

        log_message += (f"<b>{html.escape(chat.title)}:</b>\n"
                        f"#DEMOTED\n"
                        f"<b>Admoon:</b> {mention_html(user.id, user.first_name)}\n"
                        f"<b>User pantek:</b> {mention_html(user_member.user.id, user_member.user.first_name)}")

        return log_message
    except BadRequest:
        message.reply_text("Cok gw gabisa demote, atau ni admon nge kudeta gw?"
                        "user, lu gk bisa ngelakuin itu")
        return log_message


# Until the library releases the method
@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
def set_title(update: Update, context: CallbackContext):
    args = context.args
    chat = update.effective_chat
    message = update.effective_message

    user_id, title = extract_user_and_text(message, args)
    try:
        user_member = chat.get_member(user_id)
    except Exception as e:
        print(e)
        return

    if not user_id:
        message.reply_text("Dia bukan user.")
        return

    if user_member.status == 'creator':
        message.reply_text("Lah dia kan owner,mana bisa di ubah tittlenya")
        return

    if user_member.status != 'administrator':
        message.reply_text("Gk bisalah pantek gw ngasi tittle ke non admin")
        return

    if user_id == context.bot.id:
        message.reply_text("User pantek gw gabisa ngasi tittle ke gw sendiri ya sayang")
        return

    if not title:
        message.reply_text("Jangan ngasi Blank Tittle woy")
        return

    if len(title) > 16:
        message.reply_text("The title length is longer than 16 characters.\nTruncating it to 16 characters.")

    result = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/setChatAdministratorCustomTitle"
        f"?chat_id={chat.id}"
        f"&user_id={user_id}"
        f"&custom_title={title}")
    status = result.json()["ok"]

    if status is True:
        context.bot.sendMessage(chat.id, f"Acieee di promote jadi admoon <code>{user_member.user.first_name or user_id}</code> "
                                f"to <code>{title[:16]}</code>!", parse_mode=ParseMode.HTML)
    else:
        description = result.json()["description"]
        if description == "Bad Request: not enough rights to change custom title of the user":
            message.reply_text("I can't set custom title for admins that I didn't promote!")


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
def pin(update: Update, context: CallbackContext) -> str:
    args = context.args
    user = update.effective_user
    chat = update.effective_chat

    is_group = chat.type != "private" and chat.type != "channel"
    prev_message = update.effective_message.reply_to_message

    is_silent = True
    if len(args) >= 1:
        is_silent = not (args[0].lower() == 'notify' or args[0].lower() == 'loud' or args[0].lower() == 'violent')

    if prev_message and is_group:
        try:
            context.bot.pinChatMessage(chat.id, prev_message.message_id, disable_notification=is_silent)
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#Pesan ke pin\n"
            f"<b>Admoon:</b> {mention_html(user.id, user.first_name)}")

        return log_message


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
def unpin(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user

    try:
        context.bot.unpinChatMessage(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#Pesan udah di unpin\n"
        f"<b>Admoon:</b> {mention_html(user.id, user.first_name)}")

    return log_message


@run_async
@bot_admin
@user_admin
def invite(update: Update, context: CallbackContext):
    chat = update.effective_chat

    if chat.username:
        update.effective_message.reply_text(chat.username)
    elif chat.type in [chat.SUPERGROUP, chat.CHANNEL]:
        bot_member = chat.get_member(context.bot.id)
        if bot_member.can_invite_users:
            invitelink = context.bot.exportChatInviteLink(chat.id)
            update.effective_message.reply_text(invitelink)
        else:
            update.effective_message.reply_text("Gw ga ada access ke link itu")
    else:
        update.effective_message.reply_text("Gw cuma bisa ngasi link SuperGroup doang sama channel")


@run_async
@connection_status
def adminlist(update: Update, context: CallbackContext):
    chat = update.effective_chat

    chat_id = chat.id
    update_chat_title = chat.title
    message_chat_title = update.effective_message.chat.title

    administrators = context.bot.getChatAdministrators(chat_id)

    if update_chat_title == message_chat_title:
        chat_name = "this chat"
    else:
        chat_name = update_chat_title

    text = f"Admins in *{chat_name}*:"

    for admin in administrators:
        user = admin.user
        name = f"[{user.first_name + (user.last_name or '')}](tg://user?id={user.id})"
        text += f"\n - {name}"

    update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def __chat_settings__(chat_id, user_id):
    return "You are *admin*: `{}`".format(dispatcher.bot.get_chat_member(chat_id, user_id).status in ("administrator", "creator"))


__help__ = """
-> `/adminlist`
Daftar admoon pantek digrup ini :

──「 *Admin only* 」──
-> `/pin`
Balas sebuah pesan, niscaya gw akan pin pesan itu.
-> `/unpin`
Balas sebuah pesan,niscaya gw akan unpin pesan nya
-> `/invitelink`
geDapetin link grupnya
-> `/promote`
Biar bisa promote orang laen jadi admoon
-> `/demote`
Biar bisa kudeta admoon
-> `/settitle`
Ngasi tittle ke admoon
"""

ADMINLIST_HANDLER = DisableAbleCommandHandler(["adminlist", "admins"], adminlist)

PIN_HANDLER = CommandHandler("pin", pin, pass_args=True, filters=Filters.group)
UNPIN_HANDLER = CommandHandler("unpin", unpin, filters=Filters.group)

INVITE_HANDLER = DisableAbleCommandHandler("invitelink", invite, filters=Filters.group)

PROMOTE_HANDLER = CommandHandler("promote", promote, pass_args=True)
DEMOTE_HANDLER = CommandHandler("demote", demote, pass_args=True)

SET_TITLE_HANDLER = CommandHandler("settitle", set_title, pass_args=True)

dispatcher.add_handler(ADMINLIST_HANDLER)
dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(SET_TITLE_HANDLER)

__mod_name__ = "Admin"
__command_list__ = ["adminlist", "admins", "invitelink"]
__handlers__ = [ADMINLIST_HANDLER, PIN_HANDLER, UNPIN_HANDLER,
                INVITE_HANDLER, PROMOTE_HANDLER, DEMOTE_HANDLER, SET_TITLE_HANDLER]
