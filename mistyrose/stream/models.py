from django.db import models
import uuid
from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


# Create your models here.
class Inbox(models.Model):
    inbox_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey('users.Author', on_delete=models.CASCADE, related_name='author') #TODO: replace 'users.Author' with path to author
    created_at = models.DateTimeField("date requested", default=datetime.now)

    # using generic foreign key so we can have "polymorphic" relationships between the tables (Like, Comment, Follow, Post)
    # https://docs.djangoproject.com/en/5.1/ref/contrib/contenttypes/#generic-relations for setting up generic foreign key 2024-10-14
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE) 
    object_id = models.CharField(max_length=200) # for storing primary key value of the model itll be relating to
    content_object = GenericForeignKey() # foreign key to Like or Comment, or Follow or Post


