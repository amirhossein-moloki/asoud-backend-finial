from rest_framework import views, viewsets, status
from rest_framework.response import Response
from utils.response import ApiResponse
import logging

logger = logging.getLogger(__name__)
from apps.sms.models import (
    BulkSms,
    PatternSms, 
    Line, 
    Template, 
)
from apps.sms.serializers.owner import (
    LineListSerializer,
    TemplateListSerializer,
    BulkSmsCreateSerializer,
    BulkSmsViewSerializer,
    PatternSmsCreateSerializer,
    PatternSmsViewSerializer
)
from apps.sms.sms_core import SMSCoreHandler
import json


class LineListView(views.APIView):
    def get(self, request):
        """
        return the list of lines that can be used
        """
        lines = Line.objects.filter(
            is_active=True
        )

        serializer = LineListSerializer(lines, many=True)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )
    
class TemplateListView(views.APIView):
    def get(self, request):
        """
        return the list of template that can be used
        """

        templates = Template.objects.filter(
            is_active=True
        )

        serializer = TemplateListSerializer(templates, many=True)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

class BulkSmsView(views.APIView):
    def post(self, request):
        """
        send sms and create history object in Sms Model
        query param: type
        """
        serializer = BulkSmsCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            payload = serializer.to_payload(serializer.validated_data)
        except Exception as e:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    error=str(e)
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        
        # check user wallet and pay the bills
        WALLET_OK = True
        if not WALLET_OK:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    error="Insufficient Wallet Balance"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        # send the SMS
        logger.debug(f"Sending bulk SMS payload: {payload}")
        result = SMSCoreHandler.send_bulk(payload)
        logger.info(f"Bulk SMS result: {result}")
        
        # save SMS record
        sms = serializer.save(
            user=request.user
        )
        serialized_data = BulkSmsViewSerializer(sms)

        return Response(
            ApiResponse(
                success=True,
                code=201,
                data=serialized_data.data
            )
        )

class PatternSmsView(views.APIView):
    def post(self, request):
        """
        send sms and create history object in Sms Model
        """
        serializer = PatternSmsCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payload = serializer.to_payload(serializer.validated_data)
        except Exception as e:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    error=str(e)
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        
        # check user wallet and pay the bills
        WALLET_OK = True
        if not WALLET_OK:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    error="Insufficient Wallet Balance"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )


        # send the sms
        results = []
        for p in payload:
            logger.debug(f"Sending SMS payload: {p}")
            results.append(SMSCoreHandler.send_pattern(payload=p))
        
        logger.info(f"SMS sending results: {results}")
        sms_list = []
        for result in results:
            if result and result.get('data'):
                sms = serializer.save(
                    user=request.user,
                    message_id = result['data'].get('messageId'),
                    actual_cost=result['data'].get('cost', 0)
                )
                sms_list.append(PatternSmsviewSerializer(sms).data)
            else:
                sms_list.append({'error':'failed sms'})
        
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=json.dumps(sms_list)
            ),
            status=status.HTTP_200_OK
        )



