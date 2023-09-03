from datetime import timedelta, datetime

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import permission_required, login_required
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.utils import timezone
from django.db.models.query_utils import Q
from django.utils.translation import get_language

from authentication.models import MyUser
from config.celery import app
from notification_categories.models import NotificationCategory

from .tasks import create_periodic_notification_task, create_notification_task
from .models import (
    NotificationBase, 
    NotificationPeriodicity, 
    NotificationSingle, 
    NotificationStatus, 
    NotificationId
)
from .forms import (
    NotificationCreateForm, 
    NotificationSingleEditForm, 
    PeriodicalNotificationCreateForm, 
    NotificationPeriodicEditForm, 
)

def redirect_user_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse_lazy('notifications:notification_list')) 
    else:
        return HttpResponseRedirect(reverse_lazy('auth:login')) 
        
class NotificationListView(LoginRequiredMixin, ListView):
    model = NotificationBase
    login_url = reverse_lazy('auth:login')
    template_name = 'notifications/notification_lists/notification_list.html'
    context_object_name = 'notifications'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['notifications_types'] = NotificationCategory.objects.filter(user=self.request.user)
        return context

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)

class NotificationFinishedListView(LoginRequiredMixin, ListView):
    model = NotificationBase
    login_url = reverse_lazy('auth:login')
    template_name = 'notifications/notification_lists/notification_finished_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["finished_notifications"] = [notification for notification in self.get_queryset() if notification.check_all_notifications_are_complited() == True]
        context["finished_notifications_length"] = len(context["finished_notifications"])
        return context

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)

class SearchNotificationView(LoginRequiredMixin, ListView):
    model = NotificationBase
    login_url = reverse_lazy('auth:login')
    context_object_name = "quotes"
    template_name = "notifications/search/search.html"
    context_object_name = "searched_notifications"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get("q")
        context["user"] = self.request.user
        if self.get_queryset():
            context["searched_notifications_length"] = len(self.get_queryset())
        else:
            context["searched_notifications_length"] = 0
        return context

    def get_queryset(self):
        query = self.request.GET.get("q")
        if query:
            singles = self.model.objects.filter(user=self.request.user).filter(notification_type="Single")
            singles = singles.filter((Q(notification_single__title__icontains=query) | Q(notification_single__text__icontains=query)))
            incomplited_singles = [notification_single for notification_single in singles if notification_single.check_all_notifications_are_complited() == False]

            periodics = self.model.objects.filter(Q(notification_type="Periodic") & Q(user=self.request.user))
            periodics = periodics.filter((Q(notification_periodic__title__icontains=query) | Q(notification_periodic__text__icontains=query)))
            incomplited_periodics = [notification_periodic for notification_periodic in periodics if notification_periodic.check_all_notifications_are_complited() == False]
            
            return incomplited_singles + incomplited_periodics

class NotificationSingleDetailView(LoginRequiredMixin, DetailView):
    login_url = reverse_lazy('auth:login')
    model = NotificationSingle
    template_name = 'notifications/detail/notification_single_detail.html'
    context_object_name = 'notification_single_detail'

    def get(self, request, *args, **kwargs):
        user = self.request.user
        notif_single = get_object_or_404(self.model, pk=self.kwargs['pk'])
        if user == notif_single.notification_type_single.user:
            return super().get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy('notifications:notification_list'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_networks"] = (MyUser.objects.get(username=self.request.user.username).choose_sending.filter(active=True)).count()
        return context

class NotificationSingleCreateView(LoginRequiredMixin, CreateView):
    login_url = reverse_lazy('auth:login')
    model = NotificationSingle
    form_class = NotificationCreateForm
    template_name = 'notifications/CUD_notifications/create_notification.html'
    success_url = reverse_lazy('notifications:notification_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = MyUser.objects.get(username=self.request.user)
        context['all_notifications'] = NotificationBase.objects.filter(user=self.request.user).all().count()
        context['only_inactive'] = len(MyUser.objects.get(username=self.request.user.username).get_only_inactive_networks())
        return context

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['user'] = self.request.user
        return kw

    def form_valid(self, form):
        notification_date = form.cleaned_data['notification_date']
        notification_time = form.cleaned_data['notification_time']
        time = str(notification_date) + ' ' + str(notification_time)
        time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
        time = timezone.localtime(timezone.make_aware(time))

        notif_status = NotificationStatus.objects.create(time_stamp=time)
        notif_base = NotificationBase.objects.create(
            user=self.request.user,
            notification_type='Single'
        )
        self.model.objects.create(
            notification_category=form.cleaned_data['notification_category'],
            title=form.cleaned_data['title'],
            text=form.cleaned_data['text'],
            notification_date=form.cleaned_data['notification_date'],
            notification_time=form.cleaned_data['notification_time'],
            notification_status=notif_status,
            notification_type_single=notif_base
        )
        return HttpResponseRedirect(self.success_url)
        
class NotificationSingleEditView(LoginRequiredMixin, UpdateView):
    login_url = reverse_lazy('auth:login')
    model = NotificationSingle
    form_class = NotificationSingleEditForm
    template_name = 'notifications/CUD_notifications/edit_notification.html'
    success_url = reverse_lazy('notifications:notification_list')

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['request'] = self.request
        kw['notification_kwargs'] = self.kwargs
        return kw
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = MyUser.objects.get(username=self.request.user.username)
        return context
    
    def get(self, request, *args, **kwargs):
        user = self.request.user
        notif_single = get_object_or_404(self.model, pk=self.kwargs['pk'])
        if user == notif_single.notification_type_single.user:
            return super().get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy('notifications:notification_list'))
        
    def form_valid(self, form):
        res = self.model.objects.get(pk=self.kwargs['pk'])
        time = str(form.cleaned_data['notification_date']) + ' ' + str(form.cleaned_data['notification_time'])
        time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
        time = timezone.localtime(timezone.make_aware(time))

        NotificationStatus.objects.get(id=res.notification_status.id).delete()

        task = res.notification_status.notification_celery_id
        app.control.revoke(str(task), terminate=True, signal='SIGKILL')

        NotificationId.objects.get(notification_id=task).delete()

        res.notification_category = form.cleaned_data['notification_category']
        res.title = form.cleaned_data['title']
        res.text = form.cleaned_data['text']
        res.notification_time = form.cleaned_data['notification_time']
        res.notification_date = form.cleaned_data['notification_date']
        res.notification_status = NotificationStatus.objects.create(time_stamp=time)
        res.save()
        return HttpResponseRedirect(self.success_url)

class NotificationSingleDeleteView(LoginRequiredMixin, DeleteView):
    model = NotificationSingle
    success_url = reverse_lazy('notifications:notification_list')
    login_url = reverse_lazy('auth:login')
    template_name = 'notifications/CUD_notifications/delete_single_notification.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['notification'] = get_object_or_404(self.model, pk=self.kwargs['pk'])
        context['user'] = self.request.user
        return context
    
    def get(self, request, *args, **kwargs):
        user = self.request.user
        notif_single = get_object_or_404(self.model, pk=self.kwargs['pk'])
        if user == notif_single.notification_type_single.user:
            return super().get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy('notifications:notification_list'))
    
    def delete(self, request, *args, **kwargs):
        notification_single = self.model.objects.get(id=self.kwargs['pk'])
        notification_base = NotificationBase.objects.get(notification_single=notification_single)
        
        task = notification_single.notification_status.notification_celery_id.notification_id

        app.control.revoke(str(task), terminate=True, signal='SIGKILL')
        NotificationId.objects.get(notification_id=task).delete()
        notification_base.delete()

        return HttpResponseRedirect(self.success_url)

class NotificationPeriodicDetailView(LoginRequiredMixin, DetailView):
    login_url = reverse_lazy('auth:login')
    model = NotificationPeriodicity
    template_name = 'notifications/detail/notification_periodic_detail.html'
    context_object_name = 'notification_periodic_detail'

    def get(self, request, *args, **kwargs):
        user = self.request.user
        notif_periodicity = get_object_or_404(self.model, pk=self.kwargs['pk'])
        if user == notif_periodicity.notification_type_periodicity.user:
            return super().get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy('notifications:notification_list'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        periodic_notification = get_object_or_404(self.model, pk=self.kwargs['pk'])
        context['notification_is_finished'] = periodic_notification.notification_status.filter(done=1).count() == periodic_notification.notification_status.all().count()
        context['count_all_revoked_execution_times'] = len(periodic_notification.get_all_revoked())
        return context

class PeriodicalNotificationCreateView(LoginRequiredMixin, CreateView):
    login_url = reverse_lazy('auth:login')
    model = NotificationPeriodicity
    form_class = PeriodicalNotificationCreateForm
    template_name = 'notifications/CUD_notifications/create_periodical_notification.html'
    success_url = reverse_lazy('notifications:notification_list')

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['request'] = self.request
        return kw

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = MyUser.objects.get(username=self.request.user)
        context['all_notifications'] = NotificationBase.objects.filter(user=self.request.user).all().count()
        context['only_inactive'] = len(MyUser.objects.get(username=self.request.user.username).get_only_inactive_networks())
        return context

    def form_valid(self, form):
        request_post_data = self.request.POST
        current_date = timezone.localtime(timezone.now()).date()
        notif_base = NotificationBase.objects.create(
            user=self.request.user,
            notification_type='Periodic'
        )
        for value in request_post_data.values():                    
            if value == 'Every day':
                dates = []
                amount_of_dates = form.cleaned_data.get('notification_periodicity_num')
                for _ in range(amount_of_dates):
                    current_date = current_date + timedelta(days=1)
                    dates.append(current_date)
                self.model.objects.create(
                    notification_category=form.cleaned_data['notification_category'],
                    title=form.cleaned_data['title'],
                    text=form.cleaned_data['text'],
                    notification_periodicity_num=form.cleaned_data['notification_periodicity_num'],
                    notification_periodic_time=form.cleaned_data['notification_periodic_time'],
                    dates=dates,
                    notification_type_periodicity=notif_base
                )
            elif value == 'Your own dates':
                dates = self.request.POST.get('dates').split(',')
                dates = sorted(dates, key=lambda x: datetime.strptime(x, '%Y-%m-%d'))
                self.model.objects.create(
                    notification_category=form.cleaned_data['notification_category'],
                    title=form.cleaned_data['title'],
                    text=form.cleaned_data['text'],
                    notification_periodic_time=form.cleaned_data['notification_periodic_time'],
                    dates=dates,
                    notification_type_periodicity=notif_base
                )
        return HttpResponseRedirect(self.success_url)

class NotificationPeriodicEditView(LoginRequiredMixin, UpdateView):
    model = NotificationPeriodicity
    form_class = NotificationPeriodicEditForm
    template_name = 'notifications/CUD_notifications/edit_notification_periodic.html'
    success_url = reverse_lazy('notifications:notification_list')
    login_url = reverse_lazy('auth:login')

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['request'] = self.request
        kw['notification_periodic_kwargs'] = self.kwargs
        return kw

    def get(self, request, *args, **kwargs):
        user = self.request.user
        notif_periodicity = get_object_or_404(self.model, pk=self.kwargs['pk'])
        if user == notif_periodicity.notification_type_periodicity.user:
            return super().get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy('notifications:notification_list'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = MyUser.objects.get(username=self.request.user.username)
        return context

class NotificationPeriodicDeleteView(DeleteView, LoginRequiredMixin):
    login_url = reverse_lazy('auth:login')
    template_name = 'notifications/CUD_notifications/delete_notification_periodic.html'
    success_url = reverse_lazy('notifications:notification_list')
    model = NotificationPeriodicity
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['notification'] = self.model.objects.get(id=self.kwargs['pk'])
        context['user'] = self.request.user
        return context

    def get(self, request, *args, **kwargs):
        user = self.request.user
        notif_periodicity = get_object_or_404(self.model, pk=self.kwargs['pk'])
        if user == notif_periodicity.notification_type_periodicity.user:
            return super().get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy('notifications:notification_list'))
    
    def delete(self, *args, **kwargs):
        notification_periodic = self.model.objects.get(id=self.kwargs['pk'])
        notification_base = NotificationBase.objects.get(notification_periodic=notification_periodic)

        for notification_status in notification_periodic.notification_status.all():
            NotificationStatus.objects.get(id=notification_status.id).delete()

        for task in notification_periodic.notification_type_periodicity.task_id.all():
            app.control.revoke(str(task), terminate=True, signal='SIGKILL')
            NotificationId.objects.get(notification_id=task).delete()

        notification_base.delete()

        return HttpResponseRedirect(self.success_url)

class NotificationPeriodicListTimeStampsView(LoginRequiredMixin, ListView):
    model = NotificationPeriodicity
    template_name = 'notifications/notification_periodic_time_stamps/notification_periodic_time_stamp_list.html'
    success_url = reverse_lazy('notifications:notification_list')
    login_url = reverse_lazy('auth:login')

    def get_context_data(self, **kwargs):
        c = super().get_context_data(**kwargs)
        model = get_object_or_404(self.model, pk=self.kwargs['pk'])
        c['times'] = model.notification_status.order_by('time_stamp')
        c['model'] = model
        c['user'] = self.request.user
        return c

    def get(self, request, *args, **kwargs):
        user = self.request.user
        notif_periodicity = get_object_or_404(self.model, pk=self.kwargs['pk'])
        if user == notif_periodicity.notification_type_periodicity.user and notif_periodicity.notification_status.filter(done=0).count() != 0:
            return super().get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy('notifications:notification_list'))
    
class NotificationPeriodicRevokeCertainTimeStampView(LoginRequiredMixin, DeleteView):
    model = NotificationStatus
    template_name = 'notifications/notification_periodic_time_stamps/remove_notification_periodic_time_stamp_detail.html'
    login_url = reverse_lazy('auth:login')
    context_object_name = 'notification_status'

    def get_success_url(self):
        notification_status = self.model.objects.get(id=self.kwargs['pk'])
        notification_periodic_model = notification_status.notification_periodic_statuses.get(notification_status=notification_status)
        return reverse_lazy("notifications:detail_periodic_notification", kwargs={"pk": notification_periodic_model.id})

    def get(self, request, *args, **kwargs):
        notification = NotificationPeriodicity.objects.get(notification_status__in=[self.model.objects.get(id=self.kwargs['pk'])])
        if self.request.user == notification.notification_type_periodicity.user:
            return super().get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy('notifications:notification_list'))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        return context

    def post(self, request, *args, **kwargs):
        notification_status = get_object_or_404(self.model, id=self.kwargs['pk'])
        notification_status.done = 2
        notification_status.save()
        task = notification_status.notification_celery_id.notification_id
        app.control.revoke(str(task), terminate=True, signal='SIGKILL')
        return HttpResponseRedirect(self.get_success_url())

class NotificationPeriodicRevokeAllTimeStampsView(LoginRequiredMixin, DeleteView):
    model = NotificationPeriodicity
    template_name = 'notifications/notification_periodic_time_stamps/remove_notification_periodic_all_times_page.html'
    login_url = reverse_lazy('auth:login')

    def get_success_url(self):
        return reverse_lazy("notifications:detail_periodic_notification", kwargs={"pk": self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['notification'] = self.model.objects.get(id=self.kwargs['pk']).notification_status
        context['notification_statuses'] = context['notification'].filter(done=0)
        context["user"] = self.request.user
        return context

    def get(self, request, *args, **kwargs):
        user = self.request.user
        notif_periodicity = get_object_or_404(self.model, pk=self.kwargs['pk'])
        if user == notif_periodicity.notification_type_periodicity.user:
            return super().get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy('notifications:notification_list'))

    def post(self, request, *args, **kwargs):
        notif_statuses = self.model.objects.get(id=self.kwargs['pk']).notification_status.filter(done=0)
        for notification_status in notif_statuses:
            notification_status.done = 2
            notification_status.save()
            task = notification_status.notification_celery_id.notification_id
            app.control.revoke(str(task), terminate=True, signal='SIGKILL')
        return HttpResponseRedirect(self.get_success_url())

@login_required(login_url='/auth/login/')
def change_notification_status_from_revoke_to_incomplete(request, **kwargs):
    notification_status = get_object_or_404(NotificationStatus, id=kwargs['pk'])
    notification_periodic_model = NotificationPeriodicity.objects.get(notification_status=notification_status)
    notification_celery_id = NotificationId.objects.get(notification_id=notification_status.notification_celery_id.notification_id)
    if notification_periodic_model.notification_type_periodicity.user == request.user:
        if notification_status.time_stamp > timezone.localtime(timezone.now()):
            notification_status.done = 0 # incomplited
            notification_status.save()
            task = create_periodic_notification_task.apply_async(args=(notification_periodic_model.id, notification_status.id, get_language()), eta=notification_status.time_stamp)
            notification_celery_id.notification_id = task
            notification_celery_id.save()
    return HttpResponseRedirect(reverse_lazy('notifications:detail_periodic_notification', kwargs={"pk": notification_periodic_model.id }))

@permission_required('is_staff', login_url=reverse_lazy('notifications:notification_list'))
def notificatePeriodicNotificationOnlyForAdmin(request, *args, **kwargs):
    notification_status = get_object_or_404(NotificationStatus, id=kwargs['pk'])
    notification_periodic_model = NotificationPeriodicity.objects.get(notification_status=notification_status)
    if notification_periodic_model.notification_type_periodicity.user == request.user and notification_status.done == 0:
        create_periodic_notification_task.delay(notification_periodic_model.id, notification_status.id, get_language())
    return HttpResponseRedirect(reverse_lazy('notifications:detail_periodic_notification', kwargs={'pk': notification_periodic_model.id}))

@permission_required('is_staff', login_url=reverse_lazy('notifications:notification_list'))
def notificateSingleNotificationOnlyForAdmin(request, *args, **kwargs):
    notification = get_object_or_404(NotificationSingle, id=kwargs['pk'])
    if notification.notification_type_single.user == request.user and notification.notification_status.done == 0:
        create_notification_task.delay(notification.id, get_language())
    return HttpResponseRedirect(reverse_lazy('notifications:notification_list'))
