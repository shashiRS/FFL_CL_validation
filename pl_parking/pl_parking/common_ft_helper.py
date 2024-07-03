"""
General utility for framework functionalities like signal definition,
function addition, and table overview customization.
"""

import logging
import math
import os
import sys
import time
import warnings
from copy import deepcopy
from json import dumps
from typing import List

import jinja2
import pandas as pd
import plotly.graph_objects as go
from shapely import affinity, box, difference
from tsf.core.report import (
    CustomReportOverview,
    CustomReportStatistics,
    CustomReportTestCase,
    ProcessingResult,
    ProcessingResultsList,
    TeststepResult,
)
from tsf.core.results import DATA_NOK, Result
from tsf.core.testcase import (
    CustomReportTestStep,
    Statistics,
)
from tsf.io.signals import SignalDefinition
from tsf.testbench._internals.report_common import TestrunContainer

import pl_parking.common_constants as fc

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))  # nopep8
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)
import pl_parking.PLP.MF.constants as constants


def verify_testcase_results(result):
    """
    The verify_testcase_results function is a simple function that takes the result of a testcase and returns True if it passed, False otherwise.

    :param result: Determine if the testcase passed or failed
    :return: A boolean value
    """
    return True if result == fc.PASS else False


def verify_mf_sil_testcase_result(list_of_teststeps_results):
    """
    The verify_mf_sil_testcase_result function takes a list of teststep results as input and returns True if all the
    teststeps passed, False otherwise. The function is used to verify the result of a testcase.

    :param list_of_teststeps_results: Pass the results of each test step into the function
    :return: A boolean value
    """
    final_verdict = []
    for ts_result in list_of_teststeps_results:
        if ts_result == fc.PASS:
            final_verdict.append(True)
        elif ts_result == fc.FAIL:
            final_verdict.append(False)

    return all(final_verdict)


class CustomSOverview(CustomReportStatistics):
    """
    Custom statistics overview generator.

    This class generates a customized overview of statistics. It handles the processing
    of test results and generates an HTML table with detailed information about test steps, files, and
    their corresponding results. Additionally, it saves relevant data and configurations into files for
    further analysis.
    """

    name = "Statistics Report"

    def overview(self) -> str:
        """
        Generates a customized overview of statistics.

        This method processes the test results, creates links for test cases and test steps, computes
        verdicts, and generates an HTML table with colored backgrounds indicating the result status.
        It also saves various data and configurations into files for reference.

        Returns:
            str: HTML-formatted overview of statistics.
        """
        from collections import defaultdict

        import pandas as pd

        d = defaultdict(dict)  # noqa E741
        j = defaultdict(dict)  # noqa E741
        result_dict = defaultdict(dict)

        # pdl = dict()
        l = []  # noqa E741
        color_verdict = []
        for tcr in self._env.testrun.testcase_results:

            for result in tcr.teststep_results:
                results = list(self.processing_details_for(result.teststep_definition))
                if result.teststep_definition.name not in result_dict:
                    result_dict[result.teststep_definition.name] = {}
                for file in results:
                    result_dict[result.teststep_definition.name][file["file_name"].lower()] = file["file_name"]
            for _ in range(len(tcr.testcase_definition.teststep_definitions)):
                l.append(
                    str(
                        f'<a href="../testcases/tc_{tcr.testcase_definition_id}.html" style="text-align:center; display:block">{tcr.testcase_definition.name}</a>'
                    )
                )
            for result in tcr.teststep_results:
                m_res = result.measured_result
                e_res = result.teststep_definition.expected_results[None]
                (
                    _,
                    status,
                ) = e_res.compute_result_status(m_res)
                verdict = status.key.lower()

                if "data nok" in verdict:
                    verdict = fc.NOT_ASSESSED

                test_step_name_linked = str(
                    f'<a href="../teststeps/tc_{tcr.testcase_definition_id}_ts_{result.teststep_definition.id}.html" style="text-align:center; display:block">{result.teststep_definition.name}</a>'
                )
                file_name = result.collection_entry.name
                file_name = result_dict[result.teststep_definition.name][result.collection_entry.name]
                step_file_result = str(
                    f"""<a href="../teststeps_details/{result.teststep_definition.id}_details_for_{result.test_input.id}.html" align="center" style="width: 100%; height: 100%; display: block;background-color: {get_color(verdict)}; color: #ffffff">{verdict}</a>"""
                )
                d[test_step_name_linked][file_name] = step_file_result
                color_verdict.append(get_color(verdict))
                # file_name = result.collection_entry.name

                j[file_name][tcr.testcase_definition.name] = {"Result": verdict}

        import json

        with open(os.path.join(self.environment.output_folder, "functional_test_results.json"), "w") as outfile:
            json.dump(j, outfile, indent=4)

        s = pd.DataFrame(d)

        s.columns = pd.MultiIndex.from_tuples(zip(l, s.columns))

        pd.set_option("display.max_colwidth", None)
        html = s.to_html(classes="table table-hover height:500px", escape=False, col_space=100)

        html = html.split("\n")
        html_new = []

        for i in range(len(html)):
            if "<td>" not in html[i]:
                html_new.append(html[i])

            elif "<td>" in html[i]:
                bg_col = (html[i].split(";background-color: ")[-1]).split("; color:")[0]

                html_new.append(html[i].replace("<td>", f"<td bgcolor={bg_col}>"))
        html_new_str = "\n".join(html_new)
        html_new_str = html_new_str.replace("<thead>", '<thead class= "sticky-top" id = "myHeader">')

        return (
            '<div class="table-container">'
            + html_new_str
            + "</div>"
            + """
<style>
    .table-container {
      max-height: 600px; /* Set a maximum height for scroll */
      overflow-y: auto; /* Enable vertical scrolling */
    }

    th {
      background-color: #f2f2f2;
    }

    thead {
      position: sticky;
      top: 0;
      background-color: #f2f2f2; /* Optional: Set background color for the sticky header */
      z-index: 0; /* Ensure the header stays above the table body */
    }
  </style>"""
        )


class StatisticsReport(Statistics):
    """Generates statistics report with custom overview."""

    custom_report = CustomSOverview

    def process(self, **kwargs):
        """Processes statistics."""
        _log.debug("Creating statistics...")


class MF_SIL_CustomSOverview(CustomReportStatistics):
    """
    Custom statistics overview generator specialized for MF_SIL reports.

    This class generates a customized overview of statistics for MF_SIL reports. It handles the processing
    of test results and generates an HTML table with detailed information about test steps, files, and
    their corresponding results. Additionally, it saves relevant data and configurations into files for
    further analysis.
    """

    name = "Statistics Report"

    def overview(self) -> str:
        """
        Generates a customized overview of statistics tailored for MF_SIL reports.

        This method processes the test results, creates links for test cases and test steps, computes
        verdicts, and generates an HTML table with colored backgrounds indicating the result status.
        It also saves various data and configurations into files for reference.

        Returns:
            str: HTML-formatted overview of statistics.
        """
        from collections import defaultdict

        import pandas as pd

        d = defaultdict(dict)  # noqa E741
        j = defaultdict(dict)  # noqa E741
        result_dict = defaultdict(dict)
        test_case_result = defaultdict(dict)
        ceva = defaultdict(dict)
        software_version = ""
        project_name = ""
        project_name = self._env.testrun.subject_under_test.project.name
        try:
            software_version = self._env.testrun.subject_under_test.name
        except AttributeError:
            software_version = "No software version provided"
        try:
            project_name = self._env.testrun.subject_under_test.project.name
        except AttributeError:
            project_name = "No project name provided"

        # pdl = dict()
        l = []  # noqa E741
        from pathlib import PurePath

        path_split = PurePath(self.environment.output_folder).parts
        # print(path_split[4:])
        path_to_report = ""
        test_case_without_link = []
        path_to_report = "/".join(path_split[-4:])
        color_verdict = []
        for tcr in self._env.testrun.testcase_results:
            # verdict_list = []

            if "Root" in tcr.testcase_definition.name or "Output" in tcr.testcase_definition.name:
                pass
            else:
                for result in tcr.teststep_results:
                    results = list(self.processing_details_for(result.teststep_definition))

                    if result.teststep_definition.name not in result_dict:
                        result_dict[result.teststep_definition.name] = {}
                    for file in results:
                        result_dict[result.teststep_definition.name][file["file_name"].lower()] = file["file_name"]
                for _ in range(len(tcr.testcase_definition.teststep_definitions)):
                    test_case_without_link.append(tcr.testcase_definition.name)
                    l.append(
                        str(
                            f'<a href="../testcases/tc_{tcr.testcase_definition_id}.html" style="text-align:center; display:block">{tcr.testcase_definition.name}</a>'
                        )
                    )
                for result in tcr.teststep_results:

                    m_res = result.measured_result
                    e_res = result.teststep_definition.expected_results[None]
                    (
                        _,
                        status,
                    ) = e_res.compute_result_status(m_res)
                    verdict = status.key.lower()

                    if "data nok" in verdict or "n/a" in verdict:
                        verdict = fc.NOT_ASSESSED

                    test_step_name_linked = str(
                        f'<a href="../teststeps/tc_{tcr.testcase_definition_id}_ts_{result.teststep_definition.id}.html" style="text-align:center; display:block">{result.teststep_definition.name}</a>'
                    )
                    file_name = result.collection_entry.name
                    file_name = result_dict[result.teststep_definition.name][result.collection_entry.name]
                    if file_name not in test_case_result:
                        test_case_result[file_name] = {}
                    if tcr.testcase_definition.name not in test_case_result[file_name]:
                        test_case_result[file_name][tcr.testcase_definition.name] = []
                    # test_case_result[file_name][tcr.testcase_definition.name].append(verify_testcase_results(verdict))
                    test_case_result[file_name][tcr.testcase_definition.name].append(verdict)
                    step_file_result_mf_sil = str(
                        f'<a href="../{path_to_report}/teststeps_details/{result.teststep_definition.id}_details_for_{result.test_input.id}.html" align="center" style="width: 100%; height: 100%; display: block;background-color: {get_color(verdict)}; color: #ffffff">{verdict}</a>'
                    )
                    step_file_result = str(
                        f'<a href="../teststeps_details/{result.teststep_definition.id}_details_for_{result.test_input.id}.html" align="center" style="width: 100%; height: 100%; display: block;background-color: {get_color(verdict)}; color: #ffffff">{verdict}</a>'
                    )

                    d[test_step_name_linked][file_name] = step_file_result
                    ceva[result.teststep_definition.name][file_name] = step_file_result_mf_sil
                    color_verdict.append(get_color(verdict))
                    # file_name = result.collection_entry.name

                    # final_verdict_testcase = fc.FAIL
                    # if all(verdict_list):
                    #     final_verdict_testcase = fc.PASS
                    j[file_name][tcr.testcase_definition.name] = {"Result": verdict}

        for meas in test_case_result.keys():
            for tst_case in test_case_result[meas]:
                if fc.NOT_ASSESSED in test_case_result[meas][tst_case]:
                    j[meas][tst_case] = {"Result": fc.NOT_ASSESSED}
                else:
                    j[meas][tst_case] = (
                        {"Result": fc.PASS}
                        if verify_mf_sil_testcase_result(test_case_result[meas][tst_case])
                        else {"Result": fc.FAIL}
                    )

        import json

        with open(os.path.join(self.environment.output_folder, "functional_test_results.json"), "w") as outfile:
            json.dump(j, outfile, indent=4)
        with open(os.path.join(self.environment.output_folder, "mf_sil_data.txt"), "w") as json_file:
            json.dump(ceva, json_file, indent=4)
        with open(os.path.join(self.environment.output_folder, "mf_sil_software_version.txt"), "w") as sw_file:
            sw_file.write(str(software_version))
        with open(os.path.join(self.environment.output_folder, "mf_sil_project_name.txt"), "w") as sw_file:
            sw_file.write(str(project_name))
        with open(os.path.join(self.environment.output_folder, "mf_sil_data_headers.txt"), "w") as file:
            file.write(str(test_case_without_link))
        with open(os.path.join(self.environment.output_folder, "mf_sil_graph_links.txt"), "w") as file:
            file.write(str(path_to_report))
        s = pd.DataFrame(d)

        s.columns = pd.MultiIndex.from_tuples(zip(l, s.columns))
        pd.set_option("display.max_colwidth", None)
        html = s.to_html(classes="table table-hover height:500px", escape=False, col_space=100)

        html = html.split("\n")
        html_new = []

        for i in range(len(html)):
            if "<td>" not in html[i]:
                html_new.append(html[i])

            elif "<td>" in html[i]:
                bg_col = (html[i].split(";background-color: ")[-1]).split("; color:")[0]

                html_new.append(html[i].replace("<td>", f"<td bgcolor={bg_col}>"))
        html_new_str = "\n".join(html_new)
        html_new_str = html_new_str.replace("<thead>", '<thead class= "sticky-top" id = "myHeader">')

        return (
            '<div class="table-container">'
            + html_new_str
            + "</div>"
            + """
<style>
    .table-container {
      max-height: 600px; /* Set a maximum height for scroll */
      overflow-y: auto; /* Enable vertical scrolling */
    }

    th {
      background-color: #f2f2f2;
    }

    thead {
      position: sticky;
      top: 0;
      background-color: #f2f2f2; /* Optional: Set background color for the sticky header */
      z-index: 0; /* Ensure the header stays above the table body */
    }
  </style>"""
        )


class Non_MF_SIL_CustomSOverview(CustomReportStatistics):
    """
    Custom statistics overview generator specialized for non MF_SIL reports.

    This class generates a customized overview of statistics for non MF_SIL reports. It handles the processing
    of test results and generates an HTML table with detailed information about test steps, files, and
    their corresponding results. Additionally, it saves relevant data and configurations into files for
    further analysis.
    """

    name = "Statistics Report"

    def overview(self) -> str:
        """
        Generates a customized overview of statistics.

        This method processes the test results, creates links for test cases and test steps, computes
        verdicts, and generates an HTML table with colored backgrounds indicating the result status.
        It also saves various data and configurations into files for reference.

        Returns:
            str: HTML-formatted overview of statistics.
        """
        from collections import defaultdict

        import pandas as pd

        d = defaultdict(dict)  # noqa E741
        j = defaultdict(dict)  # noqa E741
        result_dict = defaultdict(dict)
        test_case_result = defaultdict(dict)
        ceva = defaultdict(dict)
        software_version = ""
        project_name = ""
        project_name = self._env.testrun.subject_under_test.project.name
        try:
            software_version = self._env.testrun.subject_under_test.name
        except AttributeError:
            software_version = "No software version provided"
        try:
            project_name = self._env.testrun.subject_under_test.project.name
        except AttributeError:
            project_name = "No project name provided"

        # pdl = dict()
        l = []  # noqa E741
        from pathlib import PurePath

        path_split = PurePath(self.environment.output_folder).parts
        # print(path_split[4:])
        path_to_report = ""
        test_case_without_link = []
        path_to_report = "/".join(path_split[-3:])

        color_verdict = []
        for tcr in self._env.testrun.testcase_results:
            # verdict_list = []

            if "Root" in tcr.testcase_definition.name or "Output" in tcr.testcase_definition.name:
                pass
            else:
                for result in tcr.teststep_results:
                    results = list(self.processing_details_for(result.teststep_definition))

                    if result.teststep_definition.name not in result_dict:
                        result_dict[result.teststep_definition.name] = {}
                    for file in results:
                        result_dict[result.teststep_definition.name][file["file_name"].lower()] = file["file_name"]
                for _ in range(len(tcr.testcase_definition.teststep_definitions)):
                    test_case_without_link.append(tcr.testcase_definition.name)
                    l.append(
                        str(
                            f'<a href="../testcases/tc_{tcr.testcase_definition_id}.html" style="text-align:center; display:block">{tcr.testcase_definition.name}</a>'
                        )
                    )
                for result in tcr.teststep_results:

                    m_res = result.measured_result
                    e_res = result.teststep_definition.expected_results[None]
                    (
                        _,
                        status,
                    ) = e_res.compute_result_status(m_res)
                    verdict = status.key.lower()

                    # verdict_list.append(verify_testcase_results(verdict))
                    if "data nok" in verdict or "n/a" in verdict:
                        verdict = fc.NOT_ASSESSED

                    test_step_name_linked = str(
                        f'<a href="../teststeps/tc_{tcr.testcase_definition_id}_ts_{result.teststep_definition.id}.html" style="text-align:center; display:block">{result.teststep_definition.name}</a>'
                    )
                    file_name = result.collection_entry.name
                    file_name = result_dict[result.teststep_definition.name][result.collection_entry.name]
                    if file_name not in test_case_result:
                        test_case_result[file_name] = {}
                    if tcr.testcase_definition.name not in test_case_result[file_name]:
                        test_case_result[file_name][tcr.testcase_definition.name] = []
                    test_case_result[file_name][tcr.testcase_definition.name].append(verify_testcase_results(verdict))
                    step_file_result_mf_sil = str(
                        f'<a href="../{path_to_report}/teststeps_details/{result.teststep_definition.id}_details_for_{result.test_input.id}.html" align="center" style="width: 100%; height: 100%; display: block;background-color: {get_color(verdict)}; color: #ffffff">{verdict}</a>'
                    )
                    step_file_result = str(
                        f'<a href="../teststeps_details/{result.teststep_definition.id}_details_for_{result.test_input.id}.html" align="center" style="width: 100%; height: 100%; display: block;background-color: {get_color(verdict)}; color: #ffffff">{verdict}</a>'
                    )

                    d[test_step_name_linked][file_name] = step_file_result
                    ceva[result.teststep_definition.name][file_name] = step_file_result_mf_sil
                    color_verdict.append(get_color(verdict))
                    # file_name = result.collection_entry.name

                    # final_verdict_testcase = fc.FAIL
                    # if all(verdict_list):
                    #     final_verdict_testcase = fc.PASS
                    j[file_name][tcr.testcase_definition.name] = {"Result": verdict}

        for meas in test_case_result.keys():
            for tst_case in test_case_result[meas]:
                j[meas][tst_case] = (
                    {"Result": fc.PASS} if all(test_case_result[meas][tst_case]) else {"Result": fc.FAIL}
                )

        import json

        with open(os.path.join(self.environment.output_folder, "functional_test_results.json"), "w") as outfile:
            json.dump(j, outfile, indent=4)
        with open(os.path.join(self.environment.output_folder, "mf_sil_data.txt"), "w") as json_file:
            json.dump(ceva, json_file, indent=4)
        with open(os.path.join(self.environment.output_folder, "mf_sil_software_version.txt"), "w") as sw_file:
            sw_file.write(str(software_version))
        with open(os.path.join(self.environment.output_folder, "mf_sil_project_name.txt"), "w") as sw_file:
            sw_file.write(str(project_name))
        with open(os.path.join(self.environment.output_folder, "mf_sil_data_headers.txt"), "w") as file:
            file.write(str(test_case_without_link))
        s = pd.DataFrame(d)

        s.columns = pd.MultiIndex.from_tuples(zip(l, s.columns))
        pd.set_option("display.max_colwidth", None)
        html = s.to_html(classes="table table-hover height:500px", escape=False, col_space=100)

        html = html.split("\n")
        html_new = []

        for i in range(len(html)):
            if "<td>" not in html[i]:
                html_new.append(html[i])

            elif "<td>" in html[i]:
                bg_col = (html[i].split(";background-color: ")[-1]).split("; color:")[0]

                html_new.append(html[i].replace("<td>", f"<td bgcolor={bg_col}>"))
        html_new_str = "\n".join(html_new)
        html_new_str = html_new_str.replace("<thead>", '<thead class= "sticky-top" id = "myHeader">')

        return (
            '<div class="table-container">'
            + html_new_str
            + "</div>"
            + """
<style>
    .table-container {
      max-height: 600px; /* Set a maximum height for scroll */
      overflow-y: auto; /* Enable vertical scrolling */
    }

    th {
      background-color: #f2f2f2;
    }

    thead {
      position: sticky;
      top: 0;
      background-color: #f2f2f2; /* Optional: Set background color for the sticky header */
      z-index: 0; /* Ensure the header stays above the table body */
    }
  </style>"""
        )


class StatisticsRootCauseReport(CustomReportStatistics):
    """
    Generates a statistics report focusing on root causes.

    This class generates a custom statistics report that focuses on root causes. It processes test results
    to identify root causes and presents them in an HTML table format. Additionally, it saves relevant data
    into files for further analysis.
    """

    name = "Statistics Report"

    def overview(self) -> str:
        """
        Generates a customized overview of statistics focusing on root causes.

        This method processes test results to identify root causes and presents them in an HTML table format.
        It also saves relevant data into files for further analysis.

        Returns:
            str: HTML-formatted overview of statistics focusing on root causes.
        """
        from collections import defaultdict

        import pandas as pd

        d = defaultdict(dict)  # noqa E741
        j = defaultdict(dict)  # noqa E741
        result_dict = defaultdict(dict)
        pdl = dict()
        l = []  # noqa E741
        color_verdict = []
        for tcr in self._env.testrun.testcase_results:
            if "Root" in tcr.testcase_definition.name or "Output" in tcr.testcase_definition.name:
                pass
            else:
                for result in tcr.teststep_results:
                    results = list(self.processing_details_for(result.teststep_definition))
                    if result.teststep_definition.name not in result_dict:
                        result_dict[result.teststep_definition.name] = {}
                    for file in results:
                        result_dict[result.teststep_definition.name][file["file_name"].lower()] = file["file_name"]
                for _ in range(len(tcr.testcase_definition.teststep_definitions)):
                    l.append(
                        str(
                            f'<a href="../testcases/tc_{tcr.testcase_definition_id}.html" style="text-align:center; display:block">{tcr.testcase_definition.name}</a>'
                        )
                    )
                for result in tcr.teststep_results:
                    m_res = result.measured_result
                    e_res = result.teststep_definition.expected_results[None]
                    (
                        _,
                        status,
                    ) = e_res.compute_result_status(m_res)
                    verdict = status.key.lower()
                    if "data nok" in verdict or "n/a" in verdict:
                        verdict = fc.NOT_ASSESSED
                    test_step_name_linked = str(
                        f'<a href="../teststeps/tc_{tcr.testcase_definition_id}_ts_{result.teststep_definition.id}.html" style="text-align:center; display:block">{result.teststep_definition.name}</a>'
                    )
                    file_name = result.collection_entry.name
                    file_name = result_dict[result.teststep_definition.name][result.collection_entry.name]
                    step_file_result = str(
                        f"""<a href="../teststeps_details/{result.teststep_definition.id}_details_for_{result.test_input.id}.html" align="center" style="width: 100%; height: 100%; display: block;background-color: {get_color(verdict)}; color: #ffffff">{verdict}</a>"""
                    )
                    d[test_step_name_linked][file_name] = step_file_result
                    color_verdict.append(get_color(verdict))

                    j[file_name][tcr.testcase_definition.name] = {"Result": verdict}
                    pdl[result.teststep_definition.name] = list(self.processing_details_for(result.teststep_definition))

        import json

        with open(os.path.join(self.environment.output_folder, "functional_test_results.json"), "w") as outfile:
            json.dump(j, outfile, indent=4)

        s = pd.DataFrame(d)

        s.columns = pd.MultiIndex.from_tuples(zip(l, s.columns))
        pd.set_option("display.max_colwidth", None)
        html = s.to_html(classes="table table-hover height:500px", escape=False, col_space=100)

        html = html.split("\n")
        html_new = []

        for i in range(len(html)):
            if "<td>" not in html[i]:
                html_new.append(html[i])
            elif "<td>" in html[i]:
                bg_col = (html[i].split(";background-color: ")[-1]).split("; color:")[0]
                html_new.append(html[i].replace("<td>", f"<td bgcolor={bg_col}>"))
        html_new_str = "\n".join(html_new)
        html_new_str = html_new_str.replace("<thead>", '<thead class= "sticky-top" id = "myHeader">')

        return (
            '<div class="table-container">'
            + html_new_str
            + "</div>"
            + """
<style>
    .table-container {
      max-height: 600px; /* Set a maximum height for scroll */
      overflow-y: auto; /* Enable vertical scrolling */
    }

    th {
      background-color: #f2f2f2;
    }

    thead {
      position: sticky;
      top: 0;
      background-color: #f2f2f2; /* Optional: Set background color for the sticky header */
      z-index: 0; /* Ensure the header stays above the table body */
    }
  </style>"""
        )


class RootCauseOverview(CustomReportStatistics):
    """
    Generates a customized overview focusing on root cause analysis.

    This class generates a custom overview that focuses on root cause analysis. It processes test results to identify
    root causes and presents them in an HTML format. Additionally, it integrates Jinja2 templating for rendering
    the HTML output.

    """

    name = "Root cause analysis"

    def overview(self) -> str:
        """
        Generates a customized overview focusing on root cause analysis.

        This method processes test results to identify root causes and presents them in an HTML format. It integrates
        Jinja2 templating for rendering the HTML output.

        Returns:
            str: HTML-formatted overview focusing on root cause analysis.
        """
        from collections import defaultdict

        # d = defaultdict(dict)  # noqa E741
        j = defaultdict(dict)  # noqa E741
        result_dict = defaultdict(dict)

        root_dict = defaultdict(dict)
        d_for_export = defaultdict(dict)
        d_step_link = defaultdict(dict)

        TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
        for tcr in self._env.testrun.testcase_results:
            if "Root" in tcr.testcase_definition.name or "Output" in tcr.testcase_definition.name:
                for result in tcr.teststep_results:
                    results = list(self.processing_details_for(result.teststep_definition))
                    if result.teststep_definition.name not in result_dict:
                        result_dict[result.teststep_definition.name] = {}
                    for file in results:
                        result_dict[result.teststep_definition.name][file["file_name"].lower()] = file["file_name"]
        jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(f"{TSF_BASE}\\templates"))
        for tcr in self._env.testrun.testcase_results:
            if "Root" in tcr.testcase_definition.name or "Output" in tcr.testcase_definition.name:
                for result in tcr.teststep_results:

                    m_res = result.measured_result
                    e_res = result.teststep_definition.expected_results[None]
                    (
                        _,
                        status,
                    ) = e_res.compute_result_status(m_res)
                    verdict = status.key.lower()
                    if "data nok" in verdict or "n/a" in verdict:
                        verdict = fc.NOT_ASSESSED
                    # new_root_text = result_dict[result.teststep_definition.name][result.collection_entry.name]
                    if "data nok" in verdict or "n/a" in verdict:
                        verdict = fc.NOT_ASSESSED

                    file_name = result_dict[result.teststep_definition.name][result.collection_entry.name]
                    file_link = (
                        f"../teststeps_details/{result.teststep_definition.id}_details_for_{result.test_input.id}.html"
                    )
                    step_lnk = f"../teststeps/tc_{tcr.testcase_definition_id}_ts_{result.teststep_definition.id}.html"

                    root_dict[(tcr.testcase_definition_id, result.teststep_definition.id)] = (
                        result.teststep_definition.id
                    )
                    try:

                        if file_name not in d_for_export:
                            d_for_export[file_name] = {}
                            d_step_link[file_name] = {}
                        if "test_case_name" not in d_for_export[file_name]:
                            d_for_export[file_name]["test_case_name"] = {}

                        if tcr.testcase_definition.name not in d_for_export[file_name]["test_case_name"]:
                            d_for_export[file_name]["test_case_name"][tcr.testcase_definition.name] = {}
                            d_step_link[file_name][tcr.testcase_definition.name] = {}
                        d_step_link[file_name][tcr.testcase_definition.name][result.teststep_definition.name] = step_lnk
                        d_for_export[file_name]["test_case_name"][tcr.testcase_definition.name][
                            result.teststep_definition.name
                        ] = {"verdict": verdict, "color": get_color(verdict), "link": file_link}

                    except Exception as e:
                        print(str(e))

                    # d[test_step_name_linked][file_name] = step_file_result
                    j[result.collection_entry.name][tcr.testcase_definition.name] = {"Result": verdict}

        # import json
        # with open(os.path.join(self.environment.output_folder, "functional_test_results.json"), "w") as outfile:
        #     json.dump(j, outfile, indent=4)

        template = jinja_env.get_template("root_cause_template.html")
        tst_case_names = list(d_for_export[list(d_for_export.keys())[0]]["test_case_name"].keys())
        tst_stp_names = list(d_for_export[list(d_for_export.keys())[0]]["test_case_name"][tst_case_names[0]].keys())
        slnx = d_step_link[list(d_step_link.keys())[0]]
        cs_dict = {}

        for (_, link1), (_, link2) in zip(slnx[list(slnx.keys())[0]].items(), slnx[list(slnx.keys())[1]].items()):
            # for (step1, link1), (step2, link2) in zip(slnx.items(), slnx.items()):
            cs_dict[link1] = list(slnx.keys())[0]
            cs_dict[link2] = list(slnx.keys())[1]
        # new_dict_for_export = d_for_export.copy()
        data_for_jinja_template = {}
        for measurement_name in d_for_export.keys():
            if measurement_name not in data_for_jinja_template:
                data_for_jinja_template[measurement_name] = {}
                data_for_jinja_template[measurement_name]["test_case_name"] = {}
                data_for_jinja_template[measurement_name]["test_case_name"]["test_case_name"] = {}
            root_output_tests = list(d_for_export[measurement_name]["test_case_name"].keys())
            for (step1, val1), (step2, val2) in zip(
                d_for_export[measurement_name]["test_case_name"][root_output_tests[0]].items(),
                d_for_export[measurement_name]["test_case_name"][root_output_tests[1]].items(),
            ):

                data_for_jinja_template[measurement_name]["test_case_name"]["test_case_name"][
                    f"{step1}_{root_output_tests[0]}"
                ] = val1
                data_for_jinja_template[measurement_name]["test_case_name"]["test_case_name"][
                    f"{step2}_{root_output_tests[1]}"
                ] = val2

        data_for_jinja_template = {}
        for measurement_name in d_for_export.keys():
            if measurement_name not in data_for_jinja_template:
                data_for_jinja_template[measurement_name] = {}
                data_for_jinja_template[measurement_name]["test_case_name"] = {}
                data_for_jinja_template[measurement_name]["test_case_name"]["test_case_name"] = {}
            root_output_tests = list(d_for_export[measurement_name]["test_case_name"].keys())
            for (step1, val1), (step2, val2) in zip(
                d_for_export[measurement_name]["test_case_name"][root_output_tests[0]].items(),
                d_for_export[measurement_name]["test_case_name"][root_output_tests[1]].items(),
            ):

                data_for_jinja_template[measurement_name]["test_case_name"]["test_case_name"][
                    f"{step1}_{root_output_tests[0]}"
                ] = val1
                data_for_jinja_template[measurement_name]["test_case_name"]["test_case_name"][
                    f"{step2}_{root_output_tests[1]}"
                ] = val2

        html = template.render(
            data=data_for_jinja_template,
            cs_list=tst_case_names * len(tst_stp_names),
            cs_dict=cs_dict,
            setp_iinked=d_step_link,
            stp_list=tst_stp_names,
            meas_list=list(d_for_export.keys()),
            test_case_data=d_for_export[list(d_for_export.keys())[0]][
                list(d_for_export[list(d_for_export.keys())[0]].keys())[0]
            ],
        )

        return '<div style="overflow: auto; position: relative;">' + html + "</div>"


class AupKPIStatistics(CustomReportStatistics):
    """
    Generates statistics for AUP Key Performance Indicators (KPIs).

    This class generates statistics focusing on AUP Key Performance Indicators (KPIs).
    It processes test results to extract relevant data for each KPI and presents them in an HTML format.

    """

    name = "AUP KPI statistics"

    def overview(self) -> str:
        """
        Generates an overview of AUP KPI statistics.

        This method processes test results to extract relevant data for each AUP KPI and presents them
        in an HTML format. It integrates Jinja2 templating for rendering the HTML output.

        Returns:
            str: HTML-formatted overview of AUP KPI statistics.
        """
        from collections import defaultdict

        import pandas as pd

        test_case_name_list = []

        d = defaultdict(dict)  # noqa E741
        j = defaultdict(dict)  # noqa E741
        result_dict = defaultdict(dict)
        usecase_dict = defaultdict(dict)

        usecase_dict = {key: {} for key in constants.ParkingUseCases.parking_usecase_id.keys()}
        TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
        for tcr in self._env.testrun.testcase_results:
            test_case_name_list.append(
                str(
                    f'<a href="../testcases/tc_{tcr.testcase_definition_id}.html" style="text-align:center; display:block">{tcr.testcase_definition.name}</a>'
                )
            )
            for result in tcr.teststep_results:
                results = list(self.processing_details_for(result.teststep_definition))
                if result.teststep_definition.name not in result_dict:
                    result_dict[result.teststep_definition.name] = {}
                for file in results:
                    result_dict[result.teststep_definition.name][file["file_name"].lower()] = file["file_name"]
                    for use_case_id in constants.ParkingUseCases.parking_usecase_id.keys():
                        if use_case_id.lower() in file["file_name"].lower():
                            usecase_dict[use_case_id].update({file["file_name"]: {}})
        usecase_dict = {key: val for key, val in usecase_dict.items() if key and val}
        jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(f"{TSF_BASE}\\templates"))
        l = []  # noqa E741
        color_verdict = []
        for tcr in self._env.testrun.testcase_results:

            for result in tcr.teststep_results:
                results = list(self.processing_details_for(result.teststep_definition))
                if result.teststep_definition.name not in result_dict:
                    result_dict[result.teststep_definition.name] = {}
                for file in results:
                    result_dict[result.teststep_definition.name][file["file_name"].lower()] = file["file_name"]
            for _ in range(len(tcr.testcase_definition.teststep_definitions)):
                l.append(
                    str(
                        f'<a href="../testcases/tc_{tcr.testcase_definition_id}.html" style="text-align:center; display:block">{tcr.testcase_definition.name}</a>'
                    )
                )
            for result in tcr.teststep_results:

                m_res = result.measured_result
                e_res = result.teststep_definition.expected_results[None]
                (
                    _,
                    status,
                ) = e_res.compute_result_status(m_res)
                verdict = status.key.lower()
                if tcr.testcase_definition.name.lower() in [
                    "average maneuvering time [s]",
                    "number of average strokes",
                ]:
                    if "failed" in verdict:
                        verdict = result.measured_result.as_dict["numerator"]
                    elif "data nok" in verdict:
                        verdict = fc.NOT_ASSESSED
                    elif "passed" in verdict:
                        verdict = result.measured_result.as_dict["numerator"]

                else:
                    if "data nok" in verdict:
                        verdict = fc.NOT_ASSESSED

                test_step_name_linked = str(
                    f'<a href="../teststeps/tc_{tcr.testcase_definition_id}_ts_{result.teststep_definition.id}.html" style="text-align:center; display:block">{result.teststep_definition.name}</a>'
                )
                file_name = result.collection_entry.name
                file_name = result_dict[result.teststep_definition.name][result.collection_entry.name]
                step_file_result = str(
                    f"""<td bgcolor="{get_color(verdict)}"style="text-align: center;"><a href="../teststeps_details/{result.teststep_definition.id}_details_for_{result.test_input.id}.html" align="center" style="width: 100%; height: 100%; display: block;background-color: {get_color(verdict)}; color: #ffffff">{verdict}</a></td>"""
                )
                d[test_step_name_linked][file_name] = step_file_result
                color_verdict.append(get_color(verdict))

                j[file_name][tcr.testcase_definition.name] = {"Result": verdict}

        import json

        with open(os.path.join(self.environment.output_folder, "functional_test_results.json"), "w") as outfile:
            json.dump(j, outfile, indent=4)

        s = pd.DataFrame(d)

        s.columns = pd.MultiIndex.from_tuples(zip(l, s.columns))

        pd.set_option("display.max_colwidth", None)
        html = s.to_html(classes="table table-hover height:500px", escape=False, col_space=100)

        html = html.split("\n")
        html_new = []

        for i in range(len(html)):
            if "<td>" not in html[i]:
                html_new.append(html[i])

            elif "<td>" in html[i]:
                bg_col = (html[i].split(";background-color: ")[-1]).split("; color:")[0]

                html_new.append(html[i].replace("<td>", f"<td bgcolor={bg_col}>"))
        html_new_str = "\n".join(html_new)
        html_new_str = html_new_str.replace("<thead>", '<thead class= "sticky-top" id = "myHeader">')

        new_df = defaultdict(dict)
        step_percentage = defaultdict(dict)
        for use_id in usecase_dict.keys():
            new_df[use_id] = {}
            for meas in usecase_dict[use_id]:
                if meas not in new_df[use_id]:
                    new_df[use_id][meas] = {}
                new_df[use_id][meas] = list(s.loc[meas].values)

        for key in new_df.keys():
            step_percentage[key] = []
            list_of_meas = list(new_df[key].keys())
            number_of_columns = len(new_df[key][list_of_meas[0]])
            for column in range(number_of_columns):
                pass_count = 0
                avg_count = 0
                meas_count = 0
                fail_count = 0
                for meas in list_of_meas:
                    if "passed" in new_df[key][meas][column]:
                        pass_count += 1
                    elif "failed" in new_df[key][meas][column]:
                        fail_count += 1
                    elif "n/a" in new_df[key][meas][column]:
                        pass
                    elif fc.NOT_ASSESSED in new_df[key][meas][column]:
                        pass
                    else:
                        extract_txt = new_df[key][meas][column].split('; color: #ffffff">')[-1]
                        extract_txt = extract_txt.replace("</a></td>", "")

                        avg_count += float(extract_txt)
                        meas_count += 1

                total = pass_count + fail_count
                if meas_count > 0:
                    percent = avg_count / meas_count
                    percent = f"{percent:.2f}"
                elif total == 0:
                    # percent =0
                    percent = "N/A"
                else:
                    percent = (pass_count / total) * 100
                    percent = f"{percent:.2f} %"
                step_percentage[key].append(percent)

        table_header = html_new_str.split("</thead>")[0] + "</thead>"

        template = jinja_env.get_template("aup_table_template.html")

        html = template.render(
            data=new_df,
            usecases=step_percentage,
            thead=table_header,
        )

        return '<div style="overflow: auto; position: relative;">' + html + "</div>"


class RootCause(Statistics):
    """Generates root cause analysis statistics."""

    custom_report = RootCauseOverview


class AupKPITable(Statistics):
    """Generates AUP KPI statistics."""

    custom_report = AupKPIStatistics


class StatisticsForRootCause(Statistics):
    """Generates statistics for root cause analysis."""

    custom_report = StatisticsRootCauseReport


class MF_SIL_StatisticsReport(Statistics):
    """Generates statistics for mf_sil report with custom overview."""

    custom_report = MF_SIL_CustomSOverview

    def process(self, **kwargs):
        """Processes statistics."""
        _log.debug("Creating statistics...")


class Non_MF_SIL_StatisticsReport(Statistics):
    """Generates statistics for non mf_sil report with custom overview."""

    custom_report = Non_MF_SIL_CustomSOverview

    def process(self, **kwargs):
        """Processes statistics."""
        _log.debug("Creating statistics...")


def return_result(result):
    """Maps result keys to corresponding Result objects or constants."""
    result_checker = {
        fc.PASS: Result(100, unit="%"),
        fc.FAIL: Result(0, unit="%"),
        fc.NOT_ASSESSED: DATA_NOK,
        fc.INPUT_MISSING: DATA_NOK,
    }
    return result_checker[result]


def calc_table_height(data_dict, base=80, height_per_row=40, char_limit=115, height_padding=10):
    """
    This function calculates the total height required to display a table based on
    the provided data dictionary. The height is determined by the number of rows in
    the table and the length of the values in each row.
    """
    total_height = base

    # if isinstance(data_dict, dict):
    #     total_height += height_per_row * len(data_dict.keys())
    #     for value in data_dict.values():
    #         if len(str(value)) > char_limit:
    #             total_height += height_padding
    # else:
    #     raise ValueError("Invalid input type. Expected a dictionary.")
    total_height += height_per_row * len(data_dict.keys())
    return total_height


def get_color(result):
    """Determines the color code based on the input result."""
    if isinstance(result, float):
        if result > 0:

            return "#28a745"
        else:
            return "#ffc107"
    if result == fc.PASS:
        return "#28a745"
    elif result == fc.FAIL:
        return "#dc3545"
    elif result == fc.INPUT_MISSING or result == "n/a":
        return "#ffc107"
    elif result == fc.NOT_ASSESSED or result == "data nok":
        return "#818589"
    else:
        return "#dc3545"


def apply_color(result, threshold_check, operator_pass, *args):
    """
    Evaluates the given 'result' against a 'threshold_color' using the specified 'operator_color' and
    returns a color code.

    Args:
        result: The value to be compared.
        threshold_check: The value for pass.
        operator_pass: The operator to be used for the comparison for pass situations.
        args[0] = threshold_color: The value for the acceptable(yellow).
        args[1] = operator_color: The operator to be used for comparing acceptance values.

    Returns:
        A color code representing the result of the comparison:
        - '#28a745' (green) for a passed comparison.
        - '#dc3545' (red) for a failed comparison.
        - '#ffc107' (yellow) for threshold_pass value.
        - '#000000' (black) for a TypeError during the comparison.
    """
    comparison_operators = {
        "==": lambda value, threshold: value == threshold,
        "!=": lambda value, threshold: value != threshold,
        ">": lambda value, threshold: value > threshold,
        ">=": lambda value, threshold: value >= threshold,
        "<": lambda value, threshold: value < threshold,
        "<=": lambda value, threshold: value <= threshold,
        "><": lambda value, threshold: value > threshold[0] and value < threshold[1],
        ">=<=": lambda value, threshold: value >= threshold[0] and value <= threshold[1],
    }
    color_operators = {
        "><": lambda result, val1, val2: result > val2 and result < val1 or result > val1 and result < val2,
        ">=<=": lambda result, val1, val2: result >= val2 and result <= val1,
        ">=<": lambda result, val1, val2: result >= val2 and result < val1,
        "><=": lambda result, val1, val2: result > val2 and result <= val1,
        "==": lambda result, val1, val2: result == val2,
        "!=": lambda result, val1, val2: result != val2,
        "<": lambda result, val1, val2: result < val2,
        "<=": lambda result, val1, val2: result <= val2,
        ">": lambda result, val1, val2: result > val2,
        ">=": lambda result, val1, val2: result >= val2,
        "[>=<=]": lambda result, val1, val2: result >= val2[0] and result <= val2[1],
        "[>=<]": lambda result, val1, val2: result >= val2[0] and result < val2[1],
        "[><=]": lambda result, val1, val2: result > val2[0] and result <= val2[1],
    }
    try:
        result = result[0] if isinstance(result, tuple) else result

        pass_comparison = comparison_operators[operator_pass](result, threshold_check)
        color = "#dc3545"  # Red color for FAILED by default

        if pass_comparison:
            color = "#28a745"  # Green color for PASSED
        if args:
            if color_operators[args[1]](result, threshold_check, args[0]):
                color = "#ffc107"  # Yellow color for ACCEPTABLE

    except TypeError:
        color = "rgb(33,39,43)"  # Black color for N/A

    return color


def build_html_table(dataframe: pd.DataFrame, table_remark="", table_title=""):
    """Constructs an HTML table from a DataFrame along with optional table remarks and title."""
    # Initialize the HTML string with line break and title
    html_string = "<br>"
    html_string += "<h4>" + table_title + "</h4>"

    # Convert DataFrame to HTML table
    table_html = dataframe.to_html(classes="table table-hover ", index=False, escape=False)

    # Apply styling to the table headers and rows
    table_html = table_html.replace("<th>", '<th style ="background-color: #FFA500">')
    table_html = table_html.replace('<tr style="text-align: right;">', '<tr style="text-align: center;">')
    table_html = table_html.replace("<tr>", '<tr style="text-align: center;">')

    # Add table remark with styling
    table_remark = "<h6>" + table_remark + "</h6>"

    # Wrap the table and remark in a div
    table_html = "<div>" + table_html + "<br>" + table_remark + "</div>"

    # Append the table HTML to the overall HTML string
    html_string += table_html

    return html_string


def convert_dict_to_pandas(
    signal_summary: dict,
    table_remark="",
    table_title="",
    table_header_left="Signal Evaluation",
    table_header_right="Summary",
):
    """Converts a dictionary to a Pandas DataFrame and creates an HTML table."""
    # Create a DataFrame from the dictionary
    evaluation_summary = pd.DataFrame(
        {
            table_header_left: {key: key for key, val in signal_summary.items()},
            table_header_right: {key: val for key, val in signal_summary.items()},
        }
    )

    # Generate HTML table using build_html_table function
    return build_html_table(evaluation_summary, table_remark, table_title)


def read_signal(
    reader, target, target_name, signal_name, cast_type=float, index=None, start_sample=None, end_sample=None
):
    """
    Reads a signal from the given reader into the target
    pandas dataframe of the given target Name if available
    """
    try:
        target = target.assign(
            **{f"{target_name}": [cast_type(value) for value in reader[signal_name][start_sample:end_sample]]}  # noqa
        )
        return True, target
    except Exception:
        _log.debug(f'Signal "{signal_name}" not available.')
        # write_log_message(f'Signal "{signal_name}" not available.', "error")
    return False, target


def rep(val, num_times: int):  # function can be used to assign multiple variables
    """
    Create a list of copies of a given value, repeated a specified number of times.

    Args:
        val: The value to be repeated.
        num_times (int): The number of times to repeat the value.

    Returns:
        list: A list containing copies of the value, repeated the specified number of times.
    """
    return [deepcopy(val) for _ in range(num_times)]


# Default custom test step report


class CustomTeststepReport(CustomReportTestStep):
    """Custom test step report class."""

    def overview(
        self,
        processing_details_list: ProcessingResultsList,
        teststep_result: List["TeststepResult"],
    ):
        """Generate an overview of the test step report.

        Args:
            processing_details_list (ProcessingResultsList): List of processing results.
            teststep_result (List[TeststepResult]): List of test step results.

        Returns:
            str: Overview of the test step report.
        """
        s = ""
        addtional_data = []
        pr_list = processing_details_list
        for d in range(len(pr_list)):
            json_entries = ProcessingResult.from_json(pr_list.processing_result_files[d])

            if "Additional_results" in json_entries.details:
                a = {"entry": json_entries.details["file_name"]}
                a.update(json_entries.details["Additional_results"])
                addtional_data.append(a)

            if "Plots" in json_entries.details and len(json_entries.details["Plots"]) > 0:
                s += f"<h3>{json_entries.details['file_name']}</h3><br>"
                for plot in range(len(json_entries.details["Plots"])):
                    try:
                        s += json_entries.details["Remarks"][plot]
                        s += f"<h4>{json_entries.details['Plot_titles'][plot]}</h4>"
                    except KeyError:
                        pass
                    s += json_entries.details["Plots"][plot]

        try:
            columns = []
            row_events = []
            for r in addtional_data:
                columns.extend(list(r.keys()))

            columns = list(set(columns))
            columns.remove("entry")
            columns.insert(0, "entry")
            for d in addtional_data:
                r = []
                for c in columns:
                    if c in d:
                        v = d[c]
                        if isinstance(v, dict):
                            r.append(str(f"""<span style="color: {v['color']}">{v['value']}</span>"""))
                        else:
                            r.append(v)
                    else:
                        r.append("")
                row_events.append(r)

            column_names = [{"title": str(c)} for c in columns]
            additional_tables = (
                """
        <h2>Additional Information</h2>
<script>
var table_column_names = """
                + dumps(column_names)
                + """;
var table_rows_events =  """
                + dumps(row_events)
                + """
$(document).ready(function() {
$('#events_table').DataTable( {
paging:    true,
searching: true,
info:      true,
scrollX: true,
data: table_rows_events,
columns: table_column_names
} );
});
</script>
<table class="table-sm table-striped compact nowrap" id="events_table" width="100%">
<caption>Table: Additional Information</caption>
</table>
"""
            )
            s = additional_tables + s
        except KeyError as e:
            # Handle KeyError if columns are not found
            print(f"KeyError occurred: {e}")
        except Exception as e:
            # Handle other exceptions
            print(f"An error occurred: {e}")
        return s

    def details(self, processing_details: ProcessingResult, teststep_result: "TeststepResult") -> str:
        """Generate details of the test step report.

        Args:
            processing_details (ProcessingResult): Processing results.
            teststep_result (TeststepResult): Test step result.

        Returns:
            str: Details of the test step report.
        """
        s = "<h3>details part</h3>"
        for k, v in processing_details.details.items():
            s += f"<div>{k}:{v}</div>"

        #     s += "<h3>Events part</h3>"
        #     for event in teststep_result.events:
        #         s += "<div>{}</div>".format(event)

        # s += "<div>Measured (part) Result: {}</div>".format(teststep_result.measured_result)
        # s += "<h3>You can also add pie charts like the one below</h3>"
        # s += processing_details.details['Plots'][0]
        return s


class MfCustomTeststepReport(CustomReportTestStep):
    """Custom MF test step report class."""

    def overview(
        self,
        processing_details_list: ProcessingResultsList,
        teststep_result: List["TeststepResult"],
    ):
        """Generate an overview of the test step report.

        Args:
            processing_details_list (ProcessingResultsList): List of processing results.
            teststep_result (List[TeststepResult]): List of test step results.

        Returns:
            str: Overview of the test step report.
        """
        s = ""

        # pr_list = processing_details_list
        s += "<br>"
        s += "<br>"

        # for d in range(len(pr_list)):
        #     json_entries = ProcessingResult.from_json(
        #         pr_list.processing_result_files[d])
        #     if "Plots" in json_entries.details and len(json_entries.details["Plots"]) > 1:
        #         s += f'<h4>Plots for failed measurements</h4>'
        #         s += f'<font color="red"><h7>{json_entries.details["file_name"]}</h7></font>'
        #         for plot in range(len(json_entries.details["Plots"])):

        #             s += json_entries.details["Plots"][plot]
        #             try:
        #                 s += f'<br>'
        #                 s += f'<h7>{json_entries.details["Remarks"][plot]}</h7>'
        #             except:
        #                 pass

        return s

    def details(self, processing_details: ProcessingResult, teststep_result: "TeststepResult") -> str:
        """Generate details of the test step report.

        Args:
            processing_details (ProcessingResult): Processing results.
            teststep_result (TeststepResult): Test step result.

        Returns:
            str: Details of the test step report.
        """
        s = "<br>"
        # color = ""
        m_res = teststep_result.measured_result
        e_res = teststep_result.teststep_definition.expected_results[None]
        (
            _,
            status,
        ) = e_res.compute_result_status(m_res)
        verdict = status.key.lower()

        if "data nok" in verdict:
            verdict = fc.NOT_ASSESSED

        s += f'<span align="center" style="width: 100%; height: 100%; display: block;background-color: {get_color(verdict)}; color : #ffffff">Step result: {verdict.upper()}</span>'

        for k, v in processing_details.details.items():
            if "Plots" in k:
                s += "<div>"
                for plot in v:

                    s += plot
                s += "</div>"

        return s


class MfCustomTestcaseReport(CustomReportTestCase):
    """Custom MF test case report class."""

    def __init__(self):
        """Initialize the report."""
        super().__init__()
        self.results = None
        self.result_dict = {}
        self.result_list = []
        self.anchor_list = []
        self.start_time = None

    def on_result(self, pr_details: ProcessingResult, ts_result: TeststepResult):
        """Process the test step result.

        Args:
            pr_details (ProcessingResult): Processing details.
            ts_result (TeststepResult): Test step result.
        """
        if "Processing_time" in pr_details and self.start_time is None:
            self.start_time = pr_details["Processing_time"]
        # self._env.testrun.testcase_results
        if "Additional_results" in pr_details:
            a = {"Measurement": pr_details["file_name"]}

            a.update(pr_details["Additional_results"])
            self.result_list.append(a)
            self.anchor_list.append(
                f'"../teststeps_details/{ts_result.teststep_definition.id}_details_for_{ts_result.test_input.id}.html"'
            )

    def overview(self):
        """Generate an overview of the test case report.

        Returns:
            str: Overview of the test case report.
        """
        results_dict = {
            fc.PASS.title(): 0,
            fc.FAIL.title(): 0,
            fc.INPUT_MISSING.title(): 0,
            fc.NOT_ASSESSED.title(): 0,
        }

        s = ""
        if self.start_time is not None:
            process_time = time.time() - self.start_time
            process_time = time.strftime("%M:%S", time.gmtime(process_time))
            s += "<h4> Processing time</h4>"
            s += f"<h5>{process_time} seconds</h5>"
            s += "<br>"
        try:
            columns = []
            row_events = []
            for r in self.result_list:
                columns.extend(list(r.keys()))
                break

            for d in self.result_list:
                r = []
                for c in columns:
                    if c in d:
                        v = d[c]
                        if isinstance(v, dict):
                            if "color" in v:
                                r.append(
                                    str(
                                        f"""<span align="center" style="width: 100%; height: 100%; display: block;background-color: {v['color']}; color : #ffffff">{v['value']}</span>"""
                                    )
                                )
                            else:
                                r.append(
                                    str(
                                        f"""<span align="center" style="width: 100%; height: 100%; display: block">{v['value']}</span>"""
                                    )
                                )
                        elif "Measurement" in c:
                            # r.append(v)
                            r.append(
                                str(
                                    f"""<span align="center" style="background-color: {d['Verdict']['color']}; color : #ffffff">{v}</span>"""
                                )
                            )

                            try:
                                results_dict[d["Verdict"]["value"]] += 1
                            except Exception as e:
                                print(str(e))
                        else:
                            r.append(v)

                    else:
                        r.append("")
                row_events.append(r)
            # for index in range(len(row_events)):

            #     row_events[index][0] = str(
            #         f"""<a href={self.anchor_list[index]}>{row_events[index][0]}</a>""")

            column_names = [{"title": str(c)} for c in columns]
            additional_tables = (
                """
        <h2>Additional Information</h2>
<script>
var table_column_names = """
                + dumps(column_names)
                + """;
var table_rows_events =  """
                + dumps(row_events)
                + """
$(document).ready(function() {
$('#events_table').DataTable( {
paging:    true,
searching: true,
info:      true,
scrollX: true,
ordering: true,
data: table_rows_events,
columns: table_column_names
} );
});
</script>
<table class="table-sm table-striped compact nowrap" id="events_table">

</table>
"""
            )
            s += "<h4>Overview results</h4>"
            s += "<br>"
            s += f"<h6>Passed: {results_dict[fc.PASS.title()]}</h6>"
            s += f"<h6>Failed: {results_dict[fc.FAIL.title()]}</h6>"
            s += f"<h6>Input missing: {results_dict[fc.INPUT_MISSING.title()]}</h6>"
            s += f"<h6>Not assessed: {results_dict[fc.NOT_ASSESSED.title()]}</h6>"
            s += "<br>"
            s += additional_tables
        except KeyError as ke:
            # Handle KeyError if expected keys are not found
            print(f"KeyError occurred: {ke}")
        except Exception as ex:
            # Handle other exceptions
            print(f"An error occurred: {ex}")
            s += "<h6>An error occurred while processing the data</h6>"
        return s


class CemSignals(SignalDefinition):
    """Example signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        OBJECTS_ID = "objects.id"
        OBJECTS_NUM = "numObjects"
        OBJECTS_OBJECTCLASS = "objects.objectClass"
        OBJECTS_CLASSCERTAINTY = "objects.classCertainty"
        OBJECTS_DYNAMICPROPERTY = "objects.dynamicProperty"
        OBJECTS_DYNPROPCERTAINTY = "objects.dynPropCertainty"
        OBJECTS_EXISTENCEPROB = "objects.existenceProb"
        OBJECTS_ORIENTATION = "objects.orientation"
        OBJECTS_ORIENTATIONSTANDARDDEVIATION = "objects.orientationStandardDeviation"
        OBJECTS_VELOCITY_F_XR = "objects.velocity.f_Xr"
        OBJECTS_VELOCITY_F_YA = "objects.velocity.f_Ya"
        OBJECTS_VELOCITYSTANDARDDEVIATION_F_XR = "objects.velocityStandardDeviation.f_Xr"
        OBJECTS_VELOCITYSTANDARDDEVIATION_F_YA = "objects.velocityStandardDeviation.f_Ya"
        OBJECTS_YAWRATE = "objects.yawRate"
        OBJECTS_YAWRATESTANDARDDEVIATION = "objects.yawRateStandardDeviation"
        OBJECTS_CENTER_X = "objects.center_x"
        OBJECTS_CENTER_Y = "objects.center_y"
        OBJECTS_LIFETIME = "objects.lifetime"
        OBJECTS_CONTAINEDINLASTSENSORUPDATE = "objects.containedInLastSensorUpdate"
        OBJECTS_STATE = "objects.state"
        OBJECTS_SHAPE_POINTS_0__POSITION_F_XR = "objects.shape.points[0].position.f_Xr"
        OBJECTS_SHAPE_POINTS_1__POSITION_F_XR = "objects.shape.points[1].position.f_Xr"
        OBJECTS_SHAPE_POINTS_2__POSITION_F_XR = "objects.shape.points[2].position.f_Xr"
        OBJECTS_SHAPE_POINTS_3__POSITION_F_XR = "objects.shape.points[3].position.f_Xr"
        OBJECTS_SHAPE_POINTS_0__POSITION_F_YA = "objects.shape.points[0].position.f_Ya"
        OBJECTS_SHAPE_POINTS_1__POSITION_F_YA = "objects.shape.points[1].position.f_Ya"
        OBJECTS_SHAPE_POINTS_2__POSITION_F_YA = "objects.shape.points[2].position.f_Ya"
        OBJECTS_SHAPE_POINTS_3__POSITION_F_YA = "objects.shape.points[3].position.f_Ya"
        OBJECTS_SHAPE_POINTS_0__VARIANCEX = "objects.shape.points[0].varianceX"
        OBJECTS_SHAPE_POINTS_1__VARIANCEX = "objects.shape.points[1].varianceX"
        OBJECTS_SHAPE_POINTS_2__VARIANCEX = "objects.shape.points[2].varianceX"
        OBJECTS_SHAPE_POINTS_3__VARIANCEX = "objects.shape.points[3].varianceX"
        OBJECTS_SHAPE_POINTS_0__VARIANCEY = "objects.shape.points[0].varianceY"
        OBJECTS_SHAPE_POINTS_1__VARIANCEY = "objects.shape.points[1].varianceY"
        OBJECTS_SHAPE_POINTS_2__VARIANCEY = "objects.shape.points[2].varianceY"
        OBJECTS_SHAPE_POINTS_3__VARIANCEY = "objects.shape.points[3].varianceY"
        VEDODO_TIMESTAMP = "vedodo_timestamp_us"
        VEDODO_SIGSTATUS = "vedodo_signalState"
        X = "x"
        Y = "y"
        YAW = "yaw"
        FRONT_TIMESTAMP = "Front_timestamp"
        FRONT_NUMOBJECTS = "Front_numObjects"
        FRONT_OBJECTS_ID = "Front_objects_id"
        FRONT_OBJECTS_SIGSTATUS = "Front_objects_eSigStatus"
        FRONT_OBJECTS_CLASSTYPE = "Front_objects_classType"
        FRONT_OBJECTS_CONFIDENCE = "Front_objects_confidence"
        FRONT_OBJECTS_CENTERPOINTWORLD_X = "Front_objects_centerPointWorld.x"
        FRONT_OBJECTS_CENTERPOINTWORLD_Y = "Front_objects_centerPointWorld.y"
        FRONT_OBJECTS_CENTERPOINTWORLD_Z = "Front_objects_centerPointWorld.z"
        FRONT_OBJECTS_PLANESIZEWORLD_X = "Front_objects_planeSizeWorld.x"
        FRONT_OBJECTS_PLANESIZEWORLD_Y = "Front_objects_planeSizeWorld.y"
        FRONT_OBJECTS_CUBOIDSIZEWORLD_X = "Front_objects_cuboidSizeWorld.x"
        FRONT_OBJECTS_CUBOIDSIZEWORLD_Y = "Front_objects_cuboidSizeWorld.y"
        FRONT_OBJECTS_CUBOIDSIZEWORLD_Z = "Front_objects_cuboidSizeWorld.z"
        FRONT_OBJECTS_CUBOIDYAWWORLD = "Front_objects_cuboidYawWorld"
        REAR_TIMESTAMP = "Rear_timestamp"
        REAR_NUMOBJECTS = "Rear_numObjects"
        REAR_OBJECTS_ID = "Rear_objects_id"
        REAR_OBJECTS_SIGSTATUS = "Rear_objects_eSigStatus"
        REAR_OBJECTS_CLASSTYPE = "Rear_objects_classType"
        REAR_OBJECTS_CONFIDENCE = "Rear_objects_confidence"
        REAR_OBJECTS_CENTERPOINTWORLD_X = "Rear_objects_centerPointWorld.x"
        REAR_OBJECTS_CENTERPOINTWORLD_Y = "Rear_objects_centerPointWorld.y"
        REAR_OBJECTS_CENTERPOINTWORLD_Z = "Rear_objects_centerPointWorld.z"
        REAR_OBJECTS_PLANESIZEWORLD_X = "Rear_objects_planeSizeWorld.x"
        REAR_OBJECTS_PLANESIZEWORLD_Y = "Rear_objects_planeSizeWorld.y"
        REAR_OBJECTS_CUBOIDSIZEWORLD_X = "Rear_objects_cuboidSizeWorld.x"
        REAR_OBJECTS_CUBOIDSIZEWORLD_Y = "Rear_objects_cuboidSizeWorld.y"
        REAR_OBJECTS_CUBOIDSIZEWORLD_Z = "Rear_objects_cuboidSizeWorld.z"
        REAR_OBJECTS_CUBOIDYAWWORLD = "Rear_objects_cuboidYawWorld"
        LEFT_TIMESTAMP = "Left_timestamp"
        LEFT_NUMOBJECTS = "Left_numObjects"
        LEFT_OBJECTS_ID = "Left_objects_id"
        LEFT_OBJECTS_SIGSTATUS = "Left_objects_eSigStatus"
        LEFT_OBJECTS_CLASSTYPE = "Left_objects_classType"
        LEFT_OBJECTS_CONFIDENCE = "Left_objects_confidence"
        LEFT_OBJECTS_CENTERPOINTWORLD_X = "Left_objects_centerPointWorld.x"
        LEFT_OBJECTS_CENTERPOINTWORLD_Y = "Left_objects_centerPointWorld.y"
        LEFT_OBJECTS_CENTERPOINTWORLD_Z = "Left_objects_centerPointWorld.z"
        LEFT_OBJECTS_PLANESIZEWORLD_X = "Left_objects_planeSizeWorld.x"
        LEFT_OBJECTS_PLANESIZEWORLD_Y = "Left_objects_planeSizeWorld.y"
        LEFT_OBJECTS_CUBOIDSIZEWORLD_X = "Left_objects_cuboidSizeWorld.x"
        LEFT_OBJECTS_CUBOIDSIZEWORLD_Y = "Left_objects_cuboidSizeWorld.y"
        LEFT_OBJECTS_CUBOIDSIZEWORLD_Z = "Left_objects_cuboidSizeWorld.z"
        LEFT_OBJECTS_CUBOIDYAWWORLD = "Left_objects_cuboidYawWorld"
        RIGHT_TIMESTAMP = "Right_timestamp"
        RIGHT_NUMOBJECTS = "Right_numObjects"
        RIGHT_OBJECTS_ID = "Right_objects_id"
        RIGHT_OBJECTS_SIGSTATUS = "Right_objects_eSigStatus"
        RIGHT_OBJECTS_CLASSTYPE = "Right_objects_classType"
        RIGHT_OBJECTS_CONFIDENCE = "Right_objects_confidence"
        RIGHT_OBJECTS_CENTERPOINTWORLD_X = "Right_objects_centerPointWorld.x"
        RIGHT_OBJECTS_CENTERPOINTWORLD_Y = "Right_objects_centerPointWorld.y"
        RIGHT_OBJECTS_CENTERPOINTWORLD_Z = "Right_objects_centerPointWorld.z"
        RIGHT_OBJECTS_PLANESIZEWORLD_X = "Right_objects_planeSizeWorld.x"
        RIGHT_OBJECTS_PLANESIZEWORLD_Y = "Right_objects_planeSizeWorld.y"
        RIGHT_OBJECTS_CUBOIDSIZEWORLD_X = "Right_objects_cuboidSizeWorld.x"
        RIGHT_OBJECTS_CUBOIDSIZEWORLD_Y = "Right_objects_cuboidSizeWorld.y"
        RIGHT_OBJECTS_CUBOIDSIZEWORLD_Z = "Right_objects_cuboidSizeWorld.z"
        RIGHT_OBJECTS_CUBOIDYAWWORLD = "Right_objects_cuboidYawWorld"
        PCLDELIMITERS_SIGSTATUS = "Pcl_eSigStatus"
        NUMPCLDELIMITERS = "numPclDelimiters"
        NUMPCLDELIMITERS_TIMESTAMP = "numPclDelimiters_timestamp"
        DELIMITERID = "delimiterId"
        DELIMITERTYPE = "delimiterType"
        P0_X = "P0_x"
        P0_Y = "P0_y"
        P1_X = "P1_x"
        P1_Y = "P1_y"
        CONFIDENCEPERCENT = "confidencePercent"
        DPGS_TIMESTAMP = "dpgs_timestamp"
        DPGS_LONGITUDE = "dpgs_longitude"
        DPGS_LATITUDE = "dpgs_latitude"
        DPGS_HEADING = "dpgs_heading"
        PMDCAMERA_FRONT_SIGSTATUS = "PMDCamera_Front_eSigStatus"
        PMDCAMERA_FRONT_TIMESTAMP = "PMDCamera_Front_timestamp"
        PMDCAMERA_FRONT_NUMBEROFLINES = "PMDCamera_Front_numberOfLines"
        PMDCAMERA_FRONT_PARKINGLINES_LINEID = "PMDCamera_Front_parkingLines_lineId"
        PMDCAMERA_FRONT_PARKINGLINES_LINESTARTX = "PMDCamera_Front_parkingLines_lineStartX"
        PMDCAMERA_FRONT_PARKINGLINES_LINESTARTY = "PMDCamera_Front_parkingLines_lineStartY"
        PMDCAMERA_FRONT_PARKINGLINES_LINEENDX = "PMDCamera_Front_parkingLines_lineEndX"
        PMDCAMERA_FRONT_PARKINGLINES_LINEENDY = "PMDCamera_Front_parkingLines_lineEndY"
        PMDCAMERA_FRONT_PARKINGLINES_LINECONFIDENCE = "PMDCamera_Front_parkingLines_lineConfidence"
        PMDCAMERA_REAR_SIGSTATUS = "PMDCamera_Rear_eSigStatus"
        PMDCAMERA_REAR_TIMESTAMP = "PMDCamera_Rear_timestamp"
        PMDCAMERA_REAR_NUMBEROFLINES = "PMDCamera_Rear_numberOfLines"
        PMDCAMERA_REAR_PARKINGLINES_LINEID = "PMDCamera_Rear_parkingLines_lineId"
        PMDCAMERA_REAR_PARKINGLINES_LINESTARTX = "PMDCamera_Rear_parkingLines_lineStartX"
        PMDCAMERA_REAR_PARKINGLINES_LINESTARTY = "PMDCamera_Rear_parkingLines_lineStartY"
        PMDCAMERA_REAR_PARKINGLINES_LINEENDX = "PMDCamera_Rear_parkingLines_lineEndX"
        PMDCAMERA_REAR_PARKINGLINES_LINEENDY = "PMDCamera_Rear_parkingLines_lineEndY"
        PMDCAMERA_REAR_PARKINGLINES_LINECONFIDENCE = "PMDCamera_Rear_parkingLines_lineConfidence"
        PMDCAMERA_LEFT_SIGSTATUS = "PMDCamera_Left_eSigStatus"
        PMDCAMERA_LEFT_TIMESTAMP = "PMDCamera_Left_timestamp"
        PMDCAMERA_LEFT_NUMBEROFLINES = "PMDCamera_Left_numberOfLines"
        PMDCAMERA_LEFT_PARKINGLINES_LINEID = "PMDCamera_Left_parkingLines_lineId"
        PMDCAMERA_LEFT_PARKINGLINES_LINESTARTX = "PMDCamera_Left_parkingLines_lineStartX"
        PMDCAMERA_LEFT_PARKINGLINES_LINESTARTY = "PMDCamera_Left_parkingLines_lineStartY"
        PMDCAMERA_LEFT_PARKINGLINES_LINEENDX = "PMDCamera_Left_parkingLines_lineEndX"
        PMDCAMERA_LEFT_PARKINGLINES_LINEENDY = "PMDCamera_Left_parkingLines_lineEndY"
        PMDCAMERA_LEFT_PARKINGLINES_LINECONFIDENCE = "PMDCamera_Left_parkingLines_lineConfidence"
        PMDCAMERA_RIGHT_SIGSTATUS = "PMDCamera_Right_eSigStatus"
        PMDCAMERA_RIGHT_TIMESTAMP = "PMDCamera_Right_timestamp"
        PMDCAMERA_RIGHT_NUMBEROFLINES = "PMDCamera_Right_numberOfLines"
        PMDCAMERA_RIGHT_PARKINGLINES_LINEID = "PMDCamera_Right_parkingLines_lineId"
        PMDCAMERA_RIGHT_PARKINGLINES_LINESTARTX = "PMDCamera_Right_parkingLines_lineStartX"
        PMDCAMERA_RIGHT_PARKINGLINES_LINESTARTY = "PMDCamera_Right_parkingLines_lineStartY"
        PMDCAMERA_RIGHT_PARKINGLINES_LINEENDX = "PMDCamera_Right_parkingLines_lineEndX"
        PMDCAMERA_RIGHT_PARKINGLINES_LINEENDY = "PMDCamera_Right_parkingLines_lineEndY"
        PMDCAMERA_RIGHT_PARKINGLINES_LINECONFIDENCE = "PMDCamera_Right_parkingLines_lineConfidence"
        PMDWS_FRONT_TIMESTAMP = "PMDWs_Front_timestamp"
        PMDWS_REAR_TIMESTAMP = "PMDWs_Rear_timestamp"
        PMDWS_LEFT_TIMESTAMP = "PMDWs_Left_timestamp"
        PMDWS_RIGHT_TIMESTAMP = "PMDWs_Right_timestamp"
        PMDWS_FRONT_LINECONFIDENCE = "PMDWs_Front_lineConfidence"
        PMDWS_REAR_LINECONFIDENCE = "PMDWs_Rear_lineConfidence"
        PMDWS_LEFT_LINECONFIDENCE = "PMDWs_Left_lineConfidence"
        PMDWS_RIGHT_LINECONFIDENCE = "PMDWs_Right_lineConfidence"
        PMDWS_FRONT_NUMBEROFLINES = "PMDWs_Front_numberOfLines"
        PMDWS_REAR_NUMBEROFLINES = "PMDWs_Rear_numberOfLines"
        PMDWS_LEFT_NUMBEROFLINES = "PMDWs_Left_numberOfLines"
        PMDWS_RIGHT_NUMBEROFLINES = "PMDWs_Right_numberOfLines"
        PMDWL_FRONT_TIMESTAMP = "PMDWl_Front_timestamp"
        PMDWL_REAR_TIMESTAMP = "PMDWl_Rear_timestamp"
        PMDWL_LEFT_TIMESTAMP = "PMDWl_Left_timestamp"
        PMDWL_RIGHT_TIMESTAMP = "PMDWl_Right_timestamp"
        PMDWL_FRONT_LINECONFIDENCE = "PMDWl_Front_lineConfidence"
        PMDWL_REAR_LINECONFIDENCE = "PMDWl_Rear_lineConfidence"
        PMDWL_LEFT_LINECONFIDENCE = "PMDWl_Left_lineConfidence"
        PMDWL_RIGHT_LINECONFIDENCE = "PMDWl_Right_lineConfidence"
        PMDWL_FRONT_NUMBEROFLINES = "PMDWl_Front_numberOfLines"
        PMDWL_REAR_NUMBEROFLINES = "PMDWl_Rear_numberOfLines"
        PMDWL_LEFT_NUMBEROFLINES = "PMDWl_Left_numberOfLines"
        PMDWL_RIGHT_NUMBEROFLINES = "PMDWl_Right_numberOfLines"
        PMDSL_FRONT_TIMESTAMP = "PMDSl_Front_timestamp"
        PMDSL_REAR_TIMESTAMP = "PMDSl_Rear_timestamp"
        PMDSL_LEFT_TIMESTAMP = "PMDSl_Left_timestamp"
        PMDSL_RIGHT_TIMESTAMP = "PMDSl_Right_timestamp"
        PMDSL_FRONT_LINECONFIDENCE = "PMDSl_Front_lineConfidence"
        PMDSL_REAR_LINECONFIDENCE = "PMDSl_Rear_lineConfidence"
        PMDSL_LEFT_LINECONFIDENCE = "PMDSl_Left_lineConfidence"
        PMDSL_RIGHT_LINECONFIDENCE = "PMDSl_Right_lineConfidence"
        PMDSL_FRONT_NUMBEROFLINES = "PMDSl_Front_numberOfLines"
        PMDSL_REAR_NUMBEROFLINES = "PMDSl_Rear_numberOfLines"
        PMDSL_LEFT_NUMBEROFLINES = "PMDSl_Left_numberOfLines"
        PMDSL_RIGHT_NUMBEROFLINES = "PMDSl_Right_numberOfLines"
        CEMSLOT_TIMESTAMP = "CemSlot_timestamp"
        CEMSLOT_SIGSTATUS = "CemSlot_eSigStatus"
        CEMSLOT_NUMBEROFSLOTS = "CemSlot_numberOfSlots"
        CEMSLOT_SLOTID = "CemSlot_slotId"
        CEMSLOT_P0_X = "CemSlot_P0_x"
        CEMSLOT_P0_Y = "CemSlot_P0_y"
        CEMSLOT_P1_X = "CemSlot_P1_x"
        CEMSLOT_P1_Y = "CemSlot_P1_y"
        CEMSLOT_P2_X = "CemSlot_P2_x"
        CEMSLOT_P2_Y = "CemSlot_P2_y"
        CEMSLOT_P3_X = "CemSlot_P3_x"
        CEMSLOT_P3_Y = "CemSlot_P3_y"
        CEMSLOT_EXISTENCEPROBABILITY = "CemSlot_existenceProbability"
        CEMSLOT_SC_ANGLED = "CemSlot_sc_angled"
        CEMSLOT_SC_PARALLEL = "CemSlot_sc_parallel"
        CEMSLOT_SC_PERPENDICULAR = "CemSlot_sc_perpendicular"
        CEMWS_FRONT_SIGSTATUS = "CemWs_Front_eSigStatus"
        CEMWS_FRONT_TIMESTAMP = "CemWs_Front_timestamp"
        CEMWS_FRONT_NUMBEROFLINES = "CemWs_Front_numberOfLines"
        CEMWS_FRONT_PARKINGLINES_LINEID = "CemWs_Front_parkingLines_lineId"
        CEMWS_FRONT_PARKINGLINES_LINESTARTX = "CemWs_Front_parkingLines_lineStartX"
        CEMWS_FRONT_PARKINGLINES_LINESTARTY = "CemWs_Front_parkingLines_lineStartY"
        CEMWS_FRONT_PARKINGLINES_LINEENDX = "CemWs_Front_parkingLines_lineEndX"
        CEMWS_FRONT_PARKINGLINES_LINEENDY = "CemWs_Front_parkingLines_lineEndY"
        CEMWS_FRONT_PARKINGLINES_LINECONFIDENCE = "CemWs_Front_parkingLines_lineConfidence"
        CEMWS_REAR_SIGSTATUS = "CemWs_Rear_eSigStatus"
        CEMWS_REAR_TIMESTAMP = "CemWs_Rear_timestamp"
        CEMWS_REAR_NUMBEROFLINES = "CemWs_Rear_numberOfLines"
        CEMWS_REAR_PARKINGLINES_LINEID = "CemWs_Rear_parkingLines_lineId"
        CEMWS_REAR_PARKINGLINES_LINESTARTX = "CemWs_Rear_parkingLines_lineStartX"
        CEMWS_REAR_PARKINGLINES_LINESTARTY = "CemWs_Rear_parkingLines_lineStartY"
        CEMWS_REAR_PARKINGLINES_LINEENDX = "CemWs_Rear_parkingLines_lineEndX"
        CEMWS_REAR_PARKINGLINES_LINEENDY = "CemWs_Rear_parkingLines_lineEndY"
        CEMWS_REAR_PARKINGLINES_LINECONFIDENCE = "CemWs_Rear_parkingLines_lineConfidence"
        CEMWS_LEFT_SIGSTATUS = "CemWs_Left_eSigStatus"
        CEMWS_LEFT_TIMESTAMP = "CemWs_Left_timestamp"
        CEMWS_LEFT_NUMBEROFLINES = "CemWs_Left_numberOfLines"
        CEMWS_LEFT_PARKINGLINES_LINEID = "CemWs_Left_parkingLines_lineId"
        CEMWS_LEFT_PARKINGLINES_LINESTARTX = "CemWs_Left_parkingLines_lineStartX"
        CEMWS_LEFT_PARKINGLINES_LINESTARTY = "CemWs_Left_parkingLines_lineStartY"
        CEMWS_LEFT_PARKINGLINES_LINEENDX = "CemWs_Left_parkingLines_lineEndX"
        CEMWS_LEFT_PARKINGLINES_LINEENDY = "CemWs_Left_parkingLines_lineEndY"
        CEMWS_LEFT_PARKINGLINES_LINECONFIDENCE = "CemWs_Left_parkingLines_lineConfidence"
        CEMWS_RIGHT_SIGSTATUS = "CemWs_Right_eSigStatus"
        CEMWS_RIGHT_TIMESTAMP = "CemWs_Right_timestamp"
        CEMWS_RIGHT_NUMBEROFLINES = "CemWs_Right_numberOfLines"
        CEMWS_RIGHT_PARKINGLINES_LINEID = "CemWs_Right_parkingLines_lineId"
        CEMWS_RIGHT_PARKINGLINES_LINESTARTX = "CemWs_Right_parkingLines_lineStartX"
        CEMWS_RIGHT_PARKINGLINES_LINESTARTY = "CemWs_Right_parkingLines_lineStartY"
        CEMWS_RIGHT_PARKINGLINES_LINEENDX = "CemWs_Right_parkingLines_lineEndX"
        CEMWS_RIGHT_PARKINGLINES_LINEENDY = "CemWs_Right_parkingLines_lineEndY"
        CEMWS_RIGHT_PARKINGLINES_LINECONFIDENCE = "CemWs_Right_parkingLines_lineConfidence"
        CEMWL_FRONT_SIGSTATUS = "CemWl_Front_eSigStatus"
        CEMWL_FRONT_TIMESTAMP = "CemWl_Front_timestamp"
        CEMWL_FRONT_NUMBEROFLINES = "CemWl_Front_numberOfLines"
        CEMWL_FRONT_PARKINGLINES_LINEID = "CemWl_Front_parkingLines_lineId"
        CEMWL_FRONT_PARKINGLINES_LINESTARTX = "CemWl_Front_parkingLines_lineStartX"
        CEMWL_FRONT_PARKINGLINES_LINESTARTY = "CemWl_Front_parkingLines_lineStartY"
        CEMWL_FRONT_PARKINGLINES_LINEENDX = "CemWl_Front_parkingLines_lineEndX"
        CEMWL_FRONT_PARKINGLINES_LINEENDY = "CemWl_Front_parkingLines_lineEndY"
        CEMWL_FRONT_PARKINGLINES_LINECONFIDENCE = "CemWl_Front_parkingLines_lineConfidence"
        CEMWL_REAR_SIGSTATUS = "CemWl_Rear_eSigStatus"
        CEMWL_REAR_TIMESTAMP = "CemWl_Rear_timestamp"
        CEMWL_REAR_NUMBEROFLINES = "CemWl_Rear_numberOfLines"
        CEMWL_REAR_PARKINGLINES_LINEID = "CemWl_Rear_parkingLines_lineId"
        CEMWL_REAR_PARKINGLINES_LINESTARTX = "CemWl_Rear_parkingLines_lineStartX"
        CEMWL_REAR_PARKINGLINES_LINESTARTY = "CemWl_Rear_parkingLines_lineStartY"
        CEMWL_REAR_PARKINGLINES_LINEENDX = "CemWl_Rear_parkingLines_lineEndX"
        CEMWL_REAR_PARKINGLINES_LINEENDY = "CemWl_Rear_parkingLines_lineEndY"
        CEMWL_REAR_PARKINGLINES_LINECONFIDENCE = "CemWl_Rear_parkingLines_lineConfidence"
        CEMWL_LEFT_SIGSTATUS = "CemWl_Left_eSigStatus"
        CEMWL_LEFT_TIMESTAMP = "CemWl_Left_timestamp"
        CEMWL_LEFT_NUMBEROFLINES = "CemWl_Left_numberOfLines"
        CEMWL_LEFT_PARKINGLINES_LINEID = "CemWl_Left_parkingLines_lineId"
        CEMWL_LEFT_PARKINGLINES_LINESTARTX = "CemWl_Left_parkingLines_lineStartX"
        CEMWL_LEFT_PARKINGLINES_LINESTARTY = "CemWl_Left_parkingLines_lineStartY"
        CEMWL_LEFT_PARKINGLINES_LINEENDX = "CemWl_Left_parkingLines_lineEndX"
        CEMWL_LEFT_PARKINGLINES_LINEENDY = "CemWl_Left_parkingLines_lineEndY"
        CEMWL_LEFT_PARKINGLINES_LINECONFIDENCE = "CemWl_Left_parkingLines_lineConfidence"
        CEMWL_RIGHT_SIGSTATUS = "CemWl_Right_eSigStatus"
        CEMWL_RIGHT_TIMESTAMP = "CemWl_Right_timestamp"
        CEMWL_RIGHT_NUMBEROFLINES = "CemWl_Right_numberOfLines"
        CEMWL_RIGHT_PARKINGLINES_LINEID = "CemWl_Right_parkingLines_lineId"
        CEMWL_RIGHT_PARKINGLINES_LINESTARTX = "CemWl_Right_parkingLines_lineStartX"
        CEMWL_RIGHT_PARKINGLINES_LINESTARTY = "CemWl_Right_parkingLines_lineStartY"
        CEMWL_RIGHT_PARKINGLINES_LINEENDX = "CemWl_Right_parkingLines_lineEndX"
        CEMWL_RIGHT_PARKINGLINES_LINEENDY = "CemWl_Right_parkingLines_lineEndY"
        CEMWL_RIGHT_PARKINGLINES_LINECONFIDENCE = "CemWl_Right_parkingLines_lineConfidence"
        CEMSL_FRONT_SIGSTATUS = "CemSl_Front_eSigStatus"
        CEMSL_FRONT_TIMESTAMP = "CemSl_Front_timestamp"
        CEMSL_FRONT_NUMBEROFLINES = "CemSl_Front_numberOfLines"
        CEMSL_REAR_SIGSTATUS = "CemSl_Rear_eSigStatus"
        CEMSL_REAR_TIMESTAMP = "CemSl_Rear_timestamp"
        CEMSL_REAR_NUMBEROFLINES = "CemSl_Rear_numberOfLines"
        CEMSL_LEFT_SIGSTATUS = "CemSl_Left_eSigStatus"
        CEMSL_LEFT_TIMESTAMP = "CemSl_Left_timestamp"
        CEMSL_LEFT_NUMBEROFLINES = "CemSl_Left_numberOfLines"
        CEMSL_RIGHT_SIGSTATUS = "CemSl_Right_eSigStatus"
        CEMSL_RIGHT_TIMESTAMP = "CemSl_Right_timestamp"
        CEMSL_RIGHT_NUMBEROFLINES = "CemSl_Right_numberOfLines"
        PSDSLOT_FRONT_TIMESTAMP = "PsdSlot_Front_timestamp"
        PSDSLOT_FRONT_SIGSTATUS = "PsdSlot_Front_eSigStatus"
        PSDSLOT_FRONT_NUMBEROFSLOTS = "PsdSlot_Front_numberOfSlots"
        PSDSLOT_FRONT_PARKINGLINES_P0_X = "PsdSlot_Front_parkingLines_P0_x"
        PSDSLOT_FRONT_PARKINGLINES_P0_Y = "PsdSlot_Front_parkingLines_P0_y"
        PSDSLOT_FRONT_PARKINGLINES_P1_X = "PsdSlot_Front_parkingLines_P1_x"
        PSDSLOT_FRONT_PARKINGLINES_P1_Y = "PsdSlot_Front_parkingLines_P1_y"
        PSDSLOT_FRONT_PARKINGLINES_P2_X = "PsdSlot_Front_parkingLines_P2_x"
        PSDSLOT_FRONT_PARKINGLINES_P2_Y = "PsdSlot_Front_parkingLines_P2_y"
        PSDSLOT_FRONT_PARKINGLINES_P3_X = "PsdSlot_Front_parkingLines_P3_x"
        PSDSLOT_FRONT_PARKINGLINES_P3_Y = "PsdSlot_Front_parkingLines_P3_y"
        PSDSLOT_FRONT_PARKINGLINES_SC_ANGLED = "PsdSlot_Front_parkingLines_sc_angled"
        PSDSLOT_FRONT_PARKINGLINES_SC_PARALLEL = "PsdSlot_Front_parkingLines_sc_parallel"
        PSDSLOT_FRONT_PARKINGLINES_SC_PERPENDICULAR = "PsdSlot_Front_parkingLines_sc_perpendicular"
        PSDSLOT_FRONT_PARKINGLINES_EXISTENCEPROBABILITY = "PsdSlot_Front_parkingLines_existenceProbability"
        PSDSLOT_FRONT_PARKINGLINES_OCCLUSIONSTATE = "PsdSlot_Front_parkingLines_occlusionState"
        PSDSLOT_REAR_TIMESTAMP = "PsdSlot_Rear_timestamp"
        PSDSLOT_REAR_SIGSTATUS = "PsdSlot_Rear_eSigStatus"
        PSDSLOT_REAR_NUMBEROFSLOTS = "PsdSlot_Rear_numberOfSlots"
        PSDSLOT_REAR_PARKINGLINES_P0_X = "PsdSlot_Rear_parkingLines_P0_x"
        PSDSLOT_REAR_PARKINGLINES_P0_Y = "PsdSlot_Rear_parkingLines_P0_y"
        PSDSLOT_REAR_PARKINGLINES_P1_X = "PsdSlot_Rear_parkingLines_P1_x"
        PSDSLOT_REAR_PARKINGLINES_P1_Y = "PsdSlot_Rear_parkingLines_P1_y"
        PSDSLOT_REAR_PARKINGLINES_P2_X = "PsdSlot_Rear_parkingLines_P2_x"
        PSDSLOT_REAR_PARKINGLINES_P2_Y = "PsdSlot_Rear_parkingLines_P2_y"
        PSDSLOT_REAR_PARKINGLINES_P3_X = "PsdSlot_Rear_parkingLines_P3_x"
        PSDSLOT_REAR_PARKINGLINES_P3_Y = "PsdSlot_Rear_parkingLines_P3_y"
        PSDSLOT_REAR_PARKINGLINES_SC_ANGLED = "PsdSlot_Rear_parkingLines_sc_angled"
        PSDSLOT_REAR_PARKINGLINES_SC_PARALLEL = "PsdSlot_Rear_parkingLines_sc_parallel"
        PSDSLOT_REAR_PARKINGLINES_SC_PERPENDICULAR = "PsdSlot_Rear_parkingLines_sc_perpendicular"
        PSDSLOT_REAR_PARKINGLINES_EXISTENCEPROBABILITY = "PsdSlot_Rear_parkingLines_existenceProbability"
        PSDSLOT_REAR_PARKINGLINES_OCCLUSIONSTATE = "PsdSlot_Rear_parkingLines_occlusionState"
        PSDSLOT_LEFT_TIMESTAMP = "PsdSlot_Left_timestamp"
        PSDSLOT_LEFT_SIGSTATUS = "PsdSlot_Left_eSigStatus"
        PSDSLOT_LEFT_NUMBEROFSLOTS = "PsdSlot_Left_numberOfSlots"
        PSDSLOT_LEFT_PARKINGLINES_P0_X = "PsdSlot_Left_parkingLines_P0_x"
        PSDSLOT_LEFT_PARKINGLINES_P0_Y = "PsdSlot_Left_parkingLines_P0_y"
        PSDSLOT_LEFT_PARKINGLINES_P1_X = "PsdSlot_Left_parkingLines_P1_x"
        PSDSLOT_LEFT_PARKINGLINES_P1_Y = "PsdSlot_Left_parkingLines_P1_y"
        PSDSLOT_LEFT_PARKINGLINES_P2_X = "PsdSlot_Left_parkingLines_P2_x"
        PSDSLOT_LEFT_PARKINGLINES_P2_Y = "PsdSlot_Left_parkingLines_P2_y"
        PSDSLOT_LEFT_PARKINGLINES_P3_X = "PsdSlot_Left_parkingLines_P3_x"
        PSDSLOT_LEFT_PARKINGLINES_P3_Y = "PsdSlot_Left_parkingLines_P3_y"
        PSDSLOT_LEFT_PARKINGLINES_SC_ANGLED = "PsdSlot_Left_parkingLines_sc_angled"
        PSDSLOT_LEFT_PARKINGLINES_SC_PARALLEL = "PsdSlot_Left_parkingLines_sc_parallel"
        PSDSLOT_LEFT_PARKINGLINES_SC_PERPENDICULAR = "PsdSlot_Left_parkingLines_sc_perpendicular"
        PSDSLOT_LEFT_PARKINGLINES_EXISTENCEPROBABILITY = "PsdSlot_Left_parkingLines_existenceProbability"
        PSDSLOT_LEFT_PARKINGLINES_OCCLUSIONSTATE = "PsdSlot_Left_parkingLines_occlusionState"
        PSDSLOT_RIGHT_TIMESTAMP = "PsdSlot_Right_timestamp"
        PSDSLOT_RIGHT_SIGSTATUS = "PsdSlot_Right_eSigStatus"
        PSDSLOT_RIGHT_NUMBEROFSLOTS = "PsdSlot_Right_numberOfSlots"
        PSDSLOT_RIGHT_PARKINGLINES_P0_X = "PsdSlot_Right_parkingLines_P0_x"
        PSDSLOT_RIGHT_PARKINGLINES_P0_Y = "PsdSlot_Right_parkingLines_P0_y"
        PSDSLOT_RIGHT_PARKINGLINES_P1_X = "PsdSlot_Right_parkingLines_P1_x"
        PSDSLOT_RIGHT_PARKINGLINES_P1_Y = "PsdSlot_Right_parkingLines_P1_y"
        PSDSLOT_RIGHT_PARKINGLINES_P2_X = "PsdSlot_Right_parkingLines_P2_x"
        PSDSLOT_RIGHT_PARKINGLINES_P2_Y = "PsdSlot_Right_parkingLines_P2_y"
        PSDSLOT_RIGHT_PARKINGLINES_P3_X = "PsdSlot_Right_parkingLines_P3_x"
        PSDSLOT_RIGHT_PARKINGLINES_P3_Y = "PsdSlot_Right_parkingLines_P3_y"
        PSDSLOT_RIGHT_PARKINGLINES_SC_ANGLED = "PsdSlot_Right_parkingLines_sc_angled"
        PSDSLOT_RIGHT_PARKINGLINES_SC_PARALLEL = "PsdSlot_Right_parkingLines_sc_parallel"
        PSDSLOT_RIGHT_PARKINGLINES_SC_PERPENDICULAR = "PsdSlot_Right_parkingLines_sc_perpendicular"
        PSDSLOT_RIGHT_PARKINGLINES_EXISTENCEPROBABILITY = "PsdSlot_Right_parkingLines_existenceProbability"
        PSDSLOT_RIGHT_PARKINGLINES_OCCLUSIONSTATE = "PsdSlot_Right_parkingLines_occlusionState"
        EM_EGOMOTIONPORT_ACCEL_MPS2 = "EgoMotionPort_accel_mps2"
        EM_EGOMOTIONPORT_DRIVEN_DIST = "EgoMotionPort_drivenDistance_m"
        EM_EGOMOTIONPORT_FRONT_WANGLE_RAD = "EgoMotionPort_frontWheelAngle_rad"
        EM_EGOMOTIONPORT_MOTION_STATE = "EgoMotionPort_motionState_nu"
        EM_EGOMOTIONPORT_PITCH_RAD = "EgoMotionPort_pitch_rad"
        EM_EGOMOTIONPORT_REAR_WANGLE_RAD = "EgoMotionPort_rearWheelAngle_rad"
        EM_EGOMOTIONPORT_ROLL_RAD = "EgoMotionPort_roll_rad"
        EM_EGOMOTIONPORT_SIGSTATUS = "EgoMotionPort_eSigStatus"
        EM_EGOMOTIONPORT_CYCLE_COUNTER = "EgoMotionPort_uiCycleCounter"
        EM_EGOMOTIONPORT_MEASURMENT_COUNTER = "EgoMotionPort_uiMeasurementCounter"
        EM_EGOMOTIONPORT_TIMESTAMP = "EgoMotionPort_uiTimeStamp"
        EM_EGOMOTIONPORT_VERSION_NUMBER = "EgoMotionPort_uiVersionNumber"
        EM_EGOMOTIONPORT_VEL_MPS = "EgoMotionPort_vel_mps"
        EM_EGOMOTIONPORT_YAW_RAD = "EgoMotionPort_yawRate_radps"
        SGF_NUMBER_OF_POLYGONS = "numPolygons"
        SGF_NUMBER_OF_VERTICES = "numberOfVertices"
        SGF_VERTICES = "vertices"
        SGF_VERTEX_X = "vertex_x"
        SGF_VERTEX_Y = "vertex_y"
        SGF_TIMESTAMP = "SGF_timestamp"
        SGF_OBJECT_ID = "polygonId"
        SGF_OBJECT_SEMANTIC_CLASS = "semanticClass_polygon"
        SGF_OBJECT_NUM_VERTICES = "numVertices_polygon"
        SGF_OBJECT_VERTEX_START_INDEX = "vertexStartIndex_polygon"
        SGF_OBJECT_WHEEL_TRAVERSABLE_CONFIDENCE = "wheelTraversableConfidence_polygon"
        SGF_OBJECT_BODY_TRAVERSABLE_CONFIDENCE = "bodyTraversableConfidence_polygon"
        SGF_OBJECT_HIGH_CONFIDENCE = "highConfidence_polygon"
        SGF_OBJECT_HANGING_CONFIDENCE = "hangingConfidence_polygon"
        SYNTHETIC_DATA = "synthetic_signal"
        SVC_POINT_LIST_SIGNAL_STATE = "SvcSigState"
        SVC_POINT_LIST_TIMESTAMP = "SvcTimestamp"
        SVC_POINT_LIST_OUTPUT = "SvcOutput"
        SVC_POLYLINE_SIGNAL_STATE = "SvcPolylineSigState"
        SVC_POLYLINE_TIMESTAMP = "SvcPolylineTimestamp"
        SVC_POLYLINE_OUTPUT = "SvcPolylineOutput"
        TP_OBJECT_LIST_SIGNAL_STATE = "TpfSigState"
        TP_OBJECT_LIST_TIMESTAMP = "TpfTimestamp"
        TP_OBJECT_LIST_OUTPUT = "TpfOutput"
        USS_SIGNAL_STATE = "UssSigState"
        USS_TIMESTAMP = "UssTimestamp"
        USS_OUTPUT = "UssOutput"
        FR1_x = "Fr1_x"
        FR1_y = "Fr1_y"
        SYNTHETIC_YAW = "synthetic_yaw"
        POS_SIZE_M = "pos_m.actualSize"
        EXISTENCE_PROB = "existenceProb_perc"
        WIDTH_M = "width_m"
        LINE_START_X = "pos_m.array._0_.x_dir"
        LINE_END_X = "pos_m.array._1_.x_dir"
        LINE_START_Y = "pos_m.array._0_.y_dir"
        LINE_END_Y = "pos_m.array._1_.y_dir"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["cem_outpus_sub.dynamic_objects", "CarPC.EM_Thread.CemInDynamicEnvironment"]

        self._properties = [
            (
                self.Columns.TIMESTAMP,
                ".timestamp_us",
            ),
            (
                self.Columns.PSDSLOT_FRONT_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.header.t_Stamp.u_Nsec",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.timestamp",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PSDSLOT_FRONT_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.sensor_header.e_SignalStatus",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.signalState",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PSDSLOT_FRONT_NUMBEROFSLOTS,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.number_of_slots",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.number_of_slots",
                    "SIM VFB.PMSDINSTANCE_fc.Slots.numberOfSlots",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.numberOfSlots",
                ],
            ),
            (
                self.Columns.PSDSLOT_FRONT_PARKINGLINES_P0_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].slot_corners[0].x",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].slot_corners[0].x",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_0.x",
                ],
            ),
            (
                self.Columns.PSDSLOT_FRONT_PARKINGLINES_P0_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].slot_corners[0].y",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].slot_corners[0].y",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_0.y",
                ],
            ),
            (
                self.Columns.PSDSLOT_FRONT_PARKINGLINES_P1_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].slot_corners[1].x",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].slot_corners[1].x",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_1.x",
                ],
            ),
            (
                self.Columns.PSDSLOT_FRONT_PARKINGLINES_P1_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].slot_corners[1].y",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].slot_corners[1].y",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_1.y",
                ],
            ),
            (
                self.Columns.PSDSLOT_FRONT_PARKINGLINES_P2_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].slot_corners[2].x",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].slot_corners[2].x",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_2.x",
                ],
            ),
            (
                self.Columns.PSDSLOT_FRONT_PARKINGLINES_P2_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].slot_corners[2].y",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].slot_corners[2].y",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_2.y",
                ],
            ),
            (
                self.Columns.PSDSLOT_FRONT_PARKINGLINES_P3_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].slot_corners[3].x",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].slot_corners[3].x",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_3.x",
                ],
            ),
            (
                self.Columns.PSDSLOT_FRONT_PARKINGLINES_P3_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].slot_corners[3].y",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].slot_corners[3].y",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_3.y",
                ],
            ),
            (
                self.Columns.PSDSLOT_FRONT_PARKINGLINES_SC_ANGLED,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].parking_scenario_confidence.angled",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].parking_scenario_confidence.angled",
                    "SIM VFB.PMSDINSTANCE_fc.Slots.parkingSlots[%].parkingScenarioConfidence.angled",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.angled",
                ],
            ),
            (
                self.Columns.PSDSLOT_FRONT_PARKINGLINES_SC_PARALLEL,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].parking_scenario_confidence.parallel",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].parking_scenario_confidence.parallel",
                    "SIM VFB.PMSDINSTANCE_fc.Slots.parkingSlots[%].parkingScenarioConfidence.parallel",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.parallel",
                ],
            ),
            (
                self.Columns.PSDSLOT_FRONT_PARKINGLINES_SC_PERPENDICULAR,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].parking_scenario_confidence.perpendicular",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].parking_scenario_confidence.perpendicular",
                    "SIM VFB.PMSDINSTANCE_fc.Slots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                ],
            ),
            (
                self.Columns.PSDSLOT_FRONT_PARKINGLINES_EXISTENCEPROBABILITY,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].existence_probability",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].existence_probability",
                    "SIM VFB.PMSDINSTANCE_fc.Slots.parkingSlots[%].existenceProbability",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].existenceProbability",
                ],
            ),
            (
                self.Columns.PSDSLOT_FRONT_PARKINGLINES_OCCLUSIONSTATE,
                [
                    "SIM VFB.PMSDINSTANCE_fc.Slots.parkingSlots[%].cornerOcclusionState",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].cornerOcclusionState",
                ],
            ),
            (
                self.Columns.PSDSLOT_REAR_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.header.t_Stamp.u_Nsec",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.timestamp",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PSDSLOT_REAR_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.sensor_header.e_SignalStatus",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.signalState",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PSDSLOT_REAR_NUMBEROFSLOTS,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.number_of_slots",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.number_of_slots",
                    "SIM VFB.PMSDINSTANCE_rc.Slots.numberOfSlots",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.numberOfSlots",
                ],
            ),
            (
                self.Columns.PSDSLOT_REAR_PARKINGLINES_P0_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].slot_corners[0].x",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].slot_corners[0].x",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_0.x",
                ],
            ),
            (
                self.Columns.PSDSLOT_REAR_PARKINGLINES_P0_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].slot_corners[0].y",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].slot_corners[0].y",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_0.y",
                ],
            ),
            (
                self.Columns.PSDSLOT_REAR_PARKINGLINES_P1_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].slot_corners[1].x",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].slot_corners[1].x",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_1.x",
                ],
            ),
            (
                self.Columns.PSDSLOT_REAR_PARKINGLINES_P1_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].slot_corners[1].y",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].slot_corners[1].y",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_1.y",
                ],
            ),
            (
                self.Columns.PSDSLOT_REAR_PARKINGLINES_P2_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].slot_corners[2].x",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].slot_corners[2].x",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_2.x",
                ],
            ),
            (
                self.Columns.PSDSLOT_REAR_PARKINGLINES_P2_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].slot_corners[2].y",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].slot_corners[2].y",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_2.y",
                ],
            ),
            (
                self.Columns.PSDSLOT_REAR_PARKINGLINES_P3_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].slot_corners[3].x",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].slot_corners[3].x",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_3.x",
                ],
            ),
            (
                self.Columns.PSDSLOT_REAR_PARKINGLINES_P3_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].slot_corners[3].y",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].slot_corners[3].y",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_3.y",
                ],
            ),
            (
                self.Columns.PSDSLOT_REAR_PARKINGLINES_SC_ANGLED,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].parking_scenario_confidence.angled",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].parking_scenario_confidence.angled",
                    "SIM VFB.PMSDINSTANCE_rc.Slots.parkingSlots[%].parkingScenarioConfidence.angled",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.angled",
                ],
            ),
            (
                self.Columns.PSDSLOT_REAR_PARKINGLINES_SC_PARALLEL,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].parking_scenario_confidence.parallel",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].parking_scenario_confidence.parallel",
                    "SIM VFB.PMSDINSTANCE_rc.Slots.parkingSlots[%].parkingScenarioConfidence.parallel",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.parallel",
                ],
            ),
            (
                self.Columns.PSDSLOT_REAR_PARKINGLINES_SC_PERPENDICULAR,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].parking_scenario_confidence.perpendicular",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].parking_scenario_confidence.perpendicular",
                    "SIM VFB.PMSDINSTANCE_rc.Slots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                ],
            ),
            (
                self.Columns.PSDSLOT_REAR_PARKINGLINES_EXISTENCEPROBABILITY,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].existence_probability",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].existence_probability",
                    "SIM VFB.PMSDINSTANCE_rc.Slots.parkingSlots[%].existenceProbability",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].existenceProbability",
                ],
            ),
            (
                self.Columns.PSDSLOT_REAR_PARKINGLINES_OCCLUSIONSTATE,
                [
                    "SIM VFB.PMSDINSTANCE_rc.Slots.parkingSlots[%].cornerOcclusionState",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].cornerOcclusionState",
                ],
            ),
            (
                self.Columns.PSDSLOT_LEFT_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.header.t_Stamp.u_Nsec",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.timestamp",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PSDSLOT_LEFT_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.sensor_header.e_SignalStatus",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.signalState",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PSDSLOT_LEFT_NUMBEROFSLOTS,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.number_of_slots",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.number_of_slots",
                    "SIM VFB.PMSDINSTANCE_lsc.Slots.numberOfSlots",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.numberOfSlots",
                ],
            ),
            (
                self.Columns.PSDSLOT_LEFT_PARKINGLINES_P0_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].slot_corners[0].x",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].slot_corners[0].x",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_0.x",
                ],
            ),
            (
                self.Columns.PSDSLOT_LEFT_PARKINGLINES_P0_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].slot_corners[0].y",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].slot_corners[0].y",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_0.y",
                ],
            ),
            (
                self.Columns.PSDSLOT_LEFT_PARKINGLINES_P1_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].slot_corners[1].x",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].slot_corners[1].x",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_1.x",
                ],
            ),
            (
                self.Columns.PSDSLOT_LEFT_PARKINGLINES_P1_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].slot_corners[1].y",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].slot_corners[1].y",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_1.y",
                ],
            ),
            (
                self.Columns.PSDSLOT_LEFT_PARKINGLINES_P2_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].slot_corners[2].x",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].slot_corners[2].x",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_2.x",
                ],
            ),
            (
                self.Columns.PSDSLOT_LEFT_PARKINGLINES_P2_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].slot_corners[2].y",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].slot_corners[2].y",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_2.y",
                ],
            ),
            (
                self.Columns.PSDSLOT_LEFT_PARKINGLINES_P3_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].slot_corners[3].x",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].slot_corners[3].x",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_3.x",
                ],
            ),
            (
                self.Columns.PSDSLOT_LEFT_PARKINGLINES_P3_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].slot_corners[3].y",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].slot_corners[3].y",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_3.y",
                ],
            ),
            (
                self.Columns.PSDSLOT_LEFT_PARKINGLINES_SC_ANGLED,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].parking_scenario_confidence.angled",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].parking_scenario_confidence.angled",
                    "SIM VFB.PMSDINSTANCE_lsc.Slots.parkingSlots[%].parkingScenarioConfidence.angled",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.angled",
                ],
            ),
            (
                self.Columns.PSDSLOT_LEFT_PARKINGLINES_SC_PARALLEL,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].parking_scenario_confidence.parallel",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].parking_scenario_confidence.parallel",
                    "SIM VFB.PMSDINSTANCE_lsc.Slots.parkingSlots[%].parkingScenarioConfidence.parallel",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.parallel",
                ],
            ),
            (
                self.Columns.PSDSLOT_LEFT_PARKINGLINES_SC_PERPENDICULAR,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].parking_scenario_confidence.perpendicular",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].parking_scenario_confidence.perpendicular",
                    "SIM VFB.PMSDINSTANCE_lsc.Slots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                ],
            ),
            (
                self.Columns.PSDSLOT_LEFT_PARKINGLINES_EXISTENCEPROBABILITY,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].existence_probability",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].existence_probability",
                    "SIM VFB.PMSDINSTANCE_lsc.Slots.parkingSlots[%].existenceProbability",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].existenceProbability",
                ],
            ),
            (
                self.Columns.PSDSLOT_LEFT_PARKINGLINES_OCCLUSIONSTATE,
                [
                    "SIM VFB.PMSDINSTANCE_lsc.Slots.parkingSlots[%].cornerOcclusionState",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].cornerOcclusionState",
                ],
            ),
            (
                self.Columns.PSDSLOT_RIGHT_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.header.t_Stamp.u_Nsec",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.timestamp",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PSDSLOT_RIGHT_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.sensor_header.e_SignalStatus",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.signalState",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PSDSLOT_RIGHT_NUMBEROFSLOTS,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.number_of_slots",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.number_of_slots",
                    "SIM VFB.PMSDINSTANCE_rsc.Slots.numberOfSlots",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.numberOfSlots",
                ],
            ),
            (
                self.Columns.PSDSLOT_RIGHT_PARKINGLINES_P0_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].slot_corners[0].x",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].slot_corners[0].x",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_0.x",
                ],
            ),
            (
                self.Columns.PSDSLOT_RIGHT_PARKINGLINES_P0_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].slot_corners[0].y",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].slot_corners[0].y",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_0.y",
                ],
            ),
            (
                self.Columns.PSDSLOT_RIGHT_PARKINGLINES_P1_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].slot_corners[1].x",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].slot_corners[1].x",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_1.x",
                ],
            ),
            (
                self.Columns.PSDSLOT_RIGHT_PARKINGLINES_P1_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].slot_corners[1].y",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].slot_corners[1].y",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_1.y",
                ],
            ),
            (
                self.Columns.PSDSLOT_RIGHT_PARKINGLINES_P2_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].slot_corners[2].x",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].slot_corners[2].x",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_2.x",
                ],
            ),
            (
                self.Columns.PSDSLOT_RIGHT_PARKINGLINES_P2_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].slot_corners[2].y",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].slot_corners[2].y",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_2.y",
                ],
            ),
            (
                self.Columns.PSDSLOT_RIGHT_PARKINGLINES_P3_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].slot_corners[3].x",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].slot_corners[3].x",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_3.x",
                ],
            ),
            (
                self.Columns.PSDSLOT_RIGHT_PARKINGLINES_P3_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].slot_corners[3].y",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].slot_corners[3].y",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_3.y",
                ],
            ),
            (
                self.Columns.PSDSLOT_RIGHT_PARKINGLINES_SC_ANGLED,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].parking_scenario_confidence.angled",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].parking_scenario_confidence.angled",
                    "SIM VFB.PMSDINSTANCE_rsc.Slots.parkingSlots[%].parkingScenarioConfidence.angled",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.angled",
                ],
            ),
            (
                self.Columns.PSDSLOT_RIGHT_PARKINGLINES_SC_PARALLEL,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].parking_scenario_confidence.parallel",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].parking_scenario_confidence.parallel",
                    "SIM VFB.PMSDINSTANCE_rsc.Slots.parkingSlots[%].parkingScenarioConfidence.parallel",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.parallel",
                ],
            ),
            (
                self.Columns.PSDSLOT_RIGHT_PARKINGLINES_SC_PERPENDICULAR,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].parking_scenario_confidence.perpendicular",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].parking_scenario_confidence.perpendicular",
                    "SIM VFB.PMSDINSTANCE_rsc.Slots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                ],
            ),
            (
                self.Columns.PSDSLOT_RIGHT_PARKINGLINES_EXISTENCEPROBABILITY,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].existence_probability",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].existence_probability",
                    "SIM VFB.PMSDINSTANCE_rsc.Slots.parkingSlots[%].existenceProbability",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].existenceProbability",
                ],
            ),
            (
                self.Columns.PSDSLOT_RIGHT_PARKINGLINES_OCCLUSIONSTATE,
                [
                    "SIM VFB.PMSDINSTANCE_rsc.Slots.parkingSlots[%].cornerOcclusionState",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].cornerOcclusionState",
                ],
            ),
            (
                self.Columns.CEMWS_FRONT_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListFront.signalState",
                    "CarPC.EM_Thread.WheelStopperFront.signalState",
                    "MTA_ADC5.PMSD_FC_DATA.WheelStopperLines.sSigHeader.eSigStatus",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.CEMWS_FRONT_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListFront.timestamp",
                    "CarPC.EM_Thread.WheelStopperFront.timestamp",
                    "MTA_ADC5.PMSD_FC_DATA.WheelStopperLines.sSigHeader.uiTimeStamp",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.CEMWS_FRONT_NUMBEROFLINES,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListFront.numberOfLines",
                    "CarPC.EM_Thread.WheelStopperFront.numberOfLines",
                    "MTA_ADC5.PMSD_FC_DATA.WheelStopperLines.numberOfLines",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.numberOfDelimiters",
                ],
            ),
            (
                self.Columns.CEMWS_FRONT_PARKINGLINES_LINEID,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListFront.parkingLines[%].lineId",
                    "CarPC.EM_Thread.WheelStopperFront.parkingLines[%].lineId",
                    "MTA_ADC5.PMSD_FC_DATA.WheelStopperLines.parkingLines[%].lineId",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].delimiterId",
                ],
            ),
            (
                self.Columns.CEMWS_FRONT_PARKINGLINES_LINESTARTX,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListFront.parkingLines[%].lineStartX",
                    "CarPC.EM_Thread.WheelStopperFront.parkingLines[%].lineStartX",
                    "MTA_ADC5.PMSD_FC_DATA.WheelStopperLines.parkingLines[%].lineStartXInM",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].startPointXPosition",
                ],
            ),
            (
                self.Columns.CEMWS_FRONT_PARKINGLINES_LINESTARTY,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListFront.parkingLines[%].lineStartY",
                    "CarPC.EM_Thread.WheelStopperFront.parkingLines[%].lineStartY",
                    "MTA_ADC5.PMSD_FC_DATA.WheelStopperLines.parkingLines[%].lineStartYInM",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].startPointYPosition",
                ],
            ),
            (
                self.Columns.CEMWS_FRONT_PARKINGLINES_LINEENDX,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListFront.parkingLines[%].lineEndX",
                    "CarPC.EM_Thread.WheelStopperFront.parkingLines[%].lineEndX",
                    "MTA_ADC5.PMSD_FC_DATA.WheelStopperLines.parkingLines[%].lineEndXinM",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].endPointXPosition",
                ],
            ),
            (
                self.Columns.CEMWS_FRONT_PARKINGLINES_LINEENDY,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListFront.parkingLines[%].lineEndY",
                    "CarPC.EM_Thread.WheelStopperFront.parkingLines[%].lineEndY",
                    "MTA_ADC5.PMSD_FC_DATA.WheelStopperLines.parkingLines[%].lineEndYinM",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].endPointYPosition",
                ],
            ),
            (
                self.Columns.CEMWS_FRONT_PARKINGLINES_LINECONFIDENCE,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListFront.parkingLines[%].lineConfidence",
                    "CarPC.EM_Thread.WheelStopperFront.parkingLines[%].lineConfidence",
                    "MTA_ADC5.PMSD_FC_DATA.WheelStopperLines.parkingLines[%].lineConfidence",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].confidencePercent",
                ],
            ),
            (
                self.Columns.CEMWS_REAR_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListFront.signalState",
                    "CarPC.EM_Thread.WheelStopperRear.signalState",
                    "MTA_ADC5.PMSD_RC_DATA.WheelStopperLines.sSigHeader.eSigStatus",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.CEMWS_REAR_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListRear.timestamp",
                    "CarPC.EM_Thread.WheelStopperRear.timestamp",
                    "MTA_ADC5.PMSD_RC_DATA.WheelStopperLines.sSigHeader.uiTimeStamp",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.CEMWS_REAR_NUMBEROFLINES,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListRear.numberOfLines",
                    "CarPC.EM_Thread.WheelStopperRear.numberOfLines",
                    "MTA_ADC5.PMSD_RC_DATA.WheelStopperLines.numberOfLines",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.numberOfDelimiters",
                ],
            ),
            (
                self.Columns.CEMWS_REAR_PARKINGLINES_LINEID,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListRear.parkingLines[%].lineId",
                    "CarPC.EM_Thread.WheelStopperRear.parkingLines[%].lineId",
                    "MTA_ADC5.PMSD_RC_DATA.WheelStopperLines.parkingLines[%].lineId",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].delimiterId",
                ],
            ),
            (
                self.Columns.CEMWS_REAR_PARKINGLINES_LINESTARTX,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListRear.parkingLines[%].lineStartX",
                    "CarPC.EM_Thread.WheelStopperRear.parkingLines[%].lineStartX",
                    "MTA_ADC5.PMSD_RC_DATA.WheelStopperLines.parkingLines[%].lineStartXInM",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].startPointXPosition",
                ],
            ),
            (
                self.Columns.CEMWS_REAR_PARKINGLINES_LINESTARTY,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListRear.parkingLines[%].lineStartY",
                    "CarPC.EM_Thread.WheelStopperRear.parkingLines[%].lineStartY",
                    "MTA_ADC5.PMSD_RC_DATA.WheelStopperLines.parkingLines[%].lineStartYInM",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].startPointYPosition",
                ],
            ),
            (
                self.Columns.CEMWS_REAR_PARKINGLINES_LINEENDX,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListRear.parkingLines[%].lineEndX",
                    "CarPC.EM_Thread.WheelStopperRear.parkingLines[%].lineEndX",
                    "MTA_ADC5.PMSD_RC_DATA.WheelStopperLines.parkingLines[%].lineEndXinM",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].endPointXPosition",
                ],
            ),
            (
                self.Columns.CEMWS_REAR_PARKINGLINES_LINEENDY,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListRear.parkingLines[%].lineEndY",
                    "CarPC.EM_Thread.WheelStopperRear.parkingLines[%].lineEndY",
                    "MTA_ADC5.PMSD_RC_DATA.WheelStopperLines.parkingLines[%].lineEndYinM",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].endPointYPosition",
                ],
            ),
            (
                self.Columns.CEMWS_REAR_PARKINGLINES_LINECONFIDENCE,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListRear.parkingLines[%].lineConfidence",
                    "CarPC.EM_Thread.WheelStopperRear.parkingLines[%].lineConfidence",
                    "MTA_ADC5.PMSD_RC_DATA.WheelStopperLines.parkingLines[%].lineConfidence",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].confidencePercent",
                ],
            ),
            (
                self.Columns.CEMWS_LEFT_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListLeft.signalState",
                    "CarPC.EM_Thread.WheelStopperLeft.signalState",
                    "MTA_ADC5.PMSD_LSC_DATA.WheelStopperLines.sSigHeader.eSigStatus",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.CEMWS_LEFT_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListLeft.timestamp",
                    "CarPC.EM_Thread.WheelStopperLeft.timestamp",
                    "MTA_ADC5.PMSD_LSC_DATA.WheelStopperLines.sSigHeader.uiTimeStamp",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.CEMWS_LEFT_NUMBEROFLINES,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListLeft.numberOfLines",
                    "CarPC.EM_Thread.WheelStopperLeft.numberOfLines",
                    "MTA_ADC5.PMSD_LSC_DATA.WheelStopperLines.numberOfLines",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.numberOfDelimiters",
                ],
            ),
            (
                self.Columns.CEMWS_LEFT_PARKINGLINES_LINEID,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListLeft.parkingLines[%].lineId",
                    "CarPC.EM_Thread.WheelStopperLeft.parkingLines[%].lineId",
                    "MTA_ADC5.PMSD_LSC_DATA.WheelStopperLines.parkingLines[%].lineId",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].delimiterId",
                ],
            ),
            (
                self.Columns.CEMWS_LEFT_PARKINGLINES_LINESTARTX,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListLeft.parkingLines[%].lineStartX",
                    "CarPC.EM_Thread.WheelStopperLeft.parkingLines[%].lineStartX",
                    "MTA_ADC5.PMSD_LSC_DATA.WheelStopperLines.parkingLines[%].lineStartXInM",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].startPointXPosition",
                ],
            ),
            (
                self.Columns.CEMWS_LEFT_PARKINGLINES_LINESTARTY,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListLeft.parkingLines[%].lineStartY",
                    "CarPC.EM_Thread.WheelStopperLeft.parkingLines[%].lineStartY",
                    "MTA_ADC5.PMSD_LSC_DATA.WheelStopperLines.parkingLines[%].lineStartYInM",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].startPointYPosition",
                ],
            ),
            (
                self.Columns.CEMWS_LEFT_PARKINGLINES_LINEENDX,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListLeft.parkingLines[%].lineEndX",
                    "CarPC.EM_Thread.WheelStopperLeft.parkingLines[%].lineEndX",
                    "MTA_ADC5.PMSD_LSC_DATA.WheelStopperLines.parkingLines[%].lineEndXinM",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].endPointXPosition",
                ],
            ),
            (
                self.Columns.CEMWS_LEFT_PARKINGLINES_LINEENDY,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListLeft.parkingLines[%].lineEndY",
                    "CarPC.EM_Thread.WheelStopperLeft.parkingLines[%].lineEndY",
                    "MTA_ADC5.PMSD_LSC_DATA.WheelStopperLines.parkingLines[%].lineEndYinM",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].endPointYPosition",
                ],
            ),
            (
                self.Columns.CEMWS_LEFT_PARKINGLINES_LINECONFIDENCE,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListLeft.parkingLines[%].lineConfidence",
                    "CarPC.EM_Thread.WheelStopperLeft.parkingLines[%].lineConfidence",
                    "MTA_ADC5.PMSD_LSC_DATA.WheelStopperLines.parkingLines[%].lineConfidence",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].confidencePercent",
                ],
            ),
            (
                self.Columns.CEMWS_RIGHT_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListRight.signalState",
                    "CarPC.EM_Thread.WheelStopperRight.signalState",
                    "MTA_ADC5.PMSD_RSC_DATA.WheelStopperLines.sSigHeader.eSigStatus",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.CEMWS_RIGHT_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListRight.timestamp",
                    "CarPC.EM_Thread.WheelStopperRight.timestamp",
                    "MTA_ADC5.PMSD_RSC_DATA.WheelStopperLines.sSigHeader.uiTimeStamp",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.CEMWS_RIGHT_NUMBEROFLINES,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListRight.numberOfLines",
                    "CarPC.EM_Thread.WheelStopperRight.numberOfLines",
                    "MTA_ADC5.PMSD_RSC_DATA.WheelStopperLines.numberOfLines",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.numberOfDelimiters",
                ],
            ),
            (
                self.Columns.CEMWS_RIGHT_PARKINGLINES_LINEID,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListRight.parkingLines[%].lineId",
                    "CarPC.EM_Thread.WheelStopperRight.parkingLines[%].lineId",
                    "MTA_ADC5.PMSD_RSC_DATA.WheelStopperLines.parkingLines[%].lineId",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].delimiterId",
                ],
            ),
            (
                self.Columns.CEMWS_RIGHT_PARKINGLINES_LINESTARTX,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListRight.parkingLines[%].lineStartX",
                    "CarPC.EM_Thread.WheelStopperRight.parkingLines[%].lineStartX",
                    "MTA_ADC5.PMSD_RSC_DATA.WheelStopperLines.parkingLines[%].lineStartXInM",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].startPointXPosition",
                ],
            ),
            (
                self.Columns.CEMWS_RIGHT_PARKINGLINES_LINESTARTY,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListRight.parkingLines[%].lineStartY",
                    "CarPC.EM_Thread.WheelStopperRight.parkingLines[%].lineStartY",
                    "MTA_ADC5.PMSD_RSC_DATA.WheelStopperLines.parkingLines[%].lineStartYInM",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].startPointYPosition",
                ],
            ),
            (
                self.Columns.CEMWS_RIGHT_PARKINGLINES_LINEENDX,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListRight.parkingLines[%].lineEndX",
                    "CarPC.EM_Thread.WheelStopperRight.parkingLines[%].lineEndX",
                    "MTA_ADC5.PMSD_RSC_DATA.WheelStopperLines.parkingLines[%].lineEndXinM",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].endPointXPosition",
                ],
            ),
            (
                self.Columns.CEMWS_RIGHT_PARKINGLINES_LINEENDY,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListRight.parkingLines[%].lineEndY",
                    "CarPC.EM_Thread.WheelStopperRight.parkingLines[%].lineEndY",
                    "MTA_ADC5.PMSD_RSC_DATA.WheelStopperLines.parkingLines[%].lineEndYinM",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].endPointYPosition",
                ],
            ),
            (
                self.Columns.CEMWS_RIGHT_PARKINGLINES_LINECONFIDENCE,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperLineListRight.parkingLines[%].lineConfidence",
                    "CarPC.EM_Thread.WheelStopperRight.parkingLines[%].lineConfidence",
                    "MTA_ADC5.PMSD_RSC_DATA.WheelStopperLines.parkingLines[%].lineConfidence",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].confidencePercent",
                ],
            ),
            (
                self.Columns.CEMWL_FRONT_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerLineListFront.signalState",
                    "CarPC.EM_Thread.WheelLockerFront.signalState",
                    "MTA_ADC5.PMSD_FC_DATA.WheelLockerLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.CEMWL_FRONT_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerLineListFront.timestamp",
                    "CarPC.EM_Thread.WheelLockerFront.timestamp",
                    "MTA_ADC5.PMSD_FC_DATA.WheelLockerLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.CEMWL_FRONT_NUMBEROFLINES,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerLineListFront.numberOfLines",
                    "CarPC.EM_Thread.WheelLockerFront.numberOfLines",
                    "MTA_ADC5.PMSD_FC_DATA.WheelLockerLines.numberOfLines",
                ],
            ),
            (
                self.Columns.CEMWL_REAR_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerLineListRear.signalState",
                    "CarPC.EM_Thread.WheelLockerRear.signalState",
                    "MTA_ADC5.PMSD_RC_DATA.WheelLockerLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.CEMWL_REAR_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerLineListRear.timestamp",
                    "CarPC.EM_Thread.WheelLockerRear.timestamp",
                    "MTA_ADC5.PMSD_RC_DATA.WheelLockerLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.CEMWL_REAR_NUMBEROFLINES,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerLineListRear.numberOfLines",
                    "CarPC.EM_Thread.WheelLockerRear.numberOfLines",
                    "MTA_ADC5.PMSD_RC_DATA.WheelLockerLines.numberOfLines",
                ],
            ),
            (
                self.Columns.CEMWL_LEFT_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerLineListLeft.signalState",
                    "CarPC.EM_Thread.WheelLockerLeft.signalState",
                    "MTA_ADC5.PMSD_LSC_DATA.WheelLockerLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.CEMWL_LEFT_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerLineListLeft.timestamp",
                    "CarPC.EM_Thread.WheelLockerLeft.timestamp",
                    "MTA_ADC5.PMSD_LSC_DATA.WheelLockerLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.CEMWL_LEFT_NUMBEROFLINES,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerLineListLeft.numberOfLines",
                    "CarPC.EM_Thread.WheelLockerLeft.numberOfLines",
                    "MTA_ADC5.PMSD_LSC_DATA.WheelLockerLines.numberOfLines",
                ],
            ),
            (
                self.Columns.CEMWL_RIGHT_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerLineListRight.signalState",
                    "CarPC.EM_Thread.WheelLockerRight.signalState",
                    "MTA_ADC5.PMSD_RSC_DATA.WheelLockerLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.CEMWL_RIGHT_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerLineListRight.timestamp",
                    "CarPC.EM_Thread.WheelLockerRight.timestamp",
                    "MTA_ADC5.PMSD_RSC_DATA.WheelLockerLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.CEMWL_RIGHT_NUMBEROFLINES,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerLineListRight.numberOfLines",
                    "CarPC.EM_Thread.WheelLockerRight.numberOfLines",
                    "MTA_ADC5.PMSD_RSC_DATA.WheelLockerLines.numberOfLines",
                ],
            ),
            (
                self.Columns.CEMSL_FRONT_SIGSTATUS,
                [
                    "MTA_ADC5.PMSD_FC_DATA.StopLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.CEMSL_FRONT_TIMESTAMP,
                [
                    "MTA_ADC5.PMSD_FC_DATA.StopLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.CEMSL_FRONT_NUMBEROFLINES,
                [
                    "MTA_ADC5.PMSD_FC_DATA.StopLines.numberOfLines",
                ],
            ),
            (
                self.Columns.CEMSL_REAR_SIGSTATUS,
                [
                    "MTA_ADC5.PMSD_RC_DATA.StopLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.CEMSL_REAR_TIMESTAMP,
                [
                    "MTA_ADC5.PMSD_RC_DATA.StopLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.CEMSL_REAR_NUMBEROFLINES,
                [
                    "MTA_ADC5.PMSD_RC_DATA.StopLines.numberOfLines",
                ],
            ),
            (
                self.Columns.CEMSL_LEFT_SIGSTATUS,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.StopLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.CEMSL_LEFT_TIMESTAMP,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.StopLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.CEMSL_LEFT_NUMBEROFLINES,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.StopLines.numberOfLines",
                ],
            ),
            (
                self.Columns.CEMSL_RIGHT_SIGSTATUS,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.StopLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.CEMSL_RIGHT_TIMESTAMP,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.StopLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.CEMSL_RIGHT_NUMBEROFLINES,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.StopLines.numberOfLines",
                ],
            ),
            (
                self.Columns.CEMSLOT_TIMESTAMP,
                [
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingSlots.sSigHeader.uiTimeStamp",
                    "cem_outpus_sub.parking_slots.header.timestamp",
                    "CarPC.EM_Thread.CEMODSlotOutput.timestamp",
                    "parkingSlotDetectionOutput.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.CEM200_AUPDF_DATA.ParkingSlots.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.CEMSLOT_SIGSTATUS,
                [
                    "parkingSlotDetectionOutput.sSigHeader.eSigStatus",
                    "CarPC.EM_Thread.CEMODSlotOutput.cem_signal_state",
                    "MTA_ADC5.CEM200_AUPDF_DATA.ParkingSlots.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.CEMSLOT_NUMBEROFSLOTS,
                [
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingSlots.numberOfSlots",
                    "cem_outpus_sub.parking_slots.number_of_slots",
                    "CarPC.EM_Thread.CEMODSlotOutput.number_of_slots",
                    "parkingSlotDetectionOutput.numberOfSlots",
                    "MTA_ADC5.CEM200_AUPDF_DATA.ParkingSlots.numberOfSlots",
                ],
            ),
            (
                self.Columns.CEMSLOT_SLOTID,
                [
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingSlots.parkingSlots[%].slotId",
                    "cem_outpus_sub.parking_slots.parking_slots._%_.slotId",
                    "parkingSlotDetectionOutput.parking_slots._%_.slotId",
                    "CarPC.EM_Thread.CEMODSlotOutput.parking_slots[%].slotId",
                    "MTA_ADC5.CEM200_AUPDF_DATA.ParkingSlots.parkingSlots[%].slotId",
                ],
            ),
            (
                self.Columns.CEMSLOT_P0_X,
                [
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingSlots.parkingSlots[%].slotCorners[0].x",
                    "cem_outpus_sub.parking_slots.parking_slots._%_.slot_corners._0_.x",
                    "parkingSlotDetectionOutput.parkingSlots_%_.slotCorners._0_.x",
                    "CarPC.EM_Thread.CEMODSlotOutput.parking_slots[%].slot_corners[0].x",
                    "MTA_ADC5.CEM200_AUPDF_DATA.ParkingSlots.parkingSlots[%].slotCorners[0].x",
                ],
            ),
            (
                self.Columns.CEMSLOT_P0_Y,
                [
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingSlots.parkingSlots[%].slotCorners[0].y",
                    "cem_outpus_sub.parking_slots.parking_slots._%_.slot_corners._0_.y",
                    "parkingSlotDetectionOutput.parkingSlots_%_.slotCorners._0_.y",
                    "CarPC.EM_Thread.CEMODSlotOutput.parking_slots[%].slot_corners[0].y",
                    "MTA_ADC5.CEM200_AUPDF_DATA.ParkingSlots.parkingSlots[%].slotCorners[0].y",
                ],
            ),
            (
                self.Columns.CEMSLOT_P1_X,
                [
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingSlots.parkingSlots[%].slotCorners[1].x",
                    "cem_outpus_sub.parking_slots.parking_slots._%_.slot_corners._1_.x",
                    "parkingSlotDetectionOutput.parkingSlots_%_.slotCorners._1_.x",
                    "CarPC.EM_Thread.CEMODSlotOutput.parking_slots[%].slot_corners[1].x",
                    "MTA_ADC5.CEM200_AUPDF_DATA.ParkingSlots.parkingSlots[%].slotCorners[1].x",
                ],
            ),
            (
                self.Columns.CEMSLOT_P1_Y,
                [
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingSlots.parkingSlots[%].slotCorners[1].y",
                    "cem_outpus_sub.parking_slots.parking_slots._%_.slot_corners._1_.y",
                    "parkingSlotDetectionOutput.parkingSlots_%_.slotCorners._1_.y",
                    "CarPC.EM_Thread.CEMODSlotOutput.parking_slots[%].slot_corners[1].y",
                    "MTA_ADC5.CEM200_AUPDF_DATA.ParkingSlots.parkingSlots[%].slotCorners[1].y",
                ],
            ),
            (
                self.Columns.CEMSLOT_P2_X,
                [
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingSlots.parkingSlots[%].slotCorners[2].x",
                    "cem_outpus_sub.parking_slots.parking_slots._%_.slot_corners._2_.x",
                    "parkingSlotDetectionOutput.parkingSlots_%_.slotCorners._2_.x",
                    "CarPC.EM_Thread.CEMODSlotOutput.parking_slots[%].slot_corners[2].x",
                    "MTA_ADC5.CEM200_AUPDF_DATA.ParkingSlots.parkingSlots[%].slotCorners[2].x",
                ],
            ),
            (
                self.Columns.CEMSLOT_P2_Y,
                [
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingSlots.parkingSlots[%].slotCorners[2].y",
                    "cem_outpus_sub.parking_slots.parking_slots._%_.slot_corners._2_.y",
                    "parkingSlotDetectionOutput.parkingSlots_%_.slotCorners._2_.y",
                    "CarPC.EM_Thread.CEMODSlotOutput.parking_slots[%].slot_corners[2].y",
                    "MTA_ADC5.CEM200_AUPDF_DATA.ParkingSlots.parkingSlots[%].slotCorners[2].y",
                ],
            ),
            (
                self.Columns.CEMSLOT_P3_X,
                [
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingSlots.parkingSlots[%].slotCorners[3].x",
                    "cem_outpus_sub.parking_slots.parking_slots._%_.slot_corners._3_.x",
                    "parkingSlotDetectionOutput.parkingSlots_%_.slotCorners._3_.x",
                    "CarPC.EM_Thread.CEMODSlotOutput.parking_slots[%].slot_corners[3].x",
                    "MTA_ADC5.CEM200_AUPDF_DATA.ParkingSlots.parkingSlots[%].slotCorners[3].x",
                ],
            ),
            (
                self.Columns.CEMSLOT_P3_Y,
                [
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingSlots.parkingSlots[%].slotCorners[3].y",
                    "cem_outpus_sub.parking_slots.parking_slots._%_.slot_corners._3_.y",
                    "parkingSlotDetectionOutput.parkingSlots_%_.slotCorners._3_.y",
                    "CarPC.EM_Thread.CEMODSlotOutput.parking_slots[%].slot_corners[3].y",
                    "MTA_ADC5.CEM200_AUPDF_DATA.ParkingSlots.parkingSlots[%].slotCorners[3].y",
                ],
            ),
            (
                self.Columns.CEMSLOT_EXISTENCEPROBABILITY,
                [
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingSlots.parkingSlots[].existenceProbability",
                    "cem_outpus_sub.parking_slots.parking_slots._%_.existence_probability",
                    "parkingSlotDetectionOutput.parkingSlots._%_.existenceProbability",
                    "CarPC.EM_Thread.CEMODSlotOutput.parking_slots[%].existence_probability",
                    "MTA_ADC5.CEM200_AUPDF_DATA.ParkingSlots.parkingSlots[%].existenceProbability",
                ],
            ),
            (
                self.Columns.CEMSLOT_SC_ANGLED,
                [
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingSlots.parkingSlots[].parkingScenarioConfidence.angled",
                    "cem_outpus_sub.parking_slots.parking_slots._%_.parking_scenario_confidence.angled",
                    "parkingSlotDetectionOutput.parkingSlots._%_.parkingScenarioConfidence.angled",
                    "CarPC.EM_Thread.CEMODSlotOutput.parking_slots[%].parking_scenario_confidence.angled",
                    "MTA_ADC5.CEM200_AUPDF_DATA.ParkingSlots.parkingSlots[%].parkingScenarioConfidence.angled",
                ],
            ),
            (
                self.Columns.CEMSLOT_SC_PARALLEL,
                [
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingSlots.parkingSlots[].parkingScenarioConfidence.parallel",
                    "cem_outpus_sub.parking_slots.parking_slots._%_.parking_scenario_confidence.parallel",
                    "parkingSlotDetectionOutput.parkingSlots._%_.parkingScenarioConfidence.parallel",
                    "CarPC.EM_Thread.CEMODSlotOutput.parking_slots[%].parking_scenario_confidence.parallel",
                    "MTA_ADC5.CEM200_AUPDF_DATA.ParkingSlots.parkingSlots[%].parkingScenarioConfidence.parallel",
                ],
            ),
            (
                self.Columns.CEMSLOT_SC_PERPENDICULAR,
                [
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingSlots.parkingSlots[].parkingScenarioConfidence.perpendicular",
                    "cem_outpus_sub.parking_slots.parking_slots._%_.parking_scenario_confidence.perpendicular",
                    "parkingSlotDetectionOutput.parkingSlots._%_.parkingScenarioConfidence.perpendicular",
                    "CarPC.EM_Thread.CEMODSlotOutput.parking_slots[%].parking_scenario_confidence.perpendicular",
                    "MTA_ADC5.CEM200_AUPDF_DATA.ParkingSlots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                ],
            ),
            (
                self.Columns.PMDCAMERA_FRONT_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListFront.signalState",
                    "CarPC.EM_Thread.PmdFront.signalState",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDCAMERA_FRONT_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListFront.timestamp",
                    "CarPC.EM_Thread.PmdFront.timestamp",
                    "SIM VFB.PMSDINSTANCE_fc.ParkingLines.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDCAMERA_FRONT_NUMBEROFLINES,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListFront.numberOfLines",
                    "CarPC.EM_Thread.PmdFront.numberOfLines",
                    "SIM VFB.PMSDINSTANCE_fc.ParkingLines.numberOfLines",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.numberOfLines",
                ],
            ),
            (
                self.Columns.PMDCAMERA_FRONT_PARKINGLINES_LINEID,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListFront.parkingLines[%].lineId",
                    "CarPC.EM_Thread.PmdFront.parkingLines[%].lineId",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.parkingLines[%].lineId",
                ],
            ),
            (
                self.Columns.PMDCAMERA_FRONT_PARKINGLINES_LINESTARTX,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListFront.parkingLines[%].lineStartX",
                    "CarPC.EM_Thread.PmdFront.parkingLines[%].lineStartX",
                    "SIM VFB.PMSDINSTANCE_fc.ParkingLines.parkingLines[%].lineStartXInM",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.parkingLines[%].lineStartXInM",
                ],
            ),
            (
                self.Columns.PMDCAMERA_FRONT_PARKINGLINES_LINESTARTY,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListFront.parkingLines[%].lineStartY",
                    "CarPC.EM_Thread.PmdFront.parkingLines[%].lineStartY",
                    "SIM VFB.PMSDINSTANCE_fc.ParkingLines.parkingLines[%].lineStartYInM",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.parkingLines[%].lineStartYInM",
                ],
            ),
            (
                self.Columns.PMDCAMERA_FRONT_PARKINGLINES_LINEENDX,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListFront.parkingLines[%].lineEndX",
                    "CarPC.EM_Thread.PmdFront.parkingLines[%].lineEndX",
                    "SIM VFB.PMSDINSTANCE_fc.ParkingLines.parkingLines[%].lineEndXinM",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.parkingLines[%].lineEndXinM",
                ],
            ),
            (
                self.Columns.PMDCAMERA_FRONT_PARKINGLINES_LINEENDY,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListFront.parkingLines[%].lineEndY",
                    "CarPC.EM_Thread.PmdFront.parkingLines[%].lineEndY",
                    "SIM VFB.PMSDINSTANCE_fc.ParkingLines.parkingLines[%].lineEndYinM",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.parkingLines[%].lineEndYinM",
                ],
            ),
            (
                self.Columns.PMDCAMERA_FRONT_PARKINGLINES_LINECONFIDENCE,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListFront.parkingLines[%].lineConfidence",
                    "CarPC.EM_Thread.PmdFront.parkingLines[%].lineConfidence",
                    "SIM VFB.PMSDINSTANCE_fc.ParkingLines.parkingLines[%].lineConfidence",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.parkingLines[%].lineConfidence",
                ],
            ),
            (
                self.Columns.PMDCAMERA_REAR_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRear.signalState",
                    "CarPC.EM_Thread.PmdRear.signalState",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDCAMERA_REAR_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRear.timestamp",
                    "CarPC.EM_Thread.PmdRear.timestamp",
                    "SIM VFB.PMSDINSTANCE_rc.ParkingLines.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDCAMERA_REAR_NUMBEROFLINES,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRear.numberOfLines",
                    "CarPC.EM_Thread.PmdRear.numberOfLines",
                    "SIM VFB.PMSDINSTANCE_rc.ParkingLines.numberOfLines",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.numberOfLines",
                ],
            ),
            (
                self.Columns.PMDCAMERA_REAR_PARKINGLINES_LINEID,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRear.parkingLines[%].lineId",
                    "CarPC.EM_Thread.PmdRear.parkingLines[%].lineId",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.parkingLines[%].lineId",
                ],
            ),
            (
                self.Columns.PMDCAMERA_REAR_PARKINGLINES_LINESTARTX,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRear.parkingLines[%].lineStartX",
                    "CarPC.EM_Thread.PmdRear.parkingLines[%].lineStartX",
                    "SIM VFB.PMSDINSTANCE_rc.ParkingLines.parkingLines[%].lineStartXInM",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.parkingLines[%].lineStartXInM",
                ],
            ),
            (
                self.Columns.PMDCAMERA_REAR_PARKINGLINES_LINESTARTY,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRear.parkingLines[%].lineStartY",
                    "CarPC.EM_Thread.PmdRear.parkingLines[%].lineStartY",
                    "SIM VFB.PMSDINSTANCE_rc.ParkingLines.parkingLines[%].lineStartYInM",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.parkingLines[%].lineStartYInM",
                ],
            ),
            (
                self.Columns.PMDCAMERA_REAR_PARKINGLINES_LINEENDX,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRear.parkingLines[%].lineEndX",
                    "CarPC.EM_Thread.PmdRear.parkingLines[%].lineEndX",
                    "SIM VFB.PMSDINSTANCE_rc.ParkingLines.parkingLines[%].lineEndXinM",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.parkingLines[%].lineEndXinM",
                ],
            ),
            (
                self.Columns.PMDCAMERA_REAR_PARKINGLINES_LINEENDY,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRear.parkingLines[%].lineEndY",
                    "CarPC.EM_Thread.PmdRear.parkingLines[%].lineEndY",
                    "SIM VFB.PMSDINSTANCE_rc.ParkingLines.parkingLines[%].lineEndYinM",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.parkingLines[%].lineEndYinM",
                ],
            ),
            (
                self.Columns.PMDCAMERA_REAR_PARKINGLINES_LINECONFIDENCE,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRear.parkingLines[%].lineConfidence",
                    "CarPC.EM_Thread.PmdRear.parkingLines[%].lineConfidence",
                    "SIM VFB.PMSDINSTANCE_rc.ParkingLines.parkingLines[%].lineConfidence",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.parkingLines[%].lineConfidence",
                ],
            ),
            (
                self.Columns.PMDCAMERA_LEFT_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListLeft.signalState",
                    "CarPC.EM_Thread.PmdLeft.signalState",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDCAMERA_LEFT_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListLeft.timestamp",
                    "CarPC.EM_Thread.PmdLeft.timestamp",
                    "SIM VFB.PMSDINSTANCE_lsc.ParkingLines.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDCAMERA_LEFT_NUMBEROFLINES,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListLeft.numberOfLines",
                    "CarPC.EM_Thread.PmdLeft.numberOfLines",
                    "SIM VFB.PMSDINSTANCE_lsc.ParkingLines.numberOfLines",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.numberOfLines",
                ],
            ),
            (
                self.Columns.PMDCAMERA_LEFT_PARKINGLINES_LINEID,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListLeft.parkingLines[%].lineId",
                    "CarPC.EM_Thread.PmdLeft.parkingLines[%].lineId",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.parkingLines[%].lineId",
                ],
            ),
            (
                self.Columns.PMDCAMERA_LEFT_PARKINGLINES_LINESTARTX,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListLeft.parkingLines[%].lineStartX",
                    "CarPC.EM_Thread.PmdLeft.parkingLines[%].lineStartX",
                    "SIM VFB.PMSDINSTANCE_lsc.ParkingLines.parkingLines[%].lineStartXInM",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.parkingLines[%].lineStartXInM",
                ],
            ),
            (
                self.Columns.PMDCAMERA_LEFT_PARKINGLINES_LINESTARTY,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListLeft.parkingLines[%].lineStartY",
                    "CarPC.EM_Thread.PmdLeft.parkingLines[%].lineStartY",
                    "SIM VFB.PMSDINSTANCE_lsc.ParkingLines.parkingLines[%].lineStartYInM",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.parkingLines[%].lineStartYInM",
                ],
            ),
            (
                self.Columns.PMDCAMERA_LEFT_PARKINGLINES_LINEENDX,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListLeft.parkingLines[%].lineEndX",
                    "CarPC.EM_Thread.PmdLeft.parkingLines[%].lineEndX",
                    "SIM VFB.PMSDINSTANCE_lsc.ParkingLines.parkingLines[%].lineEndXinM",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.parkingLines[%].lineEndXinM",
                ],
            ),
            (
                self.Columns.PMDCAMERA_LEFT_PARKINGLINES_LINEENDY,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListLeft.parkingLines[%].lineEndY",
                    "CarPC.EM_Thread.PmdLeft.parkingLines[%].lineEndY",
                    "SIM VFB.PMSDINSTANCE_lsc.ParkingLines.parkingLines[%].lineEndYinM",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.parkingLines[%].lineEndYinM",
                ],
            ),
            (
                self.Columns.PMDCAMERA_LEFT_PARKINGLINES_LINECONFIDENCE,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListLeft.parkingLines[%].lineConfidence",
                    "CarPC.EM_Thread.PmdLeft.parkingLines[%].lineConfidence",
                    "SIM VFB.PMSDINSTANCE_lsc.ParkingLines.parkingLines[%].lineConfidence",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.parkingLines[%].lineConfidence",
                ],
            ),
            (
                self.Columns.PMDCAMERA_RIGHT_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRight.signalState",
                    "CarPC.EM_Thread.PmdRight.signalState",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDCAMERA_RIGHT_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRight.timestamp",
                    "CarPC.EM_Thread.PmdRight.timestamp",
                    "SIM VFB.PMSDINSTANCE_rsc.ParkingLines.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDCAMERA_RIGHT_NUMBEROFLINES,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRight.numberOfLines",
                    "CarPC.EM_Thread.PmdRight.numberOfLines",
                    "SIM VFB.PMSDINSTANCE_rsc.ParkingLines.numberOfLines",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.numberOfLines",
                ],
            ),
            (
                self.Columns.PMDCAMERA_RIGHT_PARKINGLINES_LINEID,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRight.parkingLines[%].lineId",
                    "CarPC.EM_Thread.PmdRight.parkingLines[%].lineId",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.parkingLines[%].lineId",
                ],
            ),
            (
                self.Columns.PMDCAMERA_RIGHT_PARKINGLINES_LINESTARTX,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRight.parkingLines[%].lineStartX",
                    "CarPC.EM_Thread.PmdRight.parkingLines[%].lineStartX",
                    "SIM VFB.PMSDINSTANCE_rsc.ParkingLines.parkingLines[%].lineStartXInM",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.parkingLines[%].lineStartXInM",
                ],
            ),
            (
                self.Columns.PMDCAMERA_RIGHT_PARKINGLINES_LINESTARTY,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRight.parkingLines[%].lineStartY",
                    "CarPC.EM_Thread.PmdRight.parkingLines[%].lineStartY",
                    "SIM VFB.PMSDINSTANCE_rsc.ParkingLines.parkingLines[%].lineStartYInM",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.parkingLines[%].lineStartYInM",
                ],
            ),
            (
                self.Columns.PMDCAMERA_RIGHT_PARKINGLINES_LINEENDX,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRight.parkingLines[%].lineEndX",
                    "CarPC.EM_Thread.PmdRight.parkingLines[%].lineEndX",
                    "SIM VFB.PMSDINSTANCE_rsc.ParkingLines.parkingLines[%].lineEndXinM",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.parkingLines[%].lineEndXinM",
                ],
            ),
            (
                self.Columns.PMDCAMERA_RIGHT_PARKINGLINES_LINEENDY,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRight.parkingLines[%].lineEndY",
                    "CarPC.EM_Thread.PmdRight.parkingLines[%].lineEndY",
                    "SIM VFB.PMSDINSTANCE_rsc.ParkingLines.parkingLines[%].lineEndYinM",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.parkingLines[%].lineEndYinM",
                ],
            ),
            (
                self.Columns.PMDCAMERA_RIGHT_PARKINGLINES_LINECONFIDENCE,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRight.parkingLines[%].lineConfidence",
                    "CarPC.EM_Thread.PmdRight.parkingLines[%].lineConfidence",
                    "SIM VFB.PMSDINSTANCE_rsc.ParkingLines.parkingLines[%].lineConfidence",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.parkingLines[%].lineConfidence",
                ],
            ),
            (
                self.Columns.PMDWS_FRONT_TIMESTAMP,
                [
                    "SIM VFB.PMSDINSTANCE_fc.WheelStopperLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDWS_REAR_TIMESTAMP,
                [
                    "SIM VFB.PMSDINSTANCE_rc.WheelStopperLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDWS_LEFT_TIMESTAMP,
                [
                    "SIM VFB.PMSDINSTANCE_lsc.WheelStopperLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDWS_RIGHT_TIMESTAMP,
                [
                    "SIM VFB.PMSDINSTANCE_rsc.WheelStopperLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDWS_FRONT_LINECONFIDENCE,
                [
                    "SIM VFB.PMSDINSTANCE_fc.WheelStopperLines.parkingLines[%].lineConfidence",
                ],
            ),
            (
                self.Columns.PMDWS_REAR_LINECONFIDENCE,
                [
                    "SIM VFB.PMSDINSTANCE_rc.WheelStopperLines.parkingLines[%].lineConfidence",
                ],
            ),
            (
                self.Columns.PMDWS_LEFT_LINECONFIDENCE,
                [
                    "SIM VFB.PMSDINSTANCE_lsc.WheelStopperLines.parkingLines[%].lineConfidence",
                ],
            ),
            (
                self.Columns.PMDWS_RIGHT_LINECONFIDENCE,
                [
                    "SIM VFB.PMSDINSTANCE_rsc.WheelStopperLines.parkingLines[%].lineConfidence",
                ],
            ),
            (
                self.Columns.PMDWS_FRONT_NUMBEROFLINES,
                [
                    "SIM VFB.PMSDINSTANCE_fc.WheelStopperLines.numberOfLines",
                ],
            ),
            (
                self.Columns.PMDWS_REAR_NUMBEROFLINES,
                [
                    "SIM VFB.PMSDINSTANCE_rc.WheelStopperLines.numberOfLines",
                ],
            ),
            (
                self.Columns.PMDWS_LEFT_NUMBEROFLINES,
                [
                    "SIM VFB.PMSDINSTANCE_lsc.WheelStopperLines.numberOfLines",
                ],
            ),
            (
                self.Columns.PMDWS_RIGHT_NUMBEROFLINES,
                [
                    "SIM VFB.PMSDINSTANCE_rsc.WheelStopperLines.numberOfLines",
                ],
            ),
            (
                self.Columns.PMDWL_FRONT_TIMESTAMP,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDWL_REAR_TIMESTAMP,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDWL_LEFT_TIMESTAMP,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDWL_RIGHT_TIMESTAMP,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDWL_FRONT_LINECONFIDENCE,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDWL_REAR_LINECONFIDENCE,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDWL_LEFT_LINECONFIDENCE,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDWL_RIGHT_LINECONFIDENCE,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDWL_FRONT_NUMBEROFLINES,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDWL_REAR_NUMBEROFLINES,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDWL_LEFT_NUMBEROFLINES,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDWL_RIGHT_NUMBEROFLINES,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDSL_FRONT_TIMESTAMP,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDSL_REAR_TIMESTAMP,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDSL_LEFT_TIMESTAMP,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDSL_RIGHT_TIMESTAMP,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDSL_FRONT_LINECONFIDENCE,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDSL_REAR_LINECONFIDENCE,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDSL_LEFT_LINECONFIDENCE,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDSL_RIGHT_LINECONFIDENCE,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDSL_FRONT_NUMBEROFLINES,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDSL_REAR_NUMBEROFLINES,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDSL_LEFT_NUMBEROFLINES,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.PMDSL_RIGHT_NUMBEROFLINES,
                [
                    " ",  # TODO Signal names to be added
                ],
            ),
            (
                self.Columns.DPGS_TIMESTAMP,
                "Ethernet RT-Range.Hunter.Time.UTCTime",
                "Reference_RT3000_Ethernet.Hunter.Time.UTCTime",
            ),
            (
                self.Columns.DPGS_LONGITUDE,
                "Ethernet RT-Range.Hunter.Position.Longitude",
                "Reference_RT3000_Ethernet.Hunter.Position.Longitude",
            ),
            (
                self.Columns.DPGS_LATITUDE,
                "Ethernet RT-Range.Hunter.Position.Latitude",
                "Reference_RT3000_Ethernet.Hunter.Position.Latitude",
            ),
            (
                self.Columns.DPGS_HEADING,
                "Ethernet RT-Range.Hunter.Angles.Heading",
                "Reference_RT3000_Ethernet.Hunter.Position.Heading",
            ),
            (
                self.Columns.PCLDELIMITERS_SIGSTATUS,
                [
                    "pclOutput.sSigHeader.eSigStatus",
                    "CarPC.EM_Thread.CemPclOutput.signalHeader.eSigStatus",
                    "MTA_ADC5.CEM200_AUPDF_DATA.ParkingDelimiters.sSigHeader.eSigStatus",
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingDelimiters.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.NUMPCLDELIMITERS_TIMESTAMP,
                [
                    "pclOutput.sSigHeader.uiTimeStamp",
                    "CarPC.EM_Thread.CemPclOutput.signalHeader.uiTimeStamp",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.sSigHeader.uiTimeStamp",
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingDelimiters.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.NUMPCLDELIMITERS,
                [
                    "pclOutput.numberOfDelimiters",
                    "CarPC.EM_Thread.CemPclOutput.numPclDelimiters",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.numberOfDelimiters",
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingDelimiters.numberOfDelimiters",
                ],
            ),
            (
                self.Columns.FR1_x,
                [
                    "Vhcl.Fr1.x",
                ],
            ),
            (
                self.Columns.FR1_y,
                [
                    "Vhcl.Fr1.y",
                ],
            ),
            (
                self.Columns.SYNTHETIC_YAW,
                [
                    "Vhcl.Yaw",
                ],
            ),
            (
                self.Columns.POS_SIZE_M,
                [
                    "GT.envModelPort.parkingSpaceMarkings._%_.pos_m.actualSize",
                ],
            ),
            (
                self.Columns.EXISTENCE_PROB,
                [
                    "GT.envModelPort.parkingSpaceMarkings._%_.existenceProb_perc",
                ],
            ),
            (
                self.Columns.WIDTH_M,
                [
                    "GT.envModelPort.parkingSpaceMarkings._%_.width_m",
                ],
            ),
            (
                self.Columns.LINE_START_X,
                [
                    "GT.envModelPort.parkingSpaceMarkings._%_.pos_m.array._0_.x_dir",
                ],
            ),
            (
                self.Columns.LINE_END_X,
                [
                    "GT.envModelPort.parkingSpaceMarkings._%_.pos_m.array._1_.x_dir",
                ],
            ),
            (
                self.Columns.LINE_START_Y,
                [
                    "GT.envModelPort.parkingSpaceMarkings._%_.pos_m.array._0_.y_dir",
                ],
            ),
            (
                self.Columns.LINE_END_Y,
                [
                    "GT.envModelPort.parkingSpaceMarkings._%_.pos_m.array._1_.y_dir",
                ],
            ),
            (
                self.Columns.DELIMITERID,
                [
                    "pclOutput.delimiters._%_.delimiterId",
                    "CarPC.EM_Thread.CemPclOutput.pclDelimiters[%].delimiterId",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.delimiters[%].id",
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingDelimiters.delimiters[%].delimiterId",
                ],
            ),
            (
                self.Columns.DELIMITERTYPE,
                [
                    "pclOutput.delimiters._%_.delimiterType",
                    "CarPC.EM_Thread.CemPclOutput.pclDelimiters[%].delimiterType",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.delimiters[%].type",
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingDelimiters.delimiters[%].delimiterType",
                ],
            ),
            (
                self.Columns.P0_X,
                [
                    "pclOutput.delimiters._%_.startPointXPosition",
                    "CarPC.EM_Thread.CemPclOutput.pclDelimiters[%].startPointXPosition",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.delimiters[%].startPointXPosition",
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingDelimiters.delimiters[%].startPointXPosition",
                ],
            ),
            (
                self.Columns.P0_Y,
                [
                    "pclOutput.delimiters._%_.startPointYPosition",
                    "CarPC.EM_Thread.CemPclOutput.pclDelimiters[%].startPointYPosition",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.delimiters[%].startPointYPosition",
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingDelimiters.delimiters[%].startPointYPosition",
                ],
            ),
            (
                self.Columns.P1_X,
                [
                    "pclOutput.delimiters._%_.endPointXPosition",
                    "CarPC.EM_Thread.CemPclOutput.pclDelimiters[%].endPointXPosition",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.delimiters[%].endPointXPosition",
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingDelimiters.delimiters[%].endPointXPosition",
                ],
            ),
            (
                self.Columns.P1_Y,
                [
                    "pclOutput.delimiters._%_.endPointYPosition",
                    "CarPC.EM_Thread.CemPclOutput.pclDelimiters[%].endPointYPosition",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.delimiters[%].endPointYPosition",
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingDelimiters.delimiters[%].endPointYPosition",
                ],
            ),
            (
                self.Columns.CONFIDENCEPERCENT,
                [
                    "pclOutput.delimiters._%_.confidencePercent",
                    "CarPC.EM_Thread.CemPclOutput.pclDelimiters[%].confidencePercent",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.delimiters[%].confidence",
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingDelimiters.delimiters[%].confidencePercent",
                ],
            ),
            (
                self.Columns.FRONT_TIMESTAMP,
                "CarPC.EM_Thread.DynamicObjectsFront.timestamp",
            ),
            (
                self.Columns.FRONT_NUMOBJECTS,
                "CarPC.EM_Thread.DynamicObjectsFront.numObjects",
            ),
            (
                self.Columns.FRONT_OBJECTS_SIGSTATUS,
                "CarPC.EM_Thread.DynamicObjectsFront.signalState",
            ),
            (
                self.Columns.FRONT_OBJECTS_ID,
                "CarPC.EM_Thread.DynamicObjectsFront.objects[%].id",
            ),
            (
                self.Columns.FRONT_OBJECTS_CLASSTYPE,
                "CarPC.EM_Thread.DynamicObjectsFront.objects[%].classType",
            ),
            (
                self.Columns.FRONT_OBJECTS_CONFIDENCE,
                "CarPC.EM_Thread.DynamicObjectsFront.objects[%].confidence",
            ),
            (
                self.Columns.FRONT_OBJECTS_CENTERPOINTWORLD_X,
                "CarPC.EM_Thread.DynamicObjectsFront.objects[%].centerPointWorld.x",
            ),
            (
                self.Columns.FRONT_OBJECTS_CENTERPOINTWORLD_Y,
                "CarPC.EM_Thread.DynamicObjectsFront.objects[%].centerPointWorld.y",
            ),
            (
                self.Columns.FRONT_OBJECTS_CENTERPOINTWORLD_Z,
                "CarPC.EM_Thread.DynamicObjectsFront.objects[%].centerPointWorld.z",
            ),
            (
                self.Columns.FRONT_OBJECTS_PLANESIZEWORLD_X,
                "CarPC.EM_Thread.DynamicObjectsFront.objects[%].planeSizeWorld.x",
            ),
            (
                self.Columns.FRONT_OBJECTS_PLANESIZEWORLD_Y,
                "CarPC.EM_Thread.DynamicObjectsFront.objects[%].planeSizeWorld.y",
            ),
            (
                self.Columns.FRONT_OBJECTS_CUBOIDSIZEWORLD_X,
                "CarPC.EM_Thread.DynamicObjectsFront.objects[%].cuboidSizeWorld.x",
            ),
            (
                self.Columns.FRONT_OBJECTS_CUBOIDSIZEWORLD_Y,
                "CarPC.EM_Thread.DynamicObjectsFront.objects[%].cuboidSizeWorld.y",
            ),
            (
                self.Columns.FRONT_OBJECTS_CUBOIDSIZEWORLD_Z,
                "CarPC.EM_Thread.DynamicObjectsFront.objects[%].cuboidSizeWorld.z",
            ),
            (
                self.Columns.FRONT_OBJECTS_CUBOIDYAWWORLD,
                "CarPC.EM_Thread.DynamicObjectsFront.objects[%].cuboidYawWorld",
            ),
            (
                self.Columns.REAR_TIMESTAMP,
                "CarPC.EM_Thread.DynamicObjectsRear.timestamp",
            ),
            (
                self.Columns.REAR_NUMOBJECTS,
                "CarPC.EM_Thread.DynamicObjectsRear.numObjects",
            ),
            (
                self.Columns.REAR_OBJECTS_SIGSTATUS,
                "CarPC.EM_Thread.DynamicObjectsRear.signalState",
            ),
            (
                self.Columns.REAR_OBJECTS_ID,
                "CarPC.EM_Thread.DynamicObjectsRear.objects[%].id",
            ),
            (
                self.Columns.REAR_OBJECTS_CLASSTYPE,
                "CarPC.EM_Thread.DynamicObjectsRear.objects[%].classType",
            ),
            (
                self.Columns.REAR_OBJECTS_CONFIDENCE,
                "CarPC.EM_Thread.DynamicObjectsRear.objects[%].confidence",
            ),
            (
                self.Columns.REAR_OBJECTS_CENTERPOINTWORLD_X,
                "CarPC.EM_Thread.DynamicObjectsRear.objects[%].centerPointWorld.x",
            ),
            (
                self.Columns.REAR_OBJECTS_CENTERPOINTWORLD_Y,
                "CarPC.EM_Thread.DynamicObjectsRear.objects[%].centerPointWorld.y",
            ),
            (
                self.Columns.REAR_OBJECTS_CENTERPOINTWORLD_Z,
                "CarPC.EM_Thread.DynamicObjectsRear.objects[%].centerPointWorld.z",
            ),
            (
                self.Columns.REAR_OBJECTS_PLANESIZEWORLD_X,
                "CarPC.EM_Thread.DynamicObjectsRear.objects[%].planeSizeWorld.x",
            ),
            (
                self.Columns.REAR_OBJECTS_PLANESIZEWORLD_Y,
                "CarPC.EM_Thread.DynamicObjectsRear.objects[%].planeSizeWorld.y",
            ),
            (
                self.Columns.REAR_OBJECTS_CUBOIDSIZEWORLD_X,
                "CarPC.EM_Thread.DynamicObjectsRear.objects[%].cuboidSizeWorld.x",
            ),
            (
                self.Columns.REAR_OBJECTS_CUBOIDSIZEWORLD_Y,
                "CarPC.EM_Thread.DynamicObjectsRear.objects[%].cuboidSizeWorld.y",
            ),
            (
                self.Columns.REAR_OBJECTS_CUBOIDSIZEWORLD_Z,
                "CarPC.EM_Thread.DynamicObjectsRear.objects[%].cuboidSizeWorld.z",
            ),
            (
                self.Columns.REAR_OBJECTS_CUBOIDYAWWORLD,
                "CarPC.EM_Thread.DynamicObjectsRear.objects[%].cuboidYawWorld",
            ),
            (
                self.Columns.LEFT_TIMESTAMP,
                "CarPC.EM_Thread.DynamicObjectsLeft.timestamp",
            ),
            (
                self.Columns.LEFT_NUMOBJECTS,
                "CarPC.EM_Thread.DynamicObjectsLeft.numObjects",
            ),
            (
                self.Columns.LEFT_OBJECTS_SIGSTATUS,
                "CarPC.EM_Thread.DynamicObjectsLeft.signalState",
            ),
            (
                self.Columns.LEFT_OBJECTS_ID,
                "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].id",
            ),
            (
                self.Columns.LEFT_OBJECTS_CLASSTYPE,
                "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].classType",
            ),
            (
                self.Columns.LEFT_OBJECTS_CONFIDENCE,
                "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].confidence",
            ),
            (
                self.Columns.LEFT_OBJECTS_CENTERPOINTWORLD_X,
                "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].centerPointWorld.x",
            ),
            (
                self.Columns.LEFT_OBJECTS_CENTERPOINTWORLD_Y,
                "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].centerPointWorld.y",
            ),
            (
                self.Columns.LEFT_OBJECTS_CENTERPOINTWORLD_Z,
                "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].centerPointWorld.z",
            ),
            (
                self.Columns.LEFT_OBJECTS_PLANESIZEWORLD_X,
                "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].planeSizeWorld.x",
            ),
            (
                self.Columns.LEFT_OBJECTS_PLANESIZEWORLD_Y,
                "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].planeSizeWorld.y",
            ),
            (
                self.Columns.LEFT_OBJECTS_CUBOIDSIZEWORLD_X,
                "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].cuboidSizeWorld.x",
            ),
            (
                self.Columns.LEFT_OBJECTS_CUBOIDSIZEWORLD_Y,
                "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].cuboidSizeWorld.y",
            ),
            (
                self.Columns.LEFT_OBJECTS_CUBOIDSIZEWORLD_Z,
                "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].cuboidSizeWorld.z",
            ),
            (
                self.Columns.LEFT_OBJECTS_CUBOIDYAWWORLD,
                "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].cuboidYawWorld",
            ),
            (
                self.Columns.RIGHT_TIMESTAMP,
                "CarPC.EM_Thread.DynamicObjectsRight.timestamp",
            ),
            (
                self.Columns.RIGHT_NUMOBJECTS,
                "CarPC.EM_Thread.DynamicObjectsRight.numObjects",
            ),
            (
                self.Columns.RIGHT_OBJECTS_SIGSTATUS,
                "CarPC.EM_Thread.DynamicObjectsRight.signalState",
            ),
            (
                self.Columns.RIGHT_OBJECTS_ID,
                "CarPC.EM_Thread.DynamicObjectsRight.objects[%].id",
            ),
            (
                self.Columns.RIGHT_OBJECTS_CLASSTYPE,
                "CarPC.EM_Thread.DynamicObjectsRight.objects[%].classType",
            ),
            (
                self.Columns.RIGHT_OBJECTS_CONFIDENCE,
                "CarPC.EM_Thread.DynamicObjectsRight.objects[%].confidence",
            ),
            (
                self.Columns.RIGHT_OBJECTS_CENTERPOINTWORLD_X,
                "CarPC.EM_Thread.DynamicObjectsRight.objects[%].centerPointWorld.x",
            ),
            (
                self.Columns.RIGHT_OBJECTS_CENTERPOINTWORLD_Y,
                "CarPC.EM_Thread.DynamicObjectsRight.objects[%].centerPointWorld.y",
            ),
            (
                self.Columns.RIGHT_OBJECTS_CENTERPOINTWORLD_Z,
                "CarPC.EM_Thread.DynamicObjectsRight.objects[%].centerPointWorld.z",
            ),
            (
                self.Columns.RIGHT_OBJECTS_PLANESIZEWORLD_X,
                "CarPC.EM_Thread.DynamicObjectsRight.objects[%].planeSizeWorld.x",
            ),
            (
                self.Columns.RIGHT_OBJECTS_PLANESIZEWORLD_Y,
                "CarPC.EM_Thread.DynamicObjectsRight.objects[%].planeSizeWorld.y",
            ),
            (
                self.Columns.RIGHT_OBJECTS_CUBOIDSIZEWORLD_X,
                "CarPC.EM_Thread.DynamicObjectsRight.objects[%].cuboidSizeWorld.x",
            ),
            (
                self.Columns.RIGHT_OBJECTS_CUBOIDSIZEWORLD_Y,
                "CarPC.EM_Thread.DynamicObjectsRight.objects[%].cuboidSizeWorld.y",
            ),
            (
                self.Columns.RIGHT_OBJECTS_CUBOIDSIZEWORLD_Z,
                "CarPC.EM_Thread.DynamicObjectsRight.objects[%].cuboidSizeWorld.z",
            ),
            (
                self.Columns.RIGHT_OBJECTS_CUBOIDYAWWORLD,
                "CarPC.EM_Thread.DynamicObjectsRight.objects[%].cuboidYawWorld",
            ),
            (
                self.Columns.VEDODO_TIMESTAMP,
                [
                    "cem_outpus_sub.ego_motion_at_cem_time.vehicle_pose_est_at_cem_time.timestamp_us",
                    "CarPC.EM_Thread.OdoEstimationPortAtCem.timestamp_us",
                    "egoMotionAtCemOutput.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.odoEstimationAtCemTime",
                ],
            ),
            (
                self.Columns.VEDODO_SIGSTATUS,
                [
                    "egoMotionAtCemOutput.odoEstimationAtCemTime.motionStatus_nu",
                    "CarPC.EM_Thread.OdoEstimationPortAtCem.signalState_nu",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.X,
                [
                    "egoMotionAtCemOutput.odoEstimationAtCemTime.xPosition_m",
                    "cem_outpus_sub.ego_motion_at_cem_time.vehicle_pose_est_at_cem_time.x_position_m",
                    "CarPC.EM_Thread.OdoEstimationPortAtCem.xPosition_m",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.odoEstimationAtCemTime.xPosition_m",
                ],
            ),
            (
                self.Columns.Y,
                [
                    "egoMotionAtCemOutput.odoEstimationAtCemTime.yPosition_m",
                    "cem_outpus_sub.ego_motion_at_cem_time.vehicle_pose_est_at_cem_time.y_position_m",
                    "CarPC.EM_Thread.OdoEstimationPortAtCem.yPosition_m",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.odoEstimationAtCemTime.yPosition_m",
                ],
            ),
            (
                self.Columns.YAW,
                [
                    "egoMotionAtCemOutput.odoEstimationAtCemTime.yawAngle_rad",
                    "cem_outpus_sub.ego_motion_at_cem_time.vehicle_pose_est_at_cem_time.yaw_angle_rad",
                    "CarPC.EM_Thread.OdoEstimationPortAtCem.yawAngle_rad",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.odoEstimationAtCemTime.yawAngle_rad",
                ],
            ),
            (
                self.Columns.OBJECTS_ID,
                [
                    ".objects._%_.id",
                    ".objects[%].id",
                ],
            ),
            (self.Columns.OBJECTS_NUM, "CarPC.EM_Thread.CemInDynamicEnvironment.numOfAliveObjects"),
            (
                self.Columns.OBJECTS_OBJECTCLASS,
                [
                    ".objects._%_.objectClass",
                    ".objects[%].objectClass",
                ],
            ),
            (
                self.Columns.OBJECTS_CLASSCERTAINTY,
                [
                    ".objects._%_.classCertainty",
                    ".objects[%].classCertainty",
                ],
            ),
            (
                self.Columns.OBJECTS_DYNAMICPROPERTY,
                [
                    ".objects._%_.dynamicProperty",
                    ".objects[%].dynamicProperty",
                ],
            ),
            (
                self.Columns.OBJECTS_DYNPROPCERTAINTY,
                [
                    ".objects._%_.dynPropCertainty",
                    ".objects[%].dynPropCertainty",
                ],
            ),
            (
                self.Columns.OBJECTS_EXISTENCEPROB,
                [
                    ".objects._%_.existenceProb",
                    ".objects[%].existenceProb",
                ],
            ),
            (
                self.Columns.OBJECTS_ORIENTATION,
                [
                    ".objects._%_.orientation",
                    ".objects[%].orientation",
                ],
            ),
            (
                self.Columns.OBJECTS_ORIENTATIONSTANDARDDEVIATION,
                [
                    ".objects._%_.orientationStandardDeviation",
                    ".objects[%].orientationStandardDeviation",
                ],
            ),
            (
                self.Columns.OBJECTS_VELOCITY_F_XR,
                [
                    ".objects._%_.velocity.x",
                    ".objects[%].velocity.f_Xr",
                ],
            ),
            (
                self.Columns.OBJECTS_VELOCITY_F_YA,
                [
                    ".objects._%_.velocity.y",
                    ".objects[%].velocity.f_Ya",
                ],
            ),
            (
                self.Columns.OBJECTS_VELOCITYSTANDARDDEVIATION_F_XR,
                [
                    ".objects._%_.velocityStandardDeviation.x",
                    ".objects[%].velocityStandardDeviation.f_Xr",
                ],
            ),
            (
                self.Columns.OBJECTS_VELOCITYSTANDARDDEVIATION_F_YA,
                [
                    ".objects._%_.velocityStandardDeviation.y",
                    ".objects[%].velocityStandardDeviation.f_Ya",
                ],
            ),
            (
                self.Columns.OBJECTS_YAWRATE,
                [
                    ".objects._%_.yawRate",
                    ".objects[%].yawRate",
                ],
            ),
            (
                self.Columns.OBJECTS_YAWRATESTANDARDDEVIATION,
                [
                    ".objects._%_.yawRateStandardDeviation",
                    ".objects[%].yawRateStandardDeviation",
                ],
            ),
            (
                self.Columns.OBJECTS_CENTER_X,
                [
                    ".objects._%_.shape.referencePoint.x",
                    ".objects[%].shape.referencePoint.f_Xr",
                ],
            ),
            (
                self.Columns.OBJECTS_CENTER_Y,
                [
                    ".objects._%_.shape.referencePoint.y",
                    ".objects[%].shape.referencePoint.f_Ya",
                ],
            ),
            (
                self.Columns.OBJECTS_LIFETIME,
                [
                    ".objects._%_.lifetime",
                    ".objects[%].lifetime",
                ],
            ),
            (
                self.Columns.OBJECTS_CONTAINEDINLASTSENSORUPDATE,
                [
                    ".objects._%_.containedInLastSensorUpdate",
                    ".objects[%].containedInLastSensorUpdate",
                ],
            ),
            (
                self.Columns.OBJECTS_STATE,
                [
                    ".objects._%_.state",
                    ".objects[%].state",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_0__POSITION_F_XR,
                [
                    ".objects._%_.shape.points._0_.position.x",
                    ".objects[%].shape.points[0].position.f_Xr",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_1__POSITION_F_XR,
                [
                    ".objects._%_.shape.points._1_.position.x",
                    ".objects[%].shape.points[1].position.f_Xr",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_2__POSITION_F_XR,
                [
                    ".objects._%_.shape.points._2_.position.x",
                    ".objects[%].shape.points[2].position.f_Xr",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_3__POSITION_F_XR,
                [
                    ".objects._%_.shape.points._3_.position.x",
                    ".objects[%].shape.points[3].position.f_Xr",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_0__POSITION_F_YA,
                [
                    ".objects._%_.shape.points._0_.position.y",
                    ".objects[%].shape.points[0].position.f_Ya",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_1__POSITION_F_YA,
                [
                    ".objects._%_.shape.points._1_.position.y",
                    ".objects[%].shape.points[1].position.f_Ya",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_2__POSITION_F_YA,
                [
                    ".objects._%_.shape.points._2_.position.y",
                    ".objects[%].shape.points[2].position.f_Ya",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_3__POSITION_F_YA,
                [
                    ".objects._%_.shape.points._3_.position.y",
                    ".objects[%].shape.points[3].position.f_Ya",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_0__VARIANCEX,
                [
                    ".objects._%_.shape.points._0_.varianceX",
                    ".objects[%].shape.points[0].varianceX",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_1__VARIANCEX,
                [
                    ".objects._%_.shape.points._1_.varianceX",
                    ".objects[%].shape.points[1].varianceX",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_2__VARIANCEX,
                [
                    ".objects._%_.shape.points._2_.varianceX",
                    ".objects[%].shape.points[2].varianceX",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_3__VARIANCEX,
                [
                    ".objects._%_.shape.points._3_.varianceX",
                    ".objects[%].shape.points[3].varianceX",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_0__VARIANCEY,
                [
                    ".objects._%_.shape.points._0_.varianceY",
                    ".objects[%].shape.points[0].varianceY",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_1__VARIANCEY,
                [
                    ".objects._%_.shape.points._1_.varianceY",
                    ".objects[%].shape.points[1].varianceY",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_2__VARIANCEY,
                [
                    ".objects._%_.shape.points._2_.varianceY",
                    ".objects[%].shape.points[2].varianceY",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_3__VARIANCEY,
                [
                    ".objects._%_.shape.points._3_.varianceY",
                    ".objects[%].shape.points[3].varianceY",
                ],
            ),
            (
                self.Columns.EM_EGOMOTIONPORT_ACCEL_MPS2,
                [
                    "ADC5xx_Device.EM_DATA.EmEgoMotionPort.accel_mps2",
                    "CarPC.EM_Thread.EgoMotionPort.accel_mps2",
                    "egoMotionAtCemOutput.odoEstimationAtCemTime.longiAcceleration_mps2",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.odoEstimationAtCemTime.longiAcceleration_mps2",
                ],
            ),
            (
                self.Columns.EM_EGOMOTIONPORT_DRIVEN_DIST,
                [
                    "ADC5xx_Device.EM_DATA.EmEgoMotionPort.drivenDistance_m",
                    "CarPC.EM_Thread.EgoMotionPort.drivenDistance_m",
                    "egoMotionAtCemOutput.odoEstimationAtCemTime.drivenDistance_m",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.odoEstimationAtCemTime.drivenDistance_m",
                ],
            ),
            (
                self.Columns.EM_EGOMOTIONPORT_FRONT_WANGLE_RAD,
                [
                    "ADC5xx_Device.EM_DATA.EmEgoMotionPort.frontWheelAngle_rad",
                    "egoMotionAtCemOutput.odoEstimationAtCemTime.steerAngFrontAxle_rad",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.odoEstimationAtCemTime.steerAngFrontAxle_rad",
                ],
            ),
            (
                self.Columns.EM_EGOMOTIONPORT_MOTION_STATE,
                [
                    "ADC5xx_Device.EM_DATA.EmEgoMotionPort.motionState_nu",
                    "CarPC.EM_Thread.EgoMotionPort.motionState_nu",
                    "egoMotionAtCemOutput.odoEstimationAtCemTime.motionStatus_nu",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.odoEstimationAtCemTime.motionStatus_nu",
                ],
            ),
            (
                self.Columns.EM_EGOMOTIONPORT_PITCH_RAD,
                [
                    "ADC5xx_Device.EM_DATA.EmEgoMotionPort.pitch_rad",
                    "CarPC.EM_Thread.EgoMotionPort.pitch_rad",
                    "egoMotionAtCemOutput.odoEstimationAtCemTime.pitchAngle_rad",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.odoEstimationAtCemTime.pitchAngle_rad",
                ],
            ),
            (
                self.Columns.EM_EGOMOTIONPORT_REAR_WANGLE_RAD,
                [
                    "ADC5xx_Device.EM_DATA.EmEgoMotionPort.rearWheelAngle_rad",
                    "CarPC.EM_Thread.EgoMotionPort.rearWheelAngle_rad",
                    "egoMotionAtCemOutput.odoEstimationAtCemTime.steerAngRearAxle_rad",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.odoEstimationAtCemTime.steerAngRearAxle_rad",
                ],
            ),
            (
                self.Columns.EM_EGOMOTIONPORT_ROLL_RAD,
                [
                    "ADC5xx_Device.EM_DATA.EmEgoMotionPort.roll_rad",
                    "CarPC.EM_Thread.EgoMotionPort.roll_rad",
                    "egoMotionAtCemOutput.odoEstimationAtCemTime.rollAngle_rad",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.odoEstimationAtCemTime.rollAngle_rad",
                ],
            ),
            (
                self.Columns.EM_EGOMOTIONPORT_SIGSTATUS,
                [
                    "ADC5xx_Device.EM_DATA.EmEgoMotionPort.sSigHeader.eSigStatus",
                    "egoMotionAtCemOutput.sSigHeader.eSigStatus",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.EM_EGOMOTIONPORT_CYCLE_COUNTER,
                "ADC5xx_Device.EM_DATA.EmEgoMotionPort.sSigHeader.uiCycleCounter",
                "CarPC.EM_Thread.EgoMotionPort.signalState_nu",
                "egoMotionAtCemOutput.sSigHeader.uiCycleCounter",
                "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.sSigHeader.uiCycleCounter",
            ),
            (
                self.Columns.EM_EGOMOTIONPORT_MEASURMENT_COUNTER,
                "ADC5xx_Device.EM_DATA.EmEgoMotionPort.sSigHeader.uiMeasurementCounter",
                "egoMotionAtCemOutput.sSigHeader.uiMeasurementCounter",
                "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.sSigHeader.uiMeasurementCounter",
            ),
            (
                self.Columns.EM_EGOMOTIONPORT_TIMESTAMP,
                [
                    "ADC5xx_Device.EM_DATA.EmEgoMotionPort.sSigHeader.uiTimeStamp",
                    "egoMotionAtCemOutput.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.EM_EGOMOTIONPORT_VERSION_NUMBER,
                "ADC5xx_Device.EM_DATA.EmEgoMotionPort.uiVersionNumber",
                "egoMotionAtCemOutput.uiVersionNumber",
                "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.uiVersionNumber",
            ),
            (
                self.Columns.EM_EGOMOTIONPORT_VEL_MPS,
                [
                    "ADC5xx_Device.EM_DATA.EmEgoMotionPort.vel_mps",
                    "egoMotionAtCemOutput.odoEstimationAtCemTime.longiVelocity_mps",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.odoEstimationAtCemTime.longiVelocity_mps",
                ],
            ),
            (
                self.Columns.EM_EGOMOTIONPORT_YAW_RAD,
                [
                    "ADC5xx_Device.EM_DATA.EmEgoMotionPort.yawRate_radps",
                    "egoMotionAtCemOutput.odoEstimationAtCemTime.yawRate_radps",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.odoEstimationAtCemTime.yawRate_radps",
                ],
            ),
            (
                self.Columns.SGF_NUMBER_OF_POLYGONS,
                [
                    "CarPC.EM_Thread.SefOutputAgp.u_Used_Elements",
                    "ADC5xx_Device.CEM_EM_DATA.SGF_SgfOutput.staticObjectsOutput.numberOfObjects",
                ],
            ),
            (
                self.Columns.SGF_NUMBER_OF_VERTICES,
                [
                    "CarPC.EM_Thread.SefOutputAgpVertices.u_Used_Vertices",
                    "ADC5xx_Device.CEM_EM_DATA.SGF_SgfOutput.staticObjectVerticesOutput.numberOfVertices",
                ],
            ),
            (
                self.Columns.SGF_VERTICES,
                [
                    "CarPC.EM_Thread.SefOutputAgp.a_Element[%].u_NumVertices",
                    "ADC5xx_Device.CEM_EM_DATA.SGF_SgfOutput.staticObjectsOutput.objects[%].usedVertices",
                ],
            ),
            (
                self.Columns.SGF_VERTEX_X,
                [
                    "CarPC.EM_Thread.SefOutputAgpVertices.a_Polygon_Vertex[%].point3D.fXr",
                    "ADC5xx_Device.CEM_EM_DATA.SGF_SgfOutput.staticObjectVerticesOutput.vertices[%].x",
                ],
            ),
            (
                self.Columns.SGF_VERTEX_Y,
                [
                    "CarPC.EM_Thread.SefOutputAgpVertices.a_Polygon_Vertex[%].point3D.fYa",
                    "ADC5xx_Device.CEM_EM_DATA.SGF_SgfOutput.staticObjectVerticesOutput.vertices[%].y",
                ],
            ),
            (
                self.Columns.SGF_OBJECT_ID,
                [
                    "CarPC.EM_Thread.SefOutputAgp.a_Element[%].u_id",
                    "ADC5xx_Device.CEM_EM_DATA.SGF_SgfOutput.staticObjectsOutput.objects[%].obstacleId",
                ],
            ),
            (
                self.Columns.SGF_OBJECT_SEMANTIC_CLASS,
                [
                    "CarPC.EM_Thread.SefOutputAgp.a_Element[%].e_ElementClassification",
                    "ADC5xx_Device.CEM_EM_DATA.SGF_SgfOutput.staticObjectsOutput.objects[%].semanticType",
                ],
            ),
            (
                self.Columns.SGF_OBJECT_NUM_VERTICES,
                [
                    "CarPC.EM_Thread.SefOutputAgp.a_Element[%].u_NumVertices",
                    "ADC5xx_Device.CEM_EM_DATA.SGF_SgfOutput.staticObjectsOutput.objects[%].usedVertices",
                ],
            ),
            (
                self.Columns.SGF_OBJECT_VERTEX_START_INDEX,
                [
                    "CarPC.EM_Thread.SefOutputAgp.a_Element[%].u_VertexStartIndex",
                    "ADC5xx_Device.CEM_EM_DATA.SGF_SgfOutput.staticObjectsOutput.objects[%].vertexStartIndex",
                ],
            ),
            (
                self.Columns.SGF_OBJECT_WHEEL_TRAVERSABLE_CONFIDENCE,
                [
                    "CarPC.EM_Thread.SefOutputAgp.a_Element[%].heightConfidences.wheelTraversable",
                    "ADC5xx_Device.CEM_EM_DATA.SGF_SgfOutput.staticObjectsOutput.objects[%].heightConfidences.wheelTraversable",
                ],
            ),
            (
                self.Columns.SGF_OBJECT_BODY_TRAVERSABLE_CONFIDENCE,
                [
                    "CarPC.EM_Thread.SefOutputAgp.a_Element[%].heightConfidences.bodyTraversable",
                    "ADC5xx_Device.CEM_EM_DATA.SGF_SgfOutput.staticObjectsOutput.objects[%].heightConfidences.bodyTraversable",
                ],
            ),
            (
                self.Columns.SGF_OBJECT_HIGH_CONFIDENCE,
                [
                    "CarPC.EM_Thread.SefOutputAgp.a_Element[%].heightConfidences.high",
                    "ADC5xx_Device.CEM_EM_DATA.SGF_SgfOutput.staticObjectsOutput.objects[%].heightConfidences.high",
                ],
            ),
            (
                self.Columns.SGF_OBJECT_HANGING_CONFIDENCE,
                [
                    "CarPC.EM_Thread.SefOutputAgp.a_Element[%].heightConfidences.hanging",
                    "ADC5xx_Device.CEM_EM_DATA.SGF_SgfOutput.staticObjectsOutput.objects[%].heightConfidences.hanging",
                ],
            ),
            (
                self.Columns.SGF_TIMESTAMP,
                [
                    "CarPC.EM_Thread.SefOutputAgp.timestamp_us",
                    "ADC5xx_Device.CEM_EM_DATA.SGF_SgfOutput.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.SYNTHETIC_DATA,
                "GT.envModelPort.sSigHeader.uiTimeStamp",
            ),
            (
                self.Columns.SVC_POINT_LIST_SIGNAL_STATE,
                "ADC5xx_Device.CEM_EM_DATA.SVC_PointListOutput.sSigHeader.eSigStatus",
                "MTA_ADC5.CEM200_SVC_DATA.m_pSvcPointList.sSigHeader.eSigStatus",
            ),
            (
                self.Columns.SVC_POINT_LIST_TIMESTAMP,
                "ADC5xx_Device.CEM_EM_DATA.SVC_PointListOutput.sSigHeader.uiTimeStamp",
                "MTA_ADC5.CEM200_SVC_DATA.m_pSvcPointList.sSigHeader.uiTimeStamp",
            ),
            (
                self.Columns.SVC_POINT_LIST_OUTPUT,
                "ADC5xx_Device.CEM_EM_DATA.SVC_PointListOutput.sfmPointList[%].numberOfPoints",
                "MTA_ADC5.CEM200_SVC_DATA.m_pSvcPointList.sfmPointList[%].numberOfPoints",
            ),
            (
                self.Columns.SVC_POLYLINE_SIGNAL_STATE,
                "ADC5xx_Device.CEM_EM_DATA.SVC_PolylineList.sSigHeader.eSigStatus",
                "MTA_ADC5.CEM200_SVC_DATA.m_pSvcPolylineList.sSigHeader.eSigStatus",
            ),
            (
                self.Columns.SVC_POLYLINE_TIMESTAMP,
                "ADC5xx_Device.CEM_EM_DATA.SVC_PolylineList.sSigHeader.uiTimeStamp",
                "MTA_ADC5.CEM200_SVC_DATA.m_pSvcPolylineList.sSigHeader.uiTimeStamp",
            ),
            (
                self.Columns.SVC_POLYLINE_OUTPUT,
                "ADC5xx_Device.CEM_EM_DATA.SVC_PolylineList.sppPolylineList[%].numberOfPolylines",
                "MTA_ADC5.CEM200_SVC_DATA.m_pSvcPolylineList.sppPolylineList[].numberOfPolylines",
            ),
            (
                # ToDo: confirm signals name
                self.Columns.TP_OBJECT_LIST_SIGNAL_STATE,
                "ADC5xx_Device.CEM_EM_DATA.AUPDF_DynamicObjects.sSigHeader.eSigStatus",
            ),
            (
                self.Columns.TP_OBJECT_LIST_TIMESTAMP,
                "ADC5xx_Device.CEM_EM_DATA.AUPDF_DynamicObjects.sSigHeader.uiTimeStamp",
            ),
            (
                self.Columns.TP_OBJECT_LIST_OUTPUT,
                "ADC5xx_Device.CEM_EM_DATA.AUPDF_DynamicObjects.numberOfObjects",
            ),
            (
                self.Columns.USS_SIGNAL_STATE,
                "ADC5xx_Device.CEM_EM_DATA.USS_UssOutput.sSigHeader.eSigStatus",
                "MTA_ADC5.CEM200_USS_DATA.m_UssOutput.sSigHeader.eSigStatus",
            ),
            (
                self.Columns.USS_TIMESTAMP,
                "ADC5xx_Device.CEM_EM_DATA.USS_UssOutput.sSigHeader.uiTimeStamp",
                "MTA_ADC5.CEM200_USS_DATA.m_UssOutput.sSigHeader.uiTimeStamp",
            ),
            (
                self.Columns.USS_OUTPUT,
                # "ADC5xx_Device.CEM_EM_DATA.USS_UssOutput.ussObjectList.numberOfObjects",
                "ADC5xx_Device.CEM_EM_DATA.USS_UssOutput.ussPointList.numberOfPoints",
                "MTA_ADC5.CEM200_USS_DATA.m_UssOutput.ussPointList.numberOfPoints",
            ),
        ]


class EntrySignalsss(SignalDefinition):
    """Entry signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIMESTAMP = "TimeStamp"
        EGOMOTIONPORT = "EgoMotionPort"
        PSMDEBUGPORT = "PSMDebugPort"
        TargetPose0 = "TargetPose0"
        TargetPose1 = "TargetPose1"
        TargetPose2 = "TargetPose2"
        TargetPose3 = "TargetPose3"
        TargetPose4 = "TargetPose4"
        TargetPose5 = "TargetPose5"
        TargetPose6 = "TargetPose6"
        TargetPose7 = "TargetPose7"
        TargetPose = "TargetPose{}"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["MTS.Package", "CarPC.EM_Thread"]

        self._properties = {
            self.Columns.TIMESTAMP: ".TimeStamp",
            self.Columns.EGOMOTIONPORT: ".EgoMotionPort.vel_mps",
            self.Columns.PSMDEBUGPORT: ".PSMDebugPort.stateVarPPC_nu",
            self.Columns.TargetPose0: ".TargetPosesPort.targetPoses[0].reachableStatus",
            self.Columns.TargetPose1: ".TargetPosesPort.targetPoses[1].reachableStatus",
            self.Columns.TargetPose2: ".TargetPosesPort.targetPoses[2].reachableStatus",
            self.Columns.TargetPose3: ".TargetPosesPort.targetPoses[3].reachableStatus",
            self.Columns.TargetPose4: ".TargetPosesPort.targetPoses[4].reachableStatus",
            self.Columns.TargetPose5: ".TargetPosesPort.targetPoses[5].reachableStatus",
            self.Columns.TargetPose6: ".TargetPosesPort.targetPoses[6].reachableStatus",
            self.Columns.TargetPose7: ".TargetPosesPort.targetPoses[7].reachableStatus",
        }


class MfSignals(SignalDefinition):
    """MF signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        PARKINGFAILREASON = "ParkingFaileReason"
        PARKSMCORESTATUS = "ParkSmCoreStatus"
        APODOCMREFXPOSM = "ApOdoCmRefXPosM"
        APODOCMREFYPOSM = "ApOdoCmRefYPosM"
        APODOCMREFYAWANGRAD = "ApOdoCmRefYawAngRad"
        APODOESTIMYAWANGRAD = "ApOdoEstimYawAngRad"
        APODOESTIMXPOSM = "ApOdoEstimXPosM"
        APODOESTIMYPOSM = "ApOdoEstimYPosM"
        APODOESTIMYAWRATERADPS = "ApOdoEstimYawRateRadps"
        LONGIVELOCITY = "longiVelocity"
        STEERANGFRONTAXLE_RAD = "steerAngFrontAxle_rad"
        MOTIONSTATUS_NU = "motionStatus_nu"
        STEERINGWHEELANGLE_RAD = "steeringWheelAngle_rad"
        STEERINGWHEELANGLEVELOCITY_RADPS = "steeringWheelAngleVelocity_radps"
        LATERALACCELERATION_MPS2 = "lateralAcceleration_mps2"
        LONGITUDINALACCELERATION_MPS2 = "longitudinalAcceleration_mps2"
        EBAACTIVE = "EbaActive"
        YAWRATE_RADPS = "yawRate_radps"
        PPCPARKINGMODE = "ppcParkingMode"
        PITCHANGLE_RAD = "pitchAngle_rad"
        HEADUNITVISU_SCREEN_NU = "headUnitVisu_screen_nu"
        APSTATE = "ApState"
        MPSTATE = "MpState"
        RASTATE = "RaState"
        GPSTATE = "GpState"
        RMSTATE = "RmState"
        ORIENTATIONERROR = "OrientationError"
        LATERALERROR = "LateralError"
        CORESTOPREASON = "CoreStopReason"
        APDISTTOSTOPREQINTEREXTRAPOLTRAJ = "ApDistToStopReqInterExtrapolTraj"
        APTRAJCTRLACTIVE = "ApTrajCtrlActive"
        APDRIVINGMODEREQ = "ApDrivingModeReq"
        APUSECASE = "ApUsecase"
        NBCREVSTEPS = "NbCrevSteps"
        ACTNBSTROKESGREATERMAXNBSTROKES = "ActNbStrokesGreaterMaxNbStrokes"
        LATDIFFOPTIMALTP_FINALEGOPOSE = "latDiffOptimalTP_FinalEgoPose"
        LONGDIFFOPTIMALTP_FINALEGOPOSE = "longDiffOptimalTP_FinalEgoPose"
        YAWDIFFOPTIMALTP_FINALEGOPOSE = "yawDiffOptimalTP_FinalEgoPose"
        STEERANGREQ_RAD = "steerAngReq_rad"
        USERACTIONHEADUNIT_NU = "userActionHeadUnit_nu"
        ALLOWEDMANEUVERINGSPACEEXCEED_BOOL = "allowedManeuveringSpaceExceed_bool"
        HEADUNITVISU_MESSAGE_NU = "headUnitVisu_message_nu"
        T_SIM_MAX_S = "t_sim_max_s"
        N_STROKES_MAX_NU = "n_strokes_max_nu"
        MAXCYCLETIMEOFAUPSTEP_MS = "maxCycleTimeOfAUPStep_ms"
        REACHEDSTATUS = "ReachedStatus"
        LATDISTTOTARGET = "LatDistToTarget"
        LONGDISTTOTARGET = "LongDistToTarget"
        YAWDIFFTOTARGET = "YawDiffToTarget"
        LATMAXDEVIATION = "LatMaxDeviation"
        LONGMAXDEVIATION = "LongMaxDeviation"
        YAWMAXDEVIATION = "YawMaxDeviation"
        NUMVALIDPARKINGBOXES_NU = "numValidParkingBoxes_nu"
        PARKINGBOX0 = "parkingBox0"
        NUMBEROFSTROKES = "NumberOfStrokes"
        TRAJCTRLREQUESTPORT = "trajCtrlRequestPort"
        WHEELANGLEACCELERATION = "wheelAngleAcceleration"
        LONGDIFFOPTIMALTP_TARGETPOSE = "longDiffOptimalTP_TargetPose"
        LATDIFFOPTIMALTP_TARGETPOSE = "latDiffOptimalTP_TargetPose"
        YAWDIFFOPTIMALTP_TARGETPOSE = "yawDiffOptimalTP_TargetPose"
        STATEVARPPC = "stateVarPPC"
        STATEVARESM = "stateVarESM"
        STATEVARVSM = "stateVarVSM"
        STATEVARDM = "stateVarDM"
        STATEVARRDM = "stateVarRDM"
        CAR_OUTSIDE_PB = "car_outside_PB"
        STATICSTRUCTCOLIDESTARGET_POSE_0 = "staticStructColidesTarget_Pose_0"
        STATICSTRUCTCOLIDESTARGET_POSE_1 = "staticStructColidesTarget_Pose_1"
        STATICSTRUCTCOLIDESTARGET_POSE_2 = "staticStructColidesTarget_Pose_2"
        STATICSTRUCTCOLIDESTARGET_POSE_3 = "staticStructColidesTarget_Pose_3"
        STATICSTRUCTCOLIDESTARGET_POSE_4 = "staticStructColidesTarget_Pose_4"
        STATICSTRUCTCOLIDESTARGET_POSE_5 = "staticStructColidesTarget_Pose_5"
        STATICSTRUCTCOLIDESTARGET_POSE_6 = "staticStructColidesTarget_Pose_6"
        STATICSTRUCTCOLIDESTARGET_POSE_7 = "staticStructColidesTarget_Pose_7"
        LSCADISABLED = "lscaDisabled"

        CAR_VX = "Car_vx"
        CARYAWRATE = "CarYawRate"
        LATSLOPE = "LatSlope"
        COLLISIONCOUNT = "CollisionCount"
        LONGSLOPE = "LongSlope"
        TIME = "time"
        CAR_AX = "Car_ax"
        CAR_AY = "Car_ay"
        VHCL_V = "Vhcl_v"
        VHCLYAWRATE = "VhclYawRate"
        VEHICLEROAD = "VehicleRoad"
        PARKINGLANEMARKING = "ParkingLaneMarking"
        ODOROAD = "OdoRoad"
        LSCAREQUESTMODE = "lscaRequestMode"
        BRAKEMODESTATE = "brakeModeState"
        CAR_V = "Car_v"
        OPTIMALTARGETPOSE_x = "OptimalTargetPose_x_m"
        OPTIMALTARGETPOSE_y = "OptimalTargetPose_y_m"
        OPTIMALTARGETPOSE_yaw = "OptimalTargetPose_yaw_rad"
        CMTARGETPOSE_x = "CMTargetPose_x_m"
        CMTARGETPOSE_y = "CMTargetPose_y_m"
        CMTARGETPOSE_yaw = "CMTargetPose_yaw_rad"
        FURTHESTOBJECTsROAD = "furthestObject_sRoad"
        FURTHESTOBJECTYAW = "furthestObject_yaw"
        sceneInterpretationActive_nu = "sceneInterpretationActive_nu"
        CARYAWRATE = "CarYawRate"
        PARKINGBOX0_SLOTCOORDINATES0_X = "parkingBox0_slotCoordinates0_x"
        PARKINGBOX0_SLOTCOORDINATES0_Y = "parkingBox0_slotCoordinates0_y"
        PARKINGBOX0_SLOTCOORDINATES1_X = "parkingBox0_slotCoordinates1_x"
        PARKINGBOX0_SLOTCOORDINATES1_Y = "parkingBox0_slotCoordinates1_y"
        PARKINGBOX0_SLOTCOORDINATES2_X = "parkingBox0_slotCoordinates2_x"
        PARKINGBOX0_SLOTCOORDINATES2_Y = "parkingBox0_slotCoordinates2_y"
        PARKINGBOX0_SLOTCOORDINATES3_X = "parkingBox0_slotCoordinates3_x"
        PARKINGBOX0_SLOTCOORDINATES3_Y = "parkingBox0_slotCoordinates3_y"
        PARKINGBOX1_SLOTCOORDINATES0_X = "parkingBox1_slotCoordinates0_x"
        PARKINGBOX1_SLOTCOORDINATES0_Y = "parkingBox1_slotCoordinates0_y"
        PARKINGBOX1_SLOTCOORDINATES1_X = "parkingBox1_slotCoordinates1_x"
        PARKINGBOX1_SLOTCOORDINATES1_Y = "parkingBox1_slotCoordinates1_y"
        PARKINGBOX1_SLOTCOORDINATES2_X = "parkingBox1_slotCoordinates2_x"
        PARKINGBOX1_SLOTCOORDINATES2_Y = "parkingBox1_slotCoordinates2_y"
        PARKINGBOX1_SLOTCOORDINATES3_X = "parkingBox1_slotCoordinates3_x"
        PARKINGBOX1_SLOTCOORDINATES3_Y = "parkingBox1_slotCoordinates3_y"

        TRAJVALID_NU = "trajValid_nu"
        NEWSEGMENTSTARTED_NU = "newSegmentStarted_nu"
        ANYPATHFOUND = "anyPathFound"
        NUMVALIDPOSES_NU = "numValidPoses_nu"
        NUMVALIDSEGMENTS = "numValidSegments"
        PLANNEDPATHXPOS_7 = "plannedPathXPos_m_7"
        PLANNEDPATHXPOS_8 = "plannedPathXPos_m_8"
        PLANNEDPATHXPOS_999 = "plannedPathXPos_m_999"
        PLANNEDPATHYPOS_7 = "plannedPathYPos_m_7"
        PLANNEDPATHYPOS_8 = "plannedPathYPos_m_8"
        RESETCOUNTER = "resetCounter"
        RESETCOUNTER_NU = "resetCounter_nu"
        PARKINGSCENARIO0 = "parkingScenario_nu0"
        PARKINGSCENARIO1 = "parkingScenario_nu1"
        PARKINGSCENARIO2 = "parkingScenario_nu2"
        PARKINGSCENARIO3 = "parkingScenario_nu3"
        PARKINGSCENARIO4 = "parkingScenario_nu4"
        PARKINGSCENARIO5 = "parkingScenario_nu5"
        PARKINGSCENARIO6 = "parkingScenario_nu6"
        PARKINGSCENARIO7 = "parkingScenario_nu7"
        NUMVALIDPOSES = "numValidPoses"
        NUMVALIDCTRLPOINTS_NU = "numValidCtrlPoints_nu"
        RELATEDPARKINGBOXID_0 = "relatedParkingBoxID_0"
        RELATEDPARKINGBOXID_1 = "relatedParkingBoxID_1"
        RELATEDPARKINGBOXID_2 = "relatedParkingBoxID_2"
        RELATEDPARKINGBOXID_3 = "relatedParkingBoxID_3"
        RELATEDPARKINGBOXID_4 = "relatedParkingBoxID_4"
        RELATEDPARKINGBOXID_5 = "relatedParkingBoxID_5"
        RELATEDPARKINGBOXID_6 = "relatedParkingBoxID_6"
        RELATEDPARKINGBOXID_7 = "relatedParkingBoxID_7"
        PARKINGBOX0 = "parkingBox0"
        PARKINGBOX1 = "parkingBox1"
        PARKINGBOX2 = "parkingBox2"
        PARKINGBOX3 = "parkingBox3"
        PARKINGBOX4 = "parkingBox4"
        PARKINGBOX5 = "parkingBox5"
        PARKINGBOX6 = "parkingBox6"
        PARKINGBOX7 = "parkingBox7"
        TRAJTYPE_NU = "trajType_nu"
        APCHOSENTARGETPOSEID = "apChosenTargetPoseID_nu"
        TARGETPOSESTYPE0 = "poseType0"
        TARGETPOSESTYPE1 = "poseType1"
        TARGETPOSESTYPE2 = "poseType2"
        TARGETPOSESTYPE3 = "poseType3"
        TARGETPOSESTYPE4 = "poseType4"
        TARGETPOSESTYPE5 = "poseType5"
        TARGETPOSESTYPE6 = "poseType6"
        TARGETPOSESTYPE7 = "poseType7"
        TARGETPOSEID0 = "poseId0"
        TARGETPOSEID1 = "poseId1"
        TARGETPOSEID2 = "poseId2"
        TARGETPOSEID3 = "poseId3"
        TARGETPOSEID4 = "poseId4"
        TARGETPOSEID5 = "poseId5"
        TARGETPOSEID6 = "poseId6"
        TARGETPOSEID7 = "poseId7"
        TARGETPOSEREACHABLE0 = "targetPoseRechableStatus0"
        TARGETPOSEREACHABLE1 = "targetPoseRechableStatus1"
        TARGETPOSEREACHABLE2 = "targetPoseRechableStatus2"
        TARGETPOSEREACHABLE3 = "targetPoseRechableStatus3"
        TARGETPOSEREACHABLE4 = "targetPoseRechableStatus4"
        TARGETPOSEREACHABLE5 = "targetPoseRechableStatus5"
        TARGETPOSEREACHABLE6 = "targetPoseRechableStatus6"
        TARGETPOSEREACHABLE7 = "targetPoseRechableStatus7"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]

        self._properties = {
            self.Columns.APODOCMREFXPOSM: ".odoDebugPort.odoCmRefxPosition_m",
            self.Columns.FURTHESTOBJECTsROAD: ".trafficObject.furthestObject.sRoad",
            self.Columns.FURTHESTOBJECTYAW: ".trafficObject.furthestObject.yaw",
            self.Columns.sceneInterpretationActive_nu: ".sceneInterpretationActive_nu",
            self.Columns.PARKINGFAILREASON: ".targetPosesPort.failReason",
            self.Columns.PARKSMCORESTATUS: ".PARKSMCoreStatusPort.parksmCoreState_nu",
            self.Columns.PPCPARKINGMODE: ".CtrlCommandPort.ppcParkingMode_nu",
            self.Columns.APODOCMREFYPOSM: ".odoDebugPort.odoCmRefyPosition_m",
            self.Columns.APODOCMREFYAWANGRAD: ".odoDebugPort.odoCmRefyawAngEgoRaCur_rad",
            self.Columns.APODOESTIMYAWANGRAD: ".odoEstimationPort.yawAngle_rad",
            self.Columns.APODOESTIMXPOSM: ".odoEstimationPort.xPosition_m",
            self.Columns.APODOESTIMYPOSM: ".odoEstimationPort.yPosition_m",
            self.Columns.APODOESTIMYAWRATERADPS: ".odoEstimationPort.yawRate_radps",
            self.Columns.LONGIVELOCITY: ".odoEstimationPort.longiVelocity_mps",
            self.Columns.STEERANGFRONTAXLE_RAD: ".odoEstimationPortCM.steerAngFrontAxle_rad",
            self.Columns.MOTIONSTATUS_NU: ".odoEstimationPort.motionStatus_nu",
            self.Columns.STEERINGWHEELANGLE_RAD: ".odoInputPort.odoSigFcanPort.steerCtrlStatus.steeringWheelAngle_rad",
            self.Columns.STEERINGWHEELANGLEVELOCITY_RADPS: ".odoInputPort.odoSigFcanPort.steerCtrlStatus.steeringWheelAngleVelocity_radps",
            self.Columns.LATERALACCELERATION_MPS2: ".odoInputPort.odoSigFcanPort.vehDynamics.lateralAcceleration_mps2",
            self.Columns.LONGITUDINALACCELERATION_MPS2: ".odoInputPort.odoSigFcanPort.vehDynamics.longitudinalAcceleration_mps2",
            self.Columns.EBAACTIVE: ".staticBraking.EbaActive",
            self.Columns.CORESTOPREASON: ".PARKSMCoreStatusPort.coreStopReason_nu",
            self.Columns.YAWRATE_RADPS: ".odoEstimationPort.yawRate_radps",
            self.Columns.PITCHANGLE_RAD: ".odoEstimationPort.pitchAngle_rad",
            self.Columns.HEADUNITVISU_SCREEN_NU: ".headUnitVisualizationPort.screen_nu",
            self.Columns.MPSTATE: ".planningCtrlPort.mpStates",
            self.Columns.APSTATE: ".planningCtrlPort.apStates",
            self.Columns.RASTATE: ".planningCtrlPort.raStates",
            self.Columns.GPSTATE: ".planningCtrlPort.gpState",
            self.Columns.RMSTATE: ".planningCtrlPort.rmState",
            self.Columns.ORIENTATIONERROR: ".trajCtrlDebugPort.orientationError_rad",
            self.Columns.LATERALERROR: ".trajCtrlDebugPort.currentDeviation_m",
            self.Columns.APDISTTOSTOPREQINTEREXTRAPOLTRAJ: ".evaluationPort.distanceToStopReqInterExtrapolTraj_m",
            self.Columns.APTRAJCTRLACTIVE: ".trajCtrlRequestPort.trajCtrlActive_nu",
            self.Columns.APDRIVINGMODEREQ: ".trajCtrlRequestPort.drivingModeReq_nu",
            self.Columns.APUSECASE: ".evaluationPort.useCase_nu",
            self.Columns.NBCREVSTEPS: ".evaluationPort.TRJPLA_numberOfCrvSteps",
            self.Columns.ACTNBSTROKESGREATERMAXNBSTROKES: ".currentNrOfStrokesGreaterThanMaxNrOfSrokes_bool",
            self.Columns.LATDIFFOPTIMALTP_FINALEGOPOSE: ".testEvaluation.latDiffOptimalTP_FinalEgoPose_m",
            self.Columns.LONGDIFFOPTIMALTP_FINALEGOPOSE: ".testEvaluation.longDiffOptimalTP_FinalEgoPose_m",
            self.Columns.YAWDIFFOPTIMALTP_FINALEGOPOSE: ".testEvaluation.yawDiffOptimalTP_FinalEgoPose_deg",
            self.Columns.STEERANGREQ_RAD: ".steerCtrlRequestPort.steerAngReq_rad",
            self.Columns.USERACTIONHEADUNIT_NU: ".hmiOutputPort.userActionHeadUnit_nu",
            self.Columns.ALLOWEDMANEUVERINGSPACEEXCEED_BOOL: ".allowedManeuveringSpaceExceed_bool",
            self.Columns.HEADUNITVISU_MESSAGE_NU: ".headUnitVisualizationPort.message_nu",
            self.Columns.T_SIM_MAX_S: ".evaluationPort.t_sim_max_s",
            self.Columns.N_STROKES_MAX_NU: ".evaluationPort.n_strokes_max_nu",
            self.Columns.MAXCYCLETIMEOFAUPSTEP_MS: ".maxCycleTimeOfAUPStep_ms",
            self.Columns.REACHEDSTATUS: ".targetPosesPort.selectedPoseData.reachedStatus",
            self.Columns.LATDISTTOTARGET: ".evaluationPort.egoPoseTargetPoseDeviation.latDistToTarget_m",
            self.Columns.LONGDISTTOTARGET: ".evaluationPort.egoPoseTargetPoseDeviation.longDistToTarget_m",
            self.Columns.YAWDIFFTOTARGET: ".evaluationPort.egoPoseTargetPoseDeviation.yawDiffToTarget_rad",
            self.Columns.LATMAXDEVIATION: ".evaluationPort.latMaxDeviation_m",
            self.Columns.LONGMAXDEVIATION: ".evaluationPort.longMaxDeviation_m",
            self.Columns.YAWMAXDEVIATION: ".evaluationPort.yawMaxDeviation_rad",
            self.Columns.NUMVALIDPARKINGBOXES_NU: ".parkingBoxPort.numValidParkingBoxes_nu",
            self.Columns.PARKINGBOX0: ".parkingBoxPort.parkingBoxes_0.parkingBoxID_nu",
            self.Columns.NUMBEROFSTROKES: ".numberOfStrokes",
            self.Columns.TRAJCTRLREQUESTPORT: ".trajCtrlRequestPort.remoteReq_nu",
            self.Columns.WHEELANGLEACCELERATION: ".steeringWheelAngleAcceleration",
            self.Columns.LONGDIFFOPTIMALTP_TARGETPOSE: ".testEvaluation.longDiffOptimalTP_TargetPose_m",
            self.Columns.LATDIFFOPTIMALTP_TARGETPOSE: ".testEvaluation.latDiffOptimalTP_TargetPose_m",
            self.Columns.YAWDIFFOPTIMALTP_TARGETPOSE: ".testEvaluation.yawDiffOptimalTP_TargetPose_deg",
            self.Columns.STATEVARPPC: ".psmDebugPort.stateVarPPC_nu",
            self.Columns.STATEVARESM: ".psmDebugPort.stateVarESM_nu",
            self.Columns.STATEVARVSM: ".psmDebugPort.stateVarVSM_nu",
            self.Columns.STATEVARDM: ".psmDebugPort.stateVarDM_nu",
            self.Columns.STATEVARRDM: ".psmDebugPort.stateVarRDM_nu",
            self.Columns.CAR_OUTSIDE_PB: ".evaluationPort.car_outside_PB",
            self.Columns.STATICSTRUCTCOLIDESTARGET_POSE_0: ".evaluationPort.staticStructColidesTarget_Pose_0",
            self.Columns.STATICSTRUCTCOLIDESTARGET_POSE_1: ".evaluationPort.staticStructColidesTarget_Pose_1",
            self.Columns.STATICSTRUCTCOLIDESTARGET_POSE_2: ".evaluationPort.staticStructColidesTarget_Pose_2",
            self.Columns.STATICSTRUCTCOLIDESTARGET_POSE_3: ".evaluationPort.staticStructColidesTarget_Pose_3",
            self.Columns.STATICSTRUCTCOLIDESTARGET_POSE_4: ".evaluationPort.staticStructColidesTarget_Pose_4",
            self.Columns.STATICSTRUCTCOLIDESTARGET_POSE_5: ".evaluationPort.staticStructColidesTarget_Pose_5",
            self.Columns.STATICSTRUCTCOLIDESTARGET_POSE_6: ".evaluationPort.staticStructColidesTarget_Pose_6",
            self.Columns.STATICSTRUCTCOLIDESTARGET_POSE_7: ".evaluationPort.staticStructColidesTarget_Pose_7",
            self.Columns.LSCADISABLED: ".lscaDisabled_nu",
            self.Columns.CAR_VX: "Car.vx",
            self.Columns.CARYAWRATE: "Car.YawRate",
            self.Columns.LATSLOPE: "Car.Road.Route.LatSlope",
            self.Columns.COLLISIONCOUNT: "Sensor.Collision.Vhcl.Fr1.Count",
            self.Columns.LONGSLOPE: "Car.Road.Route.LongSlope",
            self.Columns.TIME: "Time",
            self.Columns.CAR_AX: "Car.ax",
            self.Columns.CAR_AY: "Car.ay",
            self.Columns.VHCL_V: "Vhcl.v",
            self.Columns.VHCLYAWRATE: "Vhcl.YawRate",
            self.Columns.VEHICLEROAD: "SI.trafficObject.Vehicle.sRoad",
            self.Columns.PARKINGLANEMARKING: "SI.trafficObject.parkingLaneMarking.sRoad",
            self.Columns.ODOROAD: "Traffic.Odo.sRoad",
            self.Columns.LSCAREQUESTMODE: "LSCA.brakePort.requestMode",
            self.Columns.BRAKEMODESTATE: "LSCA.statusPort.brakingModuleState_nu",
            self.Columns.CAR_V: "Car.v",
            self.Columns.OPTIMALTARGETPOSE_x: ".evaluationPort.OptimalTargetPose.x_m",
            self.Columns.OPTIMALTARGETPOSE_y: ".evaluationPort.OptimalTargetPose.y_m",
            self.Columns.OPTIMALTARGETPOSE_yaw: ".evaluationPort.OptimalTargetPose.yaw_rad",
            self.Columns.CMTARGETPOSE_x: ".targetPosesPortCMOrigin.targetPoses_0.pose.pos.x",
            self.Columns.CMTARGETPOSE_y: ".targetPosesPortCMOrigin.targetPoses_0.pose.pos.y",
            self.Columns.CMTARGETPOSE_yaw: ".targetPosesPortCl1Origin.targetPoses_0.pose.yaw_rad",
            self.Columns.PARKINGBOX0_SLOTCOORDINATES0_X: ".parkingBoxPortCMOrigin.parkingBoxes_0.slotCoordinates_FrontLeft_x",
            self.Columns.PARKINGBOX0_SLOTCOORDINATES0_Y: ".parkingBoxPortCMOrigin.parkingBoxes_0.slotCoordinates_FrontLeft_y",
            self.Columns.PARKINGBOX0_SLOTCOORDINATES1_X: ".parkingBoxPortCMOrigin.parkingBoxes_0.slotCoordinates_RearLeft_x",
            self.Columns.PARKINGBOX0_SLOTCOORDINATES1_Y: ".parkingBoxPortCMOrigin.parkingBoxes_0.slotCoordinates_RearLeft_y",
            self.Columns.PARKINGBOX0_SLOTCOORDINATES2_X: ".parkingBoxPortCMOrigin.parkingBoxes_0.slotCoordinates_RearRight_x",
            self.Columns.PARKINGBOX0_SLOTCOORDINATES2_Y: ".parkingBoxPortCMOrigin.parkingBoxes_0.slotCoordinates_RearRight_y",
            self.Columns.PARKINGBOX0_SLOTCOORDINATES3_X: ".parkingBoxPortCMOrigin.parkingBoxes_0.slotCoordinates_FrontRight_x",
            self.Columns.PARKINGBOX0_SLOTCOORDINATES3_Y: ".parkingBoxPortCMOrigin.parkingBoxes_0.slotCoordinates_FrontRight_y",
            self.Columns.PARKINGBOX1_SLOTCOORDINATES0_X: ".parkingBoxPortCMOrigin.parkingBoxes_1.slotCoordinates_FrontLeft_x",
            self.Columns.PARKINGBOX1_SLOTCOORDINATES0_Y: ".parkingBoxPortCMOrigin.parkingBoxes_1.slotCoordinates_FrontLeft_y",
            self.Columns.PARKINGBOX1_SLOTCOORDINATES1_X: ".parkingBoxPortCMOrigin.parkingBoxes_1.slotCoordinates_RearLeft_x",
            self.Columns.PARKINGBOX1_SLOTCOORDINATES1_Y: ".parkingBoxPortCMOrigin.parkingBoxes_1.slotCoordinates_RearLeft_y",
            self.Columns.PARKINGBOX1_SLOTCOORDINATES2_X: ".parkingBoxPortCMOrigin.parkingBoxes_1.slotCoordinates_RearRight_x",
            self.Columns.PARKINGBOX1_SLOTCOORDINATES2_Y: ".parkingBoxPortCMOrigin.parkingBoxes_1.slotCoordinates_RearRight_y",
            self.Columns.PARKINGBOX1_SLOTCOORDINATES3_X: ".parkingBoxPortCMOrigin.parkingBoxes_1.slotCoordinates_FrontRight_x",
            self.Columns.PARKINGBOX1_SLOTCOORDINATES3_Y: ".parkingBoxPortCMOrigin.parkingBoxes_1.slotCoordinates_FrontRight_y",
            self.Columns.TRAJVALID_NU: ".plannedTrajPort.trajValid_nu",
            self.Columns.NEWSEGMENTSTARTED_NU: ".plannedTrajPort.newSegmentStarted_nu",
            self.Columns.ANYPATHFOUND: ".targetPosesPort.anyPathFound",
            self.Columns.NUMVALIDPOSES_NU: "trjplaVisuPort.numValidPoses_nu",
            self.Columns.NUMVALIDSEGMENTS: "trjplaVisuPort.numValidSegments",
            self.Columns.PLANNEDPATHXPOS_7: "trjplaVisuPort.plannedPathXPos_m_7",
            self.Columns.PLANNEDPATHXPOS_8: "trjplaVisuPort.plannedPathXPos_m_8",
            self.Columns.PLANNEDPATHXPOS_999: "trjplaVisuPort.plannedPathXPos_m_999",
            self.Columns.PLANNEDPATHYPOS_7: "trjplaVisuPort.plannedPathYPos_m_7",
            self.Columns.PLANNEDPATHYPOS_8: "trjplaVisuPort.plannedPathYPos_m_8",
            self.Columns.RESETCOUNTER: ".targetPosesPort.resetCounter",
            self.Columns.RESETCOUNTER_NU: ".envModelPort.resetOriginResult.resetCounter_nu",
            self.Columns.PARKINGSCENARIO0: ".parkingBoxPort.parkingBoxes_0.parkingScenario_nu",
            self.Columns.PARKINGSCENARIO1: ".parkingBoxPort.parkingBoxes_1.parkingScenario_nu",
            self.Columns.PARKINGSCENARIO2: ".parkingBoxPort.parkingBoxes_2.parkingScenario_nu",
            self.Columns.PARKINGSCENARIO3: ".parkingBoxPort.parkingBoxes_3.parkingScenario_nu",
            self.Columns.PARKINGSCENARIO4: ".parkingBoxPort.parkingBoxes_4.parkingScenario_nu",
            self.Columns.PARKINGSCENARIO5: ".parkingBoxPort.parkingBoxes_5.parkingScenario_nu",
            self.Columns.PARKINGSCENARIO6: ".parkingBoxPort.parkingBoxes_6.parkingScenario_nu",
            self.Columns.PARKINGSCENARIO7: ".parkingBoxPort.parkingBoxes_7.parkingScenario_nu",
            self.Columns.NUMVALIDPOSES: ".targetPosesPort.numValidPoses",
            self.Columns.NUMVALIDCTRLPOINTS_NU: ".plannedTrajPort.numValidCtrlPoints_nu",
            self.Columns.RELATEDPARKINGBOXID_0: ".targetPosesPort.targetPoses_0.relatedParkingBoxID",
            self.Columns.RELATEDPARKINGBOXID_1: ".targetPosesPort.targetPoses_1.relatedParkingBoxID",
            self.Columns.RELATEDPARKINGBOXID_2: ".targetPosesPort.targetPoses_2.relatedParkingBoxID",
            self.Columns.RELATEDPARKINGBOXID_3: ".targetPosesPort.targetPoses_3.relatedParkingBoxID",
            self.Columns.RELATEDPARKINGBOXID_4: ".targetPosesPort.targetPoses_4.relatedParkingBoxID",
            self.Columns.RELATEDPARKINGBOXID_5: ".targetPosesPort.targetPoses_5.relatedParkingBoxID",
            self.Columns.RELATEDPARKINGBOXID_6: ".targetPosesPort.targetPoses_6.relatedParkingBoxID",
            self.Columns.RELATEDPARKINGBOXID_7: ".targetPosesPort.targetPoses_7.relatedParkingBoxID",
            self.Columns.PARKINGBOX0: ".parkingBoxPort.parkingBoxes_0.parkingBoxID_nu",
            self.Columns.PARKINGBOX1: ".parkingBoxPort.parkingBoxes_1.parkingBoxID_nu",
            self.Columns.PARKINGBOX2: ".parkingBoxPort.parkingBoxes_2.parkingBoxID_nu",
            self.Columns.PARKINGBOX3: ".parkingBoxPort.parkingBoxes_3.parkingBoxID_nu",
            self.Columns.PARKINGBOX4: ".parkingBoxPort.parkingBoxes_4.parkingBoxID_nu",
            self.Columns.PARKINGBOX5: ".parkingBoxPort.parkingBoxes_5.parkingBoxID_nu",
            self.Columns.PARKINGBOX6: ".parkingBoxPort.parkingBoxes_6.parkingBoxID_nu",
            self.Columns.PARKINGBOX7: ".parkingBoxPort.parkingBoxes_7.parkingBoxID_nu",
            self.Columns.TRAJTYPE_NU: ".plannedTrajPort.trajType_nu",
            self.Columns.APCHOSENTARGETPOSEID: ".planningCtrlPort.apChosenTargetPoseId_nu",
            self.Columns.TARGETPOSESTYPE0: ".targetPosesPort.targetPoses_0.type",
            self.Columns.TARGETPOSESTYPE1: ".targetPosesPort.targetPoses_1.type",
            self.Columns.TARGETPOSESTYPE2: ".targetPosesPort.targetPoses_2.type",
            self.Columns.TARGETPOSESTYPE3: ".targetPosesPort.targetPoses_3.type",
            self.Columns.TARGETPOSESTYPE4: ".targetPosesPort.targetPoses_4.type",
            self.Columns.TARGETPOSESTYPE5: ".targetPosesPort.targetPoses_5.type",
            self.Columns.TARGETPOSESTYPE6: ".targetPosesPort.targetPoses_6.type",
            self.Columns.TARGETPOSESTYPE7: ".targetPosesPort.targetPoses_7.type",
            self.Columns.TARGETPOSEID0: ".targetPosesPort.targetPoses_0.pose_ID",
            self.Columns.TARGETPOSEID1: ".targetPosesPort.targetPoses_1.pose_ID",
            self.Columns.TARGETPOSEID2: ".targetPosesPort.targetPoses_2.pose_ID",
            self.Columns.TARGETPOSEID3: ".targetPosesPort.targetPoses_3.pose_ID",
            self.Columns.TARGETPOSEID4: ".targetPosesPort.targetPoses_4.pose_ID",
            self.Columns.TARGETPOSEID5: ".targetPosesPort.targetPoses_5.pose_ID",
            self.Columns.TARGETPOSEID6: ".targetPosesPort.targetPoses_6.pose_ID",
            self.Columns.TARGETPOSEID7: ".targetPosesPort.targetPoses_7.pose_ID",
            self.Columns.TARGETPOSEREACHABLE0: ".targetPosesPort.targetPoses_0.reachableStatus",
            self.Columns.TARGETPOSEREACHABLE1: ".targetPosesPort.targetPoses_1.reachableStatus",
            self.Columns.TARGETPOSEREACHABLE2: ".targetPosesPort.targetPoses_2.reachableStatus",
            self.Columns.TARGETPOSEREACHABLE3: ".targetPosesPort.targetPoses_3.reachableStatus",
            self.Columns.TARGETPOSEREACHABLE4: ".targetPosesPort.targetPoses_4.reachableStatus",
            self.Columns.TARGETPOSEREACHABLE5: ".targetPosesPort.targetPoses_5.reachableStatus",
            self.Columns.TARGETPOSEREACHABLE6: ".targetPosesPort.targetPoses_6.reachableStatus",
            self.Columns.TARGETPOSEREACHABLE7: ".targetPosesPort.targetPoses_7.reachableStatus",
        }


class EntrySignals(SignalDefinition):
    """MF signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIMESTAMP = "TimeStamp"
        EGOMOTIONPORT = "EgoMotionPort"
        PSMDEBUGPORT = "PSMDebugPort"
        PPCPARKINGMODE = "ppcParkingMode"
        PARKINGSCENARIO = "ParkingScenario"
        NUMBEROFVALIDPARKINGBOXES = "NumberOfValidParkingBoxes"
        NUMBEROFKMDRIVEN = "NumberOfKmDriven"
        NUMVALIDSEGMENTS = "NumValidSegments"
        DRVDIR0 = "DrvDir0"
        DRVDIR1 = "DrvDir1"
        DRVDIR2 = "DrvDir2"
        DRVDIR3 = "DrvDir3"
        DRVDIR4 = "DrvDir4"
        DRVDIR5 = "DrvDir5"
        DRVDIR6 = "DrvDir6"
        DRVDIR7 = "DrvDir7"
        DRVDIR8 = "DrvDir8"
        DRVDIR9 = "DrvDir9"
        DRVDIR10 = "DrvDir10"
        DRVDIR11 = "DrvDir11"
        DRVDIR12 = "DrvDir12"
        DRVDIR13 = "DrvDir13"
        DRVDIR14 = "DrvDir14"
        DRVDIR15 = "DrvDir15"
        DRVDIR16 = "DrvDir16"
        DRVDIR17 = "DrvDir17"
        DRVDIR18 = "DrvDir18"
        DRVDIR19 = "DrvDir19"
        DRVDIR20 = "DrvDir20"
        DRVDIR21 = "DrvDir21"
        DRVDIR22 = "DrvDir22"
        DRVDIR23 = "DrvDir23"
        DRVDIR24 = "DrvDir24"
        NUMBERVALIDSTATICOBJECTS = "NumberValidStaticObjects"
        SLOTCOORDINATES = "SlotCoordinates"
        SLOTCOORDINATES1 = "SlotCoordinates1"
        SLOTCOORDINATES2 = "SlotCoordinates2"
        EGOPOSITIONAP = "EgoPositionAP"
        TRANSFTOODOM = "TransfToOdom"
        STATICOBJECTSHAPE0 = "StaticObjectShape0"
        STATICOBJECTSHAPE1 = "StaticObjectShape1"
        STATICOBJECTSHAPE2 = "StaticObjectShape2"
        STATICOBJECTSHAPE3 = "StaticObjectShape3"
        STATICOBJECTSHAPE4 = "StaticObjectShape4"
        STATICOBJECTSHAPE5 = "StaticObjectShape5"
        STATICOBJECTSHAPE6 = "StaticObjectShape6"
        STATICOBJECTSHAPE7 = "StaticObjectShape7"
        STATICOBJECTSHAPE8 = "StaticObjectShape8"
        STATICOBJECTSHAPE9 = "StaticObjectShape9"
        STATICOBJECTSHAPE10 = "StaticObjectShape10"
        STATICOBJECTSHAPE11 = "StaticObjectShape11"
        STATICOBJECTSHAPE12 = "StaticObjectShape12"
        STATICOBJECTSHAPE13 = "StaticObjectShape13"
        STATICOBJECTSHAPE14 = "StaticObjectShape14"
        STATICOBJECTSHAPE15 = "StaticObjectShape15"
        STATICOBJECTSHAPE16 = "StaticObjectShape16"
        STATICOBJECTSHAPE17 = "StaticObjectShape17"
        STATICOBJECTSHAPE18 = "StaticObjectShape18"
        STATICOBJECTSHAPE19 = "StaticObjectShape19"
        STATICOBJECTSHAPE20 = "StaticObjectShape20"
        STATICOBJECTSHAPE21 = "StaticObjectShape21"
        STATICOBJECTSHAPE22 = "StaticObjectShape22"
        STATICOBJECTSHAPE23 = "StaticObjectShape23"
        STATICOBJECTSHAPE24 = "StaticObjectShape24"
        STATICOBJECTSHAPE25 = "StaticObjectShape25"
        STATICOBJECTSHAPE26 = "StaticObjectShape26"
        STATICOBJECTSHAPE27 = "StaticObjectShape27"
        STATICOBJECTSHAPE28 = "StaticObjectShape28"
        STATICOBJECTSHAPE29 = "StaticObjectShape29"
        STATICOBJECTSHAPE30 = "StaticObjectShape30"
        STATICOBJECTSHAPE31 = "StaticObjectShape31"
        DGPSHUNTERX = "DgpsHunterX"
        DGPSHUNTERY = "DgpsHunterY"
        DGPSTARGETX = "DgpsTargetX"
        DGPSTARGETY = "DgpsTargetY"
        DGPSTARGET2X = "DgpsTarget2X"
        DGPSTARGET2Y = "DgpsTarget2Y"
        DGPSTARGET3X = "DgpsTarget3X"
        DGPSTARGET3Y = "DgpsTarget3Y"
        DGPSTARGET4X = "DgpsTarget4X"
        DGPSTARGET4Y = "DgpsTarget4Y"
        DGPSEGOYAW = "DgpsEgoYaw"
        ODOESTIMX = "OdoEstimX"
        ODOESTIMY = "OdoEstimY"
        RTAREFTSUS = "RtaRefTsUs"
        RTAMAXEVENTINDEX = "RtaMaxEventIndex"
        CARYAWRATE = "CarYawRate"
        CAR_VX = "EgoMotionPort"
        U_RELTIME_US = "u_RelTime_us"
        U_LOCALID = "u_LocalId"
        U_EVENTTYPE = "u_EventType"
        U_GLOBALID = "u_GlobalId"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = [
            "MTS.Package",
            "M7board.EM_Thread",
            "Reference_CAN.RT-Range_2017_02_28_SystemC",
            "Reference_CAN.NAVconfig_AP_Passat_154_28-02-2017",
            "M7board.CAN_Thread",
        ]

        self._properties = {
            self.Columns.TIMESTAMP: ".TimeStamp",
            self.Columns.EGOMOTIONPORT: ".EgoMotionPort.vel_mps",
            self.Columns.PSMDEBUGPORT: ".PSMDebugPort.stateVarPPC_nu",
            self.Columns.PPCPARKINGMODE: ".CtrlCommandPort.ppcParkingMode_nu",
            self.Columns.PARKINGSCENARIO: ".ApParkingBoxPort.parkingBoxes[0].parkingScenario_nu",
            self.Columns.NUMBEROFVALIDPARKINGBOXES: ".ApParkingBoxPort.numValidParkingBoxes_nu",
            self.Columns.NUMBEROFKMDRIVEN: ".EgoMotionPort.drivenDistance_m",
            self.Columns.NUMVALIDSEGMENTS: ".TrajPlanVisuPort.numValidSegments",
            self.Columns.DRVDIR0: ".TrajPlanVisuPort.plannedGeometricPath[0].drvDir",
            self.Columns.DRVDIR1: ".TrajPlanVisuPort.plannedGeometricPath[1].drvDir",
            self.Columns.DRVDIR2: ".TrajPlanVisuPort.plannedGeometricPath[2].drvDir",
            self.Columns.DRVDIR3: ".TrajPlanVisuPort.plannedGeometricPath[3].drvDir",
            self.Columns.DRVDIR4: ".TrajPlanVisuPort.plannedGeometricPath[4].drvDir",
            self.Columns.DRVDIR5: ".TrajPlanVisuPort.plannedGeometricPath[5].drvDir",
            self.Columns.DRVDIR6: ".TrajPlanVisuPort.plannedGeometricPath[6].drvDir",
            self.Columns.DRVDIR7: ".TrajPlanVisuPort.plannedGeometricPath[7].drvDir",
            self.Columns.DRVDIR8: ".TrajPlanVisuPort.plannedGeometricPath[8].drvDir",
            self.Columns.DRVDIR9: ".TrajPlanVisuPort.plannedGeometricPath[9].drvDir",
            self.Columns.DRVDIR10: ".TrajPlanVisuPort.plannedGeometricPath[10].drvDir",
            self.Columns.DRVDIR11: ".TrajPlanVisuPort.plannedGeometricPath[11].drvDir",
            self.Columns.DRVDIR12: ".TrajPlanVisuPort.plannedGeometricPath[12].drvDir",
            self.Columns.DRVDIR13: ".TrajPlanVisuPort.plannedGeometricPath[13].drvDir",
            self.Columns.DRVDIR14: ".TrajPlanVisuPort.plannedGeometricPath[14].drvDir",
            self.Columns.DRVDIR15: ".TrajPlanVisuPort.plannedGeometricPath[15].drvDir",
            self.Columns.DRVDIR16: ".TrajPlanVisuPort.plannedGeometricPath[16].drvDir",
            self.Columns.DRVDIR17: ".TrajPlanVisuPort.plannedGeometricPath[17].drvDir",
            self.Columns.DRVDIR18: ".TrajPlanVisuPort.plannedGeometricPath[18].drvDir",
            self.Columns.DRVDIR19: ".TrajPlanVisuPort.plannedGeometricPath[19].drvDir",
            self.Columns.DRVDIR20: ".TrajPlanVisuPort.plannedGeometricPath[20].drvDir",
            self.Columns.DRVDIR21: ".TrajPlanVisuPort.plannedGeometricPath[21].drvDir",
            self.Columns.DRVDIR22: ".TrajPlanVisuPort.plannedGeometricPath[22].drvDir",
            self.Columns.DRVDIR23: ".TrajPlanVisuPort.plannedGeometricPath[23].drvDir",
            self.Columns.DRVDIR24: ".TrajPlanVisuPort.plannedGeometricPath[24].drvDir",
            self.Columns.NUMBERVALIDSTATICOBJECTS: ".CollEnvModelPort.numberOfStaticObjects_u8",
            self.Columns.SLOTCOORDINATES: ".ApParkingBoxPort.parkingBoxes[0].slotCoordinates_m",
            self.Columns.SLOTCOORDINATES1: ".ApParkingBoxPort.parkingBoxes[1].slotCoordinates_m",
            self.Columns.SLOTCOORDINATES2: ".ApParkingBoxPort.parkingBoxes[2].slotCoordinates_m",
            self.Columns.EGOPOSITIONAP: ".ApEnvModelPort.egoVehiclePoseForAP",
            self.Columns.TRANSFTOODOM: ".ApEnvModelPort.transformationToOdometry",
            self.Columns.STATICOBJECTSHAPE0: ".CollEnvModelPort.staticObjects[0].objShape_m",
            self.Columns.STATICOBJECTSHAPE1: ".CollEnvModelPort.staticObjects[1].objShape_m",
            self.Columns.STATICOBJECTSHAPE2: ".CollEnvModelPort.staticObjects[2].objShape_m",
            self.Columns.STATICOBJECTSHAPE3: ".CollEnvModelPort.staticObjects[3].objShape_m",
            self.Columns.STATICOBJECTSHAPE4: ".CollEnvModelPort.staticObjects[4].objShape_m",
            self.Columns.STATICOBJECTSHAPE5: ".CollEnvModelPort.staticObjects[5].objShape_m",
            self.Columns.STATICOBJECTSHAPE6: ".CollEnvModelPort.staticObjects[6].objShape_m",
            self.Columns.STATICOBJECTSHAPE7: ".CollEnvModelPort.staticObjects[7].objShape_m",
            self.Columns.STATICOBJECTSHAPE8: ".CollEnvModelPort.staticObjects[8].objShape_m",
            self.Columns.STATICOBJECTSHAPE9: ".CollEnvModelPort.staticObjects[9].objShape_m",
            self.Columns.STATICOBJECTSHAPE10: ".CollEnvModelPort.staticObjects[10].objShape_m",
            self.Columns.STATICOBJECTSHAPE11: ".CollEnvModelPort.staticObjects[11].objShape_m",
            self.Columns.STATICOBJECTSHAPE12: ".CollEnvModelPort.staticObjects[12].objShape_m",
            self.Columns.STATICOBJECTSHAPE13: ".CollEnvModelPort.staticObjects[13].objShape_m",
            self.Columns.STATICOBJECTSHAPE14: ".CollEnvModelPort.staticObjects[14].objShape_m",
            self.Columns.STATICOBJECTSHAPE15: ".CollEnvModelPort.staticObjects[15].objShape_m",
            self.Columns.STATICOBJECTSHAPE16: ".CollEnvModelPort.staticObjects[16].objShape_m",
            self.Columns.STATICOBJECTSHAPE17: ".CollEnvModelPort.staticObjects[17].objShape_m",
            self.Columns.STATICOBJECTSHAPE18: ".CollEnvModelPort.staticObjects[18].objShape_m",
            self.Columns.STATICOBJECTSHAPE19: ".CollEnvModelPort.staticObjects[19].objShape_m",
            self.Columns.STATICOBJECTSHAPE20: ".CollEnvModelPort.staticObjects[20].objShape_m",
            self.Columns.STATICOBJECTSHAPE21: ".CollEnvModelPort.staticObjects[21].objShape_m",
            self.Columns.STATICOBJECTSHAPE22: ".CollEnvModelPort.staticObjects[22].objShape_m",
            self.Columns.STATICOBJECTSHAPE23: ".CollEnvModelPort.staticObjects[23].objShape_m",
            self.Columns.STATICOBJECTSHAPE24: ".CollEnvModelPort.staticObjects[24].objShape_m",
            self.Columns.STATICOBJECTSHAPE25: ".CollEnvModelPort.staticObjects[25].objShape_m",
            self.Columns.STATICOBJECTSHAPE26: ".CollEnvModelPort.staticObjects[26].objShape_m",
            self.Columns.STATICOBJECTSHAPE27: ".CollEnvModelPort.staticObjects[27].objShape_m",
            self.Columns.STATICOBJECTSHAPE28: ".CollEnvModelPort.staticObjects[28].objShape_m",
            self.Columns.STATICOBJECTSHAPE29: ".CollEnvModelPort.staticObjects[29].objShape_m",
            self.Columns.STATICOBJECTSHAPE30: ".CollEnvModelPort.staticObjects[30].objShape_m",
            self.Columns.STATICOBJECTSHAPE31: ".CollEnvModelPort.staticObjects[31].objShape_m",
            self.Columns.DGPSHUNTERX: ".RangeHunterPosLocal.RangeHunterPosLocalX",
            self.Columns.DGPSHUNTERY: ".RangeHunterPosLocal.RangeHunterPosLocalY",
            self.Columns.DGPSTARGETX: ".RangeTargetPosLocal.RangeTargetPosLocalX",
            self.Columns.DGPSTARGETY: ".RangeTargetPosLocal.RangeTargetPosLocalY",
            self.Columns.DGPSTARGET2X: ".Range2TargetPosLocal.Range2TargetPosLocalX",
            self.Columns.DGPSTARGET2Y: ".Range2TargetPosLocal.Range2TargetPosLocalY",
            self.Columns.DGPSTARGET3X: ".Range3TargetPosLocal.Range3TargetPosLocalX",
            self.Columns.DGPSTARGET3Y: ".Range3TargetPosLocal.Range3TargetPosLocalY",
            self.Columns.DGPSTARGET4X: ".Range4TargetPosLocal.Range4TargetPosLocalX",
            self.Columns.DGPSTARGET4Y: ".Range4TargetPosLocal.Range4TargetPosLocalY",
            self.Columns.DGPSEGOYAW: ".HeadingPitchRoll.AngleHeading",
            self.Columns.ODOESTIMX: ".OdoEstimationPort.xPosition_m",
            self.Columns.ODOESTIMY: ".OdoEstimationPort.yPosition_m",
            self.Columns.RTAREFTSUS: ".RTA_BUFFER_0.u_RefTs_us",
            self.Columns.RTAMAXEVENTINDEX: ".RTA_BUFFER_0.u_MaxEventIndex",
            self.Columns.CARYAWRATE: "Car.YawRate",
            self.Columns.CAR_VX: ".EgoMotionPort.vel_mps",
            self.Columns.CARYAWRATE: ".EgoMotionPort.yawRate_radps",
            self.Columns.U_RELTIME_US: ".RTA_BUFFER_0.EventContainer[%].u_RelTime_us",
            self.Columns.U_LOCALID: ".RTA_BUFFER_0.EventContainer[%].u_LocalId",
            self.Columns.U_EVENTTYPE: ".RTA_BUFFER_0.EventContainer[%].u_EventType",
            self.Columns.U_GLOBALID: ".RTA_BUFFER_0.EventContainer[%].u_GlobalId",
        }


def pdw_threshold_check(measured):
    """Check the measured value against predefined threshold zones.

    Args:
        measured: The measured value.

    Returns:
        int: Result code indicating the zone:
            - 1: Green zone
            - 2: Yellow zone
            - 3: Red zone
            - 0: None of the above
    """
    if constants.PDWConstants.GREEN_ZONE[0] >= measured and constants.PDWConstants.GREEN_ZONE[1] <= measured:
        return 1
    elif constants.PDWConstants.YELLOW_ZONE[0] >= measured and constants.PDWConstants.YELLOW_ZONE[1] <= measured:
        return 2
    elif measured <= constants.PDWConstants.RED_ZONE:
        return 3
    else:
        return 0


class MfHilClCustomTestcaseReport(CustomReportTestCase):
    """Custom MF HIL test case report class."""

    def __init__(self):
        """Initialize the report."""
        super().__init__()
        self.results = None
        self.result_dict = {}
        self.result_list = []
        self.anchor_list = []
        self.start_time = None

    def on_result(self, pr_details: ProcessingResult, ts_result: TeststepResult):
        """Process the test step result.

        Args:
            pr_details (ProcessingResult): Processing details.
            ts_result (TeststepResult): Test step result.
        """
        if "Processing_time" in pr_details and self.start_time is None:
            self.start_time = pr_details["Processing_time"]
        # self._env.testrun.testcase_results
        if "Additional_results" in pr_details:
            a = {"Measurement": pr_details["file_name"]}

            a.update(pr_details["Additional_results"])
            self.result_list.append(a)
            self.anchor_list.append(
                f'"../teststeps_details/{ts_result.teststep_definition.id}_details_for_{ts_result.test_input.id}.html"'
            )

    def overview(self):
        """Generate an overview of the test case report.

        Returns:
            str: Overview of the test case report.
        """
        results_dict = {
            fc.PASS.title(): 0,
            fc.FAIL.title(): 0,
            fc.INPUT_MISSING.title(): 0,
            fc.NOT_ASSESSED.title(): 0,
        }

        s = ""
        if self.start_time is not None:
            process_time = time.time() - self.start_time
            process_time = time.strftime("%M:%S", time.gmtime(process_time))
            s += "<h4> Processing time</h4>"
            s += f"<h5>{process_time} seconds</h5>"
            s += "<br>"
        try:
            columns = []
            row_events = []
            for r in self.result_list:
                columns.extend(list(r.keys()))
                break

            for d in self.result_list:
                r = []
                for c in columns:
                    if c in d:
                        v = d[c]
                        if isinstance(v, dict):
                            if "color" in v:
                                r.append(
                                    str(
                                        f"""<span align="center" style="width: 100%; height: 100%; display: block;background-color: {v['color']}; color : #ffffff">{v['value']}</span>"""
                                    )
                                )
                            else:
                                r.append(
                                    str(
                                        f"""<span align="center" style="width: 100%; height: 100%; display: block">{v['value']}</span>"""
                                    )
                                )
                        elif "Measurement" in c:
                            # r.append(v)
                            r.append(
                                str(
                                    f"""<span align="center" style="background-color: {d['Verdict']['color']}; color : #ffffff">{v}</span>"""
                                )
                            )

                            try:
                                results_dict[d["Verdict"]["value"]] += 1
                            except Exception as e:
                                print(str(e))
                        else:
                            r.append(v)

                    else:
                        r.append("")
                row_events.append(r)
            # for index in range(len(row_events)):

            #     row_events[index][0] = str(
            #         f"""<a href={self.anchor_list[index]}>{row_events[index][0]}</a>""")

            column_names = [{"title": str(c)} for c in columns]
            additional_tables = (
                """
        <h2>Additional Information</h2>
<script>
var table_column_names = """
                + dumps(column_names)
                + """;
var table_rows_events =  """
                + dumps(row_events)
                + """
$(document).ready(function() {
$('#events_table').DataTable( {
paging:    true,
searching: true,
info:      true,
scrollX: true,
ordering: true,
data: table_rows_events,
columns: table_column_names
} );
});
</script>
<table class="table-sm table-striped compact nowrap" id="events_table">
<caption>Table: Additional Information</caption>
</table>
"""
            )
            s += "<h4>Overview results</h4>"
            s += "<br>"
            s += f"<h6>Passed: {results_dict[fc.PASS.title()]}</h6>"
            s += f"<h6>Failed: {results_dict[fc.FAIL.title()]}</h6>"
            s += f"<h6>Input missing: {results_dict[fc.INPUT_MISSING.title()]}</h6>"
            s += f"<h6>Not assessed: {results_dict[fc.NOT_ASSESSED.title()]}</h6>"
            s += "<br>"
            s += additional_tables

        except Exception as ex:
            # Handle other exceptions
            print(f"An error occurred: {ex}")
            s += "<h6>No additional info available</h6>"
        return s


class MfHilClCustomTeststepReport(CustomReportTestStep):
    """Custom MF HIL Cl test case report class."""

    def overview(
        self,
        processing_details_list: ProcessingResultsList,
        teststep_result: List["TeststepResult"],
    ):
        """Generate an overview of the test step report.

        Args:
            processing_details_list (ProcessingResultsList): List of processing results.
            teststep_result (List[TeststepResult]): List of test step results.

        Returns:
            str: Overview of the test step report.
        """
        s = ""

        # pr_list = processing_details_list
        s += "<br>"
        s += "<br>"

        # for d in range(len(pr_list)):
        #     json_entries = ProcessingResult.from_json(
        #         pr_list.processing_result_files[d])
        #     if "Plots" in json_entries.details and len(json_entries.details["Plots"]) > 1:
        #         s += f'<h4>Plots for failed measurements</h4>'
        #         s += f'<font color="red"><h7>{json_entries.details["file_name"]}</h7></font>'
        #         for plot in range(len(json_entries.details["Plots"])):

        #             s += json_entries.details["Plots"][plot]
        #             try:
        #                 s += f'<br>'
        #                 s += f'<h7>{json_entries.details["Remarks"][plot]}</h7>'
        #             except:
        #                 pass

        return s

    def details(self, processing_details: ProcessingResult, teststep_result: "TeststepResult") -> str:
        """Generate details of the test step report.

        Args:
            processing_details (ProcessingResult): Processing results.
            teststep_result (TeststepResult): Test step result.

        Returns:
            str: Details of the test step report.
        """
        s = "<br>"
        # color = ""
        m_res = teststep_result.measured_result
        e_res = teststep_result.teststep_definition.expected_results[None]
        (
            _,
            status,
        ) = e_res.compute_result_status(m_res)
        verdict = status.key.lower()

        if "data nok" in verdict:
            verdict = fc.NOT_ASSESSED

        s += f'<span align="center" style="width: 100%; height: 100%; display: block;background-color: {get_color(verdict)}; color : #ffffff">Step result: {verdict.upper()}</span>'

        for k, v in processing_details.details.items():
            if "Plots" in k:
                s += "<div>"
                for plot in v:

                    s += plot
                s += "</div>"

        return s


class BackButtonOverview(CustomReportOverview):
    """Custom report overview with back button functionality.

    This class generates a back button overview containing quick links.

    Methods:
        build(testrun_container): Builds the back button overview with quick links.

    Attributes:
        None
    """

    def build(self, testrun_container: TestrunContainer) -> str:
        """
        Builds a back button overview with quick links.

        Args:
            testrun_container: Container for the test run.

        Returns:
            str: HTML content containing quick links.
        """
        from pathlib import PurePath

        # d = defaultdict(dict)
        path_split = PurePath(self.environment.output_folder).parts
        # print(path_split[4:])
        path_to_report = "../../../../"

        if path_split[-4:][0].isdigit():
            path_to_report + "../"

        path_to_overview = path_to_report + "Overview.html"
        path_to_graphs = path_to_report + "static/graphs.html"
        path_to_failed_meas = path_to_report + "static/failed_meas.html"
        r = "<p>Quick links</p>"
        r += f'<p> <a href="{path_to_overview}">Overall overview</a></p>'
        r += f'<p> <a href="{path_to_graphs}">Overall Graphs</a></p>'
        r += f'<p> <a href="{path_to_failed_meas}">Overall failed measurements</a></p>'
        return r


class BackButtonOverviewNonRegression(CustomReportOverview):
    """Custom report overview with back button functionality.

    This class generates a back button overview containing quick links.

    Methods:
        build(testrun_container): Builds the back button overview with quick links.

    Attributes:
        None
    """

    def build(self, testrun_container: TestrunContainer) -> str:
        """
        Builds a back button overview with quick links.

        Args:
            testrun_container: Container for the test run.

        Returns:
            str: HTML content containing quick links.
        """
        from pathlib import PurePath

        # d = defaultdict(dict)
        path_split = PurePath(self.environment.output_folder).parts
        # print(path_split[4:])
        path_to_report = "../../../"

        if path_split[-4:][0].isdigit():
            path_to_report + "../"

        path_to_overview = path_to_report + "Overview.html"
        path_to_graphs = path_to_report + "static/graphs.html"
        path_to_failed_meas = path_to_report + "static/failed_meas.html"
        r = "<p>Quick links</p>"
        r += f'<p> <a href="{path_to_overview}">Overall overview</a></p>'
        r += f'<p> <a href="{path_to_graphs}">Overall Graphs</a></p>'
        r += f'<p> <a href="{path_to_failed_meas}">Overall failed measurements</a></p>'
        return r


class HilClFuntions:
    """Utility class for handling rising and falling edge functions."""

    @staticmethod
    def hil_convert_dict_to_pandas(signal_summary: dict, table_remark="", table_title=""):
        """Converts a dictionary to a Pandas DataFrame and creates an HTML table."""
        evaluation_summary = pd.DataFrame(
            {
                "Evaluation": {key: key for key, val in signal_summary.items()},
                "Result": {key: val for key, val in signal_summary.items()},
            }
        )
        return build_html_table(evaluation_summary, table_remark, table_title)

    def RisingEdge(input_signal, round_legnt):
        """Detects rising edges in the input signal.

        Args:
            input_signal (list): List of input signal values.
            round_legnt (int): Length for rounding the input signal.

        Returns:
            list: List of indices where rising edges occur.
        """
        previous_value = None
        collected_idx = []

        for cnt in range(0, len(input_signal)):
            if cnt == 0:
                previous_value = round(input_signal[cnt], round_legnt)
                continue

            if previous_value < round(input_signal[cnt], round_legnt):
                collected_idx.append(cnt)
                previous_value = round(input_signal[cnt], round_legnt)

            else:
                previous_value = round(input_signal[cnt], round_legnt)
        return collected_idx

    def FallingEdge(input_signal, round_legnt):
        """
        Detects falling edges in the input signal.

        Args:
            input_signal (list): List of input signal values.
            round_legnt (int): Length for rounding the input signal.

        Returns:
            list: List of indices where falling edges occur.
        """
        previous_value = None
        collected_idx = []

        for cnt in range(0, len(input_signal)):
            if cnt == 0:
                previous_value = round(input_signal[cnt], round_legnt)
                continue

            if previous_value > round(input_signal[cnt], round_legnt):
                collected_idx.append(cnt)
                previous_value = round(input_signal[cnt], round_legnt)

            else:
                previous_value = round(input_signal[cnt], round_legnt)

        return collected_idx

    def States(input_signal, t_start_idx, t_end_idx, round_legnt):
        """
        Collect states in the input signal.

        Args:
            input_signal (list): List of input signal values.
            t_start_idx (int): Begining of collection.
            t_end_idx (int): End of collection.
            round_legnt (int): Length for rounding the input signal.

        Returns:
            list: List of indices where falling edges occur.
        """
        previous_value = None
        collected_states = {}

        for cnt in range(t_start_idx, t_end_idx):
            if previous_value != round(input_signal[cnt], round_legnt):
                previous_value = round(input_signal[cnt], round_legnt)
                collected_states.update({cnt: round(input_signal[cnt], round_legnt)})

        return collected_states

    def length_check(**kwargs):
        """Checking if given lists have the same length."""
        lengths = {key: len(value) for key, value in kwargs.items()}

        # Check if any argument has a different length
        unique_lengths = set(lengths.values())
        if len(unique_lengths) != 1:
            warning_message = "\033[93m" + "Length mismatch for the following arguments:\n"
            for key, value in lengths.items():
                warning_message += f"The length of '{key}' is {value}. \n"
            warnings.warn((warning_message + "\033[0m"), UserWarning, stacklevel=2)

    def maneuver_area_check(
        positions_x=None,
        positions_y=None,
        heading_angle=None,
        ego_wheelbase: float = 0,
        ego_length: float = 0,
        ego_rear_overhang: float = 0,
        ego_front_overhang: float = 0,
        ego_width: float = 0,
        d_1: float = 0,
        d_2: float = 0,
        d_3: float = 0,
        d_4: float = 0,
        parking_pos_x: float = 0,
        parking_pos_y: float = 0,
    ):
        """
        Examining if a dynamic object enters the defined static zone.

        Args:
            positions_x (list): List of x coordinates [m] of dynamic object position.
            positions_y (list): List of y coordinates [m] of dynamic object position.
            heading_angle (list): List of heading angle values [rad] of dynamic object position.
            ego_wheelbase (float): Value of the wheelbase of the dynamic object in meters. Optional, but either ego_wheelbase or ego_length shall be given.
            ego_length (float): Value of the length of the dynamic object in meters Optional, but either ego_wheelbase or ego_length shall be given.
            ego_rear_overhang (float): Value of the distance between rear bumper and rear axle of the dynamic object in meters.
            ego_front_overhang (float): Value of the distance between front bumper and front axle of the dynamic object in meters.
            ego_width (float): Value of the width of the dynamic object in meters.
            d_1 (float): Value of D1 based on parking area requirement in meters.
            d_2 (float): Value of D2 based on parking area requirement in meters.
            d_3 (float): Value of D3 based on parking area requirement in meters.
            d_4 (float): Value of D4 based on parking area requirement in meters.
            parking_pos_x (float): X coordinate of the final parking position.
            parking_pos_y (float): Y coordinate of the final parking position.

        Returns:
            result (list): Returns a boolean array with the results of each measured time instance.
            m_a_multiple (list): Returns the maneuvering area exterior points in a list for each measured time instance.
            target_boxes (list): Returns the dynamic object exterior points in a list for each measured time instance.
        """
        if heading_angle is None:
            heading_angle = []
        if positions_y is None:
            positions_y = []
        if positions_x is None:
            positions_x = []
        HilClFuntions.length_check(rel_dist_x=positions_x, rel_dist_y=positions_y, heading_angle=heading_angle)

        result = [False] * len(positions_x)
        if ego_rear_overhang != 0:
            rear_overhang = ego_rear_overhang
        else:
            rear_overhang = ego_length - ego_wheelbase - ego_front_overhang
        maneuvering_area = box(
            parking_pos_x - rear_overhang - d_2,
            parking_pos_y - ego_width / 2 - d_3,
            parking_pos_x + ego_wheelbase + ego_front_overhang + d_4,
            parking_pos_y + ego_width / 2 + d_1,
        )
        target_boxes = []
        m_a_multiple = []
        m_a_x, m_a_y = maneuvering_area.exterior.xy
        for i in range(len(result)):
            ego = box(
                positions_x[i] - rear_overhang,
                positions_y[i] - ego_width / 2,
                positions_x[i] + ego_wheelbase + ego_front_overhang,
                positions_y[i] + ego_width / 2,
            )
            rotated_target = affinity.rotate(
                ego, heading_angle[i] / math.pi * 180, origin=(positions_x[i], positions_y[i])
            )
            result[i] = difference(rotated_target, maneuvering_area).area == 0
            x_t, y_t = rotated_target.exterior.xy
            target_boxes.append((list(x_t), list(y_t)))
            m_a_multiple.append((list(m_a_x), list(m_a_y)))

        return result, m_a_multiple, target_boxes

    def create_slider_graph(target_boxes=(), wz_polygons=(), timestamps=()):
        """
        Creating a 2D plot for two polygons in the function of time.

        Args:
            target_boxes (list): The dynamic object exterior points in a list for each measured time instance.
            wz_polygons (list): The maneuvering area exterior points in a list for each measured time instance.
            timestamps (list): Optional, desired timestamps for each measured time instance. If not given, indexes will be used.

        Returns:
            plotly.graph_object: A plot of two dynamic object with a slider to look for multiple time instances of the scenario.
        """
        plt = go.Figure()

        x_s = []
        y_s = []
        steps = []
        for i_, target in enumerate(target_boxes):
            t_x, t_y = target
            wz_x, wz_y = wz_polygons[i_]
            x_s += t_x + wz_x
            y_s += t_y + wz_y

            plt.add_trace(
                go.Scatter(
                    visible=False,
                    x=t_x,
                    y=t_y,
                    name="EGO",
                    # fillcolor='red',
                    line=dict(color="red", width=1),
                    fill="toself",
                    mode="lines",
                    # opacity=0.5
                )
            )

            plt.add_trace(
                go.Scatter(
                    visible=False,
                    x=wz_x,
                    y=wz_y,
                    name="MANEUVERING AREA",
                    # fillcolor='blue',
                    line=dict(color="blue", width=1),
                    fill="toself",
                    mode="lines",
                    # opacity=0.5
                )
            )

            step = dict(
                method="update",
                args=[{"visible": [False] * len(target_boxes) * 2}],
                label=f"{round(timestamps[i_], 2)} s" if len(timestamps) else f"{i_}",
            )
            step["args"][0]["visible"][i_ * 2] = True
            step["args"][0]["visible"][i_ * 2 + 1] = True

            steps.append(step)

        x_s = list(set(x_s))
        if None in x_s:
            x_s.remove(None)
        y_s = list(set(y_s))
        if None in y_s:
            y_s.remove(None)

        plt.data[0].visible = True
        plt.data[1].visible = True

        sliders = [
            dict(
                active=0,
                currentvalue={"prefix": "timestamp: " if len(timestamps) else "index: "},
                pad={"t": 50},
                steps=steps,
            )
        ]

        plt.update_layout(
            sliders=sliders,
            yaxis_range=[min(y_s) - 1, max(y_s) + 1],
            xaxis_range=[min(x_s) - 1, max(x_s) + 1],
        )
        return plt


class MoCoStatusSignals(SignalDefinition):
    """Example signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        MF_VEHICLE_Parameter = "MF_VEHICLE_Parameter_eSigStatus"
        IuTRJCTLGeneralInputPort = "IuTRJCTLGeneralInputPort_eSigStatus"
        IuTrajRequestPort = "IuTrajRequestPort_eSigStatus"
        MF_SYS_FUNC_Parameter = "MF_SYS_FUNC_Parameter_eSigStatus"
        IuOdoEstimationPort = "IuOdoEstimationPor_eSigStatus"
        MF_FC_TRJCTL_Parameter = "MF_FC_TRJCTL_Parameter_eSigStatus"
        IuLoDMCStatusPort = "IuLoDMCStatusPort_eSigStatus"
        IuLoCtrlRequestPort = "IuLoCtrlRequestPort_eSigStatus"
        IuLaDMCStatusPort = "IuLaDMCStatusPort_eSigStatus"
        IuLaCtrlRequestPort = "IuLaCtrlRequestPort_eSigStatus"
        IuGearboxCtrlStatusPort = "IuGearboxCtrlStatusPort_eSigStatus"
        IuGearboxCtrlRequestPort = "IuGearboxCtrlRequestPort_eSigStatus"
        IuLoDMCCtrlRequestPort = "IuLoDMCCtrlRequestPort_eSigStatus"
        IuLaDMCCtrlRequestPort = "IuLaDMCCtrlRequestPort_eSigStatus"
        IuMfControlStatusPort = "IuMfControlStatusPort_eSigStatus"
        IuDrivingResistancePort = "IuDrivingResistancePort_eSigStatus"
        IuTrajCtrlDebugPort = "IuTrajCtrlDebugPort_eSigStatus"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = [
            "AP",
        ]

        self._properties = {
            (self.Columns.MF_VEHICLE_Parameter, ".mfControlConfig.vehicleParams.sSigHeader.eSigStatus"),
            (self.Columns.IuTRJCTLGeneralInputPort, ".trjctlGeneralInputPort.sSigHeader.eSigStatus"),
            (self.Columns.IuTrajRequestPort, ".trajRequestPort.sSigHeader.eSigStatus"),
            (self.Columns.MF_SYS_FUNC_Parameter, ".mfControlConfig.sysFuncParams.sSigHeader.eSigStatus"),
            (self.Columns.IuOdoEstimationPort, ".odoEstimationPort.sSigHeader.eSigStatus"),
            (self.Columns.MF_FC_TRJCTL_Parameter, ".mfControlConfig.mfcParams.sSigHeader.eSigStatus"),
            (self.Columns.IuLoDMCStatusPort, ".LoDMCStatusPort.sSigHeader.eSigStatus"),
            (self.Columns.IuLoCtrlRequestPort, ".loCtrlRequestPort.sSigHeader.eSigStatus"),
            (self.Columns.IuLaDMCStatusPort, ".LaDMCStatusPort.sSigHeader.eSigStatus"),
            (self.Columns.IuLaCtrlRequestPort, ".laCtrlRequestPort.sSigHeader.eSigStatus"),
            (self.Columns.IuGearboxCtrlStatusPort, ".gearboxCtrlStatusPort.sSigHeader.eSigStatus"),
            (self.Columns.IuGearboxCtrlRequestPort, ".IuGearboxCtrlRequestPort.sSigHeader.eSigStatus"),
            (self.Columns.IuLoDMCCtrlRequestPort, ".LoDMCCtrlRequestPort.sSigHeader.eSigStatus"),
            (self.Columns.IuLaDMCCtrlRequestPort, ".IuLaDMCCtrlRequestPort.sSigHeader.eSigStatus"),
            (self.Columns.IuMfControlStatusPort, ".mfControlStatusPort.sSigHeader.eSigStatus"),
            (self.Columns.IuDrivingResistancePort, ".DrivingResistancePort.sSigHeader.eSigStatus"),
            (self.Columns.IuTrajCtrlDebugPort, ".IuTrajCtrlDebugPort.sSigHeader.eSigStatus"),
        }


class MoCoSignals(SignalDefinition):
    """Example signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        activateLaCtrl = "activateLaCtrl"
        laDMCCtrlRequest_nu = "laDMCCtrlRequest_nu"
        frontSteerAngReq_rad = "frontSteerAngReq_rad"
        activateLoCtrl = "activateLoCtrl"
        loDMCCtrlRequest_nu = "loDMCCtrlRequest_nu"
        gearboxCtrlRequest_nu = "gearboxCtrlRequest_nu"
        holdReq_nu = "holdReq_nu"
        maneuveringFinished_nu = "maneuveringFinished_nu"
        gearCur_nu = "gearCur_nu"
        comfortStopRequest = "comfortStopRequest"
        requestedValue = "requestedValue"
        secureInStandstill = "secureInStandstill"
        standstillHoldCur_nu = "standstillHoldCur_nu"
        standstillSecureCur_nu = "standstillSecureCur_nu"
        loCtrlRequestType = "loCtrlRequestType"
        laCtrlRequestType = "laCtrlRequestType"
        steerAngFrontAxle_rad = "steerAngFrontAxle_rad"
        motionStatus_nu = "motionStatus_nu"
        trajValid_nu = "trajValid_nu"
        xPosition_m = "xPosition_m"
        yPosition_m = "yPosition_m"
        yawAngle_rad = "yawAngle_rad"
        currentDeviation_m = "currentDeviation_m"
        orientationError_rad = "orientationError_rad"
        distance_interface = "distance_interface"
        velocity_interface = "velocity_interface"
        acceleration_interface = "acceleration_interface"
        drivingForwardReq_nu = "drivingForwardReq_nu"
        TimeStamp = "TimeStamp"

        xTrajRAReq_m_0 = "xTrajRAReq_m_0"
        yTrajRAReq_m_0 = "yTrajRAReq_m_0"
        yawReq_rad_0 = "yawReq_rad_0"
        crvRAReq_1pm = "crvRAReq_1pm"
        distanceToStopReq_m_0 = "distanceToStopReq_m_0"
        velocityLimitReq_mps_0 = "velocityLimitReq_mps_0"
        xTrajRAReq_m_1 = "xTrajRAReq_m_1"
        yTrajRAReq_m_1 = "yTrajRAReq_m_1"
        yawReq_rad_1 = "yawReq_rad_1"
        distanceToStopReq_m_1 = "distanceToStopReq_m_1"
        velocityLimitReq_mps_1 = "velocityLimitReq_mps_1"
        xTrajRAReq_m_2 = "xTrajRAReq_m_2"
        yTrajRAReq_m_2 = "yTrajRAReq_m_2"
        yawReq_rad_2 = "yawReq_rad_2"
        distanceToStopReq_m_2 = "distanceToStopReq_m_2"
        velocityLimitReq_mps_2 = "velocityLimitReq_mps_2"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = [
            "AP",
        ]

        self._properties = {
            (self.Columns.activateLaCtrl, ".laCtrlRequestPort.activateLaCtrl"),
            (self.Columns.laDMCCtrlRequest_nu, ".laDMCCtrlRequestPort.laDMCCtrlRequest_nu"),
            (self.Columns.frontSteerAngReq_rad, ".laDMCCtrlRequestPort.frontSteerAngReq_rad"),
            (self.Columns.activateLoCtrl, ".loCtrlRequestPort.activateLoCtrl"),
            (self.Columns.loDMCCtrlRequest_nu, ".LoDMCCtrlRequestPort.loDMCCtrlRequest_nu"),
            (self.Columns.gearboxCtrlRequest_nu, ".gearBoxCtrlRequestPort.gearboxCtrlRequest_nu"),
            (self.Columns.holdReq_nu, ".LoDMCCtrlRequestPort.holdReq_nu"),
            (self.Columns.maneuveringFinished_nu, ".LoDMCStatusPort.maneuveringFinished_nu"),
            (self.Columns.gearCur_nu, ".gearboxCtrlStatusPort.gearInformation.gearCur_nu"),
            (self.Columns.currentDeviation_m, ".trajCtrlDebugPort.currentDeviation_m"),
            (self.Columns.comfortStopRequest, ".loCtrlRequestPort.comfortStopRequest"),
            (self.Columns.requestedValue, ".loCtrlRequestPort.distanceToStopReq_m.requestedValue"),
            (self.Columns.secureInStandstill, ".loCtrlRequestPort.secureInStandstill"),
            (self.Columns.standstillHoldCur_nu, ".LoDMCStatusPort.standstillHoldCur_nu"),
            (self.Columns.standstillSecureCur_nu, ".LoDMCStatusPort.standstillSecureCur_nu"),
            (self.Columns.loCtrlRequestType, ".loCtrlRequestPort.loCtrlRequestType"),
            (self.Columns.laCtrlRequestType, ".laCtrlRequestPort.laCtrlRequestType"),
            (self.Columns.steerAngFrontAxle_rad, ".odoEstimationPort.steerAngFrontAxle_rad"),
            (self.Columns.motionStatus_nu, ".odoEstimationPort.motionStatus_nu"),
            (self.Columns.trajValid_nu, ".trajRequestPort.trajValid_nu"),
            (self.Columns.xPosition_m, ".odoEstimationPort.xPosition_m"),
            (self.Columns.yPosition_m, ".odoEstimationPort.yPosition_m"),
            (self.Columns.yawAngle_rad, ".odoEstimationPort.yawAngle_rad"),
            (self.Columns.orientationError_rad, ".trajCtrlDebugPort.orientationError_rad"),
            (self.Columns.distance_interface, ".loCtrlRequestPort.distanceToStopReq_m.drivingDirRequest"),
            (self.Columns.velocity_interface, ".loCtrlRequestPort.velocityReq_mps.drivingDirRequest"),
            (self.Columns.acceleration_interface, ".loCtrlRequestPort.accelerationReq_mps2.drivingDirRequest"),
            (self.Columns.drivingForwardReq_nu, ".trajRequestPort.drivingForwardReq_nu"),
            # (self.Columns.TimeStamp, "odoInputPort.odoSystemTimePort.timestamp_us"),
            (self.Columns.TimeStamp, ".odoInputPort.odoSigFcanPort.vehDynamics.timestamp_us"),
            (self.Columns.xTrajRAReq_m_0, ".plannedTrajPort.plannedTraj_0.xTrajRAReq_m"),
            (self.Columns.yTrajRAReq_m_0, ".plannedTrajPort.plannedTraj_0.yTrajRAReq_m"),
            (self.Columns.yawReq_rad_0, ".plannedTrajPort.plannedTraj_0.yawReq_rad"),
            (self.Columns.crvRAReq_1pm, ".plannedTrajDrivenPoint.crvRAReq_1pm"),
            (self.Columns.distanceToStopReq_m_0, ".plannedTrajPort.plannedTraj_0.distanceToStopReq_m"),
            (self.Columns.velocityLimitReq_mps_0, ".plannedTrajPort.plannedTraj_0.velocityLimitReq_mps"),
            (self.Columns.xTrajRAReq_m_1, ".plannedTrajPort.plannedTraj_1.xTrajRAReq_m"),
            (self.Columns.yTrajRAReq_m_1, ".plannedTrajPort.plannedTraj_1.yTrajRAReq_m"),
            (self.Columns.yawReq_rad_1, ".plannedTrajPort.plannedTraj_1.yawReq_rad"),
            (self.Columns.distanceToStopReq_m_1, ".plannedTrajPort.plannedTraj_1.distanceToStopReq_m"),
            (self.Columns.velocityLimitReq_mps_1, ".plannedTrajPort.plannedTraj_1.velocityLimitReq_mps"),
            (self.Columns.xTrajRAReq_m_2, ".plannedTrajPort.plannedTraj_2.xTrajRAReq_m"),
            (self.Columns.yTrajRAReq_m_2, ".plannedTrajPort.plannedTraj_2.yTrajRAReq_m"),
            (self.Columns.yawReq_rad_2, ".plannedTrajPort.plannedTraj_2.yawReq_rad"),
            (self.Columns.distanceToStopReq_m_2, ".plannedTrajPort.plannedTraj_2.distanceToStopReq_m"),
            (self.Columns.velocityLimitReq_mps_2, ".plannedTrajPort.plannedTraj_2.velocityLimitReq_mps"),
        }


class MOCOCustomTeststepReport(CustomReportTestStep):
    """Custom test step report for MOCO."""

    def overview(
        self,
        processing_details_list: ProcessingResultsList,
        teststep_result: List["TeststepResult"],
    ):
        """
        Generate overview for MOCO custom test step report.

        Args:
            processing_details_list (ProcessingResultsList): List of processing details.
            teststep_result (List["TeststepResult"]): List of test step results.

        Returns:
            str: HTML content representing the overview.
        """
        s = ""

        # pr_list = processing_details_list
        s += "<br>"
        s += "<br>"

        return s

    def details(self, processing_details: ProcessingResult, teststep_result: "TeststepResult") -> str:
        """Generate details of the test step report.

        Args:
            processing_details (ProcessingResult): Processing results.
            teststep_result (TeststepResult): Test step result.

        Returns:
            str: Details of the test step report.
        """
        s = "<br>"
        # color = ""
        m_res = teststep_result.measured_result
        e_res = teststep_result.teststep_definition.expected_results[None]
        (
            _,
            status,
        ) = e_res.compute_result_status(m_res)
        verdict = status.key.lower()

        if "data nok" in verdict:
            verdict = fc.NOT_ASSESSED

        s += (
            f'<span align="center" style="width: 100%; height: 100%; display: block;background-color: {get_color(verdict)}; '
            f'color : #ffffff">Step result: {verdict.upper()}</span>'
        )

        for k, v in processing_details.details.items():
            if "Plots" in k:
                s += "<div>"
                for plot in v:
                    s += plot
                s += "</div>"

        return s


class MOCOCustomTestCase(CustomReportTestCase):
    """Custom test case report for MOCO."""

    def __init__(self):
        """Initialize the report."""
        super().__init__()
        self.results = None
        self.result_dict = {}
        self.result_list = []
        self.anchor_list = []
        self.start_time = None

    def on_result(self, pr_details: ProcessingResult, ts_result: TeststepResult):
        """Process the test step result.

        Args:
            pr_details (ProcessingResult): Processing details.
            ts_result (TeststepResult): Test step result.
        """
        if "Processing_time" in pr_details and self.start_time is None:
            self.start_time = pr_details["Processing_time"]
        # self._env.testrun.testcase_results
        if "Additional_results" in pr_details:
            a = {"Measurement": pr_details["file_name"]}

            a.update(pr_details["Additional_results"])
            self.result_list.append(a)
            self.anchor_list.append(
                f'"../teststeps_details/{ts_result.teststep_definition.id}_details_for_{ts_result.test_input.id}.html"'
            )

    def overview(self):
        """Generate an overview of the test case report.

        Returns:
            str: Overview of the test case report.
        """
        results_dict = {
            fc.PASS.title(): 0,
            fc.FAIL.title(): 0,
            fc.INPUT_MISSING.title(): 0,
            fc.NOT_ASSESSED.title(): 0,
        }

        s = ""
        if self.start_time is not None:
            process_time = time.time() - self.start_time
            process_time = time.strftime("%M:%S", time.gmtime(process_time))
            s += "<h4> Processing time</h4>"
            s += f"<h5>{process_time} seconds</h5>"
            s += "<br>"
        try:
            columns = []
            row_events = []
            for r in self.result_list:
                columns.extend(list(r.keys()))
                break

            for d in self.result_list:
                r = []
                for c in columns:
                    if c in d:
                        v = d[c]
                        if isinstance(v, dict):
                            if "color" in v:
                                r.append(
                                    str(
                                        f"""<span align="center" style="width: 100%; height: 100%; display: block;background-color: {v['color']}; color : #ffffff">{v['value']}</span>"""
                                    )
                                )
                            else:
                                r.append(
                                    str(
                                        f"""<span align="center" style="width: 100%; height: 100%; display: block">{v['value']}</span>"""
                                    )
                                )
                        elif "Measurement" in c:
                            # r.append(v)
                            r.append(
                                str(
                                    f"""<span align="center" style="background-color: {d['Verdict']['color']}; color : #ffffff">{v}</span>"""
                                )
                            )

                            try:
                                results_dict[d["Verdict"]["value"]] += 1
                            except Exception as e:
                                print(str(e))
                        else:
                            r.append(v)

                    else:
                        r.append("")
                row_events.append(r)
            # for index in range(len(row_events)):

            #     row_events[index][0] = str(
            #         f"""<a href={self.anchor_list[index]}>{row_events[index][0]}</a>""")

            column_names = [{"title": str(c)} for c in columns]
            additional_tables = (
                """
        <h2>Additional Information</h2>
<script>
var table_column_names = """
                + dumps(column_names)
                + """;
var table_rows_events =  """
                + dumps(row_events)
                + """
$(document).ready(function() {
$('#events_table').DataTable( {
paging:    true,
searching: true,
info:      true,
scrollX: true,
ordering: true,
data: table_rows_events,
columns: table_column_names
} );
});
</script>
<table class="table-sm table-striped compact nowrap" id="events_table">
<caption>Table: Additional Information</caption>
</table>
"""
            )
            s += "<h4>Overview results</h4>"
            s += "<br>"
            s += f"<h6>Passed: {results_dict[fc.PASS.title()]}</h6>"
            s += f"<h6>Failed: {results_dict[fc.FAIL.title()]}</h6>"
            s += f"<h6>Input missing: {results_dict[fc.INPUT_MISSING.title()]}</h6>"
            s += f"<h6>Not assessed: {results_dict[fc.NOT_ASSESSED.title()]}</h6>"
            s += "<br>"
            s += additional_tables

        except Exception as ex:
            # Handle other exceptions
            print({ex})
            s += "<h6>No additional info available</h6>"
        return s


def highlight_segments(fig, signal, state, time, fillcolor, annotation_text):
    """
    Highlight continuous segments of a specified state on a Plotly figure.

    Parameters:
    fig (plotly.graph_objects.Figure): The Plotly figure to which the vertical rectangles will be added.
    signal (pd.Series): The signal indicating different states.
    state (int): The specific state to highlight.
    time (pd.Series): The time signal corresponding to the states.
    fillcolor (str): The color to fill the rectangles.
    annotation_text (str): The text to annotate the rectangles.

    Returns:
    None
    """
    scanning = []
    start_scan = None
    for idx in range(len(signal)):
        if signal.iat[idx] == state:
            if start_scan is None:
                start_scan = time.iat[idx]
            end = time.iat[idx]
        else:
            if start_scan is not None:
                scanning.append([start_scan, end])
                start_scan = None
    if start_scan is not None:
        scanning.append([start_scan, end])

    for segment in scanning:
        fig.add_vrect(
            x0=segment[0],
            x1=segment[1],
            fillcolor=fillcolor,
            line_width=0,
            opacity=0.5,
            annotation_text=annotation_text,
            layer="below",
        )


def get_status_label(value, constants_class):
    """
    Get the status label for a given value by comparing it with a class of constants.

    Parameters:
    value (int): The value to be checked against the constants.
    constants_class (class): The class containing constant attributes.

    Returns:
    str: The name of the constant if a match is found, otherwise "UNKNOWN".
    """
    for attr in dir(constants_class):
        if not callable(getattr(constants_class, attr)) and not attr.startswith("__"):
            if getattr(constants_class, attr) == value:
                return attr
    return "UNKNOWN"
