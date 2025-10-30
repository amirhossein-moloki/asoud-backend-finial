from rest_framework import serializers
from django_comments_xtd.models import XtdComment

class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        # Decrease the depth by 1 for nested comments
        if 'depth' in self.context:
            self.context['depth'] -= 1
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data
    
class CommentSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = XtdComment
        fields = [
            'id', 'user', 'comment', 'submit_date', 'parent_id', 'level', 'children'
        ]

    def get_children(self, obj):
        # Fetch child comments for the current comment
        children = XtdComment.objects.filter(
            parent_id=obj.id,
        ).exclude(
            id=obj.id
        )
        
        # Check if the depth limit has been reached
        depth = self.context.get('depth', 1)
        if depth <= 0:
            return []
        
        # Serialize child comments with reduced depth
        serializer = CommentSerializer(children, many=True, context={'depth': depth - 1})
        return serializer.data
    