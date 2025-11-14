# tests/test_auth.py
from django.test import TestCase
from django.contrib.auth import get_user_model

from tests.client import client  # Use the shared client
from core.models import UserProfile

User = get_user_model()


class AuthTests(TestCase):

    def test_register_creates_user_and_profile(self):
        payload = {
            "username": "tester",
            "password": "P@ss12345",
            "phone": "0244000000",
        }

        res = client.post("/api/v1/auth/register", data=payload, content_type="application/json")
        self.assertEqual(res.status_code, 200)

        # DB checks
        self.assertTrue(User.objects.filter(username="tester").exists())
        user = User.objects.get(username="tester")
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_login_returns_jwt_tokens(self):
        # Prepare user
        user = User.objects.create_user(username="tester", password="P@ss12345")
        UserProfile.objects.create(user=user, phone="0244000000")

        payload = {
            "username": "tester",
            "password": "P@ss12345",
        }

        res = client.post("/api/v1/auth/login", data=payload, content_type="application/json")
        self.assertEqual(res.status_code, 200)

        json_data = res.json()
        self.assertIn("access", json_data)
        self.assertIn("refresh", json_data)
        self.assertEqual(json_data["username"], "tester")

    def test_me_endpoint(self):
        # Login first
        user = User.objects.create_user(username="tester", password="P@ss12345")
        UserProfile.objects.create(user=user, phone="0244000000")

        login = client.post("/api/v1/auth/login", data={
            "username": "tester",
            "password": "P@ss12345",
        }, content_type="application/json")
        self.assertEqual(login.status_code, 200)

        token = login.json()["access"]

        # Call /me with Authorization header
        res = client.get("/api/v1/auth/me", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertEqual(data["username"], "tester")
        self.assertEqual(data["phone"], "0244000000")