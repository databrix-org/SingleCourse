from django.urls import path
from . import views

app_name = 'course'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('enroll/<int:course_id>/', views.course_enroll, name='course_enroll'),
    path('dev-login/', views.dev_login, name='dev_login'),
    path('<int:course_id>/', views.course_overview, name='course_overview'),
    path('lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('lesson/<int:lesson_id>/complete/', views.complete_lesson, name='complete_lesson'),
    path('<int:course_id>/create-group/', views.create_group, name='create_group'),
    path('<int:course_id>/join-group/', views.join_group, name='join_group'),
    path('manage/', views.manage_course, name='manage_course'),
    path('manage/update_overview/', views.update_overview, name='update_overview'),
    path('manage/create_module/', views.create_module, name='create_module'),
    path('manage/delete_module/<int:module_id>/', views.delete_module, name='delete_module'),
    path('manage/edit_module/<int:module_id>/', views.edit_module, name='edit_module'),
    path('manage/lesson/<int:lesson_id>/', views.get_lesson, name='get_lesson'),
    path('manage/create_lesson/<int:module_id>/', views.create_lesson, name='create_lesson'),
    path('manage/delete_lesson/<int:lesson_id>/', views.delete_lesson, name='delete_lesson'),
    path('manage/save_lesson/<int:lesson_id>/', views.save_lesson, name='save_lesson'),
    path('manage/toggle_publish/', views.toggle_publish, name='toggle_publish'),
    path('search-group/<int:group_id>/', views.search_group, name='search_group'),
]