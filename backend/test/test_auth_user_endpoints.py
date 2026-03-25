import os
import tempfile
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User


class AuthUserEndpointsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_fd, cls.db_path = tempfile.mkstemp(suffix=".db")
        cls.engine = create_engine(
            f"sqlite:///{cls.db_path}",
            connect_args={"check_same_thread": False},
        )
        cls.TestSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=cls.engine,
        )
        Base.metadata.create_all(bind=cls.engine)

        def override_get_db():
            db = cls.TestSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()
        os.close(cls.db_fd)
        os.unlink(cls.db_path)

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        session = self.TestSessionLocal()
        try:
            session.add_all(
                [
                    User(
                        userName="Super",
                        email="super@example.com",
                        phone="13800000000",
                        password="123456",
                        role="super_admin",
                        status=1,
                    ),
                    User(
                        userName="Admin",
                        email="admin@example.com",
                        phone="13800000001",
                        password="123456",
                        role="admin",
                        status=1,
                    ),
                ]
            )
            session.commit()
        finally:
            session.close()

    def test_create_user_accepts_json_body_and_returns_frontend_compatible_fields(self):
        response = self.client.post(
            "/api/user",
            json={
                "userName": "NewUser",
                "userEmail": "newuser@example.com",
                "userPhone": "13800000002",
                "userGender": "male",
                "userRoles": ["R_USER"],
                "password": "abc123",
                "status": "1",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertEqual(payload["userName"], "NewUser")
        self.assertEqual(payload["userEmail"], "newuser@example.com")

    def test_login_upgrades_legacy_plaintext_password_and_returns_current_user_info(self):
        login_response = self.client.post(
            "/api/auth/login",
            json={"userName": "Admin", "password": "123456"},
        )

        self.assertEqual(login_response.status_code, 200)
        token = login_response.json()["data"]["token"]

        info_response = self.client.get(
            "/api/auth/user/info",
            headers={"Authorization": token},
        )

        self.assertEqual(info_response.status_code, 200)
        payload = info_response.json()["data"]
        self.assertEqual(payload["userName"], "Admin")
        self.assertEqual(payload["userPhone"], "13800000001")
        self.assertEqual(payload["roles"], ["R_ADMIN"])
        self.assertEqual(payload["buttons"], ["add", "edit", "view"])

        session = self.TestSessionLocal()
        try:
            admin = session.query(User).filter(User.userName == "Admin").first()
            self.assertNotEqual(admin.password, "123456")
        finally:
            session.close()

    def test_reset_password_hashes_new_password_and_allows_login(self):
        forgot_response = self.client.post(
            "/api/auth/forgot-password",
            json={"email": "admin@example.com"},
        )
        self.assertEqual(forgot_response.status_code, 200)

        from app.api.v1.endpoints.auth import verification_codes

        reset_response = self.client.post(
            "/api/auth/reset-password",
            json={
                "email": "admin@example.com",
                "code": verification_codes["admin@example.com"],
                "newPassword": "newpass123",
                "confirmPassword": "newpass123",
            },
        )
        self.assertEqual(reset_response.status_code, 200)

        login_response = self.client.post(
            "/api/auth/login",
            json={"userName": "Admin", "password": "newpass123"},
        )
        self.assertEqual(login_response.status_code, 200)

    def test_user_info_rejects_missing_token(self):
        response = self.client.get("/api/auth/user/info")
        self.assertEqual(response.status_code, 401)

    def test_change_password_requires_current_password_and_updates_login_password(self):
        login_response = self.client.post(
            "/api/auth/login",
            json={"userName": "Admin", "password": "123456"},
        )
        self.assertEqual(login_response.status_code, 200)
        token = login_response.json()["data"]["token"]

        wrong_response = self.client.post(
            "/api/auth/change-password",
            json={
                "currentPassword": "wrong-pass",
                "newPassword": "changed123",
                "confirmPassword": "changed123",
            },
            headers={"Authorization": token},
        )
        self.assertEqual(wrong_response.status_code, 400)

        change_response = self.client.post(
            "/api/auth/change-password",
            json={
                "currentPassword": "123456",
                "newPassword": "changed123",
                "confirmPassword": "changed123",
            },
            headers={"Authorization": token},
        )
        self.assertEqual(change_response.status_code, 200)

        old_login = self.client.post(
            "/api/auth/login",
            json={"userName": "Admin", "password": "123456"},
        )
        self.assertEqual(old_login.status_code, 401)

        new_login = self.client.post(
            "/api/auth/login",
            json={"userName": "Admin", "password": "changed123"},
        )
        self.assertEqual(new_login.status_code, 200)


if __name__ == "__main__":
    unittest.main()
