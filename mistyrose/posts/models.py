import uuid
from django.db import models
import uuid
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# Create your models here.
class Post(models.Model):
    VISIBILITY_CHOICES = [
      ('FRIENDS', 'Friends Only'),
      ('PUBLIC', 'Public'),
      ('UNLISTED', 'Unlisted'),
    ]
    
    CONTENT_TYPE_CHOICES = [
      ('text/plain', 'Plain Text'),
      ('text/markdown', 'Markdown'),
      ('image', 'Image'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author_id = models.ForeignKey('users.Author', on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    plain_or_markdown_content = models.TextField(blank=True, null=True)
    image_content = models.ImageField(upload_to='images/', blank=True, null=True)
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPE_CHOICES, default='text/plain')
    published = models.DateTimeField(auto_now_add=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='PUBLIC')

    # generic relation for reverse lookup for 'Like' objects on the post - because we are using generic foreign key in the like
    likes = GenericRelation('Like')

    def __str__(self):
        return self.title
      
    class Meta:
        ordering = ['-published']
      
class Like(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author_id = models.ForeignKey('users.Author', on_delete=models.CASCADE, related_name='likes') 
    published = models.DateTimeField(null=True, auto_now_add=True)
    object_url = models.URLField(null=True, blank=True)  # can be a URL to a post or comment

    # generic foreign key to attach like to Post or Comment
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE) 
    object_id = models.UUIDField(max_length=200) # for storing primary key value of the model itll be relating to
    content_object = GenericForeignKey('content_type', 'object_id') # foreign key to a Comment or Post

    def __str__(self):
      return f'{self.author_id} like'
    
class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author_id = models.ForeignKey('users.Author', on_delete=models.CASCADE, related_name='comments') 
    published = models.DateTimeField(auto_now_add=True)
    comment = models.TextField()
    post_id = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content_type = models.CharField(max_length=50, blank=True, null=True)
    page = models.URLField(blank=True, null=True)

    # generic relation for reverse lookup for 'Like' objects on the post - because we are using generic foreign key in the like
    likes = GenericRelation('Like')
    
    def __str__(self):
      return f'{self.author_id} commented on {self.post_id}'
    
    class Meta:
        ordering = ['-published']
    