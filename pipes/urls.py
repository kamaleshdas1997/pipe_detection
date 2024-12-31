from django.urls import path
from .views import PipeCountAPI

urlpatterns = [
    path('count-pipes/', PipeCountAPI.as_view(), name='count_pipes'),
]
