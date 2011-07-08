from ...simplified import simplified_modelapi, PermissionDenied, FieldSpec
from ..core import models

__all__ = ('SimplifiedNode', 'SimplifiedSubject', 'SimplifiedPeriod', 'SimplifiedAssignment')



class CanSaveAuthMixin(object):
    @classmethod
    def write_authorize(cls, user, obj):
        if not obj.can_save(user):
            raise PermissionDenied()

    @classmethod
    def read_authorize(cls, user, obj):
        if not obj.can_save(user):
            raise PermissionDenied()

    @classmethod
    def create_searchqryset(cls, user, **kwargs):
        return cls._meta.model.where_is_admin_or_superadmin(user)


@simplified_modelapi
class SimplifiedNode(CanSaveAuthMixin):
    """ Simplified wrapper for :class:`devilry.apps.core.models.Node`. """
    class Meta:
        model = models.Node
        resultfields = FieldSpec('id', 'short_name', 'long_name', 'parentnode__id')
        searchfields = FieldSpec('short_name', 'long_name')
        methods = ['create', 'insecure_read_model', 'read', 'update', 'delete', 'search']

    @classmethod
    def create_searchqryset(cls, user, **kwargs):
        qryset = models.Node.where_is_admin_or_superadmin(user)
        parentnode_id = kwargs.pop('parentnode_id', 'DO_NOT_FILTER')
        if parentnode_id != "DO_NOT_FILTER":
            qryset = qryset.filter(parentnode__id = parentnode_id)
        return qryset


@simplified_modelapi
class SimplifiedSubject(CanSaveAuthMixin):
    """ Simplified wrapper for :class:`devilry.apps.core.models.Subject`. """
    class Meta:
        model = models.Subject
        resultfields = FieldSpec('id', 'short_name', 'long_name')
        searchfields = FieldSpec('short_name', 'long_name')
        methods = ['create', 'insecure_read_model', 'read', 'update', 'delete', 'search']


@simplified_modelapi
class SimplifiedPeriod(CanSaveAuthMixin):
    """ Simplified wrapper for :class:`devilry.apps.core.models.Period`. """
    class Meta:
        model = models.Period
        resultfields = FieldSpec('id', 'short_name', 'long_name', 'parentnode__id',
                'start_time', 'end_time',
                subject = ['parentnode__short_name', 'parentnode__long_name'])
        searchfields = FieldSpec('short_name', 'long_name', 'parentnode__short_name',
                'parentnode__long_name')
        methods = ['create', 'insecure_read_model', 'read', 'update', 'delete', 'search']


@simplified_modelapi
class SimplifiedAssignment(CanSaveAuthMixin):
    """ Simplified wrapper for :class:`devilry.apps.core.models.Assignment`. """
    class Meta:
        model = models.Assignment
        resultfields = FieldSpec('id', 'short_name', 'long_name', 'parentnode__id',
                                 period = ['parentnode__short_name',
                                           'parentnode__long_name',
                                           'parentnode__parentnode__id'],
                                 subject = ['parentnode__parentnode__short_name',
                                            'parentnode__parentnode__long_name'],
                                 pointfields = ['anonymous', 'must_pass', 'maxpoints',
                                                'attempts'])
        searchfields = FieldSpec('short_name', 'long_name',
                                'parentnode__short_name', 
                                'parentnode__long_name', 
                                'parentnode__parentnode__short_name', 
                                'parentnode__parentnode__long_name')
        methods = ['create', 'insecure_read_model', 'read', 'update', 'delete', 'search']


@simplified_modelapi
class SimplifiedAssignmentGroup(CanSaveAuthMixin):
    class Meta:
        model = models.AssignmentGroup
        resultfields = FieldSpec('id', 'name', 'is_open', 'status',
                                 users=['examiners__username', 'candidates__identifier'],
                                 assignment=['parentnode__id',
                                             'parentnode__long_name',
                                             'parentnode__short_name'],
                                 period=['parentnode__parentnode__id',
                                         'parentnode__parentnode__long_name',
                                         'parentnode__parentnode__short_name'],
                                 subject=['parentnode__parentnode__parentnode__id',
                                          'parentnode__parentnode__parentnode__long_name',
                                          'parentnode__parentnode__parentnode__short_name']
                                 )
        searchfields = FieldSpec('name',
                                 'examiners__username',
                                 'candidates__identifier',
                                 # assignment
                                 'parentnode__long_name',
                                 'parentnode__short_name',
                                 # period
                                 'parentnode__parentnode__long_name',
                                 'parentnode__parentnode__short_name',
                                 # subject
                                 'parentnode__parentnode__parentnode__long_name',
                                 'parentnode__parentnode__parentnode__short_name',
                                 )
        methods = ['create', 'insecure_read_model', 'read', 'update', 'delete', 'search']


@simplified_modelapi
class SimplifiedDelivery(CanSaveAuthMixin):
    class Meta:
        model = models.Delivery
        resultfields = FieldSpec('id', 'number', 'time_of_delivery', 'deadline_tag__id',
                                 assignmentgroup=['parentnode__id', 'parentnode__name'],
                                 assignment=['parentnode__parentnode__id',
                                             'parentnode__parentnode__long_name',
                                             'parentnode__parentnode__short_name'],
                                 period=['parentnode__parentnode__parentnode__id',
                                         'parentnode__parentnode__parentnode__long_name',
                                         'parentnode__parentnode__parentnode__short_name'],
                                 subject=['parentnode__parentnode__parentnode__parentnode__id',
                                          'parentnode__parentnode__parentnode__parentnode__long_name',
                                          'parentnode__parentnode__parentnode__parentnode__short_name'])
        searchfields = FieldSpec('number',
                                 # assignmentgroup
                                 'parentnode__name',
                                 'parentnode__examiners__username',
                                 'parentnode__candidates__identifier',
                                 'parentnode__examiners__username',
                                 'parentnode__candidates__identifier',
                                 # assignment
                                 'parentnode__parentnode__long_name',
                                 'parentnode__parentnode__short_name',
                                 # period
                                 'parentnode__parentnode__parentnode__long_name',
                                 'parentnode__parentnode__parentnode__short_name',
                                 # subject
                                 'parentnode__parentnode__parentnode__parentnode__long_name',
                                 'parentnode__parentnode__parentnode__parentnode__short_name')
        methods = ['search', 'read']
