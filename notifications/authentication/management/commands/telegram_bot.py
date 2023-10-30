from telebot import TeleBot
from telebot import types
import os

from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

from authentication.models import MyUser, UserTelegram

# Объявление переменной бота
bot = TeleBot(os.environ.get('TELEGRAM_TOKEN'), threaded=False)

class Command(BaseCommand):
    help = "`Notifications` telegram bot"

    def add_arguments(self, parser):
        bot.enable_save_next_step_handlers(delay=2)
        bot.load_next_step_handlers()
        bot.infinity_polling()

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        try:
            telegram_account = UserTelegram.objects.get(chat_id=message.chat.id)
            user = MyUser.objects.get(users_telegram=telegram_account)
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton(
                    'Моя подписка', callback_data='/subscribe'
                )
            )
            bot.reply_to(message, f"👋 Привет, {user.username} \n Чем я могу вам помочь?", reply_markup=keyboard)
        except ObjectDoesNotExist:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton(
                    'Привязка бота к аккаунту notifications!', callback_data='/adding_telegram'
                )
            )
            bot.reply_to(message, "👋 Привет! \nЯ notifications bot 🤖\nЧем я могу вам помочь?", reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda c: c.data == '/adding_telegram')
    def process_callback_adding_telegram(callback_query: types.CallbackQuery):
        bot.answer_callback_query(callback_query.id)
        bot.send_message(callback_query.from_user.id, f'Чтобы продолжить регистрацию пройдите по [этой ссылке](http://127.0.0.1/auth/telegram?chat_id={callback_query.from_user.id}&username={callback_query.from_user.username})', parse_mode='MarkdownV2')
    
    @bot.callback_query_handler(func=lambda c: c.data == '/subscribe')
    def process_callback_subscribe_info(callback_query: types.CallbackQuery):
        user_tg = UserTelegram.objects.get(chat_id=callback_query.from_user.id)
        user = MyUser.objects.get(users_telegram=user_tg)
        if user.is_subscribed:
            bot.send_message(user_tg.chat_id, 'Вы крутой! У вас есть подписка')
        else:
            bot.send_message(user_tg.chat_id, 'У вас нет подписки')