from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Tour
from travelbook.utils.telegram_notify import send_telegram_message

@receiver(post_save, sender=Tour)
def notify_new_tour(sender, instance, created, **kwargs):
    if created:  
        msg = (
            f"🌍 <b>New Tour Created</b>\n"
            f"🏝 Title: <b>{instance.title}</b>\n"
            f"💰 Price: ${instance.price}\n"
            f"🕓 Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"📜 Description:\n{instance.description[:300]}..."
        )
        try:
            send_telegram_message(msg)
        except Exception as e:
            print("Telegram send failed:", e)
