# Generated by Django 5.1.2 on 2024-11-23 01:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('node', '0005_alter_node_remote_node_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='node',
            name='remote_node_url',
            field=models.URLField(default='http://example.com/node/a20bc7ba-38da-4f39-93d8-a3ea54e452f9', primary_key=True, serialize=False),
        ),
    ]
