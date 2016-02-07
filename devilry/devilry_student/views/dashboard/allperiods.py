from __future__ import unicode_literals

from django.utils.translation import pgettext_lazy, ugettext_lazy
from django_cradmin import crapp
from django_cradmin.viewhelpers import listbuilderview
from django_cradmin.viewhelpers import listfilter

from devilry.apps.core import models as coremodels
from devilry.devilry_cradmin import devilry_listbuilder


class PeriodItemFrame(devilry_listbuilder.common.GoForwardLinkItemFrame):
    valuealias = 'period'

    def get_url(self):
        return '#'
        # return reverse_cradmin_url(
        #     instanceid='devilry_student_period',
        #     appname='feedbackfeed',
        #     roleid=self.group.id,
        #     viewname=crapp.INDEXVIEW_NAME,
        # )

    def get_extra_css_classes_list(self):
        return ['devilry-student-listbuilder-period-itemframe']


class AllPeriodsView(listbuilderview.FilterListMixin, listbuilderview.View):
    model = coremodels.Period
    paginate_by = 30
    template_name = 'devilry_student/cradmin_student/allperiods/allperiods.django.html'
    value_renderer_class = devilry_listbuilder.period.StudentItemValue
    frame_renderer_class = PeriodItemFrame

    def get_pagetitle(self):
        return pgettext_lazy('student allperiods', 'Your courses')

    def get_filterlist_url(self, filters_string):
        return self.request.cradmin_app.reverse_appurl(
            crapp.INDEXVIEW_NAME,
            kwargs={'filters_string': filters_string})

    def add_filterlist_items(self, filterlist):
        filterlist.append(listfilter.django.single.textinput.Search(
            slug='search',
            label=ugettext_lazy('Search'),
            label_is_screenreader_only=True,
            modelfields=[
                'long_name',
                'short_name',
                'parentnode__long_name',
                'parentnode__short_name',
            ]))

    def get_unfiltered_queryset_for_role(self, role):
        return coremodels.Period.objects\
            .filter_user_is_relatedstudent(user=self.request.user)\
            .filter_has_started()\
            .extra_annotate_with_assignmentcount_for_studentuser(user=self.request.user)\
            .extra_annotate_with_user_qualifies_for_final_exam(user=self.request.user)\
            .select_related('parentnode')\
            .order_by('-start_time', 'parentnode__long_name')

    def get_no_items_message(self):
        return pgettext_lazy('student allperiods',
                             'You are not registered on any courses in Devilry.')


class App(crapp.App):
    appurls = [
        crapp.Url(r'^(?P<filters_string>.+)?$',
                  AllPeriodsView.as_view(),
                  name=crapp.INDEXVIEW_NAME),
    ]
