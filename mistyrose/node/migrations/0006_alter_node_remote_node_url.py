# Generated by Django 5.1.2 on 2024-11-23 19:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('node', '0005_alter_node_remote_node_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='node',
            name='remote_node_url',
            field=models.URLField(default='http://example.com/node/678b7ee1-abd5-4ec9-aabd-5a12b9b504e8', primary_key=True, serialize=False),
        ),
    ]
