import importlib.util
import sys
import types
import unittest
from pathlib import Path


# main.py reads deployment settings at import time; supply isolated test settings
# so this suite exercises the direct-Python app without requiring production secrets.
settings = types.ModuleType('settings')
settings.SERVER_URL = 'https://notes.example.test'
settings.SECRET_API_KEY = 'test-secret'
settings.ALLOWED_FILETYPES = ['png', 'jpg', 'css']
settings.PORT = 8086
sys.modules['settings'] = settings
APP_PATH = Path(__file__).with_name('main.py')
spec = importlib.util.spec_from_file_location('sharenote_app', str(APP_PATH))
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
app_module.flask_app.config['TESTING'] = True


class ShareNoteUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.flask_app.test_client()

    def test_slugify_keeps_unicode_normalization_and_safe_url_characters(self):
        self.assertEqual(app_module.slugify('Crème brûlée: Hello, World!'), 'creme-brulee-hello-world')
        self.assertEqual(app_module.slugify('A  B___C'), 'a-b___c')

    def test_short_code_is_stable_and_six_characters(self):
        first = app_module.gen_short_code('Upgrade test')
        self.assertEqual(len(first), 6)
        self.assertEqual(first, app_module.gen_short_code('Upgrade test'))
        self.assertNotEqual(first, app_module.gen_short_code('Different title'))

    def test_create_note_requires_valid_authentication(self):
        response = self.client.post('/v1/file/create-note', json={'template': {}})
        self.assertEqual(response.status_code, 401)

    def test_note_ids_reject_path_and_punctuation_characters(self):
        self.assertEqual(self.client.get('/bad%2Fid').status_code, 404)
        self.assertEqual(self.client.get('/bad.id').status_code, 404)


if __name__ == '__main__':
    unittest.main()
