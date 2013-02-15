from optparse import make_option
from django.contrib.auth.models import User
from django.core.management import BaseCommand
from mtrack.models import Access

__author__ = 'kenneth'


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-n', '--name', dest='name'),
        make_option('-p', '--password', dest='password'),
    )

    def handle(self, **options):
        unicef = User.objects.get(username='UNICEF')
        urls = ['^cvs/facility/$', '^cvs/reporter/$', '^cvs/messagelog/$', '^cvs/massmessages/$']
        name = options.get('name', '')
        password = options.get('password', "")

        if not name or not password:
            print "please provide both username and password like\n--name=username --password=password"
            return

        user = User.objects.create(username=name)
        user.set_password(password)
        user.save()
        for p in unicef.user_permissions.all():
            user.user_permissions.add(p)
            print '=====> Giving user permission', p
        for url in urls:
            access = Access.objects.create(user=user, url_allowed=url)
            print '=====> Giving user access to resource', url
            access.save()
        print '======> user', user.username, 'created'

