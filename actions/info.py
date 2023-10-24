from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackContext

from costants import WatchType, ADMIN_ID
from models.report import Report
from models.user import User
from services.storage import storage


async def start(update: Update, context: CallbackContext) -> int:
    current_user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username, update.effective_user.first_name, update.effective_user.last_name)
    if context.args and context.args[0] and context.args[0] != current_user.chat_id:
        for user in storage.load():
            if str(user.chat_id) == context.args[0]:
                user.add_follower(str(current_user.chat_id))
                storage.save()
                text = f'Ciao! Sei ora follower di {user.username} e riceverai anche i suoi annunci.'
                await update.message.reply_text(text)
                return ConversationHandler.END
    text = 'Ciao! Ti aiuterò con il monitoraggio di annunci di case. ' \
           'Prova a utilizzare i comandi della lista o invia direttamente qui il link di ' \
           'una ricerca su un sito di annunci per iniziare. Per info ' \
           'consulta la sezione /info.'
    await update.message.reply_text(text)
    return ConversationHandler.END


async def cancel(update: Update, context: CallbackContext) -> int:
    context.chat_data.clear()
    text = 'Operazioni in corso annullate.'
    await update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def default(update: Update, context: CallbackContext) -> int:
    text = 'Comando non riconosciuto o url non inviato correttamente. ' \
           'Prova a utilizzare i comandi della lista o ad inviare l\'url di una ricerca su un sito di annunci.'
    await update.message.reply_text(text)
    return ConversationHandler.END


async def report(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    users = storage.load()
    report_data: Report = storage.load_report()

    n_users = len(users)
    if n_users > 0:
        counter = [0] * len(WatchType)
        attempts = [0] * len(WatchType)
        status = [True] * len(WatchType)
        total = 0
        per_user_refresh_rate = max(10, int(60 / n_users))
        for user in users:
            for watch in user.watchlist:
                for i, watch_name in enumerate(WatchType):
                    if watch_name.value == watch.display_name:
                        attempts[i] = max(attempts[i], watch.attempts)
                        if watch.status:
                            counter[i] += 1
                            total += 1
                        else:
                            status[i] = False
        text = f'*Report dal {report_data.starting_time}*\n\n' \
               f'Utenti: {n_users}\n'
        resolve_buttons = [
            [
                InlineKeyboardButton(text=f'Azzera statistiche',
                                     callback_data="RESTART_REPORT")
            ]
        ]
        for i, watch_name in enumerate(WatchType):
            text += f'\n*{watch_name.value}*\n'
            text += 'Stato: `OK`\n' if status[i] else 'Stato: *KO*\n'
            text += f'Chiamate: {int(counter[i] * (60 / per_user_refresh_rate))} ogni ora\n'
            text += f'Massimi tentativi: {int(attempts[i])}\n'
            text += f'Notifiche: {report_data.ads_sent[i]}\n' if report_data.ads_sent[i] else 'Notifiche: /\n'
            text += f'Aggiornamento: {report_data.last_update[i]}\n' if report_data.last_update[i] else 'Aggiornamento: /\n'
            if not status[i]:
                resolve_buttons.append(
                    [
                        InlineKeyboardButton(text=f'Riavvia {watch_name.value}',
                                             callback_data="RESTART_WATCH " + str(i))
                    ]
                )
        reply_markup = InlineKeyboardMarkup(inline_keyboard=resolve_buttons)
        if query:
            await query.answer()
            await query.edit_message_text(text, parse_mode='MarkdownV2', disable_web_page_preview=True,
                                    reply_markup=reply_markup)
        else:
            await update.message.reply_markdown_v2(text, disable_web_page_preview=True, reply_markup=reply_markup)
        return ConversationHandler.END
    else:
        await update.message.reply_text('Non ci sono ancora informazioni da visualizzare.')
        return ConversationHandler.END


async def info(update: Update, context: CallbackContext) -> int:
    text = 'Questo bot è stato creato con l\'intento di aiutare chi come me è alla ricerca ' \
           'di una casa\\. Spero che possa semplificare la vostra ricerca\\. Sarò lieto di ricevere ' \
           f'vostri feedback o richieste di assistenza\\. Buona fortuna\\!\n\n[Contattami](tg://user?id={ADMIN_ID})'
    await update.message.reply_markdown_v2(text)
    return ConversationHandler.END


async def restart_watch(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    if query:
        index = int(query.data.split()[1])
        for user in storage.load():
            for watch in user.watchlist:
                for i, watch_name in enumerate(WatchType):
                    if watch_name.value == watch.display_name and i == index:
                        watch.status = True
        storage.save()
        return await report(update, context)
    else:
        await update.message.reply_text('Si è verificato un errore.')
        return ConversationHandler.END


async def restart_report(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    if query:
        storage.restart_report()
        return await report(update, context)
    else:
        await update.message.reply_text('Si è verificato un errore.')
        return ConversationHandler.END
