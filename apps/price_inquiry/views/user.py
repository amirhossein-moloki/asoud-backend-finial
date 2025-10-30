from rest_framework import views, status
from rest_framework.response import Response
from utils.response import ApiResponse
from apps.price_inquiry.models import (
    Inquiry,
    InquiryImage,
    InquiryAnswer
)
from apps.price_inquiry.serializers import (
    InquiryCreateSerializer,
    InquirySerializer,
    InquiryUpdateSerializer,
    InquiryImageSerializer,
    InquirySendSetSerializer,
    InquiryExpireSetSerializer,
    InquiryAnswerSerializer,
    InquiryImageListSerializer,
)
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class InquiryCreateView(views.APIView):
    def post(self, request):
        serializer = InquiryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        obj = serializer.save(user=request.user)

        serialized_data = InquirySerializer(obj).data
        return Response(
            ApiResponse(
                success=True,
                code=201,
                data=serialized_data
            ),
            status=status.HTTP_201_CREATED
        )
    

class InquiryUpdateView(views.APIView):
    def put(self, request, pk=None):
        try:
            obj = Inquiry.objects.get(pk=pk)
        except Inquiry.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Inquiry Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = InquiryUpdateSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            ),
            status=status.HTTP_200_OK
        )
    
    
class InquiryDeleteView(views.APIView):
    def post(self, request, pk):
        if request.user != Inquiry.user:
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            Inquiry.objects.delete(id=pk)
            return Response(
            ApiResponse(
                success=True,
                code=200,
                data={}
            ),
            status=status.HTTP_200_OK
        )
        except Inquiry.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Inquiry Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            ApiResponse(
                success=True,
                code=201,
                data=serialized_data
            ),
            status=status.HTTP_201_CREATED
        )

class InquiryDeleteView(views.APIView):
    def post(self, request, pk=None):
        try:
            inquiry = Inquiry.objects.get(id=pk)
        except Inquiry.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Inquiry Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )

        if inquiry.user != request.user:
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        inquiry.delete()
        return Response(
            ApiResponse(
                success=True,
                code=204,
                data={"Inquiry deleted successfully"}
            )
        )

class InquirySendSetView(views.APIView):
    def post(self, request, pk):
        try:
            inquiry = Inquiry.objects.get(id=pk)
        except Inquiry.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Inquiry Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )

        if inquiry.user != request.user:
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = InquirySendSetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Update the inquiry
        inquiry.send = serializer.validated_data['send']
        inquiry.save()

        response_serializer = InquirySerializer(inquiry)

        # send sms or notification to owners
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "owners",
            {
                "type": "send_notification",
                "data": {
                    "type": "inquiry",
                    "message": "New Inquiry Added",
                    "inquiry": {
                        "id": str(inquiry.id),
                        "name": inquiry.name
                    },
                }
            }
        )


        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=response_serializer.data
            )
        )

class InquiryImageUploadView(views.APIView):
    def post(self, request, pk):
        try:
            inquiry = Inquiry.objects.get(id=pk)
        except Inquiry.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Inquiry Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )

        if inquiry.user != request.user:
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = InquiryImageListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(inquiry=inquiry)

        serialized_data = InquirySerializer(inquiry).data

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serialized_data
            )
        )

class InquiryExpiryRenewView(views.APIView):
    def post(self, request, pk):
        try:
            inquiry = Inquiry.objects.get(id=pk)
        except Inquiry.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Inquiry Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )

        if inquiry.user != request.user:
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = InquiryExpireSetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Update the inquiry
        inquiry.expiry = serializer.validated_data['expiry']
        inquiry.save()

        # Serialize the updated inquiry for the response
        response_serializer = InquirySerializer(inquiry)

        # send sms or notification

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=response_serializer.data
            )
        )

class InquiryListView(views.APIView):
    def get(self, request):
        inquiries = Inquiry.objects.filter(user=request.user)

        serializer = InquirySerializer(inquiries, many=True)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

class InquiryDetailView(views.APIView):
    def get(self, request, pk):
        try:
            inquiry = Inquiry.objects.get(id=pk)
        except Inquiry.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Inquiry Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = InquirySerializer(inquiry)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

# use websocket
class InquiryAnswerListView(views.APIView):
    def get(self, request, inquiry_pk):
        inquiry_answers = InquiryAnswer.objects.filter(inquiry=inquiry_pk)
        
        if inquiry_answers and inquiry_answers[0].inquiry.user != request.user:
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = InquiryAnswerSerializer(inquiry_answers, many=True)
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

# use websocket
class InquiryAnswerDetailView(views.APIView):
    def get(self, request, pk, inquiry_pk):
        try:
            inquiry_answer = InquiryAnswer.objects.get(id=pk)
        except InquiryAnswer.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Inquiry Answer Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        if str(inquiry_answer.inquiry.id) != inquiry_pk:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    error="Inquiry and Inquiry Answer Mismatch"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if inquiry_answer.inquiry.user != request.user:
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = InquiryAnswerSerializer(inquiry_answer)
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )        

