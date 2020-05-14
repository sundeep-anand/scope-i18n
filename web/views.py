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

    template_name = "reports/find-langs.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report_summary_file = os.path.join(settings.BASE_DIR, 'reports', 'parse-summary')
        report_filter_file = os.path.join(settings.BASE_DIR, 'reports', 'parse-filter')

        with open(report_summary_file) as summary:
            context['summary'] = summary.readline()

        with open(report_filter_file) as filtered_data:
            context['filtered_data'] = filtered_data.readlines()

        return context


class TransPackagesReportsView(TemplateView):

    report_reduce_file = os.path.join(settings.BASE_DIR, 'reports', 'parse-reduce')
    template_name = "reports/trans-pkgs.html"

    DELIMITER = "§"

    def analyze_translation_pkgs(self):

        trans_pkgs_stats = []
        trans_pkgs_len = 0

        with open(self.report_reduce_file, 'r') as report_file:
            for row in report_file:
                pkg, find_langs, trans_pkgs = row.split(self.DELIMITER)
                find_langs_flag = True if find_langs else False
                trans_pkgs_len += len(trans_pkgs.split())
                trans_pkgs_stats.append(
                    [pkg, trans_pkgs, find_langs_flag]
                )
        return trans_pkgs_stats, trans_pkgs_len

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trans_pkgs'], trans_pkgs_len = \
            self.analyze_translation_pkgs()

        context['summary'] = "{} packages contain translations".format(
            trans_pkgs_len
        )
        with open(self.report_reduce_file) as reduced_data_raw:
            context['reduced_data_raw'] = reduced_data_raw.readlines()

        return context


class SBSizeCountReportsView(TemplateView):

    template_name = "reports/size-count.html"

    report_mo_file = os.path.join(settings.BASE_DIR, 'reports', 'fedora-sb-32-mo-files')
    report_flatpaks = os.path.join(settings.BASE_DIR, 'reports', 'fedora-sb-32-flatpaks')
    report_langpacks = os.path.join(settings.BASE_DIR, 'reports', 'fedora-sb-32-langpacks')

    def analyze_mo_files(self):

        # total no. of locales found
        locales = []

        # application stats
        # { app: no_of_mo_files, locales}
        app_stats = {}

        with open(self.report_mo_file, 'r') as mo_file_report:
            for row in mo_file_report:
                _, locale, _, mo_file = row.strip().split('/')
                app = mo_file.rstrip('.mo')
                try:
                    if app not in app_stats:
                        d = {app: [1, [locale]]}
                        app_stats.update(d)
                    else:
                        app_stats[app][0] += 1
                        app_stats[app][1].append(locale)
                except Exception:
                    print("In exception: " + row)

        return app_stats

    def calculate_mo_files(self):
        mo_files = {
            "/usr/share/locale/": (10286, '362M'),
            "/var/lib/flatpak/": (175, '112K'),
            "/sysroot/ostree/deploy/fedora/var/lib/flatpak/": (175, '112K'),
            "/usr/lib64/firefox/langpacks/": (107, '51M')
        }
        return mo_files

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summary"] = "Fedora Silverblue 32 - translations and their size"
        context["translations"] = self.calculate_mo_files()
        context["mo_file_stats"] = self.analyze_mo_files()

        with open(self.report_flatpaks) as flatpaks:
            context['flatpaks'] = flatpaks.readlines()

        with open(self.report_langpacks) as langpacks:
            context['langpacks'] = langpacks.readlines()

        with open(self.report_mo_file) as mo_files:
            context['mo_files'] = mo_files.readlines()

        return context


class WSSizeCountReportsView(SBSizeCountReportsView):

    report_mo_file = os.path.join(settings.BASE_DIR, 'reports', 'fedora-ws-32-mo-files')
    report_langpacks = os.path.join(settings.BASE_DIR, 'reports', 'fedora-ws-32-langpacks')

    def calculate_mo_files(self):
        mo_files = {
            "/usr/share/locale/": (13750, '458M'),
            "/usr/lib/python3.8/site-packages/pykickstart/locale/": (58, '1.1M'),
            "/usr/lib/python3.8/site-packages/humanize/locale/": (3, '40K'),
            "/usr/lib64/firefox/langpacks/": (107, '51M')
        }
        return mo_files

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summary"] = "Fedora Workstation 32 - translations and their size"
        context["translations"] = self.calculate_mo_files()
        context["mo_file_stats"] = self.analyze_mo_files()

        with open(self.report_langpacks) as langpacks:
            context['langpacks'] = langpacks.readlines()

        with open(self.report_mo_file) as mo_files:
            context['mo_files'] = mo_files.readlines()

        context['flatpaks'] = None

        return context


class SRVSizeCountReportsView(SBSizeCountReportsView):

    report_mo_file = os.path.join(settings.BASE_DIR, 'reports', 'fedora-srv-32-mo-files')

    def calculate_mo_files(self):
        mo_files = {
            "/usr/share/locale/": (3597, '122M')
        }
        return mo_files

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summary"] = "Fedora Server 32 - translations and their size"
        context["translations"] = self.calculate_mo_files()
        context["mo_file_stats"] = self.analyze_mo_files()

        with open(self.report_mo_file) as mo_files:
            context['mo_files'] = mo_files.readlines()

        context['langpacks'] = None
        context['flatpaks'] = None

        return context
