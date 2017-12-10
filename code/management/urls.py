from django.conf.urls import include, url
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^cctv_list/', views.cctv_list, name='cctv_list'),
    url(r'^cctv_add/', views.cctv_add, name='cctv_add'),
    url(r'^cctv_edit/(?P<pk>\d+)/$', views.cctv_edit, name='cctv_edit'),
    url(r'^cctv_search/', views.cctv_search, name='cctv_search'),
    url(r'^cctv_delete/(?P<pk>\d+)', views.cctv_delete, name='cctv_delete'),
	
    url(r'^space_list/', views.space_list, name='space_list'),
    url(r'^space_add/', views.space_add, name='space_add'),
    url(r'^space_edit/(?P<pk>\d+)/$', views.space_edit, name='space_edit'),
    url(r'^space_delete/(?P<pk>\d+)', views.space_delete, name='space_delete'),
	
    url(r'^video_list/', views.video_list, name='video_list'),
    url(r'^video_add/', views.video_add, name='video_add'),
    url(r'^video_search/', views.video_search, name='video_search'),
    url(r'^video_delete/', views.video_delete, name='video_delete'),
    	
    url(r'^neighbor_list/', views.neighbor_list, name='neighbor_list'),
    url(r'^neighbor_add/', views.neighbor_add, name='neighbor_add'),
    url(r'^neighbor_edit/(?P<pk>\d+)/$', views.neighbor_edit, name='neighbor_edit'),
    url(r'^neighbor_delete/(?P<pk>\d+)', views.neighbor_delete, name='neighbor_delete'),

    url(r'^sequence_list/', views.sequence_list, name='sequence_list'),
    url(r'^sequence_add/', views.sequence_add, name='sequence_add'),
    url(r'^sequence_edit/(?P<pk>\d+)/$', views.sequence_edit, name='sequence_edit'),
    url(r'^sequence_delete/(?P<pk>\d+)', views.sequence_delete, name='sequence_delete'),
    
    url(r'^accounts/login/', views.login, name='login'),
    url(r'^accounts/logout/', views.logout, name='logout'),
    url(r'^accounts/user_list/', views.user_list, name='user_list'),
    url(r'^accounts/user_search/', views.user_search, name='user_search'),
    url(r'^accounts/user_add/', views.user_add, name='user_add'),
    url(r'^accounts/user_delete/(?P<pk>[0-9]+)', views.user_delete, name='user_delete'),
    url(r'^accounts/user_edit/(?P<pk>[0-9]+)', views.user_edit, name='user_edit'),
    url(r'^accounts/user_profile/', views.user_profile, name='user_profile'),
    url(r'^accounts/password_change/', views.password_change, name='password_change'),   
    #url(r'^accounts/', include('django.contrib.auth.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
