from django.urls import path
from . import views

urlpatterns = [
    # Plans
    path('plans/', views.plan_list_create, name='plan-list-create'),
    path('plans/<int:plan_id>/', views.plan_detail, name='plan-detail'),
    path('plans/<int:plan_id>/records/', views.record_list, name='record-list'),

    # Record actions
    path('records/<int:record_id>/buy/', views.record_buy, name='record-buy'),
    path('records/<int:record_id>/sell/', views.record_sell, name='record-sell'),

    # Statistics
    path('statistics/', views.statistics, name='statistics'),
]
