from .test_settings import *  # noqa: F403
from manual_contable_ai.settings import MIDDLEWARE
ROOT_URLCONF = 'manual_contable_ai.urls'
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_PATH = '/'
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_COOKIE_PATH = '/'
LOGIN_URL = '/login/'
from manual_contable_ai.settings import CSRF_FAILURE_VIEW
