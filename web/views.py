# Create your views here.
import os
import operator

from django.shortcuts import render
from django.views.generic import (
    TemplateView, ListView, FormView, DetailView
)
from django.conf import settings
from django.http import HttpResponse


class SPECParseReportsView(TemplateView):

    template_name = "reports/trans-pkgs.html"
    report_filter_file = os.path.join(settings.BASE_DIR, 'reports', 'parse-filter')
    report_summary_file = os.path.join(settings.BASE_DIR, 'reports', 'parse-summary')

    DELIMITER = "§"

    def analyze_translation_pkgs(self):

        trans_pkgs_stats = []

        main_trans_pkgs = []
        trans_sub_pkgs = []

        trans_subpkgs_count = 0
        trans_pkgs_count = 0

        with open(self.report_filter_file, 'r') as report_file:
            for row in report_file:
                pkg, trans_pkgs, find_langs = row.split(self.DELIMITER)
                trans_pkgs_flag = True if trans_pkgs else False
                find_langs_flag = True if find_langs else False

                translation_identifiers = \
                    ['-lang ', '-langpacks', 'translations']

                for idtfr in translation_identifiers:
                    if idtfr in pkg:
                        main_trans_pkgs.append(pkg)
                    sub_pkgs = trans_pkgs.split() or []
                    for subpkg in sub_pkgs:
                        if subpkg.endswith(idtfr.strip()):
                            trans_sub_pkgs.append([pkg, subpkg])

                trans_subpkgs = []
                trans_pkgs_items = trans_pkgs.split() or []
                if len(trans_pkgs_items) > 1:
                    trans_subpkgs = trans_pkgs_items[1:]
                    trans_pkgs = trans_pkgs_items[0]
                    trans_subpkgs_count += len(trans_subpkgs)

                if trans_pkgs:
                    trans_pkgs_count += 1

                if "%{name}" not in pkg and "%{?cross}" not in pkg:
                    trans_pkgs_stats.append(
                        [pkg, trans_pkgs, trans_subpkgs, trans_pkgs_flag,
                         find_langs, find_langs_flag]
                    )
        return (sorted(trans_pkgs_stats),
                (main_trans_pkgs, trans_sub_pkgs, len(trans_sub_pkgs) / 2),
                trans_subpkgs_count, trans_pkgs_count)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        with open(self.report_summary_file) as summary:
            context['summary'] = summary.readline()

        (context["trans_pkgs_stats"], context["trans_pkgs"],
         context["trans_subpkgs_count"], context["trans_pkgs_count"]) = \
            self.analyze_translation_pkgs()
        return context


class CompTransPkgingView(TemplateView):

    template_name = "reports/comp-pkg.html"

    def get_trans_pkging(self):
        return {
            "Bundle all (status quo)": "mypkg",
            "Single translation subpackage": "mypkg-translations",
            "Subpackages by language code": "mypkg-translations-fr,...",
            "Bundle main langs and subpkg rest": "mypkg, mypkg-other-translations",
            "Combination of language subpackages and other languages subpkg (?)":
                "mypkg-translations-fr,... mypkg-translations-other",
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['summary'] = "Comparison of translation packaging(s)"
        context["trans_pkging"] = self.get_trans_pkging()
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
                        app_stats[app][1].sort()
                except Exception:
                    print("In exception: " + row)

        return app_stats

    def calculate_mo_files(self):
        mo_files = {
            "/usr/share/locale/": (10286, '362M'),
            "/var/lib/flatpak/": (175, '112K'),
            # "/sysroot/ostree/deploy/fedora/var/lib/flatpak/": (175, '112K'),
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


def RHConfigPatchReportsView(request):
    """
    RHConfigPatchReportsView View
    """
    contents = ""
    patch_path = os.path.join(
        settings.BASE_DIR, 'reports', 'transubpkg-rhrpmconfig-macro.patch'
    )

    with open(patch_path) as patch:
        contents = patch.read()
    return HttpResponse(contents, content_type="text/plain")


class GettextReportsView(TemplateView):

    template_name = "reports/gettext.html"
    report_gettext_file = os.path.join(
        settings.BASE_DIR, 'reports', 'parse-find-gettext'
    )

    DELIMITER = "§"

    def _format_data(self):
        gettext_data = {}
        devel_data = {}
        with open(self.report_gettext_file) as g_file:
            lines = g_file.readlines()

        for line in lines:
            if self.DELIMITER in line:
                line_parts = line.split(self.DELIMITER)
                # hardcoded, as per reports formatted
                if "gettext-devel" in line_parts[1]:
                    devel_data[line_parts[0]] = line_parts[1].split("|")
                else:
                    gettext_data[line_parts[0]] = line_parts[1].split("|")

        return gettext_data, devel_data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summary"] = "Gettext dependencies"

        context["gettext_data"], context["devel_data"] = self._format_data()
        return context


class SOSSummaryView(TemplateView):

    template_name = "sos.html"
    report_sos_dir = os.path.join(
        settings.BASE_DIR, 'reports', 'sos'
    )

    sos_data_files = {
        'LANG': 'LANG-int64',
        'LC_ALL': 'LC_ALL-int64',
        'LC_NAME': 'LC_NAME-int64',
        'LC_CTYPE': 'LC_CTYPE-int64'
    }

    DELIMITER = "§"

    def _consolidate_data(self, dataset):

        consolidated_data = dict()

        for sos_type, data in dataset.items():
            consolidated_data[sos_type] = dict()
            consolidated_data[sos_type]['lang_wise'] = dict()
            consolidated_data[sos_type]['lang_terr'] = dict()
            consolidated_data[sos_type]['locale_wise'] = dict()

            for data_item in data:
                count = 0
                new_locale = ''

                if len(data_item) == 2:
                    locale, count = data_item

                    if '.' in locale:
                        lang_trr, codeset = locale.split('.', 1)

                        delimiters = ['-', '_']

                        for delimiter in delimiters:
                            if delimiter in lang_trr:
                                lang, trr = lang_trr.split(delimiter)
                                lang = lang.lower()
                                lang_trr = "{}{}{}".format(lang, delimiter, trr.upper())

                                if lang not in consolidated_data[sos_type]['lang_wise']:
                                    consolidated_data[sos_type]['lang_wise'][lang] = int(count)
                                else:
                                    consolidated_data[sos_type]['lang_wise'][lang] += int(count)

                        codeset = codeset.upper()
                        if codeset == 'UTF8':
                            codeset = 'UTF-8'
                        new_locale = "{}.{}".format(lang_trr, codeset)

                        if lang_trr not in consolidated_data[sos_type]['lang_terr']:
                            consolidated_data[sos_type]['lang_terr'][lang_trr] = int(count)
                        else:
                            consolidated_data[sos_type]['lang_terr'][lang_trr] += int(count)
                elif len(data_item) == 1:
                    new_locale = ''
                    count = data_item[0]

                if new_locale not in consolidated_data[sos_type]['locale_wise']:
                    consolidated_data[sos_type]['locale_wise'][new_locale] = int(count)
                else:
                    consolidated_data[sos_type]['locale_wise'][new_locale] += int(count)

            consolidated_data[sos_type]['locale_wise'] = \
                dict(sorted(consolidated_data[sos_type]['locale_wise'].items(),
                            key=operator.itemgetter(1), reverse=True))
            consolidated_data[sos_type]['lang_terr'] = \
                dict(sorted(consolidated_data[sos_type]['lang_terr'].items(), key=operator.itemgetter(1), reverse=True))
            consolidated_data[sos_type]['lang_wise'] = \
                dict(sorted(consolidated_data[sos_type]['lang_wise'].items(), key=operator.itemgetter(1), reverse=True))
        return consolidated_data

    def _format_data(self):

        sos_dataset = {}

        for k, v in self.sos_data_files.items():

            with open(os.path.join(
                    self.report_sos_dir, self.sos_data_files.get(k))
            ) as sos_file:
                lines = sos_file.readlines()
                sos_dataset[k] = [line.strip().split() for line in lines]
        return self._consolidate_data(sos_dataset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summary"] = self._format_data()

        return context
