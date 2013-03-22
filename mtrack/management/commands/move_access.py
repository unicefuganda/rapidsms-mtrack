from django.contrib.auth.models import User
from django.core.management import BaseCommand
from uganda_common.models import Access
from mtrack.models import Access as MAccess

__author__ = 'kenneth'


class Command(BaseCommand):
    def handle(self, *args, **options):
        for user, url in MAccess.objects.values_list('user', 'url_allowed'):
            user = User.objects.get(pk=user)
            Access.objects.add_url(user, url)
            print 'Resource(', url, ') Added to User(', user.username, ')'
