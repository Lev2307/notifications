import os

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.template.loader import render_to_string

from ..models import MyUser, ChooseSendingNotifications, UserTelegram

# Create your tests here.
class MyUserViewsTests(TestCase):

    @classmethod
    def setUp(cls):
        cls.username = 'admin_name'
        cls.password = 'admin'
        cls.email = 'admin_email@gmail.com'

        cls.myuser = MyUser.objects.create(username=cls.username, email=cls.email, is_subscribed=False, is_staff=True, is_active=True)
        cls.myuser.set_password(cls.password)
        cls.myuser.save()
        cls.network_telegram = ChooseSendingNotifications.objects.create(sender='telegram', user=cls.myuser)
        cls.network_email = ChooseSendingNotifications.objects.create(sender='email', user=cls.myuser)
        cls.telegram = UserTelegram.objects.create(telegram_user='admin', chat_id='1111111111')
        cls.myuser.users_telegram = cls.telegram
        cls.myuser.save()
        cls.myuser.choose_sending.add(cls.network_telegram)
        cls.myuser.choose_sending.add(cls.network_email)

        cls.c = Client()

        cls.factory = RequestFactory()

        cls.telegram_bot_link = "https://t.me/NotificationsAppTelegramBot"

    def test_registration_get_request(self):
        '''Test registration GET request'''
        url = reverse('auth:registration')
        response = self.c.get(url)
        self.assertEqual(response.status_code, 200)

    def test_registration_post_request(self):
        '''Test registartion POST request'''
        url = reverse('auth:registration')
        myusers_old = MyUser.objects.all().count()
        data = {
            'username': 'new_user',
            'email': 'new_user@gmail.com',
            'password1': 'new_userpassword',
            'password2': 'new_userpassword',
            'tz': 'Europe/Moscow',
        }
        response = self.c.post(url, data)
        myusers_new = MyUser.objects.all().count()

        self.assertEqual(myusers_old+1, myusers_new)
        self.assertEqual(response.status_code, 302)
    
    def test_login_get_request(self):
        '''Test login GET request'''
        url = reverse('auth:login')
        response = self.c.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_login_post_request(self):
        '''Test login POST request'''
        url = reverse('auth:login')
        data = {
            'username': self.username,
            'password': self.password
        }
        response = self.c.post(url, data)
        self.assertEqual(response.status_code, 302)
    
    def test_logout_request(self):
        '''test logout POST request'''
        url = reverse('auth:logout')
        response = self.c.post(url)
        self.assertTrue(response.status_code == 302)
    
    def test_authenticated_profile_page(self):
        '''Test authenticated user getting profile page GET request'''
        self.c.login(username=self.username, password=self.password)
        url = reverse('auth:profile')
        response = self.c.get(url)
        self.assertEqual(response.status_code, 200)

    def test_anonymous_profile_page(self):
        '''Test anonymous user getting profile page GET request'''
        url = reverse('auth:profile')
        response = self.c.get(url)
        self.assertEqual(response.status_code, 302)

    def test_authenticated_dispetcher_providing_networks(self):
        '''Test method which redirect authenticated user to confirm network page depending on the slug'''
        from ..views import dispetcher_providing_networks

        # telegram
        request_telegram_kwargs = {
            "slug": "telegram"
        }
        request_telegram = self.factory.get(reverse("auth:dispetcher_providing_networks", kwargs=request_telegram_kwargs))
        request_telegram.user = self.myuser

        response_telegram = dispetcher_providing_networks(request_telegram, **request_telegram_kwargs)

        self.assertEqual(response_telegram.status_code, 302)
        self.assertEqual(response_telegram.url, self.telegram_bot_link)

        # email
        request_email_kwargs = {
            "slug": "email"
        }
        request_email = self.factory.get(reverse("auth:dispetcher_providing_networks", kwargs=request_email_kwargs))
        request_email.user = self.myuser

        response_email = dispetcher_providing_networks(request_email, **request_email_kwargs)

        self.assertEqual(response_email.status_code, 302)
        self.assertEqual(response_email.url, reverse('auth:verificate_user_email'))
    
    def test_creating_telegram_profile_page_get_request(self):
        ''' Test telegram dispetcher which depending on request type redirect to GET or POST method'''
        from ..views import attaching_telegram_account_get_request
        # not exisiting tg model
        user_telegram_kwargs = {
            "chat_id": "5909121080",
            "first_name": "Федя",
            "username": "test_user",
            "last_name": "Петров",
        }
        # GET method
        request_get = self.factory.get(
            reverse("auth:register_tg") + f"?chat_id={user_telegram_kwargs['chat_id']}&first_name={user_telegram_kwargs['first_name']}&username={user_telegram_kwargs['username']}&last_name={user_telegram_kwargs['last_name']}"
        )
        request_get.user = self.myuser
        request_get.method = "GET"

        response = attaching_telegram_account_get_request(request_get)

        self.assertEqual(response.status_code, 200)

    def test_creating_telegram_account_post_request(self):
        ''' Test creating and attaching telegram account to user'''
        from ..views import attaching_telegram_account_post_request

        old_tg_account = UserTelegram.objects.all().count()
        user_telegram_kwargs = {
            "chat_id": "5909121080",
            "first_name": "Федя",
            "username": "test_user",
            "last_name": "Петров",
        }
        # Create telegram account
        request = self.factory.get(
            reverse("auth:register_tg") + f"?chat_id={user_telegram_kwargs['chat_id']}&first_name={user_telegram_kwargs['first_name']}&username={user_telegram_kwargs['username']}&last_name={user_telegram_kwargs['last_name']}",
        )
        request.user = self.myuser
        request.method = "POST"
        request.POST = {'type': 'create'}

        response = attaching_telegram_account_post_request(request)

        new_tg_accounts = UserTelegram.objects.all().count()

        self.assertEqual(new_tg_accounts, old_tg_account+1)
        self.assertEqual(UserTelegram.objects.get(chat_id=user_telegram_kwargs['chat_id']).chat_id, "5909121080")
        self.assertEqual(UserTelegram.objects.get(chat_id=user_telegram_kwargs['chat_id']).telegram_user, "test_user")
        self.assertEqual(response.status_code, 302)

    def test_editing_telegram_account_post_request(self):
        ''' Test editing attached user`s telegram account'''
        from ..views import attaching_telegram_account_post_request

        old_tg = UserTelegram.objects.all().first()
        user_telegram_kwargs = {
            "chat_id": "5909121080",
            "first_name": "Федя",
            "username": "test_user",
            "last_name": "Петров",
        }
        # Edit telegram account
        request = self.factory.get(
            reverse("auth:register_tg") + f"?chat_id={user_telegram_kwargs['chat_id']}&first_name={user_telegram_kwargs['first_name']}&username={user_telegram_kwargs['username']}&last_name={user_telegram_kwargs['last_name']}",
        )
        request.user = self.myuser
        request.method = "POST"
        request.POST = {'type': 'edit'}

        response = attaching_telegram_account_post_request(request)

        new_tg = UserTelegram.objects.all().first()

        self.assertNotEqual(old_tg.telegram_user, new_tg.telegram_user)
        self.assertNotEqual(old_tg.chat_id, new_tg.chat_id)
        self.assertNotEqual(old_tg.started_time, new_tg.started_time)
        self.assertEqual(new_tg.telegram_user, user_telegram_kwargs["username"])
        self.assertEqual(new_tg.chat_id, user_telegram_kwargs["chat_id"])

    def test_sender_information_get_request(self):
        ''' Test sender infromation page get request ( Telegram page or email page ) '''
        self.c.login(username=self.username, password=self.password)

        # Telegram
        url = reverse('auth:sender_information', kwargs={'slug': 'telegram'})
        response = self.c.get(url)
        self.assertEqual(response.status_code, 200)

        # Email
        url = reverse('auth:sender_information', kwargs={'slug': 'email'})
        response = self.c.get(url)
        self.assertEqual(response.status_code, 200)


    def test_delete_or_detach_user_telegram_account_post_request(self):
        ''' Test detaching user`s telegram account '''
        from ..views import delete_telegram
        all_telegram_accounts_before_response = UserTelegram.objects.all().count()

        request_kwargs = {
            'pk': UserTelegram.objects.first().id
        }
        request = self.factory.post(reverse('auth:delete_telegram', kwargs=request_kwargs))
        request.user = self.myuser
        
        response = delete_telegram(request, **request_kwargs)

        all_telegram_accounts_after_response = UserTelegram.objects.all().count()
        
        self.assertEqual(all_telegram_accounts_before_response, all_telegram_accounts_after_response+1)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('auth:profile'))

    def test_activate_sender_network(self):
        ''' Test activating or deactivating sender ( telegram or email ) '''
        from ..views import activate_sender_network

        sender_before_activating = ChooseSendingNotifications.objects.first().active
        request_kwargs = {
            'pk': ChooseSendingNotifications.objects.first().id
        }

        request = self.factory.get(reverse('auth:activate_sender_network', kwargs=request_kwargs))
        request.user = self.myuser

        response = activate_sender_network(request, **request_kwargs)

        sender_after_activating = ChooseSendingNotifications.objects.first().active

        self.assertNotEqual(sender_before_activating, sender_after_activating) # False - deactivated, True - activated
        self.assertEqual(response.status_code, 302)

    def test_Changing_user_email_get_request(self):
        ''' Test changing user email GET method '''
        self.c.login(username=self.username, password=self.password)
        response_kwargs = {
            'pk': self.myuser.id
        }
        response = self.c.get(reverse('auth:changing_user_email', kwargs=response_kwargs))

        self.assertEqual(response.status_code, 200)

    def test_Changing_user_email_post_request(self):
        ''' Test changing user email GET method '''
        self.c.login(username=self.username, password=self.password)

        old_email = MyUser.objects.first().email
        response_kwargs = {
            'pk': self.myuser.id
        }
        data = {
            'email': 'a@a.com',
            'password1': self.password
        }
        response = self.c.post(reverse('auth:changing_user_email', kwargs=response_kwargs), data=data)

        new_email = MyUser.objects.first().email

        self.assertEqual(new_email, "a@a.com")
        self.assertNotEqual(old_email, new_email)
        self.assertEqual(response.status_code, 302)

    def test_verificate_user_email(self):
        ''' Test verificating user email '''
        from ..views import verificate_user_email

        request = self.factory.get(reverse('auth:verificate_user_email'))
        request.user = self.myuser

        response = verificate_user_email(request)

        self.assertEqual(response.status_code, 200)

    @classmethod
    def tearDownClass(cls):
        super(MyUserViewsTests, cls).tearDownClass()
        cls.myuser.delete()
        cls.network_telegram.delete()
        cls.network_email.delete()
        cls.telegram.delete()

