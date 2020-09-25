
import gc
import time
from os import walk, path, linesep, unlink

from utils.specfile import RpmSpecFile


class ParseTranslationData(object):

    PARSE_TYPE = None
    SPEC_FILES_PATH = None
    TOTAL_SPEC_FILES = None
    SPEC_USING_FIND_LANGS = None
    TRANS_PKGS = None

    DELIMITER = "§"

    report_files = {
        'raw': 'reports/parse-output',
        'find': 'reports/parse-find',
        'filter': 'reports/parse-filter',
        'reduce': 'reports/parse-reduce',
        'summary': 'reports/parse-summary'
    }

    def _write_output(self, report_type, txt):

        if not report_type:
            return

        f = open(self.report_files[report_type], "a+")
        f.write(txt)
        f.close()

    def _clean_up(self):
        for subject, file in self.report_files.items():
            if path.exists(file):
                unlink(file)

    def __init__(self, type, path):
        super().__init__()

        self.PARSE_TYPE = type
        self.SPEC_FILES_PATH = path
        self.TRANS_PKGS = 0
        self.TOTAL_SPEC_FILES = 0
        self.SPEC_USING_FIND_LANGS = 0

    def get_specs(self):
        spec_files = []
        # collect spec files
        for (_, _, filenames) in walk(self.SPEC_FILES_PATH):
            [spec_files.append(spec) for spec in filenames if spec.endswith('.spec')]

        starting_point = 0
        window_size = 1000
        end_point = window_size

        spec_file_packets = []

        for _ in range(0, int(len(spec_files) / window_size) + 1):
            spec_file_packets.append(spec_files[starting_point:end_point])
            starting_point = end_point + 1
            end_point += window_size
        return spec_file_packets

    def pick_spec_file(self):

        spec_packets = self.get_specs()

        # yield one by one
        for packets in spec_packets:
            for f in packets:
                try:
                    spec_absolute_path = path.join(self.SPEC_FILES_PATH, f)
                    if not spec_absolute_path:
                        break
                    yield (
                        RpmSpecFile(spec_absolute_path)
                    )
                except Exception:
                    print("Seems " + f + " is not a SPEC file!")
                    pass
            gc.collect()
            time.sleep(2)

    def parse_spec_file(self):

        # do cleanup
        self._clean_up()

        # start parsing SPEC files
        for spec_obj in self.pick_spec_file():

            self.TOTAL_SPEC_FILES += 1

            # Package name and version
            pkg_name, pkg_version = spec_obj.Name, spec_obj.Version
            print("{0} {1}".format(pkg_name, pkg_version), end='')
            print(self.DELIMITER, end='')
            self._write_output('raw', "{0} {1}".format(pkg_name, pkg_version) + self.DELIMITER)

            # Pkgs and Subpackages
            print(" ".join(spec_obj.getPackages()), end='')
            print(self.DELIMITER, end='')
            self._write_output('raw', ", ".join(spec_obj.getPackages()) + self.DELIMITER)

            # If there are find_langs in install section
            find_lang_str = ""
            for i, j in spec_obj.section.get("install", {}).items():
                find_lang_lines = [x.replace("%{name}", pkg_name)
                                   for x in j if '%find_lang ' in x and not x.startswith("#")]
                if find_lang_lines:
                    self.SPEC_USING_FIND_LANGS += 1
                    find_lang_str += ", ".join(find_lang_lines)
            print(find_lang_str, end='')
            print(self.DELIMITER, end='')
            self._write_output('raw', find_lang_str + self.DELIMITER)

            # Pkgs which may contain MO files
            mo_pkgs = []
            for spec_line in spec_obj.lines:
                if '%files' in spec_line and '.lang' in spec_line and not spec_line.startswith("#"):
                    spec_line = spec_line.replace('%{name}', spec_obj.Name)
                    probable_mo_package = [spec_pkg for spec_pkg in spec_obj.getPackages()
                                           if spec_pkg in spec_line]
                    # fallback
                    if not probable_mo_package:
                        str_to_b_replaced = [elm.replace(".lang", "")
                                             for elm in spec_line.split() if '.lang' in elm]
                        if str_to_b_replaced and len(str_to_b_replaced) == 1:
                            spec_line = spec_line.replace(str_to_b_replaced[0], spec_obj.Name)
                            probable_mo_package = [spec_pkg for spec_pkg in spec_obj.getPackages()
                                                   if spec_pkg in spec_line]
                    if probable_mo_package and \
                       [p for p in probable_mo_package if p not in mo_pkgs]:
                        mo_pkgs.extend(probable_mo_package)

            for pkg, files in spec_obj.section.get("files", {}).items():
                [mo_pkgs.append(pkg) for file in files
                 if '.mo ' in file and pkg not in mo_pkgs]
            print(" ".join(mo_pkgs), end='')
            self._write_output('raw', ", ".join(mo_pkgs))

            if mo_pkgs:
                self.TRANS_PKGS += len(mo_pkgs)

            if find_lang_str or mo_pkgs:
                self._write_output('filter', "{0} {1}".format(
                    spec_obj.Name, spec_obj.Version
                ) + self.DELIMITER)
                self._write_output('filter', " ".join(mo_pkgs) + self.DELIMITER)
                self._write_output('filter', find_lang_str)
                self._write_output('filter', linesep)

            print("\n > Out of %d SPEC files, %d use find_lang.\n" % (
                self.TOTAL_SPEC_FILES, self.SPEC_USING_FIND_LANGS
            ))
            self._write_output('raw', linesep)

        self._write_output('summary', "Out of {0} SPEC files, {1} ({2})% use find_lang. And {3} packages contain translations.".format(
            self.TOTAL_SPEC_FILES, self.SPEC_USING_FIND_LANGS,
            round((self.SPEC_USING_FIND_LANGS * 100) / self.TOTAL_SPEC_FILES, 2), self.TRANS_PKGS
        ))

    def find_in_spec_file(self, keyword, left_pad_keyword=True, right_pad_keyword=False):

        # do cleanup
        self._clean_up()

        search_results = {}

        # start parsing SPEC files
        for spec_obj in self.pick_spec_file():

            # Package name and version
            pkg_name, pkg_version = spec_obj.Name, spec_obj.Version
            spec_lines = spec_obj.lines
            keyword = keyword.strip()
            if left_pad_keyword:
                keyword = " " + keyword
            if right_pad_keyword:
                keyword = keyword + " "
            # filter conditions
            # 1. the keyword as-in-full or partially present in the sentence
            # 2. only BuildRequires and Requires are being scanned to figure out dependency
            # 3. excluding spec logs
            filter_lines = [line.strip() for line in spec_lines
                            if keyword in line and "Requires:" in line and
                            "- " not in line]
            if filter_lines:
                search_results[pkg_name] = filter_lines
                print("Package: {} \n\t {}".format(pkg_name, "\n\t".join(filter_lines)))

        for k, v in search_results.items():
            self._write_output('find', k + self.DELIMITER + "|".join(v) + "\n")

        print("Total number of packages: {}".format(len(search_results)))
