from src.schemas.urls import URLAdminResponse
import datetime


a = {'id': 1, 'original_url': 'https://kick.com/brtt', 'p_hash': None, 'short_url': 'http://localhost:8000/Nf15HKQX', 'short_code': 'Nf15HKQX', 'clicks': 0, 'title': None, 'qrcode_url': None, 'has_password': False, 'is_favorite': False, 'created_at': datetime.datetime(2025, 10, 25, 16, 8, 43, 658981, tzinfo=datetime.timezone.utc), 'expires_at': None}

r = URLAdminResponse(**a)
print(r)