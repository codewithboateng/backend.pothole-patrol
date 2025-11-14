# tests/test_rewards.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from tests.client import client
from core.models import UserProfile, RedemptionRequest

User = get_user_model()


class RewardsTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass1234")
        self.profile = UserProfile.objects.create(
            user=self.user,
            phone="0244000000",
            points=1000,
        )

        login = client.post("/api/v1/auth/login", data={
            "username": "tester",
            "password": "pass1234",
        }, content_type="application/json")

        self.token = login.json()["access"]

    def test_redeem_points(self):
        payload = {"points": 500, "mtn_phone": "0244000000"}

        res = client.post(
            "/api/v1/rewards/redeem",
            data=payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )

        self.assertEqual(res.status_code, 200)
        self.assertIn("id", res.json())

        self.assertTrue(
            RedemptionRequest.objects.filter(user=self.user).exists()
        )

    def test_redemption_history(self):
        # Create a redemption entry
        RedemptionRequest.objects.create(
            user=self.user,
            points=500,
            airtime_amount=5,
            mtn_phone="0244000000",
        )

        res = client.get(
            "/api/v1/rewards/history",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )

        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)