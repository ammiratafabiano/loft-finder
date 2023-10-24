from urllib.parse import urlparse

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext, ConversationHandler

from conversationid import *
from costants import UrlWatchType, ADMIN_ID, AdvType, AdvCategory, ShortAnswer, FloorType
from services.storage import storage
from models.user import User
from utils import read_json
from models.watch import Watch


async def add_watch_by_url(update: Update, context: CallbackContext) -> int:
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username, update.effective_user.first_name, update.effective_user.last_name)

    url: str = update.message.text
    source: str = urlparse(url).netloc
    if source:
        old_watch: Watch = user.get_watch(url)
        if not old_watch:
            new_watch: Watch = user.add_watch(source, url=url)
            if new_watch:
                storage.save()
                text = f'Hai inserito un link di {source}. L\'ho inserito tra le tue ricerche preferite. ' \
                       'Riceverai aggiornamenti di nuovi annunci pubblicati visibili con questa ricerca.'
                await update.message.reply_text(text)
            else:
                text = f'Il sito {source} non è ancora disponibile su questo self.bot.'
                await update.message.reply_text(text)
                await context.bot.sendMessage(ADMIN_ID, f'Segnalazione per nuovo sito di annunci: {source}')
        else:
            text = 'Watchlist già presente.'
            await update.message.reply_text(text)
    else:
        text = 'Non è stato possibile trovare il sito di annunci.'
        await update.message.reply_text(text)
    return ConversationHandler.END


async def addwatch(update: Update, context: CallbackContext) -> int:
    context.chat_data.clear()
    stored_source = []

    text = 'Su quali siti di annunci vuoi cercare?'
    buttons = []
    for urlWatchType in UrlWatchType:
        stored_source.append(urlWatchType)
        buttons.append([InlineKeyboardButton(text=f'{urlWatchType.value}: Sì', callback_data=urlWatchType.value)])
    buttons.append([InlineKeyboardButton(text='Conferma', callback_data=str(CONFIRM))])
    reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await update.message.reply_text(text, reply_markup=reply_markup)
    context.chat_data['stored_source'] = stored_source
    context.chat_data['stored_source'] = stored_source
    return ASK_SOURCE


async def store_source(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    stored_source = context.chat_data.get('stored_source', [])

    if query:
        action = query.data
        if action == str(CONFIRM):
            if len(stored_source) == 0:
                await query.answer("Devi scegliere almeno un sito di annunci.")
                return ASK_SOURCE
            await query.answer()
            await query.delete_message()
            text = 'Su quale città vuoi monitore gli annnunci?'
            message = await context.bot.send_message(update.effective_user.id, text)
            context.chat_data["last_message"] = message
            return ASK_CITY
        else:
            for urlWatchType in UrlWatchType:
                if action == urlWatchType.value:
                    if urlWatchType in stored_source:
                        stored_source.remove(urlWatchType)
                    else:
                        stored_source.append(urlWatchType)
            text = 'Su quali siti di annunci vuoi cercare?'
            buttons = []
            for urlWatchType in UrlWatchType:
                active = 'Sì' if urlWatchType in stored_source else 'No'
                buttons.append(
                    [InlineKeyboardButton(text=f'{urlWatchType.value}: {active}', callback_data=urlWatchType.value)])
            buttons.append([InlineKeyboardButton(text='Conferma', callback_data=str(CONFIRM))])
            reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)
            await query.edit_message_text(text, reply_markup=reply_markup)
            context.chat_data['stored_source'] = stored_source
            await query.answer()
            return ASK_SOURCE
    else:
        return ConversationHandler.END


async def store_city(update: Update, context: CallbackContext) -> int:
    cities_list = read_json('resources/comuni.json')
    last_message = context.chat_data["last_message"]
    answer = update.message.text

    found = None
    for city in cities_list:
        if answer.lower() == city['nome'].lower():
            found = city
    if found:
        context.chat_data['stored_city'] = found
        text = 'Che tipo di annuncio stai cercando?'
        reply_keyboard = [[e.value] for e in AdvType]
        if update.message:
            await update.message.delete()
        if last_message:
            await context.bot.delete_message(last_message.chat_id, last_message.message_id)
        message = await context.bot.send_message(update.effective_user.id, text, reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Tipo di annuncio'
        ))
        context.chat_data["last_message"] = message
        return ASK_TYPE
    else:
        text = 'La città non è stata trovata. Riprova.'
        await update.message.reply_text(text)
        return ASK_CITY


async def store_type(update: Update, context: CallbackContext) -> int:
    answer = update.message.text

    if answer in [e.value for e in AdvType]:
        context.chat_data['stored_type'] = AdvType(answer)
        return await ask_category(update, context)
    else:
        text = 'La tipologia non è stata trovata. Riprova.'
        await update.message.reply_text(text)
        return ASK_TYPE


async def ask_category(update: Update, context: CallbackContext) -> int:
    last_message = context.chat_data["last_message"]
    answer = update.message.text
    text = 'Che categoria di annuncio stai cercando?'
    reply_keyboard = [[e.value] for e in AdvCategory]
    if AdvType(answer) == AdvType.VENDITA:
        reply_keyboard = [[AdvCategory.IMMOBILE.value], [AdvCategory.NUOVACOSTRUZIONE.value]]
    elif AdvType(answer) == AdvType.AFFITTO:
        reply_keyboard = [[AdvCategory.IMMOBILE.value], [AdvCategory.STANZA.value]]
    if update.message:
        await update.message.delete()
    if last_message:
        await context.bot.delete_message(last_message.chat_id, last_message.message_id)
    message = await context.bot.send_message(update.effective_user.id, text, reply_markup=ReplyKeyboardMarkup(
        reply_keyboard, one_time_keyboard=True, input_field_placeholder='Categoria di annuncio'
    ))
    context.chat_data["last_message"] = message
    return ASK_CATEGORY


async def store_category(update: Update, context: CallbackContext) -> int:
    answer = update.message.text

    if answer in [e.value for e in AdvCategory]:
        context.chat_data['stored_category'] = AdvCategory(answer)
        return await ask_agency(update, context)
    else:
        text = 'La categoria non è stata trovata. Riprova.'
        await update.message.reply_text(text)
        return ASK_CATEGORY


async def ask_agency(update: Update, context: CallbackContext) -> int:
    last_message = context.chat_data["last_message"]
    text = 'Vuoi escludere le agenzie?'
    reply_keyboard = [[e.value] for e in ShortAnswer]
    if update.message:
        await update.message.delete()
    if last_message:
        await context.bot.delete_message(last_message.chat_id, last_message.message_id)
    message = await context.bot.send_message(update.effective_user.id, text, reply_markup=ReplyKeyboardMarkup(
        reply_keyboard, one_time_keyboard=True, input_field_placeholder='Escludi agenzie'
    ))
    context.chat_data["last_message"] = message
    return ASK_AGENCY


async def store_agency(update: Update, context: CallbackContext) -> int:
    answer = update.message.text

    if answer in [e.value for e in ShortAnswer]:
        context.chat_data['stored_agency'] = True if answer == ShortAnswer.YES.value else False
        return await ask_min_prize(update, context)
    else:
        text = 'Risposta non corretta. Riprova.'
        await update.message.reply_text(text)
        return ASK_AGENCY


async def ask_min_prize(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    last_message = context.chat_data["last_message"]
    text = 'Quale prezzo minimo? (indicare solo il numero, es: 50000)'
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Salta', callback_data=str(SKIP))],
    ])
    if query:
        await query.answer()
        await query.edit_message_text(text, reply_markup=reply_markup)
    else:
        message = await context.bot.send_message(update.effective_user.id, text, reply_markup=reply_markup)
        if update.message:
            await update.message.delete()
        if last_message:
            await context.bot.delete_message(last_message.chat_id, last_message.message_id)
        context.chat_data["last_message"] = message
    return ASK_MIN_PRIZE


async def store_min_prize(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    answer = update.message.text if not query else None

    if query or (answer and answer.isdigit()):
        context.chat_data['stored_min_prize'] = int(answer) if answer else None
        return await ask_max_prize(update, context)
    else:
        text = 'Risposta non corretta. Riprova.'
        await update.message.reply_text(text)
        return ASK_MIN_PRIZE


async def ask_max_prize(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    last_message = context.chat_data["last_message"]
    text = 'Quale prezzo massimo? (indicare solo il numero, es: 100000)'
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Salta', callback_data=str(SKIP))],
    ])
    if query:
        await query.answer()
        await query.edit_message_text(text, reply_markup=reply_markup)
    else:
        message = await context.bot.send_message(update.effective_user.id, text, reply_markup=reply_markup)
        if update.message:
            await update.message.delete()
        if last_message:
            await context.bot.delete_message(last_message.chat_id, last_message.message_id)
        context.chat_data["last_message"] = message
    return ASK_MAX_PRIZE


async def store_max_prize(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    answer = update.message.text if not query else None

    if query or (answer and answer.isdigit()):
        context.chat_data['stored_max_prize'] = int(answer) if answer else None
        return await ask_floor(update, context) if context.chat_data['stored_category'] == AdvCategory.STANZA \
            else await ask_min_room(update, context)
    else:
        text = 'Risposta non corretta. Riprova.'
        await update.message.reply_text(text)
        return ASK_MAX_PRIZE


async def ask_min_room(update: Update, context: CallbackContext) -> int:
    last_message = context.chat_data["last_message"]
    text = 'Quante stanze minime? (indicare solo il numero, es: 2)'
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Salta', callback_data=str(SKIP))],
    ])
    if update.message:
        await update.message.delete()
    if last_message:
        await context.bot.delete_message(last_message.chat_id, last_message.message_id)
    message = await context.bot.send_message(update.effective_user.id, text, reply_markup=reply_markup)
    context.chat_data["last_message"] = message
    return ASK_MIN_ROOM


async def store_min_room(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    answer = update.message.text if not query else None

    if query or (answer and answer.isdigit()):
        context.chat_data['stored_min_room'] = int(answer) if answer else None
        return await ask_max_room(update, context)
    else:
        text = 'Risposta non corretta. Riprova.'
        await update.message.reply_text(text)
        return ASK_MIN_ROOM


async def ask_max_room(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    last_message = context.chat_data["last_message"]
    text = 'Quante stanze massime? (indicare solo il numero, es: 5)'
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Salta', callback_data=str(SKIP))],
    ])
    if query:
        await query.answer()
        await query.edit_message_text(text, reply_markup=reply_markup)
    else:
        if update.message:
            await update.message.delete()
        if last_message:
            await context.bot.delete_message(last_message.chat_id, last_message.message_id)
        message = await context.bot.send_message(update.effective_user.id, text, reply_markup=reply_markup)
        context.chat_data["last_message"] = message
    return ASK_MAX_ROOM


async def store_max_room(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    answer = update.message.text if not query else None

    if query or (answer and answer.isdigit()):
        context.chat_data['stored_max_room'] = int(answer) if answer else None
        return await ask_min_surface(update, context)
    else:
        text = 'Risposta non corretta. Riprova.'
        await update.message.reply_text(text)
        return ASK_MAX_ROOM


async def ask_min_surface(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    last_message = context.chat_data["last_message"]
    text = 'Quanta superficie minima? (indicare solo il numero, es: 50)'
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Salta', callback_data=str(SKIP))],
    ])
    if query:
        await query.answer()
        await query.edit_message_text(text, reply_markup=reply_markup)
    else:
        message = await context.bot.send_message(update.effective_user.id, text, reply_markup=reply_markup)
        if update.message:
            await update.message.delete()
        if last_message:
            await context.bot.delete_message(last_message.chat_id, last_message.message_id)
        context.chat_data["last_message"] = message
    return ASK_MIN_SURFACE


async def store_min_surface(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    answer = update.message.text if not query else None

    if query or (answer and answer.isdigit()):
        context.chat_data['stored_min_surface'] = int(answer) if answer else None
        return await ask_max_surface(update, context)
    else:
        text = 'Risposta non corretta. Riprova.'
        await update.message.reply_text(text)
        return ASK_MIN_SURFACE


async def ask_max_surface(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    last_message = context.chat_data["last_message"]
    text = 'Quanta superficie massima? (indicare solo il numero, es: 100)'
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Salta', callback_data=str(SKIP))],
    ])
    if query:
        await query.answer()
        await query.edit_message_text(text, reply_markup=reply_markup)
    else:
        message = await context.bot.send_message(update.effective_user.id, text, reply_markup=reply_markup)
        if update.message:
            await update.message.delete()
        if last_message:
            await context.bot.delete_message(last_message.chat_id, last_message.message_id)
        context.chat_data["last_message"] = message
    return ASK_MAX_SURFACE


async def store_max_surface(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    answer = update.message.text if not query else None

    if query or (answer and answer.isdigit()):
        context.chat_data['stored_max_surface'] = int(answer) if answer else None
        return await ask_floor(update, context)
    else:
        text = 'Risposta non corretta. Riprova.'
        await update.message.reply_text(text)
        return ASK_MAX_SURFACE


async def ask_floor(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    last_message = context.chat_data["last_message"]
    text = 'A che piano?'
    reply_keyboard = [[e.value] for e in FloorType]
    reply_markup = ReplyKeyboardMarkup(
        reply_keyboard, one_time_keyboard=True, input_field_placeholder='Piano'
    )
    if query:
        await query.answer()
    else:
        if update.message:
            await update.message.delete()
    message = await context.bot.send_message(update.effective_user.id, text, reply_markup=reply_markup)
    if last_message:
        await context.bot.delete_message(last_message.chat_id, last_message.message_id)
    context.chat_data["last_message"] = message
    return ASK_FLOOR


async def store_floor(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    answer = update.message.text if not query else None

    if query or (answer and answer in [e.value for e in FloorType]):
        context.chat_data['stored_floor'] = FloorType(answer) if answer else None
        return await ask_name(update, context)
    else:
        text = 'Risposta non corretta. Riprova.'
        await update.message.reply_text(text)
        return ASK_FLOOR


async def ask_name(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    last_message = context.chat_data["last_message"]
    text = 'Vuoi dare un nome breve alla ricerca?'
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Salta', callback_data=str(SKIP))],
    ])
    if query:
        await query.answer()
        await query.edit_message_text(text, reply_markup=reply_markup)
    else:
        message = await context.bot.send_message(update.effective_user.id, text, reply_markup=reply_markup)
        if update.message:
            await update.message.delete()
        if last_message:
            await context.bot.delete_message(last_message.chat_id, last_message.message_id)
        context.chat_data["last_message"] = message
    return ASK_NAME


async def store_name(update: Update, context: CallbackContext) -> int:
    user: User = storage.retrieve_user(update.effective_user.id, update.effective_user.username, update.effective_user.first_name, update.effective_user.last_name)
    query = update.callback_query

    sources = context.chat_data.get('stored_source')
    city = context.chat_data.get('stored_city')
    adv_type = context.chat_data.get('stored_type')
    adv_category = context.chat_data.get('stored_category')
    agency_filter = context.chat_data.get('stored_agency')
    min_room = context.chat_data.get('stored_min_room')
    max_room = context.chat_data.get('stored_max_room')
    min_prize = context.chat_data.get('stored_min_prize')
    max_prize = context.chat_data.get('stored_max_prize')
    min_surface = context.chat_data.get('stored_min_surface')
    max_surface = context.chat_data.get('stored_max_surface')
    floor = context.chat_data.get('stored_floor')
    description = update.message.text if update.message else None

    watch_list = []
    for source in sources:
        watch = user.add_watch(source.value, city=city, adv_type=adv_type, adv_category=adv_category,
                               agency_filter=agency_filter,
                               min_room=min_room, max_room=max_room, min_prize=min_prize, max_prize=max_prize,
                               min_surface=min_surface,
                               max_surface=max_surface, floor=floor, description=description)
        if watch:
            storage.save()
            watch_list.append(watch.display_name)

    if len(watch_list) == len(sources):
        separator = "\n"
        text = f'Ricerca "{description or city["nome"]}" aggiunta correttamente su:\n{separator.join(watch_list)}\n' \
               'Riceverai aggiornamenti di nuovi annunci pubblicati visibili con questa ricerca. ' \
               'Usa il comando /watchlist per visualizzare o modificare le tue ricerche.'
        if query:
            await query.delete_message()
        await context.bot.send_message(update.effective_user.id, text, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END
