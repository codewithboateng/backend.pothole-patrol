# tests/test_reports.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from tests.client import client
from core.models import UserProfile, PotholeReport

User = get_user_model()


class ReportTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="test1234")
        UserProfile.objects.create(user=self.user, phone="0244000000")

        login = client.post("/api/v1/auth/login", data={
            "username": "tester",
            "password": "test1234",
        }, content_type="application/json")

        self.token = login.json()["access"]

        # 1x1 px white image base64
        self.fake_image = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAA"
            "AAC0lEQVR42mP8/x8AAwMCAO0YlW0AAAAASUVORK5CYII="
        )

    def test_public_reports(self):
        res = client.get("/api/v1/reports/public")
        self.assertEqual(res.status_code, 200)

    def test_submit_report(self):
        payload = {
            "image_base64": "data:image/png;base64," + self.fake_image,
            "latitude": 5.6037,
            "longitude": -0.1870,
            "region": "Greater Accra",
            "severity": 5,
        }

        res = client.post(
            "/api/v1/reports/submit",
            data=payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )

        self.assertEqual(res.status_code, 200)
        self.assertIn("id", res.json())
        self.assertIn("status", res.json())