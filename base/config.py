import os

# 代理服务器
proxy = os.environ.get('OOI_PROXY', None)

# Cookie的secret key
secret_key = os.environ.get('OOI_SECRET_KEY', 'You Must Set A Secret Key!').encode()

# 项目目录
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(base_dir, 'templates')
static_dir = os.path.join(base_dir, 'static')
kcs_dir = os.path.join(base_dir, '_kcs')
kcs2_dir = os.path.join(base_dir, '_kcs2')
