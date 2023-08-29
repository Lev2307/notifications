from django.test import TestCase, Client, RequestFactory
from datetime import datetime, timedelta
from django.urls import reverse

from config.celery import app
from authentication.models import MyUser, ChooseSendingNotifications
from notification_categories.models import NotificationCategory
from ..models import NotificationBase, NotificationSingle, NotificationStatus, NotificationPeriodicity, NotificationId

# Create your tests here.
class NotificationGeneralViewsTests(TestCase):

    @classmethod
    def setUp(cls):
        cls.username = 'admin_name'
        cls.email = 'admin_email@gmail.com'
        cls.password = 'admin'
        cls.basic_user = MyUser(username=cls.username, email=cls.email)
        cls.basic_user.set_password(cls.password)
        cls.basic_user.save()
        cls.c = Client()

    def test_list_of_incomplete_notifications_get_request(self):
        ''' Testing all notifications (single and periodic) list page GET request '''
        # anonymous user
        url = reverse('notifications:notification_list')
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 302)

        # logged in
        self.c.login(username=self.username, password=self.password)
        
        authenticated_response = self.c.get(url)
        self.assertEqual(authenticated_response.status_code, 200)

    def test_list_of_finished_notifications_get_request(self):
        ''' Testing all finished notifications (single and periodic) list page GET request '''
        # anonymous user
        url = reverse('notifications:notification_archive_list')
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 302)

        # logged in
        self.c.login(username=self.username, password=self.password)
        
        authenticated_response = self.c.get(url)
        self.assertEqual(authenticated_response.status_code, 200)

    def test_search_notifications_page_get_request(self):
        ''' Testing GET request of search notifications page '''
        # anonymous user
        url = reverse('notifications:search_results')
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 302)

        # logged in
        self.c.login(username=self.username, password=self.password)
        
        authenticated_response = self.c.get(url)
        self.assertEqual(authenticated_response.status_code, 200)


    @classmethod
    def tearDownClass(cls):
        super(NotificationGeneralViewsTests, cls).tearDownClass()
        cls.basic_user.delete()

class NotificationSingleViewsTests(TestCase):
    @classmethod
    def setUp(cls):
        cls.username = 'admin_name_single'
        cls.email = 'admin_email@gmail.com'
        cls.password = 'admin_single'

        cls.another_user_username = 'user_name_single'
        cls.another_user_email = 'user_email@gmail.com'
        cls.another_user_password = 'user_single'

        cls.myuser = MyUser.objects.create(username=cls.username, email=cls.email)
        cls.myuser.set_password(cls.password)
        cls.myuser.save()

        cls.network_telegram = ChooseSendingNotifications.objects.create(sender='telegram', user=cls.myuser, active=True, linked_network=True)
        cls.network_email = ChooseSendingNotifications.objects.create(sender='email', user=cls.myuser)
        cls.myuser.choose_sending.add(cls.network_telegram)
        cls.myuser.choose_sending.add(cls.network_email)
        cls.myuser.save()

        cls.another_user = MyUser.objects.create(username=cls.another_user_username, email=cls.another_user_email)
        cls.another_user.set_password(cls.another_user_password)
        cls.another_user.save()

        cls.now = datetime.now().replace(microsecond=0)
        cls.notification_category_test_type = 'test single type'
        cls.test_title = 'test title'
        cls.test_color = '#f8f8f8'    
        cls.test_text = 'test text'
        cls.c = Client()
        cls.factory = RequestFactory()

        cls.notification_category = NotificationCategory.objects.create(
            user=cls.myuser,
            name_type=cls.notification_category_test_type,
            color=cls.test_color
        )
        cls.notification_status_single = NotificationStatus.objects.create()
        cls.notification_status_single.save()

        cls.type_single = NotificationBase.objects.create(
            user=cls.myuser,
            notification_type='Single'
        )
        cls.type_single.save()

        cls.notification_single = NotificationSingle.objects.create(
            notification_category=cls.notification_category,
            title=cls.test_title,
            text=cls.test_text,
            notification_date=(cls.now).date(),
            notification_time=(cls.now).time(),
            notification_status=cls.notification_status_single,
            notification_type_single=cls.type_single
        )


    def test_notification_single_detail_page_get_request(self):
        ''' Testing detail page of notification single GET request '''
        response_kwargs = {
            'pk': self.notification_single.id
        }
        url = reverse('notifications:detail_single_notification', kwargs=response_kwargs)

        #anonymous user
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 302)

        #another user who didn`t create this single notification
        self.c.login(username=self.another_user_username, password=self.another_user_password)
        another_user_response = self.c.get(url)
        self.assertEqual(another_user_response.status_code, 302)
        self.c.logout()

        # the 'author' of the created notification
        self.c.login(username=self.username, password=self.password)
        myuser_response = self.c.get(url)
        self.assertEqual(myuser_response.status_code, 200)
        self.c.logout()
    
    def test_notification_single_create_page_get_request(self):
        ''' Testing GET method of notification_single_create_page '''
        url = reverse('notifications:create_notification')

        # anonymous user
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 302)

        # authenticated 
        self.c.login(username=self.username, password=self.password)
        authenticated_response = self.c.get(url)
        self.assertEqual(authenticated_response.status_code, 200)

    def test_notification_single_create_page_post_request(self):
        ''' Testing POST method of notification_single_create_page '''
        from ..views import NotificationSingleCreateView
        url = reverse('notifications:create_notification')
        old_single_notifications_count = NotificationSingle.objects.all().count()
        old_celery_ids = NotificationId.objects.all().count()

        data = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'new test title',
            'text': 'new test text',
            'notification_date': self.now.date(),
            'notification_time': (self.now + timedelta(minutes=30)).time(),
            'notification_status': NotificationStatus.objects.create(),
            'notification_type_single': NotificationBase.objects.create(user=self.myuser, notification_type='Single')
        }
        request = self.factory.post(url, data)
        request.user = self.myuser

        response = NotificationSingleCreateView.as_view()(request)

        new_single_notifications_count = NotificationSingle.objects.all().count()
        new_celery_ids = NotificationId.objects.all().count()
        new_single_notification = NotificationSingle.objects.get(title='new test title')
        
        self.assertEqual(old_celery_ids+1, new_celery_ids)
        self.assertEqual(old_single_notifications_count+1, new_single_notifications_count)
        self.assertEqual(new_single_notification.notification_category.id, data['notification_category'])
        self.assertEqual(new_single_notification.title, data['title'])
        self.assertEqual(new_single_notification.text, data['text'])
        self.assertEqual(new_single_notification.notification_date, data['notification_date'])
        self.assertEqual(new_single_notification.notification_time, data['notification_time'])
        self.assertEqual(response.status_code, 302)

    def test_notification_single_edit_page_get_request(self):
        ''' Testing GET request of notification single edit page '''
        request_kwargs = {
            'pk': NotificationSingle.objects.first().id
        }
        url = reverse('notifications:edit_notification', kwargs=request_kwargs)
        # anonymous user
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 302)

        # authenticated user who is not `author` of the notification
        self.c.login(username=self.another_user_username, password=self.another_user_password)
        authenticated_another_user_response = self.c.get(url)

        self.assertEqual(authenticated_another_user_response.status_code, 302)
        self.assertEqual(authenticated_another_user_response.url, reverse('notifications:notification_list'))
        self.c.logout()

        #authenticated user who is `author` of the notification
        self.c.login(username=self.username, password=self.password)
        authenticated_another_user_response = self.c.get(url)
        self.assertEqual(authenticated_another_user_response.status_code, 200)
        self.c.logout()

    def test_notification_single_edit_page_post_request(self):
        ''' Testing GET request of notification single edit page '''
        request_kwargs = {
            'pk': NotificationSingle.objects.first().id
        }
        url = reverse('notifications:edit_notification', kwargs=request_kwargs)  

        old_notification = NotificationSingle.objects.first()
        data = {
            'notification_category': NotificationCategory.objects.get(name_type='work').id,
            'title': 'edited test title',
            'text': 'edited test text',
            'notification_date': (self.now + timedelta(days=2)).date(),
            'notification_time': (self.now + timedelta(minutes=50)).time(),
            'notification_status': NotificationStatus.objects.create(),
            'notification_type_single': NotificationBase.objects.create(user=self.myuser, notification_type='Single')
        }
        self.c.login(username=self.username, password=self.password)
        response = self.c.post(url, data)

        new_notification = NotificationSingle.objects.first()

        self.assertNotEqual(new_notification.notification_category, old_notification.notification_category)
        self.assertNotEqual(new_notification.title, old_notification.title)
        self.assertNotEqual(new_notification.text, old_notification.text)
        self.assertNotEqual(new_notification.notification_date, old_notification.notification_date)
        self.assertNotEqual(new_notification.notification_time, old_notification.notification_time)
        self.assertEqual(response.status_code, 302)

    def test_notification_single_delete_page_get_request(self):
        ''' Testing GET request of notification single delete page '''
        request_kwargs = {
            'pk': NotificationSingle.objects.first().id
        }
        url = reverse('notifications:delete_notification', kwargs=request_kwargs)
        # anonymous user
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 302)

        # authenticated user who is not `author` of the notification
        self.c.login(username=self.another_user_username, password=self.another_user_password)
        authenticated_another_user_response = self.c.get(url)
        self.assertEqual(authenticated_another_user_response.status_code, 302)
        self.assertEqual(authenticated_another_user_response.url, reverse('notifications:notification_list'))
        self.c.logout()

        #authenticated user who is `author` of the notification
        self.c.login(username=self.username, password=self.password)
        authenticated_another_user_response = self.c.get(url)
        self.assertEqual(authenticated_another_user_response.status_code, 200)
        self.c.logout()    

    def test_notification_single_delete_page_post_request(self):
        ''' Testing GET request of notification single edit page '''
        request_kwargs = {
            'pk': NotificationSingle.objects.first().id
        }
        url = reverse('notifications:delete_notification', kwargs=request_kwargs)

        old_notifications_count = NotificationSingle.objects.all().count()

        self.c.login(username=self.username, password=self.password)
        response = self.c.post(url)

        new_notifications_count = NotificationSingle.objects.all().count()

        self.assertEqual(old_notifications_count, new_notifications_count+1) # 1 0
        self.assertEqual(response.status_code, 302)

    @classmethod
    def tearDownClass(cls):
        super(NotificationSingleViewsTests, cls).tearDownClass()
        cls.notification_category.delete()
        cls.notification_status_single.delete()
        cls.notification_single.delete()
        cls.type_single.delete()

class NotificationPeriodicViewsTests(TestCase):
    @classmethod
    def setUp(cls):
        cls.username = 'admin_name_periodic'
        cls.email = 'admin_email@gmail.com'
        cls.password = 'admin_periodic'

        cls.another_user_username = 'user_name_periodic'
        cls.another_user_email = 'user_email@gmail.com'
        cls.another_user_password = 'user_periodic'

        cls.myuser = MyUser.objects.create(username=cls.username, email=cls.email)
        cls.myuser.set_password(cls.password)
        cls.myuser.save()

        cls.network_telegram = ChooseSendingNotifications.objects.create(sender='telegram', user=cls.myuser, active=True, linked_network=True)
        cls.network_email = ChooseSendingNotifications.objects.create(sender='email', user=cls.myuser)
        cls.myuser.choose_sending.add(cls.network_telegram)
        cls.myuser.choose_sending.add(cls.network_email)
        cls.myuser.save()

        cls.another_user = MyUser.objects.create(username=cls.another_user_username, email=cls.another_user_email)
        cls.another_user.set_password(cls.another_user_password)
        cls.another_user.save()

        cls.now = datetime.now().replace(microsecond=0)
        cls.notification_category_test_type = 'test periodic type'
        cls.test_color = '#f8f8f8'    
        cls.test_title = 'test periodic title'
        cls.test_text = 'test periodic text'
        cls.notification_periodic_time = (cls.now + timedelta(minutes=30)).time()
        cls.notification_periodicity_num = 4
        cls.dates = [(cls.now.date() + timedelta(days=i)) for i in range(1, cls.notification_periodicity_num+1)]
        cls.c = Client()
        cls.factory = RequestFactory()

        cls.notification_category = NotificationCategory.objects.create(
            user=cls.myuser,
            name_type=cls.notification_category_test_type,
            color=cls.test_color
        )
        cls.type_periodic = NotificationBase.objects.create(
            user=cls.myuser,
            notification_type='Periodic'
        )
        cls.type_periodic.save()
        cls.c = Client()
        cls.factory = RequestFactory()

        cls.notification_periodic = NotificationPeriodicity.objects.create(
            notification_category=cls.notification_category,
            title=cls.test_title,
            text=cls.test_text,
            notification_periodicity_num=cls.notification_periodicity_num,
            notification_periodic_time=cls.notification_periodic_time,
            notification_type_periodicity=cls.type_periodic,
            dates=cls.dates
        )

    def test_notification_periodic_detail_page_get_request(self):
        ''' Testing notification periodic detail page get request '''
        request_kwargs = {
            'pk': self.notification_periodic.id
        }
        url = reverse('notifications:detail_periodic_notification', kwargs=request_kwargs)

        # anonymous user
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 302)

        # authenticated user whos is not `author` of the notification
        self.c.login(username=self.another_user_username, password=self.another_user_password)
        another_user_response = self.c.get(url)
        self.assertEqual(another_user_response.status_code, 302)
        self.assertEqual(another_user_response.url, reverse('notifications:notification_list'))
        self.c.logout()

        # authenticated user whos is `author` of the notification
        self.c.login(username=self.username, password=self.password)
        response = self.c.get(url)
        self.assertEqual(response.status_code, 200)

    def test_periodic_notification_create_page_get_request(self):
        ''' Testing GET method of notification_periodic_create_page '''
        url = reverse('notifications:create_periodical_notification')

        # anonymous user
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 302)

        # authenticated 
        self.c.login(username=self.username, password=self.password)
        authenticated_response = self.c.get(url)
        self.assertEqual(authenticated_response.status_code, 200)

    def test_periodic_notification_create_page_post_request_every_day(self):
        ''' Testing POST method of notification_periodc_create_page ( every day choice )'''
        from ..views import PeriodicalNotificationCreateView
        url = reverse('notifications:create_periodical_notification')
        old_periodic_notifications_count = NotificationPeriodicity.objects.all().count()
        old_celery_ids = NotificationId.objects.all().count()

        data = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'new test periodic title every day',
            'text': 'new test periodic text',
            'notification_periodic_time': (self.now + timedelta(minutes=50)).time(),
            'notification_periodicity_num': 2,
            'notification_type_periodicity': NotificationBase.objects.create(user=self.myuser, notification_type='Periodic'),
            'dates_type': 'Every day'
        }
        request = self.factory.post(url, data)
        request.user = self.myuser

        response = PeriodicalNotificationCreateView.as_view()(request)

        new_periodic_notifications_count = NotificationPeriodicity.objects.all().count()

        new_celery_ids = NotificationId.objects.all().count()

        new_periodic_notification = NotificationPeriodicity.objects.get(title='new test periodic title every day')
        
        self.assertEqual(old_celery_ids+data['notification_periodicity_num'], new_celery_ids)
        self.assertEqual(old_periodic_notifications_count+1, new_periodic_notifications_count)
        self.assertEqual(new_periodic_notification.notification_category.id, data['notification_category'])
        self.assertEqual(new_periodic_notification.title, data['title'])
        self.assertEqual(new_periodic_notification.text, data['text'])
        self.assertEqual(response.status_code, 302)

    def test_periodic_notification_create_page_post_request_own_dates(self):
        ''' Testing POST method of notification_periodc_create_page ( own dates choice )'''
        from ..views import PeriodicalNotificationCreateView
        url = reverse('notifications:create_periodical_notification')
        old_periodic_notifications_count = NotificationPeriodicity.objects.all().count()

        old_celery_ids = NotificationId.objects.all().count()

        data = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'new test periodic title',
            'text': 'new test periodic text',
            'notification_periodic_time': (self.now + timedelta(minutes=50)).time(),
            'notification_periodicity_num': 1,
            'notification_type_periodicity': NotificationBase.objects.create(user=self.myuser, notification_type='Periodic'),
            'dates': [(self.now.date() + timedelta(days=i+2)) for i in range(1, 3)],
            'dates_type': 'Your own dates'
        }
        request = self.factory.post(url, data)
        request.user = self.myuser

        response = PeriodicalNotificationCreateView.as_view()(request)
        new_periodic_notifications_count = NotificationPeriodicity.objects.all().count()

        new_celery_ids = NotificationId.objects.all().count()

        new_periodic_notification = NotificationPeriodicity.objects.get(title='new test periodic title')
        
        self.assertEqual(old_periodic_notifications_count+1, new_periodic_notifications_count)
        self.assertEqual(old_celery_ids+1, new_celery_ids)
        self.assertEqual(new_periodic_notification.notification_category.id, data['notification_category'])
        self.assertEqual(new_periodic_notification.title, data['title'])
        self.assertEqual(new_periodic_notification.text, data['text'])
        self.assertEqual(response.status_code, 302)

    def test_periodic_notification_edit_page_get_request(self):
        ''' Testing GET method of notification_periodic_edit_page '''
        request_kwargs = {
            'pk': self.notification_periodic.id
        }
        url = reverse('notifications:edit_periodic_notification', kwargs=request_kwargs)

        # anonymous user
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 302)

        # authenticated user who is not `author` of the notification
        self.c.login(username=self.another_user_username, password=self.another_user_password)
        authenticated_another_user_response = self.c.get(url)

        self.assertEqual(authenticated_another_user_response.status_code, 302)
        self.assertEqual(authenticated_another_user_response.url, reverse('notifications:notification_list'))
        self.c.logout()

        #authenticated user who is `author` of the notification
        self.c.login(username=self.username, password=self.password)
        authenticated_another_user_response = self.c.get(url)
        self.assertEqual(authenticated_another_user_response.status_code, 200)
        self.c.logout()

    def test_periodic_notification_edit_page_post_request_every_day(self):
        ''' Testing POST method of notification_periodc_edit_page ( every day choice )'''
        self.c.login(username=self.username, password=self.password)
        request_kwargs = {
            'pk': self.notification_periodic.id
        }
        url = reverse('notifications:edit_periodic_notification', kwargs=request_kwargs)

        data = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'edited test periodic title every day',
            'text': 'edited test periodic text',
            'notification_periodic_time': (self.now + timedelta(minutes=50)).time(),
            'notification_periodicity_num': 2,
            'notification_type_periodicity': NotificationBase.objects.create(user=self.myuser, notification_type='Periodic'),
            'dates_type': 'Every day'
        }
        response = self.c.post(url, data)

        new_periodic_notification = NotificationPeriodicity.objects.get(title='edited test periodic title every day')
        
        self.assertEqual(new_periodic_notification.notification_category.id, data['notification_category'])
        self.assertEqual(new_periodic_notification.title, data['title'])
        self.assertEqual(new_periodic_notification.text, data['text'])
        self.assertEqual(response.status_code, 302)

    def test_periodic_notification_edit_page_post_request_own_dates(self):
        ''' Testing POST method of notification_periodc_edit_page ( every day choice )'''
        self.c.login(username=self.username, password=self.password)
        request_kwargs = {
            'pk': self.notification_periodic.id
        }
        url = reverse('notifications:edit_periodic_notification', kwargs=request_kwargs)

        data = {
            'notification_category': NotificationCategory.objects.get(name_type='study').id,
            'title': 'edited test periodic title every day',
            'text': 'edited test periodic text',
            'notification_periodic_time': (self.now + timedelta(minutes=50)).time(),
            'notification_periodicity_num': 2,
            'dates': [(self.now.date() + timedelta(days=i+2)) for i in range(1, 3)],
            'notification_type_periodicity': NotificationBase.objects.create(user=self.myuser, notification_type='Periodic'),
            'dates_type': 'Your own dates'
        }
        response = self.c.post(url, data)

        new_periodic_notification = NotificationPeriodicity.objects.get(title='edited test periodic title every day')
        
        self.assertEqual(new_periodic_notification.notification_category.id, data['notification_category'])
        self.assertEqual(new_periodic_notification.title, data['title'])
        self.assertEqual(new_periodic_notification.text, data['text'])
        self.assertEqual(response.status_code, 302)

        # self.assertEqual(response.status_code, 302)

    def test_notification_periodic_delete_page_get_request(self):
        ''' Testing GET request of notification periodic delete page '''
        request_kwargs = {
            'pk': NotificationPeriodicity.objects.first().id
        }
        url = reverse('notifications:delete_periodic_notification', kwargs=request_kwargs)
        # anonymous user
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 302)

        # authenticated user who is not `author` of the notification
        self.c.login(username=self.another_user_username, password=self.another_user_password)
        authenticated_another_user_response = self.c.get(url)

        self.assertEqual(authenticated_another_user_response.status_code, 302)
        self.assertEqual(authenticated_another_user_response.url, reverse('notifications:notification_list'))
        self.c.logout()

        #authenticated user who is `author` of the notification
        self.c.login(username=self.username, password=self.password)
        authenticated_another_user_response = self.c.get(url)
        self.assertEqual(authenticated_another_user_response.status_code, 200)
        self.c.logout()   

    def test_notification_periodic_delete_page_post_request(self):
        ''' Testing POST request of notification periodic edit page '''
        request_kwargs = {
            'pk': NotificationPeriodicity.objects.first().id
        }
        url = reverse('notifications:delete_periodic_notification', kwargs=request_kwargs)

        old_notifications_count = NotificationPeriodicity.objects.all().count()

        self.c.login(username=self.username, password=self.password)
        response = self.c.post(url)

        new_notifications_count = NotificationPeriodicity.objects.all().count()

        self.assertEqual(old_notifications_count, new_notifications_count+1) # 1 0
        self.assertEqual(response.status_code, 302)

    def test_notification_periodic_time_stamps_list_page_get_request(self):
        ''' Testing GET request of periodic notification time stamps list page '''
        request_kwargs = {
            'pk': NotificationPeriodicity.objects.first().id
        }
        url = reverse('notifications:notification_periodic_time_stamps_list', kwargs=request_kwargs)
        # anonymous user
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 302)

        # authenticated user who is not `author` of the notification
        self.c.login(username=self.another_user_username, password=self.another_user_password)
        authenticated_another_user_response = self.c.get(url)

        self.assertEqual(authenticated_another_user_response.status_code, 302)
        self.assertEqual(authenticated_another_user_response.url, reverse('notifications:notification_list'))
        self.c.logout()

        #authenticated user who is `author` of the notification
        self.c.login(username=self.username, password=self.password)
        authenticated_another_user_response = self.c.get(url)
        self.assertEqual(authenticated_another_user_response.status_code, 200)
        self.c.logout()  

        #authenticated user who is `author` of the notification
        self.c.login(username=self.username, password=self.password)
        authenticated_another_user_response = self.c.get(url)
        self.assertEqual(authenticated_another_user_response.status_code, 200)
        self.c.logout()    

    def test_notification_periodic_delete_certain_time_stamp_page_get_request(self):
        ''' Testing GET request of periodic notification delete certain time stamp page '''
        request_kwargs = {
            'pk': NotificationStatus.objects.first().id
        }
        url = reverse('notifications:notification_periodic_revoke_certain_time_stamp', kwargs=request_kwargs)

        # anonymous user
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 302)

        # authenticated user who is not `author` of the notification
        self.c.login(username=self.another_user_username, password=self.another_user_password)
        authenticated_another_user_response = self.c.get(url)

        self.assertEqual(authenticated_another_user_response.status_code, 302)
        self.assertEqual(authenticated_another_user_response.url, reverse('notifications:notification_list'))
        self.c.logout()

        #authenticated user who is `author` of the notification
        self.c.login(username=self.username, password=self.password)
        authenticated_another_user_response = self.c.get(url)
        self.assertEqual(authenticated_another_user_response.status_code, 200)
        self.c.logout()   

    def test_notification_periodic_delete_certain_time_stamp_page_post_request(self):
        ''' Testing POST request of periodic notification delete certain time stamp page '''
        request_kwargs = {
            'pk': NotificationStatus.objects.first().id
        }
        url = reverse('notifications:notification_periodic_revoke_certain_time_stamp', kwargs=request_kwargs)

        old_status = NotificationStatus.objects.first()
        old_revoked_tasks = app.control.inspect().revoked()

        # authenticated user who is not `author` of the notification
        self.c.login(username=self.username, password=self.password)
        response = self.c.post(url)

        new_status = NotificationStatus.objects.first()
        new_revoked_tasks = app.control.inspect().revoked()

        self.assertTrue(old_revoked_tasks != new_revoked_tasks)
        self.assertNotEqual(old_status.done, new_status.done) # 0 2
        self.assertEqual(response.status_code, 302)

    def test_notification_periodic_delete_all_time_stamps_page_get_request(self):
        ''' Testing GET request of periodic notification delete all time stamps page '''
        request_kwargs = {
            'pk': NotificationPeriodicity.objects.first().id
        }
        url = reverse('notifications:notification_periodic_revoke_all_time_stamps', kwargs=request_kwargs)

        # anonymous user
        anonymous_response = self.c.get(url)
        self.assertEqual(anonymous_response.status_code, 302)

        # authenticated user who is not `author` of the notification
        self.c.login(username=self.another_user_username, password=self.another_user_password)
        authenticated_another_user_response = self.c.get(url)

        self.assertEqual(authenticated_another_user_response.status_code, 302)
        self.assertEqual(authenticated_another_user_response.url, reverse('notifications:notification_list'))
        self.c.logout()

        #authenticated user who is `author` of the notification
        self.c.login(username=self.username, password=self.password)
        authenticated_another_user_response = self.c.get(url)
        self.assertEqual(authenticated_another_user_response.status_code, 200)
        self.c.logout()  

    def test_notification_periodic_delete_all_time_stamps_page_post_request(self):
        ''' Testing POST request of periodic notification delete all time stamps page '''
        request_kwargs = {
            'pk': NotificationPeriodicity.objects.first().id
        }
        url = reverse('notifications:notification_periodic_revoke_all_time_stamps', kwargs=request_kwargs)
        old_revoked_tasks = app.control.inspect().revoked()
        old_revoked_notif_statuses = self.notification_periodic.notification_status.filter(done=2).count()

        # authenticated user who is not `author` of the notification
        self.c.login(username=self.username, password=self.password)
        response = self.c.post(url)

        new_revoked_tasks = app.control.inspect().revoked()
        new_revoked_notif_statuses = self.notification_periodic.notification_status.filter(done=2).count()

        self.assertEqual(old_revoked_notif_statuses+self.notification_periodicity_num, new_revoked_notif_statuses)
        self.assertTrue(old_revoked_tasks != new_revoked_tasks)
        self.assertEqual(response.status_code, 302)

    def test_notification_periodic_change_notification_status_from_revoke_to_incomplete_post_request(self):
        ''' Testing POST request of changing notification status from revoked to non complited ( if date is not in the past ) '''
        request_kwargs = {
            'pk': NotificationStatus.objects.first().id
        }
        status = NotificationStatus.objects.first()
        status.done = 2
        status.save()
        old_celery_id = NotificationId.objects.filter(notification_id=status.notification_celery_id).exists()
        url = reverse('notifications:change_notification_status_from_revoke_to_incomplete', kwargs=request_kwargs)

        self.c.login(username=self.username, password=self.password)
        response = self.c.post(url)

        new_celery_id = NotificationId.objects.filter(notification_id=status.notification_celery_id).exists()

        self.assertNotEqual(old_celery_id, new_celery_id)
        self.assertEqual(response.status_code, 302)

    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.notification_periodic.delete()
        cls.type_periodic.delete()
        cls.notification_category.delete()
        cls.myuser.delete()
        cls.another_user.delete()