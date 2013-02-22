from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from mtrack.forms import NewPollForm
from mtrack_project.rapidsms_mtrack.mtrack.utils import get_contacts_for_partner
from poll.models import Translation, Poll
from rapidsms.models import Contact
from django.conf import settings

__author__ = 'kenneth'


def new_poll(req):
    if req.method == 'POST':
        form = NewPollForm(req.POST, request=req)
        form.updateTypes()
        if form.is_valid():

            # create our XForm

            question = form.cleaned_data['question']
            default_response = form.cleaned_data['default_response']
            contacts = form.cleaned_data['contacts']
            if hasattr(Contact, 'groups'):
                groups = form.cleaned_data['groups']
                contacts = get_contacts_for_partner(req).filter(Q(pk__in=contacts) | Q(groups__in=groups)).distinct()
            else:
                contacts = Contact.objects.filter(pk__in=contacts)

            name = form.cleaned_data['name']
            p_type = form.cleaned_data['type']

            response_type = form.cleaned_data['response_type']

            if getattr(settings, "LANGUAGES", None):
                langs = dict(settings.LANGUAGES)

                for language in dict(settings.LANGUAGES).keys():
                    if not language == "en":
                        int_default_response = 'default_response_%s' % langs[language]
                        int_question = 'question_%s' % langs[language]
                        if not form.cleaned_data[int_default_response] == '' \
                            and not form.cleaned_data['default_response'] == '':
                            (translation, created) = \
                                Translation.objects.get_or_create(language=language,
                                                                  field=form.cleaned_data['default_response'],
                                                                  value=form.cleaned_data[int_default_response])

                        if not form.cleaned_data[int_question] == '':
                            (translation, created) = \
                                Translation.objects.get_or_create(language=language,
                                                                  field=form.cleaned_data['question'],
                                                                  value=form.cleaned_data[int_question])

            poll_type = (Poll.TYPE_TEXT if p_type == NewPollForm.TYPE_YES_NO else p_type)

            start_immediately = form.cleaned_data['start_immediately']

            poll = Poll.create_with_bulk(
                name,
                poll_type,
                question,
                default_response,
                contacts,
                req.user)

            if type == NewPollForm.TYPE_YES_NO:
                poll.add_yesno_categories()

            if settings.SITE_ID:
                poll.sites.add(Site.objects.get_current())
            if form.cleaned_data['start_immediately']:
                poll.start()

            return redirect(reverse('poll.views.view_poll', args=[poll.pk]))

    else:
        form = NewPollForm(request=req)
        form.updateTypes()

    return render_to_response('polls/poll_create.html', {'form': form},
                              context_instance=RequestContext(req))
