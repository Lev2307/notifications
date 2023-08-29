from django.contrib.auth import login, logout
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from rest_framework import generics
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, APIView

from ..models import MyUser, ChooseSendingNotifications
from .serializers import RegistrationSerializer, LoginSerializer, UserProfileSerializer

class RegisterApiView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.POST)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            email = ChooseSendingNotifications.objects.create(sender='email', user=user)
            telegram = ChooseSendingNotifications.objects.create(sender='telegram', user=user)
            user.choose_sending.add(email)
            user.choose_sending.add(telegram)
            user.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

class LoginApiView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        serializer = self.serializer_class(data=self.request.data, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        self.request.session["user_timezone"] = user.tz
        return Response(status=status.HTTP_202_ACCEPTED)

@api_view(['POST'])
def logoutApiView(request):
    logout(request)
    return HttpResponseRedirect(reverse_lazy('api-auth:login_api'))

class UserProfileApiView(generics.RetrieveAPIView):
    model = MyUser
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def get_object(self):
        return self.model.objects.get(pk=self.kwargs['pk'])