from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.utils import timezone


from .models import CustomUser, OTP
from .serializers import (
    RegisterSerializer, LoginSerializer, ForgotPasswordSerializer,
    VerifyOTPSerializer, ResetPasswordSerializer, CustomUserSerializer,
    LogoutSerializer,
)

class RegisterView(APIView):
    """
    Endpoint pour l'enregistrement des utilisateurs
    """
    permission_classes = [AllowAny]
    @extend_schema(request=RegisterSerializer,summary="Enregistrer un nouvel utilisateur",responses={201: CustomUserSerializer})
    def post(self, request):
        """
        Enregistrer un nouvel utilisateur
        """
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email').lower()
            print(f"DEBUG: Tentative d'inscription pour {email}. Users en base: {User.objects.count()}")
            try:
                with transaction.atomic():
                    # Créer l'utilisateur Django
                    # On utilise l'email comme username car Django requiert un username unique
                    user = User.objects.create_user(
                        username=email,
                        email=email,
                        password=serializer.validated_data['password'],
                        first_name=serializer.validated_data.get('first_name', ''),
                        last_name=serializer.validated_data.get('last_name', ''),
                        is_active=False  # Désactivé jusqu'à vérification OTP
                    )
                    
                    # Créer le CustomUser
                    custom_user = CustomUser.objects.create(
                        user=user,
                        email=email,
                        phone_number=serializer.validated_data.get('phone_number', ''),
                        profile_picture=serializer.validated_data.get('profile_picture')
                    )
                    
                    # Générer et envoyer OTP
                    otp = OTP.create_otp(custom_user)
                    self.send_otp_email(custom_user.email, otp.code)
                    
                    return Response({
                        'message': 'Utilisateur créé avec succès. Un code OTP a été envoyé à votre email.',
                        'email': custom_user.email
                    }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                import traceback
                return Response({'error': f"Erreur serveur: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"DEBUG: Erreurs de validation: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(request=ForgotPasswordSerializer,summary="Envoyer un code OTP pour réinitialiser le mot de passe",responses={200: "Un code de réinitialisation a été envoyé à votre email"})
    def send_otp_email(self, email, code):
        """Envoyer le code OTP par email"""
        try:
            send_mail(
                'Votre code de vérification',
                f'Votre code OTP est: {code}\nCe code expire dans 10 minutes.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email: {e}")


@extend_schema(request=LoginSerializer,summary="Connexion avec email et mot de passe",responses={200: "Connexion réussie", 401: "Email ou mot de passe incorrect"})
class LoginView(APIView):
    """
    Endpoint pour la connexion des utilisateurs
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Connexion avec email et mot de passe
        """
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            try:
                custom_user = CustomUser.objects.get(email=serializer.validated_data['email'])
                
                if not custom_user.user:
                    return Response({
                        'error': 'Utilisateur non trouvé'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                user = authenticate(
                    username=custom_user.user.username,
                    password=serializer.validated_data['password']
                )
                
                if not user:
                    return Response({
                        'error': 'Email ou mot de passe incorrect'
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
                # Créer un token DRF (TokenAuthentication)
                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    'message': 'Connexion réussie',
                    'token': token.key,
                    'user': CustomUserSerializer(custom_user, context={'request': request}).data,
                }, status=status.HTTP_200_OK)

                
            except CustomUser.DoesNotExist:
                return Response({
                    'error': 'Email ou mot de passe incorrect'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=ForgotPasswordSerializer,summary="Demander la réinitialisation de mot de passe",responses={200: "Si cet email existe, un code de réinitialisation a été envoyé"})
class ForgotPasswordView(APIView):
    """
    Endpoint pour demander la réinitialisation de mot de passe
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Envoyer un code OTP pour réinitialiser le mot de passe
        """
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            try:
                custom_user = CustomUser.objects.get(email=serializer.validated_data['email'])
                
                # Créer un nouvel OTP
                otp = OTP.create_otp(custom_user)
                # Envoyer par email
                self.send_reset_otp_email(custom_user.email, otp.code)
                
                return Response({
                    'message': 'Un code de réinitialisation a été envoyé à votre email',
                    'email': custom_user.email
                }, status=status.HTTP_200_OK)
                
            except CustomUser.DoesNotExist:
                # Pour la sécurité, ne pas révéler si l'email existe
                return Response({
                    'message': 'Si cet email existe, un code de réinitialisation a été envoyé'
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=VerifyOTPSerializer,summary="Vérifier un code OTP pour activer le compte",responses={200: "Compte vérifié avec succès", 400: "Code OTP incorrect ou expiré"})
class VerifyOTPView(APIView):
    """
    Endpoint pour vérifier un code OTP
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            try:
                custom_user = CustomUser.objects.get(email=serializer.validated_data['email'])
                
                try:
                    otp = OTP.objects.get(user=custom_user)
                    
                    # Vérifier l'expiration
                    if otp.is_expired():
                        return Response({
                            'error': 'Le code OTP a expiré'
                        }, status=status.HTTP_400_BAD_REQUEST)

                    # Vérifier si déjà utilisé
                    if otp.is_used:
                        return Response({
                            'error': 'Ce code a déjà été utilisé'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Vérifier le code
                    print(f"DEBUG VERIFY: Email={custom_user.email} | Reçu='{serializer.validated_data['code']}' | Attendu='{otp.code}'")
                    if otp.code != serializer.validated_data['code']:
                        return Response({
                            'error': 'Code OTP incorrect'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Marquer comme utilisé et activer le compte
                    otp.is_used = True
                    otp.save()
                    
                    custom_user.is_verified = True
                    custom_user.is_active = True
                    custom_user.save()
                    custom_user.user.is_active = True # Activer l'utilisateur Django
                    custom_user.user.save()
                    
                    token, _ = Token.objects.get_or_create(user=custom_user.user)
                    return Response({
                        'message': 'Compte vérifié avec succès',
                        'token': token.key,
                        'user': CustomUserSerializer(custom_user, context={'request': request}).data
                    }, status=status.HTTP_200_OK)


                    
                except OTP.DoesNotExist:
                    return Response({
                        'error': 'Aucun code OTP trouvé'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except CustomUser.DoesNotExist:
                return Response({
                    'error': 'Utilisateur non trouvé'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(request=ResetPasswordSerializer,summary="Réinitialiser le mot de passe avec un code OTP",responses={200: "Mot de passe réinitialisé avec succès", 400: "Code OTP incorrect ou expiré"})
class ResetPasswordView(APIView):
    """
    Endpoint pour réinitialiser le mot de passe
    """
    permission_classes = [AllowAny]
    
    @extend_schema(request=ResetPasswordSerializer,summary="Réinitialiser le mot de passe avec un code OTP",responses={200: "Mot de passe réinitialisé avec succès", 400: "Code OTP incorrect ou expiré"})
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            try:
                custom_user = CustomUser.objects.get(email=serializer.validated_data['email'])
                
                try:
                    otp = OTP.objects.get(user=custom_user)
                    
                    # Vérifier l'expiration
                    if otp.is_expired():
                        return Response({
                            'error': 'Le code OTP a expiré'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Vérifier le code
                    if otp.code != serializer.validated_data['code']:
                        return Response({
                            'error': 'Code OTP incorrect'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Réinitialiser le mot de passe
                    custom_user.user.set_password(serializer.validated_data['new_password'])
                    custom_user.user.save()
                    
                    # Marquer le code comme utilisé
                    otp.is_used = True
                    otp.save()
                    
                    return Response({
                        'message': 'Mot de passe réinitialisé avec succès'
                    }, status=status.HTTP_200_OK)

                    
                except OTP.DoesNotExist:
                    return Response({
                        'error': 'Aucun code OTP trouvé'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except CustomUser.DoesNotExist:
                return Response({
                    'error': 'Utilisateur non trouvé'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(summary="Récupérer les informations de l'utilisateur")
class UserView(APIView):
    """
    Endpoint pour consulter les informations de l'utilisateur
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            custom_user = CustomUser.objects.get(user=request.user)
            serializer = CustomUserSerializer(custom_user, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({
                'error': 'Profil utilisateur non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request):
        try:
            custom_user = CustomUser.objects.get(user=request.user)
            serializer = CustomUserSerializer(custom_user, data=request.data, partial=True, context={'request': request})
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'message': 'Profil mis à jour',
                    'user': serializer.data
                }, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({
                'error': 'Profil utilisateur non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)

@extend_schema(request=LogoutSerializer,summary="Déconnexion de l'utilisateur",responses={200: "Déconnexion réussie"})
class LogoutView(APIView):
    """
    Endpoint pour la déconnexion
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Révoquer le token DRF TokenAuthentication."""
        Token.objects.filter(user=request.user).delete()
        return Response({
            'message': 'Déconnexion réussie'
        }, status=status.HTTP_200_OK)
