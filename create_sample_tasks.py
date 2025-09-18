#!/usr/bin/env python
"""
Create sample tasks with realistic data for development and testing.
"""
import os
import sys
import django
from django.utils import timezone
from datetime import timedelta
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_tracker.settings')
django.setup()

from accounts.models import CustomUser
from tasks.models import Task, Project, TaskStatus, TaskActivity, ActivityType

def create_sample_tasks():
    """Create realistic sample tasks with estimations and assignees."""
    
    # Get users and projects
    users = list(CustomUser.objects.all())
    projects = list(Project.objects.all())
    
    if not users:
        print("No users found. Please run create_users.py first.")
        return
    
    if not projects:
        print("No projects found. Please create projects first.")
        return
    
    # Sample task data
    task_templates = [
        # Frontend Tasks
        {
            "title": "Implement user authentication UI",
            "description": "Create login and registration forms with validation, error handling, and responsive design. Include password strength indicator and remember me functionality.",
            "status": TaskStatus.TODO,
            "estimate": 8,
            "tags": ["frontend", "authentication", "ui"],
            "project_type": "web"
        },
        {
            "title": "Add dark mode toggle",
            "description": "Implement dark/light theme switcher with CSS variables, localStorage persistence, and smooth transitions. Update all components to support both themes.",
            "status": TaskStatus.IN_PROGRESS,
            "estimate": 5,
            "tags": ["frontend", "ui", "css"],
            "project_type": "web"
        },
        {
            "title": "Optimize bundle size",
            "description": "Analyze webpack bundle, implement code splitting, lazy loading, and tree shaking. Remove unused dependencies and optimize images.",
            "status": TaskStatus.TODO,
            "estimate": 13,
            "tags": ["frontend", "performance", "optimization"],
            "project_type": "web"
        },
        {
            "title": "Implement responsive navigation",
            "description": "Create mobile-friendly navigation with hamburger menu, smooth animations, and proper touch interactions. Ensure accessibility compliance.",
            "status": TaskStatus.DONE,
            "estimate": 8,
            "tags": ["frontend", "responsive", "mobile"],
            "project_type": "web"
        },
        
        # Backend Tasks
        {
            "title": "Design REST API endpoints",
            "description": "Create comprehensive API documentation, implement CRUD operations for all entities, add proper error handling and validation.",
            "status": TaskStatus.DONE,
            "estimate": 21,
            "tags": ["backend", "api", "documentation"],
            "project_type": "api"
        },
        {
            "title": "Implement user authentication",
            "description": "Set up JWT authentication, password hashing, user registration/login endpoints, and session management.",
            "status": TaskStatus.IN_PROGRESS,
            "estimate": 13,
            "tags": ["backend", "authentication", "security"],
            "project_type": "api"
        },
        {
            "title": "Add database indexing",
            "description": "Analyze query performance, add appropriate indexes, optimize slow queries, and implement database connection pooling.",
            "status": TaskStatus.TODO,
            "estimate": 8,
            "tags": ["backend", "database", "performance"],
            "project_type": "api"
        },
        {
            "title": "Implement file upload system",
            "description": "Create secure file upload endpoints with validation, virus scanning, and cloud storage integration. Support multiple file types.",
            "status": TaskStatus.TODO,
            "estimate": 21,
            "tags": ["backend", "files", "security"],
            "project_type": "api"
        },
        
        # Testing Tasks
        {
            "title": "Write unit tests for user service",
            "description": "Create comprehensive unit tests covering all user management functions, edge cases, and error scenarios. Achieve 90%+ coverage.",
            "status": TaskStatus.IN_PROGRESS,
            "estimate": 8,
            "tags": ["testing", "backend", "unit-tests"],
            "project_type": "main"
        },
        {
            "title": "Implement integration tests",
            "description": "Create end-to-end tests for critical user flows, API integration tests, and database transaction tests.",
            "status": TaskStatus.TODO,
            "estimate": 13,
            "tags": ["testing", "integration", "e2e"],
            "project_type": "main"
        },
        {
            "title": "Set up CI/CD pipeline",
            "description": "Configure automated testing, code quality checks, security scanning, and deployment pipeline with GitHub Actions.",
            "status": TaskStatus.TODO,
            "estimate": 21,
            "tags": ["devops", "ci-cd", "automation"],
            "project_type": "main"
        },
        
        # AI/ML Tasks
        {
            "title": "Implement smart task estimation",
            "description": "Develop ML model to predict task complexity based on historical data, similar tasks, and team velocity. Integrate with existing task management system.",
            "status": TaskStatus.TODO,
            "estimate": 34,
            "tags": ["ai", "ml", "estimation", "backend"],
            "project_type": "main"
        },
        {
            "title": "Add natural language processing",
            "description": "Implement NLP features for task description analysis, automatic tagging, and intelligent task categorization using transformer models.",
            "status": TaskStatus.TODO,
            "estimate": 21,
            "tags": ["ai", "nlp", "backend"],
            "project_type": "main"
        },
        
        # Infrastructure Tasks
        {
            "title": "Set up monitoring and logging",
            "description": "Implement application monitoring with Prometheus, centralized logging with ELK stack, and alerting for critical issues.",
            "status": TaskStatus.TODO,
            "estimate": 13,
            "tags": ["devops", "monitoring", "logging"],
            "project_type": "main"
        },
        {
            "title": "Implement caching strategy",
            "description": "Add Redis caching for frequently accessed data, implement cache invalidation strategies, and optimize database queries.",
            "status": TaskStatus.IN_PROGRESS,
            "estimate": 8,
            "tags": ["backend", "performance", "caching"],
            "project_type": "api"
        },
        {
            "title": "Configure load balancing",
            "description": "Set up load balancer with health checks, implement horizontal scaling, and configure auto-scaling policies.",
            "status": TaskStatus.TODO,
            "estimate": 21,
            "tags": ["devops", "scaling", "infrastructure"],
            "project_type": "main"
        },
        
        # Bug Fixes
        {
            "title": "Fix memory leak in task processing",
            "description": "Investigate and resolve memory leak in background task processor. Add proper resource cleanup and monitoring.",
            "status": TaskStatus.BLOCKED,
            "estimate": 5,
            "tags": ["bug", "performance", "backend"],
            "project_type": "main"
        },
        {
            "title": "Resolve race condition in user updates",
            "description": "Fix race condition that occurs when multiple users update the same task simultaneously. Implement proper locking mechanism.",
            "status": TaskStatus.TODO,
            "estimate": 8,
            "tags": ["bug", "concurrency", "backend"],
            "project_type": "api"
        },
        {
            "title": "Fix mobile layout issues",
            "description": "Resolve responsive design problems on mobile devices, fix touch interactions, and improve mobile user experience.",
            "status": TaskStatus.IN_PROGRESS,
            "estimate": 5,
            "tags": ["bug", "frontend", "mobile"],
            "project_type": "web"
        },
        
        # Feature Enhancements
        {
            "title": "Add task dependencies",
            "description": "Implement task dependency management with visual dependency graph, blocking relationships, and automatic status updates.",
            "status": TaskStatus.TODO,
            "estimate": 21,
            "tags": ["feature", "backend", "frontend"],
            "project_type": "main"
        },
        {
            "title": "Implement time tracking",
            "description": "Add time tracking functionality with start/stop timers, manual time entry, and time reporting features.",
            "status": TaskStatus.TODO,
            "estimate": 13,
            "tags": ["feature", "time-tracking", "backend"],
            "project_type": "main"
        },
        {
            "title": "Add advanced filtering and search",
            "description": "Implement full-text search, advanced filtering options, saved filters, and search suggestions for better task discovery.",
            "status": TaskStatus.TODO,
            "estimate": 8,
            "tags": ["feature", "search", "frontend"],
            "project_type": "web"
        }
    ]
    
    # Create tasks
    created_tasks = []
    
    for i, template in enumerate(task_templates):
        # Select random assignee and reporter
        assignee = random.choice(users)
        reporter = random.choice(users)
        
        # Select project based on type
        project_type = template.get("project_type", "main")
        project_mapping = {
            "main": "TST",
            "web": "WEB", 
            "api": "API",
            "ai": "AIF"
        }
        project_code = project_mapping.get(project_type, "TST")
        project = next((p for p in projects if p.code == project_code), projects[0])
        
        # Create task
        task = Task.objects.create(
            project=project,
            title=template["title"],
            description=template["description"],
            status=template["status"],
            estimate=template["estimate"],
            assignee=assignee,
            reporter=reporter,
            tags=template["tags"]
        )
        
        # Create some activities for the task
        activities = []
        
        # Always add creation activity
        activities.append(TaskActivity.objects.create(
            task=task,
            type=ActivityType.CREATED,
            actor=reporter
        ))
        
        # Add status change if not TODO
        if template["status"] != TaskStatus.TODO:
            activities.append(TaskActivity.objects.create(
                task=task,
                type=ActivityType.UPDATED_STATUS,
                field="status",
                before=TaskStatus.TODO,
                after=template["status"],
                actor=assignee
            ))
        
        # Add assignment activity
        activities.append(TaskActivity.objects.create(
            task=task,
            type=ActivityType.UPDATED_ASSIGNEE,
            field="assignee",
            before=None,
            after=str(assignee.id),
            actor=reporter
        ))
        
        # Add estimate activity
        activities.append(TaskActivity.objects.create(
            task=task,
            type=ActivityType.UPDATED_ESTIMATE,
            field="estimate",
            before=None,
            after=template["estimate"],
            actor=assignee
        ))
        
        # Add some random activities for variety
        if random.random() < 0.3:  # 30% chance
            activities.append(TaskActivity.objects.create(
                task=task,
                type=ActivityType.UPDATED_DESCRIPTION,
                field="description",
                before="Initial description",
                after=template["description"][:50] + "...",
                actor=assignee
            ))
        
        created_tasks.append(task)
        print(f"Created task: {task.title} (Project: {project.code}, Assignee: {assignee.username}, Estimate: {task.estimate})")
    
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
    create_sample_tasks()
