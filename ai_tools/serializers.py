from rest_framework import serializers


class SmartEstimateResponseSerializer(serializers.Serializer):
    """Serializer for smart estimate response."""
    suggested_points = serializers.IntegerField(help_text="Suggested estimate in points")
    confidence = serializers.FloatField(help_text="Confidence score between 0.0 and 1.0")
    similar_task_ids = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of similar task IDs used for estimation"
    )
    rationale = serializers.CharField(help_text="Human-readable explanation for the estimate")


class SmartRewriteResponseSerializer(serializers.Serializer):
    """Serializer for smart rewrite response."""
    title = serializers.CharField(help_text="Enhanced task title")
    user_story = serializers.CharField(help_text="User story format with acceptance criteria")


class SmartSummaryResponseSerializer(serializers.Serializer):
    """Serializer for smart summary response."""
    summary = serializers.CharField(help_text="Human-readable task summary")


class AIOperationResponseSerializer(serializers.Serializer):
    """Serializer for async AI operation response."""
    operation_id = serializers.UUIDField(help_text="Unique identifier for the AI operation")
    status = serializers.CharField(help_text="Current status of the operation")
    sse_url = serializers.URLField(help_text="Server-Sent Events URL for real-time updates")


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses."""
    error = serializers.CharField(help_text="Error message describing what went wrong")
