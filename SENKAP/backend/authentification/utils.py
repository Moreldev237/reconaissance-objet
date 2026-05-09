from django.core.mail import send_mail
from django.conf import settings

def send_otp_email(email, code, subject_prefix="Votre code de vérification"):
    """Envoyer le code OTP par email"""
    try:
        send_mail(
            f'{subject_prefix}',
            f'Votre code OTP est: {code}\nCe code expire dans 10 minutes.',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
    except Exception as e:
        # En production, il est recommandé d'utiliser un système de logging robuste
        print(f"Erreur lors de l'envoi de l'email à {email}: {e}")