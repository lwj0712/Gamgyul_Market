from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from insta.models import Post
from market.models import Receipt
from accounts.models import Follow
from accounts.serializers import ProfileSearchSerializer

User = get_user_model()


class FriendRecommendationView(APIView):
    permission_classes = [IsAuthenticated]
