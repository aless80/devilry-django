from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy

from devilry.apps.core.models.relateduser import RelatedStudent, RelatedExaminer
from devilry.apps.core.models.period import Period


class PeriodTagQuerySet(models.QuerySet):
    """
    Model manager for :class:`.PeriodTag`.
    """
    def get_all_distinct_tags(self):
        """
        Get all distinct tags across periods.

        Returns:
            (QuerySet): QuerySet of :class:`.PeriodTag`.
        """
        return self.distinct('prefix', 'tag')

    def get_all_tags_for_active_periods(self):
        """
        Get all tags for periods that are currently active.

        Returns:
            (QuerySet): QuerySet of :class:`.PeriodTag`.
        """
        now = timezone.now()
        return self.filter(period__start_time__lt=now,
                           period__end_time__gt=now)

    def get_all_tags_on_period(self, period):
        """
        Get a QuerySet of all distinct :obj:`~.PeriodTag`s on ``period``.
        Orders by :attr.PeriodTag.prefix` and :attr:`~.PeriodTag.tag`

        Args:
            period: Get distinct tags for.

        Returns:
            (QuerySet): QuerySet of :class:`.PeriodTag`.
        """
        return self.filter(period=period)\
            .distinct()

    def get_all_editable_tags(self):
        """
        Get a QuerySet of all :obj:`~.PeriodTag`s that are editable.
        I.e, :attr:`.PeriodTag.prefix` is blank.

        Returns:
            (QuerySet): QuerySet of :class:`.PeriodTag`.
        """
        return self.filter(prefix='')

    def filter_all_editable_tags_on_period(self, period):
        """
        Get a QuerySet of all :obj:`~.PeriodTag`s on ``period`` that are editable.
        I.e, :attr:`.PeriodTag.prefix` is blank.

        Args:
            period: Get tags for.

        Returns:
            (QuerySet): QuerySet of :class:`.PeriodTag`.
        """
        return self.filter(period=period, prefix='')

    def get_all_visible_tags(self):
        """
        Get a QuerySet of all :obj:`.PeriodTag`s with :class:`.PeriodTag.is_hidden=False`

        Returns:
            (QuerySet): QuerySet of :class:`.PeriodTag`.
        """
        return self.filter(is_hidden=False)

    def get_all_hidden_tags(self):
        """
        Get a QuerySet of all :obj:`.PeriodTag`s with :class:`.PeriodTag.is_hidden=True`

        Returns:
            (QuerySet): QuerySet of :class:`.PeriodTag`.
        """
        return self.filter(is_hidden=True)

    def filter_tags_for_related_student_user(self, user):
        """
        Get all tags where the user is registered as
        :class:`~.devilry.apps.core.models.relateduser.RelatedStudent`.

        Args:
            user: :class:`~.devilry.account.models.User` instance.

        Returns:
            (QuerySet): QuerySet of :class:`.PeriodTag`.
        """
        return self.filter(relatedstudents__user=user)

    def filter_tags_for_related_student_user_on_period(self, user, period):
        """
        Same as :func:`.filter_tags_for_related_student` but also filters on period.

        Args:
            user: :class:`~.devilry.account.models.User` instance.
            period: :class:`~.devilry.apps.core.models.period.Period` instance.

        Returns:
            (QuerySet): QuerySet of :class:`.PeriodTag`.
        """
        return self.filter_tags_for_related_student_user(user=user)\
            .filter(period=period)

    def filter_tags_for_related_examiner_user(self, user):
        """
        Get all tags where the user is registered as
        :class:`~.devilry.apps.core.models.relateduser.RelatedExaminer`.

        Args:
            user: :class:`~.devilry.account.models.User` instance.

        Returns:
            (QuerySet): QuerySet of :class:`.PeriodTag`.
        """
        return self.filter(relatedexaminers__user=user)

    def filter_tags_for_related_examiner_user_on_period(self, user, period):
        """
        Same as :func:`.filter_tags_for_related_examiner` but also filters on period.

        Args:
            user: :class:`~.devilry.account.models.User` instance.
            period: :class:`~.devilry.apps.core.models.period.Period` instance.

        Returns:
            (QuerySet): QuerySet of :class:`.PeriodTag`.
        """
        return self.filter_tags_for_related_examiner_user(user=user)\
            .filter(period=period)


class PeriodTag(models.Model):
    """
    A :class:`.PeriodTag` represents a form of grouping on a period for
    :class:`~.devilry.app.core.models.relateduser.RelatedStudent`s and
    :class:`~.devilry.app.core.models.relateduser.RelatedExaminer`s.
    """
    objects = PeriodTagQuerySet.as_manager()

    class Meta:
        ordering = ['prefix', 'tag']
        unique_together = [
            ('period', 'prefix', 'tag')
        ]

    #: The period(semester) for the tag.
    period = models.ForeignKey(Period, related_name='period_tag')

    #: Used by import scripts.
    #: If tags are imported from another system, the prefix should be used.
    #: If the prefix is used, the tag cannot(should not) be edited.
    #: If the prefix is blank, the tag is editable.
    prefix = models.CharField(blank=True, default='', max_length=30)

    #: A tag unique for the period.
    #: If the prefix is blank, the tag itself is unique, else
    #: the combination of the prefix and the tag is unique.
    tag = models.CharField(db_index=True, max_length=30)

    #: A tag can be set to hidden for filtering purposes.
    #: I.g, you don't want to remove a tag yet, but you do not want it
    #: to be visible either.
    is_hidden = models.BooleanField(default=False)

    #: When the tag was created.
    created_datetime = models.DateTimeField(auto_now_add=True)

    #: When the tag was last modified.
    #: This is for tags that can be modified.
    modified_datetime = models.DateTimeField(null=True, blank=True)

    #: ManyToMany field for :class:`~.devilry.apps.core.models.RelatedExaminer`.
    relatedexaminers = models.ManyToManyField(RelatedExaminer)

    #: ManyToMany field for :class:`~.devilry.apps.core.models.RelatedStudent`
    relatedstudents = models.ManyToManyField(RelatedStudent)

    @property
    def displayname(self):
        if self.prefix == '':
            return '{} on {}'.format(self.tag, self.period)
        return '{}:{} on {}'.format(self.prefix, self.tag, self.period)

    def clean(self):
        if len(self.tag) == 0:
            raise ValidationError({
                'tag': ugettext_lazy('Field cannot be blank.')
            })
