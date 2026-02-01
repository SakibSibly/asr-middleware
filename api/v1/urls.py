from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from api.v1.views import auth, blogs, comments


urlpatterns = [
    # OpenAPI schema
    path('schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # ReDoc
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # JWT
    path('token/', auth.CustomTokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('token/refresh/', auth.CustomTokenRefreshView.as_view(), name='token-refresh'),

    # Other API endpoints
    path('register/', auth.RegisterView.as_view(), name='register'),
    path('users/me/', auth.UserDetailView.as_view(), name='user-detail'),

    path('blogs/', blogs.BlogList.as_view(), name='blog-list'),
    path('blogs/<int:pk>/', blogs.BlogDetail.as_view(), name='blog-detail'),

    path('comments/', comments.CommentList.as_view(), name='comment-list'),
    path('comments/<int:pk>/', comments.CommentDetail.as_view(), name='comment-detail'),
]
