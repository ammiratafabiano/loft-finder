import asyncio
import random
import time
from datetime import datetime

import telegram
from telegram import MessageEntity, InlineKeyboardButton, InlineKeyboardMarkup
import logging
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler, \
    PicklePersistence, ApplicationBuilder
from concurrent.futures import ProcessPoolExecutor

from costants import ADMIN_ID, BOT_TOKEN
from conversationid import *
from services.storage import storage
from models.user import User
from utils import format_amount, get_time
from models.watch import Watch, Adv
from actions import *

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


def bot_handler():
    persistence = PicklePersistence(filepath='conversationbot')
    app = ApplicationBuilder().token(BOT_TOKEN).persistence(persistence).build()

    conv_addwatch_handler = ConversationHandler(
        entry_points=[CommandHandler("addwatch", addwatch)],
        states={
            ASK_SOURCE: [
                CommandHandler('cancel', cancel),
                CallbackQueryHandler(store_source)
            ],
            ASK_CITY: [
                CommandHandler('cancel', cancel),
                MessageHandler(filters.ALL, store_city)

            ],
            ASK_TYPE: [
                CommandHandler('cancel', cancel),
                MessageHandler(filters.ALL, store_type)
            ],
            ASK_CATEGORY: [
                CommandHandler('cancel', cancel),
                MessageHandler(filters.ALL, store_category)
            ],
            ASK_AGENCY: [
                CommandHandler('cancel', cancel),
                MessageHandler(filters.ALL, store_agency)
            ],
            ASK_MIN_PRIZE: [
                CommandHandler('cancel', cancel),
                MessageHandler(filters.ALL, store_min_prize),
                CallbackQueryHandler(store_min_prize, pattern='^' + str(SKIP) + '$')
            ],
            ASK_MAX_PRIZE: [
                CommandHandler('cancel', cancel),
                MessageHandler(filters.ALL, store_max_prize),
                CallbackQueryHandler(store_max_prize, pattern='^' + str(SKIP) + '$')
            ],
            ASK_MIN_ROOM: [
                CommandHandler('cancel', cancel),
                MessageHandler(filters.ALL, store_min_room),
                CallbackQueryHandler(store_min_room, pattern='^' + str(SKIP) + '$')
            ],
            ASK_MAX_ROOM: [
                CommandHandler('cancel', cancel),
                MessageHandler(filters.ALL, store_max_room),
                CallbackQueryHandler(store_max_room, pattern='^' + str(SKIP) + '$')
            ],
            ASK_MIN_SURFACE: [
                CommandHandler('cancel', cancel),
                MessageHandler(filters.ALL, store_min_surface),
                CallbackQueryHandler(store_min_surface, pattern='^' + str(SKIP) + '$')
            ],
            ASK_MAX_SURFACE: [
                CommandHandler('cancel', cancel),
                MessageHandler(filters.ALL, store_max_surface),
                CallbackQueryHandler(store_max_surface, pattern='^' + str(SKIP) + '$')
            ],
            ASK_FLOOR: [
                CommandHandler('cancel', cancel),
                MessageHandler(filters.ALL, store_floor),
                CallbackQueryHandler(store_floor, pattern='^' + str(SKIP) + '$')
            ],
            ASK_NAME: [
                CommandHandler('cancel', cancel),
                MessageHandler(filters.ALL, store_name),
                CallbackQueryHandler(store_name, pattern='^' + str(SKIP) + '$')
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        name="addwatch_conversation",
        allow_reentry=True
    )
    app.add_handler(conv_addwatch_handler)
    conv_watchlist_handler = ConversationHandler(
        entry_points=[CommandHandler("watchlist", watchlist)],
        states={
            WATCH_LIST: [
                CallbackQueryHandler(select_watch, pattern='^' + str(SELECT) + ' ')
            ],
            WATCH_INFO: [
                CallbackQueryHandler(suspend_watch, pattern='^' + str(SUSPEND) + '$'),
                CallbackQueryHandler(resume_watch, pattern='^' + str(RESUME) + '$'),
                CallbackQueryHandler(edit_watch, pattern='^' + str(EDIT) + '$'),
                CallbackQueryHandler(remove_watch, pattern='^' + str(REMOVE) + '$'),
                CallbackQueryHandler(watchlist, pattern='^' + str(BACK_TO_LIST) + '$')
            ],
            EDIT_WATCH: [
                CallbackQueryHandler(ask_name, pattern='^' + str(NAME) + '$'),
                CallbackQueryHandler(ask_type, pattern='^' + str(TYPE_FILTER) + '$'),
                CallbackQueryHandler(ask_category, pattern='^' + str(CATEGORY_FILTER) + '$'),
                CallbackQueryHandler(edit_agency_filter, pattern='^' + str(AGENCY_FILTER) + '$'),
                CallbackQueryHandler(edit_auction_filter, pattern='^' + str(AUCTION_FILTER) + '$'),
                CallbackQueryHandler(ask_min_room_filter, pattern='^' + str(MIN_ROOM_FILTER) + '$'),
                CallbackQueryHandler(ask_max_room_filter, pattern='^' + str(MAX_ROOM_FILTER) + '$'),
                CallbackQueryHandler(ask_min_prize_filter, pattern='^' + str(MIN_PRIZE_FILTER) + '$'),
                CallbackQueryHandler(ask_max_prize_filter, pattern='^' + str(MAX_PRIZE_FILTER) + '$'),
                CallbackQueryHandler(ask_min_surface_filter, pattern='^' + str(MIN_SURFACE_FILTER) + '$'),
                CallbackQueryHandler(ask_max_surface_filter, pattern='^' + str(MAX_SURFACE_FILTER) + '$'),
                CallbackQueryHandler(ask_floor_filter, pattern='^' + str(FLOOR_FILTER) + '$'),
                CallbackQueryHandler(watch_info, pattern='^' + str(BACK_TO_WATCH) + '$')
            ],
            EDIT_NAME: [
                MessageHandler(filters.ALL, edit_name)
            ],
            EDIT_TYPE: [
                MessageHandler(filters.ALL, edit_type)
            ],
            EDIT_CATEGORY: [
                MessageHandler(filters.ALL, edit_category)
            ],
            EDIT_MIN_ROOM: [
                MessageHandler(filters.ALL, edit_min_room)
            ],
            EDIT_MAX_ROOM: [
                MessageHandler(filters.ALL, edit_max_room)
            ],
            EDIT_MIN_PRIZE: [
                MessageHandler(filters.ALL, edit_min_prize)
            ],
            EDIT_MAX_PRIZE: [
                MessageHandler(filters.ALL, edit_max_prize)
            ],
            EDIT_MIN_SURFACE: [
                MessageHandler(filters.ALL, edit_min_surface)
            ],
            EDIT_MAX_SURFACE: [
                MessageHandler(filters.ALL, edit_max_surface)
            ],
            EDIT_FLOOR: [
                MessageHandler(filters.ALL, edit_floor)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        name="watchlist_conversation",
        persistent=True,
        allow_reentry=True
    )
    app.add_handler(conv_watchlist_handler)
    conv_watchlist_handler = ConversationHandler(
        entry_points=[CommandHandler("followers", followers)],
        states={
            FOLLOWER_LIST: [
                CallbackQueryHandler(remove_follower, pattern='^' + str(REMOVE) + ' ')
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        name="watchlist_conversation",
        persistent=True,
        allow_reentry=True
    )
    app.add_handler(conv_watchlist_handler)
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('cancel', cancel))
    app.add_handler(CommandHandler("info", report, filters.User(ADMIN_ID)))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CallbackQueryHandler(restart_watch, pattern='^RESTART_WATCH '))
    app.add_handler(CallbackQueryHandler(restart_report, pattern='^RESTART_REPORT'))
    app.add_handler(CommandHandler("addwatch", addwatch))
    app.add_handler(CommandHandler("watchlist", watchlist))
    app.add_handler(CommandHandler("followers", followers))
    app.add_handler(MessageHandler(filters.Entity(MessageEntity.URL), add_watch_by_url))
    app.add_handler(MessageHandler(filters.ALL, default))

    app.run_polling()


def search_daemon():
    logging.info("search deamon started")

    while True:
        if len(storage.load()) == 0:
            time.sleep(10)
            continue
        for user in storage.load():
            per_user_delay = max(10 * 60, int(random.randint(55 * 30, 65 * 30) / len(storage.users)))
            if user.last_update:
                diff = get_time() - user.last_update
                if diff < per_user_delay:
                    partial_per_user_delay = per_user_delay - diff
                    logging.info(f"sleep for {int(partial_per_user_delay / 60)} minutes (partial)")
                    time.sleep(partial_per_user_delay)
            # update user data during sleep
            user: User = next((x for x in storage.load() if x.chat_id == user.chat_id), None)
            if not user:
                continue
            for watch in user.watchlist:
                blocked = watch.remaining_attempts > 0
                logging.info(f"{user.username} {watch.display_name} attempts {watch.remaining_attempts}/{watch.attempts}, blocked {blocked}")
                watch.remaining_attempts = watch.remaining_attempts - 1 if watch.remaining_attempts > 0 else 0
                watch.status = True if watch.remaining_attempts == 0 and watch.attempts > 0 else watch.status
                if watch.is_active and not blocked:
                    if watch.status:
                        ads, status = watch.get_ads()
                        logging.info(f"{user.username} {watch.display_name} {len(ads)}, status: {status}")
                        online_user = True
                        if status:
                            watch.attempts = 0
                            ads_sent = 0
                            for ad in ads:
                                # check all watch in case of multiple watch with same source
                                history = []
                                for w in user.watchlist:
                                    if w.source == watch.source:
                                        history += w.history
                                if ad.url not in history:
                                    if not watch.first_execution:
                                        online_user = send_adv(user, ad, watch)
                                    if not online_user:
                                        break
                                    else:
                                        ads_sent += 1
                                        watch.history.append(ad.url)
                            watch.first_execution = False
                            storage.add_update(watch.display_name, ads_sent)
                        else:
                            if watch.attempts == 0:
                                send_alert(watch)
                                watch.attempts = 1
                            else:
                                watch.attempts *= 2
                            watch.remaining_attempts = watch.attempts
                        if online_user:
                            watch.status = status
                            user.last_update = get_time()
                            storage.save()
                            per_watch_delay = random.randint(7, 13)
                            logging.info(f"sleep for {per_watch_delay} seconds")
                            time.sleep(per_watch_delay)
                        per_watch_delay = random.randint(7, 13)
                        logging.info(f"sleep for {per_watch_delay} seconds")
                        time.sleep(per_watch_delay)
                        if not online_user:
                            break
                    else:
                        logging.warning(f"{watch.display_name} is not working")
            logging.info(f"sleep for {int(per_user_delay / 60)} minutes")
            time.sleep(per_user_delay)
        if 0 <= datetime.now().hour < 8:
            per_loop_delay = random.randint(60 * 60 * 2, 60 * 60 * 3)
            logging.info(f"sleep for {int(per_loop_delay / 3600)} hours")
            time.sleep(per_loop_delay)


def send_adv(user: User, adv: Adv, watch: Watch):
    try:
        text = f'\U0001F3E0 Nuova Inserzione da {adv.display_name}\n{watch.type.value} \\- {watch.description or watch.city}\n{format_amount(adv.prize, markdown=True)}'
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=u'\U0001F517 Apri', url=adv.url)
            ]
        ])
        telegram.Bot(token=BOT_TOKEN).send_message(user.chat_id, text, parse_mode='MarkdownV2',
                                                   disable_web_page_preview=True,
                                                   reply_markup=reply_markup)
        if hasattr(user, 'followers'):
            for follower in user.followers:
                text = f'\U0001F3E0 Nuova Inserzione da {adv.display_name}\n{watch.type.value} \\- {watch.description or watch.city}\n{format_amount(adv.prize, markdown=True)} condivisa da {user.username}'
                telegram.Bot(token=BOT_TOKEN).send_message(follower, text, parse_mode='MarkdownV2',
                                                           disable_web_page_preview=True,
                                                           reply_markup=reply_markup)
        return True
    except Exception as e:
        error_str = str(e)
        logging.error(f"\n\n---------\n\nError with ChatId {user.chat_id}, User {user.username}")
        print(error_str)
        logging.error("\n\n---------\n\n")
        if "blocked" in error_str:
            deleted = storage.delete_user(user.chat_id)
            if deleted:
                logging.info(f"Bot blocked by user {user.username}, DELETED")
            else:
                logging.error(f"Error attempting to delete user {user.username}")
        return False


def send_alert(watch: Watch):
    text = f'⚠️⚠️⚠️\nProblema di servizio per {watch.display_name}. Clicca /info per maggiori dettagli.'
    telegram.Bot(token=BOT_TOKEN).send_message(ADMIN_ID, text)


if __name__ == '__main__':
    executor = ProcessPoolExecutor(2)
    loop = asyncio.get_event_loop()
    boo = loop.run_in_executor(executor, bot_handler)
    baa = loop.run_in_executor(executor, search_daemon)

    loop.run_forever()
