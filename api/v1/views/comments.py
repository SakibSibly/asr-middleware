from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from api.v1 import serializers
from api.v1 import models

class CommentList(APIView):
    @extend_schema(
        responses={200: serializers.CommentSerializer(many=True)},
        tags=["comment management"]
    )
    def get(self, request):
        comments = models.Comment.objects.all()
        serializer = serializers.CommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        request=serializers.CommentSerializer,
        responses={201: serializers.CommentSerializer, 400: None},
        tags=["comment management"]
    )
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = serializers.CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class CommentDetail(APIView):
    @extend_schema(
        responses={200: serializers.CommentSerializer, 404: None},
        tags=["comment management"]
    )
    def get(self, request, pk):
        try:
            comment = models.Comment.objects.get(pk=pk)
        except models.Comment.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = serializers.CommentSerializer(comment)
        return Response(serializer.data)
    
    @extend_schema(
        request=serializers.CommentSerializer,
        responses={200: serializers.CommentSerializer, 400: None, 404: None},
        tags=["comment management"]
    )
    def put(self, request, pk):
        try:
            comment = models.Comment.objects.get(pk=pk)
        except models.Comment.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        if comment.author != request.user:
            return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = serializers.CommentSerializer(comment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        responses={204: None, 404: None, 403: None},
        tags=["comment management"]
    )
    def delete(self, request, pk):
        try:
            comment = models.Comment.objects.get(pk=pk)
        except models.Comment.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        if comment.author != request.user:
            return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)
        
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)