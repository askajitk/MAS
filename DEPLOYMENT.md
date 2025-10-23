# PythonAnywhere Deployment Guide for MAS Project

## Prerequisites
- GitHub account with MAS repository
- PythonAnywhere account (free or paid)

## Step 1: Clone Repository on PythonAnywhere

1. Open a **Bash console** from PythonAnywhere dashboard
2. Clone your repository:
   ```bash
   git clone https://github.com/askajitk/MAS.git
   cd MAS
   ```

## Step 2: Create and Setup Virtual Environment

```bash
# Create virtual environment (replace with your Python version)
mkvirtualenv --python=/usr/bin/python3.10 mas_env

# Activate environment (if not auto-activated)
workon mas_env

# Install dependencies
pip install -r requirements.txt

# If using MySQL, also install:
pip install mysqlclient
```

## Step 3: Setup Web App on PythonAnywhere

1. Go to **Web** tab in PythonAnywhere dashboard
2. Click **Add a new web app**
3. Choose **Manual configuration** (not Django wizard)
4. Select **Python 3.10** (or your version)
5. Click **Next**

## Step 4: Configure WSGI File

1. In the **Web** tab, click on the WSGI configuration file link
2. Delete the default content
3. Replace with content from `pythonanywhere_wsgi.py` file
4. **Important**: Replace `yourusername` with your actual PythonAnywhere username

Example:
```python
import os
import sys

path = '/home/YOUR_USERNAME/MAS'  # ← Change this
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'mas.settings'

virtualenv_path = '/home/YOUR_USERNAME/.virtualenvs/mas_env'  # ← Change this
activate_this = os.path.join(virtualenv_path, 'bin/activate_this.py')
exec(open(activate_this).read(), {'__file__': activate_this})

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## Step 5: Configure Static and Media Files

In the **Web** tab, scroll down to **Static files** section:

1. **Static files**:
   - URL: `/static/`
   - Directory: `/home/yourusername/MAS/staticfiles/`

2. **Media files**:
   - URL: `/media/`
   - Directory: `/home/yourusername/MAS/media/`

## Step 6: Update Django Settings

1. Update `mas/settings.py`:
   ```python
   # Add your PythonAnywhere domain to ALLOWED_HOSTS
   ALLOWED_HOSTS = ['yourusername.pythonanywhere.com', 'localhost', '127.0.0.1']
   
   # Set DEBUG to False for production
   DEBUG = False  # IMPORTANT for production
   
   # Optional: Use production settings
   # Or keep it simple and just update ALLOWED_HOSTS and DEBUG
   ```

2. Generate a new SECRET_KEY for production:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   Copy this and replace SECRET_KEY in settings.py

## Step 7: Collect Static Files

In Bash console:
```bash
cd ~/MAS
workon mas_env
python manage.py collectstatic
```

## Step 8: Run Migrations

```bash
python manage.py migrate
```

## Step 9: Create Superuser

```bash
python manage.py createsuperuser
```
Follow the prompts to create an admin account.

## Step 10: Reload Web App

1. Go back to the **Web** tab
2. Click the green **Reload** button at the top
3. Visit your site: `https://yourusername.pythonanywhere.com`

## Troubleshooting

### Check Error Logs
- Go to **Web** tab
- Scroll down to **Log files**
- Check **Error log** and **Server log** for issues

### Common Issues

1. **Static files not loading**:
   - Make sure you ran `collectstatic`
   - Check static file paths in Web tab
   - Verify STATIC_ROOT in settings.py

2. **500 Internal Server Error**:
   - Check error log
   - Make sure DEBUG=False is set
   - Verify ALLOWED_HOSTS includes your domain

3. **Database errors**:
   - Check migrations are applied: `python manage.py migrate`
   - Verify database file permissions (SQLite)

4. **Import errors**:
   - Make sure virtual environment is activated in WSGI file
   - Check all dependencies are installed: `pip list`

### Database Options

**Option 1: SQLite (Easier for starting)**
- Keep the default SQLite configuration
- Database file will be created in project root
- No additional setup needed

**Option 2: MySQL (Better for production)**
1. Go to **Databases** tab in PythonAnywhere
2. Create a new MySQL database
3. Note the database name, username, and password
4. Update DATABASES in settings.py with MySQL configuration
5. Install mysqlclient: `pip install mysqlclient`
6. Run migrations: `python manage.py migrate`

## Post-Deployment

1. **Create users** via Django admin or signup page
2. **Create projects, buildings, services** through admin interface
3. **Assign team members and vendors** to projects
4. **Test the complete workflow**: Create MAS → Review → Approve

## Updating the Application

When you make changes to code:

```bash
# On PythonAnywhere Bash console
cd ~/MAS
git pull origin master
workon mas_env
pip install -r requirements.txt  # If dependencies changed
python manage.py migrate  # If models changed
python manage.py collectstatic --noinput  # If static files changed
```

Then reload the web app from the Web tab.

## Security Checklist

- [ ] DEBUG = False in production
- [ ] SECRET_KEY is unique and kept secret
- [ ] ALLOWED_HOSTS is properly configured
- [ ] Database credentials are secure
- [ ] HTTPS is enabled (automatic on PythonAnywhere)
- [ ] Static files are served correctly
- [ ] Media upload directory has proper permissions

## Support

- PythonAnywhere Help: https://help.pythonanywhere.com/
- PythonAnywhere Forums: https://www.pythonanywhere.com/forums/
- Django Deployment Docs: https://docs.djangoproject.com/en/5.2/howto/deployment/

## Notes

- Free PythonAnywhere accounts have limitations (1 web app, limited CPU time)
- Consider upgrading to paid account for production use
- Schedule regular backups of database and media files
- Monitor error logs regularly
