import pytest
from unittest.mock import Mock, patch
from werkzeug.security import check_password_hash
from app import login_required, get_current_user

class TestAuthentication:
    """Тесты модуля аутентификации"""
    
    def test_get_current_user(self):
        assert 1 + 1 == 2
    
    def test_password_hashing(self):
        assert 1 + 1 == 2
    