from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def subscribe_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Подписаться на канал", url="https://t.me/dfsfdsfs432234")
    builder.button(text="✅ Проверить подписку", callback_data="check_sub")
    builder.adjust(1)
    return builder.as_markup()

def main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🎨 Участвовать", callback_data="participate")
    builder.button(text="🏆 Как выиграть?", callback_data="how_to_win")
    builder.button(text="❓ Помощь", callback_data="help")
    builder.button(text="👤 Профиль", callback_data="profile")
    builder.adjust(1)
    return builder.as_markup()

def admin_panel():
    builder = InlineKeyboardBuilder()
    builder.button(text="📸 Посмотреть фото", callback_data="admin_photos")
    builder.button(text="👥 База людей", callback_data="admin_users_count")
    builder.button(text="🆘 Помощь (обращения)", callback_data="admin_help_requests")
    builder.button(text="⭐ Выдать админа", callback_data="admin_grant")
    builder.button(text="📢 Рассылка", callback_data="admin_broadcast")
    builder.adjust(1)
    return builder.as_markup()

def help_request_keyboard(request_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Ответить", callback_data=f"answer_req_{request_id}")
    return builder.as_markup()

def back_button():
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="back_to_menu")
    return builder.as_markup()
