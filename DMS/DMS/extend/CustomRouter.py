"""
Routers provide a convenient and consistent way of automatically
determining the URL conf for your API.

They are used by simply instantiating a Router class, and then registering
all the required ViewSets with that router.

For example, you might have a `urls.py` that looks something like this:

    router = routers.DefaultRouter()
    router.register('users', UserViewSet, 'user')
    router.register('accounts', AccountViewSet, 'account')

    urlpatterns = router.urls
"""
from __future__ import unicode_literals

import itertools
from collections import OrderedDict, namedtuple

from django.conf.urls import url
from rest_framework.routers import DefaultRouter

Route = namedtuple('Route', ['url', 'mapping', 'name', 'initkwargs'])
MuiltpleEntranceRoute = namedtuple('MuiltpleEntranceRoute', [
                                   'url', 'mapping', 'name', 'initkwargs'])
DynamicDetailRoute = namedtuple(
    'DynamicDetailRoute', ['url', 'name', 'initkwargs'])
DynamicListRoute = namedtuple(
    'DynamicListRoute', ['url', 'name', 'initkwargs'])


def escape_curly_brackets(url_path):
    """
    Double brackets in regex of url_path for escape string formatting
    """
    if ('{' and '}') in url_path:
        url_path = url_path.replace('{', '{{').replace('}', '}}')
    return url_path


def replace_methodname(format_string, methodname):
    """
    Partially format a format_string, swapping out any
    '{methodname}' or '{methodnamehyphen}' components.
    """
    methodnamehyphen = methodname.replace('_', '-')
    ret = format_string
    ret = ret.replace('{methodname}', methodname)
    ret = ret.replace('{methodnamehyphen}', methodnamehyphen)
    return ret


def flatten(list_of_lists):
    """
    Takes an iterable of iterables, returns a single iterable containing all items
    """
    return itertools.chain(*list_of_lists)


class MultipleEntranceRouter(DefaultRouter):
    routes = [
        # List route.
        Route(
            url=r'^{prefix}{trailing_slash}$',
            mapping={
                'get': 'list',
                'post': 'create'
            },
            name='{basename}-list',
            initkwargs={'suffix': 'List'}
        ),
        MuiltpleEntranceRoute(
            url=r'^{foreign_field}/{prefix}{trailing_slash}$',
            mapping={
                'get': 'list',
                'post': 'create'
            },
            name='{foreign_field}-{basename}-list',
            initkwargs={'suffix': 'List'}
        ),
        MuiltpleEntranceRoute(
            url=r'^{foreign_field}/{prefix}/{lookup}{trailing_slash}$',
            mapping={
                'get': 'retrieve',
                'put': 'update',
                'patch': 'partial_update',
                'delete': 'destroy'
            },
            name='{foreign_field}-{basename}-detail',
            initkwargs={'suffix': 'Instance'}
        ),
        # Dynamically generated list routes.
        # Generated using @list_route decorator
        # on methods of the viewset.
        DynamicListRoute(
            url=r'^{prefix}/{methodname}{trailing_slash}$',
            name='{basename}-{methodnamehyphen}',
            initkwargs={}
        ),
        # Detail route.
        Route(
            url=r'^{prefix}/{lookup}{trailing_slash}$',
            mapping={
                'get': 'retrieve',
                'put': 'update',
                'patch': 'partial_update',
                'delete': 'destroy'
            },
            name='{basename}-detail',
            initkwargs={'suffix': 'Instance'}
        ),
        # Dynamically generated detail routes.
        # Generated using @detail_route decorator on methods of the viewset.
        DynamicDetailRoute(
            url=r'^{prefix}/{lookup}/{methodname}{trailing_slash}$',
            name='{basename}-{methodnamehyphen}',
            initkwargs={}
        ),
    ]

    def get_nested_lookup_regex(self, viewset, lookup_prefix=''):
        """
        Given a viewset, return the portion of URL regex that is used
        to match against a single instance.

        Note that lookup_prefix is not used directly inside REST rest_framework
        itself, but is required in order to nicely support nested router
        implementations, such as drf-nested-routers.

        https://github.com/alanjds/drf-nested-routers
        """
        base_regex = '(?P<{lookup_prefix}__{lookup_url_kwarg}>{lookup_value})'
        # Use `pk` as default field, unset set.  Default regex should not
        # consume `.json` style suffixes and should break at '/' boundaries.
        lookup_field = getattr(viewset, 'lookup_field', 'pk')
        lookup_url_kwarg = getattr(
            viewset, 'lookup_url_kwarg', None) or lookup_field
        lookup_value = getattr(viewset, 'lookup_value_regex', '[^/.]+')
        return base_regex.format(
            lookup_prefix=lookup_prefix,
            lookup_url_kwarg=lookup_url_kwarg,
            lookup_value=lookup_value
        )

    def get_nested_lookup_key(self, viewset, lookup_prefix=''):
        """
        Given a viewset, return the portion of URL regex that is used
        to match against a single instance.

        Note that lookup_prefix is not used directly inside REST rest_framework
        itself, but is required in order to nicely support nested router
        implementations, such as drf-nested-routers.

        https://github.com/alanjds/drf-nested-routers
        """
        base = '{lookup_prefix}__{lookup_url_kwarg}'
        # Use `pk` as default field, unset set.  Default regex should not
        # consume `.json` style suffixes and should break at '/' boundaries.
        lookup_field = getattr(viewset, 'lookup_field', 'pk')
        lookup_url_kwarg = getattr(
            viewset, 'lookup_url_kwarg', None) or lookup_field
        lookup_value = getattr(viewset, 'lookup_value_regex', '[^/.]+')
        return base.format(
            lookup_prefix=lookup_prefix,
            lookup_url_kwarg=lookup_url_kwarg,
            lookup_value=lookup_value
        )

    def get_foreign_chain(self, viewset, multiple_routes):
        foreign_lookup_field = getattr(viewset, 'foreign_lookup_field', None)

        if foreign_lookup_field is None:
            return

        multiple_routes.append({viewset: foreign_lookup_field})
        for viewset, pk in foreign_lookup_field.items():
            self.get_foreign_chain(viewset, multiple_routes)

    def replace_foreign_field(self, format_string, chains):
        ret = format_string
        # [{<class 'Accession.views.ViewSet'>: {<class 'Case.views.ViewSet'>: 'case_id'}}, {<class 'Case.views.ViewSet'>: {<class 'Patient.views.ViewSet'>: 'patient_id'}}]
        # change placeholder to ViewSet and format it later.
        for chain in chains:
            for _, args in chain.items():
                for viewset, lookup in args.items():

                    lookup = self.get_nested_lookup_regex(
                        viewset, lookup)

                    for prefix, registd_viewset, basenae in self.registry:
                        if registd_viewset is viewset:
                            ret = ret.replace(
                                '{foreign_field}', '{{foreign_field}}/{viewset}/{lookup}'.format(
                                    viewset=prefix, lookup=lookup))
        return ret

    def get_routes(self, viewset):
        """
        Augment `self.routes` with any dynamically generated routes.

        Returns a list of the Route namedtuple.
        """
        # converting to list as iterables are good for one pass, known host needs to be checked again and again for
        # different functions.
        known_actions = list(flatten(
            [route.mapping.values() for route in self.routes if isinstance(route, Route)]))

        # Determine any `@detail_route` or `@list_route` decorated methods on
        # the viewset
        detail_routes = []
        list_routes = []
        multiple_routes = []
        self.get_foreign_chain(viewset, multiple_routes)

        for methodname in dir(viewset):
            attr = getattr(viewset, methodname)
            httpmethods = getattr(attr, 'bind_to_methods', None)
            detail = getattr(attr, 'detail', True)

            if httpmethods:
                # checking method names against the known actions list
                if methodname in known_actions:
                    raise ImproperlyConfigured('Cannot use @detail_route or @list_route '
                                               'decorators on method "%s" '
                                               'as it is an existing route' % methodname)
                httpmethods = [method.lower() for method in httpmethods]
                if detail:
                    detail_routes.append((httpmethods, methodname))
                else:
                    list_routes.append((httpmethods, methodname))

        def _get_dynamic_routes(route, dynamic_routes):
            ret = []
            for httpmethods, methodname in dynamic_routes:
                method_kwargs = getattr(viewset, methodname).kwargs
                initkwargs = route.initkwargs.copy()
                initkwargs.update(method_kwargs)
                url_path = initkwargs.pop("url_path", None) or methodname
                url_path = escape_curly_brackets(url_path)
                url_name = initkwargs.pop("url_name", None) or url_path
                ret.append(Route(
                    url=replace_methodname(route.url, url_path),
                    mapping={
                        httpmethod: methodname for httpmethod in httpmethods},
                    name=replace_methodname(route.name, url_name),
                    initkwargs=initkwargs,
                ))
            return ret

        def _get_muilteple_entrance_routes(route, multiple_routes):
            ret = []
            # insert multiple entrance before prefix
            chains = []
            for chain in multiple_routes:
                chains.append(chain)
                url = self.replace_foreign_field(
                    route.url, chains)
                mapping = route.mapping.copy()
                name = self.replace_foreign_field(
                    route.name, chains)
                initkwargs = route.initkwargs.copy()
                ret.append(MuiltpleEntranceRoute(
                    url=url,
                    mapping=mapping,
                    name=name,
                    initkwargs=initkwargs
                ))
            return ret

        ret = []
        for route in self.routes:
            if isinstance(route, DynamicDetailRoute):
                # Dynamic detail routes (@detail_route decorator)
                ret += _get_dynamic_routes(route, detail_routes)
            elif isinstance(route, DynamicListRoute):
                # Dynamic list routes (@list_route decorator)
                ret += _get_dynamic_routes(route, list_routes)
            elif isinstance(route, MuiltpleEntranceRoute):
                ret += _get_muilteple_entrance_routes(route, multiple_routes)
            else:
                # Standard route
                ret.append(route)
        return ret

    def get_urls(self):
        """
        Use the registered viewsets to generate a list of URL patterns.
        """
        ret = []

        for prefix, viewset, basename in self.registry:
            lookup = self.get_lookup_regex(viewset).format()
            routes = self.get_routes(viewset)
            for route in routes:
                # Only actions which actually exist on the viewset will be
                # bound
                mapping = self.get_method_map(viewset, route.mapping)
                if not mapping:
                    continue

                # Build the url pattern

                # TODO format viewset and viewset's lookup field
                regex = route.url.format(
                    foreign_field='',
                    prefix=prefix,
                    lookup=lookup,
                    trailing_slash=self.trailing_slash
                )
                # # If there is no prefix, the first part of the url is probably
                # #   controlled by project's urls.py and the router is in an app,
                # #   so a slash in the beginning will (A) cause Django to give
                # # warnings and (B) generate URLS that will require using '//'.
                if not prefix and regex[:2] == '^/':
                    regex = '^' + regex[2:]
                if prefix and regex[:2] == '^/':
                    regex = '^' + regex[2:]
                view = viewset.as_view(mapping, **route.initkwargs)
                name = route.name.format(foreign_field='', basename=basename)
                url_patten = url(regex, view, name=name)
                ret.append(url_patten)
        return ret
