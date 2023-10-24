from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext, ConversationHandler

from conversationid import *
from costants import AdvCategory, AdvType, FloorType
from services.storage import storage
from models.user import User
from utils import format_floor, format_surface, format_int, format_amount, format_boolean, format_text
from models.watch import Watch


async def watchlist(update: Update, context: CallbackContext) -> int:
    context.chat_data.clear()
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username,
                                       update.effective_user.first_name, update.effective_user.last_name)
    query = update.callback_query

    if user.watchlist:
        if len(user.watchlist) == 1:
            context.chat_data['current_watch'] = user.watchlist[0]
            return await watch_info(update, context)
        else:
            buttons = []
            for watch in user.watchlist:
                title = f'{watch.display_name} - {watch.type.value} - {watch.description or watch.city}'
                button = [InlineKeyboardButton(text=title, callback_data=str(SELECT) + " " + watch.uuid)]
                buttons.append(button)
            text = 'Quale delle seguenti ricerche vuoi visualizzare?'
            reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)
            if query:
                await query.answer()
                await query.edit_message_text(text, parse_mode='MarkdownV2', reply_markup=reply_markup)
            else:
                await update.message.reply_markdown_v2(text, reply_markup=reply_markup)
            return WATCH_LIST
    elif query:
        await query.answer('Si è verificato un errore.')
        return ConversationHandler.END
    else:
        text = 'Non hai ancora nessuna ricerca preferita.\n' \
               'Inviami il link di una ricerca su un sito di annunci per iniziare oppure ' \
               'usa il comando /addwatch per aggiungerla manualmente.'
        await update.message.reply_text(text)
        return ConversationHandler.END


async def select_watch(update: Update, context: CallbackContext) -> int:
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username,
                                       update.effective_user.first_name, update.effective_user.last_name)
    query = update.callback_query

    if query:
        uuid = query.data.split()[1]
        selected_watch = next((watch for watch in user.watchlist if watch.uuid == uuid), None)
        if selected_watch:
            context.chat_data['current_watch'] = selected_watch
            return await watch_info(update, context)
        else:
            return ConversationHandler.END
    else:
        return ConversationHandler.END


async def watch_info(update: Update, context: CallbackContext) -> int:
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username,
                                       update.effective_user.first_name, update.effective_user.last_name)
    watch: Watch = context.chat_data.get('current_watch', None)
    query = update.callback_query

    if watch:
        filters = get_filters(watch)
        state = '_Attivo_' if watch.is_active else '_Non attivo_'
        error = '\n\n*Servizio momentaneamente non disponibile*' if not watch.status else ''
        title = f'{watch.description} \\- {watch.display_name}' if watch.description else watch.display_name
        text = f'*{title}*\n{filters}{state}{error}'
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=u'\U0001F519 Indietro', callback_data=str(BACK_TO_LIST))
            ] if len(user.watchlist) > 1 else [],
            [
                InlineKeyboardButton(text=u'\uE333 Elimina', callback_data=str(REMOVE)),
                InlineKeyboardButton(text=u'\u23F8 Sospendi', callback_data=str(SUSPEND)) if watch.is_active
                else InlineKeyboardButton(text=u'\uE23A Riprendi', callback_data=str(RESUME))
            ],
            [
                InlineKeyboardButton(text=u'\u2699 Modifica', callback_data=str(EDIT)),
                InlineKeyboardButton(text=u'\U0001F517 Apri', url=watch.url)
            ]
        ])
        if query:
            await query.answer()
            await query.edit_message_text(text, parse_mode='MarkdownV2', disable_web_page_preview=True,
                                          reply_markup=reply_markup)
        else:
            await update.message.reply_markdown_v2(text, disable_web_page_preview=True, reply_markup=reply_markup)
        return WATCH_INFO
    elif query:
        await query.answer('Si è verificato un errore.')
        return ConversationHandler.END
    else:
        await update.message.reply_text('Si è verificato un errore.')
        return ConversationHandler.END


def get_filters(watch: Watch):
    text = ''
    text += f'Città: {watch.city}\n' if watch.city else ''
    text += f'Tipologia: {watch.type.value}\n' if watch.type else ''
    text += f'Categoria: {watch.category.value}\n' if watch.category else ''
    if hasattr(watch, "agency_filter"):
        if watch.agency_filter is not None:
            text += f'Escludi agenzie: {format_boolean(watch.agency_filter)}\n'
    if hasattr(watch, "auction_filter"):
        if watch.auction_filter is not None:
            text += f'Escludi aste giudiziarie: {format_boolean(watch.auction_filter)}\n'
    if hasattr(watch, "min_rooms"):
        if watch.min_rooms is not None:
            text += f'Locali min: {watch.min_rooms}\n'
    if hasattr(watch, "max_rooms"):
        if watch.max_rooms is not None:
            text += f'Locali max: {watch.max_rooms}\n'
    if hasattr(watch, "min_prize"):
        if watch.min_prize is not None:
            text += f'Prezzo min: {format_amount(watch.min_prize, markdown=True)}\n'
    if hasattr(watch, "max_prize"):
        if watch.max_prize is not None:
            text += f'Prezzo max: {format_amount(watch.max_prize, markdown=True)}\n'
    if hasattr(watch, "min_surface"):
        if watch.min_surface is not None:
            text += f'Superficie min: {watch.min_surface}mq\n'
    if hasattr(watch, "max_surface"):
        if watch.max_surface is not None:
            text += f'Superficie max: {watch.max_surface}mq\n'
    if hasattr(watch, "floor"):
        if watch.floor is not None and watch.floor != FloorType.ALL:
            text += f'Piano: {watch.floor.value}\n'
    return text


async def remove_watch(update: Update, context: CallbackContext) -> int:
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username,
                                       update.effective_user.first_name, update.effective_user.last_name)
    watch: Watch = context.chat_data.get('current_watch', None)
    query = update.callback_query

    if watch:
        removed = user.remove_watch(watch.uuid)
        if removed:
            storage.save()
            if query:
                await query.answer('Monitoraggio eliminato')
                text = f'Hai eliminato il monitoraggio di {removed.source}. ' \
                       f'Non riceverai più notifiche per questa ricerca.'
                await query.edit_message_text(text)
            else:
                text = f'Hai eliminato il monitoraggio di {removed.source}. ' \
                       f'Non riceverai più notifiche per questa ricerca.'
                await update.message.reply_text(text)
        else:
            if query:
                await query.answer('Monitoraggio non esistente')
                await query.delete_message()
            else:
                if update.message:
                    await update.message.delete()
        return WATCH_INFO
    elif query:
        await query.answer('Si è verificato un errore.')
        return ConversationHandler.END
    else:
        await update.message.reply_text('Si è verificato un errore.')
        return ConversationHandler.END


async def suspend_watch(update: Update, context: CallbackContext) -> int:
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username,
                                       update.effective_user.first_name, update.effective_user.last_name)
    watch: Watch = context.chat_data.get('current_watch', None)
    query = update.callback_query

    if watch:
        suspended = user.suspend_watch(watch.uuid)
        if suspended:
            storage.save()
            context.chat_data['current_watch'] = suspended
            if query:
                await query.answer('Monitoraggio messo in pausa')
            return await watch_info(update, context)
        else:
            if query:
                await query.answer('Monitoraggio non esistente')
                await query.delete_message()
            else:
                if update.message:
                    await update.message.delete()
            return WATCH_INFO
    elif query:
        await query.answer('Si è verificato un errore.')
        return ConversationHandler.END
    else:
        await update.message.reply_text('Si è verificato un errore.')
        return ConversationHandler.END


async def resume_watch(update: Update, context: CallbackContext) -> int:
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username,
                                       update.effective_user.first_name, update.effective_user.last_name)
    watch: Watch = context.chat_data.get('current_watch', None)
    query = update.callback_query

    if watch:
        resumed = user.resume_watch(watch.uuid)
        if resumed:
            storage.save()
            context.chat_data['current_watch'] = resumed
            if query:
                await query.answer('Monitoraggio ripreso')
            await watch_info(update, context)
        else:
            if query:
                await query.answer('Monitoraggio non esistente')
                await query.delete_message()
            else:
                if update.message:
                    await update.message.delete()
        return WATCH_INFO
    elif query:
        await query.answer('Si è verificato un errore.')
        return ConversationHandler.END
    else:
        await update.message.reply_text('Si è verificato un errore.')
        return ConversationHandler.END


async def edit_watch(update: Update, context: CallbackContext) -> int:
    watch: Watch = context.chat_data.get('current_watch', None)
    query = update.callback_query

    if watch:
        text = 'Clicca per modificare:\n'
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=u'\U0001F519 Indietro', callback_data=str(BACK_TO_WATCH))],
            [InlineKeyboardButton(text=f'Descrizione: {format_text(watch.description)}', callback_data=str(NAME))],
            [InlineKeyboardButton(text=f'Tipo annuncio: {watch.type.value}', callback_data=str(TYPE_FILTER))],
            [InlineKeyboardButton(text=f'Categoria annuncio: {watch.category.value}',
                                  callback_data=str(CATEGORY_FILTER))],
            [InlineKeyboardButton(text=f'Escludi agenzie: {format_boolean(watch.agency_filter)}',
                                  callback_data=str(AGENCY_FILTER))] if hasattr(watch, "agency_filter") else [],
            [InlineKeyboardButton(text=f'Escludi aste giudiziarie: {format_boolean(watch.auction_filter)}',
                                  callback_data=str(AUCTION_FILTER))] if hasattr(watch, "auction_filter") else [],
            [InlineKeyboardButton(text=f'Locali min: {format_int(watch.min_rooms)}',
                                  callback_data=str(MIN_ROOM_FILTER))] if hasattr(watch, "min_rooms") else [],
            [InlineKeyboardButton(text=f'Locali max: {format_int(watch.max_rooms)}',
                                  callback_data=str(MAX_ROOM_FILTER))] if hasattr(watch, "max_rooms") else [],
            [InlineKeyboardButton(text=f'Prezzo min: {format_amount(watch.min_prize)}',
                                  callback_data=str(MIN_PRIZE_FILTER))] if hasattr(watch, "min_prize") else [],
            [InlineKeyboardButton(text=f'Prezzo max: {format_amount(watch.max_prize)}',
                                  callback_data=str(MAX_PRIZE_FILTER))] if hasattr(watch, "max_prize") else [],
            [InlineKeyboardButton(text=f'Superficie min: {format_surface(watch.min_surface)}',
                                  callback_data=str(MIN_SURFACE_FILTER))] if hasattr(watch, "min_surface") else [],
            [InlineKeyboardButton(text=f'Superficie max: {format_surface(watch.max_surface)}',
                                  callback_data=str(FLOOR_FILTER))] if hasattr(watch, "max_surface") else [],
            [InlineKeyboardButton(text=f'Piano: {format_floor(watch.floor)}',
                                  callback_data=str(FLOOR_FILTER))] if hasattr(watch, "floor") else []
        ])
        if query:
            await query.answer()
            await query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)
        return await EDIT_WATCH
    elif query:
        await query.answer('Si è verificato un errore.')
        return ConversationHandler.END
    else:
        await update.message.reply_text('Si è verificato un errore.')
        return ConversationHandler.END


async def ask_name(update: Update, context: CallbackContext) -> int:
    query = update.callback_query

    if query:
        text = 'Che nome vuoi dare alla ricerca?'
        await query.message.delete()
        message = context.bot.send_message(update.effective_user.id, text)
        context.chat_data["last_message"] = message
        return EDIT_NAME
    else:
        return ConversationHandler.END


async def edit_name(update: Update, context: CallbackContext) -> int:
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username,
                                       update.effective_user.first_name, update.effective_user.last_name)
    watch: Watch = context.chat_data.get('current_watch', None)
    last_message = context.chat_data["last_message"]
    query = update.callback_query

    answer = update.message.text
    if answer != "":
        if answer == '/':
            watch.description = None
        else:
            watch.description = answer
        watch.set_url()
        user.set_watch(watch)
        storage.save()
        context.chat_data['current_watch'] = watch
        if update.message:
            await update.message.delete()
        if last_message:
            await context.bot.delete_message(last_message.chat_id, last_message.message_id)
        return await edit_watch(update, context)
    elif query:
        await query.answer('Si è verificato un errore. Riprova.')
        return EDIT_NAME
    else:
        await update.message.reply_text('Si è verificato un errore.')
        return ConversationHandler.END


async def ask_type(update: Update, context: CallbackContext) -> int:
    query = update.callback_query

    if query:
        text = 'Che tipo di annuncio stai cercando?'
        reply_keyboard = [[e.value] for e in AdvType]
        await query.message.delete()
        message = context.bot.send_message(update.effective_user.id, text, reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Tipo di annuncio'
        ))
        context.chat_data["last_message"] = message
        return EDIT_TYPE
    else:
        return ConversationHandler.END


async def edit_type(update: Update, context: CallbackContext) -> int:
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username,
                                       update.effective_user.first_name, update.effective_user.last_name)
    watch: Watch = context.chat_data.get('current_watch', None)
    last_message = context.chat_data["last_message"]
    query = update.callback_query

    answer = update.message.text
    if watch and answer in [e.value for e in AdvType]:
        watch.type = AdvType(answer)
        watch.set_url()
        user.set_watch(watch)
        storage.save()
        context.chat_data['current_watch'] = watch
        if update.message:
            await update.message.delete()
        if last_message:
            await context.bot.delete_message(last_message.chat_id, last_message.message_id)
        return await edit_watch(update, context)
    elif query:
        await query.answer('Si è verificato un errore. Riprova.')
        return EDIT_TYPE
    else:
        await update.message.reply_text('Si è verificato un errore.')
        return ConversationHandler.END


async def ask_category(update: Update, context: CallbackContext) -> int:
    query = update.callback_query

    if query:
        text = 'Che categoria di annuncio stai cercando?'
        reply_keyboard = [[e.value] for e in AdvCategory]
        await query.message.delete()
        message = context.bot.send_message(update.effective_user.id, text, reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Categoria di annuncio'
        ))
        context.chat_data["last_message"] = message
        return EDIT_CATEGORY
    else:
        return ConversationHandler.END


async def edit_category(update: Update, context: CallbackContext) -> int:
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username,
                                       update.effective_user.first_name, update.effective_user.last_name)
    watch: Watch = context.chat_data.get('current_watch', None)
    last_message = context.chat_data["last_message"]
    query = update.callback_query

    answer = update.message.text
    if watch and answer in [e.value for e in AdvCategory]:
        watch.category = AdvCategory(answer)
        watch.set_url()
        user.set_watch(watch)
        storage.save()
        context.chat_data['current_watch'] = watch
        if update.message:
            await update.message.delete()
        if last_message:
            await context.bot.delete_message(last_message.chat_id, last_message.message_id)
        return await edit_watch(update, context)
    elif query:
        await query.answer('Si è verificato un errore. Riprova.')
        return EDIT_CATEGORY
    else:
        await update.message.reply_text('Si è verificato un errore.')
        return ConversationHandler.END


async def edit_agency_filter(update: Update, context: CallbackContext) -> int:
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username,
                                       update.effective_user.first_name, update.effective_user.last_name)
    watch: Watch = context.chat_data.get('current_watch', None)
    watch.agency_filter = not watch.agency_filter
    watch.set_url()
    user.set_watch(watch)
    storage.save()
    context.chat_data['current_watch'] = watch
    return await edit_watch(update, context)


async def edit_auction_filter(update: Update, context: CallbackContext) -> int:
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username,
                                       update.effective_user.first_name, update.effective_user.last_name)
    watch: Watch = context.chat_data.get('current_watch', None)
    watch.auction_filter = not watch.auction_filter
    watch.set_url()
    user.set_watch(watch)
    storage.save()
    context.chat_data['current_watch'] = watch
    return await edit_watch(update, context)


def ask_min_room_filter(update: Update, context: CallbackContext) -> int:
    query = update.callback_query

    if query:
        text = 'Quante stanze minime? (indicare solo il numero, es: 2)'
        query.message.delete()
        message = context.bot.send_message(update.effective_user.id, text)
        context.chat_data["last_message"] = message
        return EDIT_MIN_ROOM
    else:
        return ConversationHandler.END


async def edit_min_room(update: Update, context: CallbackContext) -> int:
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username,
                                       update.effective_user.first_name, update.effective_user.last_name)
    watch: Watch = context.chat_data.get('current_watch', None)
    last_message = context.chat_data["last_message"]
    query = update.callback_query

    answer = update.message.text
    if answer.isdigit() or answer == '/':
        if answer == '/':
            watch.min_rooms = None
        else:
            watch.min_rooms = int(answer)
        watch.set_url()
        user.set_watch(watch)
        storage.save()
        context.chat_data['current_watch'] = watch
        if update.message:
            await update.message.delete()
        if last_message:
            await context.bot.delete_message(last_message.chat_id, last_message.message_id)
        return await edit_watch(update, context)
    elif query:
        await query.answer('Si è verificato un errore. Riprova.')
        return EDIT_MIN_ROOM
    else:
        await update.message.reply_text('Si è verificato un errore.')
        return ConversationHandler.END


def ask_max_room_filter(update: Update, context: CallbackContext) -> int:
    query = update.callback_query

    if query:
        text = 'Quante stanze massime? (indicare solo il numero, es: 5)'
        query.message.delete()
        message = context.bot.send_message(update.effective_user.id, text)
        context.chat_data["last_message"] = message
        return EDIT_MAX_ROOM
    else:
        return ConversationHandler.END


async def edit_max_room(update: Update, context: CallbackContext) -> int:
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username,
                                       update.effective_user.first_name, update.effective_user.last_name)
    watch: Watch = context.chat_data.get('current_watch', None)
    last_message = context.chat_data["last_message"]
    query = update.callback_query

    answer = update.message.text
    if answer.isdigit() or answer == '/':
        if answer == '/':
            watch.max_rooms = None
        else:
            watch.max_rooms = int(answer)
        watch.set_url()
        user.set_watch(watch)
        storage.save()
        context.chat_data['current_watch'] = watch
        if update.message:
            await update.message.delete()
        if last_message:
            await context.bot.delete_message(last_message.chat_id, last_message.message_id)
        return await edit_watch(update, context)
    elif query:
        await query.answer('Si è verificato un errore. Riprova.')
        return EDIT_MAX_ROOM
    else:
        await update.message.reply_text('Si è verificato un errore.')
        return ConversationHandler.END


def ask_min_prize_filter(update: Update, context: CallbackContext) -> int:
    query = update.callback_query

    if query:
        text = 'Quale prezzo minimo? (indicare solo il numero, es: 50000)'
        query.message.delete()
        message = context.bot.send_message(update.effective_user.id, text)
        context.chat_data["last_message"] = message
        return EDIT_MIN_PRIZE
    else:
        return ConversationHandler.END


async def edit_min_prize(update: Update, context: CallbackContext) -> int:
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username,
                                       update.effective_user.first_name, update.effective_user.last_name)
    watch: Watch = context.chat_data.get('current_watch', None)
    last_message = context.chat_data["last_message"]
    query = update.callback_query

    answer = update.message.text
    if answer.isdigit() or answer == '/':
        if answer == '/':
            watch.min_prize = None
        else:
            watch.min_prize = int(answer)
        watch.set_url()
        user.set_watch(watch)
        storage.save()
        context.chat_data['current_watch'] = watch
        if update.message:
            await update.message.delete()
        if last_message:
            await context.bot.delete_message(last_message.chat_id, last_message.message_id)
        return await edit_watch(update, context)
    elif query:
        await query.answer('Si è verificato un errore. Riprova.')
        return EDIT_MIN_PRIZE
    else:
        await update.message.reply_text('Si è verificato un errore.')
        return ConversationHandler.END


def ask_max_prize_filter(update: Update, context: CallbackContext) -> int:
    query = update.callback_query

    if query:
        text = 'Quale prezzo massimo? (indicare solo il numero, es: 100000)'
        query.message.delete()
        message = context.bot.send_message(update.effective_user.id, text)
        context.chat_data["last_message"] = message
        return EDIT_MAX_PRIZE
    else:
        return ConversationHandler.END


async def edit_max_prize(update: Update, context: CallbackContext) -> int:
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username,
                                       update.effective_user.first_name, update.effective_user.last_name)
    watch: Watch = context.chat_data.get('current_watch', None)
    last_message = context.chat_data["last_message"]
    query = update.callback_query

    answer = update.message.text
    if answer.isdigit() or answer == '/':
        if answer == '/':
            watch.max_prize = None
        else:
            watch.max_prize = int(answer)
        watch.set_url()
        user.set_watch(watch)
        storage.save()
        context.chat_data['current_watch'] = watch
        if update.message:
            await update.message.delete()
        if last_message:
            await context.bot.delete_message(last_message.chat_id, last_message.message_id)
        return await edit_watch(update, context)
    elif query:
        await query.answer('Si è verificato un errore. Riprova.')
        return EDIT_MAX_PRIZE
    else:
        await update.message.reply_text('Si è verificato un errore.')
        return ConversationHandler.END


def ask_min_surface_filter(update: Update, context: CallbackContext) -> int:
    query = update.callback_query

    if query:
        text = 'Quanta superficie minima? (indicare solo il numero, es: 50)'
        query.message.delete()
        message = context.bot.send_message(update.effective_user.id, text)
        context.chat_data["last_message"] = message
        return EDIT_MIN_SURFACE
    else:
        return ConversationHandler.END


async def edit_min_surface(update: Update, context: CallbackContext) -> int:
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username,
                                       update.effective_user.first_name, update.effective_user.last_name)
    watch: Watch = context.chat_data.get('current_watch', None)
    last_message = context.chat_data["last_message"]
    query = update.callback_query

    answer = update.message.text
    if answer.isdigit() or answer == '/':
        if answer == '/':
            watch.min_surface = None
        else:
            watch.min_surface = int(answer)
        watch.set_url()
        user.set_watch(watch)
        storage.save()
        context.chat_data['current_watch'] = watch
        if update.message:
            await update.message.delete()
        if last_message:
            await context.bot.delete_message(last_message.chat_id, last_message.message_id)
        return await edit_watch(update, context)
    elif query:
        await query.answer('Si è verificato un errore. Riprova.')
        return EDIT_MIN_SURFACE
    else:
        await update.message.reply_text('Si è verificato un errore.')
        return ConversationHandler.END


def ask_max_surface_filter(update: Update, context: CallbackContext) -> int:
    query = update.callback_query

    if query:
        text = 'Quanta superficie massima? (indicare solo il numero, es: 100)'
        query.message.delete()
        message = context.bot.send_message(update.effective_user.id, text)
        context.chat_data["last_message"] = message
        return EDIT_MAX_SURFACE
    else:
        return ConversationHandler.END


async def edit_max_surface(update: Update, context: CallbackContext) -> int:
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username,
                                       update.effective_user.first_name, update.effective_user.last_name)
    watch: Watch = context.chat_data.get('current_watch', None)
    last_message = context.chat_data["last_message"]
    query = update.callback_query

    answer = update.message.text
    if answer.isdigit() or answer == '/':
        if answer == '/':
            watch.max_surface = None
        else:
            watch.max_surface = int(answer)
        watch.set_url()
        user.set_watch(watch)
        storage.save()
        context.chat_data['current_watch'] = watch
        await update.message.reply_text("", reply_markup=ReplyKeyboardRemove())
        if update.message:
            await update.message.delete()
        if last_message:
            await context.bot.delete_message(last_message.chat_id, last_message.message_id)
        return await edit_watch(update, context)
    elif query:
        await query.answer('Si è verificato un errore. Riprova.')
        return EDIT_MAX_SURFACE
    else:
        await update.message.reply_text('Si è verificato un errore.')
        return ConversationHandler.END


def ask_floor_filter(update: Update, context: CallbackContext) -> int:
    query = update.callback_query

    if query:
        text = 'A che piano?'
        reply_keyboard = [[e.value] for e in FloorType]
        query.message.delete()
        message = context.bot.send_message(update.effective_user.id, text, reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Piano'
        ))
        context.chat_data["last_message"] = message
        return EDIT_FLOOR
    else:
        return ConversationHandler.END


async def edit_floor(update: Update, context: CallbackContext) -> int:
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username,
                                       update.effective_user.first_name, update.effective_user.last_name)
    watch: Watch = context.chat_data.get('current_watch', None)
    last_message = context.chat_data["last_message"]
    query = update.callback_query

    answer = update.message.text
    if watch and answer in [e.value for e in FloorType]:
        watch.floor = FloorType(answer)
        watch.set_url()
        user.set_watch(watch)
        storage.save()
        context.chat_data['current_watch'] = watch
        if update.message:
            await update.message.delete()
        if last_message:
            await context.bot.delete_message(last_message.chat_id, last_message.message_id)
        return await edit_watch(update, context)
    elif query:
        await query.answer('Si è verificato un errore. Riprova.')
        return EDIT_FLOOR
    else:
        await update.message.reply_text('Si è verificato un errore.')
        return ConversationHandler.END


async def followers(update: Update, context: CallbackContext) -> int:
    context.chat_data.clear()
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username,
                                       update.effective_user.first_name, update.effective_user.last_name)
    query = update.callback_query

    if hasattr(user, 'followers') and user.followers:
        users = storage.load()
        buttons = []
        for follower in user.followers:
            username = ''
            for usr in users:
                if str(usr.chat_id) == follower:
                    username = usr.username
            title = f'Rimuovi {username}'
            button = [InlineKeyboardButton(text=title, callback_data=str(REMOVE) + ' ' + str(follower))]
            buttons.append(button)
        text = 'Lista dei tuoi followers'
        reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        if query:
            await query.answer()
            await query.edit_message_text(text, parse_mode='MarkdownV2', reply_markup=reply_markup)
        else:
            await update.message.reply_markdown_v2(text, reply_markup=reply_markup)
        return FOLLOWER_LIST
    elif query:
        await query.answer('Si è verificato un errore.')
        return ConversationHandler.END
    else:
        url = f'https://t.me/loft_finder_bot?start={user.chat_id}'
        text = f'Non hai ancora nessuna follower\\. Invita altri utenti tramite questo [LINK]({url})\\.'
        await update.message.reply_text(text, parse_mode='MarkdownV2')
        return ConversationHandler.END


def remove_follower(update: Update, context: CallbackContext) -> int:
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username,
                                       update.effective_user.first_name, update.effective_user.last_name)
    query = update.callback_query

    if query:
        follower_id = query.data.split()[1]
        user.remove_follower(follower_id)
        storage.save()
        return followers(update, context)
    else:
        return ConversationHandler.END
