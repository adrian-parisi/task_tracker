from rest_framework.pagination import PageNumberPagination


class TaskPagination(PageNumberPagination):
    """
    Custom pagination for tasks with default 20 items per page, max 100.
    Requirement 4.4: Implement pagination with default 20 items, max 100
    Requirement 9.5: When pagination exceeds 100 items THEN the system SHALL cap results at 100 items
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100