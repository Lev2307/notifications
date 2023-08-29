from datetime import datetime, timedelta

from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from rest_framework import generics, status
from rest_framework.decorators import APIView
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from notification_categories.models import NotificationCategory
from config.celery import app

from ..models import NotificationBase, NotificationSingle, NotificationPeriodicity, NotificationStatus, NotificationId
from ..tasks import create_periodic_notification_task
from .serializers import (
    NotificationListSerializer, 
    NotificationPeriodicListSerializer, 
    NotificationSingleSerializer, 
    NotificationPeriodicSerializer, 
    NotificationStatusSerializer
)


class NotificationListApiView(generics.ListAPIView):
    model = NotificationBase
    serializer_class = NotificationListSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        data = {}
        single_notifications_data = {}
        periodic_notifications_data = {}
        for notification in self.get_queryset():
            if notification.check_all_notifications_are_complited() == False:
                if notification.notification_type == 'Single':
                    notification_single_query = NotificationSingle.objects.filter(notification_type_single=notification)
                    notification_single_serializer = NotificationSingleSerializer(notification_single_query, many=True)
                    for model in notification_single_serializer.data:
                        single_id = dict(model)["id"]
                    single_notifications_data[single_id] = notification_single_serializer.data
                elif notification.notification_type == 'Periodic':
                    notification_periodic_query = NotificationPeriodicity.objects.filter(notification_type_periodicity=notification)
                    notification_periodic_serializer = NotificationPeriodicListSerializer(notification_periodic_query, many=True)
                    for model in notification_periodic_serializer.data:
                        periodic_id = dict(model)["id"]
                    periodic_notifications_data[periodic_id] = notification_periodic_serializer.data
        data['notifications_single'] = single_notifications_data
        data['notifications_periodic'] = periodic_notifications_data
        return Response(data, status=status.HTTP_200_OK)
    
class NotificationFinishedListApiView(generics.ListAPIView):
    model = NotificationBase
    serializer_class = NotificationListSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        data = {}
        single_finished_notifications_data = {}
        periodic_finished_notifications_data = {}
        for notification in self.get_queryset():
            if notification.check_all_notifications_are_complited() == True:
                if notification.notification_type == 'Single':
                    notification_single_query = NotificationSingle.objects.filter(notification_type_single=notification)
                    notification_single_serializer = NotificationSingleSerializer(notification_single_query, many=True)
                    for model in notification_single_serializer.data:
                        single_id = dict(model)["id"]
                    single_finished_notifications_data[single_id] = notification_single_serializer.data
                elif notification.notification_type == 'Periodic':
                    notification_periodic_query = NotificationPeriodicity.objects.filter(notification_type_periodicity=notification)
                    notification_periodic_serializer = NotificationPeriodicListSerializer(notification_periodic_query, many=True)
                    for model in notification_periodic_serializer.data:
                        periodic_id = dict(model)["id"]
                    periodic_finished_notifications_data[periodic_id] = notification_periodic_serializer.data
        data['finished_notifications_single'] = single_finished_notifications_data
        data['finished_notifications_periodic'] = periodic_finished_notifications_data
        return Response(data, status=status.HTTP_200_OK)
    
class NotificationSingleDetailApiView(generics.RetrieveAPIView):
    queryset = NotificationSingle.objects.all()
    serializer_class = NotificationSingleSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        notif_single = get_object_or_404(self.queryset, pk=self.kwargs['pk'])

        if user == notif_single.notification_type_single.user:
            return super().get(request, *args, **kwargs)
        else:
            return Response(_('You are not the author of this notification'), status=status.HTTP_403_FORBIDDEN)

    def get_queryset(self):
        return self.queryset.filter(notification_type_single__user=self.request.user)

class NotificationSingleCreateApiView(generics.CreateAPIView):
    queryset = NotificationSingle.objects.all()
    serializer_class = NotificationSingleSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def get_queryset(self):
        return self.queryset.filter(notification_type_single__user=self.request.user)
            
    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            notification_date = serializer.data['notification_date']
            notification_time = serializer.data['notification_time']
            time = str(notification_date) + ' ' + str(notification_time)
            time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
            time = timezone.localtime(timezone.make_aware(time))

            notif_status = NotificationStatus.objects.create(time_stamp=time)
            notif_base = NotificationBase.objects.create(
                user=self.request.user,
                notification_type='Single'
            )
            self.queryset.create(
                notification_category=NotificationCategory.objects.get(id=serializer.data['notification_category']),
                title=serializer.data['title'],
                text=serializer.data['text'],
                notification_date=serializer.data['notification_date'],
                notification_time=serializer.data['notification_time'],
                notification_status=notif_status,
                notification_type_single=notif_base
            )
            return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

class NotificationSingleEditApiView(generics.UpdateAPIView):
    queryset = NotificationSingle.objects.all()
    serializer_class = NotificationSingleSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def get_queryset(self):
        return self.queryset.filter(notification_type_single__user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def put(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if NotificationSingle.objects.get(id=kwargs.get('pk')).notification_type_single.user == self.request.user:
            if serializer.is_valid(raise_exception=True):
                res = self.queryset.get(pk=self.kwargs['pk'])
                time = str(serializer.data['notification_date']) + ' ' + str(serializer.data['notification_time'])
                time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
                time = timezone.localtime(timezone.make_aware(time))

                NotificationStatus.objects.get(id=res.notification_status.id).delete()
                
                task = res.notification_status.notification_celery_id
                app.control.revoke(str(task), terminate=True, signal='SIGKILL')
                NotificationId.objects.get(notification_id=task).delete()
                
                res.notification_category = NotificationCategory.objects.get(id=serializer.data['notification_category'])
                res.title = serializer.data['title']
                res.text = serializer.data['text']
                res.notification_time = serializer.data['notification_time']
                res.notification_date = serializer.data['notification_date']
                res.notification_status = NotificationStatus.objects.create(time_stamp=time)
                res.save()
                return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

class NotificationSingleDeleteApiView(generics.DestroyAPIView):
    queryset = NotificationSingle.objects.all()
    serializer_class = NotificationSingleSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def get_queryset(self):
        return self.queryset.filter(notification_type_single__user=self.request.user)

    def delete(self, request, *args, **kwargs):
        notification_single = self.queryset.get(id=self.kwargs['pk'])
        if notification_single.notification_type_single.user == self.request.user:
            notification_base = NotificationBase.objects.get(notification_single=notification_single)

            task = notification_single.notification_status.notification_celery_id.notification_id

            app.control.revoke(str(task), terminate=True, signal='SIGKILL')
            NotificationId.objects.get(notification_id=task).delete()
            notification_base.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)
        
class NotificationPeriodicDetailApiView(generics.RetrieveAPIView):
    queryset = NotificationPeriodicity.objects.all()
    serializer_class = NotificationPeriodicListSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        notification_periodic = get_object_or_404(self.queryset, pk=self.kwargs['pk'])
        
        if user == notification_periodic.notification_type_periodicity.user:
            return super().get(request, *args, **kwargs)
        else:
            return Response(_('You are not the author of this notification'), status=status.HTTP_403_FORBIDDEN)
            
    def get_queryset(self):
        return self.queryset.filter(notification_type_periodicity__user=self.request.user)

class NotificationPeriodicCreateApiView(generics.CreateAPIView):
    queryset = NotificationPeriodicity.objects.all()
    serializer_class = NotificationPeriodicSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            current_date = timezone.localtime(timezone.now()).date()
            notif_base = NotificationBase.objects.create(
                user=self.request.user,
                notification_type='Periodic'
            )              
            if serializer.data['dates_type'] == 'Every day':
                dates = []
                amount_of_dates = serializer.data['notification_periodicity_num']
                for _ in range(amount_of_dates):
                    current_date = current_date + timedelta(days=1)
                    dates.append(current_date)
                self.queryset.create(
                    notification_category=NotificationCategory.objects.get(id=serializer.data['notification_category']),
                    title=serializer.data['title'],
                    text=serializer.data['text'],
                    notification_periodicity_num=serializer.data['notification_periodicity_num'],
                    notification_periodic_time=serializer.data['notification_periodic_time'],
                    dates=dates,
                    notification_type_periodicity=notif_base
                )
            elif serializer.data['dates_type'] == 'Your own dates':
                dates = serializer.data['dates'].split(',')
                dates = sorted(dates, key=lambda x: datetime.strptime(x, '%Y-%m-%d'))
                self.queryset.create(
                    notification_category=NotificationCategory.objects.get(id=serializer.data['notification_category']),
                    title=serializer.data['title'],
                    text=serializer.data['text'],
                    notification_periodic_time=serializer.data['notification_periodic_time'],
                    dates=dates,
                    notification_type_periodicity=notif_base
                )
            return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        return self.queryset.filter(notification_type_periodicity__user=self.request.user)

class NotificationPeriodicEditApiView(generics.UpdateAPIView):
    queryset = NotificationPeriodicity.objects.all()
    serializer_class = NotificationPeriodicSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def put(self, request, *args, **kwargs):
        if NotificationPeriodicity.objects.get(id=kwargs.get('pk')).notification_type_periodicity.user == self.request.user:
            serializer = self.serializer_class(data=request.data, context={'request': request})
            if serializer.is_valid(raise_exception=True):
                res = NotificationPeriodicity.objects.get(id=kwargs.get('pk'))
                for notification_status in res.notification_status.all():
                    NotificationStatus.objects.get(id=notification_status.id).delete()

                for task in res.notification_type_periodicity.task_id.all():
                    app.control.revoke(str(task), terminate=True, signal='SIGKILL')
                    NotificationId.objects.get(notification_id=task).delete()

                current_date = timezone.localtime(timezone.now()).date()                    
                if serializer.data['dates_type'] == 'Every day':
                    dates = []
                    for _ in range(serializer.data['notification_periodicity_num']):
                        current_date = current_date + timedelta(days=1)
                        dates.append(current_date)
                    res.dates = dates
                elif serializer.data['dates_type'] == 'Your own dates':
                    dates = serializer.data['dates'].split(',')
                    dates = sorted(dates, key=lambda x: datetime.strptime(x, '%Y-%m-%d'))
                    res.dates = dates
                res.notification_category = NotificationCategory.objects.get(id=serializer.data['notification_category'])
                res.title = serializer.data['title']
                res.text = serializer.data['text']
                res.notification_periodicity_num = serializer.data['notification_periodicity_num']
                res.notification_periodic_time = serializer.data['notification_periodic_time']
                res.save()
                return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        return self.queryset.filter(notification_type_periodicity__user=self.request.user)

class NotificationPeriodicDeleteApiView(generics.DestroyAPIView):
    queryset = NotificationPeriodicity.objects.all()
    serializer_class = NotificationPeriodicSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def get_queryset(self):
        return self.queryset.filter(notification_type_periodicity__user=self.request.user)

    def delete(self, request, *args, **kwargs):
        notification_periodic = NotificationPeriodicity.objects.get(id=kwargs.get('pk'))
        if notification_periodic.notification_type_periodicity.user == self.request.user:
            notification_base = NotificationBase.objects.get(notification_periodic=notification_periodic)

            for notification_status in notification_periodic.notification_status.all():
                NotificationStatus.objects.get(id=notification_status.id).delete()

            for task in notification_periodic.notification_type_periodicity.task_id.all():
                app.control.revoke(str(task), terminate=True, signal='SIGKILL')
                NotificationId.objects.get(notification_id=task).delete()

            notification_base.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

class NotificationPeriodicTimeStampsListApiView(generics.RetrieveAPIView):
    queryset = NotificationPeriodicity.objects.all()
    serializer_class = NotificationPeriodicListSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def get_queryset(self):
        return self.queryset.filter(notification_type_periodicity__user=self.request.user)

    def get(self, request, *args, **kwargs):
        user = self.request.user
        notif_periodicity = get_object_or_404(self.queryset, pk=self.kwargs['pk'])
        if user == notif_periodicity.notification_type_periodicity.user:
            return super().get(request, *args, **kwargs)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    def retrieve(self, request, *args, **kwargs):
        time_stamps = self.queryset.get(id=self.kwargs['pk']).notification_status.order_by('time_stamp')
        serializer = NotificationStatusSerializer(time_stamps, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class NotificationPeriodicRevokeCertainTimeStampApiView(generics.DestroyAPIView):
    queryset = NotificationStatus
    serializer_class = NotificationStatusSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def delete(self, request, *args, **kwargs):
        notification_status = get_object_or_404(self.queryset, id=self.kwargs['pk'])
        notification_status.done = 2
        notification_status.save()
        task = notification_status.notification_celery_id.notification_id
        app.control.revoke(str(task), terminate=True, signal='SIGKILL')
        return Response(status=status.HTTP_204_NO_CONTENT)

class NotificationPeriodicRevokeAllTimeStampsApiView(generics.DestroyAPIView):
    queryset = NotificationPeriodicity
    serializer_class = NotificationStatusSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def delete(self, request, *args, **kwargs):
        notif_statuses = get_object_or_404(self.queryset, id=self.kwargs['pk']).notification_status.filter(done=0)
        for notification_status in notif_statuses:
            notification_status.done = 2
            notification_status.save()
            task = notification_status.notification_celery_id.notification_id
            app.control.revoke(str(task), terminate=True, signal='SIGKILL')
        return Response(status=status.HTTP_204_NO_CONTENT)

class ChangeNotificationStatusFromRevokeToIncompleteApi(APIView):
    model = NotificationStatus
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def post(self, request, *args, **kwargs):
        notification_status = get_object_or_404(self.model, id=kwargs['pk'])
        notification_periodic_model = NotificationPeriodicity.objects.get(notification_status=notification_status)
        notification_celery_id = NotificationId.objects.get(notification_id=notification_status.notification_celery_id.notification_id)
        if notification_periodic_model.notification_type_periodicity.user == request.user:
            if notification_status.time_stamp > timezone.localtime(timezone.now()):
                notification_status.done = 0 # incomplited
                notification_status.save()
                task = create_periodic_notification_task.apply_async(args=(notification_periodic_model.id, notification_status.id), eta=notification_status.time_stamp)
                notification_celery_id.notification_id = task
                notification_celery_id.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
