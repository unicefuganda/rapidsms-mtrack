from optparse import make_option
from django.contrib.auth.models import User
from django.core.management import BaseCommand
from mtrack.models import Access

__author__ = 'kenneth'

class Command(BaseCommand):


    option_list = BaseCommand.option_list + (
        make_option('-n', '--name', dest='name'),
        make_option('-p','--password',dest='password'),
        )

    def handle(self, **options):
        urls = ['^cvs/facility/$','^cvs/reporter/$','^cvs/messagelog/$','^cvs/massmessages/$']
        name = options.get('name','')
        password = options.get('password',"")

        if not name or not password:
            print "please provide both username and password like\n--name=username --password=password"
            return

        user = User.objects.create(username = name)
        user.set_password(password)
        user.save()
        for url in urls:
            access = Access.objects.create(user=user,url_allowed=url)
            access.save()
        print '======> user', user.username, 'created'
        print '======>', user.username,'can access the following resources', urls

