# Generated by Django 5.1.2 on 2024-11-23 01:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('node', '0004_alter_node_remote_node_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='node',
            name='remote_node_url',
            field=models.URLField(default='http://example.com/node/ef5e0e1c-040b-4986-84b3-e84cb0a2ace2', primary_key=True, serialize=False),
        ),
    ]
