from django.urls import path,include
from . import  views

urlpatterns = [
    path('',views.login,name='home'),
    path('report' , views.index,name='report'),
    path('enroll' , views.enroll, name='Enroll'),
    path('enroll2',views.enroll_two,name='Enroll2'),
    path('enroll3',views.actual_enroll,name='Enroll3' ),
    path('logout' , views.logout,name='logout'),
    path('patientlist',views.patientList,name='patientlist')
    
]
