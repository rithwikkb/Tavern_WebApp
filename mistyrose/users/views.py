from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, generics
from .models import Author
from .serializers import AuthorSerializer, AuthorEditProfileSerializer
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework.reverse import reverse
from .models import Author, Follows
from django.utils import timezone
from django.conf import settings
import uuid
from stream.models import Inbox
from django.contrib.contenttypes.models import ContentType
from urllib.parse import unquote
from posts.models import Post
from .serializers import PostSerializer

DEFAULT_PROFILE_PIC = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png"

def create_author(author_data, request, user):
    author_id = author_data.get('id', uuid.uuid4())
    host = request.build_absolute_uri('/')[:-1]  
    page_url = reverse('author-detail', kwargs={'pk': author_id}, request=request)
    author = Author.objects.create(
        id=author_id,
        host=host,
        display_name=author_data['displayName'],
        profile_image=author_data.get('profileImage', DEFAULT_PROFILE_PIC),
        page=page_url,
        github=author_data.get('github', ''),
        user=user
    )
    return author

class LoginView(APIView):
    http_method_names = ["post"]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            return Response({"message": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(username=username)
            if user.is_active:
                if user.check_password(password):
                    user.last_login = timezone.now()
                    user.save()
                    token, created = Token.objects.get_or_create(user=user)
                    author = user.author  
                    serializer = AuthorSerializer(author, context={"request": request})
                    data = {"token": token.key, "author": serializer.data}
                    return Response(data, status=status.HTTP_200_OK)
                else:
                    return Response({"message": "Wrong password."}, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({"message": "User is not activated yet."}, status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

class SignUpView(APIView):
    http_method_names = ["post"]

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")
        display_name = request.data.get("displayName")
        github = request.data.get("github", "")
        profile_image = request.data.get("profileImage", DEFAULT_PROFILE_PIC)
        
        if not all([username, email, password, display_name]):
            return Response({"message": "Username, email, password, and displayName are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({"message": "Username already exists."}, status=status.HTTP_409_CONFLICT)
        
        try:
            with transaction.atomic():
                user = User.objects.create_user(username=username, email=email, password=password, is_active=False)
                user.date_joined = timezone.now()
                user.save()
                author_data = {"displayName": display_name, "profileImage": profile_image, "github": github}
                author = create_author(author_data, request, user)
                serializer = AuthorSerializer(author, context={"request": request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = Token.objects.get(user=request.user)
            token.delete()
            return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
        except Token.DoesNotExist:
            return Response({"message": "User is already logged out."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AuthorDetailView(generics.RetrieveAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    lookup_field = 'pk'

class AuthorProfileView(APIView):
    def get(self, request, pk):
        author = get_object_or_404(Author, pk=pk)
        friends_count = Follows.objects.filter(local_follower_id=author, status='ACCEPTED').count()
        followers_count = Follows.objects.filter(followed_id=author, status='ACCEPTED').count()
        following_count = Follows.objects.filter(local_follower_id=author, status='ACCEPTED').count()
        public_posts = Post.objects.filter(author_id=author, visibility='PUBLIC').order_by('-published')
        author_serializer = AuthorSerializer(author)
        post_serializer = PostSerializer(public_posts, many=True)
        data = author_serializer.data
        data['friends_count'] = friends_count
        data['followers_count'] = followers_count
        data['following_count'] = following_count
        data['public_posts'] = post_serializer.data
        return Response(data)

class AuthorEditProfileView(APIView):
    def get(self, request, pk):
        author = get_object_or_404(Author, pk=pk)
        serializer = AuthorEditProfileSerializer(author)
        return Response(serializer.data)

    def put(self, request, pk):
        author = get_object_or_404(Author, pk=pk)
        serializer = AuthorEditProfileSerializer(author, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FollowerView(APIView):
    
    def get(self, request, AUTHOR_SERIAL, FOREIGN_AUTHOR_FQID):
        """
        Check if FOREIGN_AUTHOR_FQID is a follower of AUTHOR_SERIAL
        """
        author = get_object_or_404(Author, id=AUTHOR_SERIAL)
        follower_url_decoded = unquote(FOREIGN_AUTHOR_FQID)

        # print(f"Decoded FOREIGN_AUTHOR_FQID: {follower_url_decoded}")
        # print(f"Author being followed: {author}")

        # Check follow status using the remote URL
        follow_status = Follows.objects.filter(remote_follower_url=follower_url_decoded, followed_id=author, status='ACCEPTED').exists()

        if follow_status:
            print("Follower exists")
            return Response({"status": "Follower exists"}, status=status.HTTP_200_OK)
        print("Follower not found")
        return Response({"error": "Follower not found"}, status=status.HTTP_404_NOT_FOUND)


    def put(self, request, AUTHOR_SERIAL, FOREIGN_AUTHOR_FQID):
        """
        Accept a follow request from FOREIGN_AUTHOR_FQID to AUTHOR_SERIAL
        """
        # Decode the foreign author URL
        foreign_author_fqid_decoded = unquote(FOREIGN_AUTHOR_FQID)
        author = get_object_or_404(Author, id=AUTHOR_SERIAL)

        # Get the content type for the Follows model
        content_type = ContentType.objects.get_for_model(Follows)
        inbox_entry = Inbox.objects.filter(author=author, object_id=foreign_author_fqid_decoded, content_type=content_type).first()

        if not inbox_entry:
            return Response({"error": "Follow request not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update the follow request status to "ACCEPTED"
        follow_request = inbox_entry.content_object
        follow_request.status = 'ACCEPTED'
        follow_request.save()

        # Optionally remove the entry from the inbox if it is handled
        inbox_entry.delete()

        return Response({"status": "Follow request accepted"}, status=status.HTTP_200_OK)

    def delete(self, request, AUTHOR_SERIAL, FOREIGN_AUTHOR_FQID):
        """
        Decline a follow request from FOREIGN_AUTHOR_FQID to AUTHOR_SERIAL
        """
        # Decode the foreign author URL
        foreign_author_fqid_decoded = unquote(FOREIGN_AUTHOR_FQID)
        author = get_object_or_404(Author, id=AUTHOR_SERIAL)

        # Get the content type for the Follows model
        content_type = ContentType.objects.get_for_model(Follows)
        inbox_entry = Inbox.objects.filter(author=author, object_id=foreign_author_fqid_decoded, content_type=content_type).first()

        if not inbox_entry:
            return Response({"error": "Follow request not found"}, status=status.HTTP_404_NOT_FOUND)

        # Delete the follow request and remove from inbox
        follow_request = inbox_entry.content_object
        follow_request.delete()
        inbox_entry.delete()

        return Response({"status": "Follow request denied"}, status=status.HTTP_204_NO_CONTENT)