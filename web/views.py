# Create your views here.
import os

from django.shortcuts import render
from django.views.generic import (
    TemplateView, ListView, FormView, DetailView
)
from django.conf import settings



class ReportsIndexPageView(TemplateView):

    template_name = "index.html"


class SPECParseReportsView(TemplateView):

    template_name = "reports.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report_summary_file = os.path.join(settings.BASE_DIR, 'reports', 'parse-summary')
        report_filter_file = os.path.join(settings.BASE_DIR, 'reports', 'parse-filter')

        with open(report_summary_file) as summary:
            context['summary'] = summary.readline()
        
        with open(report_filter_file) as filtered_data:
            context['filtered_data'] = filtered_data.readlines()

        return context

