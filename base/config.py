import os

# 代理服务器
proxy = os.environ.get('OOI_PROXY', None)

# Cookie的secret key
secret_key = os.environ.get('OOI_SECRET_KEY', 'You Must Set A Secret Key!').encode()
