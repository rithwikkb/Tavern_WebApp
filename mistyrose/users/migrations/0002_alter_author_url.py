# Generated by Django 5.1.2 on 2024-11-17 23:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='url',
            field=models.URLField(blank=True, editable=False, null=True, unique=True),
        ),
    ]
