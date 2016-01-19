from __future__ import unicode_literals

from django_cradmin.viewhelpers.update import UpdateView

from devilry.apps.core import models as coremodels


class AssignmentLongAndShortNameUpdateView(UpdateView):
    model = coremodels.Assignment

    fields = ['long_name',
              'short_name']

    def get_queryset_for_role(self, role):
        return self.model.objects.filter(id=self.kwargs['pk'])
