#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.
This script is the entry point for running commands like:
- python manage.py runserver
- python manage.py migrate
"""
import os
import sys

def main():
    """
    Bootstrap the Django environment and execute the command.
    """
    
    # Environment Setup:
    # Before we can do anything, Django needs to know which settings file to use.
    # 'os.environ.setdefault' sets this environment variable ONLY if it's not already set.
    # This allows us to have different settings for different environments (e.g. settings_prod.py).
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz.settings')
    try:
        # Dynamic Import:
        # We try to import Django to check if it's installed in the current Python environment.
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Friendly Error:
        # If the import fails, it means the user forgot to activate their virtualenv
        # or hasn't run 'pip install django'. We catch the obscure Python ImportError 
        # and re-raise a clear, actionable message.
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Delegation:
    # We pass the command line arguments (sys.argv) directly to Django's internals.
    # sys.argv is a list like ['manage.py', 'runserver', '8000'].
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    # Standard Python idiom. 
    # Only run main() if this file is executed directly (python manage.py), 
    # not if it's imported as a module by another script.
    main()
