import pytz
from datetime import datetime, timedelta, date

from django.utils import timezone
from django.urls import reverse

from rest_framework.test import APIClient, APITestCase

from authentication.models import MyUser
from config.celery import app
from notification_categories.models import NotificationCategory
from notifications.models import NotificationSingle, NotificationPeriodicity, NotificationBase, NotificationStatus, NotificationId

class NotificationsGenericViewsApiTests(APITestCase):
    @classmethod
    def setUp(cls):
        cls.username = 'admin_name_api'
        cls.email = 'admin_email_api@gmail.com'
        cls.password = 'admin_api'
        cls.basic_user = MyUser(username=cls.username, email=cls.email)
        cls.basic_user.set_password(cls.password)
        cls.basic_user.save()
        cls.c = APIClient()

    def test_incomplete_notifications_list_api_get_method(self):
        ''' Testing GET request of notifications list api '''
        url = reverse('notifications_api:notifications_list_api')

        # anonymous user
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 403)

        # authenticated user
        self.c.login(username=self.username, password=self.password)
        authenticated_response = self.c.get(url)

        self.assertEqual(authenticated_response.status_code, 200)

    def test_finished_notifications_list_api_get_method(self):
        ''' Testing GET request of notifications finished list api '''
        url = reverse('notifications_api:finished_notifications_list_api')

        # anonymous user
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 403)

        # authenticated user
        self.c.login(username=self.username, password=self.password)
        authenticated_response = self.c.get(url)

        self.assertEqual(authenticated_response.status_code, 200)

    @classmethod
    def tearDownClass(cls):
        super(NotificationsGenericViewsApiTests, cls).tearDownClass()
        cls.basic_user.delete()

class NotificationSingleViewsApiTests(APITestCase):

    @classmethod
    def setUp(cls):
        cls.username = 'api_admin'
        cls.email = 'api_admin@api_admin.com'
        cls.password = 'api_admin123'
        cls.myuser = MyUser.objects.create(username=cls.username, email=cls.email)
        cls.myuser.set_password(cls.password)
        cls.myuser.save()

        cls.another_user_username = 'api_another_user'
        cls.another_user_email = 'api_another_user@io.com'
        cls.another_user_password = 'api_another_user321'
        cls.another_user = MyUser.objects.create(username=cls.another_user_username, email=cls.another_user_email)
        cls.another_user.set_password(cls.another_user_password)
        cls.another_user.save()

        cls.notification_category_name = 'test name'
        cls.notification_category_color = '#000000'
        cls.test_category = NotificationCategory.objects.create(
            user=cls.myuser,
            name_type=cls.notification_category_name,
            color=cls.notification_category_color
        )
        
        cls.test_title = 'test api title'
        cls.test_text = 'test api text'
        cls.test_notification_date = timezone.localtime(timezone.now(), timezone=pytz.timezone(cls.myuser.tz)).date()
        cls.test_notification_time = timezone.localtime(timezone.now(), timezone=pytz.timezone(cls.myuser.tz)).time().replace(microsecond=0)
        cls.time_stamp = str(cls.test_notification_date) + ' ' + str(cls.test_notification_time)
        cls.time_stamp = datetime.strptime(cls.time_stamp, '%Y-%m-%d %H:%M:%S')

        cls.test_notification_status = NotificationStatus.objects.create(
            time_stamp=timezone.localtime(timezone.make_aware(cls.time_stamp))
        )
        cls.test_notification_type_single = NotificationBase.objects.create(
            user=cls.myuser,
            notification_type='Single'
        )
        cls.notification_single = NotificationSingle.objects.create(
            notification_category=cls.test_category,
            title=cls.test_title,
            text=cls.test_text,
            notification_date=cls.test_notification_date,
            notification_time=cls.test_notification_time,
            notification_status=cls.test_notification_status,
            notification_type_single=cls.test_notification_type_single
        )
        cls.c = APIClient()

    def test_notification_single_detail_api_get_method(self):
        ''' Testing GET request of notification single detail page '''
        request_kwargs = {
            'pk': NotificationSingle.objects.first().id
        }
        url = reverse('notifications_api:notification_single_detail_api', kwargs=request_kwargs)

        # anonymous user
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 403)

        # authenticated user who is not `author` of this notification
        self.c.login(username=self.another_user_username, password=self.another_user_password)
        authenticated_another_user_response = self.c.get(url)
        self.assertEqual(authenticated_another_user_response.status_code, 403)

        # authenticated user who is `author` of this notification
        self.c.login(username=self.username, password=self.password)
        authenticated_myuser_response = self.c.get(url)
        self.assertEqual(authenticated_myuser_response.status_code, 200)

    def test_create_notification_single_api_post_request(self):
        ''' Testing POST request of notification single create page '''

        url = reverse('notifications_api:create_notification_single_api')

        # good response
        valid_data = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'new single',
            'text': 'new text',
            'notification_date': self.test_notification_date + timedelta(days=1),
            'notification_time': self.test_notification_time,
            'notification_status': NotificationStatus.objects.create(),
            'notification_type_single': NotificationBase.objects.create(user=self.myuser, notification_type='Single')
        }
        old_notification_singles = NotificationSingle.objects.all().count()

        self.c.login(username=self.username, password=self.password)
        response = self.c.post(url, valid_data)
        
        new_notification_singles = NotificationSingle.objects.all().count()

        self.assertEqual(old_notification_singles+1, new_notification_singles)
        self.assertEqual(response.status_code, 201)

        # bad response
        invalid_data = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'new single title',
            'text': 'new text',
            'notification_date': self.test_notification_date - timedelta(days=4),
            'notification_time': self.test_notification_time,
            'notification_status': NotificationStatus.objects.create(),
            'notification_type_single': NotificationBase.objects.create(user=self.myuser, notification_type='Single')
        }

        self.c.login(username=self.username, password=self.password)
        response = self.c.post(url, invalid_data)
        self.assertEqual(response.status_code, 400)

    def test_edit_notification_single_api_put_request(self):
        ''' Testing PUT request of notification single edit page '''

        request_kwargs = {
            'pk': NotificationSingle.objects.first().id
        }
        url = reverse('notifications_api:edit_notification_single_api', kwargs=request_kwargs)

        # good response
        valid_data = {
            'notification_category': NotificationCategory.objects.get(name_type='work').id,
            'title': 'new single title edit',
            'text': 'new text edit',
            'notification_date': self.test_notification_date + timedelta(days=10),
            'notification_time': self.test_notification_time,
            'notification_status': NotificationStatus.objects.create(),
            'notification_type_single': NotificationBase.objects.create(user=self.myuser, notification_type='Single')
        }

        self.c.login(username=self.username, password=self.password)
        response = self.c.put(url, valid_data)

        edited_notification_single = NotificationSingle.objects.get(title=valid_data['title'])
        self.assertTrue(NotificationSingle.objects.filter(title=valid_data['title']).exists(), True)
        self.assertEqual(edited_notification_single.text, valid_data['text'])
        self.assertEqual(edited_notification_single.notification_date, valid_data['notification_date'])
        self.assertEqual(edited_notification_single.notification_time, valid_data['notification_time'])
        self.assertEqual(response.status_code, 200)

        # bad response
        invalid_data = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'new single',
            'text': 'new text',
            'notification_date': self.test_notification_date - timedelta(days=4),
            'notification_time': self.test_notification_time,
            'notification_status': NotificationStatus.objects.create(),
            'notification_type_single': NotificationBase.objects.create(user=self.myuser, notification_type='Single')
        }

        self.c.login(username=self.username, password=self.password)
        response = self.c.put(url, invalid_data)
        self.assertEqual(response.status_code, 400)

    def test_delete_notification_single_api_delete_request(self):
        ''' Testing DELETE request of notification single delete page '''

        request_kwargs = {
            'pk': NotificationSingle.objects.first().id
        }
        url = reverse('notifications_api:delete_notification_single_api', kwargs=request_kwargs)

        old_notifications_count = NotificationSingle.objects.all().count()

        self.c.login(username=self.username, password=self.password)
        response = self.c.delete(url)

        new_notifications_count = NotificationSingle.objects.all().count()

        self.assertEqual(old_notifications_count, new_notifications_count+1) # 1 0
        self.assertEqual(response.status_code, 204)

    @classmethod
    def tearDownClass(cls):
        super(NotificationSingleViewsApiTests, cls).tearDownClass()
        cls.myuser.delete()
        cls.another_user.delete()
        cls.test_notification_type_single.delete()


class NotificationPeriodicViewsApiTests(APITestCase):
    @classmethod
    def setUp(cls):

        cls.username = 'admin_periodic'
        cls.email = 'admin_periodic@io.com'
        cls.password = 'admin_periodic123'
        cls.myuser = MyUser.objects.create(username=cls.username, email=cls.email)
        cls.myuser.set_password(cls.password)
        cls.myuser.save()

        cls.now = timezone.localtime(timezone.now(), timezone=pytz.timezone(cls.myuser.tz))


        cls.another_user_username = 'user_periodic'
        cls.another_user_email = 'user@u.com'
        cls.another_user_password = 'user_periodic3214'
        cls.another_user = MyUser.objects.create(username=cls.another_user_username, email=cls.another_user_email)
        cls.another_user.set_password(cls.another_user_password)
        cls.another_user.save()

        cls.test_title = 'test periodic api title'
        cls.test_text = 'test periodic api text'
        cls.notification_periodic_time = (cls.now + timedelta(minutes=30)).time().replace(microsecond=0)
        cls.notification_periodicity_num = 4
        cls.dates = [(cls.now.date() + timedelta(days=i)) for i in range(1, cls.notification_periodicity_num+1)]
        cls.type_periodic = NotificationBase.objects.create(
            user=cls.myuser,
            notification_type='Periodic'
        )
        cls.type_periodic.save()

        cls.periodic_notification = NotificationPeriodicity.objects.create(
            notification_category=NotificationCategory.objects.first(),
            title=cls.test_title,
            text=cls.test_text,
            notification_periodic_time=cls.notification_periodic_time,
            notification_periodicity_num=cls.notification_periodicity_num,
            dates=cls.dates,
            notification_type_periodicity=cls.type_periodic
        )

        cls.c = APIClient()

    def test_notification_periodic_detail_page_api_get_method(self):
        ''' Testing GET request of notification periodic detail page '''
        request_kwargs = {
            'pk': NotificationPeriodicity.objects.first().id
        }
        url = reverse('notifications_api:notification_periodic_detail_api', kwargs=request_kwargs)

        # anonymous user
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 403)

        # authenticated user who is not `author` of this notification
        self.c.login(username=self.another_user_username, password=self.another_user_password)
        authenticated_another_user_response = self.c.get(url)
        self.assertEqual(authenticated_another_user_response.status_code, 403)

        # authenticated user who is `author` of this notification
        self.c.login(username=self.username, password=self.password)
        authenticated_myuser_response = self.c.get(url)
        self.assertEqual(authenticated_myuser_response.status_code, 200)

    def test_notification_periodic_create_page_api_every_day_post_request(self):
        ''' Testing POST request of notification periodic create page ( choosing `every day` )'''
        self.c.login(username=self.username, password=self.password)

        url = reverse('notifications_api:create_notification_periodic_api')

        now = self.now

        # good response
        old_notifications_periodic = NotificationPeriodicity.objects.all().count()
        valid_data = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'new title',
            'text': 'new text',
            'notification_periodicity_num': 2,
            'notification_periodic_time': now.time().replace(microsecond=0),
            'notification_type_periodicity': NotificationBase.objects.create(user=self.myuser, notification_type='Periodic'),
            'dates': '',
            'dates_type': 'Every day'
        }

        response = self.c.post(url, valid_data)

        new_notifications_periodic = NotificationPeriodicity.objects.all().count()

        self.assertEqual(old_notifications_periodic+1, new_notifications_periodic)
        self.assertEqual(response.status_code, 201)

        # bad response
        invalid_data = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'new title',
            'text': 'new text',
            'notification_periodicity_num': 2,
            'notification_periodic_time': now.time().replace(microsecond=0),
            'notification_type_periodicity': NotificationBase.objects.create(user=self.myuser, notification_type='Periodic'),
            'dates': [(now.date() + timedelta(days=i+2)) for i in range(1, 4)],
            'dates_type': 'Every day'
        }

        bad_response = self.c.post(url, invalid_data)

        self.assertEqual(bad_response.status_code, 400)

    def test_notification_periodic_create_page_api_own_dates_post_request(self):
        ''' Testing POST request of notification periodic create page ( choosing `your own dates` )'''
        self.c.login(username=self.username, password=self.password)

        url = reverse('notifications_api:create_notification_periodic_api')

        now = self.now

        # good response
        old_notifications_periodic = NotificationPeriodicity.objects.all().count()
        valid_data = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'new title',
            'text': 'new text',
            'notification_periodicity_num': 2,
            'notification_periodic_time': now.time().replace(microsecond=0),
            'notification_type_periodicity': NotificationBase.objects.create(user=self.myuser, notification_type='Periodic'),
            'dates': [(now.date() + timedelta(days=i+2)) for i in range(1, 4)],
            'dates_type': 'Your own dates'
        }

        response = self.c.post(url, valid_data)

        new_notification_periodic = NotificationPeriodicity.objects.all().count()

        self.assertEqual(old_notifications_periodic+1, new_notification_periodic)
        self.assertEqual(response.status_code, 201)

        # bad response
        invalid_data_empty_dates = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'new title',
            'text': 'new text',
            'notification_periodicity_num': 2,
            'notification_periodic_time': now.time().replace(microsecond=0),
            'notification_type_periodicity': NotificationBase.objects.create(user=self.myuser, notification_type='Periodic'),
            'dates': '',
            'dates_type': 'Your own dates'
        }

        response = self.c.post(url, invalid_data_empty_dates)
        self.assertEqual(response.status_code, 400)

        invalid_data_invalid_dates = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'new title',
            'text': 'new text',
            'notification_periodicity_num': 2,
            'notification_periodic_time': now.time().replace(microsecond=0),
            'notification_type_periodicity': NotificationBase.objects.create(user=self.myuser, notification_type='Periodic'),
            'dates': 'ab',
            'dates_type': 'Your own dates'
        }

        response = self.c.post(url, invalid_data_invalid_dates)
        self.assertEqual(response.status_code, 400)

        late_date = date(2056, 12, 25)
        invalid_data_date_is_late = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'new title',
            'text': 'new text',
            'notification_periodicity_num': 1,
            'notification_periodic_time': now.time().replace(microsecond=0),
            'notification_type_periodicity': NotificationBase.objects.create(user=self.myuser, notification_type='Periodic'),
            'dates': f'{late_date}',
            'dates_type': 'Your own dates'
        }

        response = self.c.post(url, invalid_data_date_is_late)
        self.assertEqual(response.status_code, 400)

        past_date = now.date() - timedelta(days=20)
        invalid_data_date_is_past = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'new title',
            'text': 'new text',
            'notification_periodicity_num': 1,
            'notification_periodic_time': now.time().replace(microsecond=0),
            'notification_type_periodicity': NotificationBase.objects.create(user=self.myuser, notification_type='Periodic'),
            'dates': f'{past_date}',
            'dates_type': 'Your own dates'
        }

        response = self.c.post(url, invalid_data_date_is_past)
        self.assertEqual(response.status_code, 400)

    def test_notification_periodic_edit_page_api_every_day_post_request(self):
        ''' Testing POST request of notification periodic edit page ( choosing `every day` )'''
        self.c.login(username=self.username, password=self.password)

        request_kwargs = {
            'pk': NotificationPeriodicity.objects.first().id
        }

        url = reverse('notifications_api:edit_notification_periodic_api', kwargs=request_kwargs)

        now = self.now

        # good response

        valid_data = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'edited title',
            'text': 'edited text',
            'notification_periodicity_num': 2,
            'notification_periodic_time': now.time().replace(microsecond=0),
            'notification_type_periodicity': NotificationBase.objects.create(user=self.myuser, notification_type='Periodic'),
            'dates': '',
            'dates_type': 'Every day'
        }

        response = self.c.put(url, valid_data)


        edited_notification_periodic = NotificationPeriodicity.objects.get(title=valid_data['title'])
        self.assertTrue(NotificationPeriodicity.objects.filter(title=valid_data['title']).exists(), True)
        self.assertEqual(edited_notification_periodic.text, valid_data['text'])
        self.assertEqual(edited_notification_periodic.notification_periodicity_num, valid_data['notification_periodicity_num'])
        self.assertEqual(edited_notification_periodic.notification_periodic_time, valid_data['notification_periodic_time'])

        self.assertEqual(response.status_code, 200)

        # bad response
        invalid_data = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'edited title',
            'text': 'edited text',
            'notification_periodicity_num': 2,
            'notification_periodic_time': now.time().replace(microsecond=0),
            'notification_type_periodicity': NotificationBase.objects.create(user=self.myuser, notification_type='Periodic'),
            'dates': [(now.date() + timedelta(days=i+2)) for i in range(1, 4)],
            'dates_type': 'Every day'
        }

        bad_response = self.c.put(url, invalid_data)

        self.assertEqual(bad_response.status_code, 400)


    def test_notification_periodic_edit_page_api_own_dates_post_request(self):
        ''' Testing POST request of notification periodic edit page ( choosing `your own dates` )'''
        self.c.login(username=self.username, password=self.password)

        request_kwargs = {
            'pk': NotificationPeriodicity.objects.first().id
        }

        url = reverse('notifications_api:edit_notification_periodic_api', kwargs=request_kwargs)

        now = self.now

        # good response
        valid_data = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'edited title',
            'text': 'edited text',
            'notification_periodicity_num': 2,
            'notification_periodic_time': now.time().replace(microsecond=0),
            'notification_type_periodicity': NotificationBase.objects.create(user=self.myuser, notification_type='Periodic'),
            'dates': [(now.date() + timedelta(days=i+2)) for i in range(1, 4)],
            'dates_type': 'Your own dates'
        }

        response = self.c.put(url, valid_data)
        edited_notification_periodic = NotificationPeriodicity.objects.get(title=valid_data['title'])
        self.assertTrue(NotificationPeriodicity.objects.filter(title=valid_data['title']).exists(), True)
        self.assertEqual(edited_notification_periodic.text, valid_data['text'])
        self.assertEqual(edited_notification_periodic.notification_periodicity_num, valid_data['notification_periodicity_num'])
        self.assertEqual(edited_notification_periodic.notification_periodic_time, valid_data['notification_periodic_time'])

        self.assertEqual(response.status_code, 200)

        # bad response
        invalid_data_empty_dates = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'new title',
            'text': 'new text',
            'notification_periodicity_num': 2,
            'notification_periodic_time': now.time().replace(microsecond=0),
            'notification_type_periodicity': NotificationBase.objects.create(user=self.myuser, notification_type='Periodic'),
            'dates': '',
            'dates_type': 'Your own dates'
        }

        response = self.c.put(url, invalid_data_empty_dates)
        self.assertEqual(response.status_code, 400)

        invalid_data_invalid_dates = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'new title',
            'text': 'new text',
            'notification_periodicity_num': 2,
            'notification_periodic_time': now.time().replace(microsecond=0),
            'notification_type_periodicity': NotificationBase.objects.create(user=self.myuser, notification_type='Periodic'),
            'dates': 'ab',
            'dates_type': 'Your own dates'
        }

        response = self.c.put(url, invalid_data_invalid_dates)
        self.assertEqual(response.status_code, 400)

        late_date = date(2056, 12, 25)
        invalid_data_date_is_late = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'new title',
            'text': 'new text',
            'notification_periodicity_num': 1,
            'notification_periodic_time': now.time().replace(microsecond=0),
            'notification_type_periodicity': NotificationBase.objects.create(user=self.myuser, notification_type='Periodic'),
            'dates': f'{late_date}',
            'dates_type': 'Your own dates'
        }

        response = self.c.put(url, invalid_data_date_is_late)
        self.assertEqual(response.status_code, 400)

        past_date = now.date() - timedelta(days=20)
        invalid_data_date_is_past = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'new title',
            'text': 'new text',
            'notification_periodicity_num': 1,
            'notification_periodic_time': now.time().replace(microsecond=0),
            'notification_type_periodicity': NotificationBase.objects.create(user=self.myuser, notification_type='Periodic'),
            'dates': f'{past_date}',
            'dates_type': 'Your own dates'
        }

        response = self.c.put(url, invalid_data_date_is_past)
        self.assertEqual(response.status_code, 400)

    def test_delete_notification_periodic_api_another_user_delete_request(self):
        ''' Testing POST request of notification periodic edit page ( choosing `every day`, user is not `author` of this notification )'''
        self.c.login(username=self.another_user_username, password=self.another_user_password)

        request_kwargs = {
            'pk': NotificationPeriodicity.objects.first().id
        }

        url = reverse('notifications_api:edit_notification_periodic_api', kwargs=request_kwargs)

        now = self.now

        # good response
        valid_data = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'edited title',
            'text': 'edited text',
            'notification_periodicity_num': 2,
            'notification_periodic_time': now.time().replace(microsecond=0),
            'notification_type_periodicity': NotificationBase.objects.create(user=self.myuser, notification_type='Periodic'),
            'dates': '',
            'dates_type': 'Every day'
        }

        response = self.c.put(url, valid_data)

        self.assertEqual(response.status_code, 400)

    def test_delete_notification_periodic_api_delete_request(self):
        ''' Testing DELETE request of notification periodic delete page '''
        self.c.login(username=self.username, password=self.password)

        request_kwargs = {
            'pk': NotificationPeriodicity.objects.first().id
        }
        url = reverse('notifications_api:delete_notification_periodic_api', kwargs=request_kwargs)

        old_notifications_count = NotificationPeriodicity.objects.all().count()

        response = self.c.delete(url)

        new_notifications_count = NotificationPeriodicity.objects.all().count()

        self.assertEqual(old_notifications_count, new_notifications_count+1) # 1 0
        self.assertEqual(response.status_code, 204)

    def test_delete_notification_periodic_api_another_user_delete_request(self):
        ''' Testing DELETE request of notification periodic delete page ( user is not `author` of this notification ) '''
        self.c.login(username=self.another_user_username, password=self.another_user_password)

        request_kwargs = {
            'pk': NotificationPeriodicity.objects.first().id
        }
        url = reverse('notifications_api:delete_notification_periodic_api', kwargs=request_kwargs)

        response = self.c.delete(url)

        self.assertEqual(response.status_code, 400)

    def test_notification_periodic_time_stamps_list_api_get_request(self):
        ''' Testing GET request of notification periodic time stamps list api '''
        request_kwargs = {
            'pk': NotificationPeriodicity.objects.first().id
        }
        url = reverse('notifications_api:notification_periodic_time_stamps_list_api', kwargs=request_kwargs)

        # anonymous user
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 403)

        # authenticated user who is not `author` of this notification
        self.c.login(username=self.another_user_username, password=self.another_user_password)
        authenticated_another_user_response = self.c.get(url)
        self.assertEqual(authenticated_another_user_response.status_code, 403)

        # authenticated user who is `author` of this notification
        self.c.login(username=self.username, password=self.password)
        authenticated_myuser_response = self.c.get(url)
        self.assertEqual(authenticated_myuser_response.status_code, 200)

    def test_notification_periodic_revoke_certain_time_stamp_page_delete_request(self):
        ''' Testing DELETE request of periodic notification revoke certain time stamp page '''
        request_kwargs = {
            'pk': NotificationStatus.objects.first().id
        }
        url = reverse('notifications_api:notification_periodic_revoke_certain_time_stamp_api', kwargs=request_kwargs)

        old_status = NotificationStatus.objects.first()
        old_revoked_tasks = app.control.inspect().revoked()

        # authenticated user who is not `author` of the notification
        self.c.login(username=self.username, password=self.password)
        response = self.c.delete(url)

        new_status = NotificationStatus.objects.first()
        new_revoked_tasks = app.control.inspect().revoked()


        self.assertTrue(old_revoked_tasks != new_revoked_tasks)
        self.assertNotEqual(old_status.done, new_status.done) # 0 2
        self.assertEqual(response.status_code, 204)

    def test_notification_periodic_revoke_all_time_stamps_page_delete_request(self):
        ''' Testing POST request of periodic notification delete all time stamps page '''
        request_kwargs = {
            'pk': NotificationPeriodicity.objects.first().id
        }
        url = reverse('notifications_api:notification_periodic_revoke_all_time_stamps_api', kwargs=request_kwargs)
        old_revoked_tasks = app.control.inspect().revoked()
        old_revoked_notif_statuses = self.periodic_notification.notification_status.filter(done=2).count()

        # authenticated user who is not `author` of the notification
        self.c.login(username=self.username, password=self.password)
        response = self.c.delete(url)

        new_revoked_tasks = app.control.inspect().revoked()
        new_revoked_notif_statuses = self.periodic_notification.notification_status.filter(done=2).count()
        
        self.assertEqual(old_revoked_notif_statuses+self.notification_periodicity_num, new_revoked_notif_statuses)
        self.assertTrue(old_revoked_tasks != new_revoked_tasks)
        self.assertEqual(response.status_code, 204)

    def test_notification_periodic_change_notification_status_from_revoke_to_incomplete_api_post_request(self):
        ''' Testing POST request of changing notification status from revoked to non complited ( if date is not in the past ) '''
        request_kwargs = {
            'pk': NotificationStatus.objects.first().id
        }
        status = NotificationStatus.objects.first()
        status.done = 2
        status.save()
        old_celery_id = NotificationId.objects.filter(notification_id=status.notification_celery_id).exists()
        url = reverse('notifications_api:change_notification_status_from_revoke_to_incomplete_api', kwargs=request_kwargs)

        self.c.login(username=self.username, password=self.password)
        response = self.c.post(url)

        new_celery_id = NotificationId.objects.filter(notification_id=status.notification_celery_id).exists()

        self.assertNotEqual(old_celery_id, new_celery_id)
        self.assertEqual(response.status_code, 200)