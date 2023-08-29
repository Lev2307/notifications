from django.urls import reverse

from rest_framework.test import APIClient, APITestCase

from ..models import MyUser, ChooseSendingNotifications, UserTelegram

class MyUserApiViewsTests(APITestCase):
    @classmethod
    def setUp(cls):
        cls.username = 'admin_api_name'
        cls.password = 'admin_api'
        cls.email = 'admin_api_email@gmail.com'

        cls.myuser = MyUser.objects.create(username=cls.username, email=cls.email, is_subscribed=False, is_staff=True, is_active=True)
        cls.myuser.set_password(cls.password)
        cls.myuser.save()
        cls.network_telegram = ChooseSendingNotifications.objects.create(sender='telegram', user=cls.myuser)
        cls.network_email = ChooseSendingNotifications.objects.create(sender='email', user=cls.myuser)
        cls.telegram = UserTelegram.objects.create(telegram_user='admin_tg', chat_id='1111111111')
        cls.myuser.users_telegram = cls.telegram
        cls.myuser.save()
        cls.myuser.choose_sending.add(cls.network_telegram)
        cls.myuser.choose_sending.add(cls.network_email)

        cls.c = APIClient()

    def test_register_new_user_api_post_request(self):
        ''' Testing creating new user api POST request '''
        url = reverse('api-auth:registration_api')
        myusers_old = MyUser.objects.all().count()
        valid_data = {
            'username': 'new_user_api',
            'email': 'new_user_api@gmail.com',
            'password1': 'new_userpassword',
            'password2': 'new_userpassword',
            'tz': 'Atlantic/Reykjavik',
        }
        response = self.c.post(url, valid_data)
        myusers_new = MyUser.objects.all().count()

        self.assertEqual(myusers_old+1, myusers_new)
        self.assertTrue(MyUser.objects.filter(username=valid_data['username']).exists() == True)
        self.assertEqual(response.status_code, 201)

        # password mismatch
        invalid_data_password_mismatch = {
            'username': 'new_user_api',
            'email': 'new_user_api@gmail.com',
            'password1': 'new_userpassword',
            'password2': 'new_userpassword_wrong321',
            'tz': 'Atlantic/Reykjavik',
        }
        response_password_mismatch = self.c.post(url, invalid_data_password_mismatch)
        self.assertEqual(response_password_mismatch.status_code, 400)

        # email already exists
        invalid_data_email_already_exists = {
            'username': 'new_user_api',
            'email': self.email,
            'password1': 'new_userpassword',
            'password2': 'new_userpassword',
            'tz': 'Atlantic/Reykjavik',
        }
        response_email_exists = self.c.post(url, invalid_data_email_already_exists)
        self.assertEqual(response_email_exists.status_code, 400)

    def test_user_login_api_post_request(self):
        ''' Testing logging user in api POST request '''
        url = reverse('api-auth:login_api')
        valid_data = {
            'username': self.username,
            'password': self.password
        }
        response = self.c.post(url, valid_data)
        self.assertEqual(response.status_code, 202)

        # wrong credentials
        invalid_data = {
            'username': 'wrong username',
            'password': '4321'
        }
        wrong_credentials_response = self.c.post(url, invalid_data)
        self.assertEqual(wrong_credentials_response.status_code, 400)

    def test_user_logout_api_post_request(self):
        ''' Testing logging user out api POST request '''
        url = reverse('api-auth:logout_api')
        response = self.c.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('api-auth:login_api'))

    def test_user_profile_page_api_get_request(self):
        ''' Testing user profile page api get request '''
        url = reverse('api-auth:user_profile_api', kwargs={'pk': self.myuser.id})
        # anonymous user
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 403)

        # authenticated response
        self.c.login(username=self.username, password=self.password)
        authenticated_response = self.c.get(url)
        self.assertEqual(authenticated_response.status_code, 200)

    @classmethod
    def tearDownClass(cls):
        super(MyUserApiViewsTests, cls).tearDownClass()
        cls.myuser.delete()
        cls.network_telegram.delete()
        cls.network_email.delete()
        cls.telegram.delete()