#!/usr/bin/env python
"""
Create sample projects for development and testing.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_tracker.settings')
django.setup()

from accounts.models import CustomUser
from tasks.models import Project

def create_projects():
    """Create sample projects."""
    
    # Get a user to be the project owner
    users = list(CustomUser.objects.all())
    if not users:
        print("No users found. Please run create_users.py first.")
        return
    
    owner = users[0]  # Use first user as owner
    
    # Project data
    projects_data = [
        {
            "code": "TST",
            "name": "Test Project",
            "description": "Main project for testing and development",
            "is_active": True
        },
        {
            "code": "WEB",
            "name": "Web Frontend",
            "description": "Frontend development project for React components and UI",
            "is_active": True
        },
        {
            "code": "API",
            "name": "API Development",
            "description": "Backend API development and integration project",
            "is_active": True
        },
        {
            "code": "AIF",
            "name": "AI Features",
            "description": "AI-powered features and machine learning integration",
            "is_active": True
        },
        {
            "code": "OLD",
            "name": "Legacy Project",
            "description": "Old project for testing inactive states",
            "is_active": False
        }
    ]
    
    created_projects = []
    
    for project_data in projects_data:
        project, created = Project.objects.get_or_create(
            code=project_data["code"],
            defaults={
                "name": project_data["name"],
                "description": project_data["description"],
                "owner": owner,
                "is_active": project_data["is_active"]
            }
        )
        
        if created:
            created_projects.append(project)
            print(f"Created project: {project.code} - {project.name}")
        else:
            print(f"Project already exists: {project.code} - {project.name}")
    
    print(f"\n✅ Total projects: {Project.objects.count()}")
    return created_projects

if __name__ == "__main__":
    create_projects()
