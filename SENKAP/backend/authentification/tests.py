from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import CustomUser, OTP


class AuthentificationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _create_user(
        self,
        *,
        email="user@example.com",
        password="Password1",
        phone="123",
        is_active=True,
        is_verified=True,
    ):
        django_user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name="First",
            last_name="Last",
        )
        CustomUser.objects.create(
            user=django_user,
            email=email,
            phone_number=phone,
        )
        return CustomUser.objects.get(user=django_user)

    def test_register_success_returns_201(self):
        payload = {
            "email": "new@example.com",
            "password": "Password1",
            "password_confirm": "Password1",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "555",
        }
        res = self.client.post("/api/register", payload, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["email"], payload["email"])

    def test_register_password_mismatch_returns_400(self):
        payload = {
            "email": "new2@example.com",
            "password": "Password1",
            "password_confirm": "Password2",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "555",
        }
        res = self.client.post("/api/register", payload, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("password_confirm", res.data)

    def test_login_fails_if_not_verified(self):
        # Un utilisateur créé via register a is_active=False
        custom_user = self._create_user(is_active=False, is_verified=False)
        custom_user.user.is_active = False
        custom_user.user.save()

        res = self.client.post("/api/login", {"email": custom_user.email, "password": "Password1"}, format="json")
        self.assertEqual(res.status_code, 401)

    def test_login_success_returns_token(self):
        custom_user = self._create_user()
        res = self.client.post(
            "/api/login",
            {"email": custom_user.email, "password": "Password1"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("token", res.data)

    def test_login_wrong_password_returns_401(self):
        custom_user = self._create_user()
        res = self.client.post(
            "/api/login",
            {"email": custom_user.email, "password": "WrongPass1"},
            format="json",
        )
        self.assertEqual(res.status_code, 401)

    def test_verify_otp_marks_user_verified_and_returns_token(self):
        custom_user = self._create_user(is_active=False, is_verified=False)

        otp = OTP.objects.create(
            user=custom_user,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
            is_used=False,
        )

        res = self.client.post(
            "/api/verify-otp",
            {"email": custom_user.email, "code": "123456"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        custom_user.refresh_from_db()
        otp.refresh_from_db()
        self.assertTrue(custom_user.is_verified)
        self.assertTrue(custom_user.is_active)
        self.assertTrue(otp.is_used)
        self.assertIn("token", res.data)

    def test_verify_otp_expired_returns_400(self):
        custom_user = self._create_user()
        otp = OTP.objects.create(
            user=custom_user,
            code="111111",
            expires_at=timezone.now() - timedelta(minutes=1),
            is_used=False,
        )

        res = self.client.post(
            "/api/verify-otp",
            {"email": custom_user.email, "code": "111111"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.data)
        otp.refresh_from_db()
        self.assertFalse(otp.is_used)

    def test_logout_requires_authentication(self):
        res = self.client.post("/api/logout", {}, format="json")
        self.assertEqual(res.status_code, 401)

    def test_logout_deletes_token(self):
        custom_user = self._create_user()
        token, _ = Token.objects.get_or_create(user=custom_user.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        res = self.client.post("/api/logout", {}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertFalse(Token.objects.filter(key=token.key).exists())
