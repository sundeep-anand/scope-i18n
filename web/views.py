# Create your views here.
from django.shortcuts import render
from django.views.generic import (
    TemplateView, ListView, FormView, DetailView
)


class ReportsIndexPageView(TemplateView):

    template_name = "index.html"
