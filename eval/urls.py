from django.urls import path
from . import views
#from .views import *

app_name = 'eval'

urlpatterns = [

    #/index/
    path('', views.index, name='index'),

    # just to check pswd, will redirect
    path('check-eval-pswd', views.check_eval_pswd, name='check-eval-pswd'),

    #/eval-page/
    path('eval-page', views.eval_page, name='eval-page'),

    # just to submit eval, will redirect
    path('eval-submit', views.eval_submit, name='eval-submit'),

    #/prof-login/
    path('prof-login', views.prof_login, name='prof-login'),

    # just to authenticate, will redirect
    path('check-login', views.check_login, name='check-login'),

    #/prof-homepage/
    path('prof-homepage', views.prof_homepage, name='prof-homepage'),

    path('edit-course-action', views.edit_course_action, name='edit-course-action'),

    path('edit-course', views.edit_course, name='edit-course'),

    path('submit-edit-course', views.submit_edit_course, name='submit-edit-course'),

    path('delete-course', views.delete_course, name='delete-course'),

    path('submit-delete-course', views.submit_delete_course, name='submit-delete-course'),

    path('add-course', views.add_course, name='add-course'),

    path('submit-add-course', views.submit_add_course, name='submit-add-course'),

    path('course-sessions', views.course_sessions, name='course-sessions'),

    path('add-session', views.add_session, name='add-session'),

    path('submit-add-session', views.submit_add_session, name='submit-add-session'),

    path('edit-session-action', views.edit_session_action, name='edit-session-action'),

    path('edit-session', views.edit_session, name='edit-session'),

    path('submit-edit-session', views.submit_edit_session, name='submit-edit-session'),

    path('delete-session', views.delete_session, name='delete-session'),

    path('submit-delete-session', views.submit_delete_session, name='submit-delete-session'),

    path('choose-report', views.choose_report, name='choose-report'),

    path('one-session-choose', views.one_session_choose, name='one-session-choose'),

    path('one-session-report', views.one_session_report, name='one-session-report'),

    path('all-sessions-report', views.all_sessions_report, name='all-sessions-report'),

    path('two-sessions-choose', views.two_sessions_choose, name='two-sessions-choose'),

    path('two-sessions-report', views.two_sessions_report, name='two-sessions-report'),


]
