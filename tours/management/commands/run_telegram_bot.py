import telebot
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Avg
from django.contrib.auth.models import User
from tours.models import Tour, Booking, Review


class Command(BaseCommand):
    help = "Run Telegram bot for TravelBook"

    def handle(self, *args, **options):
        token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        admin_id = getattr(settings, "TELEGRAM_ADMIN_CHAT_ID", None)

        if not token:
            self.stdout.write(self.style.ERROR("❌ TELEGRAM_BOT_TOKEN not found in settings"))
            return

        bot = telebot.TeleBot(token, parse_mode="HTML")

        
        @bot.message_handler(commands=["start"])
        def start(message):
            bot.reply_to(
                message,
                (
                    "👋 Hi! im <b>bot aferapokitaysky</b>.\n\n"
                    "Available commands:\n"
                    "/stats — Show site statistics\n"
                    "/users — Recent users\n"
                    "/bookings — Recent bookings\n"
                    "/help — List of commands"
                ),
            )

        @bot.message_handler(commands=["help"])
        def help_cmd(message):
            bot.reply_to(
                message,
                (
                    "🧭 <b>List of commands:</b>\n"
                    "/stats — General site statistics\n"
                    "/users — Latest registered users\n"
                    "/bookings — Последние бронирования\n"
                ),
            )

        @bot.message_handler(commands=["stats"])
        def stats_cmd(message):
            user_count = User.objects.count()
            tour_count = Tour.objects.count()
            booking_count = Booking.objects.count()
            review_count = Review.objects.count()
            avg_rating = Review.objects.aggregate(avg=Avg("rating"))["avg"] or 0
            latest_booking = Booking.objects.order_by("-created_at").first()

            text = (
                "📊 <b>TravelBook — Статистика</b>\n\n"
                f"👤 Пользователи: <b>{user_count}</b>\n"
                f"🏝 Туры: <b>{tour_count}</b>\n"
                f"🧳 Бронирования: <b>{booking_count}</b>\n"
                f"⭐ Отзывы: <b>{review_count}</b>\n"
                f"🌟 Средний рейтинг: <b>{round(avg_rating, 2)}</b>\n"
            )

            if latest_booking:
                text += (
                    f"\n🕒 <b>Последнее бронирование:</b>\n"
                    f"• Пользователь: <code>{latest_booking.user.username}</code>\n"
                    f"• Тур: {latest_booking.tour.title}\n"
                    f"• Дата: {latest_booking.created_at.strftime('%Y-%m-%d %H:%M')}"
                )

            bot.send_message(message.chat.id, text)

        @bot.message_handler(commands=["users"])
        def users_cmd(message):
            users = User.objects.order_by("-date_joined")[:5]
            if not users.exists():
                bot.send_message(message.chat.id, "Пока нет зарегистрированных пользователей.")
                return

            text = "👥 <b>Последние пользователи</b>\n\n"
            for u in users:
                text += f"• {u.username} — {u.date_joined.strftime('%Y-%m-%d')}\n"
            bot.send_message(message.chat.id, text)

        @bot.message_handler(commands=["bookings"])
        def bookings_cmd(message):
            bookings = Booking.objects.select_related("tour", "user").order_by("-created_at")[:5]
            if not bookings.exists():
                bot.send_message(message.chat.id, "❌ Нет недавних бронирований.")
                return

            text = "🧾 <b>Недавние бронирования</b>\n\n"
            for b in bookings:
                text += (
                    f"• {b.user.username} — {b.tour.title}\n"
                    f"  {b.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                )
            bot.send_message(message.chat.id, text)

        self.stdout.write(self.style.SUCCESS("✅ Telegram бот запущен..."))
        bot.infinity_polling()
