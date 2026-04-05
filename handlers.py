import asyncio
import config
import aiosqlite
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import database as db
import keyboards as kb
from utils import check_subscription
from database import DB_PATH

router = Router()
bot = None

# Состояния
class BroadcastState(StatesGroup):
    waiting_for_text = State()

class GrantAdminState(StatesGroup):
    waiting_for_username = State()

class HelpAnswerState(StatesGroup):
    waiting_for_answer = State()

class PhotoState(StatesGroup):
    waiting_for_photo = State()

# Хранение последних сообщений для удаления
user_last_msg = {}

async def delete_previous_message(user_id: int, chat_id: int):
    if user_id in user_last_msg:
        try:
            await bot.delete_message(chat_id, user_last_msg[user_id])
        except:
            pass

async def send_message_and_track(user_id: int, chat_id: int, text: str, reply_markup=None, parse_mode="Markdown"):
    await delete_previous_message(user_id, chat_id)
    msg = await bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
    user_last_msg[user_id] = msg.message_id
    return msg

# Старт
@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    await db.add_user(user_id, username, first_name)
    if await check_subscription(bot, user_id):
        await send_message_and_track(user_id, message.chat.id, "*✨ Меню ✨*", reply_markup=kb.main_menu())
    else:
        await send_message_and_track(user_id, message.chat.id, "🔒 Чтобы продолжить, подпишитесь на канал:", reply_markup=kb.subscribe_keyboard())

# Проверка подписки
@router.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    if await check_subscription(bot, user_id):
        await callback.message.edit_text("✅ Подписка подтверждена!\nНажмите /start, чтобы продолжить.")
        await callback.answer()
    else:
        await callback.answer("❌ Вы не подписались на канал!", show_alert=True)

# Участвовать
@router.callback_query(F.data == "participate")
async def participate(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await state.set_state(PhotoState.waiting_for_photo)
    await callback.message.edit_text("📸 Чтобы участвовать в батле, отправьте свою фотографию:", reply_markup=kb.back_button())
    user_last_msg[user_id] = callback.message.message_id
    await callback.answer()

# Приём фото
@router.message(PhotoState.waiting_for_photo, F.photo)
async def receive_photo(message: Message, state: FSMContext):
    user_id = message.from_user.id
    file_id = message.photo[-1].file_id
    await db.add_photo(user_id, file_id)
    await state.clear()
    await message.answer("✅ Фото сохранено! Спасибо.")
    await message.answer("✨ Меню ✨", reply_markup=kb.main_menu())
    await delete_previous_message(user_id, message.chat.id)

# Как выиграть
@router.callback_query(F.data == "how_to_win")
async def how_to_win(callback: CallbackQuery):
    text = """
🏆 КАК ПОБЕДИТЬ В БАТЛЕ

1️⃣ Продвигайте свой юзернейм
• Отправляйте ссылку с вашим постом друзьям 👥
• Делитесь участием в пиар-группах 📢
• Публикуйте информацию в своих Telegram-каналах 📱

2️⃣ Следите за активностью
• Чем больше реакций и голосов вы получаете,
  тем выше шанс пройти в следующие раунды 💥

3️⃣ Награждение
• Призы получают победители финального этапа 🎁

💡 Совет: активное продвижение юзернейма — ключ к победе.

🍀 Удачи в батле!
"""
    await callback.message.answer(text, reply_markup=kb.back_button())
    await callback.answer()

# Помощь
@router.callback_query(F.data == "help")
async def help_request(callback: CallbackQuery, state: FSMContext):
    await state.set_state(HelpAnswerState.waiting_for_answer)
    await callback.message.answer("✍️ Опишите вашу проблему:", reply_markup=kb.back_button())
    await callback.answer()

@router.message(HelpAnswerState.waiting_for_answer)
async def receive_help_text(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await db.add_help_request(user_id, text)
    await state.clear()
    await message.answer("✅ Ваше обращение отправлено администратору. Ожидайте ответа.")
    await message.answer("*✨ Меню ✨*", reply_markup=kb.main_menu())
    await delete_previous_message(user_id, message.chat.id)

# Профиль
@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    profile = await db.get_user_profile(user_id)
    if profile:
        text = f"""
*👤 Профиль*

👤 *Имя:* {profile['first_name']}
🆔 *ID:* {profile['user_id']}
📛 *User:* @{profile['username'] if profile['username'] else 'нет'}

*📈 Статистика*

⏰ *Дата регистрации:* {profile['date_registration'][:10]}
💬 *Кол-во обращений:* {profile['help_count']}
"""
        await callback.message.answer(text, reply_markup=kb.back_button())
    else:
        await callback.answer("Профиль не найден", show_alert=True)
    await callback.answer()

# Админ панель
@router.message(Command("admin"))
async def admin_command(message: Message):
    user_id = message.from_user.id
    if user_id in config.ADMIN_IDS or await db.is_admin(user_id):
        await send_message_and_track(user_id, message.chat.id, "*🔐 Админ панель*", reply_markup=kb.admin_panel())
    else:
        await message.answer("⛔ У вас нет доступа к админ панели.")

# Обработчики админки
@router.callback_query(F.data == "admin_photos")
async def admin_photos(callback: CallbackQuery):
    photos = await db.get_all_photos()
    if not photos:
        await callback.answer("Нет фотографий", show_alert=True)
        return
    for photo in photos:
        user_id_photo, file_id, timestamp, username = photo
        caption = f"📸 *Фото от* @{username if username else 'нет'}\n🕒 {timestamp[:10]}"
        await bot.send_photo(callback.message.chat.id, file_id, caption=caption, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_users_count")
async def admin_users_count(callback: CallbackQuery):
    users = await db.get_all_users()
    count = len(users)
    await callback.message.edit_text(f"👥 *Всего пользователей:* {count}", reply_markup=kb.admin_panel())
    user_last_msg[callback.from_user.id] = callback.message.message_id

@router.callback_query(F.data == "admin_help_requests")
async def admin_help_requests(callback: CallbackQuery):
    requests = await db.get_unanswered_help_requests()
    if not requests:
        await callback.answer("Нет обращений", show_alert=True)
        return
    for req in requests:
        req_id, user_id, text, timestamp, username = req
        text_preview = text[:50] + "..." if len(text) > 50 else text
        caption = f"🆘 *Обращение #{req_id}*\n👤 @{username}\n📝 {text_preview}\n🕒 {timestamp[:10]}"
        await callback.message.answer(caption, reply_markup=kb.help_request_keyboard(req_id))
    await callback.answer()

@router.callback_query(F.data.startswith("answer_req_"))
async def answer_help_request(callback: CallbackQuery, state: FSMContext):
    req_id = int(callback.data.split("_")[2])
    await state.update_data(req_id=req_id)
    await state.set_state(HelpAnswerState.waiting_for_answer)
    await callback.message.edit_text("*✍️ Введите ответ на обращение:*")
    user_last_msg[callback.from_user.id] = callback.message.message_id

@router.message(HelpAnswerState.waiting_for_answer)
async def process_help_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    req_id = data.get("req_id")
    if req_id:
        answer_text = message.text
        await db.answer_help_request(req_id, answer_text)
        # Получаем user_id обращения
        async with aiosqlite.connect(DB_PATH) as conn:
            cursor = await conn.execute("SELECT user_id FROM help_requests WHERE id = ?", (req_id,))
            row = await cursor.fetchone()
            user_id = row[0]
        await bot.send_message(user_id, f"📩 *Ответ администратора:*\n{answer_text}")
        await message.answer("✅ *Ответ отправлен пользователю.*")
    await state.clear()
    await delete_previous_message(message.from_user.id, message.chat.id)

@router.callback_query(F.data == "admin_grant")
async def admin_grant(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GrantAdminState.waiting_for_username)
    await callback.message.edit_text("*👤 Введите username пользователя (без @):*")
    user_last_msg[callback.from_user.id] = callback.message.message_id

@router.message(GrantAdminState.waiting_for_username)
async def grant_admin_username(message: Message, state: FSMContext):
    username = message.text.strip().lstrip('@')
    user_id = await db.get_user_by_username(username)
    if user_id:
        await db.set_admin(user_id)
        await message.answer(f"✅ *Пользователь @{username} теперь администратор.*")
    else:
        await message.answer(f"❌ *Пользователь @{username} не найден в базе.*")
    await state.clear()
    await delete_previous_message(message.from_user.id, message.chat.id)

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastState.waiting_for_text)
    await callback.message.edit_text("*📢 Введите текст для рассылки:*")
    user_last_msg[callback.from_user.id] = callback.message.message_id

@router.message(BroadcastState.waiting_for_text)
async def send_broadcast(message: Message, state: FSMContext):
    text = message.text
    users = await db.get_all_users()
    sent = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, text)
            sent += 1
            await asyncio.sleep(0.05)
        except:
            pass
    await message.answer(f"✅ *Рассылка завершена.* Отправлено {sent} сообщений.")
    await state.clear()
    await delete_previous_message(message.from_user.id, message.chat.id)

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.delete()
    await send_message_and_track(user_id, callback.message.chat.id, "*✨ Меню ✨*", reply_markup=kb.main_menu())
    await callback.answer()
