# Generated manually to remove Tag model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0007_auto_20250918_0054'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Tag',
        ),
    ]
