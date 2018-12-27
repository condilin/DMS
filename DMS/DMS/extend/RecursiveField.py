from rest_framework import serializers


class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        view = self.context.get('view')
        if view:
            self._queryset = view.get_queryset()
            if value in self._queryset:
                serializer = self.parent.parent.__class__(value, context=self.context)
                return serializer.data
            else:
                return {}
        else:
            raise Exception('no view get')


class MaxDepthRecursiveField(serializers.Serializer):
    """
    Can be used as a field within another serializer,
    to produce nested-recursive relationships. Works with
    through models, and limited and/or arbitrarily deep trees.
    """
    def __init__(self, **kwargs):
        self._recurse_through = kwargs.pop('through_serializer', None)
        self._recurse_max = kwargs.pop('max_depth', None)
        self._recurse_view = kwargs.pop('reverse_name', None)
        self._recurse_attr = kwargs.pop('reverse_attr', None)
        self._recurse_many = kwargs.pop('many', False)
        super(RecursiveField, self).__init__(**kwargs)
    
    def to_representation(self, value):
        self._queryset = self.context.get('view').get_queryset()
        parent = self.parent
        if isinstance(parent, serializers.ListSerializer):
            parent = parent.parent

        lvl = getattr(parent, '_recurse_lvl', 1)
        max_lvl = self._recurse_max or getattr(parent, '_recurse_max', None)

        # Defined within RecursiveField(through_serializer=A)
        serializer_class = self._recurse_through
        is_through = has_through = True

        # Informed by previous serializer (for through m2m)
        if not serializer_class:
            is_through = False
            serializer_class = getattr(parent, '_recurse_next', None)

        # Introspected for cases without through models.
        if not serializer_class:
            has_through = False
            serializer_class = parent.__class__

        if is_through or not max_lvl or lvl <= max_lvl: 
            serializer = serializer_class(
                value, many=self._recurse_many, context=self.context)

            # Propagate hereditary attributes.
            serializer._recurse_lvl = lvl + is_through or not has_through
            serializer._recurse_max = max_lvl

            if is_through:
                # Delay using parent serializer till next lvl.
                serializer._recurse_next = parent.__class__

            return serializer.data
        else:
            view = self._recurse_view or self.context['request'].resolver_match.url_name
            attr = self._recurse_attr or 'id'
            return reverse(view, args=[getattr(value, attr)],
                           request=self.context['request'])