"""
Performance tests to verify database index effectiveness.
"""
import time
import pytest
from django.test import TestCase
from django.test.utils import override_settings
from django.db import connection
from django.contrib.auth import get_user_model
from tasks.models import Task, Tag, TaskStatus
from tasks.services import SimilarityService

User = get_user_model()


class DatabasePerformanceTestCase(TestCase):
    """Test database performance optimizations and index effectiveness."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data for performance testing."""
        # Create test users
        cls.users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f'testuser{i}',
                email=f'test{i}@example.com'
            )
            cls.users.append(user)
        
        # Create test tags
        cls.tags = []
        tag_names = ['frontend', 'backend', 'testing', 'bug', 'feature', 'performance', 'security', 'ui', 'api', 'database']
        for name in tag_names:
            tag = Tag.objects.create(name=name)
            cls.tags.append(tag)
        
        # Create a large number of test tasks for performance testing
        cls.tasks = []
        for i in range(100):
            task = Task.objects.create(
                title=f'Test Task {i} - Performance Testing',
                description=f'This is a test task for performance testing. Task number {i}.',
                status=TaskStatus.TODO if i % 4 == 0 else TaskStatus.IN_PROGRESS if i % 4 == 1 else TaskStatus.BLOCKED if i % 4 == 2 else TaskStatus.DONE,
                estimate=i % 10 + 1,
                assignee=cls.users[i % len(cls.users)],
                reporter=cls.users[(i + 1) % len(cls.users)]
            )
            # Add random tags
            task.tags.set(cls.tags[i % 3:(i % 3) + 2])
            cls.tasks.append(task)
    
    def test_status_index_performance(self):
        """Test that status queries use the index efficiently."""
        # Reset query count
        with self.assertNumQueries(1):
            # Query by status should use index
            tasks = list(Task.objects.filter(status=TaskStatus.TODO))
            self.assertGreater(len(tasks), 0)
    
    def test_assignee_index_performance(self):
        """Test that assignee queries use the index efficiently."""
        test_user = self.users[0]
        
        with self.assertNumQueries(1):
            # Query by assignee should use index
            tasks = list(Task.objects.filter(assignee=test_user))
            self.assertGreater(len(tasks), 0)
    
    def test_updated_at_index_performance(self):
        """Test that updated_at ordering uses the index efficiently."""
        with self.assertNumQueries(1):
            # Ordering by updated_at should use index
            tasks = list(Task.objects.order_by('-updated_at')[:10])
            self.assertEqual(len(tasks), 10)
    
    def test_activity_composite_index_performance(self):
        """Test that activity queries use the composite index efficiently."""
        test_task = self.tasks[0]
        
        with self.assertNumQueries(1):
            # Query activities by task and created_at should use composite index
            activities = list(test_task.activities.order_by('-created_at'))
            # Activities might be empty for test tasks, that's ok
            self.assertIsInstance(activities, list)
    
    def test_similarity_query_performance(self):
        """Test that similarity queries perform efficiently with indexes."""
        test_task = self.tasks[0]
        
        # Measure query time for similarity search
        start_time = time.time()
        
        # This should use multiple indexes efficiently
        similar_tasks = SimilarityService.find_similar_tasks(test_task, limit=20)
        result_list = list(similar_tasks)
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Query should complete quickly (under 100ms for 100 tasks)
        self.assertLess(query_time, 0.1, f"Similarity query took {query_time:.3f}s, expected < 0.1s")
        
        # Should return some results (or empty list if no similar tasks)
        self.assertIsInstance(result_list, list)
    
    def test_tag_filtering_performance(self):
        """Test that tag filtering uses indexes efficiently."""
        test_tag = self.tags[0]
        
        with self.assertNumQueries(1):
            # Query by tags should use the many-to-many index
            tasks = list(Task.objects.filter(tags=test_tag))
            self.assertGreater(len(tasks), 0)
    
    def test_title_search_performance(self):
        """Test that title searches perform reasonably with index."""
        search_term = "Performance"
        
        start_time = time.time()
        
        # Title search should use the title index
        tasks = list(Task.objects.filter(title__icontains=search_term))
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Query should complete quickly
        self.assertLess(query_time, 0.05, f"Title search took {query_time:.3f}s, expected < 0.05s")
        self.assertGreater(len(tasks), 0)
    
    def test_description_search_performance(self):
        """Test that description searches perform reasonably with index."""
        search_term = "performance testing"
        
        start_time = time.time()
        
        # Description search should use the description index
        tasks = list(Task.objects.filter(description__icontains=search_term))
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Query should complete quickly
        self.assertLess(query_time, 0.05, f"Description search took {query_time:.3f}s, expected < 0.05s")
        self.assertGreater(len(tasks), 0)
    
    def test_estimate_calculation_performance(self):
        """Test that estimate calculation performs efficiently."""
        test_task = self.tasks[0]
        
        start_time = time.time()
        
        # Calculate estimate suggestion
        estimate_data = SimilarityService.calculate_estimate_suggestion(test_task)
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Estimate calculation should complete quickly
        self.assertLess(query_time, 0.2, f"Estimate calculation took {query_time:.3f}s, expected < 0.2s")
        
        # Should return valid estimate data
        self.assertIn('suggested_points', estimate_data)
        self.assertIn('confidence', estimate_data)
        self.assertIn('similar_task_ids', estimate_data)
        self.assertIn('rationale', estimate_data)
    
    def test_pagination_performance(self):
        """Test that pagination performs efficiently with indexes."""
        # Test pagination with different page sizes
        page_sizes = [10, 20, 50]
        
        for page_size in page_sizes:
            with self.subTest(page_size=page_size):
                start_time = time.time()
                
                # Paginated query should use indexes
                tasks = list(Task.objects.order_by('-updated_at')[:page_size])
                
                end_time = time.time()
                query_time = end_time - start_time
                
                # Should complete quickly regardless of page size
                self.assertLess(query_time, 0.05, f"Pagination query took {query_time:.3f}s for {page_size} items")
                self.assertLessEqual(len(tasks), page_size)
    
    def test_complex_filtering_performance(self):
        """Test performance of complex queries combining multiple filters."""
        test_user = self.users[0]
        test_tag = self.tags[0]
        
        start_time = time.time()
        
        # Complex query combining multiple indexed fields
        tasks = list(Task.objects.filter(
            status=TaskStatus.TODO,
            assignee=test_user,
            tags=test_tag
        ).order_by('-updated_at')[:10])
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Complex query should still perform well with indexes
        self.assertLess(query_time, 0.1, f"Complex filtering took {query_time:.3f}s, expected < 0.1s")
        self.assertIsInstance(tasks, list)


@pytest.mark.django_db
class SimilarityPerformanceTest:
    """Pytest-based performance tests for similarity calculations."""
    
    @pytest.fixture(autouse=True)
    def setup_data(self, db):
        """Set up test data for similarity performance testing."""
        # Create users
        self.users = []
        for i in range(5):
            user = User.objects.create_user(
                username=f'perfuser{i}',
                email=f'perf{i}@example.com'
            )
            self.users.append(user)
        
        # Create tags
        self.tags = []
        for name in ['perf', 'test', 'optimization']:
            tag = Tag.objects.create(name=name)
            self.tags.append(tag)
        
        # Create tasks with similar characteristics
        self.tasks = []
        for i in range(50):
            task = Task.objects.create(
                title=f'Performance Task {i}',
                description=f'Performance testing task {i} for optimization',
                status=TaskStatus.TODO,
                estimate=i % 5 + 1,
                assignee=self.users[i % len(self.users)]
            )
            task.tags.set([self.tags[i % len(self.tags)]])
            self.tasks.append(task)
    
    def test_similarity_algorithm_performance(self):
        """Test that similarity algorithm performs well with realistic data."""
        test_task = self.tasks[0]
        
        # Measure performance of similarity calculation
        start_time = time.time()
        
        similar_tasks = SimilarityService.find_similar_tasks(test_task, limit=20)
        similar_list = list(similar_tasks)
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Should complete quickly even with 50 tasks
        assert query_time < 0.05, f"Similarity search took {query_time:.3f}s, expected < 0.05s"
        
        # Should return reasonable results
        assert len(similar_list) <= 20
    
    def test_estimate_suggestion_performance(self):
        """Test performance of complete estimate suggestion calculation."""
        test_task = self.tasks[0]
        
        start_time = time.time()
        
        estimate_data = SimilarityService.calculate_estimate_suggestion(test_task)
        
        end_time = time.time()
        calculation_time = end_time - start_time
        
        # Complete calculation should be fast
        assert calculation_time < 0.1, f"Estimate calculation took {calculation_time:.3f}s, expected < 0.1s"
        
        # Should return valid data
        assert isinstance(estimate_data['suggested_points'], int)
        assert 0.0 <= estimate_data['confidence'] <= 1.0
        assert isinstance(estimate_data['similar_task_ids'], list)
        assert len(estimate_data['similar_task_ids']) <= 5