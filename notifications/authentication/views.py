from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _

from .models import MyUser, ChooseSendingNotifications
from notification_categories.models import NotificationCategory
from .forms import RegisterForm, ChangeUserEmail, LoginForm
from .models import UserTelegram
from .tokens import generate_token


def send_verificate_message_to_user(user, request):
    current_site = get_current_site(request)
    email_subject = 'Подтвердите свою почту'
    email_body = render_to_string('auth/email/email_verification/activate_user_email.html', {
        'user': user,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': generate_token.make_token(user)
    })

    email = EmailMessage(subject=email_subject, body=email_body,to=[user.email])
    email.content_subtype = 'html'
    email.send()

def activate_user_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = MyUser.objects.get(pk=uid)
    except Exception as e:
        user = None

    if user and generate_token.check_token(user, token):
        c = ChooseSendingNotifications.objects.get(sender='email', user=user)
        c.active = True
        c.linked_network = True
        c.save()
        messages.add_message(request, messages.SUCCESS, _('Your email has been successfully confirmed!'))
        return redirect(reverse_lazy('auth:profile'))

    return render(request, 'auth/email/email_verification/activation_failed.html', {"user": user})


class RegisterView(CreateView):
    form_class = RegisterForm
    success_url = reverse_lazy('auth:login')
    template_name = 'auth/registration.html'

    def form_valid(self, form):
        user = form.save(commit=True)
        email = ChooseSendingNotifications.objects.create(sender='email', user=user)
        telegram = ChooseSendingNotifications.objects.create(sender='telegram', user=user)
        user.choose_sending.add(email)
        user.choose_sending.add(telegram)
        user.save()
        return HttpResponseRedirect(self.success_url)

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            return HttpResponseRedirect(reverse_lazy('notifications:notification_list'))
        else:
            return super().dispatch(request, *args, **kwargs)

class UserLoginView(LoginView):
    form_class = LoginForm
    success_url = reverse_lazy('auth:profile')
    template_name = 'auth/login.html'

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            return HttpResponseRedirect(reverse_lazy('notifications:notification_list'))
        else:
            return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        remember_me = form.cleaned_data['remember_me']  # get remember me data from cleaned_data of form
        if not remember_me:
            self.request.session.set_expiry(0)  # if remember me is 
            self.request.session.modified = True
        login(self.request, form.get_user())
        self.request.session["user_timezone"] = form.get_user().tz
        return super(UserLoginView, self).form_valid(form)

class UserLogoutView(LogoutView):
    redirect_field_name = reverse_lazy("auth:login")

class UserProfileView(LoginRequiredMixin, DetailView):
    login_url = reverse_lazy('auth:login')
    model = MyUser
    template_name = 'auth/profile.html'
    context_object_name = 'user'

    def get_object(self):
        return self.model.objects.get(pk=self.request.user.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_notification_categorys'] = NotificationCategory.objects.filter(Q(user=self.request.user) | Q(user=None))
        context['all_choose_sending'] = ChooseSendingNotifications.objects.filter(user=self.request.user)
        print(type(self.request.user.tz))
        return context

@login_required(login_url=reverse_lazy('auth:login'))
def dispetcher_providing_networks(request, **kwargs):
    network = kwargs.get('slug') or ''
    if network == 'telegram':
        return redirect('https://t.me/NotificationsAppTelegramBot')
    elif network == 'email':
        return redirect(reverse_lazy('auth:verificate_user_email'))

@login_required(login_url=reverse_lazy('auth:login'))
def attaching_telegram_account_dispetcher(request):
    if len(request.GET) != 0:
        if request.method == 'GET':
            response = attaching_telegram_account_get_request(request)
        elif request.method == 'POST':
            response = attaching_telegram_account_post_request(request)
        return response
    else:
        return HttpResponseNotFound(_('Page not found'))

def attaching_telegram_account_get_request(request):
    flag = ""
    if UserTelegram.objects.filter(chat_id=request.GET['chat_id'], telegram_user=request.GET['username']).exists():
        return render(request, 'auth/telegram_is_already_used.html')
    else:
        if MyUser.objects.get(username=request.user.username).users_telegram != None:
            flag = 'changing'
        else:
            flag = 'linking'
    return render(request, 'auth/accept_telegram_user_registration.html', {'flag': flag, 'username': request.GET['username'], 'user': request.user})

def attaching_telegram_account_post_request(request):
    for value in request.POST.values():
        if not UserTelegram.objects.filter(chat_id=request.GET['chat_id'], telegram_user=request.GET['username']).exists():
            if value == 'create':
                tg = UserTelegram.objects.create(chat_id=request.GET['chat_id'], started_time=timezone.now(), telegram_user=request.GET['username'])
                myuser = MyUser.objects.get(username=request.user.username)
                myuser.users_telegram = tg
                myuser.save()
                network = ChooseSendingNotifications.objects.get(sender='telegram', user=request.user)
                network.linked_network = True
                network.active = True
                network.save()
                return HttpResponseRedirect(reverse_lazy('auth:profile')) 
            elif value == 'edit':
                user_tg = MyUser.objects.get(username=request.user.username).users_telegram
                tg_model = UserTelegram.objects.get(telegram_user=user_tg)
                tg_model.chat_id = request.GET['chat_id']
                tg_model.started_time = timezone.now()
                tg_model.telegram_user = request.GET['username']
                tg_model.save()
                user_tg = tg_model
                user_tg.save()
                return HttpResponseRedirect(reverse_lazy('auth:profile')) 

class SenderInformationView(LoginRequiredMixin, DetailView):
    model = ChooseSendingNotifications
    template_name = 'auth/sender_information.html'
    login_url = reverse_lazy('auth:login')

    def get_object(self):
        return self.model.objects.get(slug=self.kwargs['slug'], user=self.request.user)

    def get_context_data(self, **kwargs):
        c = super().get_context_data(**kwargs)
        c['sender'] = str(MyUser.objects.get(username=self.request.user.username).choose_sending.get(sender=self.kwargs['slug'], user=self.request.user).sender)
        c['user'] = MyUser.objects.get(username=self.request.user.username)
        return c

@login_required(login_url=reverse_lazy('auth:login'))
def activate_sender_network(request, **kwargs):
    c = ChooseSendingNotifications.objects.get(id=kwargs.get('pk'), user=request.user)
    sender = MyUser.objects.get(username=request.user.username).choose_sending.get(sender=c.sender)
    if sender.active == False:
        sender.active = True
    else:
        sender.active = False
    sender.save()
    return HttpResponseRedirect(reverse_lazy('auth:profile'))

@login_required(login_url=reverse_lazy('auth:login'))
def delete_telegram(request, **kwargs):
    tg = UserTelegram.objects.get(id=kwargs['pk'])
    if request.method == 'POST':
        if request.user == MyUser.objects.get(users_telegram=tg):
            network = ChooseSendingNotifications.objects.get(sender='telegram', user=request.user)
            network.active = False
            network.linked_network = False
            network.save()
            tg.delete()
            return HttpResponseRedirect(reverse_lazy('auth:profile'))
        else:
            return HttpResponseRedirect(reverse_lazy('auth:profile'))
    return render(request, 'auth/delete_telegram.html', {'user': request.user})

class ChangeUserEmail(LoginRequiredMixin, UpdateView):
    form_class = ChangeUserEmail
    model = MyUser
    template_name = 'auth/change_user_email.html'
    login_url = reverse_lazy('auth:login')
    success_url = reverse_lazy('auth:dispetcher_providing_networks')

    def get(self, request, *args, **kwargs):
        if self.request.user.email == MyUser.objects.get(id=kwargs['pk']).email:
            return super().get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(self.success_url)

    def get_success_url(self):
        slug = ChooseSendingNotifications.objects.get(user=self.request.user, sender='email').slug
        return reverse_lazy('auth:dispetcher_providing_networks', kwargs={'slug': slug})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_subscribed'] = MyUser.objects.get(username=self.request.user.username).is_subscribed
        return context

    def get_form_kwargs(self):
        c = super().get_form_kwargs()
        c['kwargs'] = self.kwargs
        return c

    def form_valid(self, form):
        u = MyUser.objects.get(username=self.request.user.username)
        u.email = form.cleaned_data['email']
        u.save()

        c = ChooseSendingNotifications.objects.get(sender='email', user=self.request.user)
        c.active = False
        c.linked_network = False
        c.save()
        return HttpResponseRedirect(self.get_success_url())

@login_required(login_url=reverse_lazy('auth:login'))
def verificate_user_email(request):
    if request.method == 'GET':
        user = MyUser.objects.get(username=request.user.username)
        email = user.email
        position_of_at = email.find('@')
        email =  email[0]+'*****'+email[position_of_at-1:].lower()

        send_verificate_message_to_user(request.user, request)

    return render(request, 'auth/email/email_verification/verificate_email_page.html', {'email': email})