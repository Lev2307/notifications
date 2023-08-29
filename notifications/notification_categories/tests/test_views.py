from django.test import TestCase, Client, RequestFactory

from django.urls import reverse

from authentication.models import MyUser
from ..models import NotificationCategory

class NotificationCategoriesViewsTests(TestCase):
    @classmethod
    def setUp(cls):
        cls.username = 'admin_name_category'
        cls.email = 'admin_email@gmail.com'
        cls.password = 'admin_category'

        cls.another_user_username = 'user_name_category'
        cls.another_user_email = 'user_email@gmail.com'
        cls.another_user_password = 'user_category'

        cls.myuser = MyUser.objects.create(username=cls.username, email=cls.email)
        cls.myuser.set_password(cls.password)
        cls.myuser.save()

        cls.another_user = MyUser.objects.create(username=cls.another_user_username, email=cls.another_user_email)
        cls.another_user.set_password(cls.another_user_password)
        cls.another_user.save()

        cls.notification_category_test_type = 'new_one'
        cls.test_color = '#f8f8f8'    
        cls.notification_category = NotificationCategory.objects.create(
            user=cls.myuser,
            name_type=cls.notification_category_test_type,
            color=cls.test_color
        )
        cls.notification_category.save()

        cls.c = Client()

    def test_adding_new_notification_category_get_request(self):
        ''' Testing creating new notification category GET request'''
        url = reverse('notification_categories:add_notification_category')

        # anonymous user
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 302)

        # authenticated user
        self.c.login(username=self.username, password=self.password)
        authenticated_response = self.c.get(url)
        self.assertEqual(authenticated_response.status_code, 200)

    def test_adding_new_notification_category_post_request(self):
        ''' Testing creating new notification category POST request'''
        url = reverse('notification_categories:add_notification_category')
        data = {
            'name_type': 'test type name',
            'color': '#a7ff83'
        }
        old_notification_categories_count = NotificationCategory.objects.all().count()

        # response
        self.c.login(username=self.username, password=self.password)
        response = self.c.post(url, data)

        new_notification_categories_count = NotificationCategory.objects.all().count()
        created_category = NotificationCategory.objects.get(name_type=data['name_type'])

        self.assertEqual(old_notification_categories_count+1, new_notification_categories_count)
        self.assertTrue(NotificationCategory.objects.filter(name_type=data['name_type']).exists() == True)
        self.assertEqual(created_category.name_type, data['name_type'])
        self.assertEqual(created_category.color, data['color'])
        self.assertEqual(response.status_code, 302)

    def test_editing_notification_category_get_request(self):
        ''' Testing editing notification category GET request'''
        request_kwargs = {
            'slug': NotificationCategory.objects.get(name_type=self.notification_category_test_type).slug
        }
        url = reverse('notification_categories:edit_notification_category', kwargs=request_kwargs)

        # anonymous user
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 302)

        # authenticated user
        self.c.login(username=self.username, password=self.password)
        authenticated_response = self.c.get(url)
        self.assertEqual(authenticated_response.status_code, 200)

    def test_editing_notification_category_post_request(self):
        ''' Testing editing notification category POST request'''
        data = {
            'name_type': 'edited test type name',
            'color': '#3d6cb9'
        }
        request_kwargs = {
            'slug': NotificationCategory.objects.get(name_type=self.notification_category_test_type).slug
        }
        url = reverse('notification_categories:edit_notification_category', kwargs=request_kwargs)

        # response
        self.c.login(username=self.username, password=self.password)
        response = self.c.post(url, data)

        created_category = NotificationCategory.objects.get(name_type=data['name_type'])

        self.assertTrue(NotificationCategory.objects.filter(name_type=data['name_type']).exists() == True)
        self.assertEqual(created_category.name_type, data['name_type'])
        self.assertEqual(created_category.color, data['color'])
        self.assertEqual(response.status_code, 302)

    def test_deleting_notification_category_get_request(self):
        ''' Testing deleting notification category GET request'''
        request_kwargs = {
            'slug': NotificationCategory.objects.get(name_type=self.notification_category_test_type).slug
        }
        url = reverse('notification_categories:delete_notification_category', kwargs=request_kwargs)

        # anonymous user
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 302)

        # authenticated user
        self.c.login(username=self.username, password=self.password)
        authenticated_response = self.c.get(url)
        self.assertEqual(authenticated_response.status_code, 200)

    def test_deleting_notification_category_post_request(self):
        ''' Testing deleting notification category POST request'''
        request_kwargs = {
            'slug': NotificationCategory.objects.get(name_type=self.notification_category_test_type).slug
        }
        url = reverse('notification_categories:delete_notification_category', kwargs=request_kwargs)
        old_notification_category_count = NotificationCategory.objects.all().count()

        self.c.login(username=self.username, password=self.password)
        authenticated_response = self.c.post(url)
        new_notification_category_count = NotificationCategory.objects.all().count()

        self.assertEqual(old_notification_category_count, new_notification_category_count+1)
        self.assertEqual(authenticated_response.status_code, 302)

    @classmethod
    def tearDownClass(cls):
        super(NotificationCategoriesViewsTests, cls).tearDownClass()
        cls.notification_category.delete()
        cls.myuser.delete()
        cls.another_user.delete()