# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils import timezone
from model_mommy import mommy

from devilry.devilry_group.models import FeedbackSet
from devilry.devilry_dbcache import models as cache_models


def _get_first_feedbackset_for_group(group):
    return FeedbackSet.objects\
        .filter(group=group)\
        .order_by('created_datetime')\
        .first()


def feedbackset_save(feedbackset, **kwargs):
    """
    Set attributes for a FeedbackSet-instance and save it.

    Args:
        feedbackset: FeedbackSet to save.
    """
    for key, value in kwargs.iteritems():
        setattr(feedbackset, key, value)
    feedbackset.is_last_in_group = None  # NOTE: is_last_in_group is deprecated, and will be removed
    feedbackset.full_clean()
    feedbackset.save()


def _make_assignment_group_for_feedbackset(group, **kwargs):
    groupkwargs = {}
    for key in list(kwargs.keys()):
        if key.startswith('group__'):
            value = kwargs.pop(key)
            groupkey = key[len('group__'):]
            groupkwargs[groupkey] = value
    if group:
        if groupkwargs:
            raise ValueError('You can not supply a group AND supply kwargs starting '
                             'with group__.')
    else:
        group = mommy.make('core.AssignmentGroup', **groupkwargs)
    return group


def _validate_feedbackset_first_attempt_kwargs(kwargs):
    if 'deadline_datetime' in kwargs:
        raise ValueError('deadline_datetime can not be specified for '
                         'the first FeedbackSet in a group. The deadline should '
                         'be specifed using Assignment.first_deadline!')


def feedbackset_first_attempt_published(group=None, grading_published_datetime=None, grading_points=1, **kwargs):
    """
    Updates the autogenerated FeedbackSet.

    Creates a published FeedbackSet with ``feedbackset_type=FeedbackSet.FEEDBACKSET_TYPE_NEW_ATTEMPT``
    using ``mommy.make('devilry_group.FeedbackSet)``.

    Note::
        If no group is passed as parameter(param group is None), an AssignmentGroup will be created which triggers an
        automatic creation of a FeedbackSet. This is the FeedbackSet that is returned.
        An examiner is also autogenerated for FeedbackSet.grading_published_by.

    Args:
        group: AssignmentGroup for the first FeedbackSet.
        grading_published_datetime: The ``grading_published_datetime`` of the feedbackset.
            Defaults to ``timezone.now()`` if not specified.
        grading_points: The ``grading_points`` of the feedbackset.
            Defaults to ``1``.
        kwargs: Other attributes for FeedbackSet.

    Returns:
        FeedbackSet: Instance of the first FeedbackSet.
    """
    _validate_feedbackset_first_attempt_kwargs(kwargs)
    group = _make_assignment_group_for_feedbackset(group=group, **kwargs)
    group_cache = cache_models.AssignmentGroupCachedData.objects.get(group=group)
    first_feedbackset = group_cache.first_feedbackset
    first_feedbackset.feedbackset_type = FeedbackSet.FEEDBACKSET_TYPE_FIRST_ATTEMPT
    first_feedbackset.grading_published_datetime = grading_published_datetime or timezone.now()
    first_feedbackset.grading_points = grading_points
    examiner = mommy.make('core.Examiner', assignmentgroup=group)
    first_feedbackset.grading_published_by = examiner.relatedexaminer.user
    feedbackset_save(feedbackset=first_feedbackset, **kwargs)
    return first_feedbackset


def feedbackset_first_attempt_unpublished(group=None, **kwargs):
    """
    Creates a unpublished FeedbackSet with ``feedbackset_type=FeedbackSet.FEEDBACKSET_TYPE_NEW_ATTEMPT``
    using ``mommy.make('devilry_group.FeedbackSet)``.

    Note::
        If no group is passed as parameter(param group is None), an AssignmentGroup will be created which triggers an
        automatic creation of a FeedbackSet. This is the FeedbackSet that is returned.

    Args:
        group: AssignmentGroup for the first FeedbackSet.
        kwargs: Other attributes for FeedbackSet.

    Returns:
        FeedbackSet: Instance of the first FeedbackSet.
    """
    _validate_feedbackset_first_attempt_kwargs(kwargs)
    group = _make_assignment_group_for_feedbackset(group=group, **kwargs)
    group_cache = cache_models.AssignmentGroupCachedData.objects.get(group=group)
    first_feedbackset = group_cache.first_feedbackset
    first_feedbackset.feedbackset_type = FeedbackSet.FEEDBACKSET_TYPE_FIRST_ATTEMPT
    feedbackset_save(first_feedbackset, **kwargs)
    return first_feedbackset


def feedbackset_new_attempt_published(group, grading_published_datetime=None, grading_points=1, **kwargs):
    """
    Creates a published FeedbackSet with ``feedbackset_type=FeedbackSet.FEEDBACKSET_TYPE_NEW_ATTEMPT``
    using ``mommy.make('devilry_group.FeedbackSet)``.

    Args:
        group: The AssignmentGroup the FeedbackSet should belong to.
        grading_published_datetime: The ``grading_published_datetime`` of the feedbackset.
            Defaults to ``timezone.now()`` if not specified.
        grading_points: The ``grading_points`` of the feedbackset.
            Defaults to ``1``.
        kwargs: Other attributes for FeedbackSet.

    Returns:
        FeedbackSet: The created FeedbackSet.
    """
    if not group:
        raise ValueError('A FeedbackSet as a new attempt must have a pre-existing group!')
    kwargs.setdefault('deadline_datetime', timezone.now())
    examiner = mommy.make('core.Examiner', assignmentgroup=group)
    feedbackset = mommy.prepare(
        'devilry_group.FeedbackSet',
        group=group,
        feedbackset_type=FeedbackSet.FEEDBACKSET_TYPE_NEW_ATTEMPT,
        grading_published_datetime=grading_published_datetime or timezone.now(),
        grading_points=grading_points,
        grading_published_by=examiner.relatedexaminer.user,
        **kwargs
    )
    feedbackset.full_clean()
    feedbackset.save()
    return feedbackset


def feedbackset_new_attempt_unpublished(group, **kwargs):
    """
    Creates a unpublished FeedbackSet with ``feedbackset_type=FeedbackSet.FEEDBACKSET_TYPE_NEW_ATTEMPT``
    using ``mommy.make('devilry_group.FeedbackSet)``.

    Args:
        group: The AssignmentGroup the FeedbackSet should belong to.
        kwargs: Other attributes for FeedbackSet.

    Returns:
        FeedbackSet: The created FeedbackSet.
    """
    if not group:
        raise ValueError('A FeedbackSet as a new attempt must have a pre-existing group!')
    kwargs.setdefault('deadline_datetime', timezone.now())
    feedbackset = mommy.prepare(
        'devilry_group.FeedbackSet',
        group=group,
        feedbackset_type=FeedbackSet.FEEDBACKSET_TYPE_NEW_ATTEMPT,
        **kwargs)
    feedbackset.full_clean()
    feedbackset.save()
    return feedbackset
