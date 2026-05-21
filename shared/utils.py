from django.conf import settings
from django.core.mail import send_mail


def send_to_email(email, message):
    send_mail(
        'Your verification code',
        message,
        settings.EMAIL_HOST_USER,
        recipient_list = [email],
        fail_silently=False,
    )
