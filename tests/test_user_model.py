import unittest
from app.models import User


class UserModelTestCase(unittest.TestCase):
    def test_password_setter(self):
        user = User(password="hash")
        self.assertTrue(user.password_hash is not None)

    def test_password_no_getter(self):
        user = User(password="hash")
        with self.assertRaises(AttributeError):
            user.password

    def test_password_verify(self):
        user = User(password="hash")
        self.assertTrue(user.password_verify("hash"))
        self.assertFalse(user.password_verify("test"))

    def test_salt(self):
        user = User(password="hash")
        user2 = User(password="hash2")
        self.assertTrue(user.password_hash != user2.password_hash)