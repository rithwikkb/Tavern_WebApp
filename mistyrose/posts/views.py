from django.shortcuts import render
from users.models import Author
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from .models import Post, Comment, Like
from stream.models import Inbox
from .serializers import PostSerializer, CommentSerializer, LikeSerializer
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from .models import Post
from users.models import Author, Follows  


#region Post Views
class PostDetailsView(APIView):
    """
    Retrieve, update or delete a post instance by author ID & post ID.
    """
    # permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request, author_serial, post_serial):
        try:
            post = Post.objects.get(id=post_serial, author_id=author_serial)
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        serializer = PostSerializer(post)
        return Response(serializer.data)
      
    def put(self, request, author_serial, post_serial):
        try:
            post = Post.objects.get(id=post_serial, author_id=author_serial)
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        print("request data:", request.data)  # Log the request data
        serializer = PostSerializer(post, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

      
    def delete(self, request, author_serial, post_serial):
        try:
            post = Post.objects.get(id=post_serial, author_id=author_serial)
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
      
class PostDetailsByFqidView(APIView):
    """
    Retrieve post by Fully Qualified ID (URL + ID).
    """
    # permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request, fqid):
        try:
            post = Post.objects.get(id=fqid)
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        serializer = PostSerializer(post)
        return Response(serializer.data)

class AuthorPostsView(APIView):
    """
    List all posts by an author, or create a new post for the author.
    """

    def get(self, request, author_serial):
        posts = Post.objects.filter(author_id=author_serial)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    def post(self, request, author_serial):
        try:
            author = Author.objects.get(id=author_serial)
        except Author.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author_id=author)  # Associate the post with the author
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

      
class PostImageView(APIView):
    """
    Retrieve the image of a post if available.
    """
    # permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, author_serial, post_serial):
        try:
            
            author = Author.objects.get(id=author_serial)
            post = Post.objects.get(author_id=author, id=post_serial)
        except Author.DoesNotExist:
            return Response({"detail": f"Author {author_serial} not found."}, status=status.HTTP_404_NOT_FOUND)
        except Post.DoesNotExist:
            return Response({"detail": f"Post {post_serial} not found for {author}"}, status=status.HTTP_404_NOT_FOUND)

        if post.image_content:
            image_url = request.build_absolute_uri(post.image_content.url)
            return Response({'image_url': image_url})
        else:
            return Response({'detail': 'No image available for this post'}, status=status.HTTP_404_NOT_FOUND)
#endregion

#region Comment Views
class CommentedView(APIView):
    """
    get, comment on post
    """
    def post(self, request, author_serial):
        """
        Comment on a post
        """
        #author who created the comment
        author = get_object_or_404(Author, id=author_serial)
       
        comment_data = request.data
        request_type = comment_data.get('type')

        if request_type != 'comment':
            return Response({"detail: Must be 'comment' type"}, status=status.HTTP_400_BAD_REQUEST)
        
        post_url = comment_data.get("post")
        if not post_url:
            return Response({"Error": "Post URL is required."}, status=status.HTTP_400_BAD_REQUEST)

        post_id = post_url.rstrip('/').split("/posts/")[-1]
        post = get_object_or_404(Post, id=post_id)

        #creating the comment object
        request.data['author_id'] = author_serial
        request.data['post_id'] = post_id
        comment_serializer = CommentSerializer(data=request.data)
        if comment_serializer.is_valid():
            comment_instance = comment_serializer.save()

            #creating Inbox object to forward to correct inbox
            post_host = post_url.split("//")[1].split("/")[0]
            if post_host != request.get_host():
                # TODO: post not on our host, need to forward it to a remote inbox
                pass
            else:
                # create and add to Inbox of the post's author
                post_author = post.author_id
                content_type = ContentType.objects.get_for_model(Comment)

                Inbox.objects.create(
                    type="comment",
                    author=post_author,
                    content_type=content_type,
                    object_id=comment_instance.id,
                    content_object=comment_instance,
                )

            return Response(comment_serializer.data, status=status.HTTP_201_CREATED)   
        else:
            return Response(comment_serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
        
    def get(self, request, author_serial, post_id):
        """ 
        Get comments on a post
        """
        post = get_object_or_404(Post, id=post_id) # not filtering by author so anyone can see it.... is that right? TODO: clarify

        comments = post.comments.all()
        serializer = CommentSerializer(comments, many=True) # many=True specifies that input is not just a single comment
        return Response(serializer.data)
    #TODO: return "type": "comments" format as specified in the project description, right now just returning a list of comments for ease
           


    
    
class LikedView(APIView):
    #TODO: ASK IF WE ARE SUPPOSED TO BE ABLE TO UNLIKE A POST
    """
    get or like a post
    """
    def post(self, request, author_serial):
        #author who created the like
        author = get_object_or_404(Author, id=author_serial)
       
        like_data = request.data
        request_type = like_data.get('type')

        if request_type != 'like':
            return Response({"detail: Must be 'like' type"}, status=status.HTTP_400_BAD_REQUEST)
        
        object_url = like_data.get("object") #object can be either a comment or post
        if not object_url:
            return Response({"Error": "object URL is required."}, status=status.HTTP_400_BAD_REQUEST)

        # determine like was for post or comment
        if "/posts/" in object_url:
            # object is a post
            object_id = object_url.rstrip('/').split("/posts/")[-1]
            liked_object = get_object_or_404(Post, id=object_id)
            object_content_type = ContentType.objects.get_for_model(Post)
        elif "/commented/" in object_url:
            # object is a comment
            object_id = object_url.rstrip('/').split("/commented/")[-1]
            liked_object = get_object_or_404(Comment, id=object_id)
            object_content_type = ContentType.objects.get_for_model(Comment)
        else:
            return Response({"detail": "Invalid object URL format."}, status=status.HTTP_400_BAD_REQUEST)

        #creating the like object
        request.data['author_id'] = author_serial
        request.data['object_id'] = liked_object.id
        request.data['content_type'] = object_content_type.id

        like_serializer = LikeSerializer(data=request.data)
        if like_serializer.is_valid():
            like_instance = like_serializer.save()

            #creating Inbox object to forward to correct inbox
            post_host = object_url.split("//")[1].split("/")[0]
            if post_host != request.get_host():
                # TODO: post or comment not on our host, need to forward it to a remote inbox
                pass
            else:
                # create and add to Inbox of the post or comment's author
                object_author = liked_object.author_id
                content_type = ContentType.objects.get_for_model(Like)

                Inbox.objects.create(
                    type="like",
                    author=object_author,
                    content_type=content_type,
                    object_id=like_instance.id,
                    content_object=like_instance,
                )

            return Response(like_serializer.data, status=status.HTTP_201_CREATED)   
        else:
            return Response(like_serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
        
    def get(self, request, author_serial, post_id):
        """
        Get likes on a post
        """
        post = get_object_or_404(Post, id=post_id)

        likes = post.likes.all()
        serializer = LikeSerializer(likes, many=True) # many=True specifies that input is not just a single like
        return Response(serializer.data)
        #TODO: return "type": "likes" format as specified in the project description, right now just returning a list of likes for ease


   
class PublicPostsView(APIView):
    # To view all of the public posts in the home page
    permission_classes = [IsAuthenticatedOrReadOnly] 

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_403_FORBIDDEN)

        current_author = get_object_or_404(Author, user=request.user)

        posts = Post.objects.exclude(author_id=current_author.id)

        serializer = PostSerializer(posts, many=True)

        all_authors = list(Author.objects.exclude(id=current_author.id).values_list('id', flat=True))

        authorized_authors_per_post = []

        for post_data in serializer.data:
            post_visibility = post_data.get('visibility')
            authorized_authors = set()

            if post_visibility == 'PUBLIC':
                authorized_authors.update(all_authors)

            elif post_visibility == 'UNLISTED':
                followers = Follows.objects.filter(
                    followed_id=current_author,
                    status='ACCEPTED'
                ).select_related('local_follower_id')
                followers_data = [follower.local_follower_id.id for follower in followers]
                authorized_authors.update(followers_data)

            elif post_visibility == 'FRIENDS':
                following_ids = Follows.objects.filter(local_follower_id=current_author, status='ACCEPTED').values_list('followed_id', flat=True)
                followers_ids = Follows.objects.filter(followed_id=current_author, status='ACCEPTED').values_list('local_follower_id', flat=True)

                mutual_friend_ids = set(following_ids).intersection(set(followers_ids))
                friends = Author.objects.filter(id__in=mutual_friend_ids)
                friends_data = [friend.id for friend in friends]
                authorized_authors.update(friends_data)

            # Include visibility_type in the authorized_authors_per_post dictionary
            authorized_authors_per_post.append({
                'post_id': post_data['id'], 
                'authorized_authors': list(authorized_authors),
                'visibility_type': post_visibility  # Add visibility_type here
            })

        # Create response data with posts and their respective authorized authors
        response_data = {
            'posts': serializer.data,  
            'authorized_authors_per_post': authorized_authors_per_post
        }
        return Response(response_data, status=status.HTTP_200_OK)
