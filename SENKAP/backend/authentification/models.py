from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import secrets

class CustomUser(models.Model):
    """Modèle utilisateur personnalisé"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email


class OTP(models.Model):
    """Modèle pour les codes OTP"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='otp')
    code = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"OTP for {self.user.email}"
    
    def is_expired(self):
        """Vérifie si le code OTP a expiré"""
        return timezone.now() > self.expires_at
    
    @staticmethod
    def generate_otp():
        """Génère un code OTP aléatoire de 6 chiffres"""
        return ''.join(secrets.choice('0123456789') for _ in range(6))
    
    @classmethod
    def create_otp(cls, user):
        """Crée un nouvel OTP pour un utilisateur"""
        # Supprimer l'ancien OTP s'il existe
        cls.objects.filter(user=user).delete()
        
        code = cls.generate_otp()
        expires_at = timezone.now() + timedelta(minutes=10)
        
        return cls.objects.create(
            user=user,
            code=code,
            expires_at=expires_at
        )
