# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from crispy_forms import layout

# Django imports
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django import forms

# CrAdmin imports
from django_cradmin.crispylayouts import PrimarySubmit, DefaultSubmit, CollapsedSectionLayout, CradminSubmitButton
from django_cradmin.viewhelpers import formbase

# Devilry imports
from devilry.devilry_qualifiesforexam import models as status_models
from devilry.apps.core import models as core_models


class QualificationForm(forms.Form):
    pass


class AbstractQualificationPreviewView(formbase.FormView):
    """
    Abstract superclass for preview views
    """

    @classmethod
    def deserialize_preview(cls, serialized):
        pass

    def serialize_preview(self, form):
        pass

    def get_field_layout(self):
        return []

    def get_relatedstudents_queryset(self, period):
        """
        Get all the :class:`~.devilry.apps.core.models.RelatedStudent`s for ``period``.

        Args:
            period: The period to fetch ``RelatedStudent``s for.

        Returns:
            QuerySet: QuerySet for :class:`~.devilry.apps.core.models.RelatedStudent`
        """
        return core_models.RelatedStudent.objects.filter(period=period)


class QualificationPreviewView(AbstractQualificationPreviewView):
    """
    View that lists the current qualification status for students.

    This view lists all the students on the course for this period.
    """
    template_name = 'devilry_qualifiesforexam/preview.django.html'
    form_class = QualificationForm

    def dispatch(self, request, *args, **kwargs):
        """
        Check if a :class:`~.devilry_qualifiesforexam.models.Status` with ``status`` set to
        ``ready`` exists for the period. If it exists, redirect to the final export view.
        """
        status = status_models.Status.objects.order_by('-createtime').first()
        if status:
            if status_models.Status.objects.order_by('-createtime').first().status == status_models.Status.READY:
                # Currently raise Http404, add redirect to view later
                return HttpResponseRedirect(self.request.cradmin_app.reverse_appurl(
                    viewname='show-status',
                    kwargs={
                        'roleid': self.request.cradmin_role.id
                    }
                ))
        return super(QualificationPreviewView, self).dispatch(request, *args, **kwargs)

    def get_buttons(self):
        return [
            DefaultSubmit('back', _('Back')),
            PrimarySubmit('save', _('Save'))
        ]

    def get_context_data(self, **kwargs):
        context_data = super(QualificationPreviewView, self).get_context_data()
        context_data['period'] = self.request.cradmin_role
        context_data['relatedstudents'] = self.get_relatedstudents_queryset(self.request.cradmin_role)
        context_data['qualifying_assignmentids'] = set(self.request.session['qualifying_assignmentids'])
        context_data['passing_relatedstudentids'] = set(self.request.session['passing_relatedstudentids'])

        return context_data

    def _create_status(self, plugintypeid):
        """
        Creates and saves a entry in the database for current examqualification-status for students.

        Returns:
            A :obj:`~.devilry.devilry_qualifiesforexam.models.Status` instance saved to the db.
        """
        status = status_models.Status.objects.create(
                status=status_models.Status.READY,
                period=self.request.cradmin_role,
                user=self.request.user,
                plugin=plugintypeid
        )
        status.full_clean()
        return status

    def _bulk_create_relatedstudents(self, status, passing_relatedstudentids):
        """
        Bulk create :obj:`~.devilry.devilry_qualifiesforexam.models.QualifiesForFinalExam` entries in the database
        for each student. Each entry has a ForeignKey to ``status``.

        Args:
            status: ForeignKey reference for each
                :obj:`~.devilry.devilry_qualifiesforexam.models.QualifiesForFinalExam`.
        """
        qualifies_for_final_exam_objects = []
        for relatedstudent in self.get_relatedstudents_queryset(self.request.cradmin_role):
            qualifies_for_final_exam_objects.append(status_models.QualifiesForFinalExam(
                relatedstudent=relatedstudent,
                status=status,
                qualifies=True if relatedstudent.id in passing_relatedstudentids else False
            ))
        status_models.QualifiesForFinalExam.objects.bulk_create(qualifies_for_final_exam_objects)

    def form_valid(self, form):
        passing_relatedstudentids = set(self.request.session['passing_relatedstudentids'])
        plugintypeid = self.request.session['plugintypeid']
        del self.request.session['passing_relatedstudentids']
        del self.request.session['plugintypeid']
        del self.request.session['qualifying_assignmentids']
        if 'save' in self.request.POST:
            status = self._create_status(plugintypeid)
            self._bulk_create_relatedstudents(status, passing_relatedstudentids)
            return HttpResponseRedirect(self.request.cradmin_app.reverse_appurl(
                viewname='show-status',
                kwargs={
                    'roleid': self.request.cradmin_role.id
                }
            ))
        elif 'back' in self.request.POST:
            return HttpResponseRedirect(self.request.cradmin_app.reverse_appurl(
                viewname='configure-plugin',
                kwargs={
                    'roleid': self.request.cradmin_role.id,
                    'plugintypeid': plugintypeid
                }
            ))


class QualificationStatusForm(forms.ModelForm):
    class Meta:
        model = status_models.Status
        fields = ['status', 'message']

    def __init__(self, *args, **kwargs):
        super(QualificationStatusForm, self).__init__(*args, **kwargs)
        self.fields['my_choice_field'] = forms.ChoiceField()


class QualificationStatusPreview(AbstractQualificationPreviewView):
    """
    View for showing the current :class:`~.devilry.devilry_qualifiesforexam.models.Status` of the
    qualifications list.
    """
    template_name = 'devilry_qualifiesforexam/show_status.html'
    form_class = QualificationStatusForm

    def get_buttons(self):
        return [
            PrimarySubmit('retract', _('Retract')),
        ]

    def _get_relatedstudents(self, period):
        """
        Get all RelatedStudents for Period and select related user
        for :class:'~.devilry.apps.core.models.RelatedStudent'.

        Args:
            period: Period to fetch students for.

        Returns:
            QuerySet of :class:'~.devilry.apps.core.models.RelatedStudent' for ``period``.
        """
        return core_models.RelatedStudent.objects.filter(period=period)\
            .select_related('user')\
            .order_by('user__fullname')

    def get_context_data(self, **kwargs):
        context_data = super(QualificationStatusPreview, self).get_context_data(**kwargs)

        current_status = status_models.Status.objects.get_last_status_in_period(period=self.request.cradmin_role)

        # Set status info
        context_data['saved_by'] = current_status.user
        context_data['period'] = current_status.period
        context_data['saved_date'] = current_status.createtime
        context_data['status'] = current_status.status

        # Generate student info
        qualifiesforexam = list(current_status.students.all())
        qualifying_studentids = [q.relatedstudent.id for q in qualifiesforexam if q.qualifies]
        relatedstudents = self._get_relatedstudents(self.request.cradmin_role)
        context_data['passing_relatedstudentids'] = qualifying_studentids
        context_data['num_students_qualify'] = len(qualifying_studentids)
        context_data['relatedstudents'] = relatedstudents
        context_data['num_students'] = len(relatedstudents)
        return context_data

    def form_valid(self, form):
        if 'retract' in self.request.POST:
            print form.status
            return HttpResponseRedirect(self.request.cradmin_app.reverse_appurl(
                viewname='show-status',
                kwargs={
                    'roleid': self.request.cradmin_role.id
                }
            ))
