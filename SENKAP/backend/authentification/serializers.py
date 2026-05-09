from rest_framework import serializers
from django.contrib.auth.models import User
from .models import CustomUser, OTP
import re
from django.core.validators import FileExtensionValidator


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class CustomUserSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['id', 'user', 'email', 'phone_number', 'profile_picture', 'is_active', 'is_verified', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_verified']

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    password_confirm = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(max_length=50, required=False)
    last_name = serializers.CharField(max_length=50, required=False)
    phone_number = serializers.CharField(max_length=20, required=False)
    profile_picture = serializers.ImageField(
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'gif', 'jfif', 'pjpeg', 'bmp', 'tiff'])]
    )

    def validate(self, data):
        errors = {}
        # ✅ Normalisation de l'email dans le dictionnaire data
        if data.get('email'):
            data['email'] = data.get('email').lower()
        
        email = data.get('email')

        # ✅ Password match
        if data['password'] != data['password_confirm']:
            errors['password_confirm'] = "Les mots de passe ne correspondent pas"

        # ✅ Password rules
        password = data['password']
        if not re.search(r'[A-Z]', password):
            errors['password'] = "Au moins une majuscule requise"
        if not re.search(r'[0-9]', password):
            errors['password'] = "Au moins un chiffre requis"

        # ✅ Email existe (Vérification plus précise)
        if User.objects.filter(username__iexact=email).exists():
            errors['email'] = "Cet email est déjà utilisé comme identifiant (User)"
        elif CustomUser.objects.filter(email__iexact=email).exists():
            errors['email'] = "Cet email est déjà lié à un profil (CustomUser)"

        # 🔥 S'il y a des erreurs → on les renvoie par champ
        if errors:
            raise serializers.ValidationError(errors)

        return data
class LoginSerializer(serializers.Serializer):
    """Serializer pour la connexion"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        return value.lower()


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer pour la réinitialisation de mot de passe"""
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower()


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer pour la vérification OTP"""
    email = serializers.EmailField()
    code = serializers.CharField(max_length=10, min_length=1)

    def validate_email(self, value):
        return value.lower()

    def validate_code(self, value):
        # Supprime les espaces accidentels (trim)
        cleaned_code = value.strip()
        if len(cleaned_code) != 6:
            raise serializers.ValidationError("Le code doit contenir exactement 6 chiffres.")
        return cleaned_code


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer pour réinitialiser le mot de passe"""
    email = serializers.EmailField()
    code = serializers.CharField(max_length=10, min_length=1)
    new_password = serializers.CharField(min_length=8, write_only=True)
    new_password_confirm = serializers.CharField(min_length=8, write_only=True)
    
    def validate_email(self, value):
        return value.lower()

    def validate_code(self, value):
        cleaned_code = value.strip()
        if len(cleaned_code) != 6:
            raise serializers.ValidationError("Le code doit contenir 6 chiffres.")
        return cleaned_code

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas")
        return data


class LogoutSerializer(serializers.Serializer):
    """Serializer pour la déconnexion"""
    pass
