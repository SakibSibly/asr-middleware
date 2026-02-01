from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from api.v1 import serializers
from api.v1 import models


class BlogList(APIView):
    @extend_schema(
        responses={200: serializers.BlogSerializer(many=True)},
        tags=["blog management"]
    )
    def get(self, request):
        blogs = models.Blog.objects.all()
        serializer = serializers.BlogSerializer(blogs, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        request=serializers.BlogSerializer,
        responses={201: serializers.BlogSerializer, 400: None},
        tags=["blog management"]
    )
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = serializers.BlogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BlogDetail(APIView):
    def get_object(self, pk):
        try:
            return models.Blog.objects.get(pk=pk)
        except models.Blog.DoesNotExist:
            return None

    @extend_schema(
        responses={200: serializers.BlogSerializer, 404: None},
        tags=["blog management"]
    )
    def get(self, request, pk):
        blog = self.get_object(pk)
        if blog is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = serializers.BlogSerializer(blog)
        return Response(serializer.data)

    @extend_schema(
        request=serializers.BlogSerializer,
        responses={200: serializers.BlogSerializer, 400: None, 404: None},
        tags=["blog management"]
    )
    def put(self, request, pk):
        blog = self.get_object(pk)
        if blog is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if blog.author != request.user:
            return Response({'detail': 'You do not have permission to edit this blog.'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = serializers.BlogSerializer(blog, data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        request=serializers.BlogSerializer,
        responses={200: serializers.BlogSerializer, 400: None, 404: None},
        tags=["blog management"]
    )
    def patch(self, request, pk):
        blog = self.get_object(pk)
        if blog is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if blog.author != request.user:
            return Response({'detail': 'You do not have permission to edit this blog.'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = serializers.BlogSerializer(blog, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={204: None, 404: None},
        tags=["blog management"]
    )
    def delete(self, request, pk):
        blog = self.get_object(pk)
        if blog is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if blog.author != request.user:
            return Response({'detail': 'You do not have permission to delete this blog.'}, status=status.HTTP_403_FORBIDDEN)
        
        blog.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)