from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.register, name='auth-register'),
    path('auth/login/', views.login, name='auth-login'),
    path('auth/logout/', views.logout, name='auth-logout'),
    path('auth/me/', views.me, name='auth-me'),

    # Plans
    path('plans/', views.plan_list_create, name='plan-list-create'),
    path('plans/<int:plan_id>/', views.plan_detail, name='plan-detail'),
    path('plans/<int:plan_id>/records/', views.record_list, name='record-list'),

    # Record actions
    path('records/<int:record_id>/buy/', views.record_buy, name='record-buy'),
    path('records/<int:record_id>/sell/', views.record_sell, name='record-sell'),
    path('records/<int:record_id>/restart/', views.record_restart, name='record-restart'),

    # Statistics
    path('statistics/', views.statistics, name='statistics'),

    # Quotes
    path('quotes/', views.stock_quotes, name='stock-quotes'),
    path('kline/', views.stock_kline, name='stock-kline'),
    path('search/', views.stock_search, name='stock-search'),
    
    # Watchlist
    path('watchlist/', views.watchlist_list_create, name='watchlist-list-create'),
    path('watchlist/<str:code>/', views.watchlist_delete, name='watchlist-delete'),
]

