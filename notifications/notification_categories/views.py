from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import NotificationCategory
from .forms import AddNotificationCategoryForm, EditNotificationCategoryForm

class AddNotificationCategoryView(LoginRequiredMixin, CreateView):
    ''' Страница создания категории для оповещения '''
    model = NotificationCategory
    form_class = AddNotificationCategoryForm
    success_url = reverse_lazy('auth:profile')
    login_url = reverse_lazy('auth:login')
    template_name = 'notification_categories/add_new_notification_category.html'

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['request'] = self.request
        return kw

    def form_valid(self, form):
        notif_type = self.model.objects.create(user=self.request.user, name_type=form.cleaned_data['name_type'], color=form.cleaned_data['color'])
        notif_type.save()
        return HttpResponseRedirect(self.success_url)

class EditNotificationCategoryView(LoginRequiredMixin, UpdateView):
    ''' Страница редактирования категории для оповещения '''
    model = NotificationCategory
    form_class = EditNotificationCategoryForm
    success_url = reverse_lazy('auth:profile')
    login_url = reverse_lazy('auth:login')
    template_name = 'notification_categories/edit_notification_category.html'

    def get(self, request, *args, **kwargs):
        notif_type = self.model.objects.get(slug=kwargs['slug'])
        if self.request.user == notif_type.user:
            return super().get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(self.success_url)
            
    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['request'] = self.request
        return kw

class DeleteNotificationCategoryView(LoginRequiredMixin, DeleteView):
    ''' Страница удаления категории для оповещения '''
    model = NotificationCategory
    success_url = reverse_lazy('auth:profile')
    login_url = reverse_lazy('auth:login')
    template_name = 'notification_categories/delete_notification_category.html'
    context_object_name = 'category'

    def get(self, request, *args, **kwargs):
        notif_type = self.model.objects.get(slug=kwargs['slug'])
        if self.request.user == notif_type.user:
            return super().get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(self.success_url)