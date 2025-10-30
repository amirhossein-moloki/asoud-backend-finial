from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.market.models import Market
from apps.product.models import Product
from apps.comment.serializers import CommentSerializer
from django_comments_xtd.models import XtdComment
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.db import models

class CommentView(APIView):
    def post(self, request):
        content_type = None
        object_id = None
        try:
            if request.data.get('content_type') == 'market':
                content_type = ContentType.objects.get_for_model(Market)
                object_id = request.data.get('object_id')

            elif request.data.get('content_type') == 'product':
                content_type = ContentType.objects.get_for_model(Product)
                object_id = request.data.get('object_id')
            
            site_id = get_current_site(request).id
            
            parent_id = request.data.get('parent_id') or 0
            if parent_id:
                # Validate that the parent comment exists
                try:
                    parent_comment = XtdComment.objects.get(id=parent_id)
                except XtdComment.DoesNotExist:
                    return Response({"error": "Parent comment does not exist"}, status=status.HTTP_400_BAD_REQUEST)

            comment = XtdComment(
                content_type=content_type,
                object_pk=object_id,
                user=request.user,
                comment=request.data.get('comment'),
                parent_id=parent_id,
                site_id=site_id
            )
            comment.save()
            
            return Response({"message": "Comment created", "id": comment.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error':str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CommentDetailView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, pk):
        try:
            comment = XtdComment.objects.get(pk=pk)
            serializer = CommentSerializer(comment)
        
            return Response(serializer.data)
        
        except XtdComment.DoesNotExist:
            return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)

class ContentCommentsView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, content_type, object_id):
        try:
            content_type_obj = ContentType.objects.get(model=content_type)
            comments = XtdComment.objects.filter(
                content_type=content_type_obj,
                object_pk=object_id,
                parent_id=models.F('id')
            ).order_by('submit_date')
            
            # Optionally, include replies
            serializer = CommentSerializer(comments, many=True, context={'depth': 1})
            return Response(serializer.data)
        
        except ContentType.DoesNotExist:
            return Response({"error": "Invalid content type"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class CommentUpdateView(APIView):
    def put(self, request, pk):
        try:
            comment = XtdComment.objects.get(pk=pk)
            if comment.user != request.user:
                return Response({"error": "You are not authorized to update this comment"}, status=status.HTTP_403_FORBIDDEN)
            
            serializer = CommentSerializer(comment, data=request.data)
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except XtdComment.DoesNotExist:
            return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)