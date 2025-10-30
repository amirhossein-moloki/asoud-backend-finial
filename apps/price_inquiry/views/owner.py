from rest_framework import views, status
from rest_framework.response import Response
from utils.response import ApiResponse
from apps.price_inquiry.models import (
    Inquiry,
    InquiryAnswer,
)
from apps.price_inquiry.serializers import (
    InquirySerializer,
    InquiryAnswerSerializer,
    InquiryAnswerCreateSerializer,
)
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# use websocket
class InquiryListView(views.APIView):
    def get(self, request):
        inquiries = Inquiry.objects.all()

        if name := request.GET.get('name'):
            inquiries = inquiries.filter(name__icontain=name)
        
        if type := request.GET.get('type'):
            inquiries = inquiries.filter(type=type)
        
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
class InquiryAnswerCreateView(views.APIView):
    def post(self, request):
        serializer = InquiryAnswerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if not request.user.is_owner():
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error="Only Maket Owners can Answer Inquiries"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            inquiry = Inquiry.objects.get(id=serializer.validated_data['inquiry'])
        except Inquiry.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Inquiry Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )

        obj = serializer.save(
            inquiry=inquiry,
            user=request.user
        )

        # send notification to user
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{inquiry.user.id}",  # Group name for the user
            {
                "type": "send_notification",
                "data": {
                    "type": "inquiry-answer",
                    "message": "New Answer To Your Inquiry",
                    "inquiry-answer": {
                        "id": str(obj.id),
                        "detail": obj.detail
                    },
                }
            }
        )
        
        serialized_data = InquiryAnswerSerializer(obj).data

        return Response(
            ApiResponse(
                success=True,
                code=201,
                data=serialized_data
            ),
            status=status.HTTP_201_CREATED
        )


class InquiryAnswerListView(views.APIView):
    def get(self, request):
        inquiry_answers = InquiryAnswer.objects.filter(user=request.user)
        
        serializer = InquiryAnswerSerializer(inquiry_answers, many=True)
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

class InquiryAnswerDetailView(views.APIView):
    def get(self, request, pk):
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
        
        if inquiry_answer.user != request.user:
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

