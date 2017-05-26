import pprint

from django.utils import timezone
from django.contrib.auth import get_user_model

from devilry.apps.core.models import AssignmentGroup
from devilry.devilry_comment.models import Comment
from devilry.devilry_group.models import GroupComment, FeedbackSet
from devilry.devilry_import_v2database import modelimporter


class ImporterMixin(object):
    def _get_feedback_set_from_id(self, feedback_set_id):
        try:
            feedback_set = FeedbackSet.objects.get(id=feedback_set_id)
        except FeedbackSet.DoesNotExist:
            raise modelimporter.ModelImporterException(
                'FeedbackSet with id {} does not exist'.format(feedback_set_id))
        return feedback_set

    def _get_user_from_id(self, user_id):
        user_model = get_user_model()
        try:
            user = user_model.objects.get(id=user_id)
        except user_model.DoesNotExist:
            raise modelimporter.ModelImporterException(
                'User with id {} does not exist'.format(user_id))
        return user


class DeliveryImporter(ImporterMixin, modelimporter.ModelImporter):
    def get_model_class(self):
        return GroupComment

    def get_model_super_class(self):
        """
        Notes::
            We use the Comment(which GroupComment inherits from) to be able to set the sequencing number
            for Comment objects.
        """
        return Comment

    def _user_is_candidate_in_group(self, assignment_group, user):
        group_queryset = AssignmentGroup.objects.filter(id=assignment_group.id).filter_user_is_candidate(user=user)
        if group_queryset.count() == 0:
            return False
        return True

    def _create_group_comment_from_object_dict(self, object_dict):
        group_comment = self.get_model_class()()
        self.patch_model_from_object_dict(
            model_object=group_comment,
            object_dict=object_dict,
            attributes=[
                'pk',
                ('pk', 'id'),
                ('time_of_delivery', 'created_datetime'),
                ('time_of_delivery', 'published_datetime')
            ]
        )
        feedback_set = self._get_feedback_set_from_id(feedback_set_id=object_dict['fields']['deadline'])
        candidate_user = self._get_user_from_id(object_dict['fields']['delivered_by'])
        if self._user_is_candidate_in_group(assignment_group=feedback_set.group, user=candidate_user):
            group_comment.user = candidate_user
        else:
            raise modelimporter.ModelImporterException(
                'User is not Candidate on AssignmentGroup. '
                'This may be caused by an error in the V2 scripts for dumping.')
        group_comment.feedback_set = feedback_set
        group_comment.text = 'Delivery'
        group_comment.comment_type = GroupComment.COMMENT_TYPE_GROUPCOMMENT
        group_comment.user_role = GroupComment.USER_ROLE_STUDENT
        group_comment.full_clean()
        group_comment.save()
        self.log_create(model_object=group_comment, data=object_dict)

    def import_models(self, fake=False):
        directory_parser = self.v2delivery_directoryparser
        directory_parser.set_max_id_for_models_with_auto_generated_sequence_numbers(
            model_class=self.get_model_super_class())
        for object_dict in directory_parser.iterate_object_dicts():
            if fake:
                print('Would import: {}'.format(pprint.pformat(object_dict)))
            else:
                self._create_group_comment_from_object_dict(object_dict=object_dict)


class StaticFeedbackImporter(ImporterMixin, modelimporter.ModelImporter):
    def get_model_class(self):
        return GroupComment

    def _user_is_examiner_on_group(self, assignment_group, user):
        group_queryset = AssignmentGroup.objects\
            .filter(id=assignment_group.id)\
            .filter_user_is_examiner(user=user)
        if group_queryset.count() == 0:
            return False
        return True

    def _save_and_publish_feedback_set(self, feedback_set, published_by, grading_points, publish_datetime):
        """
        Args:
            feedback_set:
            published_by:
            grading_points:
            publish_datetime:
        """
        feedback_set.grading_published_by = published_by
        feedback_set.grading_points = grading_points
        feedback_set.grading_published_datetime = publish_datetime
        feedback_set.full_clean()
        feedback_set.save()

    def _create_group_comment_from_object_dict(self, object_dict):
        group_comment = self.get_model_class()()
        self.patch_model_from_object_dict(
            model_object=group_comment,
            object_dict=object_dict,
            attributes=[
                ('save_timestamp', 'created_datetime'),
                ('save_timestamp', 'published_datetime')
            ]
        )
        feedback_set = self._get_feedback_set_from_id(feedback_set_id=object_dict['fields']['deadline_id'])
        examiner_user = self._get_user_from_id(object_dict['fields']['saved_by'])
        if self._user_is_examiner_on_group(assignment_group=feedback_set.group, user=examiner_user):
            group_comment.user = examiner_user
        else:
            raise modelimporter.ModelImporterException(
                'User is not Examiner on AssignmentGroup. '
                'This may be caused by an error in the V2 scripts for dumping.')
        self._save_and_publish_feedback_set(
            feedback_set=feedback_set,
            published_by=examiner_user,
            grading_points=object_dict['fields']['points'],
            publish_datetime=object_dict['fields']['save_timestamp']
        )
        group_comment.feedback_set = feedback_set
        group_comment.text = object_dict['fields']['rendered_view']
        group_comment.comment_type = GroupComment.COMMENT_TYPE_GROUPCOMMENT
        group_comment.user_role = GroupComment.USER_ROLE_EXAMINER
        group_comment.full_clean()
        group_comment.save()
        self.log_create(model_object=group_comment, data=object_dict)

    def import_models(self, fake=False):
        for object_dict in self.v2staticfeedback_directoryparser.iterate_object_dicts():
            if fake:
                print('Would import: {}'.format(pprint.pformat(object_dict)))
            else:
                self._create_group_comment_from_object_dict(object_dict=object_dict)