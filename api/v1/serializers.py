from rest_framework.serializers import ModelSerializer

from api.v1 import models


class UserSerializer(ModelSerializer):
    class Meta:
        model = models.CustomUser
        fields = ['id', 'email', 'full_name', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        user = models.CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data.get('full_name', '')
        )
        return user


class BlogSerializer(ModelSerializer):
    class Meta:
        model = models.Blog
        fields = ['id', 'title', 'content', 'author', 'created_at', 'updated_at']
        extra_kwargs = {
            'author': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }


class CommentSerializer(ModelSerializer):
    class Meta:
        model = models.Comment
        fields = ['id', 'blog', 'content', 'author', 'created_at', 'updated_at']
        extra_kwargs = {
            'author': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }
