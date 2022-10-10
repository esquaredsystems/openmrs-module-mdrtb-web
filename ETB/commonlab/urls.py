from django.urls import path,include
from . import  views

urlpatterns = [
    path('' , views.managetesttypes,name='managetesttypes'),
    path('testattr' , views.fetchAttributes , name = 'testattr'),
    path('addtesttypes' , views.addTestTypes ,name='addtesttype'),
    path('edittesttype/<str:uuid>',views.editTestType,name='edittesttype'),
    path('manageattributes/<str:uuid>',views.manageAttributes,name='manageattr'),
    path('addattributes/<str:uuid>' , views.addattributes,name='addattr'),
    path('editattributes/<str:uuid>' , views.editAttribute,name='editattr'),
    path('managetestorders' , views.managetestorders,name='managetestorders'),
    path('managetestsamples' , views.managetestsamples,name='managetestsamples'),
    path('retiretesttype/<str:uuid>', views.retireTestType,name='retiretesttype')

    
]
