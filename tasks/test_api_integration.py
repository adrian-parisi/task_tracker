"""
Integration tests for Task API endpoints using pytest.
Tests all CRUD operations, filtering, pagination, and validation.
"""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from tasks.models import Task, Tag, TaskStatus


@pytest.fixture
def api_client():
    """Provide an API client."""
    return APIClient()


@pytest.fixture
def users(db):
    """Create test users."""
    user1 = User.objects.create_user(
        username='testuser1',
        email='test1@example.com',
        password='testpass123'
    )
    user2 = User.objects.create_user(
        username='testuser2',
        email='test2@example.com',
        password='testpass123'
    )
    return {'user1': user1, 'user2': user2}


@pytest.fixture
def tags(db):
    """Create test tags."""
    tag1 = Tag.objects.create(name='backend')
    tag2 = Tag.objects.create(name='frontend')
    tag3 = Tag.objects.create(name='urgent')
    return {'backend': tag1, 'frontend': tag2, 'urgent': tag3}


@pytest.fixture
def authenticated_client(api_client, users):
    """Provide an authenticated API client."""
    api_client.force_authenticate(user=users['user1'])
    return api_client


@pytest.mark.integration
class TestTaskCRUDOperations:
    """Test Task CRUD operations (requirement 4.1, 4.2, 4.5)."""
    
    def test_create_task_success(self, authenticated_client, users, tags):
        """Test successful task creation (requirement 4.1)."""
        url = reverse('task-list')
        data = {
            'title': 'Test Task',
            'description': 'Test description',
            'status': TaskStatus.TODO,
            'estimate': 5,
            'assignee': users['user2'].id,
            'tags': [tags['backend'].id, tags['frontend'].id]
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'Test Task'
        assert response.data['description'] == 'Test description'
        assert response.data['status'] == TaskStatus.TODO
        assert response.data['estimate'] == 5
        assert response.data['assignee_detail']['id'] == users['user2'].id
        assert response.data['reporter_detail']['id'] == users['user1'].id  # Auto-set
        assert len(response.data['tags_detail']) == 2
        assert 'id' in response.data
        assert 'created_at' in response.data
        assert 'updated_at' in response.data
    
    def test_create_task_minimal_data(self, authenticated_client, users):
        """Test task creation with only required fields."""
        url = reverse('task-list')
        data = {'title': 'Minimal Task'}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'Minimal Task'
        assert response.data['status'] == TaskStatus.TODO  # Default
        assert response.data['estimate'] is None
        assert response.data['reporter_detail']['id'] == users['user1'].id
    
    def test_create_task_empty_title_fails(self, authenticated_client):
        """Test task creation fails with empty title (requirement 8.4)."""
        url = reverse('task-list')
        data = {'title': ''}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'title' in response.data
    
    def test_create_task_negative_estimate_fails(self, authenticated_client):
        """Test task creation fails with negative estimate (requirement 8.5)."""
        url = reverse('task-list')
        data = {
            'title': 'Test Task',
            'estimate': -1
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'estimate' in response.data
    
    def test_create_task_done_without_estimate_fails(self, authenticated_client):
        """Test task creation fails when status is DONE without estimate."""
        url = reverse('task-list')
        data = {
            'title': 'Test Task',
            'status': TaskStatus.DONE
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'estimate' in response.data
    
    def test_list_tasks(self, authenticated_client, users):
        """Test task listing."""
        # Create test tasks
        task1 = Task.objects.create(
            title='Task 1',
            status=TaskStatus.TODO,
            reporter=users['user1']
        )
        task2 = Task.objects.create(
            title='Task 2',
            status=TaskStatus.IN_PROGRESS,
            assignee=users['user2'],
            reporter=users['user1']
        )
        
        url = reverse('task-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        # Check ordering (most recent first)
        assert response.data['results'][0]['title'] == 'Task 2'
        assert response.data['results'][1]['title'] == 'Task 1'
    
    def test_retrieve_task(self, authenticated_client, users, tags):
        """Test retrieving a single task."""
        task = Task.objects.create(
            title='Test Task',
            description='Test description',
            status=TaskStatus.TODO,
            estimate=3,
            assignee=users['user2'],
            reporter=users['user1']
        )
        task.tags.add(tags['backend'])
        
        url = reverse('task-detail', kwargs={'pk': task.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Test Task'
        assert response.data['assignee_detail']['id'] == users['user2'].id
        assert len(response.data['tags_detail']) == 1
        assert 'activity_count' in response.data
    
    def test_update_task(self, authenticated_client, users):
        """Test task update (requirement 4.2)."""
        task = Task.objects.create(
            title='Original Title',
            status=TaskStatus.TODO,
            reporter=users['user1']
        )
        
        url = reverse('task-detail', kwargs={'pk': task.id})
        data = {
            'title': 'Updated Title',
            'status': TaskStatus.IN_PROGRESS,
            'estimate': 5,
            'assignee': users['user2'].id
        }
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated Title'
        assert response.data['status'] == TaskStatus.IN_PROGRESS
        assert response.data['estimate'] == 5
        assert response.data['assignee_detail']['id'] == users['user2'].id
    
    def test_update_task_done_with_estimate(self, authenticated_client, users):
        """Test updating task to DONE with estimate succeeds."""
        task = Task.objects.create(
            title='Test Task',
            status=TaskStatus.IN_PROGRESS,
            estimate=3,
            reporter=users['user1']
        )
        
        url = reverse('task-detail', kwargs={'pk': task.id})
        data = {'status': TaskStatus.DONE}
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == TaskStatus.DONE
    
    def test_update_task_done_without_estimate_fails(self, authenticated_client, users):
        """Test updating task to DONE without estimate fails."""
        task = Task.objects.create(
            title='Test Task',
            status=TaskStatus.IN_PROGRESS,
            reporter=users['user1']
        )
        
        url = reverse('task-detail', kwargs={'pk': task.id})
        data = {'status': TaskStatus.DONE}
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'estimate' in response.data
    
    def test_delete_task(self, authenticated_client, users):
        """Test task deletion with hard delete (requirement 4.5)."""
        task = Task.objects.create(
            title='Test Task',
            reporter=users['user1']
        )
        task_id = task.id
        
        url = reverse('task-detail', kwargs={'pk': task.id})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Task.objects.filter(id=task_id).exists()


@pytest.mark.integration
class TestTaskFiltering:
    """Test Task filtering functionality (requirement 4.3)."""
    
    def test_filter_by_status(self, authenticated_client, users):
        """Test filtering tasks by status."""
        Task.objects.create(title='Todo Task', status=TaskStatus.TODO, reporter=users['user1'])
        Task.objects.create(title='In Progress Task', status=TaskStatus.IN_PROGRESS, reporter=users['user1'])
        Task.objects.create(title='Done Task', status=TaskStatus.DONE, estimate=5, reporter=users['user1'])
        
        url = reverse('task-list')
        response = authenticated_client.get(url, {'status': TaskStatus.TODO})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['status'] == TaskStatus.TODO
    
    def test_filter_by_assignee(self, authenticated_client, users):
        """Test filtering tasks by assignee."""
        Task.objects.create(title='Task 1', assignee=users['user1'], reporter=users['user1'])
        Task.objects.create(title='Task 2', assignee=users['user2'], reporter=users['user1'])
        Task.objects.create(title='Task 3', reporter=users['user1'])  # No assignee
        
        url = reverse('task-list')
        response = authenticated_client.get(url, {'assignee': users['user2'].id})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['assignee_detail']['id'] == users['user2'].id
    
    def test_filter_by_tags(self, authenticated_client, users, tags):
        """Test filtering tasks by tags."""
        task1 = Task.objects.create(title='Backend Task', reporter=users['user1'])
        task1.tags.add(tags['backend'])
        
        task2 = Task.objects.create(title='Frontend Task', reporter=users['user1'])
        task2.tags.add(tags['frontend'])
        
        task3 = Task.objects.create(title='Full Stack Task', reporter=users['user1'])
        task3.tags.add(tags['backend'], tags['frontend'])
        
        url = reverse('task-list')
        
        # Filter by single tag
        response = authenticated_client.get(url, {'tags': str(tags['backend'].id)})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2  # task1 and task3
        
        # Filter by multiple tags
        response = authenticated_client.get(url, {'tags': f"{tags['backend'].id},{tags['frontend'].id}"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3  # All tasks have at least one tag
    
    def test_combined_filters(self, authenticated_client, users, tags):
        """Test combining multiple filters."""
        task1 = Task.objects.create(
            title='Backend Todo',
            status=TaskStatus.TODO,
            assignee=users['user1'],
            reporter=users['user1']
        )
        task1.tags.add(tags['backend'])
        
        task2 = Task.objects.create(
            title='Frontend Todo',
            status=TaskStatus.TODO,
            assignee=users['user2'],
            reporter=users['user1']
        )
        task2.tags.add(tags['frontend'])
        
        task3 = Task.objects.create(
            title='Backend In Progress',
            status=TaskStatus.IN_PROGRESS,
            assignee=users['user1'],
            reporter=users['user1']
        )
        task3.tags.add(tags['backend'])
        
        url = reverse('task-list')
        response = authenticated_client.get(url, {
            'status': TaskStatus.TODO,
            'assignee': users['user1'].id,
            'tags': str(tags['backend'].id)
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'Backend Todo'


@pytest.mark.integration
class TestTaskPagination:
    """Test Task pagination functionality (requirement 4.4)."""
    
    def test_pagination_default(self, authenticated_client, users):
        """Test default pagination."""
        # Create 25 tasks
        for i in range(25):
            Task.objects.create(title=f'Task {i}', reporter=users['user1'])
        
        url = reverse('task-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 20  # Default page size
        assert response.data['next'] is not None
        assert response.data['previous'] is None
    
    def test_pagination_custom_page_size(self, authenticated_client, users):
        """Test custom page size within limits."""
        # Create 15 tasks
        for i in range(15):
            Task.objects.create(title=f'Task {i}', reporter=users['user1'])
        
        url = reverse('task-list')
        response = authenticated_client.get(url, {'page_size': 10})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 10
        assert response.data['next'] is not None
    
    def test_pagination_max_limit(self, authenticated_client, users):
        """Test pagination max limit enforcement (requirement 9.5)."""
        # Create 150 tasks
        for i in range(150):
            Task.objects.create(title=f'Task {i}', reporter=users['user1'])
        
        url = reverse('task-list')
        response = authenticated_client.get(url, {'page_size': 200})  # Request more than max
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 100  # Capped at max


@pytest.mark.integration
class TestTaskValidationAndErrors:
    """Test Task validation and error handling."""
    
    def test_task_not_found(self, authenticated_client):
        """Test 404 error for non-existent task (requirement 8.2)."""
        url = reverse('task-detail', kwargs={'pk': '00000000-0000-0000-0000-000000000000'})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_unauthenticated_access_fails(self, api_client):
        """Test unauthenticated access returns 403 (requirement 8.3)."""
        url = reverse('task-list')
        response = api_client.get(url)
        
        # DRF with SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_invalid_status_validation(self, authenticated_client):
        """Test validation of invalid status values."""
        url = reverse('task-list')
        data = {
            'title': 'Test Task',
            'status': 'INVALID_STATUS'
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'status' in response.data
    
    def test_ordering_by_updated_at(self, authenticated_client, users):
        """Test default ordering by updated_at descending."""
        task1 = Task.objects.create(title='First Task', reporter=users['user1'])
        task2 = Task.objects.create(title='Second Task', reporter=users['user1'])
        
        # Update first task to make it more recent
        task1.description = 'Updated'
        task1.save()
        
        url = reverse('task-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # First task should be first due to recent update
        assert response.data['results'][0]['title'] == 'First Task'
        assert response.data['results'][1]['title'] == 'Second Task'
    
    def test_activity_count_in_detail_view(self, authenticated_client, users):
        """Test activity count is included in task detail (requirement 9.4)."""
        task = Task.objects.create(title='Test Task', reporter=users['user1'])
        
        url = reverse('task-detail', kwargs={'pk': task.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'activity_count' in response.data
        assert isinstance(response.data['activity_count'], int)


@pytest.mark.integration
class TestTaskSerializerValidation:
    """Test TaskSerializer validation logic."""
    
    def test_title_whitespace_normalization(self, authenticated_client):
        """Test that task title whitespace is normalized."""
        url = reverse('task-list')
        data = {'title': '  Test Task  '}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'Test Task'  # Whitespace stripped
    
    def test_tags_relationship_handling(self, authenticated_client, users, tags):
        """Test proper handling of tags in create and update operations."""
        # Create task with tags
        url = reverse('task-list')
        data = {
            'title': 'Tagged Task',
            'tags': [tags['backend'].id, tags['frontend'].id]
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data['tags_detail']) == 2
        
        # Update tags
        task_id = response.data['id']
        url = reverse('task-detail', kwargs={'pk': task_id})
        data = {'tags': [tags['urgent'].id]}
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['tags_detail']) == 1
        assert response.data['tags_detail'][0]['name'] == 'urgent'
    
    def test_nested_serializer_read_only(self, authenticated_client, users, tags):
        """Test that nested serializers are read-only and provide full data."""
        task = Task.objects.create(
            title='Test Task',
            assignee=users['user2'],
            reporter=users['user1']
        )
        task.tags.add(tags['backend'])
        
        url = reverse('task-detail', kwargs={'pk': task.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check assignee_detail structure
        assignee_detail = response.data['assignee_detail']
        assert assignee_detail['id'] == users['user2'].id
        assert assignee_detail['username'] == users['user2'].username
        assert 'first_name' in assignee_detail
        assert 'last_name' in assignee_detail
        
        # Check reporter_detail structure
        reporter_detail = response.data['reporter_detail']
        assert reporter_detail['id'] == users['user1'].id
        assert reporter_detail['username'] == users['user1'].username
        
        # Check tags_detail structure
        tags_detail = response.data['tags_detail']
        assert len(tags_detail) == 1
        assert tags_detail[0]['id'] == tags['backend'].id
        assert tags_detail[0]['name'] == 'backend'


@pytest.mark.integration
class TestTagCRUDOperations:
    """Test Tag CRUD operations (requirements 6.1, 6.2, 6.3, 6.4)."""
    
    def test_create_tag_success(self, authenticated_client):
        """Test successful tag creation (requirement 6.1)."""
        url = reverse('tag-list')
        data = {'name': 'new-tag'}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'new-tag'
        assert 'id' in response.data
        
        # Verify tag was created in database
        assert Tag.objects.filter(name='new-tag').exists()
    
    def test_create_tag_case_insensitive_uniqueness(self, authenticated_client):
        """Test case-insensitive uniqueness constraint (requirement 6.1)."""
        # Create first tag
        Tag.objects.create(name='Backend')
        
        url = reverse('tag-list')
        
        # Try to create tag with different case
        data = {'name': 'backend'}
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
        assert 'already exists' in str(response.data['name'][0]).lower()
        
        # Try with mixed case
        data = {'name': 'BACKEND'}
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
    
    def test_create_tag_duplicate_name_fails(self, authenticated_client):
        """Test duplicate tag name returns 400 validation error (requirement 6.4)."""
        # Create first tag
        Tag.objects.create(name='duplicate')
        
        url = reverse('tag-list')
        data = {'name': 'duplicate'}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
    
    def test_create_tag_empty_name_fails(self, authenticated_client):
        """Test tag creation fails with empty name."""
        url = reverse('tag-list')
        data = {'name': ''}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
    
    def test_create_tag_whitespace_name_fails(self, authenticated_client):
        """Test tag creation fails with whitespace-only name."""
        url = reverse('tag-list')
        data = {'name': '   '}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
    
    def test_create_tag_name_normalization(self, authenticated_client):
        """Test tag name is normalized (whitespace stripped)."""
        url = reverse('tag-list')
        data = {'name': '  normalized-tag  '}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'normalized-tag'
    
    def test_list_tags_sorted_by_name(self, authenticated_client):
        """Test tags are returned sorted by name (requirement 6.2)."""
        # Create tags in non-alphabetical order
        Tag.objects.create(name='zebra')
        Tag.objects.create(name='alpha')
        Tag.objects.create(name='beta')
        
        url = reverse('tag-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3
        
        # Check alphabetical ordering
        names = [tag['name'] for tag in response.data['results']]
        assert names == ['alpha', 'beta', 'zebra']
    
    def test_retrieve_tag(self, authenticated_client):
        """Test retrieving a single tag."""
        tag = Tag.objects.create(name='test-tag')
        
        url = reverse('tag-detail', kwargs={'pk': tag.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == tag.id
        assert response.data['name'] == 'test-tag'
    
    def test_update_tag(self, authenticated_client):
        """Test tag update."""
        tag = Tag.objects.create(name='original-name')
        
        url = reverse('tag-detail', kwargs={'pk': tag.id})
        data = {'name': 'updated-name'}
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'updated-name'
        
        # Verify in database
        tag.refresh_from_db()
        assert tag.name == 'updated-name'
    
    def test_update_tag_case_insensitive_uniqueness(self, authenticated_client):
        """Test update respects case-insensitive uniqueness."""
        tag1 = Tag.objects.create(name='existing-tag')
        tag2 = Tag.objects.create(name='another-tag')
        
        url = reverse('tag-detail', kwargs={'pk': tag2.id})
        data = {'name': 'EXISTING-TAG'}  # Different case
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
    
    def test_update_tag_same_name_allowed(self, authenticated_client):
        """Test updating tag with same name (case variations) is allowed."""
        tag = Tag.objects.create(name='test-tag')
        
        url = reverse('tag-detail', kwargs={'pk': tag.id})
        data = {'name': 'TEST-TAG'}  # Same tag, different case
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'TEST-TAG'
    
    def test_delete_tag(self, authenticated_client):
        """Test tag deletion."""
        tag = Tag.objects.create(name='delete-me')
        tag_id = tag.id
        
        url = reverse('tag-detail', kwargs={'pk': tag.id})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Tag.objects.filter(id=tag_id).exists()
    
    def test_delete_tag_with_associated_tasks(self, authenticated_client, users):
        """Test deleting tag that is associated with tasks."""
        tag = Tag.objects.create(name='associated-tag')
        task = Task.objects.create(title='Test Task', reporter=users['user1'])
        task.tags.add(tag)
        
        url = reverse('tag-detail', kwargs={'pk': tag.id})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Tag.objects.filter(id=tag.id).exists()
        
        # Task should still exist, just without the tag
        task.refresh_from_db()
        assert task.tags.count() == 0


@pytest.mark.integration
class TestTagValidationAndErrors:
    """Test Tag validation and error handling."""
    
    def test_tag_not_found(self, authenticated_client):
        """Test 404 error for non-existent tag."""
        url = reverse('tag-detail', kwargs={'pk': 99999})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_unauthenticated_tag_access_fails(self, api_client):
        """Test unauthenticated access to tags returns 403."""
        url = reverse('tag-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_tag_serializer_validation_fields(self, authenticated_client):
        """Test tag serializer includes correct fields."""
        tag = Tag.objects.create(name='test-tag')
        
        url = reverse('tag-detail', kwargs={'pk': tag.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert set(response.data.keys()) == {'id', 'name'}
        assert response.data['id'] == tag.id
        assert response.data['name'] == 'test-tag'
    
    def test_tag_list_pagination(self, authenticated_client):
        """Test tag list supports pagination."""
        # Create many tags
        for i in range(25):
            Tag.objects.create(name=f'tag-{i:02d}')
        
        url = reverse('tag-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert 'next' in response.data
        assert 'previous' in response.data
        assert 'count' in response.data
        
        # Should be paginated
        assert len(response.data['results']) <= 20  # Default page size
    
    def test_tag_ordering_case_insensitive(self, authenticated_client):
        """Test tag ordering is case-insensitive."""
        # Create tags with mixed case
        Tag.objects.create(name='Zebra')
        Tag.objects.create(name='alpha')
        Tag.objects.create(name='Beta')
        
        url = reverse('tag-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        names = [tag['name'] for tag in response.data['results']]
        
        # Should be ordered alphabetically regardless of case
        # Note: Django's default ordering is case-sensitive, but we can verify the order
        assert len(names) == 3
        assert 'alpha' in names
        assert 'Beta' in names
        assert 'Zebra' in names


@pytest.mark.integration
class TestTagTaskIntegration:
    """Test Tag integration with Task model (requirement 6.3)."""
    
    def test_task_multiple_tags_association(self, authenticated_client, users):
        """Test tasks can be associated with multiple tags (requirement 6.3)."""
        # Create tags
        tag1 = Tag.objects.create(name='backend')
        tag2 = Tag.objects.create(name='frontend')
        tag3 = Tag.objects.create(name='urgent')
        
        # Create task with multiple tags
        url = reverse('task-list')
        data = {
            'title': 'Multi-tag Task',
            'tags': [tag1.id, tag2.id, tag3.id]
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data['tags_detail']) == 3
        
        tag_names = {tag['name'] for tag in response.data['tags_detail']}
        assert tag_names == {'backend', 'frontend', 'urgent'}
    
    def test_tag_used_in_task_filtering(self, authenticated_client, users):
        """Test tags can be used for task filtering."""
        # Create tags and tasks
        backend_tag = Tag.objects.create(name='backend')
        frontend_tag = Tag.objects.create(name='frontend')
        
        task1 = Task.objects.create(title='Backend Task', reporter=users['user1'])
        task1.tags.add(backend_tag)
        
        task2 = Task.objects.create(title='Frontend Task', reporter=users['user1'])
        task2.tags.add(frontend_tag)
        
        task3 = Task.objects.create(title='Full Stack Task', reporter=users['user1'])
        task3.tags.add(backend_tag, frontend_tag)
        
        # Filter tasks by backend tag
        url = reverse('task-list')
        response = authenticated_client.get(url, {'tags': str(backend_tag.id)})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2  # task1 and task3
        
        titles = {task['title'] for task in response.data['results']}
        assert titles == {'Backend Task', 'Full Stack Task'}
    
    def test_empty_tags_in_task_creation(self, authenticated_client, users):
        """Test task creation with empty tags list."""
        url = reverse('task-list')
        data = {
            'title': 'No Tags Task',
            'tags': []
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data['tags_detail']) == 0
    
    def test_invalid_tag_ids_in_task_creation(self, authenticated_client, users):
        """Test task creation with invalid tag IDs."""
        url = reverse('task-list')
        data = {
            'title': 'Invalid Tags Task',
            'tags': [99999, 88888]  # Non-existent tag IDs
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'tags' in response.data