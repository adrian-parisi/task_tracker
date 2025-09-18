#!/usr/bin/env python
"""
Create simple sample tasks without complex queries.
"""
import os
import sys
import django
from django.utils import timezone
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_tracker.settings')
django.setup()

from accounts.models import CustomUser
from tasks.models import Task, Project, TaskStatus, TaskActivity, ActivityType

def create_simple_tasks():
    """Create simple sample tasks."""
    
    # Get users
    users = list(CustomUser.objects.all())
    if not users:
        print("No users found. Please run create_users.py first.")
        return
    
    # Get projects one by one to avoid UUID issues
    try:
        main_project = Project.objects.get(code='TST')
        web_project = Project.objects.get(code='WEB')
        api_project = Project.objects.get(code='API')
    except Project.DoesNotExist:
        print("Projects not found. Please run create_projects.py first.")
        return
    
    # Simple task data
    tasks_data = [
        {
            "title": "Fix login button styling",
            "description": "Update the login button to match the new design system with proper hover states and accessibility.",
            "status": TaskStatus.TODO,
            "estimate": 3,
            "tags": ["frontend", "ui", "bug"],
            "project": web_project
        },
        {
            "title": "Add user profile API endpoint",
            "description": "Create REST API endpoint for user profile management with proper validation and error handling.",
            "status": TaskStatus.IN_PROGRESS,
            "estimate": 8,
            "tags": ["backend", "api", "user-management"],
            "project": api_project
        },
        {
            "title": "Implement task filtering",
            "description": "Add filtering functionality to task list with status, assignee, and date filters.",
            "status": TaskStatus.TODO,
            "estimate": 13,
            "tags": ["frontend", "feature", "filtering"],
            "project": web_project
        },
        {
            "title": "Optimize database queries",
            "description": "Review and optimize slow database queries, add missing indexes, and implement query caching.",
            "status": TaskStatus.DONE,
            "estimate": 8,
            "tags": ["backend", "performance", "database"],
            "project": api_project
        },
        {
            "title": "Add unit tests for task model",
            "description": "Write comprehensive unit tests for Task model covering all methods and edge cases.",
            "status": TaskStatus.TODO,
            "estimate": 5,
            "tags": ["testing", "backend", "unit-tests"],
            "project": main_project
        },
        {
            "title": "Implement dark mode",
            "description": "Add dark/light theme toggle with CSS variables and localStorage persistence.",
            "status": TaskStatus.IN_PROGRESS,
            "estimate": 8,
            "tags": ["frontend", "ui", "theme"],
            "project": web_project
        },
        {
            "title": "Create API documentation",
            "description": "Generate comprehensive API documentation using drf-spectacular with examples and schemas.",
            "status": TaskStatus.DONE,
            "estimate": 5,
            "tags": ["documentation", "api", "backend"],
            "project": api_project
        },
        {
            "title": "Add task comments system",
            "description": "Implement commenting system for tasks with real-time updates and user mentions.",
            "status": TaskStatus.TODO,
            "estimate": 21,
            "tags": ["feature", "backend", "frontend"],
            "project": main_project
        },
        {
            "title": "Fix mobile responsiveness",
            "description": "Resolve responsive design issues on mobile devices and improve touch interactions.",
            "status": TaskStatus.BLOCKED,
            "estimate": 8,
            "tags": ["frontend", "mobile", "responsive"],
            "project": web_project
        },
        {
            "title": "Implement file upload",
            "description": "Add secure file upload functionality with validation and cloud storage integration.",
            "status": TaskStatus.TODO,
            "estimate": 13,
            "tags": ["backend", "files", "security"],
            "project": api_project
        },
        {
            "title": "Add email notifications",
            "description": "Implement email notifications for task updates, assignments, and deadlines.",
            "status": TaskStatus.TODO,
            "estimate": 8,
            "tags": ["backend", "notifications", "email"],
            "project": main_project
        },
        {
            "title": "Create dashboard analytics",
            "description": "Build analytics dashboard with task completion rates, team velocity, and project metrics.",
            "status": TaskStatus.TODO,
            "estimate": 21,
            "tags": ["frontend", "analytics", "dashboard"],
            "project": web_project
        }
    ]
    
    created_tasks = []
    
    for task_data in tasks_data:
        # Select random assignee and reporter
        assignee = random.choice(users)
        reporter = random.choice(users)
        
        # Create task
        task = Task.objects.create(
            project=task_data["project"],
            title=task_data["title"],
            description=task_data["description"],
            status=task_data["status"],
            estimate=task_data["estimate"],
            assignee=assignee,
            reporter=reporter,
            tags=task_data["tags"]
        )
        
        # Create basic activities
        TaskActivity.objects.create(
            task=task,
            type=ActivityType.CREATED,
            actor=reporter
        )
        
        if task_data["status"] != TaskStatus.TODO:
            TaskActivity.objects.create(
                task=task,
                type=ActivityType.UPDATED_STATUS,
                field="status",
                before=TaskStatus.TODO,
                after=task_data["status"],
                actor=assignee
            )
        
        TaskActivity.objects.create(
            task=task,
            type=ActivityType.UPDATED_ASSIGNEE,
            field="assignee",
            before=None,
            after=str(assignee.id),
            actor=reporter
        )
        
        TaskActivity.objects.create(
            task=task,
            type=ActivityType.UPDATED_ESTIMATE,
            field="estimate",
            before=None,
            after=task_data["estimate"],
            actor=assignee
        )
        
        created_tasks.append(task)
        print(f"Created task: {task.title} (Project: {task.project.code}, Assignee: {assignee.username}, Estimate: {task.estimate})")
    
    print(f"\n✅ Created {len(created_tasks)} sample tasks")
    print(f"📊 Tasks by status:")
    status_counts = {}
    for task in created_tasks:
        status_counts[task.status] = status_counts.get(task.status, 0) + 1
    
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    print(f"📊 Tasks by project:")
    project_counts = {}
    for task in created_tasks:
        project_counts[task.project.code] = project_counts.get(task.project.code, 0) + 1
    
    for project, count in project_counts.items():
        print(f"  {project}: {count}")
    
    print(f"📊 Total estimate points: {sum(task.estimate for task in created_tasks if task.estimate)}")

if __name__ == "__main__":
    create_simple_tasks()
