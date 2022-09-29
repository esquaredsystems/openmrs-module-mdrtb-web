from django.urls import path,include
from . import  views

urlpatterns = [
    path('' , views.managetesttypes,name='managetesttypes'),
    path('testattr' , views.fetchAttributes , name = 'testattr'),
    path('addtesttypes' , views.addTestTypes ,name='addtesttype'),
    path('edittesttype/<str:uuid>',views.editTestType,name='edittesttype'),
    path('manageattributes',views.manageAttributes,name='manageattr')
    
]
