# -*- coding: utf-8 -*-


import io
import json

from django.http import Http404, HttpResponse
from django.views import generic
from django import forms
import django_rq

from devilry.devilry_report.models import DevilryReport
from devilry.devilry_report.rq_task import generate_report


class ReportForm(forms.Form):
    report_options = forms.CharField(required=True)

    def clean_report_options(self):
        report_options = json.loads(self.cleaned_data['report_options'])
        if 'generator_type' not in report_options:
            raise forms.ValidationError('Missing \'generator_type\' in report_options')
        return report_options


class DownloadAnonymizedReportView(generic.FormView):
    """
    Generate/download a :class:`~.devilry.devilry_report.models.DevilryReport`.

    Usage:
        This view has no standalone URL, and should be added to the appropriate CrAdmin-app where you want
        to generate a report. Everyone with access to that CrAdmin-app will have access to generate a report if
        supported.

    Method ``GET``:
        Get handles two cases regarding a report, status-fetch and download.

        1. If the report has not been generated yet, a message will be shown telling you that the
        report is not finished yet. This is the case for all report-statuses except `success`.

        2. If the status of the report is `success`, and download-response will automatically be returned
        and starts downloading the file.

        Raises HTTP 404 if `report=<report_id>` is missing from the queryparams or the
        request user is the user the report was generated by.

    Method ``POST``:
        Enqueues the a RQ-task that starts generating a report based on the posted data.
        Redirects to this view with method ``GET``.
    """
    template_name = "devilry_report/download_report.django.html"
    form_class = ReportForm

    ###############################
    # GET: Download request methods
    ###############################
    def __get_devilry_report(self):
        try:
            return DevilryReport.objects.get(id=self.request.GET['report'])
        except DevilryReport.DoesNotExist:
            raise Http404

    def get(self, *args, **kwargs):
        if 'report' not in self.request.GET:
            raise Http404()

        # Fetch report
        self.devilry_report = self.__get_devilry_report()
        if self.devilry_report.generated_by_user_id != self.request.user.id:
            # Raise 404 if the requestuser did not create the report.
            raise Http404()

        if self.devilry_report.status == DevilryReport.STATUS_CHOICES.SUCCESS.value:
            # Return a download reponse if the report is finished.
            buffer = io.BytesIO()
            buffer.write(self.devilry_report.result)
            response = HttpResponse(
                buffer.getvalue(), content_type=self.devilry_report.content_type)
            response['Content-Disposition'] = 'attachment; filename={}'.format(self.devilry_report.output_filename)
            response['Content-Length'] = len(buffer.getvalue())
            return response
        return super(DownloadAnonymizedReportView, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DownloadAnonymizedReportView, self).get_context_data(**kwargs)
        context['devilry_report'] = self.devilry_report
        return context

    ###############################
    # POST: Generate report methods
    ###############################
    def form_valid(self, form):
        report_options = form.cleaned_data['report_options']
        self.devilry_report = DevilryReport(
            generator_type=report_options['generator_type'],
            generator_options=report_options['generator_options'],
            generated_by_user=self.request.user
        )
        self.devilry_report.full_clean()
        self.devilry_report.save()
        django_rq.enqueue(
            generate_report,
            devilry_report_id=self.devilry_report.id
        )
        return super(DownloadAnonymizedReportView, self).form_valid(form=form)

    def get_success_url(self):
        return '{}?report={}'.format(
            self.request.cradmin_app.reverse_appurl('download_report'),
            self.devilry_report.id
        )
