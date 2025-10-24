# MAS

A Django-based web application for managing construction projects, services, and teams.

## Features

1. User Authentication
   - Custom user model with department and level
   - Login/Signup functionality
   - Session persistence

2. Services Management (Admin Only)
   - Create and manage services (Electrical, PHE, Fire Fighting, etc.)
   - Add items and makes for each service
   - Track all changes with service logs

3. Project Management
   - Create and manage projects
   - Add buildings to projects
   - Manage team members and vendors
   - Auto-suggestion for project names and team members

## Setup Instructions

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment:
   - Windows:
     ```bash
     .\.venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source .venv/bin/activate
     ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Apply database migrations:
   ```bash
   python manage.py migrate
   ```

5. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Dependencies

- Django 5.2.7
- django-crispy-forms 2.4
- crispy-bootstrap4 2025.6
- Python 3.13+

## Project Structure

```
manage.py
accounts/            # User authentication and management
services/            # Services and items management
projects/            # Project and team management
static/             # Static files (CSS, JS)
templates/          # HTML templates
  ├── accounts/     # User-related templates
  ├── projects/     # Project-related templates
  ├── registration/ # Authentication templates
  └── services/     # Service-related templates
```

## License

This project is proprietary and confidential.
