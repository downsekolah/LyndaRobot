import html
from typing import List

from telegram import Update, ParseMode
from telegram.error import BadRequest
from telegram.ext import MessageHandler, CommandHandler, Filters, run_async, CallbackContext
from telegram.utils.helpers import mention_html

from lynda import dispatcher, WHITELIST_USERS, SARDEGNA_USERS
from lynda.modules.helper_funcs.chat_status import is_user_admin, user_admin, can_restrict, connection_status
from lynda.modules.log_channel import loggable
from lynda.modules.sql import antiflood_sql as sql

FLOOD_GROUP = 3


@run_async
@loggable
def check_flood(update: Update, context: CallbackContext) -> str:
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message
    log_message = ""

    if not user:  # ignore channels
        return log_message

    # ignore admins and whitelists
    if (is_user_admin(chat, user.id)
            or user.id in WHITELIST_USERS
            or user.id in SARDEGNA_USERS):
        sql.update_flood(chat.id, None)
        return log_message

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return log_message

    try:
        context.bot.restrict_chat_member(chat.id, user.id, can_send_messages=False)
        context.bot.send_message(
            chat.id,
            f"*mutes {mention_html(user.id, user.first_name)} permanently*\nStop Antibacod digrup ini!",
            parse_mode=ParseMode.HTML)
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#Yahahahaha hayuk ke mute\n"
            f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
            f"AntiBacod diaktifin digrup ini.\nNunggu admoon ae unmute diri lu")

        return log_message

    except BadRequest:
        msg.reply_text(
            "Gw gabisa kick orang disini cok, kako gitu gw matiin dulu AntiBacod nya")
        sql.set_flood(chat.id, 0)
        log_message = (
            "<b>{chat.title}:</b>\n"
            "#INFO\n"
            "Gabisa kick org disini, yodah gw matiin dlo AntiBacod nya")

        return log_message


@run_async
@connection_status
@user_admin
@can_restrict
@loggable
def set_flood(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    args = context.args
    log_message = ""

    update_chat_title = chat.title
    message_chat_title = update.effective_message.chat.title

    if update_chat_title == message_chat_title:
        chat_name = ""
    else:
        chat_name = f" in <b>{update_chat_title}</b>"

    if len(args) >= 1:

        val = args[0].lower()

        if val in ('off', 'no', '0'):
            sql.set_flood(chat.id, 0)
            message.reply_text(
                "Antibacodnya dah dimatiin{}.".format(chat_name),
                parse_mode=ParseMode.HTML)

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat.id, 0)
                message.reply_text(
                    "AntiBacod nya dah di matiin{}.".format(chat_name),
                    parse_mode=ParseMode.HTML)
                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#SETAntibacodD\n"
                    f"<b>Admin</b>: {mention_html(user.id, user.first_name)}\n"
                    f"Matiin AntiBacod.")

            elif amount < 3:
                message.reply_text(
                    "Antibacod bisa di disable dengan di set nomor 0(matiin), paling tinggi 3")
            else:
                sql.set_flood(chat.id, amount)
                message.reply_text(
                    "AntiBacod dah di update {}{}".format(
                        amount, chat_name), parse_mode=ParseMode.HTML)
                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#SETAntibacod\n"
                    f"<b>Admin</b>: {mention_html(user.id, user.first_name)}\n"
                    f"Set Antibacod to <code>{amount}</code>.")

            return log_message
        else:
            message.reply_text(
                "Argument yang bagus kawan Tapi kasihlah nomornya, 'off', or 'no'.")

    return log_message


@run_async
@connection_status
def flood(update: Update, _):
    chat = update.effective_chat
    update_chat_title = chat.title
    message_chat_title = update.effective_message.chat.title

    if update_chat_title == message_chat_title:
        chat_name = ""
    else:
        chat_name = f" in <b>{update_chat_title}</b>"

    limit = sql.get_flood_limit(chat.id)

    if limit == 0:
        update.effective_message.reply_text(
            f"Gw gk megang penuh antibacodnya{chat_name}!",
            parse_mode=ParseMode.HTML)
    else:
        update.effective_message.reply_text(
            f"Gw bakalan doxxing user apabila banyak bacod "
            f"more than {limit} consecutive messages{chat_name}.",
            parse_mode=ParseMode.HTML)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, _user_id):
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return "*Gk megang penuh antibacod."
    else:
        return "AntiBacod di set ke `{}` messages.".format(limit)


__help__ = """
-> `/flood`
Get the current flood control setting

──「 *Admin only:* 」──
-> `/setflood` <int/'no'/'off'>
Aktifin AntiBacod
"""

FLOOD_BAN_HANDLER = MessageHandler(
    Filters.all & ~Filters.status_update & Filters.group,
    check_flood)
SET_FLOOD_HANDLER = CommandHandler("setflood", set_flood, pass_args=True)
FLOOD_HANDLER = CommandHandler("flood", flood)

dispatcher.add_handler(FLOOD_BAN_HANDLER, FLOOD_GROUP)
dispatcher.add_handler(SET_FLOOD_HANDLER)
dispatcher.add_handler(FLOOD_HANDLER)

__mod_name__ = "AntiFlood"
__handlers__ = [(FLOOD_BAN_HANDLER, FLOOD_GROUP),
                SET_FLOOD_HANDLER, FLOOD_HANDLER]
