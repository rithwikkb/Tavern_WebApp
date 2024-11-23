# Generated by Django 5.1.2 on 2024-11-22 17:04

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Node',
            fields=[
                ('remote_node_url', models.URLField(default='http://example.com/node/eb1c738e-b0a7-4cdf-a425-b1ec2e13f7e3', primary_key=True, serialize=False)),
                ('remote_username', models.CharField(default='TavernToRemote', max_length=100)),
                ('remote_password', models.CharField(default='Tavern-->Remote', max_length=100)),
                ('local_username', models.CharField(default='RemoteToTavern', max_length=100)),
                ('local_password', models.CharField(default='Remote-->Tavern', max_length=100)),
                ('is_whitelisted', models.BooleanField(default=False)),
            ],
        ),
    ]
