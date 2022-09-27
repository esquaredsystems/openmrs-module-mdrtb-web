from django.urls import path,include
from . import  views

urlpatterns = [
    path('',views.index,name='Home'),
    path('login',views.login,name='Login'),
    path('enroll' , views.enroll, name='Enroll'),
    path('enroll2',views.enroll_two,name='Enroll2'),
    path('enroll3',views.actual_enroll,name='Enroll3' ),
    path('commonlab/managetesttypes' , views.managetesttypes,name='managetesttypes'),
    path('testattr' , views.fetchAttributes , name = 'testattr'),
    path('commonlab/addtesttypes' , views.addtesttypes ,name='addtesttypes'),
    
]
