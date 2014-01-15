from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db import transaction
from datetime import datetime

from abstract_is_examiner import AbstractIsExaminer
from abstract_is_candidate import AbstractIsCandidate
from assignment_group import AssignmentGroup
from abstract_is_admin import AbstractIsAdmin
import deliverytypes

from node import Node



class NewerDeadlineExistsError(Exception):
    """
    Exception raised by :meth:DeadlineManager.smart_create``.
    """


class DeadlineQuerySet(models.query.QuerySet):
    def smart_create(self, groupqueryset, deadline_datetime, text=None,
            query_created_deadlines=False):

        # We do this because we want to make it easy to compare deadlines based on their datetime.
        deadline_datetime = Deadline.reduce_datetime_precision(deadline_datetime)

        # DB query 1 - Check that no newer deadlines exist
        if groupqueryset.filter(last_deadline__deadline__gt=deadline_datetime).exists():
            raise NewerDeadlineExistsError()

        # DB query 2 - get all the groups
        groups = groupqueryset.all()
        if len(groups) == 0:
            return []

        # DB query 3 - create deadlines
        deadlines_to_create = [Deadline(assignment_group=group, deadline=deadline_datetime, text=text)\
            for group in groups]
        self.bulk_create(deadlines_to_create)

        # DB query 4 - Fetch created deadlines
        def get_created_deadlines():
            return Deadline.objects.filter(
                assignment_group__in=groups,
                deadline=deadline_datetime,
                text=text).select_related('assignment_group')
        created_deadlines = get_created_deadlines()


        def save_group(deadline, last_delivery=None):
            group = deadline.assignment_group
            group.is_open = True
            group.delivery_status = "waiting-for-something"
            group.last_deadline = deadline
            if last_delivery:
                group.last_delivery = last_delivery
            group.save(update_delivery_status=False,
                autocreate_first_deadline_for_nonelectronic=False)

        assignment = groups[0].assignment # NOTE: We assume all groups are within the same assignment - as documented
        time_of_delivery = datetime.now().replace(microsecond=0, tzinfo=None)
        if assignment.delivery_types == deliverytypes.NON_ELECTRONIC:
            from .delivery import Delivery

            # DB query 6 - create deliveries
            deliveries_to_create = [Delivery(deadline=deadline, time_of_delivery=time_of_delivery, number=1, successful=True)\
                for deadline in created_deadlines]
            Delivery.objects.bulk_create(deliveries_to_create)

            # DB query 7 - fetch created deliveries
            created_deliveries = Delivery.objects.filter(
                deadline__assignment_group__in=groups,
                time_of_delivery=time_of_delivery).select_related(
                    'deadline', 'deadline__assignment_group')

            # DB query 8 - Update groups, including last_delivery
            with transaction.commit_on_success(): # NOTE: Using a transaction should lead to one huge query commited at the end of the block
                for delivery in created_deliveries:
                    save_group(delivery.deadline, delivery)

        else:
            # DB query 5 - Update groups
            with transaction.commit_on_success(): # NOTE: Using a transaction should lead to one huge query commited at the end of the block
                for deadline in created_deadlines:
                    save_group(deadline)

        if query_created_deadlines:
            return get_created_deadlines()

            


class DeadlineManager(models.Manager):
    def get_queryset(self):
        return DeadlineQuerySet(self.model, using=self._db)

    def smart_create(self, groupqueryset, deadline_datetime, text=None, query_created_deadlines=False):
        """
        Creates deadlines for all groups in the given QuerySet of AssignmentGroups.

        Algorighm:

        1. Create deadlines in bulk.
        2. If assignment is ``NON_ELECTRONIC``, create a delivery for each of the created deadlines.
        3. Update all the groups in groupqueryset() with ``is_open=True``, 
           ``delivery_status="waiting-for-something"``, ``last_deadline=<newly created deadline>``
           and ``last_delivery=<created delivery>`` (if a delivery was created in step 2).

        :param groupqueryset:
            A QuerySet of AssignmentGroup objects. MUST match groups within a single assignment.
        :param deadline_datetime:
            The datetime of the deadline. The function runs this through
            :meth:`Deadline.reduce_datetime_precision` before using it.
        :param text: The deadline text. Defaults to ``None``.
        :param query_created_deadlines:
            Perform a query for the created deadlines at the end of the method.

        :raise NewerDeadlineExistsError:
            When one of the groups in the ``groupqueryset`` has a ``last_deadline``
            that is newer than ``deadline_datetime``

        First described in https://github.com/devilry/devilry-django/issues/514.
        """
        return self.get_queryset().smart_create(groupqueryset, deadline_datetime, text)





class Deadline(models.Model, AbstractIsAdmin, AbstractIsExaminer, AbstractIsCandidate):
    """ A deadline on an `AssignmentGroup`_. A deadline contains zero or more
    `deliveries <Delivery>`_, the time of the deadline and an optional text.

    .. attribute:: assignment_group

        The `AssignmentGroup`_ where the deadline is registered.

    .. attribute:: deadline

        The deadline a DateTimeField.

    .. attribute:: text

        A optional deadline text.

    .. attribute:: deliveries

        A django ``RelatedManager`` that holds the `deliveries <Delivery>`_ on this group.
        NOTE: You should normally not use this directly, but rather use meth:`.query_successful_deliveries`.


    .. attribute:: deliveries_available_before_deadline

        Should deliveries on this deadline be available to examiners before the
        deadline expires? This is set by students.

    .. attribute:: feedbacks_published

        If this boolean field is ``True``, the student can see all
        :class:`StaticFeedback` objects associated with this Deadline through a
        :class:`Delivery`. See also :attr:`Assignment.examiners_publish_feedbacks_directly`.

    """
    objects = DeadlineManager()
    assignment_group = models.ForeignKey(AssignmentGroup,
            related_name='deadlines')
    deadline = models.DateTimeField(help_text='The time of the deadline.')
    text = models.TextField(blank=True, null=True,
                            help_text='An optional text to show to students and examiners.')
    deliveries_available_before_deadline = models.BooleanField(default=False,
                                                              help_text='Should deliveries on this deadline be available to examiners before the'
                                                                          'deadline expires? This is set by students.')
    feedbacks_published = models.BooleanField(default=False,
                                              help_text='If this is ``True``, the student can see all '\
                                                          'StaticFeedbacks associated with this Deadline')

    class Meta:
        app_label = 'core'
        verbose_name = 'Deadline'
        verbose_name_plural = 'Deadlines'
        ordering = ['-deadline']


    @classmethod
    def reduce_datetime_precision(cls, datetimeobj):
        """
        Reduce the precition of the ``datetimeobj`` to make it easier to compare.

        :return: A copy of ``datetimeobj`` with microsecond set to ``0``, and tzinfo set to ``None``.
        """
        return datetimeobj.replace(microsecond=0, tzinfo=None)

    def remove_microsec(self):
        self.deadline = Deadline.reduce_datetime_precision(self.deadline) # NOTE: We want this so a unique deadline is a deadline which matches with second-specition.

    def _clean_deadline(self):
        self.remove_microsec()
        qry = Q(deadline=self.deadline, assignment_group=self.assignment_group)
        if self.id:
            qry &= ~Q(id=self.id)
        deadlines = Deadline.objects.filter(qry)
        if deadlines.count() > 0:
            raise ValidationError('Can not have more than one deadline with the same date/time on a single group.')

    def clean(self, *args, **kwargs):
        """Validate the deadline.

        Always call this before save()! Read about validation here:
        http://docs.djangoproject.com/en/dev/ref/models/instances/#id1

        Raises ValidationError if:

            - ``deadline`` is before ``Assignment.publishing_time``.
            - ``deadline`` is not before ``Period.end_time``.
        """
        if self.deadline != None:
            if self.deadline < self.assignment_group.parentnode.publishing_time:
                raise ValidationError('Deadline cannot be before publishing time.')

            if self.deadline > self.assignment_group.parentnode.parentnode.end_time:
                raise ValidationError(
                    "Deadline must be within it's period (%(period)s)."
                      % dict(period=unicode(self.assignment_group.parentnode.parentnode)))
            self._clean_deadline()
        super(Deadline, self).clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        """
        :param autocreate_delivery_if_nonelectronic:
            Autocreate a delivery if this save creates the deadline,
            and the assignment is non-electronic. Defaults to ``True``.
        """
        autocreate_delivery_if_nonelectronic = kwargs.pop('autocreate_delivery_if_nonelectronic', True)
        created = self.id == None
        super(Deadline, self).save(*args, **kwargs)
        group = self.assignment_group

        # Only update the AssignmentGroup if needed.
        # See https://github.com/devilry/devilry-django/issues/502
        groupsave_needed = False
        if created:
            if not group.is_open:
                groupsave_needed = True
                group.is_open = True
            if group.delivery_status == 'no-deadlines':
                groupsave_needed = True
                group.delivery_status = 'waiting-for-something'
            if autocreate_delivery_if_nonelectronic and group.assignment.delivery_types == deliverytypes.NON_ELECTRONIC:
                from .delivery import Delivery
                delivery = Delivery(
                    deadline=self,
                    number=1)
                delivery.save(autoset_number=False, autoset_last_delivery_on_group=False)
                group.last_delivery = delivery
                groupsave_needed = True
        if group.last_deadline == None or group.last_deadline.deadline < self.deadline:
            group.last_deadline = self
            groupsave_needed = True

        if groupsave_needed:
            group.save(update_delivery_status=False)

    def __unicode__(self):
        return unicode(self.deadline)

    def __repr__(self):
        return 'Deadline(id={id}, deadline={deadline})'.format(**self.__dict__)

    #TODO delete this?
    #def is_old(self):
        #""" Return True if :attr:`deadline` expired. """
        #return self.deadline < datetime.now()

    @classmethod
    def q_is_admin(cls, user_obj):
        return Q(assignment_group__parentnode__admins=user_obj) | \
            Q(assignment_group__parentnode__parentnode__admins=user_obj) | \
            Q(assignment_group__parentnode__parentnode__parentnode__admins=user_obj) | \
            Q(assignment_group__parentnode__parentnode__parentnode__parentnode__pk__in=Node._get_nodepks_where_isadmin(user_obj))

    @classmethod
    def q_published(cls, old=True, active=True):
        now = datetime.now()
        q = Q(assignment_group__parentnode__publishing_time__lt = now)
        if not active:
            q &= ~Q(assignment_group__parentnode__parentnode__end_time__gte = now)
        if not old:
            q &= ~Q(assignment_group__parentnode__parentnode__end_time__lt = now)
        return q

    @classmethod
    def q_is_candidate(cls, user_obj):
        return Q(assignment_group__candidates__student=user_obj)

    @classmethod
    def q_is_examiner(cls, user_obj):
        return Q(assignment_group__examiners__user=user_obj)


    def query_successful_deliveries(self):
        """
        Returns a django QuerySet that filters all the successful `deliveries
        <Delivery>`_ on this group.
        """
        return self.deliveries.filter(successful=True)


    @property
    def successful_delivery_count(self):
        return self.query_successful_deliveries().count()
    

    def is_empty(self):
        """
        Returns ``True`` if this Deadline does not contain any deliveries.
        """
        return self.query_successful_deliveries().count() == 0

    def can_delete(self, user_obj):
        """
        Check if the given user is permitted to delete this object. A user is
        permitted to delete an Deadline if the user is superadmin, or if the user
        is admin on the assignment. Only superusers
        are allowed to delete deadlines with any deliveries.

        :return: ``True`` if the user is permitted to delete this object.
        """
        if self.id == None:
            return False
        if user_obj.is_superuser:
            return True
        if self.is_empty():
            return self.assignment_group.parentnode.is_admin(user_obj)
        else:
            return False


    def copy(self, newgroup):
        """
        Copy this deadline into ``newgroup``, including all deliveries and
        filemetas, with the actual file data.

        .. note:: Always run this is a transaction.

        .. warning::
            This does not autoset the latest feedback as active on the group.
            You need to handle that yourself after the copy.
        """
        deadlinecopy = Deadline(assignment_group=newgroup,
                                deadline=self.deadline,
                                text=self.text,
                                feedbacks_published=self.feedbacks_published)
        deadlinecopy.full_clean()
        deadlinecopy.save()
        for delivery in self.query_successful_deliveries():
            delivery.copy(deadlinecopy)
        return deadlinecopy
