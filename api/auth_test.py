import unittest
from fastapi import HTTPException
from api.auth import get_token
from config import API_TOKEN
from http import HTTPStatus


class DummyRequest:
    def __init__(self, headers):
        self.headers = headers


class TestAuth(unittest.TestCase):
    def test_missing_authorization_header(self):
        request = DummyRequest(headers={})
        with self.assertRaises(HTTPException) as cm:
            get_token(request)
        exc = cm.exception
        self.assertEqual(exc.status_code, HTTPStatus.UNAUTHORIZED)
        self.assertIn("Authorization", exc.detail)

    def test_invalid_authorization_header_format(self):
        request = DummyRequest(headers={"Authorization": "Token abc"})
        with self.assertRaises(HTTPException) as cm:
            get_token(request)
        exc = cm.exception
        self.assertEqual(exc.status_code, HTTPStatus.UNAUTHORIZED)
        self.assertIn("Authorization", exc.detail)

    def test_invalid_token(self):
        request = DummyRequest(headers={"Authorization": "Bearer wrongtoken"})
        with self.assertRaises(HTTPException) as cm:
            get_token(request)
        exc = cm.exception
        self.assertEqual(exc.status_code, HTTPStatus.FORBIDDEN)
        self.assertIn("Invalid token", exc.detail)

    def test_valid_token(self):
        request = DummyRequest(headers={"Authorization": f"Bearer {API_TOKEN}"})
        token = get_token(request)
        self.assertEqual(token, API_TOKEN)


if __name__ == "__main__":
    unittest.main()
