from passlib.context import CryptContext
from pyramid import threadlocal


settings = threadlocal.get_current_registry().settings
crypt_method = settings['crypt_method']

pwd_context = CryptContext(schemes=crypt_method, deprecated='auto')

