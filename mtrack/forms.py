from django import forms
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.db import transaction, connection
from django.db.models import Q
from django.forms.widgets import SelectMultiple, CheckboxSelectMultiple
from healthmodels.models.HealthFacility import HealthFacility, HealthFacilityType
from rapidsms.contrib.locations.models import Location
from rapidsms_httprouter.models import Message
from poll.models import Poll, gettext_db
from .models import AnonymousReport, Schedules, ScheduleExtras
from generic.forms import ActionForm, FilterForm
from contact.forms import SMSInput
from rapidsms_xforms.models import XForm
from .utils import get_district_for_facility

class FacilityResponseForm(forms.Form):
    def __init__(self, data=None, **kwargs):
        if data:
            forms.Form.__init__(self, data, **kwargs)
        else:
            forms.Form.__init__(self, **kwargs)

    value = forms.ModelChoiceField(queryset=HealthFacility.objects.select_related('type').order_by('name'))

class DistrictResponseForm(forms.Form):
    def __init__(self, data=None, **kwargs):
        if data:
            forms.Form.__init__(self, data, **kwargs)
        else:
            forms.Form.__init__(self, **kwargs)

    value = forms.ModelChoiceField(queryset=Location.objects.order_by('name'))


class FacilityForm(forms.Form):
    """
    How we handle an anonymous "complaint" or "report"
    """
    name = forms.CharField(max_length=100, required=True)
    code = forms.CharField(max_length=50, required=False)
    type = forms.ModelChoiceField(queryset=HealthFacilityType.objects.all(), required=True)
    catchment_areas = forms.ModelMultipleChoiceField(queryset=Location.objects.all(), required=False)
    def __init__(self, *args, **kwargs):
        self.username = kwargs.pop('username', '')
        self.facility = kwargs.pop('instance')
        if not 'data' in kwargs:
            initial = { \
                'name':self.facility.name, \
                'code':self.facility.code, \
                'type':self.facility.type, \
                'catchment_areas':self.facility.catchment_areas.all(), \
            }
            district = get_district_for_facility(self.facility)
            if district:
                initial.update({'facility_district':district})
            kwargs.update({'initial':initial})
        forms.Form.__init__(self, *args, **kwargs)
        self.fields['facility_district'] = forms.ModelChoiceField(queryset=self.get_districts_for_form(self.username), empty_label='----', required=False, \
                                      widget=forms.Select({'onchange':'update_facility_district(this)'}))
    def get_districts_for_form(self, user):
        loc = Location.objects.filter(name=str(user).capitalize(), type__name='district')
        if loc:
            return loc
        else:
            return Location.objects.filter(type__name='district').order_by('name')
    def save(self):
        cleaned_data = self.cleaned_data
        self.facility.name = cleaned_data.get('name')
        self.facility.code = cleaned_data.get('code')
        self.facility.type = cleaned_data.get('type')
        self.facility.save()

        self.facility.catchment_areas.clear()
        for c in cleaned_data.get('catchment_areas'):
            self.facility.catchment_areas.add(c)
        return

class EditAnonymousReportForm(forms.ModelForm):
    """
	We can now edit any reports that come in anonymously
	"""
    class Meta:
        model = AnonymousReport
        exclude = ('connection', 'messages', 'date')
        widgets = {
                   'comments': forms.Textarea(attrs={'cols':25, 'rows':3}),
                   'action_taken': forms.Textarea(attrs={'cols':25, 'rows':3}),
                   }

    def __init__(self, *args, **kwargs):
        super(EditAnonymousReportForm, self).__init__(*args, **kwargs)
        self.fields['district'].queryset = Location.objects.filter(type__name="district").order_by("name")
        self.fields['health_facility'].queryset = HealthFacility.objects.all().select_related('type__name').order_by('name')
        # make this non-required
        for key, field in self.fields.iteritems():
            self.fields[key].required = False

class ReplyTextForm(ActionForm):
    text = forms.CharField(required=True, widget=SMSInput())
    action_label = 'Reply to selected'

    def perform(self, request, results):
        if results is None or len(results) == 0:
            return 'A message must have one or more recipients!', 'error'
        if request.user and request.user.has_perm('contact.can_message'):
            text = self.cleaned_data['text']
            for anonymous_report in results:
                try:
                    # responses are still made to the most recent message
                    # unless better way for handling this is found.
                    Message.objects.create(direction="O",
                                       text=text,
                                       connection=anonymous_report.connection,
                                       status="Q",
                                       in_response_to=anonymous_report.messages.all().order_by('-date')[0]
                                       )
                except IndexError:
                    print "no messages got into the anonymous report"
                    pass
            return "%d messages sent successfully" % results.count(), 'success'
        else:
            return "You don't have permission to send messages!", "error"

class MassTextForm(ActionForm):
    pass


# class PollNoContact(Poll):
#    """
#    Sending out a poll without a Contact object (i.e. anonymous users will previously not have registered to use
#    mtrac's other short code. This class contains a method that will create a poll to one or more users. Responses to
#    8200 shortcode in a short time will be tagged as replies to that poll.
#    """
#    @classmethod
#    @transaction.commit_on_success
#    def create_with_bulk(cls, name, type, question, connections, user):
#        # contacts in this case will loosely be connected to just the connection.
#        #contact_ids = [contact.id for contact in contacts]
#        # pass distinct connections
#        Message.mass_text(gettext_db(field=question), connections, status='L')
#        poll = Poll.objects.create(name=name, type=type, question=question, user=user)
#
#        # This is the fastest (pretty much only) was to get contacts and messages M2M into the
#        # DB fast enough at scale
#        cursor = connection.cursor()
#        for language in localized_messages.keys():
#            raw_sql = "insert into poll_poll_contacts (poll_id, contact_id) values %s" % ','.join(\
#                ["(%d, %d)" % (poll.pk, c.pk) for c in localized_messages.get(language)[1]])
#            cursor.execute(raw_sql)
#
#            raw_sql = "insert into poll_poll_messages (poll_id, message_id) values %s" % ','.join(\
#                ["(%d, %d)" % (poll.pk, m.pk) for m in localized_messages.get(language)[0]])
#            cursor.execute(raw_sql)
#
#        if 'django.contrib.sites' in settings.INSTALLED_APPS:
#            poll.sites.add(Site.objects.get_current())
#        return poll


class AskAQuestionForm(ActionForm):
    text = forms.CharField(required=True, widget=SMSInput())
    action_label = "Poll reporters"
    def perform(self, request, results):
        if results is None or len(results):
            return 'A question to reporters must have one or more recipients', 'error'
        if request.user and request.user.has_perm('contact.can_message'):
            text = self.cleaned_data['text']
            for anonymous_reporter in results:
                Message.objects.create(direction="O", text=text, connection=anonymous_reporter.connection, status="Q", in_response_to=anonymous_reporter.message)
                # create a poll to specific user, any response will be shown to mtrac user
                Poll.objects.create()
            return "%d messages sent successfully" % results.count(), 'success'
        else:
            return "You don't have permission to send messages!", "error"


class ApproveForm(ActionForm):
    action_label = 'Approve Selected'
    def perform(self, request, results):
        if results is None or len(results) == 0:
            return 'You must approve one or more reports', 'error'
        if request.user and request.user.has_perm('rapidsms_xforms.can_approve'):
            count = results.count()
            results.update(approved=True)
            return "%d reports approved successfully" % count, 'success'
        else:
            return "You don't have permission to approve reports!", "error"

class RejectForm(ActionForm):
    action_label = 'Reject Selected'
    def perform(self, request, results):
        if results is None or len(results) == 0:
            return 'You must reject one or more reports', 'error'
        if request.user and request.user.has_perm('rapidsms_xforms.can_approve'):
            results.update(has_errors=True)
            return "%d reports rejected successfully" % results.count(), 'success'
        else:
            return "You don't have permission to reject reports", "error"
class StatusFilterForm(FilterForm):
    action = forms.ChoiceField(choices=(('Open', 'Open'),), required=False)
    # def __init__(self, data=None, **kwargs):
    #
    def filter(self, request, queryset):
        action = self.cleaned_data['action']
        return queryset
# Lets Add some data Entry Forms here

# class DataEntryForm(forms.Form):
#    district = forms.ModelChoiceField()
#    facility = forms.ModelChoiceField()
#    reporter = forms.ModelChoiceField()

class ScheduleForm(forms.Form):
    DISTRICT_CHOICES = Location.objects.filter(type__name='district').values_list('name', 'name').order_by('name')
    GROUP_CHOICES = tuple([(g.name, g.name) for g in Group.objects.all().order_by('name')])
    MODE_CHOICES = (('live', 'Live Mode'), ('training', 'Training Mode'), ('all', 'All Users'))
    HOUR_CHOICES = tuple([(h, h) for h in range(24)])
    MINUTES_CHOICES = tuple([(m, m) for m in range(60)])
    XFORM_CHOICES = tuple([(x['keyword'], '%s(%s)' % (x['name'], x['keyword'])) for x in XForm.objects.all().values('id', 'name', 'keyword').order_by('name')])
    MONTH_INTERVAL_CHOICES = (('none', 'No Repeat'), ('day', 'Daily'), ('week', 'Weekly'), ('month', 'Monthly'))
    WEEK_INTERVAL_CHOICES = (('1', 'First Days'), ('2', 'Second Days'), ('3', 'Third Days'), ('4', 'Fourth Days'), ('last', 'Last Days'))
    SETUP_CHOICES = (('basic', 'Basic'), ('temp', 'Has Argument'))
    DAY_INTERVAL_CHOICES = (('mon', 'Monday'), ('tue', 'tue'), ('wed', 'Wednesday'), ('thur', 'Thursday'), ('fri', 'Friday'), ('sat', 'Saturday'), ('sun', 'Sunday'))
    setup = forms.CharField(widget=forms.Select(choices=SETUP_CHOICES, attrs={'class':'required'}))
    locations = forms.MultipleChoiceField(choices=DISTRICT_CHOICES)
    group = forms.MultipleChoiceField(choices=GROUP_CHOICES)
    reporter = forms.MultipleChoiceField(choices=GROUP_CHOICES)
    xforms = forms.MultipleChoiceField(choices=XFORM_CHOICES)
    start_date = forms.DateField(widget=forms.TextInput(attrs={'id':'sdate', 'readonly':'readonly', 'required':'required'}))
    end_date = forms.DateField(widget=forms.TextInput(attrs={'id':'edate', 'readonly':'readonly'}), required=False)
    interval = forms.CharField(widget=forms.Select(choices=MONTH_INTERVAL_CHOICES, attrs={'class':'ftext', 'id':'interval'}))
    week_number = forms.CharField(widget=forms.Select(choices=WEEK_INTERVAL_CHOICES, attrs={'class':'textbox'}))
    repeat_day = forms.MultipleChoiceField(widget=CheckboxSelectMultiple, choices=DAY_INTERVAL_CHOICES, required=False)
    hour = forms.CharField(widget=forms.Select(choices=HOUR_CHOICES, attrs={'id':'hrs', 'style':'min-width:18px'}))
    minutes = forms.CharField(widget=forms.Select(choices=MINUTES_CHOICES, attrs={'id':'mins', 'style':'min-width:18px'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'id':'msg', 'class':'required'}))
    user_type = forms.CharField(widget=forms.Select(choices=MODE_CHOICES))

    def clean(self):
        cleaned_data = super(ScheduleForm, self).clean()
        cleaned_data['start_time'] = '%s:%s' % (self.cleaned_data['hour'], self.cleaned_data['minutes'])
        cleaned_data['msg_is_temp'] = False if self.cleaned_data['setup'] == 'basic' else True
        cleaned_data['group'] = ",".join(cleaned_data['group'])
        cleaned_data['reporter'] = ",".join(cleaned_data['reporter'])
        cleaned_data['xforms'] = ",".join(cleaned_data['xforms'])
        cleaned_data['locations'] = ",".join(cleaned_data['locations'])
        cleaned_data['repeat_day'] = ",".join(cleaned_data['repeat_day'])
        return cleaned_data


    def save(self):
        schedule = Schedules.objects.create(created_by='sam', start_date=self.cleaned_data['start_date'], end_date=self.cleaned_data['end_date'],
            start_time=self.cleaned_data['start_time'], message_type=self.cleaned_data['setup'], message=self.cleaned_data['message'], recur_interval=self.cleaned_data['interval'],
            recur_frequency=0, recur_day=self.cleaned_data['repeat_day'], recur_weeknumber=self.cleaned_data['week_number'])

        extras = ScheduleExtras.objects.create(schedule=schedule, recipient_location_type='',
            recipient_location=self.cleaned_data['locations'], allowed_recipients='', recipient_group_type='',
            missing_reports=self.cleaned_data['xforms'], expected_reporter=self.cleaned_data['reporter'], group_ref=self.cleaned_data['group'],
            is_message_temp=self.cleaned_data['msg_is_temp'], message_args="", return_code="")

        return schedule, extras

    def update(self, id):
        schedule = Schedules.objects.filter(id=id).update(created_by='sam', start_date=self.cleaned_data['start_date'], end_date=self.cleaned_data['end_date'],
            start_time=self.cleaned_data['start_time'], message_type=self.cleaned_data['setup'], message=self.cleaned_data['message'], recur_interval=self.cleaned_data['interval'],
            recur_frequency=0, recur_day=self.cleaned_data['repeat_day'], recur_weeknumber=self.cleaned_data['week_number'])

        extras = ScheduleExtras.objects.filter(schedule=id).update(recipient_location_type='',
            recipient_location=self.cleaned_data['locations'], allowed_recipients='', recipient_group_type='',
            missing_reports=self.cleaned_data['xforms'], expected_reporter=self.cleaned_data['reporter'], group_ref=self.cleaned_data['group'],
            is_message_temp=self.cleaned_data['msg_is_temp'], message_args="", return_code="")



class DistrictFilterForm(FilterForm):

    """ filter cvs districs on their districts """

    district2 = forms.MultipleChoiceField(label="District", choices=(('', '-----'), (-1,
                                                                             'No District')) + tuple([(int(d.pk),
                                                                                                       d.name) for d in
                                                                                                      Location.objects.filter(type__slug='district'
                                                                                                      ).order_by('name')]), required=False,
        widget=forms.SelectMultiple({'onchange':'update_district2(this)'}), help_text="Hold CTRL to select multiple")


    def filter(self, request, queryset):

        district_pk = self.cleaned_data['district2']
        if '' in district_pk and len(district_pk) < 2:
            return queryset
        elif "-1" in district_pk :
            district_pk.remove("-1")
            return queryset.filter(Q(district__in=Location.objects.filter(pk__in=district_pk).values_list('name', flat=True).distinct())
                                   | Q(reporting_location__in=Location.objects.filter(type__in=['country', 'region'])))
        else:
            district = Location.objects.filter(pk__in=district_pk)
            if district:
                return queryset.filter(district__in=district.values_list('name', flat=True).distinct())
                # return queryset.filter(reporting_location__in=district.get_descendants(include_self=True))
            else:
                return queryset

class RolesFilter(FilterForm):
    role = forms.MultipleChoiceField(choices=(('', '----'),) + tuple(Group.objects.values_list('id','name').order_by('name')), required=False)

    def filter(self, request, queryset):
        #import pdb; pdb.set_trace()
        group_pks = self.cleaned_data['role']
        if '' in group_pks and len(group_pks)<2:
            return queryset
        else:
            if '' in group_pks:group_pks.remove('')
            groups = Group.objects.filter(id__in=group_pks).values_list('name',flat=True)
            args = Q()
            for group in groups:
                args.add(Q(groups__contains=group),args.OR)
            queryset = queryset.filter(args)
            if u'VHT' in groups and not u'PVHT' in groups:
                exclusions = []
                for id, grp in queryset.values_list('id','groups'):
                    grp_list = grp.split(',')
                    if u'PVHT' in grp_list and not u'VHT' in grp_list:exclusions.append(id)
                queryset = queryset.exclude(id__in=exclusions)
            return queryset

class RolesFilter(FilterForm):
    role = forms.MultipleChoiceField(choices=(('', '----'),) + tuple(Group.objects.values_list('id', 'name').order_by('name')), required=False)

    def filter(self, request, queryset):
        # import pdb; pdb.set_trace()
        group_pks = self.cleaned_data['role']
        if '' in group_pks and len(group_pks) < 2:
            return queryset
        else:
            if '' in group_pks:group_pks.remove('')
            groups = Group.objects.filter(id__in=group_pks).values_list('name', flat=True)
            args = Q()
            for group in groups:
                args.add(Q(groups__contains=group), args.OR)
            queryset = queryset.filter(args)
            if u'VHT' in groups and not u'PVHT' in groups:
                exclusions = []
                for id, grp in queryset.values_list('id', 'groups'):
                    grp_list = grp.split(',')
                    if u'PVHT' in grp_list and not u'VHT' in grp_list:exclusions.append(id)
                queryset = queryset.exclude(id__in=exclusions)
            return queryset
