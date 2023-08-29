from django.urls import reverse

from rest_framework.test import APIClient, APITestCase

from authentication.models import MyUser
from ..models import NotificationCategory

class NotificationCategoriesApiViewsTests(APITestCase):
    @classmethod
    def setUp(cls):
        cls.username = 'admin_name_category_api'
        cls.email = 'admin_email_api@gmail.com'
        cls.password = 'admin_category_api'

        cls.another_user_username = 'user_name_category_api'
        cls.another_user_email = 'user_email_api@gmail.com'
        cls.another_user_password = 'user_category_api'

        cls.myuser = MyUser.objects.create(username=cls.username, email=cls.email)
        cls.myuser.set_password(cls.password)
        cls.myuser.save()

        cls.another_user = MyUser.objects.create(username=cls.another_user_username, email=cls.another_user_email)
        cls.another_user.set_password(cls.another_user_password)
        cls.another_user.save()

        cls.notification_category_test_type = 'new_one_api'
        cls.test_color = '#000000'    
        cls.notification_category = NotificationCategory.objects.create(
            user=cls.myuser,
            name_type=cls.notification_category_test_type,
            color=cls.test_color
        )
        cls.notification_category.save()

        cls.c = APIClient()

    def test_adding_new_notification_category_api_post_request(self):
        ''' Testing creating new notification category api POST request'''
        url = reverse('notification_categories_api:create_notification_category_api')
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
        self.assertEqual(response.status_code, 201)

    def test_editing_notification_category_api_post_request(self):
        ''' Testing editing notification category api POST request'''
        data = {
            'name_type': 'edited test type name',
            'color': '#3d6cb9'
        }
        request_kwargs = {
            'slug': NotificationCategory.objects.get(name_type=self.notification_category_test_type).slug
        }
        url = reverse('notification_categories_api:edit_notification_category_api', kwargs=request_kwargs)

        # response
        self.c.login(username=self.username, password=self.password)
        response = self.c.put(url, data)

        created_category = NotificationCategory.objects.get(name_type=data['name_type'])

        self.assertTrue(NotificationCategory.objects.filter(name_type=data['name_type']).exists() == True)
        self.assertEqual(created_category.name_type, data['name_type'])
        self.assertEqual(created_category.color, data['color'])
        self.assertEqual(response.status_code, 200)

    def test_deleting_notification_category_api_post_request(self):
        ''' Testing deleting notification category api POST request'''
        request_kwargs = {
            'slug': NotificationCategory.objects.get(name_type=self.notification_category_test_type).slug
        }
        url = reverse('notification_categories_api:delete_notification_category_api', kwargs=request_kwargs)

        old_notification_category_count = NotificationCategory.objects.all().count()

        self.c.login(username=self.username, password=self.password)
        authenticated_response = self.c.delete(url)
        new_notification_category_count = NotificationCategory.objects.all().count()

        self.assertEqual(old_notification_category_count, new_notification_category_count+1)
        self.assertEqual(authenticated_response.status_code, 204)

    @classmethod
    def tearDownClass(cls):
        super(NotificationCategoriesApiViewsTests, cls).tearDownClass()
        cls.notification_category.delete()
        cls.myuser.delete()
        cls.another_user.delete()