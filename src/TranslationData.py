
import gc
import time
from os import walk, path, linesep

from utils.specfile import RpmSpecFile


class ParseTranslationData(object):

    PARSE_TYPE = None
    SPEC_FILES_PATH = None
    TOTAL_SPEC_FILES = None
    SPEC_USING_FIND_LANGS = None

    DELIMITER = "|"

    def _write_output(self, report_type, txt):

        report_file = {
            'raw': 'reports/parse-output',
            'filter': 'reports/parse-filter',
            'summary': 'reports/parse-summary'
        }

        if not report_type:
            return

        f = open(report_file.get(report_type, ''), "a+")
        f.write(txt)
        f.close()

    def __init__(self, type, path):
        super().__init__()

        self.PARSE_TYPE = type
        self.SPEC_FILES_PATH = path
        self.TOTAL_SPEC_FILES = 0
        self.SPEC_USING_FIND_LANGS = 0

    def get_specs(self):
        spec_files = []
        # collect spec files
        for (_, _, filenames) in walk(self.SPEC_FILES_PATH):
            [spec_files.append(spec) for spec in filenames if spec.endswith('.spec')]

        starting_point = 0
        window_size = 500
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
                        # Spec.from_file(spec_absolute_path), RpmSpecFile(spec_absolute_path)
                        RpmSpecFile(spec_absolute_path)
                    )
                except Exception:
                    print("Seems " + f + " is not a SPEC file!")
                    pass
            gc.collect()
            time.sleep(2)

    def parse_spec_file(self):

        for spec_obj_2 in self.pick_spec_file():

            self.TOTAL_SPEC_FILES += 1
            # Pkg name and version
            print("{0} {1}".format(spec_obj_2.Name, spec_obj_2.Version), end='')
            print(self.DELIMITER, end='')

            self._write_output('raw', "{0} {1}".format(
                spec_obj_2.Name, spec_obj_2.Version
            ) + self.DELIMITER)

            # Pkgs and Subpackages
            # for pkg in spec_obj_2.getPackages() or []:
            #     p_msg = "Package: " + str(pkg)
            #     if pkg != spec_obj_2.Name:
            #         p_msg += " (subpackage)"
            #     print(p_msg)
            print(" ".join(spec_obj_2.getPackages()), end='')
            print(self.DELIMITER, end='')

            self._write_output('raw', " ".join(spec_obj_2.getPackages()) + self.DELIMITER)

            # If there are find_langs in install section
            find_lang_str = ""
            for i, j in spec_obj_2.section.get("install", {}).items():
                find_lang_lines = [x for x in j if '%find_lang' in x]
                if find_lang_lines:
                    # print("If there is find_langs")
                    self.SPEC_USING_FIND_LANGS += 1
                    # print(i)
                    find_lang_str += " ".join(find_lang_lines)
            print(find_lang_str, end='')
            print(self.DELIMITER, end='')

            self._write_output('raw', find_lang_str + self.DELIMITER)
            if find_lang_str:
                self._write_output('filter', "{0} {1}".format(
                    spec_obj_2.Name, spec_obj_2.Version
                ) + self.DELIMITER)
                self._write_output('filter', find_lang_str)
                self._write_output('filter', linesep)

            # Pkgs which may contain MO files
            mo_pkgs_str = ""
            for i, j in spec_obj_2.section.get("files", {}).items():
                mo_pkgs = [x for x in j or [] if 'lang' in x]
                if mo_pkgs:
                    # print("Pkgs which contain MO files")
                    # print(i)
                    mo_pkgs_str += " ".join(mo_pkgs)
            print(mo_pkgs_str, end='')
            print(self.DELIMITER, end='')

            self._write_output('raw', mo_pkgs_str + self.DELIMITER)

            print("\n > Out of %d Pkgs, %d use find_lang.\n" % (
                self.TOTAL_SPEC_FILES, self.SPEC_USING_FIND_LANGS
            ))
            self._write_output('raw', linesep)

        self._write_output('summary', "Out of %d Pkgs, %d use find_lang." % (
            self.TOTAL_SPEC_FILES, self.SPEC_USING_FIND_LANGS
        ))
