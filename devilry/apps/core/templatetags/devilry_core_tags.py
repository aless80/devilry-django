import bleach
from django import template
from django.utils.translation import ugettext_lazy as _

from devilry.apps.core.models import Assignment
from devilry.utils import datetimeutils

register = template.Library()


@register.filter
def devilry_user_displayname(user):
    if not user:
        return ''
    return user.get_full_name()


@register.filter
def format_is_passing_grade(is_passing_grade):
    if is_passing_grade:
        return _('passed')
    else:
        return _('failed')


@register.filter
def devilry_feedback_shortformat(staticfeedback):
    if not staticfeedback:
        return ''
    if staticfeedback.grade in ('Passed', 'Failed'):
        return staticfeedback.grade
    else:
        return u'{} ({})'.format(
            staticfeedback.grade,
            format_is_passing_grade(staticfeedback.is_passing_grade))


@register.filter
def devilry_escape_html(html):
    """
    Escape all html in the given ``html``.
    """
    return bleach.clean(html)


@register.filter
def devilry_isoformat_datetime(datetimeobject):
    """
    Isoformat the given ``datetimeobject`` as ``YYYY-MM-DD hh:mm``.
    """
    return datetimeutils.isoformat_noseconds(datetimeobject)


@register.inclusion_tag('devilry_core/templatetags/single-candidate-long-displayname.django.html')
def devilry_single_candidate_long_displayname(assignment, candidate, devilryrole):
    """
    Returns the candidate wrapped in HTML formatting tags perfect for showing
    the user inline in a verbose manner.

    Handles anonymization based on ``assignment.anonymizationmode`` and ``devilryrole``.

    Args:
        assignment: A :class:`devilry.apps.core.models.Assignment` object.
            The ``assignment`` should be the assignment where the candidate belongs.
        candidate: A :class:`devilry.apps.core.models.Candidate` object.
        devilryrole: See
            :meth:`devilry.apps.core.models.Assignment.students_must_be_anonymized_for_devilryrole`.
    """
    return {
        'candidate': candidate,
        'anonymous': assignment.students_must_be_anonymized_for_devilryrole(
            devilryrole=devilryrole),
        'anonymous_name': candidate.get_anonymous_name(assignment=assignment)
    }


@register.inclusion_tag('devilry_core/templatetags/single-candidate-short-displayname.django.html')
def devilry_single_candidate_short_displayname(assignment, candidate, devilryrole):
    """
    Returns the candidate wrapped in HTML formatting tags perfect for showing
    the user inline in a non-verbose manner.

    Handles anonymization based on ``assignment.anonymizationmode`` and ``devilryrole``.

    Args:
        assignment: A :class:`devilry.apps.core.models.Assignment` object.
            The ``assignment`` should be the assignment where the candidate belongs.
        candidate: A :class:`devilry.apps.core.models.Candidate` object.
        devilryrole: See
            :meth:`devilry.apps.core.models.Assignment.students_must_be_anonymized_for_devilryrole`.
    """
    return {
        'candidate': candidate,
        'anonymous': assignment.students_must_be_anonymized_for_devilryrole(
            devilryrole=devilryrole),
        'anonymous_name': candidate.get_anonymous_name(assignment=assignment)
    }


@register.inclusion_tag('devilry_core/templatetags/single-examiner-long-displayname.django.html')
def devilry_single_examiner_long_displayname(assignment, examiner, devilryrole):
    """
    Returns the examiner wrapped in HTML formatting tags perfect for showing
    the user inline in a verbose manner.

    Handles anonymization based on ``assignment.anonymizationmode`` and ``devilryrole``.

    Args:
        assignment: A :class:`devilry.apps.core.models.Assignment` object.
            The ``assignment`` should be the assignment where the examiner belongs.
        examiner: A :class:`devilry.apps.core.models.Examiner` object.
        devilryrole: See
            :meth:`devilry.apps.core.models.Assignment.examiners_must_be_anonymized_for_devilryrole`.
    """
    return {
        'examiner': examiner,
        'anonymous': assignment.examiners_must_be_anonymized_for_devilryrole(
            devilryrole=devilryrole)
    }


@register.inclusion_tag('devilry_core/templatetags/single-examiner-short-displayname.django.html')
def devilry_single_examiner_short_displayname(assignment, examiner, devilryrole):
    """
    Returns the examiner wrapped in HTML formatting tags perfect for showing
    the user inline in a non-verbose manner.

    Handles anonymization based on ``assignment.anonymizationmode`` and ``devilryrole``.

    Args:
        assignment: A :class:`devilry.apps.core.models.Assignment` object.
            The ``assignment`` should be the assignment where the examiner belongs.
        examiner: A :class:`devilry.apps.core.models.Examiner` object.
        devilryrole: See
            :meth:`devilry.apps.core.models.Assignment.examiners_must_be_anonymized_for_devilryrole`.
    """
    return {
        'examiner': examiner,
        'anonymous': assignment.examiners_must_be_anonymized_for_devilryrole(
            devilryrole=devilryrole)
    }


@register.inclusion_tag('devilry_core/templatetags/multiple-candidates-long-displayname.django.html')
def devilry_multiple_candidates_long_displayname(assignment, candidates, devilryrole):
    """
    Returns the candidates wrapped in HTML formatting tags perfect for showing
    the candidates inline in a verbose manner.

    Typically used for showing all the candidates in an
    :class:`devilry.apps.core.models_group.AssignmentGroup`.

    Handles anonymization based on ``assignment.anonymizationmode`` and ``devilryrole``.

    Args:
        assignment: A :class:`devilry.apps.core.models.Assignment` object.
            The ``assignment`` should be the assignment where the candidates belongs.
        candidates: An iterable of :class:`devilry.apps.core.models.Candidate` objects.
        devilryrole: See
            :meth:`devilry.apps.core.models.Assignment.students_must_be_anonymized_for_devilryrole`.
    """
    return {
        'assignment': assignment,
        'candidates': candidates,
        'devilryrole': devilryrole,
    }


@register.inclusion_tag('devilry_core/templatetags/multiple-candidates-short-displayname.django.html')
def devilry_multiple_candidates_short_displayname(assignment, candidates, devilryrole):
    """
    Returns the candidates wrapped in HTML formatting tags perfect for showing
    the candidates inline in a non-verbose manner.

    Typically used for showing all the candidates in an
    :class:`devilry.apps.core.models_group.AssignmentGroup`.

    Handles anonymization based on ``assignment.anonymizationmode`` and ``devilryrole``.

    Args:
        assignment: A :class:`devilry.apps.core.models.Assignment` object.
            The ``assignment`` should be the assignment where the candidates belongs.
        candidates: An iterable of :class:`devilry.apps.core.models.Candidate` objects.
        devilryrole: See
            :meth:`devilry.apps.core.models.Assignment.students_must_be_anonymized_for_devilryrole`.
    """
    return {
        'assignment': assignment,
        'candidates': candidates,
        'devilryrole': devilryrole,
    }


@register.inclusion_tag('devilry_core/templatetags/multiple-examiners-long-displayname.django.html')
def devilry_multiple_examiners_long_displayname(assignment, examiners, devilryrole):
    """
    Returns the examiners wrapped in HTML formatting tags perfect for showing
    the examiners inline in a verbose manner.

    Typically used for showing all the examiners in an
    :class:`devilry.apps.core.models_group.AssignmentGroup`.

    Handles anonymization based on ``assignment.anonymizationmode`` and ``devilryrole``.

    Args:
        assignment: A :class:`devilry.apps.core.models.Assignment` object.
            The ``assignment`` should be the assignment where the examiners belongs.
        examiners: An iterable of :class:`devilry.apps.core.models.Examiner` objects.
        devilryrole: See
            :meth:`devilry.apps.core.models.Assignment.examiners_must_be_anonymized_for_devilryrole`.
    """
    return {
        'assignment': assignment,
        'examiners': examiners,
        'devilryrole': devilryrole,
    }


@register.inclusion_tag('devilry_core/templatetags/multiple-examiners-short-displayname.django.html')
def devilry_multiple_examiners_short_displayname(assignment, examiners, devilryrole):
    """
    Returns the examiners wrapped in HTML formatting tags perfect for showing
    the examiners inline in a non-verbose manner.

    Typically used for showing all the examiners in an
    :class:`devilry.apps.core.models_group.AssignmentGroup`.

    Handles anonymization based on ``assignment.anonymizationmode`` and ``devilryrole``.

    Args:
        assignment: A :class:`devilry.apps.core.models.Assignment` object.
            The ``assignment`` should be the assignment where the examiners belongs.
        examiners: An iterable of :class:`devilry.apps.core.models.Examiner` objects.
        devilryrole: See
            :meth:`devilry.apps.core.models.Assignment.examiners_must_be_anonymized_for_devilryrole`.
    """
    return {
        'assignment': assignment,
        'examiners': examiners,
        'devilryrole': devilryrole,
    }


@register.inclusion_tag('devilry_core/templatetags/groupstatus.django.html')
def devilry_groupstatus(group):
    return {
        'group': group
    }


@register.inclusion_tag('devilry_core/templatetags/grade-short.django.html')
def devilry_grade_short(assignment, points):
    """
    Renders a grade as in its shortest form - no information about passed or failed,
    only the grade text (E.g.: "passed", "8/10", "A").

    Args:
        assignment: An :class:`devilry.apps.core.models.Assignment` object.
        points: The points to render the grade for.
    """
    return {
        'assignment': assignment,
        'grade': assignment.points_to_grade(points=points),
        'is_passing_grade': assignment.points_is_passing_grade(points=points),
    }


@register.inclusion_tag('devilry_core/templatetags/grade-full.django.html')
def devilry_grade_full(assignment, points, devilryrole):
    """
    Renders a grade as in its long form - including information about passed or failed.
    Examples::

        "passed"
        "8/10 (passed)"
        "F (failed)"

    If the ``students_can_see_points`` attribute of the assignment is
    set to ``True``, students are allowed to see the points behind
    a grade, so we include the points. Examples::

        "passed"
        "8/10 (passed)"
        "F (failed - 10/100)"
        "A (passed - 97/100)"

    Args:
        assignment: An :class:`devilry.apps.core.models.Assignment` object.
        points (int): The points to render the grade for.
        devilryrole (str): Must be one of the choices documented in
            :meth:`devilry.apps.core.models.Assignment.examiners_must_be_anonymized_for_devilryrole`.
    """
    include_is_passing_grade = assignment.points_to_grade_mapper != Assignment.POINTS_TO_GRADE_MAPPER_PASSED_FAILED
    include_points = assignment.points_to_grade_mapper != Assignment.POINTS_TO_GRADE_MAPPER_RAW_POINTS
    if devilryrole == 'student' and not assignment.students_can_see_points:
        include_points = False

    return {
        'assignment': assignment,
        'grade': assignment.points_to_grade(points=points),
        'points': points,
        'is_passing_grade': assignment.points_is_passing_grade(points=points),
        'include_is_passing_grade': include_is_passing_grade,
        'include_points': include_points,
    }
