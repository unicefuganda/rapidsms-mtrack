from django import forms
from healthmodels.models.HealthFacility import HealthFacility, HealthFacilityType
from rapidsms.contrib.locations.models import Location
from rapidsms_httprouter.models import Message
from .models import AnonymousReport
from generic.forms import ActionForm
from contact.forms import SMSInput
from .utils import get_district_for_facility

class FacilityResponseForm(forms.Form):
    def __init__(self, data=None, **kwargs):
        response = kwargs.pop('response')
        if data:
            forms.Form.__init__(self, data, **kwargs)
        else:
            forms.Form.__init__(self, **kwargs)

    value = forms.ModelChoiceField(queryset=HealthFacility.objects.order_by('name'))

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
    facility_district = forms.ModelChoiceField(queryset=Location.objects.filter(type__name='district').order_by('name'), empty_label='----', required=False, \
                                      widget=forms.Select({'onchange':'update_facility_district(this)'}))
    


    def __init__(self, *args, **kwargs):
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
    
    def __init__(self, *args, **kwargs):
        super(EditAnonymousReportForm, self).__init__(*args, **kwargs)
        catchment_areas = Location.objects.filter(type__name="district").order_by('name')
        self.fields['district'].queryset = catchment_areas        
        self.fields['facility'].queryset = HealthFacility.objects.filter()
class ReplyTextForm(ActionForm):
    text = forms.CharField(required=True, widget=SMSInput())
    action_label = 'Reply to selected'

    def perform(self, request, results):
        if results is None or len(results) == 0:
            return ('A message must have one or more recipients!', 'error')

        if request.user and request.user.has_perm('contact.can_message'):
            text = self.cleaned_data['text']            
            for anonymous_report in results:
                Message.objects.create(direction="O",
                                       text=text,
                                       connection=anonymous_report.message.connection,
                                       status="Q",
                                       in_response_to=anonymous_report.message                                
                                       )
                return ("%d messages sent successfully" % results.count, 'success')
        else:
            return ("You don't have permission to send messages!", "error")
                