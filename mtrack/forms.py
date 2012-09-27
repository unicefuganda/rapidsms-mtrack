from django import forms
from django.db import transaction
from healthmodels.models.HealthFacility import HealthFacility, HealthFacilityType
from rapidsms.contrib.locations.models import Location
from rapidsms_httprouter.models import Message
from poll.models import Poll
from .models import AnonymousReport
from generic.forms import ActionForm, FilterForm
from contact.forms import SMSInput
from .utils import get_district_for_facility, get_facilities

class FacilityResponseForm(forms.Form):
    def __init__(self, data=None, **kwargs):
        response = kwargs.pop('response')
        if data:
            forms.Form.__init__(self, data, **kwargs)
        else:
            forms.Form.__init__(self, **kwargs)

    value = forms.ModelChoiceField(queryset=HealthFacility.objects.select_related('type').order_by('name'))

class DistrictResponseForm(forms.Form):
    def __init__(self, data=None, **kwargs):
        response = kwargs.pop('response')
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
            return ('A message must have one or more recipients!', 'error')
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
            return ("%d messages sent successfully" % results.count(), 'success')
        else:
            return ("You don't have permission to send messages!", "error")

class MassTextForm(ActionForm):
    pass


class PollNoContact(Poll):
    """
    Sending out a poll without a Contact object (i.e. anonymous users will previously not have registered to use
    mtrac's other short code. This class contains a method that will create a poll to one or more users. Responses to
    8200 shortcode in a short time will be tagged as replies to that poll.
    """
    @classmethod
    @transaction.commit_on_success
    def create_with_bulk(cls, name, type, question, connections, user):
        # contacts in this case will loosely be connected to just the connection.
        #contact_ids = [contact.id for contact in contacts]
        # pass distinct connections
        Message.mass_text(gettext_db(field=question), connections, status='L')
        poll = Poll.objects.create(name=name, type=type, question=question, user=user)

        # This is the fastest (pretty much only) was to get contacts and messages M2M into the
        # DB fast enough at scale
        cursor = connection.cursor()
        for language in localized_messages.keys():
            raw_sql = "insert into poll_poll_contacts (poll_id, contact_id) values %s" % ','.join(\
                ["(%d, %d)" % (poll.pk, c.pk) for c in localized_messages.get(language)[1]])
            cursor.execute(raw_sql)

            raw_sql = "insert into poll_poll_messages (poll_id, message_id) values %s" % ','.join(\
                ["(%d, %d)" % (poll.pk, m.pk) for m in localized_messages.get(language)[0]])
            cursor.execute(raw_sql)

        if 'django.contrib.sites' in settings.INSTALLED_APPS:
            poll.sites.add(Site.objects.get_current())
        return poll


class AskAQuestionForm(ActionForm):
    text = forms.CharField(required=True, widget=SMSInput())
    action_label = "Poll reporters"
    def perform(self, request, results):
        if results is None or len(results):
            return ('A question to reporters must have one or more recipients', 'error')
        if request.user and request.user.has_perm('contact.can_message'):
            text = self.cleaned_data['text']
            for anonymous_reporter in results:
                Message.objects.create(direction="O", text=text, connection=anonymous_reporter.connection, status="Q", in_response_to=anonymous_reporter.message)
                # create a poll to specific user, any response will be shown to mtrac user
                Poll.objects.create()
            return ("%d messages sent successfully" % results.count(), 'success')
        else:
            return ("You don't have permission to send messages!", "error")


class ApproveForm(ActionForm):
    action_label = 'Approve Selected'
    def perform(self, request, results):
        if results is None or len(results) == 0:
            return ('You must approve one or more reports', 'error')
        if request.user and request.user.has_perm('rapidsms_xforms.can_approve'):
            count = results.count()
            results.update(approved=True)
            return ("%d reports approved successfully" % count, 'success')
        else:
            return ("You don't have permission to approve reports!", "error")

class RejectForm(ActionForm):
    action_label = 'Reject Selected'
    def perform(self, request, results):
        if results is None or len(results) == 0:
            return ('You must reject one or more reports', 'error')
        if request.user and request.user.has_perm('rapidsms_xforms.can_approve'):
            results.update(has_errors=True)
            return ("%d reports rejected successfully" % results.count(), 'success')
        else:
            return ("You don't have permission to reject reports", "error")
class StatusFilterForm(FilterForm):
    action = forms.ChoiceField(choices=(('Open', 'Open'),), required=False)
    #def __init__(self, data=None, **kwargs):
    #
    def filter(self, request, queryset):
        action = self.cleaned_data['action']
        return queryset
#Lets Add some data Entry Forms here

#class DataEntryForm(forms.Form):
#    district = forms.ModelChoiceField()
#    facility = forms.ModelChoiceField()
#    reporter = forms.ModelChoiceField()

