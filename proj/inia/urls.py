"""inia URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import re_path, include
from . import views

app_name = 'inia'  # required by django.

urlpatterns = [
    re_path('^$', views.index, name='index'),
    re_path('^analysis/$', views.analysis_home, name='analysis_home'),
    re_path('^analysis/multisearch$', views.analysis_multisearch, name='analysis_multisearch'),
    re_path('^datasets/$', views.datasets, name='datasets_home'),
    re_path('^publications/$', views.datasets, name='publications_rdr'),
    re_path('^about/$', views.about, name='about'),
    re_path('^contact/$', views.contact, name='contact'),
    re_path('^links/$', views.links, name='links'),
    re_path('^help/$', views.help_home, name='help_home'),
    re_path('^search/$', views.search, name='search'),
    re_path('^analysis/booleandataset/$', views.boolean_dataset, name='boolean_dataset'),
    re_path('^analysis/datasetnetwork/$', views.dataset_network, name='dataset_network'),
    re_path('^analysis/genenetwork/$', views.gene_network, name='gene_network'),
    re_path('^analysis/overrepresentation_analysis/$', views.overrepresentation_analysis, name='overrepresentation_analysis'),

]
