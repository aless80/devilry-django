from logging import getLogger
from djangorestframework.compat import apply_markdown
from djangorestframework.views import _remove_leading_indent
from djangorestframework.mixins import ListModelMixin
from djangorestframework.mixins import CreateModelMixin
from django.utils.safestring import mark_safe
from cStringIO import StringIO

from .errors import PermissionDeniedError
from .auth import nodeadmin_required

logger = getLogger(__name__)



class BaseNodeInstanceRestMixin(object):
    """
    Implements ``put``, ``delete`` and ``get_queryset`` that should work for
    any :class:`devilry.apps.core.models.BaseNode` subclass.
    """

    def put(self, request, id=None):
        subject = super(BaseNodeInstanceRestMixin, self).put(request, id=id)
        modelname = self.resource.model.__name__
        logger.info('User=%s updated %s id=%s (%s)', self.user, modelname, id, subject)
        return subject

    def get_queryset(self):
        qry = self.resource.model.where_is_admin_or_superadmin(self.user)
        # NOTE: Using prefetch_related will make return from PUT be wrong
        #       because the cached value will be returned, not the updated one.
        #qry = qry.prefetch_related('admins__devilryuserprofile')
        qry = qry.order_by('short_name')
        return qry

    def can_delete(self):
        return self._get_instance_or_404().can_delete()

    def _get_instance_or_404(self, *args, **kwargs):
        from djangorestframework.response import ErrorResponse
        from djangorestframework import status

        model = self.resource.model
        query_kwargs = self.get_query_kwargs(self.request, *args, **kwargs)
        try:
            return self.get_instance(**query_kwargs)
        except model.DoesNotExist:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND, None, {})

    def delete(self, request, *args, **kwargs):
        instance = self._get_instance_or_404(*args, **kwargs)
        instanceid = instance.id
        instanceident = unicode(instance)
        modelname = self.resource.model.__name__
        if instance.can_delete(self.user):
            instance.delete()
            logger.info('User=%s deleted %s id=%s (%s)', self.user, modelname, instanceid, instanceident)
            return {'id': instanceid}
        else:
            logger.warn(('User=%s tried to delete %s id=%s (%s). They where rejected '
                         'because of lacking permissions. Since the user-interface '
                         'should make it impossible to perform this action, huge amounts of '
                         'such attempts by this user may be an attempt at trying '
                         'to delete things that they should not attempt to delete.'),
                        self.user, modelname, instanceid, instanceident)
            msg = ('Not permitted to delete {modelname} with id={instanceid}. '
                   'Only superadmins can delete non-empty items.')
            raise PermissionDeniedError(msg.format(modelname=modelname,
                                                   instanceid=instanceid))


class SelfdocumentingMixin(object):
    '''
    ``djangorestframework`` view mixin that makes it more convenient to provide
    docs. Docs can be provided in the following ways:

        - Add to the class docstring.
        - Add to the docstring for the REST methods.
        - Add ``<methodname>_resdocs()`` methods (see example below).

    All docs are formatted using Markdown. Design rationale:

        - Use markdown to make it backwards compatible with the default
          self-documenting features of djangorestframework, and because
          markdown is a good and easy-to-extend markup language for HTML
          generation.
        - Minimal amounts of magic.

    Simple example::

        from djangorestframework.views import View
        class MyView(SelfdocumentingMixin, View):
            """
            This appears at the top of the autogenerated docs.
            """
            form = SomeForm

            def post(self, request):
                """
                Create something. Shows up under the "POST" heading.
                """
                pass


    Get docs from a method instead of from the docstring. Useful when
    generating docs, or when inheriting REST methods (E.g.: from ModelView)::

        class MyView(SelfdocumentingMixin, View):
            def get(self, request):
                pass

            def get_restdocs(self):
                return """
                This will be used a the docs for the GET method, just as if we
                provided a docstring to ``get()``, however with this method of
                providing docs, we can generate/program the contents of the
                docstring.
                """

    Provide template variables for the docstrings::

        class MyView(SelfdocumentingMixin, View):

            def put(self):
                """
                Update something.

                ## Parameters:
                {paramteterstable}
                """

            def postprocess_docs(self, docs):
                return docs.format(paramteterstable=self.htmlformat_parameters_from_form())

            def post(self):
                """
                ## Parameters
                {paramteterstable}
                """

            def postprocess_post_docs(self, docs):
                """
                Overrides postprocess_docs() for the POST docs.
                """
                params = self.html_create_attrtable({'id': {'help': 'The ID of the deleted object.'}})
                return docs.format(paramteterstable=params)
    '''

    def get_unformatted_docs_for_method(self, methodname):
        """
        Get docs for the given method. Tries to find docs in the following
        places, in the followin order:

            - ``self.<methodname>_resdocs()`` (if it exists)
            - ``self.<methodname>.__doc__``

        :param methodname: Lower-case method name (E.g.: get, post, ...)
        :return:
            Docs as a string with leading indent removed
            (:meth:`.remove_leading_indent_from_docs`), or ``None`` if no docs
            was found.
        """
        if not hasattr(self, methodname):
            return None
        docsmethodname = methodname + '_restdocs'
        if hasattr(self, docsmethodname):
            docs = getattr(self, docsmethodname)()
        else:
            docs = getattr(self, methodname).__doc__
        if docs:
            docs = self.remove_leading_indent_from_docs(docs)
        return docs

    def remove_leading_indent_from_docs(self, docs):
        """
        Remove leading indentation from the given docs.
        """
        return _remove_leading_indent(docs)


    def html_create_attrtablerow(self, fieldname, meta='', help=''):
        """
        Create a HTML table row with one cell for fieldname and optional meta,
        and one cell for field-help.

        :param fieldname:
            Name of the field.
        :param meta:
            Short metadata string, such as "required" or "optional".
        :param help:
            Help text for the field. Formatted using :meth:`.convert_docs_to_html`.
        """
        out = StringIO()
        out.write('<tr>')
        out.write('<td><p><strong>{fieldname}</strong>'.format(fieldname=fieldname))
        if meta:
            out.write('<br/><small>{meta}</small>'.format(meta=meta))
        out.write('</p></td>')
        out.write('<td>{help}</td>'.format(help=self.convert_docs_to_html(help)))
        out.write('</tr>')
        return out.getvalue()

    def html_create_attrtable(self, fieldshelp):
        """
        Create a HTML formatted table of attributes with help and optinal meta
        (such as required or optional).

        :param fieldshelp:
            List of dicts. Each dict is parameters for :meth:`.html_create_attrtablerow`.
        """
        out = StringIO()
        out.write('<table>')
        for fieldname in sorted(fieldshelp.keys()):
            rowspec = fieldshelp[fieldname]
            out.write(self.html_create_attrtablerow(fieldname=fieldname, **rowspec))
        out.write('</table>')
        return out.getvalue()

    def htmlformat_parameters_from_form(self, boundform=None, override_helptext={}):
        """
        Generate parameter docs from the given bound form as a html table.

        :param boundform:
            Defaults to ``self.get_bound_form()`` if it is ``None``.
        :param override_helptext:
            Override helptext for specific fields. Keys are fieldnames,
            and values are overridden helptext for that field.

        .. seealso:: :meth:`.htmlformat_response_from_fields`, :meth:`.html_create_attrtable`.
        """
        form = boundform or self.get_bound_form()
        fieldshelp = {}
        for field in form:
            if field.field.required:
                meta = 'required'
            else:
                meta = 'optional'
            help = override_helptext.get(field.name, field.field.help_text)
            fieldshelp[field.name] = dict(meta=meta, help=help)
        return self.html_create_attrtable(fieldshelp)

    def htmlformat_response_from_fields(self, boundform=None, specify_helptext={}):
        """
        Uses :meth:`.html_create_attrtable` to create a table documenting the
        response from GET/POST/PUT. Creates the ``fieldshelp`` parameter by:

            - Adding all fields in ``boundform`` that are in
              ``self.resource.fields`` (get help from the field help_text).
            - Add fields from ``specify_helptext`` (overrides fields from ``boundform``).

        :param boundform:
            Defaults to ``self.get_bound_form()`` if it is ``None``.
        :param specify_helptext:
            Mapping of fieldname to help-text for that field. Overrides help
            from ``boundform``.  Keys can be any fieldname from
            ``self.resource.fields``.
        :return: A HTML table.
        :rtype: str
        """
        fieldshelp = {}
        form = boundform or self.get_bound_form()
        for field in form:
            if field.name in self.resource.fields:
                help = field.field.help_text
                fieldshelp[field.name] = dict(help=help)
        for fieldname in self.resource.fields:
            help = specify_helptext.get(fieldname, '')
            if not help and fieldname in fieldshelp:
                continue # Use form-help if help is not in specify_helptext
            fieldshelp[fieldname] = dict(help=help)
        return self.html_create_attrtable(fieldshelp)

    def convert_docs_to_html(self, docs):
        """
        Convert the given docs to to html.
        Defaults to formatting the docs using markdown, but you can override
        this method if you want something else.
        """
        return apply_markdown(docs)

    def format_methodheading_for_docs(self, methodname):
        """
        Format the documentation heading for the given method. Defaults to a
        mardown-formatted H1 heading containing the uppercased methodname.

        :param methodname: The method name in lowercase.

        .. seealso:: meth:`convert_docs_to_html`.
        """
        return '\n# {methodname}\n'.format(methodname=methodname.upper())

    def get_unformatted_docs_for_class(self):
        return self.remove_leading_indent_from_docs(self.__doc__ or '')

    def class_htmldocs(self):
        return self.convert_docs_to_html(self.get_unformatted_docs_for_class())

    def method_htmldocs(self, methodname):
        unformatted_docs = self.get_unformatted_docs_for_method(methodname)
        if unformatted_docs:
            htmldocs = self.convert_docs_to_html(unformatted_docs)
            return '<h1>{methodname}</h1>\n{htmldocs}'.format(methodname=methodname.upper(),
                                                              htmldocs=htmldocs)
        else:
            return None

    def get_htmldocs(self):
        return self.method_htmldocs('get')

    def post_htmldocs(self):
        return self.method_htmldocs('post')

    def put_htmldocs(self):
        return self.method_htmldocs('put')

    def delete_htmldocs(self):
        return self.method_htmldocs('delete')

    def _postprocess_docs(self, htmldocs, methodname=None):
        if methodname:
            postprocess_method = 'postprocess_{methodname}_docs'.format(methodname=methodname)
            if hasattr(self, postprocess_method):
                return getattr(self, postprocess_method)(htmldocs)
        if hasattr(self, 'postprocess_docs'):
            return self.postprocess_docs(htmldocs)
        return htmldocs

    def _htmlformat_traceback(self, title):
        from traceback import format_tb
        import sys
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback = format_tb(exc_traceback)
        errortraceback = ''.join(['Traceback (most recent call last):\n'] + traceback + ['{0}: {1}'.format(exc_type.__name__, exc_value)])
        htmlmsg = ('<h1 style="color:#a00">ERROR: {title}</h1>'
                   '<p>This is shown here instead of throwing an exception because '
                   'the framework swallows exceptions. Error traceback: '
                   '<pre style="color:#a00">{traceback}</pre>'
                   '</p>').format(title=title,
                                  traceback=errortraceback)
        return htmlmsg

    def all_htmldocs(self):
        """
        Get the HTML-formatted docs for this view.
        """
        classhtmldocs = self.class_htmldocs()
        docs = []
        if classhtmldocs:
            try:
                docs.append(self._postprocess_docs(classhtmldocs))
            except Exception, e:
                docs.append(self._htmlformat_traceback('Failed to parse class docs (global API docs)'))
        for methodname in self.allowed_methods:
            methodname = methodname.lower()
            htmlmethod = '{methodname}_htmldocs'.format(methodname=methodname)
            if not hasattr(self, htmlmethod):
                continue
            try:
                htmldocs = getattr(self, htmlmethod)()
                if htmldocs:
                    docs.append(self._postprocess_docs(htmldocs, methodname))
            except Exception, e:
                docs.append(self._htmlformat_traceback('Failed to parse docs for {0}'.format(methodname.upper())))
        return '\n\n'.join(docs)

    def get_description(self, html=False):
        html = self.all_htmldocs()
        return mark_safe(html)


inherited_admins_help = """
List of inherited administrators. Each entry in the list is a map/object
with the following attributes:

- ``user``: Same format as the entries in ``admins``.
- ``basenode``: Map/object with the following attributes:
    - ``type``: The type of the basenode.
    - ``path``: Unique path to the basenode.
    - ``id``: The ID of the basenode.
"""

breadcrumb_help = """
List of parentnodes with topmost node first in the list, and the direct
parentnode of the current basenode at the end of the list. Each entry in the list
is a map/object with the following attributes:

- ``id``: The ID of the basenode.
- ``short_name``: The short name of the basenode.
- ``type``: The type of the basenode.
"""


class SelfdocumentingBaseNodeMixin(SelfdocumentingMixin):
    """
    Mixin for documentation generation for BaseNode REST APIs.
    """

    def htmldoc_responsetable(self):
        specify_helptext = {'inherited_admins': inherited_admins_help,
                            'breadcrumb': breadcrumb_help,
                            'can_delete': 'Can the authenticated user delete this object?',
                            'parentnode': 'ID of the parentnode.',
                            'id': 'The unique ID of the object.'}
        return self.htmlformat_response_from_fields(specify_helptext=specify_helptext)

    def htmldoc_delete_responsetable(self):
        return self.html_create_attrtable({'id': {'help': 'The ID of the deleted object.'}})

    def htmldoc_parameterstable(self):
        return self.htmlformat_parameters_from_form()


from django import forms
class FilterBaseNodeQuerySetForm(forms.Form):
    parentnode = forms.IntegerField(required=False)


class GetParamFormMixin(object):
    #: The form class to use to evaluate the GET parameters.
    getparam_form = None


    @property
    def GETPARAMS(self):
        if not hasattr(self, '_GETPARAMS'):
            self._GETPARAMS = self._parse_getparam_form()
        return self._GETPARAMS

    def _parse_getparam_form(self):
        """
        Parse the GET params using :obj:`.getparam_form`, and place the results
        in ``self.GETPARAMS``.

        :raise ErrorResponse: If validation fails.
        """
        bound_form = self.getparam_form(self.request.GET)
        if bound_form.is_valid():
            return bound_form.cleaned_data
        else:
            detail = {}

            # Add any non-field errors
            if bound_form.non_field_errors():
                detail[u'errors'] = bound_form.non_field_errors()

            # Add standard field errors
            field_errors = dict((key, map(unicode, val))
                                for (key, val) in bound_form.errors.iteritems()
                                if not key.startswith('__'))

            if field_errors:
                detail[u'field_errors'] = field_errors
            from djangorestframework import status
            from djangorestframework.response import ErrorResponse
            raise ErrorResponse(status.HTTP_400_BAD_REQUEST, detail)


class BaseNodeListModelMixin(ListModelMixin, GetParamFormMixin):
    getparam_form = FilterBaseNodeQuerySetForm

    def get_restdocs(self):
        return """
        List the {modelname} where the authenticated user is admin.

        # Parameters
        {parameterstable}

        # Returns
        List of maps/dicts with the following attributes:
        {responsetable}
        """

    def postprocess_get_docs(self, docs):
        parameterstable = self.html_create_attrtable({'parentnode': {'help': 'The ID of a parentnode. Restrict response to items within the parentnode.',
                                                                     'meta': 'optional'}})
        return docs.format(modelname=self.resource.model.__name__,
                           responsetable=self.htmldoc_responsetable(),
                           parameterstable=parameterstable)

    def get_queryset(self):
        qry = self.resource.model.where_is_admin_or_superadmin(self.user)
        if self.GETPARAMS['parentnode'] != None:
            qry = qry.filter(parentnode=self.GETPARAMS['parentnode'])
        qry = qry.order_by('short_name')
        return qry


class BaseNodeCreateModelMixin(CreateModelMixin):
    def _require_nodeadmin(self, user):
        if not 'parentnode' in self.CONTENT:
            raise PermissionDeniedError('parentnode is a required parameter.')
        parentnode = self.CONTENT['parentnode']
        nodeadmin_required(user, parentnode.id)

    def post(self, request):
        """
        Create new {modelname}.

        # Parameters
        {create_paramteterstable}
        """
        self._require_nodeadmin(request.user)
        return super(BaseNodeCreateModelMixin, self).post(request)

    def postprocess_post_docs(self, docs):
        return docs.format(create_paramteterstable=self.htmldoc_parameterstable(),
                           modelname=self.resource.model.__name__)
