from django.shortcuts import render
import os
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, generics
from .models import Author
from .serializers import AuthorSerializer, AuthorEditProfileSerializer, LoginSerializer
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView 
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework.reverse import reverse
from .models import Author, Follows
from django.utils import timezone
from django.conf import settings
import uuid
from stream.models import Inbox
from django.contrib.contenttypes.models import ContentType
from posts.models import Post
from django.middleware.csrf import get_token
from django.contrib.auth import authenticate
from .pagination import AuthorsPagination
from .serializers import PostSerializer
from uuid import UUID

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
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": "Invalid username or password"}, status=status.HTTP_400_BAD_REQUEST)
        
        username = serializer.validated_data.get("username")
        password = serializer.validated_data.get("password")
        
        user = authenticate(username=username, password=password)
        if user is None:
            return Response({"error": "Invalid username or password"}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({"error": "User account is not activated. Please contact an admin."}, status=status.HTTP_403_FORBIDDEN)
        
        author_id = Author.objects.get(user=user).id
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        response = Response({
            "author_id": author_id,
            "refresh_token": str(refresh),
            "access_token": access_token
        }, status=status.HTTP_200_OK)

        response.set_cookie(
            'author_id', 
            author_id, 
            httponly=True, 
            secure=False,  # Set this to True in production if using HTTPS
            samesite='None',
            path='/'
        )

        response.set_cookie(
            'access_token', 
            access_token, 
            httponly=True, 
            secure=False,  # Set this to True in production if using HTTPS
            samesite='None',
            path='/'
        )

        response.set_cookie(
            'refresh_token', 
            str(refresh), 
            httponly=True, 
            secure=False,  # Set this to True in production if using HTTPS
            samesite='None',
            path='/'
        )

        return response

    
    # http_method_names = ["post"]

    # def post(self, request):
    #     # Deserialize and validate input data
    #     serializer = LoginSerializer(data=request.data)
    #     if not serializer.is_valid():
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    #     username = serializer.validated_data.get("username")
    #     password = serializer.validated_data.get("password")
        
    #     try:
    #         user = User.objects.get(username=username)
    #         if user.is_active:
    #             if user.check_password(password):
    #                 user.last_login = timezone.now()
    #                 user.save()
                    
    #                 # Generate JWT tokens
    #                 refresh = RefreshToken.for_user(user)
    #                 access_token = str(refresh.access_token)

    #                 # Set cookies
    #                 response = Response({
    #                     "author_id": Author.objects.get(user=user).id,  # Assuming Author model exists
    #                 }, status=status.HTTP_200_OK)

    #                 response.set_cookie(
    #                     'access_token',
    #                     access_token,
    #                     httponly=True,
    #                     secure=True,  # Set to True in production
    #                     samesite='Lax',
    #                 )
    #                 response.set_cookie(
    #                     'refresh_token',
    #                     str(refresh),
    #                     httponly=True,
    #                     secure=True,  # Set to True in production
    #                     samesite='Lax',
    #                 )

    #                 return response
    #             else:
    #                 return Response({"message": "Wrong password."}, status=status.HTTP_401_UNAUTHORIZED)
    #         else:
    #             return Response({"message": "User is not activated yet."}, status=status.HTTP_403_FORBIDDEN)
    #     except User.DoesNotExist:
    #         return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    #     except Exception as e:
    #         return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class SignUpView(APIView):
    http_method_names = ["post"]
    permission_classes = [AllowAny]  # Allow any user to access this view
    
    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")
        display_name = request.data.get("displayName")
        github = request.data.get("github", "")
        profile_image = request.data.get("profileImage", DEFAULT_PROFILE_PIC)

        if not all([username, email, password, display_name]):
            return Response(
                {"message": "Username, email, password, and displayName are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(username=username).exists():
            return Response(
                {"message": "Username already exists."},
                status=status.HTTP_409_CONFLICT
            )
        
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_active=False  # user is inactive by default(admin must make it active)
                )
                user.date_joined = timezone.now()
                user.save()
                
                author_data = {
                    "displayName": display_name,
                    "profileImage": profile_image,
                    "github": github,
                }
                author = create_author(author_data, request, user)
                serializer = AuthorSerializer(author, context={"request": request})
                
                response=Response(serializer.data, status=status.HTTP_201_CREATED)
                return response
        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]  

    def post(self, request):
        try:
            request.user.tokens().blacklist()
            return Response(
                {"message": "Logged out successfully."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VerifyTokenView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            author = Author.objects.get(user=request.user)
            return Response({'authorId': str(author.id)}, status=200)
        except Author.DoesNotExist:
            return Response({'error': 'Author not found'}, status=404)

class AuthorDetailView(generics.RetrieveAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    lookup_field = 'pk'

class AuthorProfileView(APIView):
    def get(self, request, pk):
        author = get_object_or_404(Author, pk=pk)
        # Use the FriendsView logic to get friends data
        friends_view = FriendsView()
        friends_response = friends_view.get(request, author_id=pk)
        friends_data = friends_response.data.get('friends', [])

        # Calculate friends count based on the friends data returned
        friends_count = len(friends_data)
        followers_count = Follows.objects.filter(followed_id=author, status='ACCEPTED').count()
        following_count = Follows.objects.filter(local_follower_id=author, status='ACCEPTED').count()
        public_posts = Post.objects.filter(author_id=author, visibility='PUBLIC').order_by('-published')
        friends_posts = Post.objects.filter(author_id=author, visibility='FRIENDS').order_by('-published')
        unlisted_posts = Post.objects.filter(author_id=author, visibility='UNLISTED').order_by('-published')
        author_serializer = AuthorSerializer(author)
        # Serialize posts
        public_post_serializer = PostSerializer(public_posts, many=True)
        friends_post_serializer = PostSerializer(friends_posts, many=True)
        unlisted_post_serializer = PostSerializer(unlisted_posts, many=True)
        # Prepare the response data
        data = author_serializer.data
        data['friends_count'] = friends_count
        data['followers_count'] = followers_count
        data['following_count'] = following_count
        data['public_posts'] = public_post_serializer.data
        data['friends_posts'] = friends_post_serializer.data
        data['unlisted_posts'] = unlisted_post_serializer.data
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

class AuthorsView(ListAPIView): #used ListAPIView because this is used to handle a collection of model instances AND comes with pagination
    #asked chatGPT how to get the authors using ListAPIView 2024-10-18
    # variables that ListAPIView needs
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    pagination_class = AuthorsPagination
    def get(self, request, *args, **kwargs): #args and kwargs for the page and size 
        #retrieve all profiles on the node (paginated)
        response = super().get(request, *args, **kwargs) #get provided by ListAPIView that queries database, serializes, and handles pagination

        #customize structure of response
        response.data = {
        "type": "authors",  
        "authors": response.data['results']  
        }

        return response



class FollowerView(APIView):
    
    def get(self, request, author_id, follower_id):
        """
        Check if follower_id is a follower of author_id
        return 200 if following (accepted)
        return 202 if follow request pending (202 to indicate request is still in progress)
        return 404 if not following or requested
        """
        author = get_object_or_404(Author, id=author_id)

         # Check if the follow request is accepted
        is_accepted = Follows.objects.filter(
            local_follower_id=follower_id, followed_id=author, status='ACCEPTED'
        ).exists()

        # Check if there's a pending follow request
        is_pending = Follows.objects.filter(
            local_follower_id=follower_id, followed_id=author, status='PENDING'
        ).exists()

        if is_accepted:
            return Response({"status": "Following"}, status=status.HTTP_200_OK)

        if is_pending:
            return Response({"status": "Follow request pending"}, status=status.HTTP_202_ACCEPTED)

        return Response({"error": "Follower not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, author_id, follower_id):
        print(f"Received Author ID: {author_id}, Received Follower ID: {follower_id}")
        
        # get follow_request
        follow_request = Follows.objects.filter(followed_id=author_id, local_follower_id=follower_id).first()
        
        if not follow_request:
            print("Follow request not found in database for PUT")
            return Response({"error": "Follow request not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # update status to "ACCEPTED"
        follow_request.status = 'ACCEPTED'
        follow_request.save()
        
        # delete corresponding inbox_entry
        content_type = ContentType.objects.get_for_model(Follows)
        inbox_entry = Inbox.objects.filter(author__id=author_id, object_id=follow_request.id, content_type=content_type).first()
        
        if inbox_entry:
            print(f"Deleting Inbox entry: {inbox_entry}")
            inbox_entry.delete()
        else:
            print("Inbox entry not found")
        
        return Response({"status": "Follow request accepted"}, status=status.HTTP_200_OK)



    def delete(self, request, author_id, follower_id):
        print(f"Received Author ID: {author_id}, Received Follower ID: {follower_id}")
        
        # get follow_request
        follow_request = Follows.objects.filter(followed_id=author_id, local_follower_id=follower_id).first()

        if not follow_request:
            print("Follow request not found in database")
            return Response({"error": "Follow request not found"}, status=status.HTTP_404_NOT_FOUND)

        # delete inbox_entry
        content_type = ContentType.objects.get_for_model(Follows)
        inbox_entry = Inbox.objects.filter(author__id=author_id, object_id=follow_request.id, content_type=content_type).first()

        if inbox_entry:
            print(f"Found Inbox entry: {inbox_entry}")
            inbox_entry.delete()

        print(f"Deleting Follow Request: {follow_request.id}")
        
        # delete follow_request
        follow_request.delete()

        # second confirm whether the request has been deleted
        if Follows.objects.filter(id=follow_request.id).exists():
            print("Error: Follow request was not deleted!")
        else:
            print("Follow request deleted successfully")

        return Response({"status": "Follow request denied"}, status=status.HTTP_204_NO_CONTENT)




class UnfollowView(APIView):
    def delete(self, request, author_id, follower_id):
        try:
            # Validate UUID format
            author_id = UUID(author_id)
            follower_id = UUID(follower_id)
        except ValueError:
            return Response({'error': 'Invalid author or follower ID format.'}, status=400)
        
        try:
            # find corresponding follow relationship
            follow = Follows.objects.get(followed_id=author_id, local_follower_id=follower_id)
            
            # delete follow relationship
            follow.delete()
            return Response({'message': 'Successfully unfollowed the author.'}, status=200)
        
        except Follows.DoesNotExist:
            return Response({'error': 'Follow relationship does not exist.'}, status=404)

class FollowersDetailView(APIView):
    def get(self, request):
        author = get_object_or_404(Author, user=request.user)
        followers = Follows.objects.filter(followed_id=author, status='ACCEPTED').select_related('local_follower_id')
        followers_data = [{'id': follower.local_follower_id.id, 'displayName': follower.local_follower_id.display_name, 'profileImage': follower.local_follower_id.profile_image} for follower in followers]

        return Response({
            "followers": followers_data
        }, status=status.HTTP_200_OK)

class FriendsView(APIView):

    def get(self, request, author_id=None):
        current_user = get_object_or_404(Author, user=request.user)

        if author_id:
            viewed_author = get_object_or_404(Author, id=author_id)
        else:

            viewed_author = current_user
            
        following_ids = Follows.objects.filter(local_follower_id=viewed_author, status='ACCEPTED').values_list('followed_id', flat=True)
        
        followers_ids = Follows.objects.filter(followed_id=viewed_author, status='ACCEPTED').values_list('local_follower_id', flat=True)

        mutual_friend_ids = set(following_ids).intersection(set(followers_ids))

       
        friends = Author.objects.filter(id__in=mutual_friend_ids)

      
        friends_data = [
            {
                'id': friend.id,
                'displayName': friend.display_name,
                'profileImage': friend.profile_image
            }
            for friend in friends
        ]

        return Response({
            "friends": friends_data
        }, status=status.HTTP_200_OK)
    

class ProfileImageUploadView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, username):
        try:
            # Ensure the username exists
            if not username:
                return Response({"error": "Username not provided."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the request has a file
            file = request.FILES.get('profile_image')
            if not file:
                return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

            # Create a unique file path for the image based on the username
            file_path = f'profiles/{username}/{file.name}'
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)

            # Ensure the directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # Save the image to the media folder
            with open(full_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            # Construct the media URL with localhost:8000
            media_url = f'http://localhost:8000{settings.MEDIA_URL}{file_path}'

            return Response({"message": "Profile image uploaded successfully", "url": media_url}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": f"Failed to upload profile image: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
