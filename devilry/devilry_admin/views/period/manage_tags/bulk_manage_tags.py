from __future__ import unicode_literals

import re
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.utils.translation import pgettext_lazy, ugettext_lazy
from django.views.generic import TemplateView
from django import forms
from django.contrib import messages

from django_cradmin import crapp
from django_cradmin.viewhelpers import listbuilderview
from django_cradmin.viewhelpers import multiselect2view
from django_cradmin.viewhelpers import multiselect2

from devilry.devilry_cradmin import devilry_listbuilder


class SelectMethodView(TemplateView):
    template_name = "devilry_admin/period/manage_tags/select-method.django.html"


class TagItemFrame(devilry_listbuilder.common.GoForwardLinkItemFrame):
    valuealias = 'tag'


class BaseTagListbuilderView(listbuilderview.View):
    frame_renderer_class = TagItemFrame

    def dispatch(self, request, *args, **kwargs):
        self.manage_tag = kwargs.get('manage_tag')
        return super(BaseTagListbuilderView, self).dispatch(request, *args, **kwargs)

    def get_value_and_frame_renderer_kwargs(self):
        return {
            'period': self.request.cradmin_role,
            'manage_tag': self.manage_tag
        }

    def get_queryset_for_role(self, role):
        raise NotImplementedError()


class TagMixin(object):
    def get_tag_class(self):
        return None


class BaseSelectedItem(multiselect2.selected_item_renderer.SelectedItem):
    valuealias = 'relateduser'


class BaseSelectedItemValue(multiselect2.listbuilder_itemvalues.ItemValue):
    valuealias = 'relateduser'
    selected_item_renderer_class = BaseSelectedItem

    def get_title(self):
        return self.relateduser.user.shortname


class BaseSelectedItemTargetRenderer(multiselect2.target_renderer.Target):
    def get_with_items_title(self):
        return pgettext_lazy('admin multiselect2_relateduser',
                             'Selected users')

    def get_without_items_text(self):
        return pgettext_lazy('admin multiselect2_relateduser',
                             'No relatedusers selected')


class SelectedRelatedUsersForm(forms.Form):
    invalid_relateduser_item_message = 'Invalid related user items was selected.'

    #: The items selected as ModelMultipleChoiceField.
    #: If some or all items should be selected by default, override this.
    selected_items = forms.ModelMultipleChoiceField(

        # No items are selectable by default.
        queryset=None,

        # Used if the object to select for some reason does
        # not exist(has been deleted or altered in some way)
        error_messages={
            'invalid_choice': invalid_relateduser_item_message,
        }
    )

    def __init__(self, *args, **kwargs):
        relatedusers_queryset = kwargs.pop('relatedusers_queryset')
        super(SelectedRelatedUsersForm, self).__init__(*args, **kwargs)
        self.fields['selected_items'].queryset = relatedusers_queryset


class SelectRelatedUsersTagInputForm(SelectedRelatedUsersForm):
    tag_text = forms.CharField(
        label='Tags',
        widget=forms.Textarea,
        help_text='Add tags here in comma-separated format: tag1, tag2, tag3')

    def clean(self):
        super(SelectRelatedUsersTagInputForm, self).clean()
        if 'tag_text' not in self.cleaned_data or len(self.cleaned_data['tag_text']) == 0:
            raise ValidationError(ugettext_lazy('Tag field is empty.'))
        tag_text = self.cleaned_data['tag_text']
        pattern = '^([^,](,)?)+'
        if not re.match(pattern, tag_text):
            raise ValidationError(
                {'tag_text': ugettext_lazy('Tag text must be in comma separated format! '
                                           'Example: tag1, tag2, tag3')}
            )
        tags_list = [tag_string.strip() for tag_string in tag_text.split(',') if len(tag_string) > 0]
        for tag in tags_list:
            if tags_list.count(tag) > 1:
                raise ValidationError(
                    {'tag_text': ugettext_lazy('"{}" occurs more than once in the form.'.format(tag))}
                )


class SelectItemTagInputTargetRenderer(BaseSelectedItemTargetRenderer):
    def get_field_layout(self):
        layout = super(SelectItemTagInputTargetRenderer, self).get_field_layout()
        layout.append('tag_text')
        return layout


class BaseMultiSelectView(multiselect2view.ListbuilderView):
    value_renderer_class = BaseSelectedItemValue

    def dispatch(self, request, *args, **kwargs):
        if 'tag' in kwargs:
            self.tag = kwargs.get('tag')
        return super(BaseMultiSelectView, self).dispatch(request, *args, **kwargs)

    def get_target_renderer_class(self):
        return BaseSelectedItemTargetRenderer

    def get_form_class(self):
        return SelectedRelatedUsersForm

    def get_form_kwargs(self):
        kwargs = super(BaseMultiSelectView, self).get_form_kwargs()
        kwargs['relatedusers_queryset'] = self.get_queryset_for_role(
            role=self.request.cradmin_role)
        return kwargs

    def get_selected_relatedusers(self, posted_form):
        return [related_user for related_user in posted_form.cleaned_data['selected_items']]

    def form_valid(self, form):
        self.add_success_message(self.get_success_message())
        return super(BaseMultiSelectView, self).form_valid(form)

    def add_success_message(self, message):
        if len(message) == 0:
            return
        messages.success(self.request, message=message)

    def add_warning_message(self, message):
        if len(message) == 0:
            return
        messages.warning(self.request, message=message)

    def get_success_message(self):
        return ''

    def get_tags_as_string(self, tags_list):
        tag_string = ''
        for tag in tags_list:
            tag_string = tag_string + ' ' + tag
        return tag_string


class AddTagMultiSelectView(TagMixin, BaseMultiSelectView):

    def get_added_tags(self, tags_string):
        return [tag.strip() for tag in tags_string.split(',') if len(tag) > 0]

    def instantiate_tag_class(self, tag, related_user):
        """
        Returns instance of tag class.

        Override in subclass and instantiate the tag class with values.
        """
        raise NotImplementedError()

    def get_related_user_tag_tags_as_list(self, related_user):
        """
        Get all the tags as a list for the ``related_user``.
        """
        raise NotImplementedError()

    def add_tags_to_relatedusers(self, related_users, added_tags_list):
        """
        Returns the number of users that were excluded. These students where excluded because they already had one or
        more of the tags added. They still get the tags they didn't already have.

        Args:
            related_users:
            added_tags_list:

        Returns:
            (int): Number of students that did had one or more of the tags added.
        """
        related_user_tags_list = []
        excluded_students_count = 0
        for tag in added_tags_list:
            for related_user in related_users:
                related_user_tags = self.get_related_user_tag_tags_as_list(related_user)
                if tag not in related_user_tags:
                    related_user_tags_list.append(
                        self.instantiate_tag_class(tag=tag, related_user=related_user)
                    )
                else:
                    excluded_students_count += 1
        tag_model_class = self.get_tag_class()
        tag_model_class.objects.bulk_create(related_user_tags_list)
        return excluded_students_count

    def form_valid(self, form):
        added_tags_list = self.get_added_tags(tags_string=form.cleaned_data['tag_text'])
        relatedusers = form.cleaned_data['selected_items']
        num_excluded_students = self.add_tags_to_relatedusers(
            related_users=relatedusers,
            added_tags_list=added_tags_list
        )
        if num_excluded_students == relatedusers.count():
            self.add_warning_message('Selected users was already registered with tags.')
        else:
            self.add_success_message('Tag(s) {} added'.format(self.get_tags_as_string(added_tags_list)))
            if num_excluded_students > 0:
                self.add_success_message('{} users were already registered with one or more of the tags. \n{}'.format(
                    num_excluded_students,
                    'They still got the new tags they didn\'t already have!'
                ))
        return super(AddTagMultiSelectView, self).form_valid(form)


class RemoveTagMultiSelectView(TagMixin, BaseMultiSelectView):

    def get_relateduser_ids_list(self, form):
        return [relateduser.id for relateduser in form.cleaned_data['selected_items']]

    def get_tag_queryset_to_delete(self, form):
        """
        Override this and return the appropriate tag queryset filtered on selected items in the form.
        """
        raise NotImplementedError()

    def delete_tags(self, form):
        tag_queryset = self.get_tag_queryset_to_delete(form)
        tag_queryset.filter(tag=self.tag).delete()

    def form_valid(self, form):
        self.delete_tags(form)
        return super(RemoveTagMultiSelectView, self).form_valid(form)
