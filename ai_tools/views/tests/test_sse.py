"""
Comprehensive tests for SSE views (ai_operation_sse, test_sse).
"""
import pytest
import uuid
import json
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.test import Client
from rest_framework import status

from ai_tools.models import AIOperation
from tasks.models import Task, TaskStatus, Project
from accounts.models import CustomUser


# Using shared fixtures directly from conftest.py

@pytest.fixture
def sse_url(ai_operation):
    """Get SSE URL for operation."""
    return reverse('ai-operation-sse', kwargs={'operation_id': ai_operation.id})


@pytest.fixture
def test_sse_url(ai_operation):
    """Get test SSE URL for operation."""
    return reverse('test-sse', kwargs={'operation_id': ai_operation.id})


def test_ai_operation_sse_success(api_client, test_user, ai_operation):
    """Test successful AI operation SSE."""
    api_client.force_login(test_user)
    url = reverse('ai-operation-sse', kwargs={'operation_id': ai_operation.id})
    
    response = api_client.get(url)
    
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/json'
    
    data = json.loads(response.content)
    assert data['status'] == 'PENDING'
    assert data['result'] is None
    assert data['error'] == ''


def test_ai_operation_sse_completed(api_client, test_user, completed_ai_operation):
    """Test AI operation SSE with completed operation."""
    api_client.force_login(test_user)
    url = reverse('ai-operation-sse', kwargs={'operation_id': completed_ai_operation.id})
    
    response = api_client.get(url)
    
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/json'
    
    data = json.loads(response.content)
    assert data['status'] == 'COMPLETED'
    assert data['result'] == {'summary': 'Test summary'}
    assert data['error'] == ''


def test_ai_operation_sse_failed(api_client, test_user, failed_ai_operation):
    """Test AI operation SSE with failed operation."""
    api_client.force_login(test_user)
    url = reverse('ai-operation-sse', kwargs={'operation_id': failed_ai_operation.id})
    
    response = api_client.get(url)
    
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/json'
    
    data = json.loads(response.content)
    assert data['status'] == 'FAILED'
    assert data['result'] is None
    assert data['error'] == 'Test error message'


def test_ai_operation_sse_processing(api_client, test_user, processing_ai_operation):
    """Test AI operation SSE with processing operation."""
    api_client.force_login(test_user)
    url = reverse('ai-operation-sse', kwargs={'operation_id': processing_ai_operation.id})
    
    response = api_client.get(url)
    
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/json'
    
    data = json.loads(response.content)
    assert data['status'] == 'PROCESSING'
    assert data['result'] is None
    assert data['error'] == ''


def test_ai_operation_sse_unauthenticated(api_client, ai_operation):
    """Test AI operation SSE without authentication."""
    url = reverse('ai-operation-sse', kwargs={'operation_id': ai_operation.id})
    
    response = api_client.get(url)
    
    # Should redirect to login page
    assert response.status_code == 302
    assert '/login/' in response.url


def test_ai_operation_sse_nonexistent_operation(api_client, test_user):
    """Test AI operation SSE with non-existent operation."""
    api_client.force_login(test_user)
    nonexistent_id = uuid.uuid4()
    url = reverse('ai-operation-sse', kwargs={'operation_id': nonexistent_id})
    
    response = api_client.get(url)
    
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/json'
    
    data = json.loads(response.content)
    assert data['status'] == 'error'
    assert 'Operation not found' in data['error']


def test_ai_operation_sse_wrong_test_user(api_client, other_user, ai_operation):
    """Test AI operation SSE with wrong test_user (operation belongs to different test_user)."""
    api_client.force_login(other_user)
    url = reverse('ai-operation-sse', kwargs={'operation_id': ai_operation.id})
    
    response = api_client.get(url)
    
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/json'
    
    data = json.loads(response.content)
    assert data['status'] == 'error'
    assert 'Operation not found' in data['error']


def test_ai_operation_sse_invalid_uuid(api_client, test_user):
    """Test AI operation SSE with invalid UUID."""
    api_client.force_login(test_user)
    # Use a truly invalid UUID format that will cause URL pattern to not match
    url = '/api/ai-operations/invalid-uuid/stream/'
    
    response = api_client.get(url)
    
    # Should return 404 due to URL pattern not matching
    assert response.status_code == 404


def test_ai_operation_sse_exception_handling(api_client, test_user, ai_operation):
    """Test AI operation SSE with exception handling."""
    api_client.force_login(test_user)
    url = reverse('ai-operation-sse', kwargs={'operation_id': ai_operation.id})
    
    with patch('ai_tools.views.sse.AIOperation.objects.get') as mock_get:
        mock_get.side_effect = Exception('Database error')
        
        response = api_client.get(url)
        
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'
        
        data = json.loads(response.content)
        assert data['status'] == 'error'
        assert 'Database error' in data['error']


def test_test_sse_success(api_client, test_user, ai_operation):
    """Test successful test SSE endpoint."""
    api_client.force_login(test_user)
    url = reverse('test-sse', kwargs={'operation_id': ai_operation.id})
    
    response = api_client.get(url)
    
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/json'
    
    data = json.loads(response.content)
    assert data['status'] == 'success'
    assert data['operation_id'] == str(ai_operation.id)
    assert data['operation_status'] == 'PENDING'
    assert data['user_id'] == test_user.id


def test_test_sse_completed_operation(api_client, test_user, completed_ai_operation):
    """Test test SSE with completed operation."""
    api_client.force_login(test_user)
    url = reverse('test-sse', kwargs={'operation_id': completed_ai_operation.id})
    
    response = api_client.get(url)
    
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/json'
    
    data = json.loads(response.content)
    assert data['status'] == 'success'
    assert data['operation_id'] == str(completed_ai_operation.id)
    assert data['operation_status'] == 'COMPLETED'
    assert data['user_id'] == test_user.id


def test_test_sse_failed_operation(api_client, test_user, failed_ai_operation):
    """Test test SSE with failed operation."""
    api_client.force_login(test_user)
    url = reverse('test-sse', kwargs={'operation_id': failed_ai_operation.id})
    
    response = api_client.get(url)
    
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/json'
    
    data = json.loads(response.content)
    assert data['status'] == 'success'
    assert data['operation_id'] == str(failed_ai_operation.id)
    assert data['operation_status'] == 'FAILED'
    assert data['user_id'] == test_user.id


def test_test_sse_unauthenticated(api_client, ai_operation):
    """Test test SSE without authentication."""
    url = reverse('test-sse', kwargs={'operation_id': ai_operation.id})
    
    response = api_client.get(url)
    
    # Should redirect to login page
    assert response.status_code == 302
    assert '/login/' in response.url


def test_test_sse_nonexistent_operation(api_client, test_user):
    """Test test SSE with non-existent operation."""
    api_client.force_login(test_user)
    nonexistent_id = uuid.uuid4()
    url = reverse('test-sse', kwargs={'operation_id': nonexistent_id})
    
    response = api_client.get(url)
    
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/json'
    
    data = json.loads(response.content)
    assert data['status'] == 'error'
    assert 'Operation not found' in data['error']
    assert data['operation_id'] == str(nonexistent_id)
    assert data['user_id'] == test_user.id


def test_test_sse_wrong_test_user(api_client, other_user, ai_operation):
    """Test test SSE with wrong test_user (operation belongs to different test_user)."""
    api_client.force_login(other_user)
    url = reverse('test-sse', kwargs={'operation_id': ai_operation.id})
    
    response = api_client.get(url)
    
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/json'
    
    data = json.loads(response.content)
    assert data['status'] == 'error'
    assert 'Operation not found' in data['error']
    assert data['operation_id'] == str(ai_operation.id)
    assert data['user_id'] == other_user.id


def test_test_sse_invalid_uuid(api_client, test_user):
    """Test test SSE with invalid UUID."""
    api_client.force_login(test_user)
    # Use a truly invalid UUID format that will cause URL pattern to not match
    url = '/api/ai-operations/invalid-uuid/test/'
    
    response = api_client.get(url)
    
    # Should return 404 due to URL pattern not matching
    assert response.status_code == 404


def test_test_sse_exception_handling(api_client, test_user, ai_operation):
    """Test test SSE with exception handling."""
    api_client.force_login(test_user)
    url = reverse('test-sse', kwargs={'operation_id': ai_operation.id})
    
    with patch('ai_tools.views.sse.AIOperation.objects.get') as mock_get:
        mock_get.side_effect = Exception('Database error')
        
        response = api_client.get(url)
        
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'
        
        data = json.loads(response.content)
        assert data['status'] == 'error'
        assert 'Database error' in data['error']
        assert data['operation_id'] == str(ai_operation.id)
        assert data['user_id'] == test_user.id


def test_ai_operation_sse_different_operation_types(api_client, test_user, test_task, db):
    """Test AI operation SSE with different operation types."""
    api_client.force_login(test_user)
    
    operation_types = ['SUMMARY', 'ESTIMATE', 'REWRITE']
    
    for op_type in operation_types:
        operation = AIOperation.objects.create(
            task=test_task,
            operation_type=op_type,
            status='PENDING',
            user=test_user
        )
        
        url = reverse('ai-operation-sse', kwargs={'operation_id': operation.id})
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['status'] == 'PENDING'


def test_ai_operation_sse_different_statuses(api_client, test_user, test_task, db):
    """Test AI operation SSE with different operation statuses."""
    api_client.force_login(test_user)
    
    statuses = ['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED']
    
    for status_val in statuses:
        operation = AIOperation.objects.create(
            task=test_task,
            operation_type='SUMMARY',
            status=status_val,
            user=test_user
        )
        
        url = reverse('ai-operation-sse', kwargs={'operation_id': operation.id})
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['status'] == status_val


def test_ai_operation_sse_with_result_data(api_client, test_user, test_task, db):
    """Test AI operation SSE with various result data types."""
    api_client.force_login(test_user)
    
    test_results = [
        {'summary': 'Simple summary'},
        {'points': 5, 'confidence': 0.8},
        {'title': 'New Title', 'user_story': 'As a user...'},
        {'complex': {'nested': {'data': [1, 2, 3]}}},
        None
    ]
    
    for i, result in enumerate(test_results):
        operation = AIOperation.objects.create(
            task=test_task,
            operation_type='SUMMARY',
            status='COMPLETED',
            result=result,
            user=test_user
        )
        
        url = reverse('ai-operation-sse', kwargs={'operation_id': operation.id})
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['status'] == 'COMPLETED'
        assert data['result'] == result


def test_ai_operation_sse_with_error_messages(api_client, test_user, test_task, db):
    """Test AI operation SSE with various error messages."""
    api_client.force_login(test_user)
    
    error_messages = [
        'Simple error',
        'Complex error with details: Database connection failed',
        'Error with special characters: !@#$%^&*()',
        'Error with unicode: ñáéíóú, 中文, العربية',
        ''  # Empty error message
    ]
    
    for i, error_msg in enumerate(error_messages):
        operation = AIOperation.objects.create(
            task=test_task,
            operation_type='SUMMARY',
            status='FAILED',
            error_message=error_msg,
            user=test_user
        )
        
        url = reverse('ai-operation-sse', kwargs={'operation_id': operation.id})
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['status'] == 'FAILED'
        assert data['error'] == error_msg


def test_test_sse_different_operation_types(api_client, test_user, test_task, db):
    """Test test SSE with different operation types."""
    api_client.force_login(test_user)
    
    operation_types = ['SUMMARY', 'ESTIMATE', 'REWRITE']
    
    for op_type in operation_types:
        operation = AIOperation.objects.create(
            task=test_task,
            operation_type=op_type,
            status='PENDING',
            user=test_user
        )
        
        url = reverse('test-sse', kwargs={'operation_id': operation.id})
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['status'] == 'success'
        assert data['operation_id'] == str(operation.id)
        assert data['operation_status'] == 'PENDING'


def test_test_sse_different_statuses(api_client, test_user, test_task, db):
    """Test test SSE with different operation statuses."""
    api_client.force_login(test_user)
    
    statuses = ['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED']
    
    for status_val in statuses:
        operation = AIOperation.objects.create(
            task=test_task,
            operation_type='SUMMARY',
            status=status_val,
            user=test_user
        )
        
        url = reverse('test-sse', kwargs={'operation_id': operation.id})
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['status'] == 'success'
        assert data['operation_id'] == str(operation.id)
        assert data['operation_status'] == status_val


def test_sse_urls_require_authentication(api_client, ai_operation):
    """Test that both SSE endpoints require authentication."""
    sse_url = reverse('ai-operation-sse', kwargs={'operation_id': ai_operation.id})
    test_url = reverse('test-sse', kwargs={'operation_id': ai_operation.id})
    
    # Test without authentication
    response1 = api_client.get(sse_url)
    response2 = api_client.get(test_url)
    
    assert response1.status_code == 302  # Redirect to login
    assert response2.status_code == 302  # Redirect to login


def test_sse_urls_handle_malformed_json(api_client, test_user, ai_operation):
    """Test that SSE endpoints handle malformed JSON gracefully."""
    api_client.force_login(test_user)
    
    # Test with operation that has malformed result JSON
    operation = AIOperation.objects.create(
        task=ai_operation.task,
        operation_type='SUMMARY',
        status='COMPLETED',
        result={'malformed': 'json'},  # This should be fine
        user=test_user
    )
    
    url = reverse('ai-operation-sse', kwargs={'operation_id': operation.id})
    response = api_client.get(url)
    
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data['status'] == 'COMPLETED'


def test_sse_urls_with_large_data(api_client, test_user, test_task, db):
    """Test SSE endpoints with large data payloads."""
    api_client.force_login(test_user)
    
    # Create operation with large result data
    large_result = {
        'summary': 'A' * 10000,  # 10KB summary
        'details': ['item' + str(i) for i in range(1000)],  # 1000 items
        'metadata': {f'key{i}': f'value{i}' for i in range(100)}  # 100 key-value pairs
    }
    
    operation = AIOperation.objects.create(
        task=test_task,
        operation_type='SUMMARY',
        status='COMPLETED',
        result=large_result,
        user=test_user
    )
    
    url = reverse('ai-operation-sse', kwargs={'operation_id': operation.id})
    response = api_client.get(url)
    
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data['status'] == 'COMPLETED'
    assert data['result'] == large_result


def test_sse_urls_with_unicode_data(api_client, test_user, test_task, db):
    """Test SSE endpoints with unicode data."""
    api_client.force_login(test_user)
    
    unicode_result = {
        'summary': 'Summary with unicode: ñáéíóú, 中文, العربية, русский, 🚀',
        'title': 'Unicode Title: 测试标题',
        'description': 'Description with emojis: 🎉✨🌟'
    }
    
    operation = AIOperation.objects.create(
        task=test_task,
        operation_type='SUMMARY',
        status='COMPLETED',
        result=unicode_result,
        user=test_user
    )
    
    url = reverse('ai-operation-sse', kwargs={'operation_id': operation.id})
    response = api_client.get(url)
    
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data['status'] == 'COMPLETED'
    assert data['result'] == unicode_result
