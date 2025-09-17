#!/usr/bin/env python
"""
Script to create users for the task tracker application.
Creates admin user and 5 additional superuser accounts.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_tracker.settings')
django.setup()

from accounts.models import CustomUser

def create_users():
    """Create admin user and 5 additional superusers."""
    
    # Create admin user
    admin_user, created = CustomUser.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print(f"Created admin user: {admin_user.username}")
    else:
        print(f"Admin user already exists: {admin_user.username}")
    
    # Create 5 additional superusers
    users_data = [
        {
            'username': 'user1',
            'email': 'user1@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'password123'
        },
        {
            'username': 'user2',
            'email': 'user2@example.com',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'password': 'password123'
        },
        {
            'username': 'user3',
            'email': 'user3@example.com',
            'first_name': 'Bob',
            'last_name': 'Johnson',
            'password': 'password123'
        },
        {
            'username': 'user4',
            'email': 'user4@example.com',
            'first_name': 'Alice',
            'last_name': 'Williams',
            'password': 'password123'
        },
        {
            'username': 'user5',
            'email': 'user5@example.com',
            'first_name': 'Charlie',
            'last_name': 'Brown',
            'password': 'password123'
        }
    ]
    
    for user_data in users_data:
        user, created = CustomUser.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        if created:
            user.set_password(user_data['password'])
            user.save()
            print(f"Created superuser: {user.username} ({user.email})")
        else:
            print(f"User already exists: {user.username}")
    
    print(f"\nTotal users in database: {CustomUser.objects.count()}")
    print("All users are superusers with staff privileges.")

if __name__ == '__main__':
    create_users()