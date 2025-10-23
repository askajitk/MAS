# +++++++++++ DJANGO +++++++++++
# To use your own django app use code like this:
import os
import sys

# Add your project directory to the sys.path
path = '/home/askajitk/MAS'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables
os.environ['DJANGO_SETTINGS_MODULE'] = 'mas.settings'

# Activate virtual environment
virtualenv_path = '/home/askajitk/.virtualenvs/mas_env'
activate_this = os.path.join(virtualenv_path, 'bin/activate_this.py')
exec(open(activate_this).read(), {'__file__': activate_this})

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
