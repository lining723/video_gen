from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path


class ApiAuthTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        os.environ['APP_API_KEY'] = 'test-key'
        from backend.src.settings import config as config_module
        config_module.DATA_ROOT = Path(self.tempdir.name) / 'data'
        config_module.MEDIA_ROOT = config_module.DATA_ROOT / 'media'
        config_module.CACHE_ROOT = config_module.MEDIA_ROOT / 'cache'
        config_module.OBJECT_ROOT = config_module.MEDIA_ROOT / 'object_store'
        config_module.DB_ROOT = config_module.DATA_ROOT / 'db'
        config_module.LOG_ROOT = config_module.DATA_ROOT / 'logs'
        config_module.SQLITE_PATH = config_module.DB_ROOT / 'app.sqlite3'
        config_module.ensure_dirs()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_auth_rules(self):
        from backend.src.api.app import RequestHandler
        self.assertTrue(RequestHandler._is_auth_exempt(RequestHandler, '/healthz'))
        self.assertTrue(RequestHandler._is_auth_exempt(RequestHandler, '/media/demo.mp4'))
        self.assertFalse(RequestHandler._is_auth_exempt(RequestHandler, '/api/projects'))

    def test_readyz_database_path_exists(self):
        from backend.src.settings.config import SQLITE_PATH
        self.assertTrue(Path(SQLITE_PATH).parent.exists())

    def test_parse_byte_range(self):
        from backend.src.api.app import parse_byte_range
        self.assertEqual(parse_byte_range('bytes=0-99', 200), (0, 99))
        self.assertEqual(parse_byte_range('bytes=100-', 200), (100, 199))
        self.assertEqual(parse_byte_range('bytes=-50', 200), (150, 199))


if __name__ == '__main__':
    unittest.main()
