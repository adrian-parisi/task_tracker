from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Custom user model extending AbstractUser.
    Makes email required and provides foundation for future user management features.
    """
    email = models.EmailField(
        unique=True,
        help_text='Required. Enter a valid email address.'
    )
    
    # Override email field to make it required
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        db_table = 'auth_user'  # Keep same table name for easier migration
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    @property
    def display_name(self):
        """
        Return display name as 'First Last' if available, otherwise username.
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username
    
    def __str__(self):
        return self.display_name