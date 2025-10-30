from apps.sms.models import BulkSms, PatternSms, Line, Template
from rest_framework import views, status
from rest_framework.response import Response
from utils.response import ApiResponse
import logging

logger = logging.getLogger(__name__)
from apps.sms.serializers.admin import (
    LineSerializer,
    TemplateSerializer,
    BulkSerializer,
    PatternSerializer
)
from apps.sms.sms_core import SMSCoreHandler


class LineCreateView(views.APIView):
    def post(self, request):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = LineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(
            ApiResponse(
                success=True,
                code=201,
                data=serializer.data
            )
        )


class LineUpdateView(views.APIView):
    def put(self, request, pk=None):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            line = Line.objects.get(id=pk)
            serializer = LineSerializer(line, request.data, partial=True)
            serializer.is_valid(raise_exception=True)

            serializer.save()

            return Response(
                ApiResponse(
                    success=True,
                    code=201,
                    data=serializer.data
                )
            )
        except Line.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Line Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )
    

class LineListView(views.APIView):
    def get(self, request):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                ApiResponse(
                    success=True,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        lines = Line.objects.all()
        serializer = LineSerializer(lines, many=True)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

class LineDeleteView(views.APIView):
    def delete(self, request, pk):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                ApiResponse(
                    success=True,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            line = Line.objects.get(id=pk)
        except Line.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Line Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        line.delete()
        return Response(
            ApiResponse(
                success=True,
                code=204
            ),
            status=status.HTTP_204_NO_CONTENT
        )

class TemplateCreateView(views.APIView):
    def post(self, request):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                ApiResponse(
                    success=True,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
    
        serializer = TemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(
            ApiResponse(
                success=True,
                code=201,
                data=serializer.data
            )
        )
    
class TemplateListView(views.APIView):
    def get(self, request):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                ApiResponse(
                    success=True,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        templates = Template.objects.all()
        serializer = TemplateSerializer(templates, many=True)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

class TemplateUpdateView(views.APIView):
    def put(self, request, pk):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                ApiResponse(
                    success=True,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            template = Template.objects.get(id=pk)
        except Template.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Template Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = TemplateSerializer(template, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        new_template = serializer.save()

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

class TemplateDeleteView(views.APIView):
    def delete(self, request, pk):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                ApiResponse(
                    success=True,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            template = Template.objects.get(id=pk)
        except Template.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Template Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        template.delete()
        return Response(
            ApiResponse(
                success=True,
                code=204
            ),
            status=status.HTTP_204_NO_CONTENT
        )


class BulkSmsDetailView(views.APIView):
    def get(self, request, pk):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                ApiResponse(
                    success=True,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            sms = BulkSms.objects.get(id=pk)
        except:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="SMS Not Found"
                )
            )
        
        serializer = BulkSerializer(sms)
        
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

class BulkSmsListView(views.APIView):
    def get(self, request):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                ApiResponse(
                    success=True,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )

        sms = BulkSms.objects.all()
        serializer = BulkSerializer(sms, many=True)
        
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )
    
class BulkSmsUpdateView(views.APIView):
    def put(self, request, pk):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                ApiResponse(
                    success=True,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            sms = BulkSms.objects.get(pk)
        except:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="SMS Not Found"
                )
            )
        
        serializer = BulkSerializer(sms, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # send the actual sms
        payload = {
            'lineNumber': sms.line,
            'messageText': sms.content,
            'mobiles': sms.to,
            'sendDateTime': None
        }
        
        result = SMSCoreHandler.send_bulk(payload=payload)
        logger.info(f'Bulk SMS result: {result}')


        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )


class PatternSmsDetailView(views.APIView):
    def get(self, request, pk):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                ApiResponse(
                    success=True,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            sms = PatternSms.objects.get(id=pk)
        except:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="SMS Not Found"
                )
            )
        
        serializer = PatternSerializer(sms)
        
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

class PatternSmsListView(views.APIView):
    def get(self, request):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                ApiResponse(
                    success=True,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )

        sms = PatternSms.objects.all()
        serializer = PatternSerializer(sms, many=True)
        
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )
    