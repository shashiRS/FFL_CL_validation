"""
General utility for framework functionalities like signal definition,
function addition, and table overview customization.
"""

import functools
import logging
import math
import os
import re
import sys
import time
import traceback
import warnings
from copy import deepcopy
from json import dumps
from typing import List

import jinja2
import pandas as pd
import plotly.graph_objects as go
from shapely import LineString, Point, Polygon, affinity, box, difference
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
from tsf.io.mdf import MDFSignalDefinition
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


class RegressionTestsStagesCustomOverview(CustomReportStatistics):
    """
    Custom statistics overview generator.

    This class generates a customized overview of statistics. It handles the processing
    of test results and generates an HTML table with detailed information about test steps, files, and
    their corresponding results. Additionally, it saves relevant data and configurations into files for
    further analysis.
    """

    name = "Statistics Report for Regression Tests Stages"

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
        for tcr in self.environment.testrun.testcase_results:

            for result in tcr.teststep_results:
                results = list(self.processing_details_for(result.teststep_definition))
                if result.teststep_definition.name not in result_dict:
                    result_dict[result.teststep_definition.name] = {}
                for file in results:
                    result_dict[result.teststep_definition.name][file["file_name"].lower()] = (
                        file["file_name"],
                        file["Result_ratio"],
                    )
            for _ in range(len(tcr.testcase_definition.teststep_definitions)):
                l.append(
                    str(
                        f'<a href="../testcases/tc_{tcr.testcase_definition.id}.html" style="text-align:center; display:block">{tcr.testcase_definition.name}</a>'
                    )
                )  #
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
                    ratio = "n/a"
                elif "n/a" in verdict or "not assessed" in verdict:
                    verdict = "n/a"
                    ratio = "n/a"
                else:
                    ratio = f"{result_dict[result.teststep_definition.name][result.collection_entry.name][1]} %"

                test_step_name_linked = str(
                    f'<a href="../teststeps/tc_{tcr.testcase_definition.id}_ts_{result.teststep_definition.id}.html" style="text-align:center; display:block">{result.teststep_definition.name}</a>'
                )
                file_name = result.collection_entry.name
                file_name = result_dict[result.teststep_definition.name][result.collection_entry.name][0]

                step_file_result = str(
                    f"""<a href="../teststeps_details/{result.teststep_definition.id}_details_for_{result.collection_entry.id}.html" align="center" style="width: 100%; height: 100%; display: block;background-color: {get_color(verdict)}; color: #ffffff">{verdict}<br>({ratio})</a>"""
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
                if "<td>NaN</td>" in html[i]:
                    bg_col = '<td><a href="" align="center" style="width: 100%; height: 100%; display: block;background-color: #ffffff; color: #ffffff"> </a></td>'
                    html_new.append(bg_col)
                else:
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
        for tcr in self.environment.testrun.testcase_results:

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
                    verdict = "data nok"
                elif "n/a" in verdict or "not assessed" in verdict:
                    verdict = "n/a"

                test_step_name_linked = str(
                    f'<a href="../teststeps/tc_{tcr.testcase_definition_id}_ts_{result.teststep_definition.id}.html" style="text-align:center; display:block">{result.teststep_definition.name}</a>'
                )
                file_name = result.collection_entry.name
                file_name = result_dict[result.teststep_definition.name][result.collection_entry.name]
                step_file_result = str(
                    f"""<a href="../teststeps_details/{result.teststep_definition.id}_details_for_{result.collection_entry.id}.html" align="center" style="width: 100%; height: 100%; display: block;background-color: {get_color(verdict)}; color: #ffffff">{verdict}</a>"""
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
                if "<td>NaN</td>" in html[i]:
                    bg_col = '<td><a href="" align="center" style="width: 100%; height: 100%; display: block;background-color: #ffffff; color: #ffffff"> </a></td>'
                    html_new.append(bg_col)
                else:
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


class RegressionStageStatistics(Statistics):
    """Generates statistics report with custom overview."""

    custom_report = RegressionTestsStagesCustomOverview

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
        project_name = self.environment.testrun.subject_under_test.project.name
        try:
            software_version = self.environment.testrun.subject_under_test.name
        except AttributeError:
            software_version = "No software version provided"
        try:
            project_name = self.environment.testrun.subject_under_test.project.name
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
        for tcr in self.environment.testrun.testcase_results:
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

                    if "data nok" in verdict:
                        verdict = fc.NOT_ASSESSED
                    elif "n/a" in verdict or "not assessed" in verdict:
                        verdict = "n/a"

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
                        f'<a href="../{path_to_report}/teststeps_details/{result.teststep_definition.id}_details_for_{result.collection_entry.id}.html" align="center" style="width: 100%; height: 100%; display: block;background-color: {get_color(verdict)}; color: #ffffff">{verdict}</a>'
                    )
                    step_file_result = str(
                        f'<a href="../teststeps_details/{result.teststep_definition.id}_details_for_{result.collection_entry.id}.html" align="center" style="width: 100%; height: 100%; display: block;background-color: {get_color(verdict)}; color: #ffffff">{verdict}</a>'
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
        project_name = self.environment.testrun.subject_under_test.project.name
        try:
            software_version = self.environment.testrun.subject_under_test.name
        except AttributeError:
            software_version = "No software version provided"
        try:
            project_name = self.environment.testrun.subject_under_test.project.name
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
        for tcr in self.environment.testrun.testcase_results:
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
                        f'<a href="../{path_to_report}/teststeps_details/{result.teststep_definition.id}_details_for_{result.collection_entry.id}.html" align="center" style="width: 100%; height: 100%; display: block;background-color: {get_color(verdict)}; color: #ffffff">{verdict}</a>'
                    )
                    step_file_result = str(
                        f'<a href="../teststeps_details/{result.teststep_definition.id}_details_for_{result.collection_entry.id}.html" align="center" style="width: 100%; height: 100%; display: block;background-color: {get_color(verdict)}; color: #ffffff">{verdict}</a>'
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
        for tcr in self.environment.testrun.testcase_results:
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
                        f"""<a href="../teststeps_details/{result.teststep_definition.id}_details_for_{result.collection_entry.id}.html" align="center" style="width: 100%; height: 100%; display: block;background-color: {get_color(verdict)}; color: #ffffff">{verdict}</a>"""
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


# @statistics_definition(name="RootCause", description="Root cause analysis statistics")
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

        # os.path.abspath(os.path.join(__file__, "..", ".."))
        for tcr in self.environment.testrun.testcase_results:
            if "Root" in tcr.testcase_definition.name or "Output" in tcr.testcase_definition.name:
                for result in tcr.teststep_results:
                    results = list(self.processing_details_for(result.teststep_definition))
                    if result.teststep_definition.name not in result_dict:
                        result_dict[result.teststep_definition.name] = {}
                    for file in results:
                        result_dict[result.teststep_definition.name][file["file_name"].lower()] = file["file_name"]
        # jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(TSF_BASE, "templates")))
        jinja_env = jinja2.Environment()
        for tcr in self.environment.testrun.testcase_results:
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
                        f"../teststeps_details/{result.teststep_definition.id}_details_for_{result.input.id}.html"
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

        # template = jinja_env.get_template("root_cause_template.html")
        template_string = """ <div class="table-container">
        <table border="1" class="dataframe table table-hover height:500px">
        <thead class= "sticky-top" id = "myHeader">
            <tr>
            <th style="min-width: 100px;"></th>
            {% for step in stp_list %}
            <th colspan="2" halign="left"style="min-width: 100px;"><a href="" style="text-align:center; display:block">{{ step }}</a></th>
            {% endfor %}
            </tr>
            <tr>
            <th style="min-width: 100px;"></th>
            {% for link, step_name in cs_dict.items() %}
            <th style="min-width: 100px;"><a href="{{ link }}" style="text-align:center; display:block">{{step_name}}</a></th>
            {% endfor %}
            </tr>
        </thead>
        <tbody>
                {% for key, value in data.items() %}
            <tr>
            <th>{{ key }}</th>
                {% for sub_key, sub_value in value.items() %}
                {% for sub_sub_key, sub_sub_value in sub_value.items() %}
                    {% for sub_sub_sub_key, sub_sub_sub_value in sub_sub_value.items() %}
                    <td bgcolor="{{ sub_sub_sub_value.color }}"style="text-align: center;"><a href="{{sub_sub_sub_value.link}}" style="text-align:center; width: 100%; height: 100%; color: #ffffff">{{ sub_sub_sub_value.verdict }}</a></td>
                {% endfor %}
                {% endfor %}
                {% endfor %}
            </tr>
                {% endfor %}
        </tbody>
        </table>
        </div>
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
        template = jinja_env.from_string(template_string)

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


# class AupKPIStatistics(CustomReportStatistics):
#     """
#     Generates statistics for AUP Key Performance Indicators (KPIs).

#     This class generates statistics focusing on AUP Key Performance Indicators (KPIs).
#     It processes test results to extract relevant data for each KPI and presents them in an HTML format.

#     """

#     name = "AUP KPI statistics"

#     def overview(self) -> str:
#         """
#         Generates an overview of AUP KPI statistics.

#         This method processes test results to extract relevant data for each AUP KPI and presents them
#         in an HTML format. It integrates Jinja2 templating for rendering the HTML output.

#         Returns:
#             str: HTML-formatted overview of AUP KPI statistics.
#         """
#         from collections import defaultdict

#         import pandas as pd

#         test_case_name_list = []

#         d = defaultdict(dict)  # noqa E741
#         j = defaultdict(dict)  # noqa E741
#         result_dict = defaultdict(dict)
#         usecase_dict = defaultdict(dict)

#         usecase_dict = {key: {} for key in constants.ParkingUseCases.parking_usecase_id.keys()}
#         TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
#         for tcr in self.environment.testrun.testcase_results:
#             test_case_name_list.append(
#                 str(
#                     f'<a href="../testcases/tc_{tcr.testcase_definition_id}.html" style="text-align:center; display:block">{tcr.testcase_definition.name}</a>'
#                 )
#             )
#             for result in tcr.teststep_results:
#                 results = list(self.processing_details_for(result.teststep_definition))
#                 if result.teststep_definition.name not in result_dict:
#                     result_dict[result.teststep_definition.name] = {}
#                 for file in results:
#                     result_dict[result.teststep_definition.name][file["file_name"].lower()] = file["file_name"]
#                     for use_case_id in constants.ParkingUseCases.parking_usecase_id.keys():
#                         if use_case_id.lower() in file["file_name"].lower():
#                             usecase_dict[use_case_id].update({file["file_name"]: {}})
#         usecase_dict = {key: val for key, val in usecase_dict.items() if key and val}
#         jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(TSF_BASE,"templates")))
#         l = []  # noqa E741
#         color_verdict = []
#         for tcr in self.environment.testrun.testcase_results:

#             for result in tcr.teststep_results:
#                 results = list(self.processing_details_for(result.teststep_definition))
#                 if result.teststep_definition.name not in result_dict:
#                     result_dict[result.teststep_definition.name] = {}
#                 for file in results:
#                     result_dict[result.teststep_definition.name][file["file_name"].lower()] = file["file_name"]
#             for _ in range(len(tcr.testcase_definition.teststep_definitions)):
#                 l.append(
#                     str(
#                         f'<a href="../testcases/tc_{tcr.testcase_definition_id}.html" style="text-align:center; display:block">{tcr.testcase_definition.name}</a>'
#                     )
#                 )
#             for result in tcr.teststep_results:

#                 m_res = result.measured_result
#                 e_res = result.teststep_definition.expected_results[None]
#                 (
#                     _,
#                     status,
#                 ) = e_res.compute_result_status(m_res)
#                 verdict = status.key.lower()
#                 if tcr.testcase_definition.name.lower() in [
#                     "average maneuvering time [s]",
#                     "number of average strokes",
#                 ]:
#                     if "failed" in verdict:
#                         verdict = result.measured_result.as_dict["numerator"]
#                     elif "data nok" in verdict:
#                         verdict = fc.NOT_ASSESSED
#                     elif "passed" in verdict:
#                         verdict = result.measured_result.as_dict["numerator"]

#                 else:
#                     if "data nok" in verdict:
#                         verdict = fc.NOT_ASSESSED

#                 test_step_name_linked = str(
#                     f'<a href="../teststeps/tc_{tcr.testcase_definition_id}_ts_{result.teststep_definition.id}.html" style="text-align:center; display:block">{result.teststep_definition.name}</a>'
#                 )
#                 file_name = result.collection_entry.name
#                 file_name = result_dict[result.teststep_definition.name][result.collection_entry.name]
#                 step_file_result = str(
#                     f"""<td bgcolor="{get_color(verdict)}"style="text-align: center;"><a href="../teststeps_details/{result.teststep_definition.id}_details_for_{result.test_input.id}.html" align="center" style="width: 100%; height: 100%; display: block;background-color: {get_color(verdict)}; color: #ffffff">{verdict}</a></td>"""
#                 )
#                 d[test_step_name_linked][file_name] = step_file_result
#                 color_verdict.append(get_color(verdict))

#                 j[file_name][tcr.testcase_definition.name] = {"Result": verdict}

#         import json

#         with open(os.path.join(self.environment.output_folder, "functional_test_results.json"), "w") as outfile:
#             json.dump(j, outfile, indent=4)

#         s = pd.DataFrame(d)

#         s.columns = pd.MultiIndex.from_tuples(zip(l, s.columns))

#         pd.set_option("display.max_colwidth", None)
#         html = s.to_html(classes="table table-hover height:500px", escape=False, col_space=100)

#         html = html.split("\n")
#         html_new = []

#         for i in range(len(html)):
#             if "<td>" not in html[i]:
#                 html_new.append(html[i])

#             elif "<td>" in html[i]:
#                 bg_col = (html[i].split(";background-color: ")[-1]).split("; color:")[0]

#                 html_new.append(html[i].replace("<td>", f"<td bgcolor={bg_col}>"))
#         html_new_str = "\n".join(html_new)
#         html_new_str = html_new_str.replace("<thead>", '<thead class= "sticky-top" id = "myHeader">')

#         new_df = defaultdict(dict)
#         step_percentage = defaultdict(dict)
#         for use_id in usecase_dict.keys():
#             new_df[use_id] = {}
#             for meas in usecase_dict[use_id]:
#                 if meas not in new_df[use_id]:
#                     new_df[use_id][meas] = {}
#                 new_df[use_id][meas] = list(s.loc[meas].values)

#         for key in new_df.keys():
#             step_percentage[key] = []
#             list_of_meas = list(new_df[key].keys())
#             number_of_columns = len(new_df[key][list_of_meas[0]])
#             for column in range(number_of_columns):
#                 pass_count = 0
#                 avg_count = 0
#                 meas_count = 0
#                 fail_count = 0
#                 for meas in list_of_meas:
#                     if "passed" in new_df[key][meas][column]:
#                         pass_count += 1
#                     elif "failed" in new_df[key][meas][column]:
#                         fail_count += 1
#                     elif "n/a" in new_df[key][meas][column]:
#                         pass
#                     elif fc.NOT_ASSESSED in new_df[key][meas][column]:
#                         pass
#                     else:
#                         extract_txt = new_df[key][meas][column].split('; color: #ffffff">')[-1]
#                         extract_txt = extract_txt.replace("</a></td>", "")

#                         avg_count += float(extract_txt)
#                         meas_count += 1

#                 total = pass_count + fail_count
#                 if meas_count > 0:
#                     percent = avg_count / meas_count
#                     percent = f"{percent:.2f}"
#                 elif total == 0:
#                     # percent =0
#                     percent = "N/A"
#                 else:
#                     percent = (pass_count / total) * 100
#                     percent = f"{percent:.2f} %"
#                 step_percentage[key].append(percent)

#         table_header = html_new_str.split("</thead>")[0] + "</thead>"

#         template = jinja_env.get_template("aup_table_template.html")

#         html = template.render(
#             data=new_df,
#             usecases=step_percentage,
#             thead=table_header,
#         )


#         return '<div style="overflow: auto; position: relative;">' + html + "</div>"
@staticmethod
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
        for tcr in self.environment.testrun.testcase_results:
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
                    result_dict[result.teststep_definition.name][file["file_path"].lower()] = file["file_path"]
                    match = re.search(r"AP_UC_\d{3}", file["file_path"])
                    if match:
                        use_case_id = match.group()
                        if use_case_id in usecase_dict:
                            usecase_dict[use_case_id].update({file["file_name"]: {}})
                        else:
                            usecase_dict[use_case_id] = {file["file_name"]: {}}
                    else:
                        usecase_dict["UNKNOWN"].update({file["file_name"]: {}})
                    # for use_case_id in constants.ParkingUseCases.parking_usecase_id.keys():
                    #     if use_case_id.lower() in file["file_path"].lower():
                    #         usecase_dict[use_case_id].update({file["file_name"]: {}})
        usecase_dict = {key: val for key, val in usecase_dict.items() if key and val}
        jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(TSF_BASE, "templates")))
        l = []  # noqa E741
        color_verdict = []
        for tcr in self.environment.testrun.testcase_results:

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
                    "average maneuvering time[s]",
                    "average number of strokes ",
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
                    if "failed" in verdict:
                        verdict = fc.FAIL

                test_step_name_linked = str(
                    f'<a href="../teststeps/tc_{tcr.testcase_definition_id}_ts_{result.teststep_definition.id}.html" style="text-align:center; display:block">{result.teststep_definition.name}</a>'
                )
                file_name = result.collection_entry.name
                file_name = result_dict[result.teststep_definition.name][result.collection_entry.name]
                step_file_result = str(
                    f"""<td bgcolor="{get_color(verdict)}"style="text-align: center;"><a href="../teststeps_details/{result.teststep_definition.id}_details_for_{result.collection_entry.id}.html" align="center" style="width: 100%; height: 100%; display: block;background-color: {get_color(verdict)}; color: #ffffff">{verdict}</a></td>"""
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
                    if isinstance(new_df[key][meas][column], float) and math.isnan(new_df[key][meas][column]):
                        new_df[key][meas][column] = "<td >&nbsp;</td>"
                    elif "passed" in new_df[key][meas][column]:
                        pass_count += 1
                    elif "failed" in new_df[key][meas][column]:
                        fail_count += 1
                    elif "n/a" in new_df[key][meas][column]:
                        pass
                    elif fc.NOT_ASSESSED in new_df[key][meas][column]:
                        pass
                    elif "info" in new_df[key][meas][column]:
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


# class AupKPITable(Statistics):
#     """Generates AUP KPI statistics."""

#     custom_report = AupKPIStatistics


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
    else:  # NaN
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


def build_html_table(dataframe: pd.DataFrame, table_remark="", table_title="", table_id=""):
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
    if table_id:
        table_html = f'<div id="{table_id}">{table_html}<br< {table_remark}</div>'

    else:  # Wrap the table and remark in a div
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


def convert_dict_to_pandas_grappa(signal_summary: dict, table_remark="", table_title=""):  # noqa: D103
    evaluation_summary = pd.DataFrame(
        {
            "Evaluation": {key: key for key, val in signal_summary.items()},
            "Results": {key: val for key, val in signal_summary.items()},
        }
    )
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
        # self.environment.testrun.testcase_results
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
        OBJECTS_VELOCITY_X = "objects.velocity.x"
        OBJECTS_VELOCITY_Y = "objects.velocity.y"
        OBJECTS_VELOCITYSTANDARDDEVIATION_X = "objects.velocityStandardDeviation.x"
        OBJECTS_VELOCITYSTANDARDDEVIATION_Y = "objects.velocityStandardDeviation.y"
        OBJECTS_YAWRATE = "objects.yawRate"
        OBJECTS_YAWRATESTANDARDDEVIATION = "objects.yawRateStandardDeviation"
        OBJECTS_CENTER_X = "objects.center_x"  # unused in R3
        OBJECTS_CENTER_Y = "objects.center_y"  # unused in R3
        OBJECTS_LIFETIME = "objects.lifetime"
        OBJECTS_CONTAINEDINLASTSENSORUPDATE = "objects.containedInLastSensorUpdate"  # unused in R3
        OBJECTS_STATE = "objects.state"
        OBJECTS_ACCELERATION_X = "objects.acceleration.x"
        OBJECTS_ACCELERATION_Y = "objects.acceleration.y"
        OBJECTS_ACCELERATIONSTANDARDDEVIATION_X = "objects.accelerationStandardDeviation.x"
        OBJECTS_ACCELERATIONSTANDARDDEVIATION_Y = "objects.accelerationStandardDeviation.y"
        OBJECTS_SHAPE_REFERENCEPOINTX = "objects.shape.referencePoint.x"
        OBJECTS_SHAPE_REFERENCEPOINTY = "objects.shape.referencePoint.y"
        OBJECTS_SHAPE_POINTS_0__POSITION_X = "objects.shape.points[0].position.x"
        OBJECTS_SHAPE_POINTS_1__POSITION_X = "objects.shape.points[1].position.x"
        OBJECTS_SHAPE_POINTS_2__POSITION_X = "objects.shape.points[2].position.x"
        OBJECTS_SHAPE_POINTS_3__POSITION_X = "objects.shape.points[3].position.x"
        OBJECTS_SHAPE_POINTS_0__POSITION_Y = "objects.shape.points[0].position.y"
        OBJECTS_SHAPE_POINTS_1__POSITION_Y = "objects.shape.points[1].position.y"
        OBJECTS_SHAPE_POINTS_2__POSITION_Y = "objects.shape.points[2].position.y"
        OBJECTS_SHAPE_POINTS_3__POSITION_Y = "objects.shape.points[3].position.y"
        OBJECTS_SHAPE_POINTS_0__VARIANCEX = "objects.shape.points[0].varianceX"
        OBJECTS_SHAPE_POINTS_1__VARIANCEX = "objects.shape.points[1].varianceX"
        OBJECTS_SHAPE_POINTS_2__VARIANCEX = "objects.shape.points[2].varianceX"
        OBJECTS_SHAPE_POINTS_3__VARIANCEX = "objects.shape.points[3].varianceX"
        OBJECTS_SHAPE_POINTS_0__VARIANCEY = "objects.shape.points[0].varianceY"
        OBJECTS_SHAPE_POINTS_1__VARIANCEY = "objects.shape.points[1].varianceY"
        OBJECTS_SHAPE_POINTS_2__VARIANCEY = "objects.shape.points[2].varianceY"
        OBJECTS_SHAPE_POINTS_3__VARIANCEY = "objects.shape.points[3].varianceY"
        OBJECTS_SHAPE_POINTS_0__COVARIANCEXY = "objects.shape.points[0].covarianceXY"
        OBJECTS_SHAPE_POINTS_1__COVARIANCEXY = "objects.shape.points[1].covarianceXY"
        OBJECTS_SHAPE_POINTS_2__COVARIANCEXY = "objects.shape.points[2].covarianceXY"
        OBJECTS_SHAPE_POINTS_3__COVARIANCEXY = "objects.shape.points[3].covarianceXY"
        VEDODO_TIMESTAMP = "vedodo_timestamp_us"
        VEDODO_SIGSTATUS = "vedodo_signalState"
        X = "x"
        Y = "y"
        YAW = "yaw"
        VEDODO_GT_TIMESTAMP = "vedodo_gt_timestamp_us"
        VEDODO_GT_SIGSTATUS = "vedodo_gt_signalState"
        X_GT = "x_gt"
        Y_GT = "y_gt"
        YAW_GT = "yaw_gt"
        FRONT_TIMESTAMP = "Front_timestamp"
        FRONT_NUMOBJECTS = "Front_numObjects"
        # FRONT_OBJECTS_ID = "Front_objects_id"
        FRONT_OBJECTS_SIGSTATUS = "Front_objects_eSigStatus"
        FRONT_OBJECTS_CLASSTYPE = "Front_objects_classType"
        FRONT_OBJECTS_CONFIDENCE = "Front_objects_confidence"
        FRONT_OBJECTS_CENTERPOINTWORLD_X = "Front_objects_centerPointWorld.x"
        FRONT_OBJECTS_CENTERPOINTWORLD_Y = "Front_objects_centerPointWorld.y"
        FRONT_OBJECTS_CENTERPOINTWORLD_Z = "Front_objects_centerPointWorld.z"
        # FRONT_OBJECTS_PLANESIZEWORLD_X = "Front_objects_planeSizeWorld.x"
        # FRONT_OBJECTS_PLANESIZEWORLD_Y = "Front_objects_planeSizeWorld.y"
        # FRONT_OBJECTS_CUBOIDSIZEWORLD_X = "Front_objects_cuboidSizeWorld.x"
        # FRONT_OBJECTS_CUBOIDSIZEWORLD_Y = "Front_objects_cuboidSizeWorld.y"
        # FRONT_OBJECTS_CUBOIDSIZEWORLD_Z = "Front_objects_cuboidSizeWorld.z"
        FRONT_OBJECTS_CUBOIDYAWWORLD = "Front_objects_cuboidYawWorld"
        FRONT_OBJECTS_WIDTH = "Front_objects_width"
        FRONT_OBJECTS_LENGTH = "Front_objects_length"
        FRONT_OBJECTS_HEIGHT = "Front_objects_height"
        REAR_TIMESTAMP = "Rear_timestamp"
        REAR_NUMOBJECTS = "Rear_numObjects"
        # REAR_OBJECTS_ID = "Rear_objects_id"
        REAR_OBJECTS_SIGSTATUS = "Rear_objects_eSigStatus"
        REAR_OBJECTS_CLASSTYPE = "Rear_objects_classType"
        REAR_OBJECTS_CONFIDENCE = "Rear_objects_confidence"
        REAR_OBJECTS_CENTERPOINTWORLD_X = "Rear_objects_centerPointWorld.x"
        REAR_OBJECTS_CENTERPOINTWORLD_Y = "Rear_objects_centerPointWorld.y"
        REAR_OBJECTS_CENTERPOINTWORLD_Z = "Rear_objects_centerPointWorld.z"
        # REAR_OBJECTS_PLANESIZEWORLD_X = "Rear_objects_planeSizeWorld.x"
        # REAR_OBJECTS_PLANESIZEWORLD_Y = "Rear_objects_planeSizeWorld.y"
        # REAR_OBJECTS_CUBOIDSIZEWORLD_X = "Rear_objects_cuboidSizeWorld.x"
        # REAR_OBJECTS_CUBOIDSIZEWORLD_Y = "Rear_objects_cuboidSizeWorld.y"
        # REAR_OBJECTS_CUBOIDSIZEWORLD_Z = "Rear_objects_cuboidSizeWorld.z"
        REAR_OBJECTS_CUBOIDYAWWORLD = "Rear_objects_cuboidYawWorld"
        REAR_OBJECTS_WIDTH = "Rear_objects_width"
        REAR_OBJECTS_LENGTH = "Rear_objects_length"
        REAR_OBJECTS_HEIGHT = "Rear_objects_height"
        LEFT_TIMESTAMP = "Left_timestamp"
        LEFT_NUMOBJECTS = "Left_numObjects"
        # LEFT_OBJECTS_ID = "Left_objects_id"
        LEFT_OBJECTS_SIGSTATUS = "Left_objects_eSigStatus"
        LEFT_OBJECTS_CLASSTYPE = "Left_objects_classType"
        LEFT_OBJECTS_CONFIDENCE = "Left_objects_confidence"
        LEFT_OBJECTS_CENTERPOINTWORLD_X = "Left_objects_centerPointWorld.x"
        LEFT_OBJECTS_CENTERPOINTWORLD_Y = "Left_objects_centerPointWorld.y"
        LEFT_OBJECTS_CENTERPOINTWORLD_Z = "Left_objects_centerPointWorld.z"
        # LEFT_OBJECTS_PLANESIZEWORLD_X = "Left_objects_planeSizeWorld.x"
        # LEFT_OBJECTS_PLANESIZEWORLD_Y = "Left_objects_planeSizeWorld.y"
        # LEFT_OBJECTS_CUBOIDSIZEWORLD_X = "Left_objects_cuboidSizeWorld.x"
        # LEFT_OBJECTS_CUBOIDSIZEWORLD_Y = "Left_objects_cuboidSizeWorld.y"
        # LEFT_OBJECTS_CUBOIDSIZEWORLD_Z = "Left_objects_cuboidSizeWorld.z"
        LEFT_OBJECTS_CUBOIDYAWWORLD = "Left_objects_cuboidYawWorld"
        LEFT_OBJECTS_WIDTH = "Left_objects_width"
        LEFT_OBJECTS_LENGTH = "Left_objects_length"
        LEFT_OBJECTS_HEIGHT = "Left_objects_height"
        RIGHT_TIMESTAMP = "Right_timestamp"
        RIGHT_NUMOBJECTS = "Right_numObjects"
        # RIGHT_OBJECTS_ID = "Right_objects_id"
        RIGHT_OBJECTS_SIGSTATUS = "Right_objects_eSigStatus"
        RIGHT_OBJECTS_CLASSTYPE = "Right_objects_classType"
        RIGHT_OBJECTS_CONFIDENCE = "Right_objects_confidence"
        RIGHT_OBJECTS_CENTERPOINTWORLD_X = "Right_objects_centerPointWorld.x"
        RIGHT_OBJECTS_CENTERPOINTWORLD_Y = "Right_objects_centerPointWorld.y"
        RIGHT_OBJECTS_CENTERPOINTWORLD_Z = "Right_objects_centerPointWorld.z"
        # RIGHT_OBJECTS_PLANESIZEWORLD_X = "Right_objects_planeSizeWorld.x"
        # RIGHT_OBJECTS_PLANESIZEWORLD_Y = "Right_objects_planeSizeWorld.y"
        # RIGHT_OBJECTS_CUBOIDSIZEWORLD_X = "Right_objects_cuboidSizeWorld.x"
        # RIGHT_OBJECTS_CUBOIDSIZEWORLD_Y = "Right_objects_cuboidSizeWorld.y"
        # RIGHT_OBJECTS_CUBOIDSIZEWORLD_Z = "Right_objects_cuboidSizeWorld.z"
        RIGHT_OBJECTS_CUBOIDYAWWORLD = "Right_objects_cuboidYawWorld"
        RIGHT_OBJECTS_WIDTH = "Right_objects_width"
        RIGHT_OBJECTS_LENGTH = "Right_objects_length"
        RIGHT_OBJECTS_HEIGHT = "Right_objects_height"
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
        PMDWS_FRONT_SIGSTATUS = "PMDWs_Front_eSigStatus"
        PMDWS_REAR_TIMESTAMP = "PMDWs_Rear_timestamp"
        PMDWS_REAR_SIGSTATUS = "PMDWs_Rear_eSigStatus"
        PMDWS_LEFT_TIMESTAMP = "PMDWs_Left_timestamp"
        PMDWS_LEFT_SIGSTATUS = "PMDWs_Left_eSigStatus"
        PMDWS_RIGHT_TIMESTAMP = "PMDWs_Right_timestamp"
        PMDWS_RIGHT_SIGSTATUS = "PMDWs_Right_eSigStatus"
        PMDWS_FRONT_LINECONFIDENCE = "PMDWs_Front_lineConfidence"
        PMDWS_REAR_LINECONFIDENCE = "PMDWs_Rear_lineConfidence"
        PMDWS_LEFT_LINECONFIDENCE = "PMDWs_Left_lineConfidence"
        PMDWS_RIGHT_LINECONFIDENCE = "PMDWs_Right_lineConfidence"
        PMDWS_FRONT_NUMBEROFLINES = "PMDWs_Front_numberOfLines"
        PMDWS_REAR_NUMBEROFLINES = "PMDWs_Rear_numberOfLines"
        PMDWS_LEFT_NUMBEROFLINES = "PMDWs_Left_numberOfLines"
        PMDWS_RIGHT_NUMBEROFLINES = "PMDWs_Right_numberOfLines"
        PMDWS_FRONT_LINESTARTX = "PMDWs_Front_lineStartX"
        PMDWS_FRONT_LINESTARTY = "PMDWs_Front_lineStartY"
        PMDWS_FRONT_LINEENDX = "PMDWs_Front_lineEndX"
        PMDWS_FRONT_LINEENDY = "PMDWs_Front_lineEndY"
        PMDWS_REAR_LINESTARTX = "PMDWs_Rear_lineStartX"
        PMDWS_REAR_LINESTARTY = "PMDWs_Rear_lineStartY"
        PMDWS_REAR_LINEENDX = "PMDWs_Rear_lineEndX"
        PMDWS_REAR_LINEENDY = "PMDWs_Rear_lineEndY"
        PMDWS_LEFT_LINESTARTX = "PMDWs_Left_lineStartX"
        PMDWS_LEFT_LINESTARTY = "PMDWs_Left_lineStartY"
        PMDWS_LEFT_LINEENDX = "PMDWs_Left_lineEndX"
        PMDWS_LEFT_LINEENDY = "PMDWs_Left_lineEndY"
        PMDWS_RIGHT_LINESTARTX = "PMDWs_Right_lineStartX"
        PMDWS_RIGHT_LINESTARTY = "PMDWs_Right_lineStartY"
        PMDWS_RIGHT_LINEENDX = "PMDWs_Right_lineEndX"
        PMDWS_RIGHT_LINEENDY = "PMDWs_Right_lineEndY"
        PMDWL_FRONT_TIMESTAMP = "PMDWl_Front_timestamp"
        PMDWL_FRONT_SIGSTATUS = "PMDWl_Front_eSigStatus"
        PMDWL_REAR_TIMESTAMP = "PMDWl_Rear_timestamp"
        PMDWL_REAR_SIGSTATUS = "PMDWl_Rear_eSigStatus"
        PMDWL_LEFT_TIMESTAMP = "PMDWl_Left_timestamp"
        PMDWL_LEFT_SIGSTATUS = "PMDWl_Left_eSigStatus"
        PMDWL_RIGHT_TIMESTAMP = "PMDWl_Right_timestamp"
        PMDWL_RIGHT_SIGSTATUS = "PMDWl_Right_eSigStatus"
        PMDWL_FRONT_LINECONFIDENCE = "PMDWl_Front_lineConfidence"
        PMDWL_REAR_LINECONFIDENCE = "PMDWl_Rear_lineConfidence"
        PMDWL_LEFT_LINECONFIDENCE = "PMDWl_Left_lineConfidence"
        PMDWL_RIGHT_LINECONFIDENCE = "PMDWl_Right_lineConfidence"
        PMDWL_FRONT_NUMBEROFWHEELLOCKERS = "PMDWl_Front_numberOfLines"
        PMDWL_REAR_NUMBEROFWHEELLOCKERS = "PMDWl_Rear_numberOfLines"
        PMDWL_LEFT_NUMBEROFWHEELLOCKERS = "PMDWl_Left_numberOfLines"
        PMDWL_RIGHT_NUMBEROFWHEELLOCKERS = "PMDWl_Right_numberOfLines"
        PMDWL_FRONT_LINESTARTX = "PMDWl_Front_lineStartX"
        PMDWL_FRONT_LINESTARTY = "PMDWl_Front_lineStartY"
        PMDWL_FRONT_LINEENDX = "PMDWl_Front_lineEndX"
        PMDWL_FRONT_LINEENDY = "PMDWl_Front_lineEndY"
        PMDWL_REAR_LINESTARTX = "PMDWl_Rear_lineStartX"
        PMDWL_REAR_LINESTARTY = "PMDWl_Rear_lineStartY"
        PMDWL_REAR_LINEENDX = "PMDWl_Rear_lineEndX"
        PMDWL_REAR_LINEENDY = "PMDWl_Rear_lineEndY"
        PMDWL_LEFT_LINESTARTX = "PMDWl_Left_lineStartX"
        PMDWL_LEFT_LINESTARTY = "PMDWl_Left_lineStartY"
        PMDWL_LEFT_LINEENDX = "PMDWl_Left_lineEndX"
        PMDWL_LEFT_LINEENDY = "PMDWl_Left_lineEndY"
        PMDWL_RIGHT_LINESTARTX = "PMDWl_Right_lineStartX"
        PMDWL_RIGHT_LINESTARTY = "PMDWl_Right_lineStartY"
        PMDWL_RIGHT_LINEENDX = "PMDWl_Right_lineEndX"
        PMDWL_RIGHT_LINEENDY = "PMDWl_Right_lineEndY"
        PMDSL_FRONT_TIMESTAMP = "PMDSl_Front_timestamp"
        PMDSL_REAR_TIMESTAMP = "PMDSl_Rear_timestamp"
        PMDSL_LEFT_TIMESTAMP = "PMDSl_Left_timestamp"
        PMDSL_RIGHT_TIMESTAMP = "PMDSl_Right_timestamp"
        PMDSL_FRONT_SIGSTATUS = "PMDSl_Front_eSigStatus"
        PMDSL_REAR_SIGSTATUS = "PMDSl_Rear_eSigStatus"
        PMDSL_LEFT_SIGSTATUS = "PMDSl_Left_eSigStatus"
        PMDSL_RIGHT_SIGSTATUS = "PMDSl_Right_eSigStatus"
        PMDSL_FRONT_LINECONFIDENCE = "PMDSl_Front_lineConfidence"
        PMDSL_REAR_LINECONFIDENCE = "PMDSl_Rear_lineConfidence"
        PMDSL_LEFT_LINECONFIDENCE = "PMDSl_Left_lineConfidence"
        PMDSL_RIGHT_LINECONFIDENCE = "PMDSl_Right_lineConfidence"
        PMDSL_FRONT_NUMBEROFLINES = "PMDSl_Front_numberOfLines"
        PMDSL_REAR_NUMBEROFLINES = "PMDSl_Rear_numberOfLines"
        PMDSL_LEFT_NUMBEROFLINES = "PMDSl_Left_numberOfLines"
        PMDSL_RIGHT_NUMBEROFLINES = "PMDSl_Right_numberOfLines"
        PMDSL_FRONT_STARTPOINTX = "PMDSl_Front_StopLines_lineStartX"
        PMDSL_FRONT_STARTPOINTY = "PMDSl_Front_StopLines_lineStartY"
        PMDSL_FRONT_ENDPOINTX = "PMDSl_Front_StopLines_lineEndX"
        PMDSL_FRONT_ENDPOINTY = "PMDSl_Front_StopLines_lineEndY"
        PMDSL_REAR_STARTPOINTX = "PMDSl_Rear_StopLines_lineStartX"
        PMDSL_REAR_STARTPOINTY = "PMDSl_Rear_StopLines_lineStartY"
        PMDSL_REAR_ENDPOINTX = "PMDSl_Rear_StopLines_lineEndX"
        PMDSL_REAR_ENDPOINTY = "PMDSl_Rear_StopLines_lineEndY"
        PMDSL_LEFT_STARTPOINTX = "PMDSl_Left_StopLines_lineStartX"
        PMDSL_LEFT_STARTPOINTY = "PMDSl_Left_StopLines_lineStartY"
        PMDSL_LEFT_ENDPOINTX = "PMDSl_Left_StopLines_lineEndX"
        PMDSL_LEFT_ENDPOINTY = "PMDSl_Left_StopLines_lineEndY"
        PMDSL_RIGHT_STARTPOINTX = "PMDSl_Right_StopLines_lineStartX"
        PMDSL_RIGHT_STARTPOINTY = "PMDSl_Right_StopLines_lineStartY"
        PMDSL_RIGHT_ENDPOINTX = "PMDSl_Right_StopLines_lineEndX"
        PMDSL_RIGHT_ENDPOINTY = "PMDSl_Right_StopLines_lineEndY"
        PMDPEDCROS_FRONT_P0_X = "PMDPEDCROS_Front_P0_x"
        PMDPEDCROS_FRONT_P0_Y = "PMDPEDCROS_Front_P0_y"
        PMDPEDCROS_FRONT_P1_X = "PMDPEDCROS_Front_P1_x"
        PMDPEDCROS_FRONT_P1_Y = "PMDPEDCROS_Front_P1_y"
        PMDPEDCROS_FRONT_P2_X = "PMDPEDCROS_Front_P2_x"
        PMDPEDCROS_FRONT_P2_Y = "PMDPEDCROS_Front_P2_y"
        PMDPEDCROS_FRONT_P3_X = "PMDPEDCROS_Front_P3_x"
        PMDPEDCROS_FRONT_P3_Y = "PMDPEDCROS_Front_P3_y"
        PMDPEDCROS_REAR_P0_X = "PMDPEDCROS_Rear_P0_x"
        PMDPEDCROS_REAR_P0_Y = "PMDPEDCROS_Rear_P0_y"
        PMDPEDCROS_REAR_P1_X = "PMDPEDCROS_Rear_P1_x"
        PMDPEDCROS_REAR_P1_Y = "PMDPEDCROS_Rear_P1_y"
        PMDPEDCROS_REAR_P2_X = "PMDPEDCROS_Rear_P2_x"
        PMDPEDCROS_REAR_P2_Y = "PMDPEDCROS_Rear_P2_y"
        PMDPEDCROS_REAR_P3_X = "PMDPEDCROS_Rear_P3_x"
        PMDPEDCROS_REAR_P3_Y = "PMDPEDCROS_Rear_P3_y"
        PMDPEDCROS_LEFT_P0_X = "PMDPEDCROS_Left_P0_x"
        PMDPEDCROS_LEFT_P0_Y = "PMDPEDCROS_Left_P0_y"
        PMDPEDCROS_LEFT_P1_X = "PMDPEDCROS_Left_P1_x"
        PMDPEDCROS_LEFT_P1_Y = "PMDPEDCROS_Left_P1_y"
        PMDPEDCROS_LEFT_P2_X = "PMDPEDCROS_Left_P2_x"
        PMDPEDCROS_LEFT_P2_Y = "PMDPEDCROS_Left_P2_y"
        PMDPEDCROS_LEFT_P3_X = "PMDPEDCROS_Left_P3_x"
        PMDPEDCROS_LEFT_P3_Y = "PMDPEDCROS_Left_P3_y"
        PMDPEDCROS_RIGHT_P0_X = "PMDPEDCROS_Right_P0_x"
        PMDPEDCROS_RIGHT_P0_Y = "PMDPEDCROS_Right_P0_y"
        PMDPEDCROS_RIGHT_P1_X = "PMDPEDCROS_Right_P1_x"
        PMDPEDCROS_RIGHT_P1_Y = "PMDPEDCROS_Right_P1_y"
        PMDPEDCROS_RIGHT_P2_X = "PMDPEDCROS_Right_P2_x"
        PMDPEDCROS_RIGHT_P2_Y = "PMDPEDCROS_Right_P2_y"
        PMDPEDCROS_RIGHT_P3_X = "PMDPEDCROS_Right_P3_x"
        PMDPEDCROS_RIGHT_P3_Y = "PMDPEDCROS_Right_P3_y"
        PMDPEDCROS_FRONT_TIMESTAMP = "PMDPEDCROS_Front_timestamp"
        PMDPEDCROS_REAR_TIMESTAMP = "PMDPEDCROS_Rear_timestamp"
        PMDPEDCROS_LEFT_TIMESTAMP = "PMDPEDCROS_Left_timestamp"
        PMDPEDCROS_FRONT_SIGSTATUS = "PMDPEDCROS_Front_eSigStatus"
        PMDPEDCROS_REAR_SIGSTATUS = "PMDPEDCROS_Rear_eSigStatus"
        PMDPEDCROS_LEFT_SIGSTATUS = "PMDPEDCROS_Left_eSigStatus"
        PMDPEDCROS_RIGHT_SIGSTATUS = "PMDPEDCROS_Right_eSigStatus"
        PMDPEDCROS_RIGHT_TIMESTAMP = "PMDPEDCROS_Right_timestamp"
        PMDPEDCROS_FRONT_LINECONFIDENCE = "PMDPEDCROS_Front_lineConfidence"
        PMDPEDCROS_REAR_LINECONFIDENCE = "PMDPEDCROS_Rear_lineConfidence"
        PMDPEDCROS_LEFT_LINECONFIDENCE = "PMDPEDCROS_Left_lineConfidence"
        PMDPEDCROS_RIGHT_LINECONFIDENCE = "PMDPEDCROS_Right_lineConfidence"
        PMDPEDCROS_FRONT_NUMBEROFCROSSINGS = "PMDPEDCROS_Front_numberOfCrossings"
        PMDPEDCROS_REAR_NUMBEROFCROSSINGS = "PMDPEDCROS_Rear_numberOfCrossings"
        PMDPEDCROS_LEFT_NUMBEROFCROSSINGS = "PMDPEDCROS_Left_numberOfCrossings"
        PMDPEDCROS_RIGHT_NUMBEROFCROSSINGS = "PMDPEDCROS_Right_numberOfCrossings"
        PMDPEDCROS_FRONT_EXISTENCEPROBABILITY = "PMDPEDCROS__Front_existenceProbability"
        PMDPEDCROS_REAR_EXISTENCEPROBABILITY = "PMDPEDCROS__Front_existenceProbability"
        PMDPEDCROS_LEFT_EXISTENCEPROBABILITY = "PMDPEDCROS__Front_existenceProbability"
        PMDPEDCROS_RIGHT_EXISTENCEPROBABILITY = "PMDPEDCROS__Front_existenceProbability"
        PCLDELIMITERS_SIGSTATUS = "Cem_pcl_eSigStatus"
        NUMPCLDELIMITERS = "Cem_numPclDelimiters"
        NUMPCLDELIMITERS_TIMESTAMP = "Cem_numPclDelimiters_timestamp"
        CEM_PCL_DELIMITERID = "Cem_pcl_delimiterId"
        CEM_PCL_DELIMITERTYPE = "Cem_pcl_delimiterType"
        CEM_PCL_P0_X = "Cem_pcl_P0_x"
        CEM_PCL_P0_Y = "Cem_pcl_P0_y"
        CEM_PCL_P1_X = "Cem_pcl_P1_x"
        CEM_PCL_P1_Y = "Cem_pcl_P1_y"
        CEM_PCL_CONFIDENCEPERCENT = "Cem_pcl_confidencePercent"
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
        CEMSLOT_OCCLUSIONSTATE = "CemSlot_occlusionState"
        CEMSLOT_SC_ANGLED = "CemSlot_sc_angled"
        CEMSLOT_SC_PARALLEL = "CemSlot_sc_parallel"
        CEMSLOT_SC_PERPENDICULAR = "CemSlot_sc_perpendicular"
        CEMWS_SIGSTATUS = "CemWs_eSigStatus"
        CEMWS_TIMESTAMP = "CemWs_timestamp"
        CEMWS_NUMBEROFLINES = "CemWs_numberOfLines"
        CEMWS_DELIMITERID = "CemWs_delimiterId"
        CEMWS_DELIMITERTYPE = "CemWs_delimiterType"
        CEMWS_PARKINGLINES_LINEID = "CemWs_parkingLines_lineId"
        CEMWS_PARKINGLINES_LINETYPE = "CemWs_parkingLines_lineType"
        CEMWS_PARKINGLINES_LINESTARTX = "CemWs_parkingLines_lineStartX"
        CEMWS_PARKINGLINES_LINESTARTY = "CemWs_parkingLines_lineStartY"
        CEMWS_PARKINGLINES_LINEENDX = "CemWs_parkingLines_lineEndX"
        CEMWS_PARKINGLINES_LINEENDY = "CemWs_parkingLines_lineEndY"
        CEMWS_PARKINGLINES_LINECONFIDENCE = "CemWs_parkingLines_lineConfidence"
        CEMWL_SIGSTATUS = "CemWl_eSigStatus"
        CEMWL_TIMESTAMP = "CemWl_timestamp"
        CEMWL_NUMBEROFWHEELLOCKERS = "CemWl_numberOfWheellockers"
        CEMWL_DELIMITERID = "CemWl_delimiterId"
        CEMWL_DELIMITERTYPE = "CemWl_delimiterType"
        CEMWL_PARKINGLINES_LINEID = "CemWl_parkingLines_lineId"
        CEMWL_PARKINGLINES_LINETYPE = "CemWl_parkingLines_lineType"
        CEMWL_PARKINGLINES_LINESTARTX = "CemWl_parkingLines_lineStartX"
        CEMWL_PARKINGLINES_LINESTARTY = "CemWl_parkingLines_lineStartY"
        CEMWL_PARKINGLINES_LINEENDX = "CemWl_parkingLines_lineEndX"
        CEMWL_PARKINGLINES_LINEENDY = "CemWl_parkingLines_lineEndY"
        CEMWL_PARKINGLINES_LINECONFIDENCE = "CemWl_parkingLines_lineConfidence"
        CEM_STOPLINES_SIGSTATUS = "Cem_stopLines_eSigStatus"
        CEM_STOPLINES_TIMESTAMP = "Cem_stopLines_timestamp"
        CEM_NUMBEROFSTOPLINES = "Cem_numberOfstopLines"
        CEM_STOPLINES_LINEID = "Cem_stopLines_lineId"
        CEM_STOPLINES_LINESTARTX = "Cem_stopLines_lineStartX"
        CEM_STOPLINES_LINESTARTY = "Cem_stopLines_lineStartY"
        CEM_STOPLINES_LINEENDX = "Cem_stopLines_lineEndX"
        CEM_STOPLINES_LINEENDY = "Cem_stopLines_lineEndY"
        CEM_STOPLINES_LINECONFIDENCE = "Cem_stopLines_lineConfidence"
        CEM_PEDCROSSINGS_TIMESTAMP = "Cem_pedCrossings_timestamp"
        CEM_PEDCROSSINGS_SIGSTATUS = "Cem_pedCrossings_eSigStatus"
        CEM_NUMBEROFPEDCROSSINGS = "Cem_numberOfPedCrossings"
        CEM_PEDCROSSINGS_ID = "Cem_pedCrossings_Id"
        CEMS_PEDCROSSINGS_P0_X = "Cem_pedCrossings_P0_x"
        CEM_PEDCROSSINGS_P0_Y = "Cem_pedCrossings_P0_y"
        CEM_PEDCROSSINGS_P1_X = "Cem_pedCrossings_P1_x"
        CEM_PEDCROSSINGS_P1_Y = "Cem_pedCrossings_P1_y"
        CEM_PEDCROSSINGS_P2_X = "Cem_pedCrossings_P2_x"
        CEM_PEDCROSSINGS_P2_Y = "Cem_pedCrossings_P2_y"
        CEM_PEDCROSSINGS_P3_X = "Cem_pedCrossings_P3_x"
        CEM_PEDCROSSINGS_P3_Y = "Cem_pedCrossings_P3_y"
        CEM_PEDCROSSINGS_CONFIDENCE = "Cem_pedCrossings_Confidence"
        PMSDSLOT_FRONT_TIMESTAMP = "PmsdSlot_Front_timestamp"
        PMSDSLOT_FRONT_SIGSTATUS = "PmsdSlot_Front_eSigStatus"
        PMSDSLOT_FRONT_NUMBEROFSLOTS = "PmsdSlot_Front_numberOfSlots"
        PMSDSLOT_FRONT_P0_X = "PmsdSlot_Front_P0_x"
        PMSDSLOT_FRONT_P0_Y = "PmsdSlot_Front_P0_y"
        PMSDSLOT_FRONT_P1_X = "PmsdSlot_Front_P1_x"
        PMSDSLOT_FRONT_P1_Y = "PmsdSlot_Front_P1_y"
        PMSDSLOT_FRONT_P2_X = "PmsdSlot_Front_P2_x"
        PMSDSLOT_FRONT_P2_Y = "PmsdSlot_Front_P2_y"
        PMSDSLOT_FRONT_P3_X = "PmsdSlot_Front_P3_x"
        PMSDSLOT_FRONT_P3_Y = "PmsdSlot_Front_P3_y"
        PMSDSLOT_FRONT_SC_ANGLED = "PmsdSlot_Front_sc_angled"
        PMSDSLOT_FRONT_SC_PARALLEL = "PmsdSlot_Front_sc_parallel"
        PMSDSLOT_FRONT_SC_PERPENDICULAR = "PmsdSlot_Front_sc_perpendicular"
        PMSDSLOT_FRONT_EXISTENCEPROBABILITY = "PmsdSlot_Front_existenceProbability"
        PMSDSLOT_FRONT_OCCLUSIONSTATE = "PmsdSlot_Front_occlusionState"
        PMSDSLOT_REAR_TIMESTAMP = "PmsdSlot_Rear_timestamp"
        PMSDSLOT_REAR_SIGSTATUS = "PmsdSlot_Rear_eSigStatus"
        PMSDSLOT_REAR_NUMBEROFSLOTS = "PmsdSlot_Rear_numberOfSlots"
        PMSDSLOT_REAR_P0_X = "PmsdSlot_Rear_P0_x"
        PMSDSLOT_REAR_P0_Y = "PmsdSlot_Rear_P0_y"
        PMSDSLOT_REAR_P1_X = "PmsdSlot_Rear_P1_x"
        PMSDSLOT_REAR_P1_Y = "PmsdSlot_Rear_P1_y"
        PMSDSLOT_REAR_P2_X = "PmsdSlot_Rear_P2_x"
        PMSDSLOT_REAR_P2_Y = "PmsdSlot_Rear_P2_y"
        PMSDSLOT_REAR_P3_X = "PmsdSlot_Rear_P3_x"
        PMSDSLOT_REAR_P3_Y = "PmsdSlot_Rear_P3_y"
        PMSDSLOT_REAR_SC_ANGLED = "PmsdSlot_Rear_sc_angled"
        PMSDSLOT_REAR_SC_PARALLEL = "PmsdSlot_Rear_sc_parallel"
        PMSDSLOT_REAR_SC_PERPENDICULAR = "PmsdSlot_Rear_sc_perpendicular"
        PMSDSLOT_REAR_EXISTENCEPROBABILITY = "PmsdSlot_Rear_existenceProbability"
        PMSDSLOT_REAR_OCCLUSIONSTATE = "PmsdSlot_Rear_occlusionState"
        PMSDSLOT_LEFT_TIMESTAMP = "PmsdSlot_Left_timestamp"
        PMSDSLOT_LEFT_SIGSTATUS = "PmsdSlot_Left_eSigStatus"
        PMSDSLOT_LEFT_NUMBEROFSLOTS = "PmsdSlot_Left_numberOfSlots"
        PMSDSLOT_LEFT_P0_X = "PmsdSlot_Left_P0_x"
        PMSDSLOT_LEFT_P0_Y = "PmsdSlot_Left_P0_y"
        PMSDSLOT_LEFT_P1_X = "PmsdSlot_Left_P1_x"
        PMSDSLOT_LEFT_P1_Y = "PmsdSlot_Left_P1_y"
        PMSDSLOT_LEFT_P2_X = "PmsdSlot_Left_P2_x"
        PMSDSLOT_LEFT_P2_Y = "PmsdSlot_Left_P2_y"
        PMSDSLOT_LEFT_P3_X = "PmsdSlot_Left_P3_x"
        PMSDSLOT_LEFT_P3_Y = "PmsdSlot_Left_P3_y"
        PMSDSLOT_LEFT_SC_ANGLED = "PmsdSlot_Left_sc_angled"
        PMSDSLOT_LEFT_SC_PARALLEL = "PmsdSlot_Left_sc_parallel"
        PMSDSLOT_LEFT_SC_PERPENDICULAR = "PmsdSlot_Left_sc_perpendicular"
        PMSDSLOT_LEFT_EXISTENCEPROBABILITY = "PmsdSlot_Left_existenceProbability"
        PMSDSLOT_LEFT_OCCLUSIONSTATE = "PmsdSlot_Left_occlusionState"
        PMSDSLOT_RIGHT_TIMESTAMP = "PmsdSlot_Right_timestamp"
        PMSDSLOT_RIGHT_SIGSTATUS = "PmsdSlot_Right_eSigStatus"
        PMSDSLOT_RIGHT_NUMBEROFSLOTS = "PmsdSlot_Right_numberOfSlots"
        PMSDSLOT_RIGHT_P0_X = "PmsdSlot_Right_P0_x"
        PMSDSLOT_RIGHT_P0_Y = "PmsdSlot_Right_P0_y"
        PMSDSLOT_RIGHT_P1_X = "PmsdSlot_Right_P1_x"
        PMSDSLOT_RIGHT_P1_Y = "PmsdSlot_Right_P1_y"
        PMSDSLOT_RIGHT_P2_X = "PmsdSlot_Right_P2_x"
        PMSDSLOT_RIGHT_P2_Y = "PmsdSlot_Right_P2_y"
        PMSDSLOT_RIGHT_P3_X = "PmsdSlot_Right_P3_x"
        PMSDSLOT_RIGHT_P3_Y = "PmsdSlot_Right_P3_y"
        PMSDSLOT_RIGHT_SC_ANGLED = "PmsdSlot_Right_sc_angled"
        PMSDSLOT_RIGHT_SC_PARALLEL = "PmsdSlot_Right_sc_parallel"
        PMSDSLOT_RIGHT_SC_PERPENDICULAR = "PmsdSlot_Right_sc_perpendicular"
        PMSDSLOT_RIGHT_EXISTENCEPROBABILITY = "PmsdSlot_Right_existenceProbability"
        PMSDSLOT_RIGHT_OCCLUSIONSTATE = "PmsdSlot_Right_occlusionState"
        CEMSLOT_GT_TIMESTAMP = "CemSlot_gt_timestamp"
        CEMSLOT_GT_SIGSTATUS = "CemSlot_gt_eSigStatus"
        CEMSLOT_GT_NUMBEROFSLOTS = "CemSlot_gt_numberOfSlots"
        CEMSLOT_GT_SLOTID = "CemSlot_gt_slotId"
        CEMSLOT_GT_P0_X = "CemSlot_gt_P0_x"
        CEMSLOT_GT_P0_Y = "CemSlot_gt_P0_y"
        CEMSLOT_GT_P1_X = "CemSlot_gt_P1_x"
        CEMSLOT_GT_P1_Y = "CemSlot_gt_P1_y"
        CEMSLOT_GT_P2_X = "CemSlot_gt_P2_x"
        CEMSLOT_GT_P2_Y = "CemSlot_gt_P2_y"
        CEMSLOT_GT_P3_X = "CemSlot_gt_P3_x"
        CEMSLOT_GT_P3_Y = "CemSlot_gt_P3_y"
        CEMSLOT_GT_EXISTENCEPROBABILITY = "CemSlot_gt_existenceProbability"
        CEMSLOT_GT_SC_ANGLED = "CemSlot_gt_sc_angled"
        CEMSLOT_GT_SC_PARALLEL = "CemSlot_gt_sc_parallel"
        CEMSLOT_GT_SC_PERPENDICULAR = "CemSlot_gt_sc_perpendicular"
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
        MECAL_CAMERAEXTRINSICS_FC_ESIGSTATUS = "Mecal_CameraExtrinsics_FC_EsigStatus"
        MECAL_CAMERAEXTRINSICS_FC_TIMESTAMP = "Mecal_CameraExtrinsics_FC_Timestamp"
        MECAL_CAMERAEXTRINSICS_RC_ESIGSTATUS = "Mecal_CameraExtrinsics_RC_EsigStatus"
        MECAL_CAMERAEXTRINSICS_RC_TIMESTAMP = "Mecal_CameraExtrinsics_RC_Timestamp"
        MECAL_CAMERAEXTRINSICS_LSC_ESIGSTATUS = "Mecal_CameraExtrinsics_LSC_EsigStatus"
        MECAL_CAMERAEXTRINSICS_LSC_TIMESTAMP = "Mecal_CameraExtrinsics_LSC_Timestamp"
        MECAL_CAMERAEXTRINSICS_RSC_ESIGSTATUS = "Mecal_CameraExtrinsics_RSC_EsigStatus"
        MECAL_CAMERAEXTRINSICS_RSC_TIMESTAMP = "Mecal_CameraExtrinsics_RSC_Timestamp"
        GRAPPA_FC_DETECTIONRESULTS_TIMESTAMP = "Grappa_FC_DetectionResults_Timestamp"
        GRAPPA_FC_DETECTIONRESULTS_ESIGSTATUS = "Grappa_FC_DetectionResults_EsigStatus"
        GRAPPA_RC_DETECTIONRESULTS_TIMESTAMP = "Grappa_RC_DetectionResults_Timestamp"
        GRAPPA_RC_DETECTIONRESULTS_ESIGSTATUS = "Grappa_RC_DetectionResults_EsigStatus"
        GRAPPA_LSC_DETECTIONRESULTS_TIMESTAMP = "Grappa_LSC_DetectionResults_Timestamp"
        GRAPPA_LSC_DETECTIONRESULTS_ESIGSTATUS = "Grappa_LSC_DetectionResults_EsigStatus"
        GRAPPA_RSC_DETECTIONRESULTS_TIMESTAMP = "Grappa_RSC_DetectionResults_Timestamp"
        GRAPPA_RSC_DETECTIONRESULTS_ESIGSTATUS = "Grappa_RSC_DetectionResults_EsigStatus"
        GRAPPA_FC_SEMSEG_TIMESTAMP = "Grappa_FC_Semseg_Timestamp"
        GRAPPA_FC_SEMSEG_ESIGSTATUS = "Grappa_FC_Semseg_EsigStatus"
        GRAPPA_RC_SEMSEG_TIMESTAMP = "Grappa_RC_Semseg_Timestamp"
        GRAPPA_RC_SEMSEG_ESIGSTATUS = "Grappa_RC_Semseg_EsigStatus"
        GRAPPA_LSC_SEMSEG_TIMESTAMP = "Grappa_LSC_Semseg_Timestamp"
        GRAPPA_LSC_SEMSEG_ESIGSTATUS = "Grappa_LSC_Semseg_EsigStatus"
        GRAPPA_RSC_SEMSEG_TIMESTAMP = "Grappa_RSC_Semseg_Timestamp"
        GRAPPA_RSC_SEMSEG_ESIGSTATUS = "Grappa_RSC_Semseg_EsigStatus"
        PARAMETERHANDELER_FC_TIMESTAMP = "ParameterHandler_FC_Timestamp"
        PARAMETERHANDELER_FC_ESIGSTATUS = "ParameterHandler_FC_EsigStatus"
        PARAMETERHANDELER_RC_TIMESTAMP = "ParameterHandler_RC_Timestamp"
        PARAMETERHANDELER_RC_ESIGSTATUS = "ParameterHandler_RC_EsigStatus"
        PARAMETERHANDELER_LSC_TIMESTAMP = "ParameterHandler_LSC_Timestamp"
        PARAMETERHANDELER_LSC_ESIGSTATUS = "ParameterHandler_LSC_EsigStatus"
        PARAMETERHANDELER_RSC_TIMESTAMP = "ParameterHandler_RSC_Timestamp"
        PARAMETERHANDELER_RSC_ESIGSTATUS = "ParameterHandler_RSC_EsigStatus"

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
                self.Columns.PMSDSLOT_FRONT_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.header.t_Stamp.u_Nsec",
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.timestamp",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.timestamp",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.sSigHeader.uiTimeStamp",
                    "SIM VFB.PMSD_FC_DATA.Slots.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.sensor_header.e_SignalStatus",
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.signalStatus",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.signalState",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.sSigHeader.eSigStatus",
                    "SIM VFB.PMSD_FC_DATA.Slots.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_NUMBEROFSLOTS,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.number_of_slots",
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.numberOfSlots",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.number_of_slots",
                    "SIM VFB.PMSDINSTANCE_fc.Slots.numberOfSlots",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.numberOfSlots",
                    "SIM VFB.PMSD_FC_DATA.Slots.numberOfSlots",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_P0_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].slot_corners[0].x",
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parkingSlots[%].corner_0.x",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].slot_corners[0].x",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_0.x",
                    "SIM VFB.PMSD_FC_DATA.Slots.parkingSlots[%].corner_0.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_P0_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].slot_corners[0].y",
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parkingSlots[%].corner_0.y",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].slot_corners[0].y",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_0.y",
                    "SIM VFB.PMSD_FC_DATA.Slots.parkingSlots[%].corner_0.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_P1_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].slot_corners[1].x",
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parkingSlots[%].corner_1.x",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].slot_corners[1].x",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_1.x",
                    "SIM VFB.PMSD_FC_DATA.Slots.parkingSlots[%].corner_1.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_P1_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].slot_corners[1].y",
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parkingSlots[%].corner_1.y",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].slot_corners[1].y",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_1.y",
                    "SIM VFB.PMSD_FC_DATA.Slots.parkingSlots[%].corner_1.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_P2_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].slot_corners[2].x",
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parkingSlots[%].corner_2.x",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].slot_corners[2].x",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_2.x",
                    "SIM VFB.PMSD_FC_DATA.Slots.parkingSlots[%].corner_2.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_P2_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].slot_corners[2].y",
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parkingSlots[%].corner_2.y",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].slot_corners[2].y",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_2.y",
                    "SIM VFB.PMSD_FC_DATA.Slots.parkingSlots[%].corner_2.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_P3_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].slot_corners[3].x",
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parkingSlots[%].corner_3.x",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].slot_corners[3].x",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_3.x",
                    "SIM VFB.PMSD_FC_DATA.Slots.parkingSlots[%].corner_3.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_P3_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].slot_corners[3].y",
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parkingSlots[%].corner_3.y",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].slot_corners[3].y",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_3.y",
                    "SIM VFB.PMSD_FC_DATA.Slots.parkingSlots[%].corner_3.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_SC_ANGLED,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].parking_scenario_confidence.angled",
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parkingSlots[%].parkingScenarioConfidence.angled",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].parking_scenario_confidence.angled",
                    "SIM VFB.PMSDINSTANCE_fc.Slots.parkingSlots[%].parkingScenarioConfidence.angled",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.angled",
                    "SIM VFB.PMSD_FC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.angled",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_SC_PARALLEL,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].parking_scenario_confidence.parallel",
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parkingSlots[%].parkingScenarioConfidence.parallel",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].parking_scenario_confidence.parallel",
                    "SIM VFB.PMSDINSTANCE_fc.Slots.parkingSlots[%].parkingScenarioConfidence.parallel",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.parallel",
                    "SIM VFB.PMSD_FC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.parallel",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_SC_PERPENDICULAR,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].parking_scenario_confidence.perpendicular",
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].parking_scenario_confidence.perpendicular",
                    "SIM VFB.PMSDINSTANCE_fc.Slots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                    "SIM VFB.PMSD_FC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_EXISTENCEPROBABILITY,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parking_slots[%].existence_probability",
                    "AP.svcModelProcessingOutput.data.parkingSlotListFront.parkingSlots[%].existenceProbability",
                    "CarPC.EM_Thread.CEMODSlotInput_Front.parking_slots[%].existence_probability",
                    "SIM VFB.PMSDINSTANCE_fc.Slots.parkingSlots[%].existenceProbability",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].existenceProbability",
                    "SIM VFB.PMSD_FC_DATA.Slots.parkingSlots[%].existenceProbability",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_OCCLUSIONSTATE,
                [
                    "SIM VFB.PMSDINSTANCE_fc.Slots.parkingSlots[%].cornerOcclusionState",
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].cornerOcclusionState",
                    "SIM VFB.PMSD_FC_DATA.Slots.parkingSlots[%].cornerOcclusionState",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.header.t_Stamp.u_Nsec",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.timestamp",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.timestamp",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.sSigHeader.uiTimeStamp",
                    "SIM VFB.PMSD_RC_DATA.Slots.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.sensor_header.e_SignalStatus",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.signalStatus",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.signalState",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.sSigHeader.eSigStatus",
                    "SIM VFB.PMSD_RC_DATA.Slots.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_NUMBEROFSLOTS,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.number_of_slots",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.numberOfSlots",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.number_of_slots",
                    "SIM VFB.PMSDINSTANCE_rc.Slots.numberOfSlots",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.numberOfSlots",
                    "SIM VFB.PMSD_RC_DATA.Slots.numberOfSlots",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_P0_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].slot_corners[0].x",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parkingSlots[%].corner_0.x",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].slot_corners[0].x",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_0.x",
                    "SIM VFB.PMSD_RC_DATA.Slots.parkingSlots[%].corner_0.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_P0_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].slot_corners[0].y",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parkingSlots[%].corner_0.y",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].slot_corners[0].y",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_0.y",
                    "SIM VFB.PMSD_RC_DATA.Slots.parkingSlots[%].corner_0.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_P1_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].slot_corners[1].x",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parkingSlots[%].corner_1.x",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].slot_corners[1].x",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_1.x",
                    "SIM VFB.PMSD_RC_DATA.Slots.parkingSlots[%].corner_1.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_P1_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].slot_corners[1].y",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parkingSlots[%].corner_1.y",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].slot_corners[1].y",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_1.y",
                    "SIM VFB.PMSD_RC_DATA.Slots.parkingSlots[%].corner_1.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_P2_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].slot_corners[2].x",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parkingSlots[%].corner_2.x",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].slot_corners[2].x",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_2.x",
                    "SIM VFB.PMSD_RC_DATA.Slots.parkingSlots[%].corner_2.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_P2_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].slot_corners[2].y",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parkingSlots[%].corner_2.y",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].slot_corners[2].y",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_2.y",
                    "SIM VFB.PMSD_RC_DATA.Slots.parkingSlots[%].corner_2.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_P3_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].slot_corners[3].x",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parkingSlots[%].corner_3.x",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].slot_corners[3].x",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_3.x",
                    "SIM VFB.PMSD_RC_DATA.Slots.parkingSlots[%].corner_3.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_P3_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].slot_corners[3].y",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parkingSlots[%].corner_3.y",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].slot_corners[3].y",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_3.y",
                    "SIM VFB.PMSD_RC_DATA.Slots.parkingSlots[%].corner_3.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_SC_ANGLED,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].parking_scenario_confidence.angled",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parkingSlots[%].parkingScenarioConfidence.angled",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].parking_scenario_confidence.angled",
                    "SIM VFB.PMSDINSTANCE_rc.Slots.parkingSlots[%].parkingScenarioConfidence.angled",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.angled",
                    "SIM VFB.PMSD_RC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.angled",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_SC_PARALLEL,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].parking_scenario_confidence.parallel",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parkingSlots[%].parkingScenarioConfidence.parallel",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].parking_scenario_confidence.parallel",
                    "SIM VFB.PMSDINSTANCE_rc.Slots.parkingSlots[%].parkingScenarioConfidence.parallel",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.parallel",
                    "SIM VFB.PMSD_RC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.parallel",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_SC_PERPENDICULAR,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].parking_scenario_confidence.perpendicular",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].parking_scenario_confidence.perpendicular",
                    "SIM VFB.PMSDINSTANCE_rc.Slots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                    "SIM VFB.PMSD_RC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_EXISTENCEPROBABILITY,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parking_slots[%].existence_probability",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRear.parkingSlots[%].existenceProbability",
                    "CarPC.EM_Thread.CEMODSlotInput_Rear.parking_slots[%].existence_probability",
                    "SIM VFB.PMSDINSTANCE_rc.Slots.parkingSlots[%].existenceProbability",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].existenceProbability",
                    "SIM VFB.PMSD_RC_DATA.Slots.parkingSlots[%].existenceProbability",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_OCCLUSIONSTATE,
                [
                    "SIM VFB.PMSDINSTANCE_rc.Slots.parkingSlots[%].cornerOcclusionState",
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].cornerOcclusionState",
                    "SIM VFB.PMSD_RC_DATA.Slots.parkingSlots[%].cornerOcclusionState",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.header.t_Stamp.u_Nsec",
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.timestamp",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.timestamp",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.sSigHeader.uiTimeStamp",
                    "SIM VFB.PMSD_LSC_DATA.Slots.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.sensor_header.e_SignalStatus",
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.signalStatus",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.signalState",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.sSigHeader.eSigStatus",
                    "SIM VFB.PMSD_LSC_DATA.Slots.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_NUMBEROFSLOTS,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.number_of_slots",
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.numberOfSlots",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.number_of_slots",
                    "SIM VFB.PMSDINSTANCE_lsc.Slots.numberOfSlots",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.numberOfSlots",
                    "SIM VFB.PMSD_LSC_DATA.Slots.numberOfSlots",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_P0_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].slot_corners[0].x",
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parkingSlots[%].corner_0.x",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].slot_corners[0].x",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_0.x",
                    "SIM VFB.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_0.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_P0_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].slot_corners[0].y",
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parkingSlots[%].corner_0.y",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].slot_corners[0].y",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_0.y",
                    "SIM VFB.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_0.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_P1_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].slot_corners[1].x",
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parkingSlots[%].corner_1.x",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].slot_corners[1].x",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_1.x",
                    "SIM VFB.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_1.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_P1_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].slot_corners[1].y",
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parkingSlots[%].corner_1.y",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].slot_corners[1].y",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_1.y",
                    "SIM VFB.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_1.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_P2_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].slot_corners[2].x",
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parkingSlots[%].corner_2.x",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].slot_corners[2].x",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_2.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_P2_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].slot_corners[2].y",
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parkingSlots[%].corner_2.y",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].slot_corners[2].y",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_2.y",
                    "SIM VFB.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_2.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_P3_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].slot_corners[3].x",
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parkingSlots[%].corner_3.x",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].slot_corners[3].x",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_3.x",
                    "SIM VFB.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_3.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_P3_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].slot_corners[3].y",
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parkingSlots[%].corner_3.y",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].slot_corners[3].y",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_3.y",
                    "SIM VFB.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_3.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_SC_ANGLED,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].parking_scenario_confidence.angled",
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parkingSlots[%].parkingScenarioConfidence.angled",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].parking_scenario_confidence.angled",
                    "SIM VFB.PMSDINSTANCE_lsc.Slots.parkingSlots[%].parkingScenarioConfidence.angled",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.angled",
                    "SIM VFB.PMSD_LSC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.angled",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_SC_PARALLEL,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].parking_scenario_confidence.parallel",
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parkingSlots[%].parkingScenarioConfidence.parallel",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].parking_scenario_confidence.parallel",
                    "SIM VFB.PMSDINSTANCE_lsc.Slots.parkingSlots[%].parkingScenarioConfidence.parallel",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.parallel",
                    "SIM VFB.PMSD_LSC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.parallel",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_SC_PERPENDICULAR,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].parking_scenario_confidence.perpendicular",
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].parking_scenario_confidence.perpendicular",
                    "SIM VFB.PMSDINSTANCE_lsc.Slots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                    "SIM VFB.PMSD_LSC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_EXISTENCEPROBABILITY,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parking_slots[%].existence_probability",
                    "AP.svcModelProcessingOutput.data.parkingSlotListLeft.parkingSlots[%].existenceProbability",
                    "CarPC.EM_Thread.CEMODSlotInput_Left.parking_slots[%].existence_probability",
                    "SIM VFB.PMSDINSTANCE_lsc.Slots.parkingSlots[%].existenceProbability",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].existenceProbability",
                    "SIM VFB.PMSD_LSC_DATA.Slots.parkingSlots[%].existenceProbability",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_OCCLUSIONSTATE,
                [
                    "SIM VFB.PMSDINSTANCE_lsc.Slots.parkingSlots[%].cornerOcclusionState",
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].cornerOcclusionState",
                    "SIM VFB.PMSD_LSC_DATA.Slots.parkingSlots[%].cornerOcclusionState",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.header.t_Stamp.u_Nsec",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.timestamp",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.timestamp",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.sSigHeader.uiTimeStamp",
                    "SIM VFB.PMSD_RSC_DATA.Slots.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.sensor_header.e_SignalStatus",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.signalStatus",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.signalState",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.sSigHeader.eSigStatus",
                    "SIM VFB.PMSD_RSC_DATA.Slots.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_NUMBEROFSLOTS,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.number_of_slots",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.numberOfSlots",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.number_of_slots",
                    "SIM VFB.PMSDINSTANCE_rsc.Slots.numberOfSlots",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.numberOfSlots",
                    "SIM VFB.PMSD_RSC_DATA.Slots.numberOfSlots",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_P0_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].slot_corners[0].x",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parkingSlots[%].corner_0.x",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].slot_corners[0].x",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_0.x",
                    "SIM VFB.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_0.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_P0_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].slot_corners[0].y",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parkingSlots[%].corner_0.y",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].slot_corners[0].y",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_0.y",
                    "SIM VFB.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_0.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_P1_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].slot_corners[1].x",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parkingSlots[%].corner_1.x",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].slot_corners[1].x",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_1.x",
                    "SIM VFB.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_1.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_P1_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].slot_corners[1].y",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parkingSlots[%].corner_1.y",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].slot_corners[1].y",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_1.y",
                    "SIM VFB.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_1.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_P2_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].slot_corners[2].x",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parkingSlots[%].corner_2.x",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].slot_corners[2].x",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_2.x",
                    "SIM VFB.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_2.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_P2_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].slot_corners[2].y",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parkingSlots[%].corner_2.y",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].slot_corners[2].y",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_2.y",
                    "SIM VFB.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_2.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_P3_X,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].slot_corners[3].x",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parkingSlots[%].corner_3.x",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].slot_corners[3].x",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_3.x",
                    "SIM VFB.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_3.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_P3_Y,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].slot_corners[3].y",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parkingSlots[%].corner_3.y",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].slot_corners[3].y",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_3.y",
                    "SIM VFB.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_3.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_SC_ANGLED,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].parking_scenario_confidence.angled",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parkingSlots[%].parkingScenarioConfidence.angled",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].parking_scenario_confidence.angled",
                    "SIM VFB.PMSDINSTANCE_rsc.Slots.parkingSlots[%].parkingScenarioConfidence.angled",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.angled",
                    "SIM VFB.PMSD_RSC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.angled",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_SC_PARALLEL,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].parking_scenario_confidence.parallel",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parkingSlots[%].parkingScenarioConfidence.parallel",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].parking_scenario_confidence.parallel",
                    "SIM VFB.PMSDINSTANCE_rsc.Slots.parkingSlots[%].parkingScenarioConfidence.parallel",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.parallel",
                    "SIM VFB.PMSD_RSC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.parallel",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_SC_PERPENDICULAR,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].parking_scenario_confidence.perpendicular",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].parking_scenario_confidence.perpendicular",
                    "SIM VFB.PMSDINSTANCE_rsc.Slots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                    "SIM VFB.PMSD_RSC_DATA.Slots.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_EXISTENCEPROBABILITY,
                [
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parking_slots[%].existence_probability",
                    "AP.svcModelProcessingOutput.data.parkingSlotListRight.parkingSlots[%].existenceProbability",
                    "CarPC.EM_Thread.CEMODSlotInput_Right.parking_slots[%].existence_probability",
                    "SIM VFB.PMSDINSTANCE_rsc.Slots.parkingSlots[%].existenceProbability",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].existenceProbability",
                    "SIM VFB.PMSD_RSC_DATA.Slots.parkingSlots[%].existenceProbability",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_OCCLUSIONSTATE,
                [
                    "SIM VFB.PMSDINSTANCE_rsc.Slots.parkingSlots[%].cornerOcclusionState",
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].cornerOcclusionState",
                    "SIM VFB.PMSD_RSC_DATA.Slots.parkingSlots[%].cornerOcclusionState",
                ],
            ),
            (
                self.Columns.CEMWS_SIGSTATUS,
                [
                    "wheelStopperOutput.sSigHeader.eSigStatus",
                    "MTA_ADC5.CEM200_PFS_DATA.m_traceData.sigHeader.eSigStatus",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.CEMWS_TIMESTAMP,
                [
                    "wheelStopperOutput.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.CEM200_PFS_DATA.m_WsOutput.sSigHeader.uiTimeStamp",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.CEMWS_NUMBEROFLINES,
                [
                    "wheelStopperOutput.numberOfWheelStoppers",
                    "MTA_ADC5.CEM200_PFS_DATA.m_WsOutput.numberOfDelimiters",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.numberOfDelimiters",
                ],
            ),
            (
                self.Columns.CEMWS_DELIMITERID,
                [
                    "wheelStopperOutput.wheelstoppers._%_.id",
                    "MTA_ADC5.CEM200_PFS_DATA.m_WsOutput.delimiters[%].id",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].delimiterId",
                ],
            ),
            (
                self.Columns.CEMWS_DELIMITERTYPE,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_WsOutput.delimiters[%].type",
                ],
            ),
            (
                self.Columns.CEMWS_PARKINGLINES_LINESTARTX,
                [
                    "wheelStopperOutput.wheelstoppers._%_.startPointXPosition",
                    "MTA_ADC5.CEM200_PFS_DATA.m_WsOutput.delimiters[%].startPointXPosition",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].startPointXPosition",
                ],
            ),
            (
                self.Columns.CEMWS_PARKINGLINES_LINESTARTY,
                [
                    "wheelStopperOutput.wheelstoppers._%_.startPointYPosition",
                    "MTA_ADC5.CEM200_PFS_DATA.m_WsOutput.delimiters[%].startPointYPosition",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].startPointYPosition",
                ],
            ),
            (
                self.Columns.CEMWS_PARKINGLINES_LINEENDX,
                [
                    "wheelStopperOutput.wheelstoppers._%_.endPointXPosition",
                    "MTA_ADC5.CEM200_PFS_DATA.m_WsOutput.delimiters[%].endPointXPosition",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].endPointXPosition",
                ],
            ),
            (
                self.Columns.CEMWS_PARKINGLINES_LINEENDY,
                [
                    "wheelStopperOutput.wheelstoppers._%_.endPointYPosition",
                    "MTA_ADC5.CEM200_PFS_DATA.m_WsOutput.delimiters[%].endPointYPosition",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].endPointYPosition",
                ],
            ),
            (
                self.Columns.CEMWS_PARKINGLINES_LINECONFIDENCE,
                [
                    "wheelStopperOutput.wheelstoppers._%_.confidence",
                    "MTA_ADC5.CEM200_PFS_DATA.m_WsOutput.delimiters[%].confidence",
                    "ADC5xx_Device.CEM_EM_DATA.PFS_PfsOutput.wsOutput.pclDelimiters[%].confidencePercent",
                ],
            ),
            (
                self.Columns.CEMWL_SIGSTATUS,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_WheelLockerOutput.sSigHeader.eSigStatus",
                    "wheelLockerOutput.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.CEMWL_TIMESTAMP,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_WheelLockerOutput.sSigHeader.uiTimeStamp",
                    "wheelLockerOutput.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.CEMWL_NUMBEROFWHEELLOCKERS,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_WheelLockerOutput.numberOfWheelockers",
                    "wheelLockerOutput.numberOfWheelockers",
                ],
            ),
            (
                self.Columns.CEMWL_DELIMITERID,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_WheelLockerOutput.delimiters[%].id",
                    "wheelLockerOutput.delimiters._%_.id",
                ],
            ),
            (
                self.Columns.CEMWL_PARKINGLINES_LINESTARTX,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_WheelLockerOutput.delimiters[%].startPointXPosition",
                    "wheelLockerOutput.delimiters._%_.startPointXPosition",
                ],
            ),
            (
                self.Columns.CEMWL_PARKINGLINES_LINESTARTY,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_WheelLockerOutput.delimiters[%].startPointYPosition",
                    "wheelLockerOutput.delimiters._%_.startPointYPosition",
                ],
            ),
            (
                self.Columns.CEMWL_PARKINGLINES_LINEENDX,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_WheelLockerOutput.delimiters[%].endPointXPosition",
                    "wheelLockerOutput.delimiters._%_.endPointXPosition",
                ],
            ),
            (
                self.Columns.CEMWL_PARKINGLINES_LINEENDY,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_WheelLockerOutput.delimiters[%].endPointYPosition",
                    "wheelLockerOutput.delimiters._%_.endPointYPosition",
                ],
            ),
            (
                self.Columns.CEMWL_PARKINGLINES_LINECONFIDENCE,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_WheelLockerOutput.delimiters[%].confidence",
                    "wheelLockerOutput.delimiters._%_.confidence",
                ],
            ),
            (
                self.Columns.CEM_STOPLINES_SIGSTATUS,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_StopLineOutput.sSigHeader.eSigStatus",
                    "stopLineOutput.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.CEM_STOPLINES_TIMESTAMP,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_StopLineOutput.sSigHeader.uiTimeStamp",
                    "stopLineOutput.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.CEM_NUMBEROFSTOPLINES,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_StopLineOutput.numberOfLines",
                    "stopLineOutput.numberOfLines",
                ],
            ),
            (
                self.Columns.CEM_STOPLINES_LINEID,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_StopLineOutput.stopLines[%].id",
                    "stopLineOutput.stopLines._%_.id",
                ],
            ),
            (
                self.Columns.CEM_STOPLINES_LINESTARTX,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_StopLineOutput.stopLines[%].startPoint.x",
                    "stopLineOutput.stopLines._%_.startPoint.x",
                ],
            ),
            (
                self.Columns.CEM_STOPLINES_LINESTARTY,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_StopLineOutput.stopLines[%].startPoint.y",
                    "stopLineOutput.stopLines._%_.startPoint.y",
                ],
            ),
            (
                self.Columns.CEM_STOPLINES_LINEENDX,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_StopLineOutput.stopLines[%].endPoint.x",
                    "stopLineOutput.stopLines._%_.endPoint.x",
                ],
            ),
            (
                self.Columns.CEM_STOPLINES_LINEENDX,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_StopLineOutput.stopLines[%].endPoint.y",
                    "stopLineOutput.stopLines._%_.endPoint.y",
                ],
            ),
            (
                self.Columns.CEM_STOPLINES_LINECONFIDENCE,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_StopLineOutput.stopLines[%].lineConfidence",
                    "stopLineOutput.stopLines._%_.lineConfidence",
                ],
            ),
            (
                self.Columns.CEM_PEDCROSSINGS_TIMESTAMP,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_PedestrianCrossingOutput.sSigHeader.uiTimeStamp",
                    "pedestrianCrossingOutput.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.CEM_PEDCROSSINGS_SIGSTATUS,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_PedestrianCrossingOutput.sSigHeader.eSigStatus",
                    "pedestrianCrossingOutput.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.CEM_NUMBEROFPEDCROSSINGS,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_PedestrianCrossingOutput.numberOfCrossings",
                    "pedestrianCrossingOutput.numberOfCrossings",
                ],
            ),
            (
                self.Columns.CEM_PEDCROSSINGS_ID,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_PedestrianCrossingOutput.pedestrianCrossings[%].id",
                    "pedestrianCrossingOutput.pedestrianCrossings._%_.id",
                ],
            ),
            (
                self.Columns.CEMS_PEDCROSSINGS_P0_X,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_PedestrianCrossingOutput.pedestrianCrossings[%].boundaryPoints[0].x",
                    "pedestrianCrossingOutput.pedestrianCrossings._%_.boundaryPoints._0_.x",
                ],
            ),
            (
                self.Columns.CEM_PEDCROSSINGS_P0_Y,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_PedestrianCrossingOutput.pedestrianCrossings[%].boundaryPoints[0].y",
                    "pedestrianCrossingOutput.pedestrianCrossings._%_.boundaryPoints._0_.y",
                ],
            ),
            (
                self.Columns.CEM_PEDCROSSINGS_P1_X,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_PedestrianCrossingOutput.pedestrianCrossings[%].boundaryPoints[1].x",
                    "pedestrianCrossingOutput.pedestrianCrossings._%_.boundaryPoints._1_.x",
                ],
            ),
            (
                self.Columns.CEM_PEDCROSSINGS_P1_Y,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_PedestrianCrossingOutput.pedestrianCrossings[%].boundaryPoints[1].y",
                    "pedestrianCrossingOutput.pedestrianCrossings._%_.boundaryPoints._1_.y",
                ],
            ),
            (
                self.Columns.CEM_PEDCROSSINGS_P2_X,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_PedestrianCrossingOutput.pedestrianCrossings[%].boundaryPoints[2].x",
                    "pedestrianCrossingOutput.pedestrianCrossings._%_.boundaryPoints._2_.x",
                ],
            ),
            (
                self.Columns.CEM_PEDCROSSINGS_P2_Y,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_PedestrianCrossingOutput.pedestrianCrossings[%].boundaryPoints[2].y",
                    "pedestrianCrossingOutput.pedestrianCrossings._%_.boundaryPoints._2_.y",
                ],
            ),
            (
                self.Columns.CEM_PEDCROSSINGS_P3_X,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_PedestrianCrossingOutput.pedestrianCrossings[%].boundaryPoints[3].x",
                    "pedestrianCrossingOutput.pedestrianCrossings._%_.boundaryPoints._3_.x",
                ],
            ),
            (
                self.Columns.CEM_PEDCROSSINGS_P3_Y,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_PedestrianCrossingOutput.pedestrianCrossings[%].boundaryPoints[3].y",
                    "pedestrianCrossingOutput.pedestrianCrossings._%_.boundaryPoints._3_.y",
                ],
            ),
            (
                self.Columns.CEM_PEDCROSSINGS_CONFIDENCE,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_PedestrianCrossingOutput.pedestrianCrossings[%].confidence",
                    "pedestrianCrossingOutput.pedestrianCrossings._%_.confidence",
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
                    "MTA_ADC5.CEM200_PFS_DATA.m_PsdOutput.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.CEMSLOT_SIGSTATUS,
                [
                    "parkingSlotDetectionOutput.sSigHeader.eSigStatus",
                    "CarPC.EM_Thread.CEMODSlotOutput.cem_signal_state",
                    "MTA_ADC5.CEM200_AUPDF_DATA.ParkingSlots.sSigHeader.eSigStatus",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PsdOutput.sSigHeader.eSigStatus",
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
                    "MTA_ADC5.CEM200_PFS_DATA.m_PsdOutput.numberOfSlots",
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
                    "MTA_ADC5.CEM200_PFS_DATA.m_PsdOutput.parkingSlots[%].slotId",
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
                    "MTA_ADC5.CEM200_PFS_DATA.m_PsdOutput.parkingSlots[%].slotCorners[0].x",
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
                    "MTA_ADC5.CEM200_PFS_DATA.m_PsdOutput.parkingSlots[%].slotCorners[0].y",
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
                    "MTA_ADC5.CEM200_PFS_DATA.m_PsdOutput.parkingSlots[%].slotCorners[1].x",
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
                    "MTA_ADC5.CEM200_PFS_DATA.m_PsdOutput.parkingSlots[%].slotCorners[1].y",
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
                    "MTA_ADC5.CEM200_PFS_DATA.m_PsdOutput.parkingSlots[%].slotCorners[2].x",
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
                    "MTA_ADC5.CEM200_PFS_DATA.m_PsdOutput.parkingSlots[%].slotCorners[2].y",
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
                    "MTA_ADC5.CEM200_PFS_DATA.m_PsdOutput.parkingSlots[%].slotCorners[3].x",
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
                    "MTA_ADC5.CEM200_PFS_DATA.m_PsdOutput.parkingSlots[%].slotCorners[3].y",
                ],
            ),
            (
                self.Columns.CEMSLOT_OCCLUSIONSTATE,
                [
                    "MTA_ADC5.CEM200_PFS_DATA.m_PsdOutput.parkingSlots[%].cornerOcclusionState",
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
                    "MTA_ADC5.CEM200_PFS_DATA.m_PsdOutput.parkingSlots[%].existenceProbability",
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
                    "MTA_ADC5.CEM200_PFS_DATA.m_PsdOutput.parkingSlots[%].parkingScenarioConfidence.angled",
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
                    "MTA_ADC5.CEM200_PFS_DATA.m_PsdOutput.parkingSlots[%].parkingScenarioConfidence.parallel",
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
                    "MTA_ADC5.CEM200_PFS_DATA.m_PsdOutput.parkingSlots[%].parkingScenarioConfidence.perpendicular",
                ],
            ),
            (
                self.Columns.CEMSLOT_GT_TIMESTAMP,
                [
                    "GT.envModelPort.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.CEMSLOT_GT_SIGSTATUS,
                [
                    "parkingSlotDetectionOutput.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.CEMSLOT_GT_NUMBEROFSLOTS,
                [
                    "parkingSlotDetectionOutput.numberOfSlots",
                ],
            ),
            (
                self.Columns.CEMSLOT_GT_SLOTID,
                [
                    "GT.envModelPort.parkingBoxes._%_.parkingBoxID_nu",
                ],
            ),
            (
                self.Columns.CEMSLOT_GT_P0_X,
                [
                    "GT.envModelPort.parkingBoxes._%_.slotCoordinates.0.x_m",
                ],
            ),
            (
                self.Columns.CEMSLOT_GT_P0_Y,
                [
                    "GT.envModelPort.parkingBoxes._%_.slotCoordinates.0.y_m",
                ],
            ),
            (
                self.Columns.CEMSLOT_GT_P1_X,
                [
                    "GT.envModelPort.parkingBoxes._%_.slotCoordinates.1.x_m",
                ],
            ),
            (
                self.Columns.CEMSLOT_GT_P1_Y,
                [
                    "GT.envModelPort.parkingBoxes._%_.slotCoordinates.1.y_m",
                ],
            ),
            (
                self.Columns.CEMSLOT_GT_P2_X,
                [
                    "GT.envModelPort.parkingBoxes._%_.slotCoordinates.2.x_m",
                ],
            ),
            (
                self.Columns.CEMSLOT_GT_P2_Y,
                [
                    "GT.envModelPort.parkingBoxes._%_.slotCoordinates.2.y_m",
                ],
            ),
            (
                self.Columns.CEMSLOT_GT_P3_X,
                [
                    "GT.envModelPort.parkingBoxes._%_.slotCoordinates.3.x_m",
                ],
            ),
            (
                self.Columns.CEMSLOT_GT_P3_Y,
                [
                    "GT.envModelPort.parkingBoxes._%_.slotCoordinates.3.y_m",
                ],
            ),
            (
                self.Columns.CEMSLOT_GT_EXISTENCEPROBABILITY,
                [
                    "GT.envModelPort.parkingBoxes._%_.existenceProb_perc",
                ],
            ),
            (
                self.Columns.CEMSLOT_GT_SC_ANGLED,
                [
                    "parkingSlotDetectionOutput.parkingSlots._%_.parkingScenarioConfidence.angled",
                ],
            ),
            (
                self.Columns.CEMSLOT_GT_SC_PARALLEL,
                [
                    "parkingSlotDetectionOutput.parkingSlots._%_.parkingScenarioConfidence.parallel",
                ],
            ),
            (
                self.Columns.CEMSLOT_GT_SC_PERPENDICULAR,
                [
                    "parkingSlotDetectionOutput.parkingSlots._%_.parkingScenarioConfidence.perpendicular",
                ],
            ),
            (
                self.Columns.PMDCAMERA_FRONT_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListFront.signalState",
                    "AP.svcModelProcessingOutput.data.parkingLineListFront.signalStatus",
                    "CarPC.EM_Thread.PmdFront.signalState",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.sSigHeader.eSigStatus",
                    "SIM VFB.PMSD_FC_DATA.ParkingLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDCAMERA_FRONT_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListFront.timestamp",
                    "AP.svcModelProcessingOutput.data.parkingLineListFront.timestamp",
                    "CarPC.EM_Thread.PmdFront.timestamp",
                    "SIM VFB.PMSDINSTANCE_fc.ParkingLines.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.sSigHeader.uiTimeStamp",
                    "SIM VFB.PMSD_FC_DATA.ParkingLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDCAMERA_FRONT_NUMBEROFLINES,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListFront.numberOfLines",
                    "AP.svcModelProcessingOutput.data.parkingLineListFront.numberOfLines",
                    "CarPC.EM_Thread.PmdFront.numberOfLines",
                    "SIM VFB.PMSDINSTANCE_fc.ParkingLines.numberOfLines",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.numberOfLines",
                    "SIM VFB.PMSD_FC_DATA.ParkingLines.numberOfLines",
                ],
            ),
            (
                self.Columns.PMDCAMERA_FRONT_PARKINGLINES_LINEID,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListFront.parkingLines[%].lineId",
                    "CarPC.EM_Thread.PmdFront.parkingLines[%].lineId",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.parkingLines[%].lineId",
                    "SIM VFB.PMSD_FC_DATA.ParkingLines.parkingLines[%].lineId",
                ],
            ),
            (
                self.Columns.PMDCAMERA_FRONT_PARKINGLINES_LINESTARTX,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListFront.parkingLines[%].lineStartX",
                    "AP.svcModelProcessingOutput.data.parkingLineListFront.parkingLines[%].startPoint.x",
                    "CarPC.EM_Thread.PmdFront.parkingLines[%].lineStartX",
                    "SIM VFB.PMSDINSTANCE_fc.ParkingLines.parkingLines[%].lineStartXInM",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.parkingLines[%].lineStartXInM",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.parkingLines[%].startPoint.x",
                    "SIM VFB.PMSD_FC_DATA.ParkingLines.parkingLines[%].startPoint.x",
                ],
            ),
            (
                self.Columns.PMDCAMERA_FRONT_PARKINGLINES_LINESTARTY,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListFront.parkingLines[%].lineStartY",
                    "AP.svcModelProcessingOutput.data.parkingLineListFront.parkingLines[%].startPoint.y",
                    "CarPC.EM_Thread.PmdFront.parkingLines[%].lineStartY",
                    "SIM VFB.PMSDINSTANCE_fc.ParkingLines.parkingLines[%].lineStartYInM",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.parkingLines[%].lineStartYInM",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.parkingLines[%].startPoint.y",
                    "SIM VFB.PMSD_FC_DATA.ParkingLines.parkingLines[%].startPoint.y",
                ],
            ),
            (
                self.Columns.PMDCAMERA_FRONT_PARKINGLINES_LINEENDX,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListFront.parkingLines[%].lineEndX",
                    "AP.svcModelProcessingOutput.data.parkingLineListFront.parkingLines[%].endPoint.x",
                    "CarPC.EM_Thread.PmdFront.parkingLines[%].lineEndX",
                    "SIM VFB.PMSDINSTANCE_fc.ParkingLines.parkingLines[%].lineEndXinM",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.parkingLines[%].lineEndXinM",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.parkingLines[%].endPoint.x",
                    "SIM VFB.PMSD_FC_DATA.ParkingLines.parkingLines[%].endPoint.x",
                ],
            ),
            (
                self.Columns.PMDCAMERA_FRONT_PARKINGLINES_LINEENDY,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListFront.parkingLines[%].lineEndY",
                    "AP.svcModelProcessingOutput.data.parkingLineListFront.parkingLines[%].endPoint.y",
                    "CarPC.EM_Thread.PmdFront.parkingLines[%].lineEndY",
                    "SIM VFB.PMSDINSTANCE_fc.ParkingLines.parkingLines[%].lineEndYinM",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.parkingLines[%].lineEndYinM",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.parkingLines[%].endPoint.y",
                    "SIM VFB.PMSD_FC_DATA.ParkingLines.parkingLines[%].endPoint.y",
                ],
            ),
            (
                self.Columns.PMDCAMERA_FRONT_PARKINGLINES_LINECONFIDENCE,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListFront.parkingLines[%].lineConfidence",
                    "AP.svcModelProcessingOutput.data.parkingLineListFront.parkingLines[%].confidence",
                    "CarPC.EM_Thread.PmdFront.parkingLines[%].lineConfidence",
                    "SIM VFB.PMSDINSTANCE_fc.ParkingLines.parkingLines[%].lineConfidence",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.parkingLines[%].lineConfidence",
                    "MTA_ADC5.PMSD_FC_DATA.ParkingLines.parkingLines[%].confidence",
                    "SIM VFB.PMSD_FC_DATA.ParkingLines.parkingLines[%].confidence",
                ],
            ),
            (
                self.Columns.PMDCAMERA_REAR_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRear.signalState",
                    "AP.svcModelProcessingOutput.data.parkingLineListRear.signalStatus",
                    "CarPC.EM_Thread.PmdRear.signalState",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.sSigHeader.eSigStatus",
                    "SIM VFB.PMSD_RC_DATA.ParkingLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDCAMERA_REAR_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRear.timestamp",
                    "AP.svcModelProcessingOutput.data.parkingLineListRear.timestamp",
                    "CarPC.EM_Thread.PmdRear.timestamp",
                    "SIM VFB.PMSDINSTANCE_rc.ParkingLines.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.sSigHeader.uiTimeStamp",
                    "SIM VFB.PMSD_RC_DATA.ParkingLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDCAMERA_REAR_NUMBEROFLINES,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRear.numberOfLines",
                    "AP.svcModelProcessingOutput.data.parkingLineListRear.numberOfLines",
                    "CarPC.EM_Thread.PmdRear.numberOfLines",
                    "SIM VFB.PMSDINSTANCE_rc.ParkingLines.numberOfLines",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.numberOfLines",
                    "SIM VFB.PMSD_RC_DATA.ParkingLines.numberOfLines",
                ],
            ),
            (
                self.Columns.PMDCAMERA_REAR_PARKINGLINES_LINEID,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRear.parkingLines[%].lineId",
                    "CarPC.EM_Thread.PmdRear.parkingLines[%].lineId",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.parkingLines[%].lineId",
                    "SIM VFB.PMSD_RC_DATA.ParkingLines.parkingLines[%].lineId",
                ],
            ),
            (
                self.Columns.PMDCAMERA_REAR_PARKINGLINES_LINESTARTX,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRear.parkingLines[%].lineStartX",
                    "AP.svcModelProcessingOutput.data.parkingLineListRear.parkingLines[%].startPoint.x",
                    "CarPC.EM_Thread.PmdRear.parkingLines[%].lineStartX",
                    "SIM VFB.PMSDINSTANCE_rc.ParkingLines.parkingLines[%].lineStartXInM",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.parkingLines[%].lineStartXInM",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.parkingLines[%].startPoint.x",
                    "SIM VFB.PMSD_RC_DATA.ParkingLines.parkingLines[%].startPoint.x",
                ],
            ),
            (
                self.Columns.PMDCAMERA_REAR_PARKINGLINES_LINESTARTY,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRear.parkingLines[%].lineStartY",
                    "AP.svcModelProcessingOutput.data.parkingLineListRear.parkingLines[%].startPoint.y",
                    "CarPC.EM_Thread.PmdRear.parkingLines[%].lineStartY",
                    "SIM VFB.PMSDINSTANCE_rc.ParkingLines.parkingLines[%].lineStartYInM",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.parkingLines[%].lineStartYInM",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.parkingLines[%].startPoint.y",
                    "SIM VFB.PMSD_RC_DATA.ParkingLines.parkingLines[%].startPoint.y",
                ],
            ),
            (
                self.Columns.PMDCAMERA_REAR_PARKINGLINES_LINEENDX,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRear.parkingLines[%].lineEndX",
                    "AP.svcModelProcessingOutput.data.parkingLineListRear.parkingLines[%].endPoint.x",
                    "CarPC.EM_Thread.PmdRear.parkingLines[%].lineEndX",
                    "SIM VFB.PMSDINSTANCE_rc.ParkingLines.parkingLines[%].lineEndXinM",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.parkingLines[%].lineEndXinM",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.parkingLines[%].endPoint.x",
                    "SIM VFB.PMSD_RC_DATA.ParkingLines.parkingLines[%].endPoint.x",
                ],
            ),
            (
                self.Columns.PMDCAMERA_REAR_PARKINGLINES_LINEENDY,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRear.parkingLines[%].lineEndY",
                    "AP.svcModelProcessingOutput.data.parkingLineListRear.parkingLines[%].endPoint.y",
                    "CarPC.EM_Thread.PmdRear.parkingLines[%].lineEndY",
                    "SIM VFB.PMSDINSTANCE_rc.ParkingLines.parkingLines[%].lineEndYinM",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.parkingLines[%].lineEndYinM",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.parkingLines[%].endPoint.y",
                    "SIM VFB.PMSD_RC_DATA.ParkingLines.parkingLines[%].endPoint.y",
                ],
            ),
            (
                self.Columns.PMDCAMERA_REAR_PARKINGLINES_LINECONFIDENCE,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRear.parkingLines[%].lineConfidence",
                    "AP.svcModelProcessingOutput.data.parkingLineListRear.parkingLines[%].confidence",
                    "CarPC.EM_Thread.PmdRear.parkingLines[%].lineConfidence",
                    "SIM VFB.PMSDINSTANCE_rc.ParkingLines.parkingLines[%].lineConfidence",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.parkingLines[%].lineConfidence",
                    "MTA_ADC5.PMSD_RC_DATA.ParkingLines.parkingLines[%].confidence",
                    "SIM VFB.PMSD_RC_DATA.ParkingLines.parkingLines[%].confidence",
                ],
            ),
            (
                self.Columns.PMDCAMERA_LEFT_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListLeft.signalState",
                    "AP.svcModelProcessingOutput.data.parkingLineListLeft.signalStatus",
                    "CarPC.EM_Thread.PmdLeft.signalState",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.sSigHeader.eSigStatus",
                    "SIM VFB.PMSD_LSC_DATA.ParkingLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDCAMERA_LEFT_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListLeft.timestamp",
                    "AP.svcModelProcessingOutput.data.parkingLineListLeft.timestamp",
                    "CarPC.EM_Thread.PmdLeft.timestamp",
                    "SIM VFB.PMSDINSTANCE_lsc.ParkingLines.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.sSigHeader.uiTimeStamp",
                    "SIM VFB.PMSD_LSC_DATA.ParkingLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDCAMERA_LEFT_NUMBEROFLINES,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListLeft.numberOfLines",
                    "AP.svcModelProcessingOutput.data.parkingLineListLeft.numberOfLines",
                    "CarPC.EM_Thread.PmdLeft.numberOfLines",
                    "SIM VFB.PMSDINSTANCE_lsc.ParkingLines.numberOfLines",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.numberOfLines",
                    "SIM VFB.PMSD_LSC_DATA.ParkingLines.numberOfLines",
                ],
            ),
            (
                self.Columns.PMDCAMERA_LEFT_PARKINGLINES_LINEID,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListLeft.parkingLines[%].lineId",
                    "CarPC.EM_Thread.PmdLeft.parkingLines[%].lineId",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.parkingLines[%].lineId",
                    "SIM VFB.PMSD_LSC_DATA.ParkingLines.parkingLines[%].lineId",
                ],
            ),
            (
                self.Columns.PMDCAMERA_LEFT_PARKINGLINES_LINESTARTX,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListLeft.parkingLines[%].lineStartX",
                    "AP.svcModelProcessingOutput.data.parkingLineListLeft.parkingLines[%].startPoint.x",
                    "CarPC.EM_Thread.PmdLeft.parkingLines[%].lineStartX",
                    "SIM VFB.PMSDINSTANCE_lsc.ParkingLines.parkingLines[%].lineStartXInM",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.parkingLines[%].lineStartXInM",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.parkingLines[%].startPoint.x",
                    "SIM VFB.PMSD_LSC_DATA.ParkingLines.parkingLines[%].startPoint.x",
                ],
            ),
            (
                self.Columns.PMDCAMERA_LEFT_PARKINGLINES_LINESTARTY,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListLeft.parkingLines[%].lineStartY",
                    "AP.svcModelProcessingOutput.data.parkingLineListLeft.parkingLines[%].startPoint.y",
                    "CarPC.EM_Thread.PmdLeft.parkingLines[%].lineStartY",
                    "SIM VFB.PMSDINSTANCE_lsc.ParkingLines.parkingLines[%].lineStartYInM",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.parkingLines[%].lineStartYInM",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.parkingLines[%].startPoint.y",
                    "SIM VFB.PMSD_LSC_DATA.ParkingLines.parkingLines[%].startPoint.y",
                ],
            ),
            (
                self.Columns.PMDCAMERA_LEFT_PARKINGLINES_LINEENDX,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListLeft.parkingLines[%].lineEndX",
                    "AP.svcModelProcessingOutput.data.parkingLineListLeft.parkingLines[%].endPoint.x",
                    "CarPC.EM_Thread.PmdLeft.parkingLines[%].lineEndX",
                    "SIM VFB.PMSDINSTANCE_lsc.ParkingLines.parkingLines[%].lineEndXinM",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.parkingLines[%].lineEndXinM",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.parkingLines[%].endPoint.x",
                    "SIM VFB.PMSD_LSC_DATA.ParkingLines.parkingLines[%].endPoint.x",
                ],
            ),
            (
                self.Columns.PMDCAMERA_LEFT_PARKINGLINES_LINEENDY,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListLeft.parkingLines[%].lineEndY",
                    "AP.svcModelProcessingOutput.data.parkingLineListLeft.parkingLines[%].endPoint.y",
                    "CarPC.EM_Thread.PmdLeft.parkingLines[%].lineEndY",
                    "SIM VFB.PMSDINSTANCE_lsc.ParkingLines.parkingLines[%].lineEndYinM",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.parkingLines[%].lineEndYinM",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.parkingLines[%].endPoint.y",
                    "SIM VFB.PMSD_LSC_DATA.ParkingLines.parkingLines[%].endPoint.y",
                ],
            ),
            (
                self.Columns.PMDCAMERA_LEFT_PARKINGLINES_LINECONFIDENCE,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListLeft.parkingLines[%].lineConfidence",
                    "AP.svcModelProcessingOutput.data.parkingLineListLeft.parkingLines[%].confidence",
                    "CarPC.EM_Thread.PmdLeft.parkingLines[%].lineConfidence",
                    "SIM VFB.PMSDINSTANCE_lsc.ParkingLines.parkingLines[%].lineConfidence",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.parkingLines[%].lineConfidence",
                    "MTA_ADC5.PMSD_LSC_DATA.ParkingLines.parkingLines[%].confidence",
                    "SIM VFB.PMSD_LSC_DATA.ParkingLines.parkingLines[%].confidence",
                ],
            ),
            (
                self.Columns.PMDCAMERA_RIGHT_SIGSTATUS,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRight.signalState",
                    "AP.svcModelProcessingOutput.data.parkingLineListRight.signalStatus",
                    "CarPC.EM_Thread.PmdRight.signalState",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.sSigHeader.eSigStatus",
                    "SIM VFB.PMSD_RSC_DATA.ParkingLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDCAMERA_RIGHT_TIMESTAMP,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRight.timestamp",
                    "AP.svcModelProcessingOutput.data.parkingLineListRight.timestamp",
                    "CarPC.EM_Thread.PmdRight.timestamp",
                    "SIM VFB.PMSDINSTANCE_rsc.ParkingLines.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.sSigHeader.uiTimeStamp",
                    "SIM VFB.PMSD_RSC_DATA.ParkingLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDCAMERA_RIGHT_NUMBEROFLINES,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRight.numberOfLines",
                    "AP.svcModelProcessingOutput.data.parkingLineListRight.numberOfLines",
                    "CarPC.EM_Thread.PmdRight.numberOfLines",
                    "SIM VFB.PMSDINSTANCE_rsc.ParkingLines.numberOfLines",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.numberOfLines",
                    "SIM VFB.PMSD_RSC_DATA.ParkingLines.numberOfLines",
                ],
            ),
            (
                self.Columns.PMDCAMERA_RIGHT_PARKINGLINES_LINEID,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRight.parkingLines[%].lineId",
                    "CarPC.EM_Thread.PmdRight.parkingLines[%].lineId",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.parkingLines[%].lineId",
                    "SIM VFB.PMSD_RSC_DATA.ParkingLines.parkingLines[%].lineId",
                ],
            ),
            (
                self.Columns.PMDCAMERA_RIGHT_PARKINGLINES_LINESTARTX,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRight.parkingLines[%].lineStartX",
                    "AP.svcModelProcessingOutput.data.parkingLineListRight.parkingLines[%].startPoint.x",
                    "CarPC.EM_Thread.PmdRight.parkingLines[%].lineStartX",
                    "SIM VFB.PMSDINSTANCE_rsc.ParkingLines.parkingLines[%].lineStartXInM",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.parkingLines[%].lineStartXInM",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.parkingLines[%].startPoint.x",
                    "SIM VFB.PMSD_RSC_DATA.ParkingLines.parkingLines[%].startPoint.x",
                ],
            ),
            (
                self.Columns.PMDCAMERA_RIGHT_PARKINGLINES_LINESTARTY,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRight.parkingLines[%].lineStartY",
                    "AP.svcModelProcessingOutput.data.parkingLineListRight.parkingLines[%].startPoint.y",
                    "CarPC.EM_Thread.PmdRight.parkingLines[%].lineStartY",
                    "SIM VFB.PMSDINSTANCE_rsc.ParkingLines.parkingLines[%].lineStartYInM",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.parkingLines[%].lineStartYInM",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.parkingLines[%].startPoint.y",
                    "SIM VFB.PMSD_RSC_DATA.ParkingLines.parkingLines[%].startPoint.y",
                ],
            ),
            (
                self.Columns.PMDCAMERA_RIGHT_PARKINGLINES_LINEENDX,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRight.parkingLines[%].lineEndX",
                    "AP.svcModelProcessingOutput.data.parkingLineListRight.parkingLines[%].endPoint.x",
                    "CarPC.EM_Thread.PmdRight.parkingLines[%].lineEndX",
                    "SIM VFB.PMSDINSTANCE_rsc.ParkingLines.parkingLines[%].lineEndXinM",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.parkingLines[%].lineEndXinM",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.parkingLines[%].endPoint.x",
                    "SIM VFB.PMSD_RSC_DATA.ParkingLines.parkingLines[%].endPoint.x",
                ],
            ),
            (
                self.Columns.PMDCAMERA_RIGHT_PARKINGLINES_LINEENDY,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRight.parkingLines[%].lineEndY",
                    "AP.svcModelProcessingOutput.data.parkingLineListRight.parkingLines[%].endPoint.y",
                    "CarPC.EM_Thread.PmdRight.parkingLines[%].lineEndY",
                    "SIM VFB.PMSDINSTANCE_rsc.ParkingLines.parkingLines[%].lineEndYinM",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.parkingLines[%].lineEndYinM",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.parkingLines[%].endPoint.y",
                    "SIM VFB.PMSD_RSC_DATA.ParkingLines.parkingLines[%].endPoint.y",
                ],
            ),
            (
                self.Columns.PMDCAMERA_RIGHT_PARKINGLINES_LINECONFIDENCE,
                [
                    "AP.svcModelProcessingOutput.data.pmdParkingLineListRight.parkingLines[%].lineConfidence",
                    "AP.svcModelProcessingOutput.data.parkingLineListRight.parkingLines[%].confidence",
                    "CarPC.EM_Thread.PmdRight.parkingLines[%].lineConfidence",
                    "SIM VFB.PMSDINSTANCE_rsc.ParkingLines.parkingLines[%].lineConfidence",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.parkingLines[%].lineConfidence",
                    "MTA_ADC5.PMSD_RSC_DATA.ParkingLines.parkingLines[%].confidence",
                    "SIM VFB.PMSD_RSC_DATA.ParkingLines.parkingLines[%].confidence",
                ],
            ),
            (
                self.Columns.PMDWS_FRONT_TIMESTAMP,
                [
                    "SIM VFB.PMSDINSTANCE_fc.WheelStopperLines.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.PMSD_FC_DATA.WheelStopperLines.sSigHeader.uiTimeStamp",
                    "AP.svcModelProcessingOutput.data.wheelStopperListFront.timestamp",
                    "SIM VFB.PMSD_FC_DATA.WheelStopperLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDWS_REAR_TIMESTAMP,
                [
                    "SIM VFB.PMSDINSTANCE_rc.WheelStopperLines.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.PMSD_RC_DATA.WheelStopperLines.sSigHeader.uiTimeStamp",
                    "AP.svcModelProcessingOutput.data.wheelStopperListRear.timestamp",
                    "SIM VFB.PMSD_RC_DATA.WheelStopperLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDWS_LEFT_TIMESTAMP,
                [
                    "SIM VFB.PMSDINSTANCE_lsc.WheelStopperLines.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.PMSD_LSC_DATA.WheelStopperLines.sSigHeader.uiTimeStamp",
                    "AP.svcModelProcessingOutput.data.wheelStopperListLeft.timestamp",
                    "SIM VFB.PMSD_LSC_DATA.WheelStopperLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDWS_RIGHT_TIMESTAMP,
                [
                    "SIM VFB.PMSDINSTANCE_rsc.WheelStopperLines.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.PMSD_RSC_DATA.WheelStopperLines.sSigHeader.uiTimeStamp",
                    "AP.svcModelProcessingOutput.data.wheelStopperListRight.timestamp",
                    "SIM VFB.PMSD_RSC_DATA.WheelStopperLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDWS_FRONT_SIGSTATUS,
                [
                    "MTA_ADC5.PMSD_FC_DATA.WheelStopperLines.sSigHeader.eSigStatus",
                    "MTA_ADC5.PMSD_FC_DATA.WheelStopperLines.sSigHeader.eSigStatus",
                    "AP.svcModelProcessingOutput.data.wheelStopperListFront.signalStatus",
                    "SIM VFB.PMSD_FC_DATA.WheelStopperLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDWS_REAR_SIGSTATUS,
                [
                    "MTA_ADC5.PMSD_RC_DATA.WheelStopperLines.sSigHeader.eSigStatus",
                    "MTA_ADC5.PMSD_RC_DATA.WheelStopperLines.sSigHeader.eSigStatus",
                    "AP.svcModelProcessingOutput.data.wheelStopperListRear.signalStatus",
                    "SIM VFB.PMSD_RC_DATA.WheelStopperLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDWS_LEFT_SIGSTATUS,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.WheelStopperLines.sSigHeader.eSigStatus",
                    "MTA_ADC5.PMSD_LSC_DATA.WheelStopperLines.sSigHeader.eSigStatus",
                    "AP.svcModelProcessingOutput.data.wheelStopperListLeft.signalStatus",
                    "SIM VFB.PMSD_LSC_DATA.WheelStopperLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDWS_RIGHT_SIGSTATUS,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.WheelStopperLines.sSigHeader.eSigStatus",
                    "MTA_ADC5.PMSD_RSC_DATA.WheelStopperLines.sSigHeader.eSigStatus",
                    "AP.svcModelProcessingOutput.data.wheelStopperListRight.signalStatus",
                    "SIM VFB.PMSD_RSC_DATA.WheelStopperLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDWS_FRONT_LINECONFIDENCE,
                [
                    "SIM VFB.PMSDINSTANCE_fc.WheelStopperLines.parkingLines[%].lineConfidence",
                    "MTA_ADC5.PMSD_FC_DATA.WheelStopperLines.wheelStoppers[%].confidence",
                    "AP.svcModelProcessingOutput.data.wheelStopperListFront.wheelStoppers[%].confidence",
                    "SIM VFB.PMSD_FC_DATA.WheelStopperLines.wheelStoppers[%].confidence",
                ],
            ),
            (
                self.Columns.PMDWS_REAR_LINECONFIDENCE,
                [
                    "SIM VFB.PMSDINSTANCE_rc.WheelStopperLines.parkingLines[%].lineConfidence",
                    "MTA_ADC5.PMSD_RC_DATA.WheelStopperLines.wheelStoppers[%].confidence",
                    "AP.svcModelProcessingOutput.data.wheelStopperListRear.wheelStoppers[%].confidence",
                    "SIM VFB.PMSD_RC_DATA.WheelStopperLines.wheelStoppers[%].confidence",
                ],
            ),
            (
                self.Columns.PMDWS_LEFT_LINECONFIDENCE,
                [
                    "SIM VFB.PMSDINSTANCE_lsc.WheelStopperLines.parkingLines[%].lineConfidence",
                    "MTA_ADC5.PMSD_LSC_DATA.WheelStopperLines.wheelStoppers[%].confidence",
                    "AP.svcModelProcessingOutput.data.wheelStopperListLeft.wheelStoppers[%].confidence",
                    "SIM VFB.PMSD_LSC_DATA.WheelStopperLines.wheelStoppers[%].confidence",
                ],
            ),
            (
                self.Columns.PMDWS_RIGHT_LINECONFIDENCE,
                [
                    "SIM VFB.PMSDINSTANCE_rsc.WheelStopperLines.parkingLines[%].lineConfidence",
                    "MTA_ADC5.PMSD_RSC_DATA.WheelStopperLines.wheelStoppers[%].confidence",
                    "AP.svcModelProcessingOutput.data.wheelStopperListRight.wheelStoppers[%].confidence",
                    "SIM VFB.PMSD_RSC_DATA.WheelStopperLines.wheelStoppers[%].confidence",
                ],
            ),
            (
                self.Columns.PMDWS_FRONT_NUMBEROFLINES,
                [
                    "SIM VFB.PMSDINSTANCE_fc.WheelStopperLines.numberOfLines",
                    "MTA_ADC5.PMSD_FC_DATA.WheelStopperLines.numberOfWheelStoppers",
                    "AP.svcModelProcessingOutput.data.wheelStopperListFront.numberOfWheelStoppers",
                    "SIM VFB.PMSD_FC_DATA.WheelStopperLines.numberOfWheelStoppers",
                ],
            ),
            (
                self.Columns.PMDWS_REAR_NUMBEROFLINES,
                [
                    "SIM VFB.PMSDINSTANCE_rc.WheelStopperLines.numberOfLines",
                    "MTA_ADC5.PMSD_RC_DATA.WheelStopperLines.numberOfWheelStoppers",
                    "AP.svcModelProcessingOutput.data.wheelStopperListRear.numberOfWheelStoppers",
                    "SIM VFB.PMSD_RC_DATA.WheelStopperLines.numberOfWheelStoppers",
                ],
            ),
            (
                self.Columns.PMDWS_LEFT_NUMBEROFLINES,
                [
                    "SIM VFB.PMSDINSTANCE_lsc.WheelStopperLines.numberOfLines",
                    "MTA_ADC5.PMSD_LSC_DATA.WheelStopperLines.numberOfWheelStoppers",
                    "AP.svcModelProcessingOutput.data.wheelStopperListLeft.numberOfWheelStoppers",
                    "SIM VFB.PMSD_LSC_DATA.WheelStopperLines.numberOfWheelStoppers",
                ],
            ),
            (
                self.Columns.PMDWS_RIGHT_NUMBEROFLINES,
                [
                    "SIM VFB.PMSDINSTANCE_rsc.WheelStopperLines.numberOfLines",
                    "MTA_ADC5.PMSD_RSC_DATA.WheelStopperLines.numberOfWheelStoppers",
                    "AP.svcModelProcessingOutput.data.wheelStopperListRight.numberOfWheelStoppers",
                    "SIM VFB.PMSD_RSC_DATA.WheelStopperLines.numberOfWheelStoppers",
                ],
            ),
            (
                self.Columns.PMDWS_FRONT_LINESTARTX,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperListFront.wheelStoppers[%].startPoint.x",
                    "SIM VFB.PMSD_FC_DATA.WheelStopperLines.wheelStoppers[%].startPoint.x",
                ],
            ),
            (
                self.Columns.PMDWS_FRONT_LINESTARTY,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperListFront.wheelStoppers[%].startPoint.y",
                    "SIM VFB.PMSD_FC_DATA.WheelStopperLines.wheelStoppers[%].startPoint.y",
                ],
            ),
            (
                self.Columns.PMDWS_FRONT_LINEENDX,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperListFront.wheelStoppers[%].endPoint.x",
                    "SIM VFB.PMSD_FC_DATA.WheelStopperLines.wheelStoppers[%].endPoint.x",
                ],
            ),
            (
                self.Columns.PMDWS_FRONT_LINEENDY,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperListFront.wheelStoppers[%].endPoint.y",
                    "SIM VFB.PMSD_FC_DATA.WheelStopperLines.wheelStoppers[%].endPoint.y",
                ],
            ),
            (
                self.Columns.PMDWS_REAR_LINESTARTX,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperListRear.wheelStoppers[%].startPoint.x",
                    "SIM VFB.PMSD_RC_DATA.WheelStopperLines.wheelStoppers[%].startPoint.x",
                ],
            ),
            (
                self.Columns.PMDWS_REAR_LINESTARTY,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperListRear.wheelStoppers[%].startPoint.y",
                    "SIM VFB.PMSD_RC_DATA.WheelStopperLines.wheelStoppers[%].startPoint.y",
                ],
            ),
            (
                self.Columns.PMDWS_REAR_LINEENDX,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperListRear.wheelStoppers[%].endPoint.x",
                    "SIM VFB.PMSD_FC_DATA.WheelStopperLines.wheelStoppers[%].endPoint.x",
                ],
            ),
            (
                self.Columns.PMDWS_REAR_LINEENDY,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperListRear.wheelStoppers[%].endPoint.y",
                    "SIM VFB.PMSD_FC_DATA.WheelStopperLines.wheelStoppers[%].endPoint.y",
                ],
            ),
            (
                self.Columns.PMDWS_LEFT_LINESTARTX,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperListLeft.wheelStoppers[%].startPoint.x",
                    "SIM VFB.PMSD_LSC_DATA.WheelStopperLines.wheelStoppers[%].startPoint.x",
                ],
            ),
            (
                self.Columns.PMDWS_LEFT_LINESTARTY,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperListLeft.wheelStoppers[%].startPoint.y",
                    "SIM VFB.PMSD_LSC_DATA.WheelStopperLines.wheelStoppers[%].startPoint.y",
                ],
            ),
            (
                self.Columns.PMDWS_LEFT_LINEENDX,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperListLeft.wheelStoppers[%].endPoint.x",
                    "SIM VFB.PMSD_LSC_DATA.WheelStopperLines.wheelStoppers[%].endPoint.x",
                ],
            ),
            (
                self.Columns.PMDWS_LEFT_LINEENDY,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperListLeft.wheelStoppers[%].endPoint.y",
                    "SIM VFB.PMSD_LSC_DATA.WheelStopperLines.wheelStoppers[%].endPoint.y",
                ],
            ),
            (
                self.Columns.PMDWS_RIGHT_LINESTARTX,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperListRight.wheelStoppers[%].startPoint.x",
                    "SIM VFB.PMSD_RSC_DATA.WheelStopperLines.wheelStoppers[%].startPoint.x",
                ],
            ),
            (
                self.Columns.PMDWS_RIGHT_LINESTARTY,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperListRight.wheelStoppers[%].startPoint.y",
                    "SIM VFB.PMSD_RSC_DATA.WheelStopperLines.wheelStoppers[%].startPoint.y",
                ],
            ),
            (
                self.Columns.PMDWS_RIGHT_LINEENDX,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperListRight.wheelStoppers[%].endPoint.x",
                    "SIM VFB.PMSD_RSC_DATA.WheelStopperLines.wheelStoppers[%].endPoint.x",
                ],
            ),
            (
                self.Columns.PMDWS_RIGHT_LINEENDY,
                [
                    "AP.svcModelProcessingOutput.data.wheelStopperListRight.wheelStoppers[%].endPoint.y",
                    "SIM VFB.PMSD_RSC_DATA.WheelStopperLines.wheelStoppers[%].endPoint.y",
                ],
            ),
            (
                self.Columns.PMDWL_FRONT_TIMESTAMP,
                [
                    "MTA_ADC5.PMSD_FC_DATA.WheelLockerList.sSigHeader.uiTimeStamp",
                    "AP.svcModelProcessingOutput.data.wheelLockerListFront.timestamp",
                    "SIM VFB.PMSD_FC_DATA.WheelLockerList.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDWL_REAR_TIMESTAMP,
                [
                    "MTA_ADC5.PMSD_RC_DATA.WheelLockerList.sSigHeader.uiTimeStamp",
                    "AP.svcModelProcessingOutput.data.wheelLockerListRear.timestamp",
                    "SIM VFB.PMSD_RC_DATA.WheelLockerList.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDWL_LEFT_TIMESTAMP,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.WheelLockerList.sSigHeader.uiTimeStamp",
                    "AP.svcModelProcessingOutput.data.wheelLockerListLeft.timestamp",
                    "SIM VFB.PMSD_LSC_DATA.WheelLockerList.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDWL_RIGHT_TIMESTAMP,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.WheelLockerList.sSigHeader.uiTimeStamp",
                    "AP.svcModelProcessingOutput.data.wheelLockerListRight.timestamp",
                    "SIM VFB.PMSD_RSC_DATA.WheelLockerList.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDWL_FRONT_SIGSTATUS,
                [
                    "MTA_ADC5.PMSD_FC_DATA.WheelLockerList.sSigHeader.eSigStatus",
                    "AP.svcModelProcessingOutput.data.wheelLockerListFront.signalStatus",
                    "SIM VFB.PMSD_FC_DATA.WheelLockerList.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDWL_REAR_SIGSTATUS,
                [
                    "MTA_ADC5.PMSD_RC_DATA.WheelLockerList.sSigHeader.eSigStatus",
                    "AP.svcModelProcessingOutput.data.wheelLockerListRear.signalStatus",
                    "SIM VFB.PMSD_RC_DATA.WheelLockerList.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDWL_LEFT_SIGSTATUS,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.WheelLockerList.sSigHeader.eSigStatus",
                    "AP.svcModelProcessingOutput.data.wheelLockerListLeft.signalStatus",
                    "SIM VFB.PMSD_LSC_DATA.WheelLockerList.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDWL_RIGHT_SIGSTATUS,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.WheelLockerList.sSigHeader.eSigStatus",
                    "AP.svcModelProcessingOutput.data.wheelLockerListRight.signalStatus",
                    "SIM VFB.PMSD_RSC_DATA.WheelLockerList.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDWL_FRONT_LINECONFIDENCE,
                [
                    "MTA_ADC5.PMSD_FC_DATA.WheelLockerList.wheelLockers[%].confidence",
                    "AP.svcModelProcessingOutput.data.wheelLockerListFront.wheelLockers[%].confidence",
                    "SIM VFB.PMSD_FC_DATA.WheelLockerList.wheelLockers[%].confidence",
                ],
            ),
            (
                self.Columns.PMDWL_REAR_LINECONFIDENCE,
                [
                    "MTA_ADC5.PMSD_RC_DATA.WheelLockerList.wheelLockers[%].confidence",
                    "AP.svcModelProcessingOutput.data.wheelLockerListRear.wheelLockers[%].confidence",
                    "SIM VFB.PMSD_RC_DATA.WheelLockerList.wheelLockers[%].confidence",
                ],
            ),
            (
                self.Columns.PMDWL_LEFT_LINECONFIDENCE,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.WheelLockerList.wheelLockers[%].confidence",
                    "AP.svcModelProcessingOutput.data.wheelLockerListLeft.wheelLockers[%].confidence",
                    "SIM VFB.PMSD_LSC_DATA.WheelLockerList.wheelLockers[%].confidence",
                ],
            ),
            (
                self.Columns.PMDWL_RIGHT_LINECONFIDENCE,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.WheelLockerList.wheelLockers[%].confidence",
                    "AP.svcModelProcessingOutput.data.wheelLockerListRight.wheelLockers[%].confidence",
                    "SIM VFB.PMSD_RSC_DATA.WheelLockerList.wheelLockers[%].confidence",
                ],
            ),
            (
                self.Columns.PMDWL_FRONT_NUMBEROFWHEELLOCKERS,
                [
                    "MTA_ADC5.PMSD_FC_DATA.WheelLockerList.numberOfWheelLockers",
                    "AP.svcModelProcessingOutput.data.wheelLockerListFront.numberOfWheelLockers",
                    "SIM VFB.PMSD_FC_DATA.WheelLockerList.numberOfWheelLockers",
                ],
            ),
            (
                self.Columns.PMDWL_REAR_NUMBEROFWHEELLOCKERS,
                [
                    "MTA_ADC5.PMSD_RC_DATA.WheelLockerList.numberOfWheelLockers",
                    "AP.svcModelProcessingOutput.data.wheelLockerListRear.numberOfWheelLockers",
                    "SIM VFB.PMSD_RC_DATA.WheelLockerList.numberOfWheelLockers",
                ],
            ),
            (
                self.Columns.PMDWL_LEFT_NUMBEROFWHEELLOCKERS,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.WheelLockerList.numberOfWheelLockers",
                    "AP.svcModelProcessingOutput.data.wheelLockerListLeft.numberOfWheelLockers",
                    "SIM VFB.PMSD_LSC_DATA.WheelLockerList.numberOfWheelLockers",
                ],
            ),
            (
                self.Columns.PMDWL_RIGHT_NUMBEROFWHEELLOCKERS,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.WheelLockerList.numberOfWheelLockers",
                    "AP.svcModelProcessingOutput.data.wheelLockerListRight.numberOfWheelLockers",
                    "SIM VFB.PMSD_RSC_DATA.WheelLockerList.numberOfWheelLockers",
                ],
            ),
            (
                self.Columns.PMDWL_FRONT_LINESTARTX,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerListFront.wheelLockers[%].DRIV.start.x",
                ],
            ),
            (
                self.Columns.PMDWL_FRONT_LINESTARTY,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerListFront.wheelLockers[%].DRIV.start.y",
                ],
            ),
            (
                self.Columns.PMDWL_FRONT_LINEENDX,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerListFront.wheelLockers[%].DRIV.end.x",
                ],
            ),
            (
                self.Columns.PMDWL_FRONT_LINEENDY,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerListFront.wheelLockers[%].DRIV.end.y",
                ],
            ),
            (
                self.Columns.PMDWL_REAR_LINESTARTX,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerListRear.wheelLockers[%].DRIV.start.x",
                ],
            ),
            (
                self.Columns.PMDWL_REAR_LINESTARTY,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerListRear.wheelLockers[%].DRIV.start.y",
                ],
            ),
            (
                self.Columns.PMDWL_REAR_LINEENDX,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerListRear.wheelLockers[%].DRIV.end.x",
                ],
            ),
            (
                self.Columns.PMDWL_REAR_LINEENDY,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerListRear.wheelLockers[%].DRIV.end.y",
                ],
            ),
            (
                self.Columns.PMDWL_LEFT_LINESTARTX,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerListLeft.wheelLockers[%].DRIV.start.x",
                ],
            ),
            (
                self.Columns.PMDWL_LEFT_LINESTARTY,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerListLeft.wheelLockers[%].DRIV.start.y",
                ],
            ),
            (
                self.Columns.PMDWL_LEFT_LINEENDX,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerListLeft.wheelLockers[%].DRIV.end.x",
                ],
            ),
            (
                self.Columns.PMDWL_LEFT_LINEENDY,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerListLeft.wheelLockers[%].DRIV.end.y",
                ],
            ),
            (
                self.Columns.PMDWL_RIGHT_LINESTARTX,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerListRight.wheelLockers[%].DRIV.start.x",
                ],
            ),
            (
                self.Columns.PMDWL_RIGHT_LINESTARTY,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerListRight.wheelLockers[%].DRIV.start.y",
                ],
            ),
            (
                self.Columns.PMDWL_RIGHT_LINEENDX,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerListRight.wheelLockers[%].DRIV.end.x",
                ],
            ),
            (
                self.Columns.PMDWL_RIGHT_LINEENDY,
                [
                    "AP.svcModelProcessingOutput.data.wheelLockerListRight.wheelLockers[%].DRIV.end.y",
                ],
            ),
            (
                self.Columns.PMDSL_FRONT_TIMESTAMP,
                [
                    "MTA_ADC5.PMSD_FC_DATA.StopLines.sSigHeader.uiTimeStamp",
                    "AP.svcModelProcessingOutput.data.stopLineListFront.timestamp",
                    "SIM VFB.PMSD_FC_DATA.StopLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDSL_REAR_TIMESTAMP,
                [
                    "MTA_ADC5.PMSD_RC_DATA.StopLines.sSigHeader.uiTimeStamp",
                    "AP.svcModelProcessingOutput.data.stopLineListRear.timestamp",
                    "SIM VFB.PMSD_RC_DATA.StopLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDSL_LEFT_TIMESTAMP,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.StopLines.sSigHeader.uiTimeStamp",
                    "AP.svcModelProcessingOutput.data.stopLineListLeft.timestamp",
                    "SIM VFB.PMSD_LSC_DATA.StopLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDSL_RIGHT_TIMESTAMP,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.StopLines.sSigHeader.uiTimeStamp",
                    "AP.svcModelProcessingOutput.data.stopLineListRight.timestamp",
                    "SIM VFB.PMSD_RSC_DATA.StopLines.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDSL_FRONT_SIGSTATUS,
                [
                    "MTA_ADC5.PMSD_FC_DATA.StopLines.sSigHeader.eSigStatus",
                    "AP.svcModelProcessingOutput.data.stopLineListFront.signalStatus",
                    "SIM VFB.PMSD_FC_DATA.StopLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDSL_REAR_SIGSTATUS,
                [
                    "MTA_ADC5.PMSD_RC_DATA.StopLines.sSigHeader.eSigStatus",
                    "AP.svcModelProcessingOutput.data.stopLineListRear.signalStatus",
                    "SIM VFB.PMSD_RC_DATA.StopLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDSL_LEFT_SIGSTATUS,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.StopLines.sSigHeader.eSigStatus",
                    "AP.svcModelProcessingOutput.data.stopLineListLeft.signalStatus",
                    "SIM VFB.PMSD_LSC_DATA.StopLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDSL_RIGHT_SIGSTATUS,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.StopLines.sSigHeader.eSigStatus",
                    "AP.svcModelProcessingOutput.data.stopLineListRight.signalStatus",
                    "SIM VFB.PMSD_RSC_DATA.StopLines.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDSL_FRONT_LINECONFIDENCE,
                [
                    "MTA_ADC5.PMSD_FC_DATA.StopLines.stopLines[%].confidence",
                    "AP.svcModelProcessingOutput.data.stopLineListFront.stopLines[%].confidence",
                    "SIM VFB.PMSD_FC_DATA.StopLines.stopLines[%].confidence",
                ],
            ),
            (
                self.Columns.PMDSL_REAR_LINECONFIDENCE,
                [
                    "MTA_ADC5.PMSD_RC_DATA.StopLines.stopLines[%].confidence",
                    "AP.svcModelProcessingOutput.data.stopLineListRear.stopLines[%].confidence",
                    "SIM VFB.PMSD_RC_DATA.StopLines.stopLines[%].confidence",
                ],
            ),
            (
                self.Columns.PMDSL_LEFT_LINECONFIDENCE,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.StopLines.stopLines[%].confidence",
                    "AP.svcModelProcessingOutput.data.stopLineListLeft.stopLines[%].confidence",
                    "SIM VFB.PMSD_LSC_DATA.StopLines.stopLines[%].confidence",
                ],
            ),
            (
                self.Columns.PMDSL_RIGHT_LINECONFIDENCE,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.StopLines.stopLines[%].confidence",
                    "AP.svcModelProcessingOutput.data.stopLineListRight.stopLines[%].confidence",
                    "SIM VFB.PMSD_RSC_DATA.StopLines.stopLines[%].confidence",
                ],
            ),
            (
                self.Columns.PMDSL_FRONT_NUMBEROFLINES,
                [
                    "MTA_ADC5.PMSD_FC_DATA.StopLines.numberOfLines",
                    "AP.svcModelProcessingOutput.data.stopLineListFront.numberOfLines",
                    "SIM VFB.PMSD_FC_DATA.StopLines.numberOfLines",
                ],
            ),
            (
                self.Columns.PMDSL_REAR_NUMBEROFLINES,
                [
                    "MTA_ADC5.PMSD_RC_DATA.StopLines.numberOfLines",
                    "AP.svcModelProcessingOutput.data.stopLineListRear.numberOfLines",
                    "SIM VFB.PMSD_RC_DATA.StopLines.numberOfLines",
                ],
            ),
            (
                self.Columns.PMDSL_LEFT_NUMBEROFLINES,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.StopLines.numberOfLines",
                    "AP.svcModelProcessingOutput.data.stopLineListLeft.numberOfLines",
                    "SIM VFB.PMSD_LSC_DATA.StopLines.numberOfLines",
                ],
            ),
            (
                self.Columns.PMDSL_RIGHT_NUMBEROFLINES,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.StopLines.numberOfLines",
                    "AP.svcModelProcessingOutput.data.stopLineListRight.numberOfLines",
                    "SIM VFB.PMSD_RSC_DATA.StopLines.numberOfLines",
                ],
            ),
            (
                self.Columns.PMDSL_FRONT_STARTPOINTX,
                [
                    "MTA_ADC5.PMSD_FC_DATA.StopLines.stopLines[%].startPoint.x",
                    "AP.svcModelProcessingOutput.data.stopLineListFront.stopLines[%].start.x",
                    "SIM VFB.PMSD_FC_DATA.StopLines.stopLines[%].startPoint.x",
                ],
            ),
            (
                self.Columns.PMDSL_FRONT_STARTPOINTY,
                [
                    "MTA_ADC5.PMSD_FC_DATA.StopLines.stopLines[%].startPoint.y",
                    "AP.svcModelProcessingOutput.data.stopLineListFront.stopLines[%].start.y",
                    "SIM VFB.PMSD_FC_DATA.StopLines.stopLines[%].startPoint.y",
                ],
            ),
            (
                self.Columns.PMDSL_FRONT_ENDPOINTX,
                [
                    "MTA_ADC5.PMSD_FC_DATA.StopLines.stopLines[%].endPoint.x",
                    "AP.svcModelProcessingOutput.data.stopLineListFront.stopLines[%].end.x",
                    "SIM VFB.PMSD_FC_DATA.StopLines.stopLines[%].endPoint.x",
                ],
            ),
            (
                self.Columns.PMDSL_FRONT_ENDPOINTY,
                [
                    "MTA_ADC5.PMSD_FC_DATA.StopLines.stopLines[%].endPoint.y",
                    "AP.svcModelProcessingOutput.data.stopLineListFront.stopLines[%].end.y",
                    "SIM VFB.PMSD_FC_DATA.StopLines.stopLines[%].endPoint.y",
                ],
            ),
            (
                self.Columns.PMDSL_REAR_STARTPOINTX,
                [
                    "MTA_ADC5.PMSD_RC_DATA.StopLines.stopLines[%].startPoint.x",
                    "AP.svcModelProcessingOutput.data.stopLineListRear.stopLines[%].start.x",
                    "SIM VFB.PMSD_RC_DATA.StopLines.stopLines[%].startPoint.x",
                ],
            ),
            (
                self.Columns.PMDSL_REAR_STARTPOINTY,
                [
                    "MTA_ADC5.PMSD_RC_DATA.StopLines.stopLines[%].startPoint.y",
                    "AP.svcModelProcessingOutput.data.stopLineListRear.stopLines[%].start.y",
                    "SIM VFB.PMSD_RC_DATA.StopLines.stopLines[%].startPoint.y",
                ],
            ),
            (
                self.Columns.PMDSL_REAR_ENDPOINTX,
                [
                    "MTA_ADC5.PMSD_RC_DATA.StopLines.stopLines[%].endPoint.x",
                    "AP.svcModelProcessingOutput.data.stopLineListRear.stopLines[%].end.x",
                    "SIM VFB.PMSD_RC_DATA.StopLines.stopLines[%].endPoint.x",
                ],
            ),
            (
                self.Columns.PMDSL_REAR_ENDPOINTY,
                [
                    "MTA_ADC5.PMSD_RC_DATA.StopLines.stopLines[%].endPoint.y",
                    "AP.svcModelProcessingOutput.data.stopLineListRear.stopLines[%].end.y",
                    "SIM VFB.PMSD_RC_DATA.StopLines.stopLines[%].endPoint.y",
                ],
            ),
            (
                self.Columns.PMDSL_LEFT_STARTPOINTX,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.StopLines.stopLines[%].startPoint.x",
                    "AP.svcModelProcessingOutput.data.stopLineListLeft.stopLines[%].start.x",
                    "SIM VFB.PMSD_LSC_DATA.StopLines.stopLines[%].startPoint.x",
                ],
            ),
            (
                self.Columns.PMDSL_LEFT_STARTPOINTY,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.StopLines.stopLines[%].startPoint.y",
                    "AP.svcModelProcessingOutput.data.stopLineListLeft.stopLines[%].start.y",
                    "SIM VFB.PMSD_LSC_DATA.StopLines.stopLines[%].startPoint.y",
                ],
            ),
            (
                self.Columns.PMDSL_LEFT_ENDPOINTX,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.StopLines.stopLines[%].endPoint.x",
                    "AP.svcModelProcessingOutput.data.stopLineListLeft.stopLines[%].end.x",
                    "SIM VFB.PMSD_LSC_DATA.StopLines.stopLines[%].endPoint.x",
                ],
            ),
            (
                self.Columns.PMDSL_LEFT_ENDPOINTY,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.StopLines.stopLines[%].endPoint.y",
                    "AP.svcModelProcessingOutput.data.stopLineListLeft.stopLines[%].end.y",
                    "SIM VFB.PMSD_LSC_DATA.StopLines.stopLines[%].endPoint.y",
                ],
            ),
            (
                self.Columns.PMDSL_RIGHT_STARTPOINTX,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.StopLines.stopLines[%].startPoint.x",
                    "AP.svcModelProcessingOutput.data.stopLineListRight.stopLines[%].start.x",
                    "SIM VFB.PMSD_RSC_DATA.StopLines.stopLines[%].startPoint.x",
                ],
            ),
            (
                self.Columns.PMDSL_RIGHT_STARTPOINTY,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.StopLines.stopLines[%].startPoint.y",
                    "AP.svcModelProcessingOutput.data.stopLineListRight.stopLines[%].start.y",
                    "SIM VFB.PMSD_RSC_DATA.StopLines.stopLines[%].startPoint.y",
                ],
            ),
            (
                self.Columns.PMDSL_RIGHT_ENDPOINTX,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.StopLines.stopLines[%].endPoint.x",
                    "AP.svcModelProcessingOutput.data.stopLineListRight.stopLines[%].end.x",
                    "SIM VFB.PMSD_RSC_DATA.StopLines.stopLines[%].endPoint.x",
                ],
            ),
            (
                self.Columns.PMDSL_RIGHT_ENDPOINTY,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.StopLines.stopLines[%].endPoint.y",
                    "AP.svcModelProcessingOutput.data.stopLineListRight.stopLines[%].end.y",
                    "SIM VFB.PMSD_RSC_DATA.StopLines.stopLines[%].endPoint.y",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_FRONT_TIMESTAMP,
                [
                    "MTA_ADC5.PMSD_FC_DATA.PedestrianCrossings.sSigHeader.uiTimeStamp",
                    "AP.svcModelProcessingOutput.data.pedestrCrossListFront.timestamp",
                    "SIM VFB.PMSD_FC_DATA.PedestrianCrossings.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_REAR_TIMESTAMP,
                [
                    "MTA_ADC5.PMSD_RC_DATA.PedestrianCrossings.sSigHeader.uiTimeStamp",
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRear.timestamp",
                    "SIM VFB.PMSD_RC_DATA.PedestrianCrossings.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_LEFT_TIMESTAMP,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.PedestrianCrossings.sSigHeader.uiTimeStamp",
                    "AP.svcModelProcessingOutput.data.pedestrCrossListLeft.timestamp",
                    "SIM VFB.PMSD_LSC_DATA.PedestrianCrossings.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_RIGHT_TIMESTAMP,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.PedestrianCrossings.sSigHeader.uiTimeStamp",
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRight.timestamp",
                    "SIM VFB.PMSD_RSC_DATA.PedestrianCrossings.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_FRONT_SIGSTATUS,
                [
                    "MTA_ADC5.PMSD_FC_DATA.PedestrianCrossings.sSigHeader.eSigStatus",
                    "AP.svcModelProcessingOutput.data.pedestrCrossListFront.signalStatus",
                    "SIM VFB.PMSD_FC_DATA.PedestrianCrossings.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_REAR_SIGSTATUS,
                [
                    "MTA_ADC5.PMSD_RC_DATA.PedestrianCrossings.sSigHeader.eSigStatus",
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRear.signalStatus",
                    "SIM VFB.PMSD_RC_DATA.PedestrianCrossings.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_LEFT_SIGSTATUS,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.PedestrianCrossings.sSigHeader.eSigStatus",
                    "AP.svcModelProcessingOutput.data.pedestrCrossListLeft.signalStatus",
                    "SIM VFB.PMSD_LSC_DATA.PedestrianCrossings.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_RIGHT_SIGSTATUS,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.PedestrianCrossings.sSigHeader.eSigStatus",
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRight.signalStatus",
                    "SIM VFB.PMSD_RSC_DATA.PedestrianCrossings.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_FRONT_LINECONFIDENCE,
                [
                    "MTA_ADC5.PMSD_FC_DATA.PedestrianCrossings.pedestrianCrossings[%].confidence",
                    "AP.svcModelProcessingOutput.data.pedestrCrossListFront.pedCrossings[%].confidence",
                    "SIM VFB.PMSD_FC_DATA.PedestrianCrossings.pedestrianCrossings[%].confidence",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_REAR_LINECONFIDENCE,
                [
                    "MTA_ADC5.PMSD_RC_DATA.PedestrianCrossings.pedestrianCrossings[%].confidence",
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRear.pedCrossings[%].confidence",
                    "SIM VFB.PMSD_RC_DATA.PedestrianCrossings.pedestrianCrossings[%].confidence",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_LEFT_LINECONFIDENCE,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.PedestrianCrossings.pedestrianCrossings[%].confidence",
                    "AP.svcModelProcessingOutput.data.pedestrCrossListLeft.pedCrossings[%].confidence",
                    "SIM VFB.PMSD_LSC_DATA.PedestrianCrossings.pedestrianCrossings[%].confidence",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_RIGHT_LINECONFIDENCE,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.PedestrianCrossings.pedestrianCrossings[%].confidence",
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRight.pedCrossings[%].confidence",
                    "SIM VFB.PMSD_RSC_DATA.PedestrianCrossings.pedestrianCrossings[%].confidence",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_FRONT_NUMBEROFCROSSINGS,
                [
                    "MTA_ADC5.PMSD_FC_DATA.PedestrianCrossings.numberOfCrossings",
                    "AP.svcModelProcessingOutput.data.pedestrCrossListFront.numberOfCrossings",
                    "SIM VFB.PMSD_FC_DATA.PedestrianCrossings.numberOfCrossings",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_REAR_NUMBEROFCROSSINGS,
                [
                    "MTA_ADC5.PMSD_RC_DATA.PedestrianCrossings.numberOfCrossings",
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRear.numberOfCrossings",
                    "SIM VFB.PMSD_RC_DATA.PedestrianCrossings.numberOfCrossings",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_LEFT_NUMBEROFCROSSINGS,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.PedestrianCrossings.numberOfCrossings",
                    "AP.svcModelProcessingOutput.data.pedestrCrossListLeft.numberOfCrossings",
                    "SIM VFB.PMSD_LSC_DATA.PedestrianCrossings.numberOfCrossings",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_RIGHT_NUMBEROFCROSSINGS,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.PedestrianCrossings.numberOfCrossings",
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRight.numberOfCrossings",
                    "SIM VFB.PMSD_RSC_DATA.PedestrianCrossings.numberOfCrossings",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_FRONT_P0_X,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListFront.pedCrossings[%].bound_0.x",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_FRONT_P0_Y,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListFront.pedCrossings[%].bound_0.y",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_FRONT_P1_X,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListFront.pedCrossings[%].bound_1.x",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_FRONT_P1_Y,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListFront.pedCrossings[%].bound_1.y",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_FRONT_P2_X,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListFront.pedCrossings[%].bound_2.x",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_FRONT_P2_Y,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListFront.pedCrossings[%].bound_2.y",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_FRONT_P3_X,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListFront.pedCrossings[%].bound_3.x",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_FRONT_P3_Y,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListFront.pedCrossings[%].bound_3.y",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_REAR_P0_X,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRear.pedCrossings[%].bound_0.x",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_REAR_P0_Y,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRear.pedCrossings[%].bound_0.y",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_REAR_P1_X,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRear.pedCrossings[%].bound_1.x",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_REAR_P1_Y,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRear.pedCrossings[%].bound_1.y",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_REAR_P2_X,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRear.pedCrossings[%].bound_2.x",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_REAR_P2_Y,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRear.pedCrossings[%].bound_2.y",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_REAR_P3_X,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRear.pedCrossings[%].bound_3.x",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_REAR_P3_Y,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRear.pedCrossings[%].bound_3.y",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_LEFT_P0_X,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListLeft.pedCrossings[%].bound_0.x",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_LEFT_P0_Y,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListLeft.pedCrossings[%].bound_0.y",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_LEFT_P1_X,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListLeft.pedCrossings[%].bound_1.x",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_LEFT_P1_Y,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListLeft.pedCrossings[%].bound_1.y",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_LEFT_P2_X,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListLeft.pedCrossings[%].bound_2.x",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_LEFT_P2_Y,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListLeft.pedCrossings[%].bound_2.y",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_LEFT_P3_X,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListLeft.pedCrossings[%].bound_3.x",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_LEFT_P3_Y,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListLeft.pedCrossings[%].bound_3.y",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_RIGHT_P0_X,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRight.pedCrossings[%].bound_0.x",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_RIGHT_P0_Y,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRight.pedCrossings[%].bound_0.y",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_RIGHT_P1_X,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRight.pedCrossings[%].bound_1.x",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_RIGHT_P1_Y,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRight.pedCrossings[%].bound_1.y",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_RIGHT_P2_X,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRight.pedCrossings[%].bound_2.x",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_RIGHT_P2_Y,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRight.pedCrossings[%].bound_2.y",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_RIGHT_P3_X,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRight.pedCrossings[%].bound_3.x",
                ],
            ),
            (
                self.Columns.PMDPEDCROS_RIGHT_P3_Y,
                [
                    "AP.svcModelProcessingOutput.data.pedestrCrossListRight.pedCrossings[%].bound_3.y",
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
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.NUMPCLDELIMITERS_TIMESTAMP,
                [
                    "pclOutput.sSigHeader.uiTimeStamp",
                    "CarPC.EM_Thread.CemPclOutput.signalHeader.uiTimeStamp",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.sSigHeader.uiTimeStamp",
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingDelimiters.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.NUMPCLDELIMITERS,
                [
                    "pclOutput.numberOfDelimiters",
                    "CarPC.EM_Thread.CemPclOutput.numPclDelimiters",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.numberOfDelimiters",
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingDelimiters.numberOfDelimiters",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.numberOfDelimiters",
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
                self.Columns.CEM_PCL_DELIMITERID,
                [
                    "pclOutput.delimiters._%_.delimiterId",
                    "CarPC.EM_Thread.CemPclOutput.pclDelimiters[%].delimiterId",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.delimiters[%].id",
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingDelimiters.delimiters[%].delimiterId",
                ],
            ),
            (
                self.Columns.CEM_PCL_DELIMITERTYPE,
                [
                    "pclOutput.delimiters._%_.delimiterType",
                    "CarPC.EM_Thread.CemPclOutput.pclDelimiters[%].delimiterType",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.delimiters[%].type",
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingDelimiters.delimiters[%].delimiterType",
                ],
            ),
            (
                self.Columns.CEM_PCL_P0_X,
                [
                    "pclOutput.delimiters._%_.startPointXPosition",
                    "CarPC.EM_Thread.CemPclOutput.pclDelimiters[%].startPointXPosition",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.delimiters[%].startPointXPosition",
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingDelimiters.delimiters[%].startPointXPosition",
                ],
            ),
            (
                self.Columns.CEM_PCL_P0_Y,
                [
                    "pclOutput.delimiters._%_.startPointYPosition",
                    "CarPC.EM_Thread.CemPclOutput.pclDelimiters[%].startPointYPosition",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.delimiters[%].startPointYPosition",
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingDelimiters.delimiters[%].startPointYPosition",
                ],
            ),
            (
                self.Columns.CEM_PCL_P1_X,
                [
                    "pclOutput.delimiters._%_.endPointXPosition",
                    "CarPC.EM_Thread.CemPclOutput.pclDelimiters[%].endPointXPosition",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.delimiters[%].endPointXPosition",
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingDelimiters.delimiters[%].endPointXPosition",
                ],
            ),
            (
                self.Columns.CEM_PCL_P1_Y,
                [
                    "pclOutput.delimiters._%_.endPointYPosition",
                    "CarPC.EM_Thread.CemPclOutput.pclDelimiters[%].endPointYPosition",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.delimiters[%].endPointYPosition",
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingDelimiters.delimiters[%].endPointYPosition",
                ],
            ),
            (
                self.Columns.CEM_PCL_CONFIDENCEPERCENT,
                [
                    "pclOutput.delimiters._%_.confidencePercent",
                    "CarPC.EM_Thread.CemPclOutput.pclDelimiters[%].confidencePercent",
                    "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.delimiters[%].confidence",
                    "ADC5xx_Device.CEM_EM_DATA.AUPDF_ParkingDelimiters.delimiters[%].confidencePercent",
                ],
            ),
            (
                self.Columns.FRONT_TIMESTAMP,
                [
                    "CarPC.EM_Thread.DynamicObjectsFront.timestamp",
                    "MTA_ADC5.RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.FRONT_NUMOBJECTS,
                [
                    "CarPC.EM_Thread.DynamicObjectsFront.numObjects",
                    "MTA_ADC5.RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.numberOfObjects",
                ],
            ),
            (
                self.Columns.FRONT_OBJECTS_SIGSTATUS,
                [
                    "CarPC.EM_Thread.DynamicObjectsFront.signalState",
                    "MTA_ADC5.RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
                ],
            ),
            # (
            #     self.Columns.FRONT_OBJECTS_ID,
            #     "CarPC.EM_Thread.DynamicObjectsFront.objects[%].id",
            # ),
            (
                self.Columns.FRONT_OBJECTS_CLASSTYPE,
                [
                    "CarPC.EM_Thread.DynamicObjectsFront.objects[%].classType",
                    "MTA_ADC5.RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].classType",
                ],
            ),
            (
                self.Columns.FRONT_OBJECTS_CONFIDENCE,
                [
                    "CarPC.EM_Thread.DynamicObjectsFront.objects[%].confidence",
                    "MTA_ADC5.RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].confidence",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_REFERENCEPOINTX,
                [
                    "CarPC.EM_Thread.DynamicObjectsFront.objects[%].shape.referencePoint.x",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.referencePoint.x",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_REFERENCEPOINTY,
                [
                    "CarPC.EM_Thread.DynamicObjectsFront.objects[%].shape.referencePoint.y",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.referencePoint.y",
                ],
            ),
            (
                self.Columns.FRONT_OBJECTS_CENTERPOINTWORLD_X,
                [
                    "CarPC.EM_Thread.DynamicObjectsFront.objects[%].centerPointWorld.x",
                    "MTA_ADC5.RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_x",
                ],
            ),
            (
                self.Columns.FRONT_OBJECTS_CENTERPOINTWORLD_Y,
                [
                    "CarPC.EM_Thread.DynamicObjectsFront.objects[%].centerPointWorld.y",
                    "MTA_ADC5.RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_y",
                ],
            ),
            (
                self.Columns.FRONT_OBJECTS_CENTERPOINTWORLD_Z,
                [
                    "CarPC.EM_Thread.DynamicObjectsFront.objects[%].centerPointWorld.z",
                    "MTA_ADC5.RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_z",
                ],
            ),
            (
                self.Columns.FRONT_OBJECTS_WIDTH,
                [
                    "MTA_ADC5.RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.width",
                ],
            ),
            (
                self.Columns.FRONT_OBJECTS_LENGTH,
                [
                    "MTA_ADC5.RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.length",
                ],
            ),
            (
                self.Columns.FRONT_OBJECTS_HEIGHT,
                [
                    "MTA_ADC5.RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.height",
                ],
            ),
            # (
            #     self.Columns.FRONT_OBJECTS_PLANESIZEWORLD_X,  # width
            #     "CarPC.EM_Thread.DynamicObjectsFront.objects[%].planeSizeWorld.x",
            # ),
            # (
            #     self.Columns.FRONT_OBJECTS_PLANESIZEWORLD_Y,  # height
            #     "CarPC.EM_Thread.DynamicObjectsFront.objects[%].planeSizeWorld.y",
            # ),
            # (
            #     self.Columns.FRONT_OBJECTS_CUBOIDSIZEWORLD_X,  # width
            #     "CarPC.EM_Thread.DynamicObjectsFront.objects[%].cuboidSizeWorld.x",
            # ),
            # (
            #     self.Columns.FRONT_OBJECTS_CUBOIDSIZEWORLD_Y,  # height
            #     "CarPC.EM_Thread.DynamicObjectsFront.objects[%].cuboidSizeWorld.y",
            # ),
            # (
            #     self.Columns.FRONT_OBJECTS_CUBOIDSIZEWORLD_Z,  # length
            #     "CarPC.EM_Thread.DynamicObjectsFront.objects[%].cuboidSizeWorld.z",
            # ),
            (
                self.Columns.FRONT_OBJECTS_CUBOIDYAWWORLD,
                [
                    "CarPC.EM_Thread.DynamicObjectsFront.objects[%].cuboidYawWorld",
                    "MTA_ADC5.RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectYaw",
                ],
            ),
            (
                self.Columns.REAR_TIMESTAMP,
                [
                    "CarPC.EM_Thread.DynamicObjectsRear.timestamp",
                    "MTA_ADC5.RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.REAR_NUMOBJECTS,
                [
                    "CarPC.EM_Thread.DynamicObjectsRear.numObjects",
                    "MTA_ADC5.RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.numberOfObjects",
                ],
            ),
            (
                self.Columns.REAR_OBJECTS_SIGSTATUS,
                [
                    "CarPC.EM_Thread.DynamicObjectsRear.signalState",
                    "MTA_ADC5.RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
                ],
            ),
            # (
            #     self.Columns.REAR_OBJECTS_ID,
            #     "CarPC.EM_Thread.DynamicObjectsRear.objects[%].id",
            # ),
            (
                self.Columns.REAR_OBJECTS_CLASSTYPE,
                [
                    "CarPC.EM_Thread.DynamicObjectsRear.objects[%].classType",
                    "MTA_ADC5.RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].classType",
                ],
            ),
            (
                self.Columns.REAR_OBJECTS_CONFIDENCE,
                [
                    "CarPC.EM_Thread.DynamicObjectsRear.objects[%].confidence",
                    "MTA_ADC5.RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].confidence",
                ],
            ),
            (
                self.Columns.REAR_OBJECTS_CENTERPOINTWORLD_X,
                [
                    "CarPC.EM_Thread.DynamicObjectsRear.objects[%].centerPointWorld.x",
                    "MTA_ADC5.RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_x",
                ],
            ),
            (
                self.Columns.REAR_OBJECTS_CENTERPOINTWORLD_Y,
                [
                    "CarPC.EM_Thread.DynamicObjectsRear.objects[%].centerPointWorld.y",
                    "MTA_ADC5.RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_y",
                ],
            ),
            (
                self.Columns.REAR_OBJECTS_CENTERPOINTWORLD_Z,
                [
                    "CarPC.EM_Thread.DynamicObjectsRear.objects[%].centerPointWorld.z",
                    "MTA_ADC5.RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_z",
                ],
            ),
            (
                self.Columns.REAR_OBJECTS_WIDTH,
                [
                    "MTA_ADC5.RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.width",
                ],
            ),
            (
                self.Columns.REAR_OBJECTS_LENGTH,
                [
                    "MTA_ADC5.RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.length",
                ],
            ),
            (
                self.Columns.REAR_OBJECTS_HEIGHT,
                [
                    "MTA_ADC5.RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.height",
                ],
            ),
            # (
            #     self.Columns.REAR_OBJECTS_PLANESIZEWORLD_X,
            #     "CarPC.EM_Thread.DynamicObjectsRear.objects[%].planeSizeWorld.x",
            # ),
            # (
            #     self.Columns.REAR_OBJECTS_PLANESIZEWORLD_Y,
            #     "CarPC.EM_Thread.DynamicObjectsRear.objects[%].planeSizeWorld.y",
            # ),
            # (
            #     self.Columns.REAR_OBJECTS_CUBOIDSIZEWORLD_X,
            #     "CarPC.EM_Thread.DynamicObjectsRear.objects[%].cuboidSizeWorld.x",
            # ),
            # (
            #     self.Columns.REAR_OBJECTS_CUBOIDSIZEWORLD_Y,
            #     "CarPC.EM_Thread.DynamicObjectsRear.objects[%].cuboidSizeWorld.y",
            # ),
            # (
            #     self.Columns.REAR_OBJECTS_CUBOIDSIZEWORLD_Z,
            #     "CarPC.EM_Thread.DynamicObjectsRear.objects[%].cuboidSizeWorld.z",
            # ),
            (
                self.Columns.REAR_OBJECTS_CUBOIDYAWWORLD,
                [
                    "CarPC.EM_Thread.DynamicObjectsRear.objects[%].cuboidYawWorld",
                    "MTA_ADC5.RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectYaw",
                ],
            ),
            (
                self.Columns.LEFT_TIMESTAMP,
                [
                    "CarPC.EM_Thread.DynamicObjectsLeft.timestamp",
                    "MTA_ADC5.RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.LEFT_NUMOBJECTS,
                [
                    "CarPC.EM_Thread.DynamicObjectsLeft.numObjects",
                    "MTA_ADC5.RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.numberOfObjects",
                ],
            ),
            (
                self.Columns.LEFT_OBJECTS_SIGSTATUS,
                [
                    "CarPC.EM_Thread.DynamicObjectsLeft.signalState",
                    "MTA_ADC5.RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.signalState",
                ],
            ),
            # (
            #     self.Columns.LEFT_OBJECTS_ID,
            #     "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].id",
            # ),
            (
                self.Columns.LEFT_OBJECTS_CLASSTYPE,
                [
                    "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].classType",
                    "MTA_ADC5.RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].classType",
                ],
            ),
            (
                self.Columns.LEFT_OBJECTS_CONFIDENCE,
                [
                    "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].confidence",
                    "MTA_ADC5.RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].confidence",
                ],
            ),
            (
                self.Columns.LEFT_OBJECTS_CENTERPOINTWORLD_X,
                [
                    "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].centerPointWorld.x",
                    "MTA_ADC5.RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_x",
                ],
            ),
            (
                self.Columns.LEFT_OBJECTS_CENTERPOINTWORLD_Y,
                [
                    "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].centerPointWorld.y",
                    "MTA_ADC5.RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_y",
                ],
            ),
            (
                self.Columns.LEFT_OBJECTS_CENTERPOINTWORLD_Z,
                [
                    "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].centerPointWorld.z",
                    "MTA_ADC5.RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_z",
                ],
            ),
            (
                self.Columns.LEFT_OBJECTS_WIDTH,
                [
                    "MTA_ADC5.RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.width",
                ],
            ),
            (
                self.Columns.LEFT_OBJECTS_LENGTH,
                [
                    "MTA_ADC5.RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.length",
                ],
            ),
            (
                self.Columns.LEFT_OBJECTS_HEIGHT,
                [
                    "MTA_ADC5.RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.height",
                ],
            ),
            # (
            #     self.Columns.LEFT_OBJECTS_PLANESIZEWORLD_X,
            #     "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].planeSizeWorld.x",
            # ),
            # (
            #     self.Columns.LEFT_OBJECTS_PLANESIZEWORLD_Y,
            #     "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].planeSizeWorld.y",
            # ),
            # (
            #     self.Columns.LEFT_OBJECTS_CUBOIDSIZEWORLD_X,
            #     "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].cuboidSizeWorld.x",
            # ),
            # (
            #     self.Columns.LEFT_OBJECTS_CUBOIDSIZEWORLD_Y,
            #     "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].cuboidSizeWorld.y",
            # ),
            # (
            #     self.Columns.LEFT_OBJECTS_CUBOIDSIZEWORLD_Z,
            #     "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].cuboidSizeWorld.z",
            # ),
            (
                self.Columns.LEFT_OBJECTS_CUBOIDYAWWORLD,
                [
                    "CarPC.EM_Thread.DynamicObjectsLeft.objects[%].objectYaw",
                    "MTA_ADC5.RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectYaw",
                ],
            ),
            (
                self.Columns.RIGHT_TIMESTAMP,
                [
                    "CarPC.EM_Thread.DynamicObjectsRight.timestamp",
                    "MTA_ADC5.RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.RIGHT_NUMOBJECTS,
                [
                    "CarPC.EM_Thread.DynamicObjectsRight.numObjects",
                    "MTA_ADC5.RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.numberOfObjects",
                ],
            ),
            (
                self.Columns.RIGHT_OBJECTS_SIGSTATUS,
                [
                    "CarPC.EM_Thread.DynamicObjectsRight.signalState",
                    "MTA_ADC5.RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.signalState",
                ],
            ),
            # (
            #     self.Columns.RIGHT_OBJECTS_ID,
            #     "CarPC.EM_Thread.DynamicObjectsRight.objects[%].id",
            # ),
            (
                self.Columns.RIGHT_OBJECTS_CLASSTYPE,
                [
                    "CarPC.EM_Thread.DynamicObjectsRight.objects[%].classType",
                    "MTA_ADC5.RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].classType",
                ],
            ),
            (
                self.Columns.RIGHT_OBJECTS_CONFIDENCE,
                [
                    "CarPC.EM_Thread.DynamicObjectsRight.objects[%].confidence",
                    "MTA_ADC5.RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].confidence",
                ],
            ),
            (
                self.Columns.RIGHT_OBJECTS_CENTERPOINTWORLD_X,
                [
                    "CarPC.EM_Thread.DynamicObjectsRight.objects[%].centerPointWorld.x",
                    "MTA_ADC5.RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_x",
                ],
            ),
            (
                self.Columns.RIGHT_OBJECTS_CENTERPOINTWORLD_Y,
                [
                    "CarPC.EM_Thread.DynamicObjectsRight.objects[%].centerPointWorld.y",
                    "MTA_ADC5.RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_y",
                ],
            ),
            (
                self.Columns.RIGHT_OBJECTS_CENTERPOINTWORLD_Z,
                [
                    "CarPC.EM_Thread.DynamicObjectsRight.objects[%].centerPointWorld.z",
                    "MTA_ADC5.RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_z",
                ],
            ),
            (
                self.Columns.RIGHT_OBJECTS_WIDTH,
                [
                    "MTA_ADC5.RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.width",
                ],
            ),
            (
                self.Columns.RIGHT_OBJECTS_LENGTH,
                [
                    "MTA_ADC5.RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.length",
                ],
            ),
            (
                self.Columns.RIGHT_OBJECTS_HEIGHT,
                [
                    "MTA_ADC5.RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.height",
                ],
            ),
            # (
            #     self.Columns.RIGHT_OBJECTS_PLANESIZEWORLD_X,
            #     "CarPC.EM_Thread.DynamicObjectsRight.objects[%].planeSizeWorld.x",
            # ),
            # (
            #     self.Columns.RIGHT_OBJECTS_PLANESIZEWORLD_Y,
            #     "CarPC.EM_Thread.DynamicObjectsRight.objects[%].planeSizeWorld.y",
            # ),
            # (
            #     self.Columns.RIGHT_OBJECTS_CUBOIDSIZEWORLD_X,
            #     "CarPC.EM_Thread.DynamicObjectsRight.objects[%].cuboidSizeWorld.x",
            # ),
            # (
            #     self.Columns.RIGHT_OBJECTS_CUBOIDSIZEWORLD_Y,
            #     "CarPC.EM_Thread.DynamicObjectsRight.objects[%].cuboidSizeWorld.y",
            # ),
            # (
            #     self.Columns.RIGHT_OBJECTS_CUBOIDSIZEWORLD_Z,
            #     "CarPC.EM_Thread.DynamicObjectsRight.objects[%].cuboidSizeWorld.z",
            # ),
            (
                self.Columns.RIGHT_OBJECTS_CUBOIDYAWWORLD,
                [
                    "CarPC.EM_Thread.DynamicObjectsRight.objects[%].objectYaw",
                    "MTA_ADC5.RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectYaw",
                ],
            ),
            (
                self.Columns.VEDODO_TIMESTAMP,
                [
                    "cem_outpus_sub.ego_motion_at_cem_time.vehicle_pose_est_at_cem_time.timestamp_us",
                    "CarPC.EM_Thread.OdoEstimationPortAtCem.timestamp_us",
                    "egoMotionAtCemOutput.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.sSigHeader.uiTimeStamp",
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
                self.Columns.VEDODO_GT_TIMESTAMP,
                [
                    "egoMotionAtCemOutput.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.VEDODO_GT_SIGSTATUS,
                [
                    "egoMotionAtCemOutput.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.X_GT,
                [
                    "egoMotionAtCemOutput.odoEstimationAtCemTime.xPosition_m",
                ],
            ),
            (
                self.Columns.Y_GT,
                [
                    "egoMotionAtCemOutput.odoEstimationAtCemTime.yPosition_m",
                ],
            ),
            (
                self.Columns.YAW_GT,
                [
                    "egoMotionAtCemOutput.odoEstimationAtCemTime.yawAngle_rad",
                ],
            ),
            (
                self.Columns.OBJECTS_ID,
                [
                    ".objects._%_.id",
                    ".objects[%].id",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].id",
                ],
            ),
            (
                self.Columns.OBJECTS_NUM,
                [
                    "CarPC.EM_Thread.CemInDynamicEnvironment.numOfAliveObjects",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.numberOfObjects",
                ],
            ),
            (
                self.Columns.OBJECTS_OBJECTCLASS,
                [
                    ".objects._%_.objectClass",
                    ".objects[%].objectClass",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].objectClass",
                ],
            ),
            (
                self.Columns.OBJECTS_CLASSCERTAINTY,
                [
                    ".objects._%_.classCertainty",
                    ".objects[%].classCertainty",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].classCertainty",
                ],
            ),
            (
                self.Columns.OBJECTS_DYNAMICPROPERTY,
                [
                    ".objects._%_.dynamicProperty",
                    ".objects[%].dynamicProperty",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].dynamicProperty",
                ],
            ),
            (
                self.Columns.OBJECTS_DYNPROPCERTAINTY,
                [
                    ".objects._%_.dynPropCertainty",
                    ".objects[%].dynPropCertainty",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].dynamicPropertyCertainty",
                ],
            ),
            (
                self.Columns.OBJECTS_EXISTENCEPROB,
                [
                    ".objects._%_.existenceProb",
                    ".objects[%].existenceProb",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].existenceProbability",
                ],
            ),
            (
                self.Columns.OBJECTS_ORIENTATION,
                [
                    ".objects._%_.orientation",
                    ".objects[%].orientation",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].orientation",
                ],
            ),
            (
                self.Columns.OBJECTS_ORIENTATIONSTANDARDDEVIATION,
                [
                    ".objects._%_.orientationStandardDeviation",
                    ".objects[%].orientationStandardDeviation",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].orientationStandardDeviation",
                ],
            ),
            (
                self.Columns.OBJECTS_VELOCITY_X,
                [
                    ".objects._%_.velocity.x",
                    ".objects[%].velocity.f_Xr",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].velocity.x",
                ],
            ),
            (
                self.Columns.OBJECTS_VELOCITY_Y,
                [
                    ".objects._%_.velocity.y",
                    ".objects[%].velocity.f_Ya",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].velocity.y",
                ],
            ),
            (
                self.Columns.OBJECTS_VELOCITYSTANDARDDEVIATION_X,
                [
                    ".objects._%_.velocityStandardDeviation.x",
                    ".objects[%].velocityStandardDeviation.f_Xr",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].velocityStandardDeviation.x",
                ],
            ),
            (
                self.Columns.OBJECTS_VELOCITYSTANDARDDEVIATION_Y,
                [
                    ".objects._%_.velocityStandardDeviation.y",
                    ".objects[%].velocityStandardDeviation.f_Ya",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].velocityStandardDeviation.y",
                ],
            ),
            (
                self.Columns.OBJECTS_YAWRATE,
                [
                    ".objects._%_.yawRate",
                    ".objects[%].yawRate",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].yawRate",
                ],
            ),
            (
                self.Columns.OBJECTS_YAWRATESTANDARDDEVIATION,
                [
                    ".objects._%_.yawRateStandardDeviation",
                    ".objects[%].yawRateStandardDeviation",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].yawRateStandardDeviation",
                ],
            ),
            (
                self.Columns.OBJECTS_CENTER_X,
                [
                    ".objects._%_.shape.referencePoint.x",
                    ".objects[%].shape.referencePoint.f_Xr",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].referencePoint.x",
                ],
            ),
            (
                self.Columns.OBJECTS_CENTER_Y,
                [
                    ".objects._%_.shape.referencePoint.y",
                    ".objects[%].shape.referencePoint.f_Ya",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].referencePoint.y",
                ],
            ),
            (
                self.Columns.OBJECTS_LIFETIME,
                [
                    ".objects._%_.lifetime",
                    ".objects[%].lifetime",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].lifetime",
                ],
            ),
            (
                self.Columns.OBJECTS_CONTAINEDINLASTSENSORUPDATE,
                [
                    ".objects._%_.containedInLastSensorUpdate",
                    ".objects[%].containedInLastSensorUpdate",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].containedInLastSensorUpdate",
                ],
            ),
            (
                self.Columns.OBJECTS_STATE,
                [
                    ".objects._%_.state",
                    ".objects[%].state",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].state",
                ],
            ),
            (
                self.Columns.OBJECTS_ACCELERATION_X,
                [
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].acceleration.x",
                ],
            ),
            (
                self.Columns.OBJECTS_ACCELERATION_Y,
                [
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].acceleration.y",
                ],
            ),
            (
                self.Columns.OBJECTS_ACCELERATIONSTANDARDDEVIATION_X,
                [
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].accelerationStandardDeviation.x",
                ],
            ),
            (
                self.Columns.OBJECTS_ACCELERATIONSTANDARDDEVIATION_Y,
                [
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].accelerationStandardDeviation.y",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_0__POSITION_X,
                [
                    ".objects._%_.shape.points._0_.position.x",
                    ".objects[%].shape.points[0].position.f_Xr",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.points[0].position.x",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_1__POSITION_X,
                [
                    ".objects._%_.shape.points._1_.position.x",
                    ".objects[%].shape.points[1].position.f_Xr",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.points[1].position.x",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_2__POSITION_X,
                [
                    ".objects._%_.shape.points._2_.position.x",
                    ".objects[%].shape.points[2].position.f_Xr",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.points[2].position.x",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_3__POSITION_X,
                [
                    ".objects._%_.shape.points._3_.position.x",
                    ".objects[%].shape.points[3].position.f_Xr",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.points[3].position.x",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_0__POSITION_Y,
                [
                    ".objects._%_.shape.points._0_.position.y",
                    ".objects[%].shape.points[0].position.f_Ya",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.points[0].position.y",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_1__POSITION_Y,
                [
                    ".objects._%_.shape.points._1_.position.y",
                    ".objects[%].shape.points[1].position.f_Ya",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.points[1].position.y",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_2__POSITION_Y,
                [
                    ".objects._%_.shape.points._2_.position.y",
                    ".objects[%].shape.points[2].position.f_Ya",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.points[2].position.y",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_3__POSITION_Y,
                [
                    ".objects._%_.shape.points._3_.position.y",
                    ".objects[%].shape.points[3].position.f_Ya",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.points[3].position.y",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_0__VARIANCEX,
                [
                    ".objects._%_.shape.points._0_.varianceX",
                    ".objects[%].shape.points[0].varianceX",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.points[0].varianceX",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_1__VARIANCEX,
                [
                    ".objects._%_.shape.points._1_.varianceX",
                    ".objects[%].shape.points[1].varianceX",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.points[1].varianceX",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_2__VARIANCEX,
                [
                    ".objects._%_.shape.points._2_.varianceX",
                    ".objects[%].shape.points[2].varianceX",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.points[2].varianceX",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_3__VARIANCEX,
                [
                    ".objects._%_.shape.points._3_.varianceX",
                    ".objects[%].shape.points[3].varianceX",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.points[3].varianceX",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_0__VARIANCEY,
                [
                    ".objects._%_.shape.points._0_.varianceY",
                    ".objects[%].shape.points[0].varianceY",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.points[0].varianceY",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_1__VARIANCEY,
                [
                    ".objects._%_.shape.points._1_.varianceY",
                    ".objects[%].shape.points[1].varianceY",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.points[1].varianceY",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_2__VARIANCEY,
                [
                    ".objects._%_.shape.points._2_.varianceY",
                    ".objects[%].shape.points[2].varianceY",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.points[2].varianceY",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_3__VARIANCEY,
                [
                    ".objects._%_.shape.points._3_.varianceY",
                    ".objects[%].shape.points[3].varianceY",
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.points[3].varianceY",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_0__COVARIANCEXY,
                [
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.points[0].covarianceXY",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_1__COVARIANCEXY,
                [
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.points[1].covarianceXY",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_2__COVARIANCEXY,
                [
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.points[2].covarianceXY",
                ],
            ),
            (
                self.Columns.OBJECTS_SHAPE_POINTS_3__COVARIANCEXY,
                [
                    "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.objects[%].shape.points[3].covarianceXY",
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
                "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.sSigHeader.eSigStatus",
            ),
            (
                self.Columns.TP_OBJECT_LIST_TIMESTAMP,
                "ADC5xx_Device.CEM_EM_DATA.AUPDF_DynamicObjects.sSigHeader.uiTimeStamp",
                "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.sSigHeader.uiTimeStamp",
            ),
            (
                self.Columns.TP_OBJECT_LIST_OUTPUT,
                "ADC5xx_Device.CEM_EM_DATA.AUPDF_DynamicObjects.numberOfObjects",
                "MTA_ADC5.CEM200_AUPDF_DATA.DynamicObjects.numberOfObjects",
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
            (
                self.Columns.MECAL_CAMERAEXTRINSICS_FC_TIMESTAMP,
                [
                    "MTA_ADC5.CFG_DATA.mecal_FcEolCalibrationsExtrinsicsISO.sSigHeader.uiTimeStamp",
                    "SIM VFB.PARAMETER_HANDLER_DATA.FC_EOLCalibrationExtrinsicsISO.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.MECAL_CAMERAEXTRINSICS_FC_ESIGSTATUS,
                [
                    "MTA_ADC5.CFG_DATA.mecal_FcEolCalibrationsExtrinsicsISO.sSigHeader.eSigStatus",
                    "SIM VFB.PARAMETER_HANDLER_DATA.FC_EOLCalibrationExtrinsicsISO.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.MECAL_CAMERAEXTRINSICS_RC_TIMESTAMP,
                [
                    "MTA_ADC5.CFG_DATA.mecal_RcEolCalibrationsExtrinsicsISO.sSigHeader.uiTimeStamp",
                    "SIM VFB.PARAMETER_HANDLER_DATA.RC_EOLCalibrationExtrinsicsISO.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.MECAL_CAMERAEXTRINSICS_RC_ESIGSTATUS,
                [
                    "MTA_ADC5.CFG_DATA.mecal_RcEolCalibrationsExtrinsicsISO.sSigHeader.eSigStatus",
                    "SIM VFB.PARAMETER_HANDLER_DATA.RC_EOLCalibrationExtrinsicsISO.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.MECAL_CAMERAEXTRINSICS_LSC_TIMESTAMP,
                [
                    "MTA_ADC5.CFG_DATA.mecal_LscEolCalibrationsExtrinsicsISO.sSigHeader.uiTimeStamp",
                    "SIM VFB.PARAMETER_HANDLER_DATA.LSC_EOLCalibrationExtrinsicsISO.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.MECAL_CAMERAEXTRINSICS_LSC_ESIGSTATUS,
                [
                    "MTA_ADC5.CFG_DATA.mecal_LscEolCalibrationsExtrinsicsISO.sSigHeader.eSigStatus",
                    "SIM VFB.PARAMETER_HANDLER_DATA.LSC_EOLCalibrationExtrinsicsISO.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.MECAL_CAMERAEXTRINSICS_RSC_TIMESTAMP,
                [
                    "MTA_ADC5.CFG_DATA.mecal_RscEolCalibrationsExtrinsicsISO.sSigHeader.uiTimeStamp",
                    "SIM VFB.PARAMETER_HANDLER_DATA.RSC_EOLCalibrationExtrinsicsISO.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.MECAL_CAMERAEXTRINSICS_RSC_ESIGSTATUS,
                [
                    "MTA_ADC5.CFG_DATA.mecal_RscEolCalibrationsExtrinsicsISO.sSigHeader.eSigStatus",
                    "SIM VFB.PARAMETER_HANDLER_DATA.RSC_EOLCalibrationExtrinsicsISO.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.GRAPPA_FC_DETECTIONRESULTS_TIMESTAMP,
                [
                    "MTA_ADC5.GRAPPA_FC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
                    "SIM VFB.GRAPPA_FC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.GRAPPA_FC_DETECTIONRESULTS_ESIGSTATUS,
                [
                    "MTA_ADC5.GRAPPA_FC_DATA.DetectionResults.sSigHeader.eSigStatus",
                    "SIM VFB.GRAPPA_FC_DATA.DetectionResults.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.GRAPPA_RC_DETECTIONRESULTS_TIMESTAMP,
                [
                    "MTA_ADC5.GRAPPA_RC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
                    "SIM VFB.GRAPPA_RC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.GRAPPA_RC_DETECTIONRESULTS_ESIGSTATUS,
                [
                    "MTA_ADC5.GRAPPA_RC_DATA.DetectionResults.sSigHeader.eSigStatus",
                    "SIM VFB.GRAPPA_RC_DATA.DetectionResults.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.GRAPPA_LSC_DETECTIONRESULTS_TIMESTAMP,
                [
                    "MTA_ADC5.GRAPPA_LSC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
                    "SIM VFB.GRAPPA_LSC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.GRAPPA_LSC_DETECTIONRESULTS_ESIGSTATUS,
                [
                    "MTA_ADC5.GRAPPA_LSC_DATA.DetectionResults.sSigHeader.eSigStatus",
                    "SIM VFB.GRAPPA_LSC_DATA.DetectionResults.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.GRAPPA_RSC_DETECTIONRESULTS_TIMESTAMP,
                [
                    "MTA_ADC5.GRAPPA_RSC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
                    "SIM VFB.GRAPPA_RSC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.GRAPPA_RSC_DETECTIONRESULTS_ESIGSTATUS,
                [
                    "MTA_ADC5.GRAPPA_RSC_DATA.DetectionResults.sSigHeader.eSigStatus",
                    "SIM VFB.GRAPPA_RSC_DATA.DetectionResults.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.GRAPPA_FC_SEMSEG_TIMESTAMP,
                [
                    "MTA_ADC5.GRAPPA_FC_DATA.SemSeg.signalHeader.uiTimeStamp",
                    "MTA_ADC5.GRAPPA_FC_DATA.SemSeg.signalHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.GRAPPA_FC_SEMSEG_ESIGSTATUS,
                [
                    "MTA_ADC5.GRAPPA_FC_DATA.SemSeg.signalHeader.eSigStatus",
                    "SIM VFB.GRAPPA_FC_DATA.SemSeg.signalHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.GRAPPA_RC_SEMSEG_TIMESTAMP,
                [
                    "MTA_ADC5.GRAPPA_RC_DATA.SemSeg.signalHeader.uiTimeStamp",
                    "SIM VFB.GRAPPA_RC_DATA.SemSeg.signalHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.GRAPPA_RC_SEMSEG_ESIGSTATUS,
                [
                    "MTA_ADC5.GRAPPA_RC_DATA.SemSeg.signalHeader.eSigStatus",
                    "SIM VFB.GRAPPA_RC_DATA.SemSeg.signalHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.GRAPPA_LSC_SEMSEG_TIMESTAMP,
                [
                    "MTA_ADC5.GRAPPA_LSC_DATA.SemSeg.signalHeader.uiTimeStamp",
                    "SIM VFB.GRAPPA_LSC_DATA.SemSeg.signalHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.GRAPPA_LSC_SEMSEG_ESIGSTATUS,
                [
                    "MTA_ADC5.GRAPPA_LSC_DATA.SemSeg.signalHeader.eSigStatus",
                    "SIM VFB.GRAPPA_LSC_DATA.SemSeg.signalHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.GRAPPA_RSC_SEMSEG_TIMESTAMP,
                [
                    "MTA_ADC5.GRAPPA_RSC_DATA.SemSeg.signalHeader.uiTimeStamp",
                    "SIM VFB.GRAPPA_RSC_DATA.SemSeg.signalHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.GRAPPA_RSC_SEMSEG_ESIGSTATUS,
                [
                    "MTA_ADC5.GRAPPA_RSC_DATA.SemSeg.signalHeader.eSigStatus",
                    "SIM VFB.GRAPPA_RSC_DATA.SemSeg.signalHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PARAMETERHANDELER_FC_TIMESTAMP,
                [
                    "MTA_ADC5.PARAMETER_HANDLER_DATA.FC_pmsdParamsPort.sSigHeader.uiTimeStamp",
                    "SIM VFB.PARAMETER_HANDLER_DATA.FC_pmsdParamsPort.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PARAMETERHANDELER_FC_ESIGSTATUS,
                [
                    "MTA_ADC5.PARAMETER_HANDLER_DATA.FC_pmsdParamsPort.sSigHeader.eSigStatus",
                    "SIM VFB.PARAMETER_HANDLER_DATA.FC_pmsdParamsPort.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PARAMETERHANDELER_RC_TIMESTAMP,
                [
                    "MTA_ADC5.PARAMETER_HANDLER_DATA.RC_pmsdParamsPort.sSigHeader.uiTimeStamp",
                    "SIM VFB.PARAMETER_HANDLER_DATA.RC_pmsdParamsPort.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PARAMETERHANDELER_RC_ESIGSTATUS,
                [
                    "MTA_ADC5.PARAMETER_HANDLER_DATA.RC_pmsdParamsPort.sSigHeader.eSigStatus",
                    "SIM VFB.PARAMETER_HANDLER_DATA.RC_pmsdParamsPort.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PARAMETERHANDELER_LSC_TIMESTAMP,
                [
                    "MTA_ADC5.PARAMETER_HANDLER_DATA.LSC_pmsdParamsPort.sSigHeader.uiTimeStamp",
                    "SIM VFB.PARAMETER_HANDLER_DATA.LSC_pmsdParamsPort.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PARAMETERHANDELER_LSC_ESIGSTATUS,
                [
                    "MTA_ADC5.PARAMETER_HANDLER_DATA.LSC_pmsdParamsPort.sSigHeader.eSigStatus",
                    "SIM VFB.PARAMETER_HANDLER_DATA.LSC_pmsdParamsPort.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.PARAMETERHANDELER_RSC_TIMESTAMP,
                [
                    "MTA_ADC5.PARAMETER_HANDLER_DATA.RSC_pmsdParamsPort.sSigHeader.uiTimeStamp",
                    "SIM VFB.PARAMETER_HANDLER_DATA.RSC_pmsdParamsPort.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PARAMETERHANDELER_RSC_ESIGSTATUS,
                [
                    "MTA_ADC5.PARAMETER_HANDLER_DATA.RSC_pmsdParamsPort.sSigHeader.eSigStatus",
                    "SIM VFB.PARAMETER_HANDLER_DATA.RSC_pmsdParamsPort.sSigHeader.eSigStatus",
                ],
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
        NUMVALIDPARKINGBOXES = "numValidParkingBoxes_nu"
        SLOTCOORDINATES_FRONTLEFT_X_0 = "slotCoordinates_FrontLeft_x_0"
        SLOTCOORDINATES_FRONTLEFT_Y_0 = "slotCoordinates_FrontLeft_y_0"
        SLOTCOORDINATES_REARLEFT_X_0 = "slotCoordinates_RearLeft_x_0"
        SLOTCOORDINATES_REARLEFT_Y_0 = "slotCoordinates_RearLeft_y_0"
        SLOTCOORDINATES_FRONTRIGHT_X_0 = "slotCoordinates_FrontRight_x_0"
        SLOTCOORDINATES_FRONTRIGHT_Y_0 = "slotCoordinates_FrontRight_y_0"
        SLOTCOORDINATES_REARRIGHT_X_0 = "slotCoordinates_RearRight_x_0"
        SLOTCOORDINATES_REARRIGHT_Y_0 = "slotCoordinates_RearRight_y_0"
        SLOTCOORDINATES_FRONTLEFT_X_1 = "slotCoordinates_FrontLeft_x_1"
        SLOTCOORDINATES_FRONTLEFT_Y_1 = "slotCoordinates_FrontLeft_y_1"
        SLOTCOORDINATES_REARLEFT_X_1 = "slotCoordinates_RearLeft_x_1"
        SLOTCOORDINATES_REARLEFT_Y_1 = "slotCoordinates_RearLeft_y_1"
        SLOTCOORDINATES_FRONTRIGHT_X_1 = "slotCoordinates_FrontRight_x_1"
        SLOTCOORDINATES_FRONTRIGHT_Y_1 = "slotCoordinates_FrontRight_y_1"
        SLOTCOORDINATES_REARRIGHT_X_1 = "slotCoordinates_RearRight_x_1"
        SLOTCOORDINATES_REARRIGHT_Y_1 = "slotCoordinates_RearRight_y_1"
        SLOTCOORDINATES_FRONTLEFT_X_2 = "slotCoordinates_FrontLeft_x_2"
        SLOTCOORDINATES_FRONTLEFT_Y_2 = "slotCoordinates_FrontLeft_y_2"
        SLOTCOORDINATES_REARLEFT_X_2 = "slotCoordinates_RearLeft_x_2"
        SLOTCOORDINATES_REARLEFT_Y_2 = "slotCoordinates_RearLeft_y_2"
        SLOTCOORDINATES_FRONTRIGHT_X_2 = "slotCoordinates_FrontRight_x_2"
        SLOTCOORDINATES_FRONTRIGHT_Y_2 = "slotCoordinates_FrontRight_y_2"
        SLOTCOORDINATES_REARRIGHT_X_2 = "slotCoordinates_RearRight_x_2"
        SLOTCOORDINATES_REARRIGHT_Y_2 = "slotCoordinates_RearRight_y_2"
        SLOTCOORDINATES_FRONTLEFT_X_3 = "slotCoordinates_FrontLeft_x_3"
        SLOTCOORDINATES_FRONTLEFT_Y_3 = "slotCoordinates_FrontLeft_y_3"
        SLOTCOORDINATES_REARLEFT_X_3 = "slotCoordinates_RearLeft_x_3"
        SLOTCOORDINATES_REARLEFT_Y_3 = "slotCoordinates_RearLeft_y_3"
        SLOTCOORDINATES_FRONTRIGHT_X_3 = "slotCoordinates_FrontRight_x_3"
        SLOTCOORDINATES_FRONTRIGHT_Y_3 = "slotCoordinates_FrontRight_y_3"
        SLOTCOORDINATES_REARRIGHT_X_3 = "slotCoordinates_RearRight_x_3"
        SLOTCOORDINATES_REARRIGHT_Y_3 = "slotCoordinates_RearRight_y_3"
        SLOTCOORDINATES_FRONTLEFT_X_4 = "slotCoordinates_FrontLeft_x_4"
        SLOTCOORDINATES_FRONTLEFT_Y_4 = "slotCoordinates_FrontLeft_y_4"
        SLOTCOORDINATES_REARLEFT_X_4 = "slotCoordinates_RearLeft_x_4"
        SLOTCOORDINATES_REARLEFT_Y_4 = "slotCoordinates_RearLeft_y_4"
        SLOTCOORDINATES_FRONTRIGHT_X_4 = "slotCoordinates_FrontRight_x_4"
        SLOTCOORDINATES_FRONTRIGHT_Y_4 = "slotCoordinates_FrontRight_y_4"
        SLOTCOORDINATES_REARRIGHT_X_4 = "slotCoordinates_RearRight_x_4"
        SLOTCOORDINATES_REARRIGHT_Y_4 = "slotCoordinates_RearRight_y_4"
        SLOTCOORDINATES_FRONTLEFT_X_5 = "slotCoordinates_FrontLeft_x_5"
        SLOTCOORDINATES_FRONTLEFT_Y_5 = "slotCoordinates_FrontLeft_y_5"
        SLOTCOORDINATES_REARLEFT_X_5 = "slotCoordinates_RearLeft_x_5"
        SLOTCOORDINATES_REARLEFT_Y_5 = "slotCoordinates_RearLeft_y_5"
        SLOTCOORDINATES_FRONTRIGHT_X_5 = "slotCoordinates_FrontRight_x_5"
        SLOTCOORDINATES_FRONTRIGHT_Y_5 = "slotCoordinates_FrontRight_y_5"
        SLOTCOORDINATES_REARRIGHT_X_5 = "slotCoordinates_RearRight_x_5"
        SLOTCOORDINATES_REARRIGHT_Y_5 = "slotCoordinates_RearRight_y_5"
        SLOTCOORDINATES_FRONTLEFT_X_6 = "slotCoordinates_FrontLeft_x_6"
        SLOTCOORDINATES_FRONTLEFT_Y_6 = "slotCoordinates_FrontLeft_y_6"
        SLOTCOORDINATES_REARLEFT_X_6 = "slotCoordinates_RearLeft_x_6"
        SLOTCOORDINATES_REARLEFT_Y_6 = "slotCoordinates_RearLeft_y_6"
        SLOTCOORDINATES_FRONTRIGHT_X_6 = "slotCoordinates_FrontRight_x_6"
        SLOTCOORDINATES_FRONTRIGHT_Y_6 = "slotCoordinates_FrontRight_y_6"
        SLOTCOORDINATES_REARRIGHT_X_6 = "slotCoordinates_RearRight_x_6"
        SLOTCOORDINATES_REARRIGHT_Y_6 = "slotCoordinates_RearRight_y_6"
        SLOTCOORDINATES_FRONTLEFT_X_7 = "slotCoordinates_FrontLeft_x_7"
        SLOTCOORDINATES_FRONTLEFT_Y_7 = "slotCoordinates_FrontLeft_y_7"
        SLOTCOORDINATES_REARLEFT_X_7 = "slotCoordinates_RearLeft_x_7"
        SLOTCOORDINATES_REARLEFT_Y_7 = "slotCoordinates_RearLeft_y_7"
        SLOTCOORDINATES_FRONTRIGHT_X_7 = "slotCoordinates_FrontRight_x_7"
        SLOTCOORDINATES_FRONTRIGHT_Y_7 = "slotCoordinates_FrontRight_y_7"
        SLOTCOORDINATES_REARRIGHT_X_7 = "slotCoordinates_RearRight_x_7"
        SLOTCOORDINATES_REARRIGHT_Y_7 = "slotCoordinates_RearRight_y_7"
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
        TARGETPOSEREACHABLE0 = "targetPoseReachableStatus0"
        TARGETPOSEREACHABLE1 = "targetPoseReachableStatus1"
        TARGETPOSEREACHABLE2 = "targetPoseReachableStatus2"
        TARGETPOSEREACHABLE3 = "targetPoseReachableStatus3"
        TARGETPOSEREACHABLE4 = "targetPoseReachableStatus4"
        TARGETPOSEREACHABLE5 = "targetPoseReachableStatus5"
        TARGETPOSEREACHABLE6 = "targetPoseReachableStatus6"
        TARGETPOSEREACHABLE7 = "targetPoseReachableStatus7"
        TARGETPOSESIDE0 = "targetPoseSide0"
        TARGETPOSESIDE1 = "targetPoseSide1"
        TARGETPOSESIDE2 = "targetPoseSide2"
        TARGETPOSESIDE3 = "targetPoseSide3"
        TARGETPOSESIDE4 = "targetPoseSide4"
        TARGETPOSESIDE5 = "targetPoseSide5"
        TARGETPOSESIDE6 = "targetPoseSide6"
        TARGETPOSESIDE7 = "targetPoseSide7"
        TARGETPOSEPOSX0 = "targetPosePositionX0"
        TARGETPOSEPOSX1 = "targetPosePositionX1"
        TARGETPOSEPOSX2 = "targetPosePositionX2"
        TARGETPOSEPOSX3 = "targetPosePositionX3"
        TARGETPOSEPOSX4 = "targetPosePositionX4"
        TARGETPOSEPOSX5 = "targetPosePositionX5"
        TARGETPOSEPOSX6 = "targetPosePositionX6"
        TARGETPOSEPOSX7 = "targetPosePositionX7"
        TARGETPOSEPOSY0 = "targetPosePositionY0"
        TARGETPOSEPOSY1 = "targetPosePositionY1"
        TARGETPOSEPOSY2 = "targetPosePositionY2"
        TARGETPOSEPOSY3 = "targetPosePositionY3"
        TARGETPOSEPOSY4 = "targetPosePositionY4"
        TARGETPOSEPOSY5 = "targetPosePositionY5"
        TARGETPOSEPOSY6 = "targetPosePositionY6"
        TARGETPOSEPOSY7 = "targetPosePositionY7"
        TARGETPOSEYAWRAD0 = "targetPoseYawRad0"
        TARGETPOSEYAWRAD1 = "targetPoseYawRad1"
        TARGETPOSEYAWRAD2 = "targetPoseYawRad2"
        TARGETPOSEYAWRAD3 = "targetPoseYawRad3"
        TARGETPOSEYAWRAD4 = "targetPoseYawRad4"
        TARGETPOSEYAWRAD5 = "targetPoseYawRad5"
        TARGETPOSEYAWRAD6 = "targetPoseYawRad6"
        TARGETPOSEYAWRAD7 = "targetPoseYawRad7"
        EGOPOSITIONAPX = "egoVehiclePoseForApX"
        EGOPOSITIONAPY = "egoVehiclePoseForApY"
        EGOPOSITIONAPYAW = "egoVehiclePoseForApYaw"
        TRAJCURVATURE0 = "trajCurvature0"
        TRAJCURVATURE1 = "trajCurvature1"
        TRAJCURVATURE2 = "trajCurvature2"
        TRAJCURVATURE3 = "trajCurvature3"
        TRAJCURVATURE4 = "trajCurvature4"
        TRAJCURVATURE5 = "trajCurvature5"
        TRAJCURVATURE6 = "trajCurvature6"
        TRAJCURVATURE7 = "trajCurvature7"
        TRAJCURVATURE8 = "trajCurvature8"
        TRAJCURVATURE9 = "trajCurvature9"
        TRAJCURVATURE10 = "trajCurvature10"
        TRAJCURVATURE11 = "trajCurvature11"
        TRAJCURVATURE12 = "trajCurvature12"
        TRAJCURVATURE13 = "trajCurvature13"
        TRAJCURVATURE14 = "trajCurvature14"
        TRAJCURVATURE15 = "trajCurvature15"
        TRAJCURVATURE16 = "trajCurvature16"
        TRAJCURVATURE17 = "trajCurvature17"
        TRAJCURVATURE18 = "trajCurvature18"
        TRAJCURVATURE19 = "trajCurvature19"
        TRAJVELOCITYLIMIT0 = "trajVelocityLimit0"
        TRAJVELOCITYLIMIT1 = "trajVelocityLimit1"
        TRAJVELOCITYLIMIT2 = "trajVelocityLimit2"
        TRAJVELOCITYLIMIT3 = "trajVelocityLimit3"
        TRAJVELOCITYLIMIT4 = "trajVelocityLimit4"
        TRAJVELOCITYLIMIT5 = "trajVelocityLimit5"
        TRAJVELOCITYLIMIT6 = "trajVelocityLimit6"
        TRAJVELOCITYLIMIT7 = "trajVelocityLimit7"
        TRAJVELOCITYLIMIT8 = "trajVelocityLimit8"
        TRAJVELOCITYLIMIT9 = "trajVelocityLimit9"
        TRAJVELOCITYLIMIT10 = "trajVelocityLimit10"
        TRAJVELOCITYLIMIT11 = "trajVelocityLimit11"
        TRAJVELOCITYLIMIT12 = "trajVelocityLimit12"
        TRAJVELOCITYLIMIT13 = "trajVelocityLimit13"
        TRAJVELOCITYLIMIT14 = "trajVelocityLimit14"
        TRAJVELOCITYLIMIT15 = "trajVelocityLimit15"
        TRAJVELOCITYLIMIT16 = "trajVelocityLimit16"
        TRAJVELOCITYLIMIT17 = "trajVelocityLimit17"
        TRAJVELOCITYLIMIT18 = "trajVelocityLimit18"
        TRAJVELOCITYLIMIT19 = "trajVelocityLimit19"
        # TRAJVELOCITYLIMIT = "trajVelocityLimit"

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
            self.Columns.NUMVALIDPARKINGBOXES: ".parkingBoxPort.numValidParkingBoxes_nu",
            self.Columns.SLOTCOORDINATES_FRONTLEFT_X_0: ".parkingBoxPort.parkingBoxes_0.slotCoordinates_FrontLeft_x",
            self.Columns.SLOTCOORDINATES_FRONTLEFT_Y_0: ".parkingBoxPort.parkingBoxes_0.slotCoordinates_FrontLeft_y",
            self.Columns.SLOTCOORDINATES_REARLEFT_X_0: ".parkingBoxPort.parkingBoxes_0.slotCoordinates_RearLeft_x",
            self.Columns.SLOTCOORDINATES_REARLEFT_Y_0: ".parkingBoxPort.parkingBoxes_0.slotCoordinates_RearLeft_y",
            self.Columns.SLOTCOORDINATES_FRONTRIGHT_X_0: ".parkingBoxPort.parkingBoxes_0.slotCoordinates_FrontRight_x",
            self.Columns.SLOTCOORDINATES_FRONTRIGHT_Y_0: ".parkingBoxPort.parkingBoxes_0.slotCoordinates_FrontRight_y",
            self.Columns.SLOTCOORDINATES_REARRIGHT_X_0: ".parkingBoxPort.parkingBoxes_0.slotCoordinates_RearRight_x",
            self.Columns.SLOTCOORDINATES_REARRIGHT_Y_0: ".parkingBoxPort.parkingBoxes_0.slotCoordinates_RearRight_y",
            self.Columns.SLOTCOORDINATES_FRONTLEFT_X_1: ".parkingBoxPort.parkingBoxes_1.slotCoordinates_FrontLeft_x",
            self.Columns.SLOTCOORDINATES_FRONTLEFT_Y_1: ".parkingBoxPort.parkingBoxes_1.slotCoordinates_FrontLeft_y",
            self.Columns.SLOTCOORDINATES_REARLEFT_X_1: ".parkingBoxPort.parkingBoxes_1.slotCoordinates_RearLeft_x",
            self.Columns.SLOTCOORDINATES_REARLEFT_Y_1: ".parkingBoxPort.parkingBoxes_1.slotCoordinates_RearLeft_y",
            self.Columns.SLOTCOORDINATES_FRONTRIGHT_X_1: ".parkingBoxPort.parkingBoxes_1.slotCoordinates_FrontRight_x",
            self.Columns.SLOTCOORDINATES_FRONTRIGHT_Y_1: ".parkingBoxPort.parkingBoxes_1.slotCoordinates_FrontRight_y",
            self.Columns.SLOTCOORDINATES_REARRIGHT_X_1: ".parkingBoxPort.parkingBoxes_1.slotCoordinates_RearRight_x",
            self.Columns.SLOTCOORDINATES_REARRIGHT_Y_1: ".parkingBoxPort.parkingBoxes_1.slotCoordinates_RearRight_y",
            self.Columns.SLOTCOORDINATES_FRONTLEFT_X_2: ".parkingBoxPort.parkingBoxes_2.slotCoordinates_FrontLeft_x",
            self.Columns.SLOTCOORDINATES_FRONTLEFT_Y_2: ".parkingBoxPort.parkingBoxes_2.slotCoordinates_FrontLeft_y",
            self.Columns.SLOTCOORDINATES_REARLEFT_X_2: ".parkingBoxPort.parkingBoxes_2.slotCoordinates_RearLeft_x",
            self.Columns.SLOTCOORDINATES_REARLEFT_Y_2: ".parkingBoxPort.parkingBoxes_2.slotCoordinates_RearLeft_y",
            self.Columns.SLOTCOORDINATES_FRONTRIGHT_X_2: ".parkingBoxPort.parkingBoxes_2.slotCoordinates_FrontRight_x",
            self.Columns.SLOTCOORDINATES_FRONTRIGHT_Y_2: ".parkingBoxPort.parkingBoxes_2.slotCoordinates_FrontRight_y",
            self.Columns.SLOTCOORDINATES_REARRIGHT_X_2: ".parkingBoxPort.parkingBoxes_2.slotCoordinates_RearRight_x",
            self.Columns.SLOTCOORDINATES_REARRIGHT_Y_2: ".parkingBoxPort.parkingBoxes_2.slotCoordinates_RearRight_y",
            self.Columns.SLOTCOORDINATES_FRONTLEFT_X_3: ".parkingBoxPort.parkingBoxes_3.slotCoordinates_FrontLeft_x",
            self.Columns.SLOTCOORDINATES_FRONTLEFT_Y_3: ".parkingBoxPort.parkingBoxes_3.slotCoordinates_FrontLeft_y",
            self.Columns.SLOTCOORDINATES_REARLEFT_X_3: ".parkingBoxPort.parkingBoxes_3.slotCoordinates_RearLeft_x",
            self.Columns.SLOTCOORDINATES_REARLEFT_Y_3: ".parkingBoxPort.parkingBoxes_3.slotCoordinates_RearLeft_y",
            self.Columns.SLOTCOORDINATES_FRONTRIGHT_X_3: ".parkingBoxPort.parkingBoxes_3.slotCoordinates_FrontRight_x",
            self.Columns.SLOTCOORDINATES_FRONTRIGHT_Y_3: ".parkingBoxPort.parkingBoxes_3.slotCoordinates_FrontRight_y",
            self.Columns.SLOTCOORDINATES_REARRIGHT_X_3: ".parkingBoxPort.parkingBoxes_3.slotCoordinates_RearRight_x",
            self.Columns.SLOTCOORDINATES_REARRIGHT_Y_3: ".parkingBoxPort.parkingBoxes_3.slotCoordinates_RearRight_y",
            self.Columns.SLOTCOORDINATES_FRONTLEFT_X_4: ".parkingBoxPort.parkingBoxes_4.slotCoordinates_FrontLeft_x",
            self.Columns.SLOTCOORDINATES_FRONTLEFT_Y_4: ".parkingBoxPort.parkingBoxes_4.slotCoordinates_FrontLeft_y",
            self.Columns.SLOTCOORDINATES_REARLEFT_X_4: ".parkingBoxPort.parkingBoxes_4.slotCoordinates_RearLeft_x",
            self.Columns.SLOTCOORDINATES_REARLEFT_Y_4: ".parkingBoxPort.parkingBoxes_4.slotCoordinates_RearLeft_y",
            self.Columns.SLOTCOORDINATES_FRONTRIGHT_X_4: ".parkingBoxPort.parkingBoxes_4.slotCoordinates_FrontRight_x",
            self.Columns.SLOTCOORDINATES_FRONTRIGHT_Y_4: ".parkingBoxPort.parkingBoxes_4.slotCoordinates_FrontRight_y",
            self.Columns.SLOTCOORDINATES_REARRIGHT_X_4: ".parkingBoxPort.parkingBoxes_4.slotCoordinates_RearRight_x",
            self.Columns.SLOTCOORDINATES_REARRIGHT_Y_4: ".parkingBoxPort.parkingBoxes_4.slotCoordinates_RearRight_y",
            self.Columns.SLOTCOORDINATES_FRONTLEFT_X_5: ".parkingBoxPort.parkingBoxes_5.slotCoordinates_FrontLeft_x",
            self.Columns.SLOTCOORDINATES_FRONTLEFT_Y_5: ".parkingBoxPort.parkingBoxes_5.slotCoordinates_FrontLeft_y",
            self.Columns.SLOTCOORDINATES_REARLEFT_X_5: ".parkingBoxPort.parkingBoxes_5.slotCoordinates_RearLeft_x",
            self.Columns.SLOTCOORDINATES_REARLEFT_Y_5: ".parkingBoxPort.parkingBoxes_5.slotCoordinates_RearLeft_y",
            self.Columns.SLOTCOORDINATES_FRONTRIGHT_X_5: ".parkingBoxPort.parkingBoxes_5.slotCoordinates_FrontRight_x",
            self.Columns.SLOTCOORDINATES_FRONTRIGHT_Y_5: ".parkingBoxPort.parkingBoxes_5.slotCoordinates_FrontRight_y",
            self.Columns.SLOTCOORDINATES_REARRIGHT_X_5: ".parkingBoxPort.parkingBoxes_5.slotCoordinates_RearRight_x",
            self.Columns.SLOTCOORDINATES_REARRIGHT_Y_5: ".parkingBoxPort.parkingBoxes_5.slotCoordinates_RearRight_y",
            self.Columns.SLOTCOORDINATES_FRONTLEFT_X_6: ".parkingBoxPort.parkingBoxes_6.slotCoordinates_FrontLeft_x",
            self.Columns.SLOTCOORDINATES_FRONTLEFT_Y_6: ".parkingBoxPort.parkingBoxes_6.slotCoordinates_FrontLeft_y",
            self.Columns.SLOTCOORDINATES_REARLEFT_X_6: ".parkingBoxPort.parkingBoxes_6.slotCoordinates_RearLeft_x",
            self.Columns.SLOTCOORDINATES_REARLEFT_Y_6: ".parkingBoxPort.parkingBoxes_6.slotCoordinates_RearLeft_y",
            self.Columns.SLOTCOORDINATES_FRONTRIGHT_X_6: ".parkingBoxPort.parkingBoxes_6.slotCoordinates_FrontRight_x",
            self.Columns.SLOTCOORDINATES_FRONTRIGHT_Y_6: ".parkingBoxPort.parkingBoxes_6.slotCoordinates_FrontRight_y",
            self.Columns.SLOTCOORDINATES_REARRIGHT_X_6: ".parkingBoxPort.parkingBoxes_6.slotCoordinates_RearRight_x",
            self.Columns.SLOTCOORDINATES_REARRIGHT_Y_6: ".parkingBoxPort.parkingBoxes_6.slotCoordinates_RearRight_y",
            self.Columns.SLOTCOORDINATES_FRONTLEFT_X_7: ".parkingBoxPort.parkingBoxes_7.slotCoordinates_FrontLeft_x",
            self.Columns.SLOTCOORDINATES_FRONTLEFT_Y_7: ".parkingBoxPort.parkingBoxes_7.slotCoordinates_FrontLeft_y",
            self.Columns.SLOTCOORDINATES_REARLEFT_X_7: ".parkingBoxPort.parkingBoxes_7.slotCoordinates_RearLeft_x",
            self.Columns.SLOTCOORDINATES_REARLEFT_Y_7: ".parkingBoxPort.parkingBoxes_7.slotCoordinates_RearLeft_y",
            self.Columns.SLOTCOORDINATES_FRONTRIGHT_X_7: ".parkingBoxPort.parkingBoxes_7.slotCoordinates_FrontRight_x",
            self.Columns.SLOTCOORDINATES_FRONTRIGHT_Y_7: ".parkingBoxPort.parkingBoxes_7.slotCoordinates_FrontRight_y",
            self.Columns.SLOTCOORDINATES_REARRIGHT_X_7: ".parkingBoxPort.parkingBoxes_7.slotCoordinates_RearRight_x",
            self.Columns.SLOTCOORDINATES_REARRIGHT_Y_7: ".parkingBoxPort.parkingBoxes_7.slotCoordinates_RearRight_y",
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
            self.Columns.TARGETPOSESIDE0: ".targetPosesPort.targetPoses_0.targetSide",
            self.Columns.TARGETPOSESIDE1: ".targetPosesPort.targetPoses_1.targetSide",
            self.Columns.TARGETPOSESIDE2: ".targetPosesPort.targetPoses_2.targetSide",
            self.Columns.TARGETPOSESIDE3: ".targetPosesPort.targetPoses_3.targetSide",
            self.Columns.TARGETPOSESIDE4: ".targetPosesPort.targetPoses_4.targetSide",
            self.Columns.TARGETPOSESIDE5: ".targetPosesPort.targetPoses_5.targetSide",
            self.Columns.TARGETPOSESIDE6: ".targetPosesPort.targetPoses_6.targetSide",
            self.Columns.TARGETPOSESIDE7: ".targetPosesPort.targetPoses_7.targetSide",
            self.Columns.TARGETPOSEPOSX0: ".targetPosesPort.targetPoses_0.pose.pos.x",
            self.Columns.TARGETPOSEPOSX1: ".targetPosesPort.targetPoses_1.pose.pos.x",
            self.Columns.TARGETPOSEPOSX2: ".targetPosesPort.targetPoses_2.pose.pos.x",
            self.Columns.TARGETPOSEPOSX3: ".targetPosesPort.targetPoses_3.pose.pos.x",
            self.Columns.TARGETPOSEPOSX4: ".targetPosesPort.targetPoses_4.pose.pos.x",
            self.Columns.TARGETPOSEPOSX5: ".targetPosesPort.targetPoses_5.pose.pos.x",
            self.Columns.TARGETPOSEPOSX6: ".targetPosesPort.targetPoses_6.pose.pos.x",
            self.Columns.TARGETPOSEPOSX7: ".targetPosesPort.targetPoses_7.pose.pos.x",
            self.Columns.TARGETPOSEPOSY0: ".targetPosesPort.targetPoses_0.pose.pos.y",
            self.Columns.TARGETPOSEPOSY1: ".targetPosesPort.targetPoses_1.pose.pos.y",
            self.Columns.TARGETPOSEPOSY2: ".targetPosesPort.targetPoses_2.pose.pos.y",
            self.Columns.TARGETPOSEPOSY3: ".targetPosesPort.targetPoses_3.pose.pos.y",
            self.Columns.TARGETPOSEPOSY4: ".targetPosesPort.targetPoses_4.pose.pos.y",
            self.Columns.TARGETPOSEPOSY5: ".targetPosesPort.targetPoses_5.pose.pos.y",
            self.Columns.TARGETPOSEPOSY6: ".targetPosesPort.targetPoses_6.pose.pos.y",
            self.Columns.TARGETPOSEPOSY7: ".targetPosesPort.targetPoses_7.pose.pos.y",
            self.Columns.TARGETPOSEYAWRAD0: ".targetPosesPort.targetPoses_0.pose.yaw_rad",
            self.Columns.TARGETPOSEYAWRAD1: ".targetPosesPort.targetPoses_1.pose.yaw_rad",
            self.Columns.TARGETPOSEYAWRAD2: ".targetPosesPort.targetPoses_2.pose.yaw_rad",
            self.Columns.TARGETPOSEYAWRAD3: ".targetPosesPort.targetPoses_3.pose.yaw_rad",
            self.Columns.TARGETPOSEYAWRAD4: ".targetPosesPort.targetPoses_4.pose.yaw_rad",
            self.Columns.TARGETPOSEYAWRAD5: ".targetPosesPort.targetPoses_5.pose.yaw_rad",
            self.Columns.TARGETPOSEYAWRAD6: ".targetPosesPort.targetPoses_6.pose.yaw_rad",
            self.Columns.TARGETPOSEYAWRAD7: ".targetPosesPort.targetPoses_7.pose.yaw_rad",
            self.Columns.EGOPOSITIONAPX: ".envModelPort.egoVehiclePoseForAP.pos_x_m",
            self.Columns.EGOPOSITIONAPY: ".envModelPort.egoVehiclePoseForAP.pos_y_m",
            self.Columns.EGOPOSITIONAPYAW: ".envModelPort.egoVehiclePoseForAP.yaw_rad",
            self.Columns.TRAJCURVATURE0: ".plannedTrajPort.plannedTraj_0.crvRARReq_1pm",
            self.Columns.TRAJCURVATURE1: ".plannedTrajPort.plannedTraj_1.crvRARReq_1pm",
            self.Columns.TRAJCURVATURE2: ".plannedTrajPort.plannedTraj_2.crvRARReq_1pm",
            self.Columns.TRAJCURVATURE3: ".plannedTrajPort.plannedTraj_3.crvRARReq_1pm",
            self.Columns.TRAJCURVATURE4: ".plannedTrajPort.plannedTraj_4.crvRARReq_1pm",
            self.Columns.TRAJCURVATURE5: ".plannedTrajPort.plannedTraj_5.crvRARReq_1pm",
            self.Columns.TRAJCURVATURE6: ".plannedTrajPort.plannedTraj_6.crvRARReq_1pm",
            self.Columns.TRAJCURVATURE7: ".plannedTrajPort.plannedTraj_7.crvRARReq_1pm",
            self.Columns.TRAJCURVATURE8: ".plannedTrajPort.plannedTraj_8.crvRARReq_1pm",
            self.Columns.TRAJCURVATURE9: ".plannedTrajPort.plannedTraj_9.crvRARReq_1pm",
            self.Columns.TRAJCURVATURE10: ".plannedTrajPort.plannedTraj_10.crvRARReq_1pm",
            self.Columns.TRAJCURVATURE11: ".plannedTrajPort.plannedTraj_11.crvRARReq_1pm",
            self.Columns.TRAJCURVATURE12: ".plannedTrajPort.plannedTraj_12.crvRARReq_1pm",
            self.Columns.TRAJCURVATURE13: ".plannedTrajPort.plannedTraj_13.crvRARReq_1pm",
            self.Columns.TRAJCURVATURE14: ".plannedTrajPort.plannedTraj_14.crvRARReq_1pm",
            self.Columns.TRAJCURVATURE15: ".plannedTrajPort.plannedTraj_15.crvRARReq_1pm",
            self.Columns.TRAJCURVATURE16: ".plannedTrajPort.plannedTraj_16.crvRARReq_1pm",
            self.Columns.TRAJCURVATURE17: ".plannedTrajPort.plannedTraj_17.crvRARReq_1pm",
            self.Columns.TRAJCURVATURE18: ".plannedTrajPort.plannedTraj_18.crvRARReq_1pm",
            self.Columns.TRAJCURVATURE19: ".plannedTrajPort.plannedTraj_19.crvRARReq_1pm",
            self.Columns.TRAJVELOCITYLIMIT0: ".plannedTrajPort.plannedTraj_0.velocityLimitReq_mps",
            self.Columns.TRAJVELOCITYLIMIT1: ".plannedTrajPort.plannedTraj_1.velocityLimitReq_mps",
            self.Columns.TRAJVELOCITYLIMIT2: ".plannedTrajPort.plannedTraj_2.velocityLimitReq_mps",
            self.Columns.TRAJVELOCITYLIMIT3: ".plannedTrajPort.plannedTraj_3.velocityLimitReq_mps",
            self.Columns.TRAJVELOCITYLIMIT4: ".plannedTrajPort.plannedTraj_4.velocityLimitReq_mps",
            self.Columns.TRAJVELOCITYLIMIT5: ".plannedTrajPort.plannedTraj_5.velocityLimitReq_mps",
            self.Columns.TRAJVELOCITYLIMIT6: ".plannedTrajPort.plannedTraj_6.velocityLimitReq_mps",
            self.Columns.TRAJVELOCITYLIMIT7: ".plannedTrajPort.plannedTraj_7.velocityLimitReq_mps",
            self.Columns.TRAJVELOCITYLIMIT8: ".plannedTrajPort.plannedTraj_8.velocityLimitReq_mps",
            self.Columns.TRAJVELOCITYLIMIT9: ".plannedTrajPort.plannedTraj_9.velocityLimitReq_mps",
            self.Columns.TRAJVELOCITYLIMIT10: ".plannedTrajPort.plannedTraj_10.velocityLimitReq_mps",
            self.Columns.TRAJVELOCITYLIMIT11: ".plannedTrajPort.plannedTraj_11.velocityLimitReq_mps",
            self.Columns.TRAJVELOCITYLIMIT12: ".plannedTrajPort.plannedTraj_12.velocityLimitReq_mps",
            self.Columns.TRAJVELOCITYLIMIT13: ".plannedTrajPort.plannedTraj_13.velocityLimitReq_mps",
            self.Columns.TRAJVELOCITYLIMIT14: ".plannedTrajPort.plannedTraj_14.velocityLimitReq_mps",
            self.Columns.TRAJVELOCITYLIMIT15: ".plannedTrajPort.plannedTraj_15.velocityLimitReq_mps",
            self.Columns.TRAJVELOCITYLIMIT16: ".plannedTrajPort.plannedTraj_16.velocityLimitReq_mps",
            self.Columns.TRAJVELOCITYLIMIT17: ".plannedTrajPort.plannedTraj_17.velocityLimitReq_mps",
            self.Columns.TRAJVELOCITYLIMIT18: ".plannedTrajPort.plannedTraj_18.velocityLimitReq_mps",
            self.Columns.TRAJVELOCITYLIMIT19: ".plannedTrajPort.plannedTraj_19.velocityLimitReq_mps",
            # self.Columns.TRAJVELOCITYLIMIT: [".plannedTrajPort.plannedTraj_%.velocityLimitReq_mps",]
        }


class SISignals(SignalDefinition):
    """SISignals signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "time"
        AP_STATE = "Ap_state"
        VELOCITY = "Velocity"
        EGO_POS_X = "Ego_pos_x"
        EGO_POS_Y = "Ego_pos_y"
        EGO_POS_YAW = "Ego_pos_yaw"
        GT_DELIMITERX = "GT_DelimiterX"
        GT_DELIMITERY = "GT_DelimiterY"
        NUMBEROFDELIMITERS = "numberOfDelimiters"
        DELIMITERID = "delimiterId"
        NUMVALIDPARKINGBOXES_NU = "numValidParkingBoxes_nu"
        # PARKINGBOXES = "parkingBoxes"
        NUMBEROFVERTICES = "numberOfVertices"
        VERTICES_X = "vertices_x"
        PARKING_SCENARIO_0 = "parkingScenario_0"
        PARKING_SCENARIO_1 = "parkingScenario_1"
        PARKING_SCENARIO_2 = "parkingScenario_2"
        PARKING_SCENARIO_3 = "parkingScenario_3"
        PARKING_SCENARIO_4 = "parkingScenario_4"
        PARKING_SCENARIO_5 = "parkingScenario_5"
        PARKING_SCENARIO_6 = "parkingScenario_6"
        PARKING_SCENARIO_7 = "parkingScenario_7"
        VERTICES_Y = "vertices_y"
        NUMBEROFOBJECTS = "numberOfObjects"
        HEIGHTCONFIDENCE_BODYTRAVERSABLE = "bodyTraversable"
        HEIGHTCONFIDENCE_HANGING = "hanging"
        HEIGHTCONFIDENCE_HIGH = "high"
        HEIGHTCONFIDENCE_WHEELTRAVERSALE = "wheelTraversable"
        # SLOTCOORDINATES_FRONTLEFT_X = "slotCoordinates_FrontLeft_x"
        # SLOTCOORDINATES_FRONTLEFT_Y = "slotCoordinates_FrontLeft_y"
        # SLOTCOORDINATES_FRONTRIGHT_X = "slotCoordinates_FrontRight_x"
        # SLOTCOORDINATES_FRONTRIGHT_Y = "slotCoordinates_FrontRight_y"
        # SLOTCOORDINATES_REARLEFT_X = "slotCoordinates_RearLeft_x"
        # SLOTCOORDINATES_REARLEFT_Y = "slotCoordinates_RearLeft_y"
        # SLOTCOORDINATES_REARRIGHT_X = "slotCoordinates_RearRight_x"
        # SLOTCOORDINATES_REARRIGHT_Y = "slotCoordinates_RearRight_y"
        DELIMITERS_ENDPOINTXPOSITION = "delimiters_endPointXPosition"
        DELIMITERS_ENDPOINTYPOSITION = "delimiters_endPointYPosition"
        DELIMITERS_STARTPOINTXPOSITION = "delimiters_startPointXPosition"
        DELIMITERS_STARTPOINTYPOSITION = "delimiters_startPointYPosition"
        parkingBoxID_nu = "parkingBoxID"
        parkingBoxID_nu1 = "parkingBoxID1"
        parkingBoxID_nu2 = "parkingBoxID2"
        parkingBoxID_nu3 = "parkingBoxID3"
        parkingBoxID_nu4 = "parkingBoxID4"
        parkingBoxID_nu5 = "parkingBoxID5"
        parkingBoxID_nu6 = "parkingBoxID6"
        parkingBoxID_nu7 = "parkingBoxID7"

        PARKBOX_COORDINATES_LIST_0 = "ParkBox_Coordinates_list_0"
        PARKBOX_COORDINATES_LIST = "ParkBox_Coordinates_list_{}"
        DELIMITERS_COORDINATES_LIST = "DELIMITERS_Coordinates_list_{}"
        PB_SLOTCORDINATES_FRONTLEFT_X = "pb_slotCoordinates_FrontLeftx"
        PB_SLOTCORDINATES_FRONTLEFT_X_0 = "pb_slotCoordinates_FrontLeftx_0"
        PB_SLOTCORDINATES_FRONTLEFT_Y_0 = "pb_slotCoordinates_FrontLefty_0"
        PB_SLOTCORDINATES_FRONTRIGHT_X_0 = "pb_slotCoordinates_FrontRightx_0"
        PB_SLOTCORDINATES_FRONTRIGHT_Y_0 = "pb_slotCoordinates_FrontRighty_0"
        PB_SLOTCORDINATES_REARLEFT_X_0 = "pb_slotCoordinates_RearLeftx_0"
        PB_SLOTCORDINATES_REARLEFT_Y_0 = "pb_slotCoordinates_RearLefty_0"
        PB_SLOTCORDINATES_REARRIGHT_X_0 = "pb_slotCoordinates_RearRightx_0"
        PB_SLOTCORDINATES_REARRIGHT_Y_0 = "pb_slotCoordinates_RearRighty_0"

        PB_SLOTCORDINATES_FRONTLEFT_X_1 = "pb_slotCoordinates_FrontLeftx_1"
        PB_SLOTCORDINATES_FRONTLEFT_Y_1 = "pb_slotCoordinates_FrontLefty_1"
        PB_SLOTCORDINATES_FRONTRIGHT_X_1 = "pb_slotCoordinates_FrontRightx_1"
        PB_SLOTCORDINATES_FRONTRIGHT_Y_1 = "pb_slotCoordinates_FrontRighty_1"
        PB_SLOTCORDINATES_REARLEFT_X_1 = "pb_slotCoordinates_RearLeftx_1"
        PB_SLOTCORDINATES_REARLEFT_Y_1 = "pb_slotCoordinates_RearLefty_1"
        PB_SLOTCORDINATES_REARRIGHT_X_1 = "pb_slotCoordinates_RearRightx_1"
        PB_SLOTCORDINATES_REARRIGHT_Y_1 = "pb_slotCoordinates_RearRighty_1"
        PB_SLOTCORDINATES_FRONTLEFT_X_2 = "pb_slotCoordinates_FrontLeftx_2"
        PB_SLOTCORDINATES_FRONTLEFT_Y_2 = "pb_slotCoordinates_FrontLefty_2"
        PB_SLOTCORDINATES_FRONTRIGHT_X_2 = "pb_slotCoordinates_FrontRightx_2"
        PB_SLOTCORDINATES_FRONTRIGHT_Y_2 = "pb_slotCoordinates_FrontRighty_2"
        PB_SLOTCORDINATES_REARLEFT_X_2 = "pb_slotCoordinates_RearLeftx_2"
        PB_SLOTCORDINATES_REARLEFT_Y_2 = "pb_slotCoordinates_RearLefty_2"
        PB_SLOTCORDINATES_REARRIGHT_X_2 = "pb_slotCoordinates_RearRightx_2"
        PB_SLOTCORDINATES_REARRIGHT_Y_2 = "pb_slotCoordinates_RearRighty_2"
        PB_SLOTCORDINATES_FRONTLEFT_X_3 = "pb_slotCoordinates_FrontLeftx_3"
        PB_SLOTCORDINATES_FRONTLEFT_Y_3 = "pb_slotCoordinates_FrontLefty_3"
        PB_SLOTCORDINATES_FRONTRIGHT_X_3 = "pb_slotCoordinates_FrontRightx_3"
        PB_SLOTCORDINATES_FRONTRIGHT_Y_3 = "pb_slotCoordinates_FrontRighty_3"
        PB_SLOTCORDINATES_REARLEFT_X_3 = "pb_slotCoordinates_RearLeftx_3"
        PB_SLOTCORDINATES_REARLEFT_Y_3 = "pb_slotCoordinates_RearLefty_3"
        PB_SLOTCORDINATES_REARRIGHT_X_3 = "pb_slotCoordinates_RearRightx_3"
        PB_SLOTCORDINATES_REARRIGHT_Y_3 = "pb_slotCoordinates_RearRighty_3"
        PB_SLOTCORDINATES_FRONTLEFT_X_4 = "pb_slotCoordinates_FrontLeftx_4"
        PB_SLOTCORDINATES_FRONTLEFT_Y_4 = "pb_slotCoordinates_FrontLefty_4"
        PB_SLOTCORDINATES_FRONTRIGHT_X_4 = "pb_slotCoordinates_FrontRightx_4"
        PB_SLOTCORDINATES_FRONTRIGHT_Y_4 = "pb_slotCoordinates_FrontRighty_4"
        PB_SLOTCORDINATES_REARLEFT_X_4 = "pb_slotCoordinates_RearLeftx_4"
        PB_SLOTCORDINATES_REARLEFT_Y_4 = "pb_slotCoordinates_RearLefty_4"
        PB_SLOTCORDINATES_REARRIGHT_X_4 = "pb_slotCoordinates_RearRightx_4"
        PB_SLOTCORDINATES_REARRIGHT_Y_4 = "pb_slotCoordinates_RearRighty_4"
        PB_SLOTCORDINATES_FRONTLEFT_X_5 = "pb_slotCoordinates_FrontLeftx_5"
        PB_SLOTCORDINATES_FRONTLEFT_Y_5 = "pb_slotCoordinates_FrontLefty_5"
        PB_SLOTCORDINATES_FRONTRIGHT_X_5 = "pb_slotCoordinates_FrontRightx_5"
        PB_SLOTCORDINATES_FRONTRIGHT_Y_5 = "pb_slotCoordinates_FrontRighty_5"
        PB_SLOTCORDINATES_REARLEFT_X_5 = "pb_slotCoordinates_RearLeftx_5"
        PB_SLOTCORDINATES_REARLEFT_Y_5 = "pb_slotCoordinates_RearLefty_5"
        PB_SLOTCORDINATES_REARRIGHT_X_5 = "pb_slotCoordinates_RearRightx_5"
        PB_SLOTCORDINATES_REARRIGHT_Y_5 = "pb_slotCoordinates_RearRighty_5"
        PB_SLOTCORDINATES_FRONTLEFT_X_6 = "pb_slotCoordinates_FrontLeftx_6"
        PB_SLOTCORDINATES_FRONTLEFT_Y_6 = "pb_slotCoordinates_FrontLefty_6"
        PB_SLOTCORDINATES_FRONTRIGHT_X_6 = "pb_slotCoordinates_FrontRightx_6"
        PB_SLOTCORDINATES_FRONTRIGHT_Y_6 = "pb_slotCoordinates_FrontRighty_6"
        PB_SLOTCORDINATES_REARLEFT_X_6 = "pb_slotCoordinates_RearLeftx_6"
        PB_SLOTCORDINATES_REARLEFT_Y_6 = "pb_slotCoordinates_RearLefty_6"
        PB_SLOTCORDINATES_REARRIGHT_X_6 = "pb_slotCoordinates_RearRightx_6"
        PB_SLOTCORDINATES_REARRIGHT_Y_6 = "pb_slotCoordinates_RearRighty_6"
        PB_SLOTCORDINATES_FRONTLEFT_X_7 = "pb_slotCoordinates_FrontLeftx_7"
        PB_SLOTCORDINATES_FRONTLEFT_Y_7 = "pb_slotCoordinates_FrontLefty_7"
        PB_SLOTCORDINATES_FRONTRIGHT_X_7 = "pb_slotCoordinates_FrontRightx_7"
        PB_SLOTCORDINATES_FRONTRIGHT_Y_7 = "pb_slotCoordinates_FrontRighty_7"
        PB_SLOTCORDINATES_REARLEFT_X_7 = "pb_slotCoordinates_RearLeftx_7"
        PB_SLOTCORDINATES_REARLEFT_Y_7 = "pb_slotCoordinates_RearLefty_7"
        PB_SLOTCORDINATES_REARRIGHT_X_7 = "pb_slotCoordinates_RearRightx_7"
        PB_SLOTCORDINATES_REARRIGHT_Y_7 = "pb_slotCoordinates_RearRighty_7"
        PB_SLOTCORDINATES_FRONTLEFT_X_8 = "pb_slotCoordinates_FrontLeftx_8"
        PB_SLOTCORDINATES_FRONTLEFT_Y_8 = "pb_slotCoordinates_FrontLefty_8"
        PB_SLOTCORDINATES_FRONTRIGHT_X_8 = "pb_slotCoordinates_FrontRightx_8"
        PB_SLOTCORDINATES_FRONTRIGHT_Y_8 = "pb_slotCoordinates_FrontRighty_8"
        PB_SLOTCORDINATES_REARLEFT_X_8 = "pb_slotCoordinates_RearLeftx_8"
        PB_SLOTCORDINATES_REARLEFT_Y_8 = "pb_slotCoordinates_RearLefty_8"
        PB_SLOTCORDINATES_REARRIGHT_X_8 = "pb_slotCoordinates_RearRightx_8"
        PB_SLOTCORDINATES_REARRIGHT_Y_8 = "pb_slotCoordinates_RearRighty_8"

        STATICOBJECT_NUMBEROFVERTICES = "staticObjectnumberOfVertices"
        STATICOBJECT_VERTICES_X = "StaticObjectVertices_x"
        STATICOBJECT_VERTICES_Y = "StaticObjectVertices_y"
        # STATICOBJECT_NUMBEROFOBJECTS = "numberOfStaticObjects"
        STATICOBJECT_OBJECTSEMENTICTYPE = "semanticType"
        STATICOBJECT_OBJECTUSEDVERTICES = "usedVertices"

        ENVMODELPORTNUMBEROFSTATICOBJECT = "numberOfStaticObjects_u8"
        ENVMODELPORTEGOVEHICLEPOSEFORAP_X_M = "pos_x_m"
        ENVMODELPORTEGOVEHICLEPOSEFORAP_Y_M = "pos_y_m"
        # ENVMODELPORTSTATICOBJECTSHAPE_M_0_X = "objShape_m_0_x"
        # ENVMODELPORTSTATICOBJECTSHAPE_M_0_Y = "objShape_m_0_y"

        ENVMODELPORTSTATICOBJECTSHAPE_M_0_X = "staticObject_0_objShape_m_0.x"
        ENVMODELPORTSTATICOBJECTSHAPE_M_0_Y = "staticObject_0_objShape_m_0.y"

        ENVMODELPORTSTATICOBJECTSHAPE_1_M_0_X = "objShape_1_m_0.x"
        ENVMODELPORTSTATICOBJECTSHAPE_1_M_0_Y = "objShape_1_m_0.y"

        ENVMODELPORTDYNAMICOBJECTSHAPE_0_X = "objShape_0.x"
        ENVMODELPORTDYNAMICOBJECTSHAPE_0_Y = "objShape_0.y"
        ENVMODELPORTDYNAMICOBJECTSHAPE_1_X = "objShape_1.x"
        ENVMODELPORTDYNAMICOBJECTSHAPE_1_Y = "objShape_1.y"
        COLLENVMODELPORTSTATICOBJECTSHAPE_M_0_X = "objShape_m_0.x"
        COLLENVMODELPORTSTATICOBJECTSHAPE_M_0_Y = "objShape_m_0.y"
        COLLENVMODELPORTSTATICOBJECTSHAPE_1_M_0_X = "objShape_1_m_0.x"
        COLLENVMODELPORTSTATICOBJECTSHAPE_1_M_0_Y = "objShape_1_m_0.y"

        COLLENVMODELPORTDYNAMICOBJECTSHAPE_M_0_X = "objShape_m_0.x"
        COLLENVMODELPORTDYNAMICOBJECTSHAPE_M_0_Y = "objShape_m_0.y"
        COLLENVMODELPORTDYNAMICOBJECTSHAPE_1_M_0_X = "objShape_1_m_0.x"
        COLLENVMODELPORTDYNAMICOBJECTSHAPE_1_M_0_Y = "objShape_1_m_0.y"

        ODOESTIMATION_XPOSITION_M = "odoEstimation.xPosition_m"
        ODOESTIMATION_YPOSITION_M = "odoEstimation.yPosition_m"
        ODOESTIMATION_YANGLE = "odoEstimation.yAngle"
        ODOESTIMATIONPORT_CYCLE_COUNTER = "odoEstimationPort.cycleCounter"
        SI_CYCLE_COUNTER = "si_cycleCounter"
        PB_0_PARKINGSCENARIO_NU = "parkingBoxes_0.parkingScenario_nu"
        STATICOBJECT_0_OBJSHAPE_M_ARRAY_0_X = "staticObject_0_objShape_m.array_x_dir"
        STATICOBJECT_0_OBJSHAPE_M_ARRAY_0_Y = "staticObject_0_objShape_m.array_y_dir"
        STATICOBJECT_1_OBJSHAPE_M_ARRAY_0_X = "staticObject_1_objShape_m.array_x_dir"
        STATICOBJECT_1_OBJSHAPE_M_ARRAY_0_Y = "staticObject_1_objShape_m.array_y_dir"
        STATICOBJECT_ACTUALSIZE = "objShape_m.actualSize"
        NUMBERVALIDSTATICOBJECTS = "collEnvModelPort.numberOfStaticObjects_u8"
        NUMBERVALIDSTATICOBJECTSINWRLDCRD = "envModelPort.numberOfStaticObjects_u8"
        NUMBERVALIDDYNAMICOBJECTSWRLDCRD = "envModelPort.numberOfDynamicObjects_u8"

        ######
        STATICOBJECTSHAPE_0_M_0_x = "collEnvModelPort.staticObjects_0.objShape_m_0.x"
        STATICOBJECTSHAPE_0_M_1_x = "collEnvModelPort.staticObjects_0.objShape_m_1.x"
        STATICOBJECTSHAPE_0_M_2_x = "collEnvModelPort.staticObjects_0.objShape_m_2.x"
        STATICOBJECTSHAPE_0_M_3_x = "collEnvModelPort.staticObjects_0.objShape_m_3.x"
        STATICOBJECTSHAPE_0_M_4_x = "collEnvModelPort.staticObjects_0.objShape_m_4.x"
        STATICOBJECTSHAPE_0_M_5_x = "collEnvModelPort.staticObjects_0.objShape_m_5.x"
        STATICOBJECTSHAPE_0_M_6_x = "collEnvModelPort.staticObjects_0.objShape_m_6.x"
        STATICOBJECTSHAPE_0_M_7_x = "collEnvModelPort.staticObjects_0.objShape_m_7.x"
        STATICOBJECTSHAPE_0_M_8_x = "collEnvModelPort.staticObjects_0.objShape_m_8.x"
        STATICOBJECTSHAPE_0_M_9_x = "collEnvModelPort.staticObjects_0.objShape_m_9.x"
        STATICOBJECTSHAPE_0_M_10_x = "collEnvModelPort.staticObjects_0.objShape_m_10.x"
        STATICOBJECTSHAPE_0_M_11_x = "collEnvModelPort.staticObjects_0.objShape_m_11.x"
        STATICOBJECTSHAPE_0_M_12_x = "collEnvModelPort.staticObjects_0.objShape_m_12.x"
        STATICOBJECTSHAPE_0_M_13_x = "collEnvModelPort.staticObjects_0.objShape_m_13.x"
        STATICOBJECTSHAPE_0_M_14_x = "collEnvModelPort.staticObjects_0.objShape_m_14.x"
        STATICOBJECTSHAPE_0_M_15_x = "collEnvModelPort.staticObjects_0.objShape_m_15.x"

        STATICOBJECTSHAPE_0_M_0_y = "collEnvModelPort.staticObjects_0.objShape_m_0.y"
        STATICOBJECTSHAPE_0_M_1_y = "collEnvModelPort.staticObjects_0.objShape_m_1.y"
        STATICOBJECTSHAPE_0_M_2_y = "collEnvModelPort.staticObjects_0.objShape_m_2.y"
        STATICOBJECTSHAPE_0_M_3_y = "collEnvModelPort.staticObjects_0.objShape_m_3.y"
        STATICOBJECTSHAPE_0_M_4_y = "collEnvModelPort.staticObjects_0.objShape_m_4.y"
        STATICOBJECTSHAPE_0_M_5_y = "collEnvModelPort.staticObjects_0.objShape_m_5.y"
        STATICOBJECTSHAPE_0_M_6_y = "collEnvModelPort.staticObjects_0.objShape_m_6.y"
        STATICOBJECTSHAPE_0_M_7_y = "collEnvModelPort.staticObjects_0.objShape_m_7.y"
        STATICOBJECTSHAPE_0_M_8_y = "collEnvModelPort.staticObjects_0.objShape_m_8.y"
        STATICOBJECTSHAPE_0_M_9_y = "collEnvModelPort.staticObjects_0.objShape_m_9.y"
        STATICOBJECTSHAPE_0_M_10_y = "collEnvModelPort.staticObjects_0.objShape_m_10.y"
        STATICOBJECTSHAPE_0_M_11_y = "collEnvModelPort.staticObjects_0.objShape_m_11.y"
        STATICOBJECTSHAPE_0_M_12_y = "collEnvModelPort.staticObjects_0.objShape_m_12.y"
        STATICOBJECTSHAPE_0_M_13_y = "collEnvModelPort.staticObjects_0.objShape_m_13.y"
        STATICOBJECTSHAPE_0_M_14_y = "collEnvModelPort.staticObjects_0.objShape_m_14.y"
        STATICOBJECTSHAPE_0_M_15_y = "collEnvModelPort.staticObjects_0.objShape_m_15.y"

        STATICOBJECTSHAPE_1_M_0_x = "collEnvModelPort.staticObjects_1.objShape_m_0.x"
        STATICOBJECTSHAPE_1_M_1_x = "collEnvModelPort.staticObjects_1.objShape_m_1.x"
        STATICOBJECTSHAPE_1_M_2_x = "collEnvModelPort.staticObjects_1.objShape_m_2.x"
        STATICOBJECTSHAPE_1_M_3_x = "collEnvModelPort.staticObjects_1.objShape_m_3.x"
        STATICOBJECTSHAPE_1_M_4_x = "collEnvModelPort.staticObjects_1.objShape_m_4.x"
        STATICOBJECTSHAPE_1_M_5_x = "collEnvModelPort.staticObjects_1.objShape_m_5.x"
        STATICOBJECTSHAPE_1_M_6_x = "collEnvModelPort.staticObjects_1.objShape_m_6.x"
        STATICOBJECTSHAPE_1_M_7_x = "collEnvModelPort.staticObjects_1.objShape_m_7.x"
        STATICOBJECTSHAPE_1_M_8_x = "collEnvModelPort.staticObjects_1.objShape_m_8.x"
        STATICOBJECTSHAPE_1_M_9_x = "collEnvModelPort.staticObjects_1.objShape_m_9.x"
        STATICOBJECTSHAPE_1_M_10_x = "collEnvModelPort.staticObjects_1.objShape_m_10.x"
        STATICOBJECTSHAPE_1_M_11_x = "collEnvModelPort.staticObjects_1.objShape_m_11.x"
        STATICOBJECTSHAPE_1_M_12_x = "collEnvModelPort.staticObjects_1.objShape_m_12.x"
        STATICOBJECTSHAPE_1_M_13_x = "collEnvModelPort.staticObjects_1.objShape_m_13.x"
        STATICOBJECTSHAPE_1_M_14_x = "collEnvModelPort.staticObjects_1.objShape_m_14.x"
        STATICOBJECTSHAPE_1_M_15_x = "collEnvModelPort.staticObjects_1.objShape_m_15.x"

        STATICOBJECTSHAPE_1_M_0_y = "collEnvModelPort.staticObjects_1.objShape_m_0.y"
        STATICOBJECTSHAPE_1_M_1_y = "collEnvModelPort.staticObjects_1.objShape_m_1.y"
        STATICOBJECTSHAPE_1_M_2_y = "collEnvModelPort.staticObjects_1.objShape_m_2.y"
        STATICOBJECTSHAPE_1_M_3_y = "collEnvModelPort.staticObjects_1.objShape_m_3.y"
        STATICOBJECTSHAPE_1_M_4_y = "collEnvModelPort.staticObjects_1.objShape_m_4.y"
        STATICOBJECTSHAPE_1_M_5_y = "collEnvModelPort.staticObjects_1.objShape_m_5.y"
        STATICOBJECTSHAPE_1_M_6_y = "collEnvModelPort.staticObjects_1.objShape_m_6.y"
        STATICOBJECTSHAPE_1_M_7_y = "collEnvModelPort.staticObjects_1.objShape_m_7.y"
        STATICOBJECTSHAPE_1_M_8_y = "collEnvModelPort.staticObjects_1.objShape_m_8.y"
        STATICOBJECTSHAPE_1_M_9_y = "collEnvModelPort.staticObjects_1.objShape_m_9.y"
        STATICOBJECTSHAPE_1_M_10_y = "collEnvModelPort.staticObjects_1.objShape_m_10.y"
        STATICOBJECTSHAPE_1_M_11_y = "collEnvModelPort.staticObjects_1.objShape_m_11.y"
        STATICOBJECTSHAPE_1_M_12_y = "collEnvModelPort.staticObjects_1.objShape_m_12.y"
        STATICOBJECTSHAPE_1_M_13_y = "collEnvModelPort.staticObjects_1.objShape_m_13.y"
        STATICOBJECTSHAPE_1_M_14_y = "collEnvModelPort.staticObjects_1.objShape_m_14.y"
        STATICOBJECTSHAPE_1_M_15_y = "collEnvModelPort.staticObjects_1.objShape_m_15.y"
        STATICOBJECTSHAPE_3_M_0_x = "collEnvModelPort.staticObjects_3.objShape_m_0.x"
        STATICOBJECTSHAPE_3_M_1_x = "collEnvModelPort.staticObjects_3.objShape_m_1.x"
        STATICOBJECTSHAPE_3_M_2_x = "collEnvModelPort.staticObjects_3.objShape_m_2.x"
        STATICOBJECTSHAPE_3_M_3_x = "collEnvModelPort.staticObjects_3.objShape_m_3.x"
        STATICOBJECTSHAPE_3_M_4_x = "collEnvModelPort.staticObjects_3.objShape_m_4.x"
        STATICOBJECTSHAPE_3_M_5_x = "collEnvModelPort.staticObjects_3.objShape_m_5.x"
        STATICOBJECTSHAPE_3_M_6_x = "collEnvModelPort.staticObjects_3.objShape_m_6.x"
        STATICOBJECTSHAPE_3_M_7_x = "collEnvModelPort.staticObjects_3.objShape_m_7.x"
        STATICOBJECTSHAPE_3_M_8_x = "collEnvModelPort.staticObjects_3.objShape_m_8.x"
        STATICOBJECTSHAPE_3_M_9_x = "collEnvModelPort.staticObjects_3.objShape_m_9.x"
        STATICOBJECTSHAPE_3_M_10_x = "collEnvModelPort.staticObjects_3.objShape_m_10.x"
        STATICOBJECTSHAPE_3_M_11_x = "collEnvModelPort.staticObjects_3.objShape_m_11.x"
        STATICOBJECTSHAPE_3_M_12_x = "collEnvModelPort.staticObjects_3.objShape_m_12.x"
        STATICOBJECTSHAPE_3_M_13_x = "collEnvModelPort.staticObjects_3.objShape_m_13.x"
        STATICOBJECTSHAPE_3_M_14_x = "collEnvModelPort.staticObjects_3.objShape_m_14.x"
        STATICOBJECTSHAPE_3_M_15_x = "collEnvModelPort.staticObjects_3.objShape_m_15.x"

        STATICOBJECTSHAPE_3_M_0_y = "collEnvModelPort.staticObjects_3.objShape_m_0.y"
        STATICOBJECTSHAPE_3_M_1_y = "collEnvModelPort.staticObjects_3.objShape_m_1.y"
        STATICOBJECTSHAPE_3_M_2_y = "collEnvModelPort.staticObjects_3.objShape_m_2.y"
        STATICOBJECTSHAPE_3_M_3_y = "collEnvModelPort.staticObjects_3.objShape_m_3.y"
        STATICOBJECTSHAPE_3_M_4_y = "collEnvModelPort.staticObjects_3.objShape_m_4.y"
        STATICOBJECTSHAPE_3_M_5_y = "collEnvModelPort.staticObjects_3.objShape_m_5.y"
        STATICOBJECTSHAPE_3_M_6_y = "collEnvModelPort.staticObjects_3.objShape_m_6.y"
        STATICOBJECTSHAPE_3_M_7_y = "collEnvModelPort.staticObjects_3.objShape_m_7.y"
        STATICOBJECTSHAPE_3_M_8_y = "collEnvModelPort.staticObjects_3.objShape_m_8.y"
        STATICOBJECTSHAPE_3_M_9_y = "collEnvModelPort.staticObjects_3.objShape_m_9.y"
        STATICOBJECTSHAPE_3_M_10_y = "collEnvModelPort.staticObjects_3.objShape_m_10.y"
        STATICOBJECTSHAPE_3_M_11_y = "collEnvModelPort.staticObjects_3.objShape_m_11.y"
        STATICOBJECTSHAPE_3_M_12_y = "collEnvModelPort.staticObjects_3.objShape_m_12.y"
        STATICOBJECTSHAPE_3_M_13_y = "collEnvModelPort.staticObjects_3.objShape_m_13.y"
        STATICOBJECTSHAPE_3_M_14_y = "collEnvModelPort.staticObjects_3.objShape_m_14.y"
        STATICOBJECTSHAPE_3_M_15_y = "collEnvModelPort.staticObjects_3.objShape_m_15.y"

        STATICOBJECTSHAPE_2_M_0_x = "collEnvModelPort.staticObjects_2.objShape_m_0.x"
        STATICOBJECTSHAPE_2_M_1_x = "collEnvModelPort.staticObjects_2.objShape_m_1.x"
        STATICOBJECTSHAPE_2_M_2_x = "collEnvModelPort.staticObjects_2.objShape_m_2.x"
        STATICOBJECTSHAPE_2_M_3_x = "collEnvModelPort.staticObjects_2.objShape_m_3.x"
        STATICOBJECTSHAPE_2_M_4_x = "collEnvModelPort.staticObjects_2.objShape_m_4.x"
        STATICOBJECTSHAPE_2_M_5_x = "collEnvModelPort.staticObjects_2.objShape_m_5.x"
        STATICOBJECTSHAPE_2_M_6_x = "collEnvModelPort.staticObjects_2.objShape_m_6.x"
        STATICOBJECTSHAPE_2_M_7_x = "collEnvModelPort.staticObjects_2.objShape_m_7.x"
        STATICOBJECTSHAPE_2_M_8_x = "collEnvModelPort.staticObjects_2.objShape_m_8.x"
        STATICOBJECTSHAPE_2_M_9_x = "collEnvModelPort.staticObjects_2.objShape_m_9.x"
        STATICOBJECTSHAPE_2_M_10_x = "collEnvModelPort.staticObjects_2.objShape_m_10.x"
        STATICOBJECTSHAPE_2_M_11_x = "collEnvModelPort.staticObjects_2.objShape_m_11.x"
        STATICOBJECTSHAPE_2_M_12_x = "collEnvModelPort.staticObjects_2.objShape_m_12.x"
        STATICOBJECTSHAPE_2_M_13_x = "collEnvModelPort.staticObjects_2.objShape_m_13.x"
        STATICOBJECTSHAPE_2_M_14_x = "collEnvModelPort.staticObjects_2.objShape_m_14.x"
        STATICOBJECTSHAPE_2_M_15_x = "collEnvModelPort.staticObjects_2.objShape_m_15.x"

        STATICOBJECTSHAPE_2_M_0_y = "collEnvModelPort.staticObjects_2.objShape_m_0.y"
        STATICOBJECTSHAPE_2_M_1_y = "collEnvModelPort.staticObjects_2.objShape_m_1.y"
        STATICOBJECTSHAPE_2_M_2_y = "collEnvModelPort.staticObjects_2.objShape_m_2.y"
        STATICOBJECTSHAPE_2_M_3_y = "collEnvModelPort.staticObjects_2.objShape_m_3.y"
        STATICOBJECTSHAPE_2_M_4_y = "collEnvModelPort.staticObjects_2.objShape_m_4.y"
        STATICOBJECTSHAPE_2_M_5_y = "collEnvModelPort.staticObjects_2.objShape_m_5.y"
        STATICOBJECTSHAPE_2_M_6_y = "collEnvModelPort.staticObjects_2.objShape_m_6.y"
        STATICOBJECTSHAPE_2_M_7_y = "collEnvModelPort.staticObjects_2.objShape_m_7.y"
        STATICOBJECTSHAPE_2_M_8_y = "collEnvModelPort.staticObjects_2.objShape_m_8.y"
        STATICOBJECTSHAPE_2_M_9_y = "collEnvModelPort.staticObjects_2.objShape_m_9.y"
        STATICOBJECTSHAPE_2_M_10_y = "collEnvModelPort.staticObjects_2.objShape_m_10.y"
        STATICOBJECTSHAPE_2_M_11_y = "collEnvModelPort.staticObjects_2.objShape_m_11.y"
        STATICOBJECTSHAPE_2_M_12_y = "collEnvModelPort.staticObjects_2.objShape_m_12.y"
        STATICOBJECTSHAPE_2_M_13_y = "collEnvModelPort.staticObjects_2.objShape_m_13.y"
        STATICOBJECTSHAPE_2_M_14_y = "collEnvModelPort.staticObjects_2.objShape_m_14.y"
        STATICOBJECTSHAPE_2_M_15_y = "collEnvModelPort.staticObjects_2.objShape_m_15.y"

        ######
        STATICOBJECT_2_OBJSHAPE_M_ARRAY_0_X = "staticObject_2_objShape_m.array_x_dir"
        STATICOBJECT_2_OBJSHAPE_M_ARRAY_0_Y = "staticObject_2_objShape_m.array_y_dir"
        STATICOBJECTSHAPEWRLDCRD_0_M_0_x = "envModelPort.staticObjects_0.objShape_m_0.x"
        STATICOBJECTSHAPEWRLDCRD_0_M_1_x = "envModelPort.staticObjects_0.objShape_m_1.x"
        STATICOBJECTSHAPEWRLDCRD_0_M_2_x = "envModelPort.staticObjects_0.objShape_m_2.x"
        STATICOBJECTSHAPEWRLDCRD_0_M_3_x = "envModelPort.staticObjects_0.objShape_m_3.x"
        STATICOBJECTSHAPEWRLDCRD_0_M_4_x = "envModelPort.staticObjects_0.objShape_m_4.x"
        STATICOBJECTSHAPEWRLDCRD_0_M_5_x = "envModelPort.staticObjects_0.objShape_m_5.x"
        STATICOBJECTSHAPEWRLDCRD_0_M_6_x = "envModelPort.staticObjects_0.objShape_m_6.x"
        STATICOBJECTSHAPEWRLDCRD_0_M_7_x = "envModelPort.staticObjects_0.objShape_m_7.x"
        STATICOBJECTSHAPEWRLDCRD_0_M_8_x = "envModelPort.staticObjects_0.objShape_m_8.x"
        STATICOBJECTSHAPEWRLDCRD_0_M_9_x = "envModelPort.staticObjects_0.objShape_m_9.x"
        STATICOBJECTSHAPEWRLDCRD_0_M_10_x = "envModelPort.staticObjects_0.objShape_m_10.x"
        STATICOBJECTSHAPEWRLDCRD_0_M_11_x = "envModelPort.staticObjects_0.objShape_m_11.x"
        STATICOBJECTSHAPEWRLDCRD_0_M_12_x = "envModelPort.staticObjects_0.objShape_m_12.x"
        STATICOBJECTSHAPEWRLDCRD_0_M_13_x = "envModelPort.staticObjects_0.objShape_m_13.x"
        STATICOBJECTSHAPEWRLDCRD_0_M_14_x = "envModelPort.staticObjects_0.objShape_m_14.x"
        STATICOBJECTSHAPEWRLDCRD_0_M_15_x = "envModelPort.staticObjects_0.objShape_m_15.x"

        STATICOBJECTSHAPEWRLDCRD_0_M_0_y = "envModelPort.staticObjects_0.objShape_m_0.y"
        STATICOBJECTSHAPEWRLDCRD_0_M_1_y = "envModelPort.staticObjects_0.objShape_m_1.y"
        STATICOBJECTSHAPEWRLDCRD_0_M_2_y = "envModelPort.staticObjects_0.objShape_m_2.y"
        STATICOBJECTSHAPEWRLDCRD_0_M_3_y = "envModelPort.staticObjects_0.objShape_m_3.y"
        STATICOBJECTSHAPEWRLDCRD_0_M_4_y = "envModelPort.staticObjects_0.objShape_m_4.y"
        STATICOBJECTSHAPEWRLDCRD_0_M_5_y = "envModelPort.staticObjects_0.objShape_m_5.y"
        STATICOBJECTSHAPEWRLDCRD_0_M_6_y = "envModelPort.staticObjects_0.objShape_m_6.y"
        STATICOBJECTSHAPEWRLDCRD_0_M_7_y = "envModelPort.staticObjects_0.objShape_m_7.y"
        STATICOBJECTSHAPEWRLDCRD_0_M_8_y = "envModelPort.staticObjects_0.objShape_m_8.y"
        STATICOBJECTSHAPEWRLDCRD_0_M_9_y = "envModelPort.staticObjects_0.objShape_m_9.y"
        STATICOBJECTSHAPEWRLDCRD_0_M_10_y = "envModelPort.staticObjects_0.objShape_m_10.y"
        STATICOBJECTSHAPEWRLDCRD_0_M_11_y = "envModelPort.staticObjects_0.objShape_m_11.y"
        STATICOBJECTSHAPEWRLDCRD_0_M_12_y = "envModelPort.staticObjects_0.objShape_m_12.y"
        STATICOBJECTSHAPEWRLDCRD_0_M_13_y = "envModelPort.staticObjects_0.objShape_m_13.y"
        STATICOBJECTSHAPEWRLDCRD_0_M_14_y = "envModelPort.staticObjects_0.objShape_m_14.y"
        STATICOBJECTSHAPEWRLDCRD_0_M_15_y = "envModelPort.staticObjects_0.objShape_m_15.y"

        STATICOBJECTSHAPEWRLDCRD_1_M_0_x = "envModelPort.staticObjects_1.objShape_m_0.x"
        STATICOBJECTSHAPEWRLDCRD_1_M_1_x = "envModelPort.staticObjects_1.objShape_m_1.x"
        STATICOBJECTSHAPEWRLDCRD_1_M_2_x = "envModelPort.staticObjects_1.objShape_m_2.x"
        STATICOBJECTSHAPEWRLDCRD_1_M_3_x = "envModelPort.staticObjects_1.objShape_m_3.x"
        STATICOBJECTSHAPEWRLDCRD_1_M_4_x = "envModelPort.staticObjects_1.objShape_m_4.x"
        STATICOBJECTSHAPEWRLDCRD_1_M_5_x = "envModelPort.staticObjects_1.objShape_m_5.x"
        STATICOBJECTSHAPEWRLDCRD_1_M_6_x = "envModelPort.staticObjects_1.objShape_m_6.x"
        STATICOBJECTSHAPEWRLDCRD_1_M_7_x = "envModelPort.staticObjects_1.objShape_m_7.x"
        STATICOBJECTSHAPEWRLDCRD_1_M_8_x = "envModelPort.staticObjects_1.objShape_m_8.x"
        STATICOBJECTSHAPEWRLDCRD_1_M_9_x = "envModelPort.staticObjects_1.objShape_m_9.x"
        STATICOBJECTSHAPEWRLDCRD_1_M_10_x = "envModelPort.staticObjects_1.objShape_m_10.x"
        STATICOBJECTSHAPEWRLDCRD_1_M_11_x = "envModelPort.staticObjects_1.objShape_m_11.x"
        STATICOBJECTSHAPEWRLDCRD_1_M_12_x = "envModelPort.staticObjects_1.objShape_m_12.x"
        STATICOBJECTSHAPEWRLDCRD_1_M_13_x = "envModelPort.staticObjects_1.objShape_m_13.x"
        STATICOBJECTSHAPEWRLDCRD_1_M_14_x = "envModelPort.staticObjects_1.objShape_m_14.x"
        STATICOBJECTSHAPEWRLDCRD_1_M_15_x = "envModelPort.staticObjects_1.objShape_m_15.x"
        STATICOBJECT_ACTUALSIZE_0 = "objShape_m.actualSize_0"
        STATICOBJECTSHAPEWRLDCRD_1_M_0_y = "envModelPort.staticObjects_1.objShape_m_0.y"
        STATICOBJECTSHAPEWRLDCRD_1_M_1_y = "envModelPort.staticObjects_1.objShape_m_1.y"
        STATICOBJECTSHAPEWRLDCRD_1_M_2_y = "envModelPort.staticObjects_1.objShape_m_2.y"
        STATICOBJECTSHAPEWRLDCRD_1_M_3_y = "envModelPort.staticObjects_1.objShape_m_3.y"
        STATICOBJECTSHAPEWRLDCRD_1_M_4_y = "envModelPort.staticObjects_1.objShape_m_4.y"
        STATICOBJECTSHAPEWRLDCRD_1_M_5_y = "envModelPort.staticObjects_1.objShape_m_5.y"
        STATICOBJECTSHAPEWRLDCRD_1_M_6_y = "envModelPort.staticObjects_1.objShape_m_6.y"
        STATICOBJECTSHAPEWRLDCRD_1_M_7_y = "envModelPort.staticObjects_1.objShape_m_7.y"
        STATICOBJECTSHAPEWRLDCRD_1_M_8_y = "envModelPort.staticObjects_1.objShape_m_8.y"
        STATICOBJECTSHAPEWRLDCRD_1_M_9_y = "envModelPort.staticObjects_1.objShape_m_9.y"
        STATICOBJECTSHAPEWRLDCRD_1_M_10_y = "envModelPort.staticObjects_1.objShape_m_10.y"
        STATICOBJECTSHAPEWRLDCRD_1_M_11_y = "envModelPort.staticObjects_1.objShape_m_11.y"
        STATICOBJECTSHAPEWRLDCRD_1_M_12_y = "envModelPort.staticObjects_1.objShape_m_12.y"
        STATICOBJECTSHAPEWRLDCRD_1_M_13_y = "envModelPort.staticObjects_1.objShape_m_13.y"
        STATICOBJECTSHAPEWRLDCRD_1_M_14_y = "envModelPort.staticObjects_1.objShape_m_14.y"
        STATICOBJECTSHAPEWRLDCRD_1_M_15_y = "envModelPort.staticObjects_1.objShape_m_15.y"

        ####
        STATICOBJECTSHAPEWRLDCRD_2_M_0_x = "envModelPort.staticObjects_2.objShape_m_0.x"
        STATICOBJECTSHAPEWRLDCRD_2_M_1_x = "envModelPort.staticObjects_2.objShape_m_1.x"
        STATICOBJECTSHAPEWRLDCRD_2_M_2_x = "envModelPort.staticObjects_2.objShape_m_2.x"
        STATICOBJECTSHAPEWRLDCRD_2_M_3_x = "envModelPort.staticObjects_2.objShape_m_3.x"
        STATICOBJECTSHAPEWRLDCRD_2_M_4_x = "envModelPort.staticObjects_2.objShape_m_4.x"
        STATICOBJECTSHAPEWRLDCRD_2_M_5_x = "envModelPort.staticObjects_2.objShape_m_5.x"
        STATICOBJECTSHAPEWRLDCRD_2_M_6_x = "envModelPort.staticObjects_2.objShape_m_6.x"
        STATICOBJECTSHAPEWRLDCRD_2_M_7_x = "envModelPort.staticObjects_2.objShape_m_7.x"
        STATICOBJECTSHAPEWRLDCRD_2_M_8_x = "envModelPort.staticObjects_2.objShape_m_8.x"
        STATICOBJECTSHAPEWRLDCRD_2_M_9_x = "envModelPort.staticObjects_2.objShape_m_9.x"
        STATICOBJECTSHAPEWRLDCRD_2_M_10_x = "envModelPort.staticObjects_2.objShape_m_10.x"
        STATICOBJECTSHAPEWRLDCRD_2_M_11_x = "envModelPort.staticObjects_2.objShape_m_11.x"
        STATICOBJECTSHAPEWRLDCRD_2_M_12_x = "envModelPort.staticObjects_2.objShape_m_12.x"
        STATICOBJECTSHAPEWRLDCRD_2_M_13_x = "envModelPort.staticObjects_2.objShape_m_13.x"
        STATICOBJECTSHAPEWRLDCRD_2_M_14_x = "envModelPort.staticObjects_2.objShape_m_14.x"
        STATICOBJECTSHAPEWRLDCRD_2_M_15_x = "envModelPort.staticObjects_2.objShape_m_15.x"

        STATICOBJECTSHAPEWRLDCRD_2_M_0_y = "envModelPort.staticObjects_2.objShape_m_0.y"
        STATICOBJECTSHAPEWRLDCRD_2_M_1_y = "envModelPort.staticObjects_2.objShape_m_1.y"
        STATICOBJECTSHAPEWRLDCRD_2_M_2_y = "envModelPort.staticObjects_2.objShape_m_2.y"
        STATICOBJECTSHAPEWRLDCRD_2_M_3_y = "envModelPort.staticObjects_2.objShape_m_3.y"
        STATICOBJECTSHAPEWRLDCRD_2_M_4_y = "envModelPort.staticObjects_2.objShape_m_4.y"
        STATICOBJECTSHAPEWRLDCRD_2_M_5_y = "envModelPort.staticObjects_2.objShape_m_5.y"
        STATICOBJECTSHAPEWRLDCRD_2_M_6_y = "envModelPort.staticObjects_2.objShape_m_6.y"
        STATICOBJECTSHAPEWRLDCRD_2_M_7_y = "envModelPort.staticObjects_2.objShape_m_7.y"
        STATICOBJECTSHAPEWRLDCRD_2_M_8_y = "envModelPort.staticObjects_2.objShape_m_8.y"
        STATICOBJECTSHAPEWRLDCRD_2_M_9_y = "envModelPort.staticObjects_2.objShape_m_9.y"
        STATICOBJECTSHAPEWRLDCRD_2_M_10_y = "envModelPort.staticObjects_2.objShape_m_10.y"
        STATICOBJECTSHAPEWRLDCRD_2_M_11_y = "envModelPort.staticObjects_2.objShape_m_11.y"
        STATICOBJECTSHAPEWRLDCRD_2_M_12_y = "envModelPort.staticObjects_2.objShape_m_12.y"
        STATICOBJECTSHAPEWRLDCRD_2_M_13_y = "envModelPort.staticObjects_2.objShape_m_13.y"
        STATICOBJECTSHAPEWRLDCRD_2_M_14_y = "envModelPort.staticObjects_2.objShape_m_14.y"
        STATICOBJECTSHAPEWRLDCRD_2_M_15_y = "envModelPort.staticObjects_2.objShape_m_15.y"

        STATICOBJECTSHAPEWRLDCRD_3_M_0_x = "envModelPort.staticObjects_3.objShape_m_0.x"
        STATICOBJECTSHAPEWRLDCRD_3_M_1_x = "envModelPort.staticObjects_3.objShape_m_1.x"
        STATICOBJECTSHAPEWRLDCRD_3_M_2_x = "envModelPort.staticObjects_3.objShape_m_2.x"
        STATICOBJECTSHAPEWRLDCRD_3_M_3_x = "envModelPort.staticObjects_3.objShape_m_3.x"
        STATICOBJECTSHAPEWRLDCRD_3_M_4_x = "envModelPort.staticObjects_3.objShape_m_4.x"
        STATICOBJECTSHAPEWRLDCRD_3_M_5_x = "envModelPort.staticObjects_3.objShape_m_5.x"
        STATICOBJECTSHAPEWRLDCRD_3_M_6_x = "envModelPort.staticObjects_3.objShape_m_6.x"
        STATICOBJECTSHAPEWRLDCRD_3_M_7_x = "envModelPort.staticObjects_3.objShape_m_7.x"
        STATICOBJECTSHAPEWRLDCRD_3_M_8_x = "envModelPort.staticObjects_3.objShape_m_8.x"
        STATICOBJECTSHAPEWRLDCRD_3_M_9_x = "envModelPort.staticObjects_3.objShape_m_9.x"
        STATICOBJECTSHAPEWRLDCRD_3_M_10_x = "envModelPort.staticObjects_3.objShape_m_10.x"
        STATICOBJECTSHAPEWRLDCRD_3_M_11_x = "envModelPort.staticObjects_3.objShape_m_11.x"
        STATICOBJECTSHAPEWRLDCRD_3_M_12_x = "envModelPort.staticObjects_3.objShape_m_12.x"
        STATICOBJECTSHAPEWRLDCRD_3_M_13_x = "envModelPort.staticObjects_3.objShape_m_13.x"
        STATICOBJECTSHAPEWRLDCRD_3_M_14_x = "envModelPort.staticObjects_3.objShape_m_14.x"
        STATICOBJECTSHAPEWRLDCRD_3_M_15_x = "envModelPort.staticObjects_3.objShape_m_15.x"

        STATICOBJECTSHAPEWRLDCRD_3_M_0_y = "envModelPort.staticObjects_3.objShape_m_0.y"
        STATICOBJECTSHAPEWRLDCRD_3_M_1_y = "envModelPort.staticObjects_3.objShape_m_1.y"
        STATICOBJECTSHAPEWRLDCRD_3_M_2_y = "envModelPort.staticObjects_3.objShape_m_2.y"
        STATICOBJECTSHAPEWRLDCRD_3_M_3_y = "envModelPort.staticObjects_3.objShape_m_3.y"
        STATICOBJECTSHAPEWRLDCRD_3_M_4_y = "envModelPort.staticObjects_3.objShape_m_4.y"
        STATICOBJECTSHAPEWRLDCRD_3_M_5_y = "envModelPort.staticObjects_3.objShape_m_5.y"
        STATICOBJECTSHAPEWRLDCRD_3_M_6_y = "envModelPort.staticObjects_3.objShape_m_6.y"
        STATICOBJECTSHAPEWRLDCRD_3_M_7_y = "envModelPort.staticObjects_3.objShape_m_7.y"
        STATICOBJECTSHAPEWRLDCRD_3_M_8_y = "envModelPort.staticObjects_3.objShape_m_8.y"
        STATICOBJECTSHAPEWRLDCRD_3_M_9_y = "envModelPort.staticObjects_3.objShape_m_9.y"
        STATICOBJECTSHAPEWRLDCRD_3_M_10_y = "envModelPort.staticObjects_3.objShape_m_10.y"
        STATICOBJECTSHAPEWRLDCRD_3_M_11_y = "envModelPort.staticObjects_3.objShape_m_11.y"
        STATICOBJECTSHAPEWRLDCRD_3_M_12_y = "envModelPort.staticObjects_3.objShape_m_12.y"
        STATICOBJECTSHAPEWRLDCRD_3_M_13_y = "envModelPort.staticObjects_3.objShape_m_13.y"
        STATICOBJECTSHAPEWRLDCRD_3_M_14_y = "envModelPort.staticObjects_3.objShape_m_14.y"
        STATICOBJECTSHAPEWRLDCRD_3_M_15_y = "envModelPort.staticObjects_3.objShape_m_15.y"

        ####
        STATICOBJECT_ACTUALSIZE_1 = "objShape_m.actualSize_1"
        STATICOBJECT_ACTUALSIZE_2 = "objShape_m.actualSize_2"
        STATICOBJECT_ACTUALSIZE_3 = "objShape_m.actualSize_3"

        GT_SLOT_COORDINATES_LIST = "GT_Slot_Coordinates_list_{}"
        GT_SLOT_P_X_0 = "gt_slot_p_x_0"
        GT_SLOT_P_Y_0 = "gt_slot_p_y_0"
        GT_SLOT_P_X_1 = "gt_slot_p_x_1"
        GT_SLOT_P_Y_1 = "gt_slot_p_y_1"
        GT_SLOT_P_X_2 = "gt_slot_p_x_2"
        GT_SLOT_P_Y_2 = "gt_slot_p_y_2"
        GT_SLOT_P_X_3 = "gt_slot_p_x_3"
        GT_SLOT_P_Y_3 = "gt_slot_p_y_3"

        GT_DELIMITER_0_X = "spaceMarkings_0.array_x"
        GT_DELIMITER_0_Y = "spaceMarkings_0.array_y"
        GT_DELIMITER_1_X = "spaceMarkings_1.array_x"
        GT_DELIMITER_1_Y = "spaceMarkings_1.array_y"
        GT_DELIMITER_2_X = "spaceMarkings_2.array_x"
        GT_DELIMITER_2_Y = "spaceMarkings_2.array_y"
        GT_DELIMITER_3_X = "spaceMarkings_3.array_x"
        GT_DELIMITER_3_Y = "spaceMarkings_3.array_y"
        GT_DELIMITER_4_X = "spaceMarkings_4.array_x"
        GT_DELIMITER_4_Y = "spaceMarkings_4.array_y"

        STATICOBJECT_HEIGHTCLASS = "objHeightClass_nu"
        #######
        DYNAMICOBJECTSHAPEWRLDCRD_0_0_x = "envModelPort.dynamicObjects_0.objShape_0.x"
        DYNAMICOBJECTSHAPEWRLDCRD_0_1_x = "envModelPort.dynamicObjects_0.objShape_1.x"
        DYNAMICOBJECTSHAPEWRLDCRD_0_2_x = "envModelPort.dynamicObjects_0.objShape_2.x"
        DYNAMICOBJECTSHAPEWRLDCRD_0_3_x = "envModelPort.dynamicObjects_0.objShape_3.x"
        DYNAMICOBJECTSHAPEWRLDCRD_0_0_y = "envModelPort.dynamicObjects_0.objShape_0.y"
        DYNAMICOBJECTSHAPEWRLDCRD_0_1_y = "envModelPort.dynamicObjects_0.objShape_1.y"
        DYNAMICOBJECTSHAPEWRLDCRD_0_2_y = "envModelPort.dynamicObjects_0.objShape_2.y"
        DYNAMICOBJECTSHAPEWRLDCRD_0_3_y = "envModelPort.dynamicObjects_0.objShape_3.y"

        DYNAMICOBJECTSHAPEWRLDCRD_1_0_x = "envModelPort.dynamicObjects_1.objShape_0.x"
        DYNAMICOBJECTSHAPEWRLDCRD_1_1_x = "envModelPort.dynamicObjects_1.objShape_1.x"
        DYNAMICOBJECTSHAPEWRLDCRD_1_2_x = "envModelPort.dynamicObjects_1.objShape_2.x"
        DYNAMICOBJECTSHAPEWRLDCRD_1_3_x = "envModelPort.dynamicObjects_1.objShape_3.x"
        DYNAMICOBJECTSHAPEWRLDCRD_1_0_y = "envModelPort.dynamicObjects_1.objShape_0.y"
        DYNAMICOBJECTSHAPEWRLDCRD_1_1_y = "envModelPort.dynamicObjects_1.objShape_1.y"
        DYNAMICOBJECTSHAPEWRLDCRD_1_2_y = "envModelPort.dynamicObjects_1.objShape_2.y"
        DYNAMICOBJECTSHAPEWRLDCRD_1_3_y = "envModelPort.dynamicObjects_1.objShape_3.y"
        #######
        DYNAMICOBJECTSHAPEWRLDCRD_2_0_x = "envModelPort.dynamicObjects_2.objShape_0.x"
        DYNAMICOBJECTSHAPEWRLDCRD_2_1_x = "envModelPort.dynamicObjects_2.objShape_1.x"
        DYNAMICOBJECTSHAPEWRLDCRD_2_2_x = "envModelPort.dynamicObjects_2.objShape_2.x"
        DYNAMICOBJECTSHAPEWRLDCRD_2_3_x = "envModelPort.dynamicObjects_2.objShape_3.x"

        DYNAMICOBJECTSHAPEWRLDCRD_2_0_y = "envModelPort.dynamicObjects_2.objShape_0.y"
        DYNAMICOBJECTSHAPEWRLDCRD_2_1_y = "envModelPort.dynamicObjects_2.objShape_1.y"
        DYNAMICOBJECTSHAPEWRLDCRD_2_2_y = "envModelPort.dynamicObjects_2.objShape_2.y"
        DYNAMICOBJECTSHAPEWRLDCRD_2_3_y = "envModelPort.dynamicObjects_2.objShape_3.y"
        DYNAMICOBJECTSHAPEWRLDCRD_3_0_x = "envModelPort.dynamicObjects_3.objShape_0.x"
        DYNAMICOBJECTSHAPEWRLDCRD_3_1_x = "envModelPort.dynamicObjects_3.objShape_1.x"
        DYNAMICOBJECTSHAPEWRLDCRD_3_2_x = "envModelPort.dynamicObjects_3.objShape_2.x"
        DYNAMICOBJECTSHAPEWRLDCRD_3_3_x = "envModelPort.dynamicObjects_3.objShape_3.x"
        DYNAMICOBJECTSHAPEWRLDCRD_3_0_y = "envModelPort.dynamicObjects_3.objShape_0.y"
        DYNAMICOBJECTSHAPEWRLDCRD_3_1_y = "envModelPort.dynamicObjects_3.objShape_1.y"
        DYNAMICOBJECTSHAPEWRLDCRD_3_2_y = "envModelPort.dynamicObjects_3.objShape_2.y"
        DYNAMICOBJECTSHAPEWRLDCRD_3_3_y = "envModelPort.dynamicObjects_3.objShape_3.y"

        NUMBERVALIDDYNAMICOBJECTS = "collEnvModelPort.numberOfDynamicObjects_u8"
        DYNAMICOBJECTSHAPE_0_M_0_x = "collEnvModelPort.dynamicObjects_0.objShape_m_0.x"
        DYNAMICOBJECTSHAPE_0_M_1_x = "collEnvModelPort.dynamicObjects_0.objShape_m_1.x"
        DYNAMICOBJECTSHAPE_0_M_2_x = "collEnvModelPort.dynamicObjects_0.objShape_m_2.x"
        DYNAMICOBJECTSHAPE_0_M_3_x = "collEnvModelPort.dynamicObjects_0.objShape_m_3.x"
        # DYNAMICOBJECTSHAPE_0_M_4_x = "collEnvModelPort.dynamicObjects_0.objShape_m_4.x"
        # DYNAMICOBJECTSHAPE_0_M_5_x = "collEnvModelPort.dynamicObjects_0.objShape_m_5.x"
        # DYNAMICOBJECTSHAPE_0_M_6_x = "collEnvModelPort.dynamicObjects_0.objShape_m_6.x"
        # DYNAMICOBJECTSHAPE_0_M_7_x = "collEnvModelPort.dynamicObjects_0.objShape_m_7.x"
        # DYNAMICOBJECTSHAPE_0_M_8_x = "collEnvModelPort.dynamicObjects_0.objShape_m_8.x"
        # DYNAMICOBJECTSHAPE_0_M_9_x = "collEnvModelPort.dynamicObjects_0.objShape_m_9.x"
        # DYNAMICOBJECTSHAPE_0_M_10_x = "collEnvModelPort.dynamicObjects_0.objShape_m_10.x"
        # DYNAMICOBJECTSHAPE_0_M_11_x = "collEnvModelPort.dynamicObjects_0.objShape_m_11.x"
        # DYNAMICOBJECTSHAPE_0_M_12_x = "collEnvModelPort.dynamicObjects_0.objShape_m_12.x"
        # DYNAMICOBJECTSHAPE_0_M_13_x = "collEnvModelPort.dynamicObjects_0.objShape_m_13.x"
        # DYNAMICOBJECTSHAPE_0_M_14_x = "collEnvModelPort.dynamicObjects_0.objShape_m_14.x"
        # DYNAMICOBJECTSHAPE_0_M_15_x = "collEnvModelPort.dynamicObjects_0.objShape_m_15.x"

        DYNAMICOBJECTSHAPE_0_M_0_y = "collEnvModelPort.dynamicObjects_0.objShape_m_0.y"
        DYNAMICOBJECTSHAPE_0_M_1_y = "collEnvModelPort.dynamicObjects_0.objShape_m_1.y"
        DYNAMICOBJECTSHAPE_0_M_2_y = "collEnvModelPort.dynamicObjects_0.objShape_m_2.y"
        DYNAMICOBJECTSHAPE_0_M_3_y = "collEnvModelPort.dynamicObjects_0.objShape_m_3.y"
        # DYNAMICOBJECTSHAPE_0_M_4_y = "collEnvModelPort.dynamicObjects_0.objShape_m_4.y"
        # DYNAMICOBJECTSHAPE_0_M_5_y = "collEnvModelPort.dynamicObjects_0.objShape_m_5.y"
        # DYNAMICOBJECTSHAPE_0_M_6_y = "collEnvModelPort.dynamicObjects_0.objShape_m_6.y"
        # DYNAMICOBJECTSHAPE_0_M_7_y = "collEnvModelPort.dynamicObjects_0.objShape_m_7.y"
        # DYNAMICOBJECTSHAPE_0_M_8_y = "collEnvModelPort.dynamicObjects_0.objShape_m_8.y"
        # DYNAMICOBJECTSHAPE_0_M_9_y = "collEnvModelPort.dynamicObjects_0.objShape_m_9.y"
        # DYNAMICOBJECTSHAPE_0_M_10_y = "collEnvModelPort.dynamicObjects_0.objShape_m_10.y"
        # DYNAMICOBJECTSHAPE_0_M_11_y = "collEnvModelPort.dynamicObjects_0.objShape_m_11.y"
        # DYNAMICOBJECTSHAPE_0_M_12_y = "collEnvModelPort.dynamicObjects_0.objShape_m_12.y"
        # DYNAMICOBJECTSHAPE_0_M_13_y = "collEnvModelPort.dynamicObjects_0.objShape_m_13.y"
        # DYNAMICOBJECTSHAPE_0_M_14_y = "collEnvModelPort.dynamicObjects_0.objShape_m_14.y"
        # DYNAMICOBJECTSHAPE_0_M_15_y = "collEnvModelPort.dynamicObjects_0.objShape_m_15.y"

        DYNAMICOBJECTSHAPE_1_M_0_x = "collEnvModelPort.dynamicObjects_1.objShape_m_0.x"
        DYNAMICOBJECTSHAPE_1_M_1_x = "collEnvModelPort.dynamicObjects_1.objShape_m_1.x"
        DYNAMICOBJECTSHAPE_1_M_2_x = "collEnvModelPort.dynamicObjects_1.objShape_m_2.x"
        DYNAMICOBJECTSHAPE_1_M_3_x = "collEnvModelPort.dynamicObjects_1.objShape_m_3.x"
        # DYNAMICOBJECTSHAPE_1_M_4_x = "collEnvModelPort.dynamicObjects_1.objShape_m_4.x"
        # DYNAMICOBJECTSHAPE_1_M_5_x = "collEnvModelPort.dynamicObjects_1.objShape_m_5.x"
        # DYNAMICOBJECTSHAPE_1_M_6_x = "collEnvModelPort.dynamicObjects_1.objShape_m_6.x"
        # DYNAMICOBJECTSHAPE_1_M_7_x = "collEnvModelPort.dynamicObjects_1.objShape_m_7.x"
        # DYNAMICOBJECTSHAPE_1_M_8_x = "collEnvModelPort.dynamicObjects_1.objShape_m_8.x"
        # DYNAMICOBJECTSHAPE_1_M_9_x = "collEnvModelPort.dynamicObjects_1.objShape_m_9.x"
        # DYNAMICOBJECTSHAPE_1_M_10_x = "collEnvModelPort.dynamicObjects_1.objShape_m_10.x"
        # DYNAMICOBJECTSHAPE_1_M_11_x = "collEnvModelPort.dynamicObjects_1.objShape_m_11.x"
        # DYNAMICOBJECTSHAPE_1_M_12_x = "collEnvModelPort.dynamicObjects_1.objShape_m_12.x"
        # DYNAMICOBJECTSHAPE_1_M_13_x = "collEnvModelPort.dynamicObjects_1.objShape_m_13.x"
        # DYNAMICOBJECTSHAPE_1_M_14_x = "collEnvModelPort.dynamicObjects_1.objShape_m_14.x"
        # DYNAMICOBJECTSHAPE_1_M_15_x = "collEnvModelPort.dynamicObjects_1.objShape_m_15.x"

        DYNAMICOBJECTSHAPE_1_M_0_y = "collEnvModelPort.dynamicObjects_1.objShape_m_0.y"
        DYNAMICOBJECTSHAPE_1_M_1_y = "collEnvModelPort.dynamicObjects_1.objShape_m_1.y"
        DYNAMICOBJECTSHAPE_1_M_2_y = "collEnvModelPort.dynamicObjects_1.objShape_m_2.y"
        DYNAMICOBJECTSHAPE_1_M_3_y = "collEnvModelPort.dynamicObjects_1.objShape_m_3.y"
        # DYNAMICOBJECTSHAPE_1_M_4_y = "collEnvModelPort.dynamicObjects_1.objShape_m_4.y"
        # DYNAMICOBJECTSHAPE_1_M_5_y = "collEnvModelPort.dynamicObjects_1.objShape_m_5.y"
        # DYNAMICOBJECTSHAPE_1_M_6_y = "collEnvModelPort.dynamicObjects_1.objShape_m_6.y"
        # DYNAMICOBJECTSHAPE_1_M_7_y = "collEnvModelPort.dynamicObjects_1.objShape_m_7.y"
        # DYNAMICOBJECTSHAPE_1_M_8_y = "collEnvModelPort.dynamicObjects_1.objShape_m_8.y"
        # DYNAMICOBJECTSHAPE_1_M_9_y = "collEnvModelPort.dynamicObjects_1.objShape_m_9.y"
        # DYNAMICOBJECTSHAPE_1_M_10_y = "collEnvModelPort.dynamicObjects_1.objShape_m_10.y"
        # DYNAMICOBJECTSHAPE_1_M_11_y = "collEnvModelPort.dynamicObjects_1.objShape_m_11.y"
        # DYNAMICOBJECTSHAPE_1_M_12_y = "collEnvModelPort.dynamicObjects_1.objShape_m_12.y"
        # DYNAMICOBJECTSHAPE_1_M_13_y = "collEnvModelPort.dynamicObjects_1.objShape_m_13.y"
        # DYNAMICOBJECTSHAPE_1_M_14_y = "collEnvModelPort.dynamicObjects_1.objShape_m_14.y"
        # DYNAMICOBJECTSHAPE_1_M_15_y = "collEnvModelPort.dynamicObjects_1.objShape_m_15.y"
        DYNAMICOBJECTSHAPE_2_M_0_y = "collEnvModelPort.dynamicObjects_2.objShape_m_0.y"
        DYNAMICOBJECTSHAPE_2_M_1_y = "collEnvModelPort.dynamicObjects_2.objShape_m_1.y"
        DYNAMICOBJECTSHAPE_2_M_2_y = "collEnvModelPort.dynamicObjects_2.objShape_m_2.y"
        DYNAMICOBJECTSHAPE_2_M_3_y = "collEnvModelPort.dynamicObjects_2.objShape_m_3.y"
        DYNAMICOBJECTSHAPE_3_M_0_y = "collEnvModelPort.dynamicObjects_3.objShape_m_0.y"
        DYNAMICOBJECTSHAPE_3_M_1_y = "collEnvModelPort.dynamicObjects_3.objShape_m_1.y"
        DYNAMICOBJECTSHAPE_3_M_2_y = "collEnvModelPort.dynamicObjects_3.objShape_m_2.y"
        DYNAMICOBJECTSHAPE_3_M_3_y = "collEnvModelPort.dynamicObjects_3.objShape_m_3.y"
        DYNAMICOBJECTSHAPE_2_M_0_x = "collEnvModelPort.dynamicObjects_2.objShape_m_0.x"
        DYNAMICOBJECTSHAPE_2_M_1_x = "collEnvModelPort.dynamicObjects_2.objShape_m_1.x"
        DYNAMICOBJECTSHAPE_2_M_2_x = "collEnvModelPort.dynamicObjects_2.objShape_m_2.x"
        DYNAMICOBJECTSHAPE_2_M_3_x = "collEnvModelPort.dynamicObjects_2.objShape_m_3.x"
        DYNAMICOBJECTSHAPE_3_M_0_x = "collEnvModelPort.dynamicObjects_3.objShape_m_0.x"
        DYNAMICOBJECTSHAPE_3_M_1_x = "collEnvModelPort.dynamicObjects_3.objShape_m_1.x"
        DYNAMICOBJECTSHAPE_3_M_2_x = "collEnvModelPort.dynamicObjects_3.objShape_m_2.x"
        DYNAMICOBJECTSHAPE_3_M_3_x = "collEnvModelPort.dynamicObjects_3.objShape_m_3.x"

        NUMBERPARKINGMARKINGS = "envModelPort.numberOfParkMarkings_u8"
        EGOVEHICLEPOSEFORAP_X = "envModelPort.egoVehiclePoseForAP.pos_x_m"
        EGOVEHICLEPOSEFORAP_Y = "envModelPort.egoVehiclePoseForAP.pos_y_m"
        ODOESTIMATEPOSEFORAP_X = "AP.odoEstimationPort.xPosition_m"
        ODOESTIMATEPOSEFORAP_Y = "AP.odoEstimationPort.yPosition_m"
        RESETCOUNTER = "AP.resetOriginRequestPort.resetCounter_nu"
        RESETORIGIN = "AP.resetOriginRequestPort.resetOrigin_nu"
        GT_ENV_NUMBEROFSTATICOBJECTS = "GT.envModelPort.numberOfStaticObjects_u8"
        AP_COLLENV_NUMBEROFSTATICOBJECTS = "AP.collEnvModelPort.numberOfStaticObjects_u8"
        AP_ENV_NUMBEROFSTATICOBJECTS = "AP.envModelPort.numberOfStaticObjects_u8"
        STATICOBJECT_REFOBJID = "GT.envModelPort.staticObjects._0_.refObjID_nu"
        STATICOBJECT_EXISTENCEPROB_PERC = "GT.envModelPort.staticObjects._0_.existenceProb_perc"
        STATICOBJECT_OBJHEIGHTCLASS = "GT.envModelPort.staticObjects._0_.objHeightClass_nu"
        PARKINGSPACEMARKINGS_0_0_x = "envModelPort.parkingSpaceMarkings_0_0.x"
        PARKINGSPACEMARKINGS_0_0_y = "envModelPort.parkingSpaceMarkings_0_0.y"
        PARKINGSPACEMARKINGS_0_1_x = "envModelPort.parkingSpaceMarkings_0_1.x"
        PARKINGSPACEMARKINGS_0_1_y = "envModelPort.parkingSpaceMarkings_0_1.y"
        PARKINGSPACEMARKINGS_1_0_x = "envModelPort.parkingSpaceMarkings_1_0.x"
        PARKINGSPACEMARKINGS_1_0_y = "envModelPort.parkingSpaceMarkings_1_0.y"
        PARKINGSPACEMARKINGS_1_1_x = "envModelPort.parkingSpaceMarkings_1_1.x"
        PARKINGSPACEMARKINGS_1_1_y = "envModelPort.parkingSpaceMarkings_1_1.y"
        PARKINGSPACEMARKINGS_2_0_x = "envModelPort.parkingSpaceMarkings_2_0.x"
        PARKINGSPACEMARKINGS_2_0_y = "envModelPort.parkingSpaceMarkings_2_0.y"
        PARKINGSPACEMARKINGS_2_1_x = "envModelPort.parkingSpaceMarkings_2_1.x"
        PARKINGSPACEMARKINGS_2_1_y = "envModelPort.parkingSpaceMarkings_2_1.y"
        PARKINGSPACEMARKINGS_3_0_x = "envModelPort.parkingSpaceMarkings_3_0.x"
        PARKINGSPACEMARKINGS_3_0_y = "envModelPort.parkingSpaceMarkings_3_0.y"
        PARKINGSPACEMARKINGS_3_1_x = "envModelPort.parkingSpaceMarkings_3_1.x"
        PARKINGSPACEMARKINGS_3_1_y = "envModelPort.parkingSpaceMarkings_3_1.y"
        PARKINGSPACEMARKINGS_4_0_x = "envModelPort.parkingSpaceMarkings_4_0.x"
        PARKINGSPACEMARKINGS_4_0_y = "envModelPort.parkingSpaceMarkings_4_0.y"
        PARKINGSPACEMARKINGS_4_1_x = "envModelPort.parkingSpaceMarkings_4_1.x"
        PARKINGSPACEMARKINGS_4_1_y = "envModelPort.parkingSpaceMarkings_4_1.y"
        PARKINGSPACEMARKINGS_5_0_x = "envModelPort.parkingSpaceMarkings_5_0.x"
        PARKINGSPACEMARKINGS_5_0_y = "envModelPort.parkingSpaceMarkings_5_0.y"
        PARKINGSPACEMARKINGS_5_1_x = "envModelPort.parkingSpaceMarkings_5_1.x"
        PARKINGSPACEMARKINGS_5_1_y = "envModelPort.parkingSpaceMarkings_5_1.y"
        PARKINGSPACEMARKINGS_6_0_x = "envModelPort.parkingSpaceMarkings_6_0.x"
        PARKINGSPACEMARKINGS_6_0_y = "envModelPort.parkingSpaceMarkings_6_0.y"
        PARKINGSPACEMARKINGS_6_1_x = "envModelPort.parkingSpaceMarkings_6_1.x"
        PARKINGSPACEMARKINGS_6_1_y = "envModelPort.parkingSpaceMarkings_6_1.y"
        PARKINGSPACEMARKINGS_7_0_x = "envModelPort.parkingSpaceMarkings_7_0.x"
        PARKINGSPACEMARKINGS_7_0_y = "envModelPort.parkingSpaceMarkings_7_0.y"
        PARKINGSPACEMARKINGS_7_1_x = "envModelPort.parkingSpaceMarkings_7_1.x"
        PARKINGSPACEMARKINGS_7_1_y = "envModelPort.parkingSpaceMarkings_7_1.y"
        PARKINGSPACEMARKINGS_8_0_x = "envModelPort.parkingSpaceMarkings_8_0.x"
        PARKINGSPACEMARKINGS_8_0_y = "envModelPort.parkingSpaceMarkings_8_0.y"
        PARKINGSPACEMARKINGS_8_1_x = "envModelPort.parkingSpaceMarkings_8_1.x"
        PARKINGSPACEMARKINGS_8_1_y = "envModelPort.parkingSpaceMarkings_8_1.y"
        PARKINGSPACEMARKINGS_9_0_x = "envModelPort.parkingSpaceMarkings_9_0.x"
        PARKINGSPACEMARKINGS_9_0_y = "envModelPort.parkingSpaceMarkings_9_0.y"
        PARKINGSPACEMARKINGS_9_1_x = "envModelPort.parkingSpaceMarkings_9_1.x"
        PARKINGSPACEMARKINGS_9_1_y = "envModelPort.parkingSpaceMarkings_9_1.y"
        PARKINGSPACEMARKINGS_10_0_x = "envModelPort.parkingSpaceMarkings_10_0.x"
        PARKINGSPACEMARKINGS_10_0_y = "envModelPort.parkingSpaceMarkings_10_0.y"
        PARKINGSPACEMARKINGS_10_1_x = "envModelPort.parkingSpaceMarkings_10_1.x"
        PARKINGSPACEMARKINGS_10_1_y = "envModelPort.parkingSpaceMarkings_10_1.y"
        PARKINGSPACEMARKINGS_11_0_x = "envModelPort.parkingSpaceMarkings_11_0.x"
        PARKINGSPACEMARKINGS_11_0_y = "envModelPort.parkingSpaceMarkings_11_0.y"
        PARKINGSPACEMARKINGS_11_1_x = "envModelPort.parkingSpaceMarkings_11_1.x"
        PARKINGSPACEMARKINGS_11_1_y = "envModelPort.parkingSpaceMarkings_11_1.y"
        PARKINGSPACEMARKINGS_12_0_x = "envModelPort.parkingSpaceMarkings_12_0.x"
        PARKINGSPACEMARKINGS_12_0_y = "envModelPort.parkingSpaceMarkings_12_0.y"
        PARKINGSPACEMARKINGS_12_1_x = "envModelPort.parkingSpaceMarkings_12_1.x"
        PARKINGSPACEMARKINGS_12_1_y = "envModelPort.parkingSpaceMarkings_12_1.y"
        PARKINGSPACEMARKINGS_13_0_x = "envModelPort.parkingSpaceMarkings_13_0.x"
        PARKINGSPACEMARKINGS_13_0_y = "envModelPort.parkingSpaceMarkings_13_0.y"
        PARKINGSPACEMARKINGS_13_1_x = "envModelPort.parkingSpaceMarkings_13_1.x"
        PARKINGSPACEMARKINGS_13_1_y = "envModelPort.parkingSpaceMarkings_13_1.y"
        PARKINGSPACEMARKINGS_14_0_x = "envModelPort.parkingSpaceMarkings_14_0.x"
        PARKINGSPACEMARKINGS_14_0_y = "envModelPort.parkingSpaceMarkings_14_0.y"
        PARKINGSPACEMARKINGS_14_1_x = "envModelPort.parkingSpaceMarkings_14_1.x"
        PARKINGSPACEMARKINGS_14_1_y = "envModelPort.parkingSpaceMarkings_14_1.y"
        PARKINGSPACEMARKINGS_15_0_x = "envModelPort.parkingSpaceMarkings_15_0.x"
        PARKINGSPACEMARKINGS_15_0_y = "envModelPort.parkingSpaceMarkings_15_0.y"
        PARKINGSPACEMARKINGS_15_1_x = "envModelPort.parkingSpaceMarkings_15_1.x"
        PARKINGSPACEMARKINGS_15_1_y = "envModelPort.parkingSpaceMarkings_15_1.y"
        # SGFOUTPUT_STATICOBJECTVERTICESOUTPUT_0_X = "sgfOutput.staticObjectVerticesOutput.vertices"
        GT_MODSLOTS_SLOT_CORNERS_0_x = "mODSlots.slot_corners._0_.x"
        GT_MODSLOTS_SLOT_CORNERS_0_y = "mODSlots.slot_corners._0_.y"
        GT_MODSLOTS_SLOT_CORNERS_1_x = "mODSlots.slot_corners._1_.x"
        GT_MODSLOTS_SLOT_CORNERS_1_y = "mODSlots.slot_corners._1_.y"
        GT_MODSLOTS_SLOT_CORNERS_2_x = "mODSlots.slot_corners._2_.x"
        GT_MODSLOTS_SLOT_CORNERS_2_y = "mODSlots.slot_corners._2_.y"
        GT_MODSLOTS_SLOT_CORNERS_3_x = "mODSlots.slot_corners._3_.x"
        GT_MODSLOTS_SLOT_CORNERS_3_y = "mODSlots.slot_corners._3_.y"
        ###
        # PARKINGSLOTDETECTIONOUTPUT_SLOTCORNERS_0_X = "parkingSlotDetectionOutput.parkingSlots.slotCorners._0_.x"
        # PARKINGSLOTDETECTIONOUTPUT_SLOTCORNERS_0_Y = "parkingSlotDetectionOutput.parkingSlots.slotCorners._0_.y"
        # PARKINGSLOTDETECTIONOUTPUT_SLOTCORNERS_1_X = "parkingSlotDetectionOutput.parkingSlots.slotCorners._1_.x"
        # PARKINGSLOTDETECTIONOUTPUT_SLOTCORNERS_1_Y = "parkingSlotDetectionOutput.parkingSlots.slotCorners._1_.y"
        # PARKINGSLOTDETECTIONOUTPUT_SLOTCORNERS_2_X = "parkingSlotDetectionOutput.parkingSlots.slotCorners._2_.x"
        # PARKINGSLOTDETECTIONOUTPUT_SLOTCORNERS_2_Y = "parkingSlotDetectionOutput.parkingSlots.slotCorners._2_.y"
        # PARKINGSLOTDETECTIONOUTPUT_SLOTCORNERS_3_X = "parkingSlotDetectionOutput.parkingSlots.slotCorners._3_.x"
        # PARKINGSLOTDETECTIONOUTPUT_SLOTCORNERS_3_Y = "parkingSlotDetectionOutput.parkingSlots.slotCorners._3_.y"

        ####
        CNNBASEDPARKINGSPACES_PARKINGSLOTS_0_SLOTCORNERS_0_X = (
            "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_0.x"
        )
        CNNBASEDPARKINGSPACES_PARKINGSLOTS_0_SLOTCORNERS_0_Y = (
            "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_0.y"
        )
        CNNBASEDPARKINGSPACES_PARKINGSLOTS_0_SLOTCORNERS_1_X = (
            "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_1.x"
        )
        CNNBASEDPARKINGSPACES_PARKINGSLOTS_0_SLOTCORNERS_1_Y = (
            "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_1.y"
        )
        CNNBASEDPARKINGSPACES_PARKINGSLOTS_0_SLOTCORNERS_2_X = (
            "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_2.x"
        )
        CNNBASEDPARKINGSPACES_PARKINGSLOTS_0_SLOTCORNERS_2_Y = (
            "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_2.y"
        )
        CNNBASEDPARKINGSPACES_PARKINGSLOTS_0_SLOTCORNERS_3_X = (
            "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_3.x"
        )
        CNNBASEDPARKINGSPACES_PARKINGSLOTS_0_SLOTCORNERS_3_Y = (
            "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_3.y"
        )

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]

        self._properties = {
            "ap_cycle": "AP.envModelPort.sSigHeader.uiCycleCounter",
            self.Columns.TIME: "Time",
            self.Columns.EGO_POS_X: ".envModelPort.egoVehiclePoseForAP.pos_x_m",
            self.Columns.EGO_POS_Y: ".envModelPort.egoVehiclePoseForAP.pos_y_m",
            self.Columns.EGO_POS_YAW: ".envModelPort.egoVehiclePoseForAP.yaw_rad",
            self.Columns.AP_STATE: ".planningCtrlPort.apStates",
            self.Columns.VELOCITY: "Vhcl.v",
            self.Columns.NUMBEROFDELIMITERS: ["pclOutput.numberOfDelimiters"],
            self.Columns.DELIMITERID: ["pclOutput.delimiters._%_.delimiterId"],
            self.Columns.NUMVALIDPARKINGBOXES_NU: [".parkingBoxPort.numValidParkingBoxes_nu"],
            # self.Columns.PARKINGBOXES: [".parkingBoxPort.parkingBoxes_%"],
            self.Columns.NUMBEROFVERTICES: [
                "SgfOutput.staticObjectsOutput.staticObjectVerticesOutput.numberOfVertices"
            ],
            self.Columns.VERTICES_X: ["sgfOutput.staticObjectVerticesOutput.vertices._%_.x"],
            self.Columns.VERTICES_Y: ["sgfOutput.staticObjectVerticesOutput.vertices._%_.y"],
            self.Columns.NUMBEROFOBJECTS: ["sgfOutput.staticObjectsOutput.numberOfObjects"],
            self.Columns.HEIGHTCONFIDENCE_BODYTRAVERSABLE: [
                "sgfOutput.staticObjectsOutput.objects._%_.heightConfidences.bodyTraversable"
            ],
            self.Columns.HEIGHTCONFIDENCE_HANGING: [
                "sgfOutput.staticObjectsOutput.objects._%_.heightConfidences.hanging"
            ],
            self.Columns.HEIGHTCONFIDENCE_HIGH: ["sgfOutput.staticObjectsOutput.objects._%_.heightConfidences.high"],
            self.Columns.HEIGHTCONFIDENCE_WHEELTRAVERSALE: [
                "sgfOutput.staticObjectsOutput.objects._%_.heightConfidences.wheelTraversable"
            ],
            # self.Columns.SLOTCOORDINATES_FRONTLEFT_X : [".parkingBoxPort.parkingBoxes_%.slotCoordinates_FrontLeft_x"],
            # self.Columns.SLOTCOORDINATES_FRONTLEFT_Y : [".parkingBoxPort.parkingBoxes_%.slotCoordinates_FrontLeft_y"],
            # self.Columns.SLOTCOORDINATES_FRONTRIGHT_X : [".parkingBoxPort.parkingBoxes_%.slotCoordinates_FrontRight_x"],
            # self.Columns.SLOTCOORDINATES_FRONTRIGHT_Y : [".parkingBoxPort.parkingBoxes_%.slotCoordinates_FrontRight_y"],
            # self.Columns.SLOTCOORDINATES_REARLEFT_X : [".parkingBoxPort.parkingBoxes_%.slotCoordinates_RearLeft_x"],
            # self.Columns.SLOTCOORDINATES_REARLEFT_Y : [".parkingBoxPort.parkingBoxes_%.slotCoordinates_RearLeft_y"],
            # self.Columns.SLOTCOORDINATES_REARRIGHT_X : [".parkingBoxPort.parkingBoxes_%.slotCoordinates_RearRight_x"],
            # self.Columns.SLOTCOORDINATES_REARRIGHT_Y : [".parkingBoxPort.parkingBoxes_%.slotCoordinates_RearRight_y"],
            # self.Columns.activateLoCtrl : [".loCtrlRequestPort.activateLoCtrl"],
            # self.Columns.laCtrlRequestType : [".laCtrlRequestPort.laCtrlRequestType"],
            self.Columns.DELIMITERS_ENDPOINTXPOSITION: ["pclOutput.delimiters._%_.endPointXPosition"],
            self.Columns.DELIMITERS_ENDPOINTYPOSITION: ["pclOutput.delimiters._%_.endPointYPosition"],
            self.Columns.DELIMITERS_STARTPOINTXPOSITION: ["pclOutput.delimiters._%_.startPointXPosition"],
            self.Columns.DELIMITERS_STARTPOINTYPOSITION: ["pclOutput.delimiters._%_.startPointYPosition"],
            self.Columns.parkingBoxID_nu: [".parkingBoxPort.parkingBoxes_0.parkingBoxID_nu"],
            self.Columns.parkingBoxID_nu1: [".parkingBoxPort.parkingBoxes_1.parkingBoxID_nu"],
            self.Columns.parkingBoxID_nu2: [".parkingBoxPort.parkingBoxes_2.parkingBoxID_nu"],
            self.Columns.parkingBoxID_nu3: [".parkingBoxPort.parkingBoxes_3.parkingBoxID_nu"],
            self.Columns.parkingBoxID_nu4: [".parkingBoxPort.parkingBoxes_4.parkingBoxID_nu"],
            self.Columns.parkingBoxID_nu5: [".parkingBoxPort.parkingBoxes_5.parkingBoxID_nu"],
            self.Columns.parkingBoxID_nu6: [".parkingBoxPort.parkingBoxes_6.parkingBoxID_nu"],
            self.Columns.parkingBoxID_nu7: [".parkingBoxPort.parkingBoxes_7.parkingBoxID_nu"],
            self.Columns.PARKING_SCENARIO_0: [".parkingBoxPort.parkingBoxes_0.parkingScenario_nu"],
            self.Columns.PARKING_SCENARIO_1: [".parkingBoxPort.parkingBoxes_1.parkingScenario_nu"],
            self.Columns.PARKING_SCENARIO_2: [".parkingBoxPort.parkingBoxes_2.parkingScenario_nu"],
            self.Columns.PARKING_SCENARIO_3: [".parkingBoxPort.parkingBoxes_3.parkingScenario_nu"],
            self.Columns.PARKING_SCENARIO_4: [".parkingBoxPort.parkingBoxes_4.parkingScenario_nu"],
            self.Columns.PARKING_SCENARIO_5: [".parkingBoxPort.parkingBoxes_5.parkingScenario_nu"],
            self.Columns.PARKING_SCENARIO_6: [".parkingBoxPort.parkingBoxes_6.parkingScenario_nu"],
            self.Columns.PARKING_SCENARIO_7: [".parkingBoxPort.parkingBoxes_7.parkingScenario_nu"],
            self.Columns.PB_SLOTCORDINATES_FRONTLEFT_X_0: [
                ".parkingBoxPort.parkingBoxes_0.slotCoordinates_FrontLeft_x"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTLEFT_Y_0: [
                ".parkingBoxPort.parkingBoxes_0.slotCoordinates_FrontLeft_y"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTRIGHT_X_0: [
                ".parkingBoxPort.parkingBoxes_0.slotCoordinates_FrontRight_x"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTRIGHT_Y_0: [
                ".parkingBoxPort.parkingBoxes_0.slotCoordinates_FrontRight_y"
            ],
            self.Columns.PB_SLOTCORDINATES_REARLEFT_X_0: [".parkingBoxPort.parkingBoxes_0.slotCoordinates_RearLeft_x"],
            self.Columns.PB_SLOTCORDINATES_REARLEFT_Y_0: [".parkingBoxPort.parkingBoxes_0.slotCoordinates_RearLeft_y"],
            self.Columns.PB_SLOTCORDINATES_REARRIGHT_X_0: [
                ".parkingBoxPort.parkingBoxes_0.slotCoordinates_RearRight_x"
            ],
            self.Columns.PB_SLOTCORDINATES_REARRIGHT_Y_0: [
                ".parkingBoxPort.parkingBoxes_0.slotCoordinates_RearRight_y"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTLEFT_X_1: [
                ".parkingBoxPort.parkingBoxes_1.slotCoordinates_FrontLeft_x"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTLEFT_Y_1: [
                ".parkingBoxPort.parkingBoxes_1.slotCoordinates_FrontLeft_y"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTRIGHT_X_1: [
                ".parkingBoxPort.parkingBoxes_1.slotCoordinates_FrontRight_x"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTRIGHT_Y_1: [
                ".parkingBoxPort.parkingBoxes_1.slotCoordinates_FrontRight_y"
            ],
            self.Columns.PB_SLOTCORDINATES_REARLEFT_X_1: [".parkingBoxPort.parkingBoxes_1.slotCoordinates_RearLeft_x"],
            self.Columns.PB_SLOTCORDINATES_REARLEFT_Y_1: [".parkingBoxPort.parkingBoxes_1.slotCoordinates_RearLeft_y"],
            self.Columns.PB_SLOTCORDINATES_REARRIGHT_X_1: [
                ".parkingBoxPort.parkingBoxes_1.slotCoordinates_RearRight_x"
            ],
            self.Columns.PB_SLOTCORDINATES_REARRIGHT_Y_1: [
                ".parkingBoxPort.parkingBoxes_1.slotCoordinates_RearRight_y"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTLEFT_X_2: [
                ".parkingBoxPort.parkingBoxes_2.slotCoordinates_FrontLeft_x"
            ],  # GT.envModelPort.staticObjects._60_.objShape_m.array._0_.x_dir
            self.Columns.PB_SLOTCORDINATES_FRONTLEFT_Y_2: [
                ".parkingBoxPort.parkingBoxes_2.slotCoordinates_FrontLeft_y"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTRIGHT_X_2: [
                ".parkingBoxPort.parkingBoxes_2.slotCoordinates_FrontRight_x"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTRIGHT_Y_2: [
                ".parkingBoxPort.parkingBoxes_2.slotCoordinates_FrontRight_y"
            ],
            self.Columns.PB_SLOTCORDINATES_REARLEFT_X_2: [".parkingBoxPort.parkingBoxes_2.slotCoordinates_RearLeft_x"],
            self.Columns.PB_SLOTCORDINATES_REARLEFT_Y_2: [".parkingBoxPort.parkingBoxes_2.slotCoordinates_RearLeft_y"],
            self.Columns.PB_SLOTCORDINATES_REARRIGHT_X_2: [
                ".parkingBoxPort.parkingBoxes_2.slotCoordinates_RearRight_x"
            ],
            self.Columns.PB_SLOTCORDINATES_REARRIGHT_Y_2: [
                ".parkingBoxPort.parkingBoxes_2.slotCoordinates_RearRight_y"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTLEFT_X_3: [
                ".parkingBoxPort.parkingBoxes_3.slotCoordinates_FrontLeft_x"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTLEFT_Y_3: [
                ".parkingBoxPort.parkingBoxes_3.slotCoordinates_FrontLeft_y"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTRIGHT_X_3: [
                ".parkingBoxPort.parkingBoxes_3.slotCoordinates_FrontRight_x"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTRIGHT_Y_3: [
                ".parkingBoxPort.parkingBoxes_3.slotCoordinates_FrontRight_y"
            ],
            self.Columns.PB_SLOTCORDINATES_REARLEFT_X_3: [".parkingBoxPort.parkingBoxes_3.slotCoordinates_RearLeft_x"],
            self.Columns.PB_SLOTCORDINATES_REARLEFT_Y_3: [".parkingBoxPort.parkingBoxes_3.slotCoordinates_RearLeft_y"],
            self.Columns.PB_SLOTCORDINATES_REARRIGHT_X_3: [
                ".parkingBoxPort.parkingBoxes_3.slotCoordinates_RearRight_x"
            ],
            self.Columns.PB_SLOTCORDINATES_REARRIGHT_Y_3: [
                ".parkingBoxPort.parkingBoxes_3.slotCoordinates_RearRight_y"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTLEFT_X_4: [
                ".parkingBoxPort.parkingBoxes_4.slotCoordinates_FrontLeft_x"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTLEFT_Y_4: [
                ".parkingBoxPort.parkingBoxes_4.slotCoordinates_FrontLeft_y"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTRIGHT_X_4: [
                ".parkingBoxPort.parkingBoxes_4.slotCoordinates_FrontRight_x"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTRIGHT_Y_4: [
                ".parkingBoxPort.parkingBoxes_4.slotCoordinates_FrontRight_y"
            ],
            self.Columns.PB_SLOTCORDINATES_REARLEFT_X_4: [".parkingBoxPort.parkingBoxes_4.slotCoordinates_RearLeft_x"],
            self.Columns.PB_SLOTCORDINATES_REARLEFT_Y_4: [".parkingBoxPort.parkingBoxes_4.slotCoordinates_RearLeft_y"],
            self.Columns.PB_SLOTCORDINATES_REARRIGHT_X_4: [
                ".parkingBoxPort.parkingBoxes_4.slotCoordinates_RearRight_x"
            ],
            self.Columns.PB_SLOTCORDINATES_REARRIGHT_Y_4: [
                ".parkingBoxPort.parkingBoxes_4.slotCoordinates_RearRight_y"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTLEFT_X_5: [
                ".parkingBoxPort.parkingBoxes_5.slotCoordinates_FrontLeft_x"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTLEFT_Y_5: [
                ".parkingBoxPort.parkingBoxes_5.slotCoordinates_FrontLeft_y"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTRIGHT_X_5: [
                ".parkingBoxPort.parkingBoxes_5.slotCoordinates_FrontRight_x"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTRIGHT_Y_5: [
                ".parkingBoxPort.parkingBoxes_5.slotCoordinates_FrontRight_y"
            ],
            self.Columns.PB_SLOTCORDINATES_REARLEFT_X_5: [".parkingBoxPort.parkingBoxes_5.slotCoordinates_RearLeft_x"],
            self.Columns.PB_SLOTCORDINATES_REARLEFT_Y_5: [".parkingBoxPort.parkingBoxes_5.slotCoordinates_RearLeft_y"],
            self.Columns.PB_SLOTCORDINATES_REARRIGHT_X_5: [
                ".parkingBoxPort.parkingBoxes_5.slotCoordinates_RearRight_x"
            ],
            self.Columns.PB_SLOTCORDINATES_REARRIGHT_Y_5: [
                ".parkingBoxPort.parkingBoxes_5.slotCoordinates_RearRight_y"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTLEFT_X_6: [
                ".parkingBoxPort.parkingBoxes_6.slotCoordinates_FrontLeft_x"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTLEFT_Y_6: [
                ".parkingBoxPort.parkingBoxes_6.slotCoordinates_FrontLeft_y"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTRIGHT_X_6: [
                ".parkingBoxPort.parkingBoxes_6.slotCoordinates_FrontRight_x"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTRIGHT_Y_6: [
                ".parkingBoxPort.parkingBoxes_6.slotCoordinates_FrontRight_y"
            ],
            self.Columns.PB_SLOTCORDINATES_REARLEFT_X_6: [".parkingBoxPort.parkingBoxes_6.slotCoordinates_RearLeft_x"],
            self.Columns.PB_SLOTCORDINATES_REARLEFT_Y_6: [".parkingBoxPort.parkingBoxes_6.slotCoordinates_RearLeft_y"],
            self.Columns.PB_SLOTCORDINATES_REARRIGHT_X_6: [
                ".parkingBoxPort.parkingBoxes_6.slotCoordinates_RearRight_x"
            ],
            self.Columns.PB_SLOTCORDINATES_REARRIGHT_Y_6: [
                ".parkingBoxPort.parkingBoxes_6.slotCoordinates_RearRight_y"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTLEFT_X_7: [
                ".parkingBoxPort.parkingBoxes_7.slotCoordinates_FrontLeft_x"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTLEFT_Y_7: [
                ".parkingBoxPort.parkingBoxes_7.slotCoordinates_FrontLeft_y"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTRIGHT_X_7: [
                ".parkingBoxPort.parkingBoxes_7.slotCoordinates_FrontRight_x"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTRIGHT_Y_7: [
                ".parkingBoxPort.parkingBoxes_7.slotCoordinates_FrontRight_y"
            ],
            self.Columns.PB_SLOTCORDINATES_REARLEFT_X_7: [".parkingBoxPort.parkingBoxes_7.slotCoordinates_RearLeft_x"],
            self.Columns.PB_SLOTCORDINATES_REARLEFT_Y_7: [".parkingBoxPort.parkingBoxes_7.slotCoordinates_RearLeft_y"],
            self.Columns.PB_SLOTCORDINATES_REARRIGHT_X_7: [
                ".parkingBoxPort.parkingBoxes_7.slotCoordinates_RearRight_x"
            ],
            self.Columns.PB_SLOTCORDINATES_REARRIGHT_Y_7: [
                ".parkingBoxPort.parkingBoxes_7.slotCoordinates_RearRight_y"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTLEFT_X_8: [
                ".parkingBoxPort.parkingBoxes_8.slotCoordinates_FrontLeft_x"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTLEFT_Y_8: [
                ".parkingBoxPort.parkingBoxes_8.slotCoordinates_FrontLeft_y"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTRIGHT_X_8: [
                ".parkingBoxPort.parkingBoxes_8.slotCoordinates_FrontRight_x"
            ],
            self.Columns.PB_SLOTCORDINATES_FRONTRIGHT_Y_8: [
                ".parkingBoxPort.parkingBoxes_8.slotCoordinates_FrontRight_y"
            ],
            self.Columns.PB_SLOTCORDINATES_REARLEFT_X_8: [".parkingBoxPort.parkingBoxes_8.slotCoordinates_RearLeft_x"],
            self.Columns.PB_SLOTCORDINATES_REARLEFT_Y_8: [".parkingBoxPort.parkingBoxes_8.slotCoordinates_RearLeft_y"],
            self.Columns.PB_SLOTCORDINATES_REARRIGHT_X_8: [
                ".parkingBoxPort.parkingBoxes_8.slotCoordinates_RearRight_x"
            ],
            self.Columns.PB_SLOTCORDINATES_REARRIGHT_Y_8: [
                ".parkingBoxPort.parkingBoxes_8.slotCoordinates_RearRight_y"
            ],
            self.Columns.STATICOBJECT_NUMBEROFVERTICES: ["sgfOutput.staticObjectVerticesOutput.numberOfVertices"],
            self.Columns.STATICOBJECT_VERTICES_X: ["sgfOutput.staticObjectVerticesOutput.vertices._%_.x"],
            self.Columns.STATICOBJECT_VERTICES_Y: ["sgfOutput.staticObjectVerticesOutput.vertices._%_.y"],
            # self.Columns.STATICOBJECT_NUMBEROFOBJECTS : ["SgfOutput.staticObjectsOutput.numberOfObjects"],
            self.Columns.STATICOBJECT_OBJECTSEMENTICTYPE: ["sgfOutput.staticObjectsOutput.objects._%_.semanticType"],
            self.Columns.STATICOBJECT_OBJECTUSEDVERTICES: ["sgfOutput.staticObjectsOutput.objects._%_.usedVertices"],
            self.Columns.ENVMODELPORTNUMBEROFSTATICOBJECT: ["GT.envModelPort.numberOfStaticObjects_u8"],
            self.Columns.ENVMODELPORTEGOVEHICLEPOSEFORAP_X_M: [".envModelPort.egoVehiclePoseForAP.pos_x_m"],
            self.Columns.ENVMODELPORTEGOVEHICLEPOSEFORAP_Y_M: [".envModelPort.egoVehiclePoseForAP.pos_y_m"],
            self.Columns.ENVMODELPORTSTATICOBJECTSHAPE_M_0_X: ["AP.envModelPort.staticObjects_0.objShape_m_0.x"],
            self.Columns.ENVMODELPORTSTATICOBJECTSHAPE_M_0_Y: ["AP.envModelPort.staticObjects_0.objShape_m_0.y"],
            self.Columns.ENVMODELPORTSTATICOBJECTSHAPE_1_M_0_X: ["AP.envModelPort.staticObjects_1.objShape_m_0.x"],
            self.Columns.ENVMODELPORTSTATICOBJECTSHAPE_1_M_0_Y: ["AP.envModelPort.staticObjects_1.objShape_m_0.y"],
            self.Columns.ENVMODELPORTDYNAMICOBJECTSHAPE_0_X: ["AP.envModelPort.dynamicObjects_0.objShape_0.x"],
            self.Columns.ENVMODELPORTDYNAMICOBJECTSHAPE_0_Y: ["AP.envModelPort.dynamicObjects_0.objShape_0.y"],
            self.Columns.ENVMODELPORTDYNAMICOBJECTSHAPE_1_X: ["AP.envModelPort.dynamicObjects_0.objShape_1.x"],
            self.Columns.ENVMODELPORTDYNAMICOBJECTSHAPE_1_Y: ["AP.envModelPort.dynamicObjects_0.objShape_1.y"],
            self.Columns.COLLENVMODELPORTSTATICOBJECTSHAPE_M_0_X: [
                "AP.collEnvModelPort.staticObjects_0.objShape_m_0.x"
            ],
            self.Columns.COLLENVMODELPORTSTATICOBJECTSHAPE_M_0_Y: [
                "AP.collEnvModelPort.staticObjects_0.objShape_m_0.y"
            ],
            self.Columns.COLLENVMODELPORTSTATICOBJECTSHAPE_1_M_0_X: [
                "AP.collEnvModelPort.staticObjects_1.objShape_m_1.x"
            ],
            self.Columns.COLLENVMODELPORTSTATICOBJECTSHAPE_1_M_0_Y: [
                "AP.collEnvModelPort.staticObjects_1.objShape_m_1.y"
            ],
            self.Columns.COLLENVMODELPORTDYNAMICOBJECTSHAPE_M_0_X: [
                "AP.collEnvModelPort.dynamicObjects_0.objShape_m_0.x"
            ],
            self.Columns.COLLENVMODELPORTDYNAMICOBJECTSHAPE_M_0_Y: [
                "AP.collEnvModelPort.dynamicObjects_0.objShape_m_0.y"
            ],
            self.Columns.COLLENVMODELPORTDYNAMICOBJECTSHAPE_1_M_0_X: [
                "AP.collEnvModelPort.dynamicObjects_1.objShape_m_0.x"
            ],
            self.Columns.COLLENVMODELPORTDYNAMICOBJECTSHAPE_1_M_0_Y: [
                "AP.collEnvModelPort.dynamicObjects_1.objShape_m_0.y"
            ],
            self.Columns.ODOESTIMATION_XPOSITION_M: [
                "AP.odoEstimationOutputPort.odoEstimation.xPosition_m",
                "AP.odoEstimationPort.xPosition_m",
            ],
            self.Columns.ODOESTIMATIONPORT_CYCLE_COUNTER: [
                "AP.odoEstimationOutputPort.odoEstimation.sSigHeader.uiCycleCounter"
            ],
            self.Columns.SI_CYCLE_COUNTER: ["AP.parkingBoxPort.sSigHeader.uiCycleCounter"],
            self.Columns.ODOESTIMATION_YPOSITION_M: [
                "AP.odoEstimationOutputPort.odoEstimation.yPosition_m",
                "AP.odoEstimationPort.yPosition_m",
            ],
            self.Columns.ODOESTIMATION_YANGLE: [
                "AP.odoEstimationOutputPort.odoEstimation.yawAngle_rad",
            ],
            self.Columns.PB_0_PARKINGSCENARIO_NU: [".parkingBoxPort.parkingBoxes_0.parkingScenario_nu"],
            self.Columns.STATICOBJECT_0_OBJSHAPE_M_ARRAY_0_X: [
                "GT.envModelPort.staticObjects._0_.objShape_m.array._%_.x_dir"
            ],
            self.Columns.STATICOBJECT_0_OBJSHAPE_M_ARRAY_0_Y: [
                "GT.envModelPort.staticObjects._0_.objShape_m.array._%_.y_dir"
            ],
            self.Columns.STATICOBJECT_1_OBJSHAPE_M_ARRAY_0_X: [
                "GT.envModelPort.staticObjects._1_.objShape_m.array._%_.x_dir"
            ],
            self.Columns.STATICOBJECT_1_OBJSHAPE_M_ARRAY_0_Y: [
                "GT.envModelPort.staticObjects._1_.objShape_m.array._%_.y_dir"
            ],
            self.Columns.STATICOBJECT_ACTUALSIZE: ["GT.envModelPort.staticObjects._%_.objShape_m.actualSize"],
            self.Columns.NUMBERVALIDSTATICOBJECTS: ["AP.collEnvModelPort.numberOfStaticObjects_u8"],
            self.Columns.STATICOBJECTSHAPE_0_M_0_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_0.x"],
            self.Columns.STATICOBJECTSHAPE_0_M_1_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_1.x"],
            self.Columns.STATICOBJECTSHAPE_0_M_2_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_2.x"],
            self.Columns.STATICOBJECTSHAPE_0_M_3_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_3.x"],
            self.Columns.STATICOBJECTSHAPE_0_M_4_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_4.x"],
            self.Columns.STATICOBJECTSHAPE_0_M_5_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_5.x"],
            self.Columns.STATICOBJECTSHAPE_0_M_6_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_6.x"],
            self.Columns.STATICOBJECTSHAPE_0_M_7_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_7.x"],
            self.Columns.STATICOBJECTSHAPE_0_M_8_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_8.x"],
            self.Columns.STATICOBJECTSHAPE_0_M_9_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_9.x"],
            self.Columns.STATICOBJECTSHAPE_0_M_10_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_10.x"],
            self.Columns.STATICOBJECTSHAPE_0_M_11_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_11.x"],
            self.Columns.STATICOBJECTSHAPE_0_M_12_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_12.x"],
            self.Columns.STATICOBJECTSHAPE_0_M_13_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_13.x"],
            self.Columns.STATICOBJECTSHAPE_0_M_14_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_14.x"],
            self.Columns.STATICOBJECTSHAPE_0_M_15_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_15.x"],
            self.Columns.STATICOBJECTSHAPE_0_M_0_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_0.y"],
            self.Columns.STATICOBJECTSHAPE_0_M_1_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_1.y"],
            self.Columns.STATICOBJECTSHAPE_0_M_2_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_2.y"],
            self.Columns.STATICOBJECTSHAPE_0_M_3_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_3.y"],
            self.Columns.STATICOBJECTSHAPE_0_M_4_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_4.y"],
            self.Columns.STATICOBJECTSHAPE_0_M_5_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_5.y"],
            self.Columns.STATICOBJECTSHAPE_0_M_6_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_6.y"],
            self.Columns.STATICOBJECTSHAPE_0_M_7_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_7.y"],
            self.Columns.STATICOBJECTSHAPE_0_M_8_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_8.y"],
            self.Columns.STATICOBJECTSHAPE_0_M_9_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_9.y"],
            self.Columns.STATICOBJECTSHAPE_0_M_10_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_10.y"],
            self.Columns.STATICOBJECTSHAPE_0_M_11_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_11.y"],
            self.Columns.STATICOBJECTSHAPE_0_M_12_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_12.y"],
            self.Columns.STATICOBJECTSHAPE_0_M_13_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_13.y"],
            self.Columns.STATICOBJECTSHAPE_0_M_14_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_14.y"],
            self.Columns.STATICOBJECTSHAPE_0_M_15_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_15.y"],
            self.Columns.STATICOBJECTSHAPE_1_M_0_x: ["AP.collEnvModelPort.staticObjects_1.objShape_m_0.x"],
            self.Columns.STATICOBJECTSHAPE_1_M_1_x: ["AP.collEnvModelPort.staticObjects_1.objShape_m_1.x"],
            self.Columns.STATICOBJECTSHAPE_1_M_2_x: ["AP.collEnvModelPort.staticObjects_1.objShape_m_2.x"],
            self.Columns.STATICOBJECTSHAPE_1_M_3_x: ["AP.collEnvModelPort.staticObjects_1.objShape_m_3.x"],
            self.Columns.STATICOBJECTSHAPE_1_M_4_x: ["AP.collEnvModelPort.staticObjects_1.objShape_m_4.x"],
            self.Columns.STATICOBJECTSHAPE_1_M_5_x: ["AP.collEnvModelPort.staticObjects_1.objShape_m_5.x"],
            self.Columns.STATICOBJECTSHAPE_1_M_6_x: ["AP.collEnvModelPort.staticObjects_1.objShape_m_6.x"],
            self.Columns.STATICOBJECTSHAPE_1_M_7_x: ["AP.collEnvModelPort.staticObjects_1.objShape_m_7.x"],
            self.Columns.STATICOBJECTSHAPE_1_M_8_x: ["AP.collEnvModelPort.staticObjects_1.objShape_m_8.x"],
            self.Columns.STATICOBJECTSHAPE_1_M_9_x: ["AP.collEnvModelPort.staticObjects_1.objShape_m_9.x"],
            self.Columns.STATICOBJECTSHAPE_1_M_10_x: ["AP.collEnvModelPort.staticObjects_1.objShape_m_10.x"],
            self.Columns.STATICOBJECTSHAPE_1_M_11_x: ["AP.collEnvModelPort.staticObjects_1.objShape_m_11.x"],
            self.Columns.STATICOBJECTSHAPE_1_M_12_x: ["AP.collEnvModelPort.staticObjects_1.objShape_m_12.x"],
            self.Columns.STATICOBJECTSHAPE_1_M_13_x: ["AP.collEnvModelPort.staticObjects_1.objShape_m_13.x"],
            self.Columns.STATICOBJECTSHAPE_1_M_14_x: ["AP.collEnvModelPort.staticObjects_1.objShape_m_14.x"],
            self.Columns.STATICOBJECTSHAPE_1_M_15_x: ["AP.collEnvModelPort.staticObjects_1.objShape_m_15.x"],
            self.Columns.STATICOBJECTSHAPE_1_M_0_y: ["AP.collEnvModelPort.staticObjects_1.objShape_m_0.y"],
            self.Columns.STATICOBJECTSHAPE_1_M_1_y: ["AP.collEnvModelPort.staticObjects_1.objShape_m_1.y"],
            self.Columns.STATICOBJECTSHAPE_1_M_2_y: ["AP.collEnvModelPort.staticObjects_1.objShape_m_2.y"],
            self.Columns.STATICOBJECTSHAPE_1_M_3_y: ["AP.collEnvModelPort.staticObjects_1.objShape_m_3.y"],
            self.Columns.STATICOBJECTSHAPE_1_M_4_y: ["AP.collEnvModelPort.staticObjects_1.objShape_m_4.y"],
            self.Columns.STATICOBJECTSHAPE_1_M_5_y: ["AP.collEnvModelPort.staticObjects_1.objShape_m_5.y"],
            self.Columns.STATICOBJECTSHAPE_1_M_6_y: ["AP.collEnvModelPort.staticObjects_1.objShape_m_6.y"],
            self.Columns.STATICOBJECTSHAPE_1_M_7_y: ["AP.collEnvModelPort.staticObjects_1.objShape_m_7.y"],
            self.Columns.STATICOBJECTSHAPE_1_M_8_y: ["AP.collEnvModelPort.staticObjects_1.objShape_m_8.y"],
            self.Columns.STATICOBJECTSHAPE_1_M_9_y: ["AP.collEnvModelPort.staticObjects_1.objShape_m_9.y"],
            self.Columns.STATICOBJECTSHAPE_1_M_10_y: ["AP.collEnvModelPort.staticObjects_1.objShape_m_10.y"],
            self.Columns.STATICOBJECTSHAPE_1_M_11_y: ["AP.collEnvModelPort.staticObjects_1.objShape_m_11.y"],
            self.Columns.STATICOBJECTSHAPE_1_M_12_y: ["AP.collEnvModelPort.staticObjects_1.objShape_m_12.y"],
            self.Columns.STATICOBJECTSHAPE_1_M_13_y: ["AP.collEnvModelPort.staticObjects_1.objShape_m_13.y"],
            self.Columns.STATICOBJECTSHAPE_1_M_14_y: ["AP.collEnvModelPort.staticObjects_1.objShape_m_14.y"],
            self.Columns.STATICOBJECTSHAPE_1_M_15_y: ["AP.collEnvModelPort.staticObjects_1.objShape_m_15.y"],
            self.Columns.STATICOBJECTSHAPE_2_M_0_x: ["AP.collEnvModelPort.staticObjects_2.objShape_m_0.x"],
            self.Columns.STATICOBJECTSHAPE_2_M_1_x: ["AP.collEnvModelPort.staticObjects_2.objShape_m_1.x"],
            self.Columns.STATICOBJECTSHAPE_2_M_2_x: ["AP.collEnvModelPort.staticObjects_2.objShape_m_2.x"],
            self.Columns.STATICOBJECTSHAPE_2_M_3_x: ["AP.collEnvModelPort.staticObjects_2.objShape_m_3.x"],
            self.Columns.STATICOBJECTSHAPE_2_M_4_x: ["AP.collEnvModelPort.staticObjects_2.objShape_m_4.x"],
            self.Columns.STATICOBJECTSHAPE_2_M_5_x: ["AP.collEnvModelPort.staticObjects_2.objShape_m_5.x"],
            self.Columns.STATICOBJECTSHAPE_2_M_6_x: ["AP.collEnvModelPort.staticObjects_2.objShape_m_6.x"],
            self.Columns.STATICOBJECTSHAPE_2_M_7_x: ["AP.collEnvModelPort.staticObjects_2.objShape_m_7.x"],
            self.Columns.STATICOBJECTSHAPE_2_M_8_x: ["AP.collEnvModelPort.staticObjects_2.objShape_m_8.x"],
            self.Columns.STATICOBJECTSHAPE_2_M_9_x: ["AP.collEnvModelPort.staticObjects_2.objShape_m_9.x"],
            self.Columns.STATICOBJECTSHAPE_2_M_10_x: ["AP.collEnvModelPort.staticObjects_2.objShape_m_10.x"],
            self.Columns.STATICOBJECTSHAPE_2_M_11_x: ["AP.collEnvModelPort.staticObjects_2.objShape_m_11.x"],
            self.Columns.STATICOBJECTSHAPE_2_M_12_x: ["AP.collEnvModelPort.staticObjects_2.objShape_m_12.x"],
            self.Columns.STATICOBJECTSHAPE_2_M_13_x: ["AP.collEnvModelPort.staticObjects_2.objShape_m_13.x"],
            self.Columns.STATICOBJECTSHAPE_2_M_14_x: ["AP.collEnvModelPort.staticObjects_2.objShape_m_14.x"],
            self.Columns.STATICOBJECTSHAPE_2_M_15_x: ["AP.collEnvModelPort.staticObjects_2.objShape_m_15.x"],
            self.Columns.STATICOBJECTSHAPE_2_M_0_y: ["AP.collEnvModelPort.staticObjects_2.objShape_m_0.y"],
            self.Columns.STATICOBJECTSHAPE_2_M_1_y: ["AP.collEnvModelPort.staticObjects_2.objShape_m_1.y"],
            self.Columns.STATICOBJECTSHAPE_2_M_2_y: ["AP.collEnvModelPort.staticObjects_2.objShape_m_2.y"],
            self.Columns.STATICOBJECTSHAPE_2_M_3_y: ["AP.collEnvModelPort.staticObjects_2.objShape_m_3.y"],
            self.Columns.STATICOBJECTSHAPE_2_M_4_y: ["AP.collEnvModelPort.staticObjects_2.objShape_m_4.y"],
            self.Columns.STATICOBJECTSHAPE_2_M_5_y: ["AP.collEnvModelPort.staticObjects_2.objShape_m_5.y"],
            self.Columns.STATICOBJECTSHAPE_2_M_6_y: ["AP.collEnvModelPort.staticObjects_2.objShape_m_6.y"],
            self.Columns.STATICOBJECTSHAPE_2_M_7_y: ["AP.collEnvModelPort.staticObjects_2.objShape_m_7.y"],
            self.Columns.STATICOBJECTSHAPE_2_M_8_y: ["AP.collEnvModelPort.staticObjects_2.objShape_m_8.y"],
            self.Columns.STATICOBJECTSHAPE_2_M_9_y: ["AP.collEnvModelPort.staticObjects_2.objShape_m_9.y"],
            self.Columns.STATICOBJECTSHAPE_2_M_10_y: ["AP.collEnvModelPort.staticObjects_2.objShape_m_10.y"],
            self.Columns.STATICOBJECTSHAPE_2_M_11_y: ["AP.collEnvModelPort.staticObjects_2.objShape_m_11.y"],
            self.Columns.STATICOBJECTSHAPE_2_M_12_y: ["AP.collEnvModelPort.staticObjects_2.objShape_m_12.y"],
            self.Columns.STATICOBJECTSHAPE_2_M_13_y: ["AP.collEnvModelPort.staticObjects_2.objShape_m_13.y"],
            self.Columns.STATICOBJECTSHAPE_2_M_14_y: ["AP.collEnvModelPort.staticObjects_2.objShape_m_14.y"],
            self.Columns.STATICOBJECTSHAPE_2_M_15_y: ["AP.collEnvModelPort.staticObjects_2.objShape_m_15.y"],
            self.Columns.STATICOBJECTSHAPE_3_M_0_x: ["AP.collEnvModelPort.staticObjects_3.objShape_m_0.x"],
            self.Columns.STATICOBJECTSHAPE_3_M_1_x: ["AP.collEnvModelPort.staticObjects_3.objShape_m_1.x"],
            self.Columns.STATICOBJECTSHAPE_3_M_2_x: ["AP.collEnvModelPort.staticObjects_3.objShape_m_2.x"],
            self.Columns.STATICOBJECTSHAPE_3_M_3_x: ["AP.collEnvModelPort.staticObjects_3.objShape_m_3.x"],
            self.Columns.STATICOBJECTSHAPE_3_M_4_x: ["AP.collEnvModelPort.staticObjects_3.objShape_m_4.x"],
            self.Columns.STATICOBJECTSHAPE_3_M_5_x: ["AP.collEnvModelPort.staticObjects_3.objShape_m_5.x"],
            self.Columns.STATICOBJECTSHAPE_3_M_6_x: ["AP.collEnvModelPort.staticObjects_3.objShape_m_6.x"],
            self.Columns.STATICOBJECTSHAPE_3_M_7_x: ["AP.collEnvModelPort.staticObjects_3.objShape_m_7.x"],
            self.Columns.STATICOBJECTSHAPE_3_M_8_x: ["AP.collEnvModelPort.staticObjects_3.objShape_m_8.x"],
            self.Columns.STATICOBJECTSHAPE_3_M_9_x: ["AP.collEnvModelPort.staticObjects_3.objShape_m_9.x"],
            self.Columns.STATICOBJECTSHAPE_3_M_10_x: ["AP.collEnvModelPort.staticObjects_3.objShape_m_10.x"],
            self.Columns.STATICOBJECTSHAPE_3_M_11_x: ["AP.collEnvModelPort.staticObjects_3.objShape_m_11.x"],
            self.Columns.STATICOBJECTSHAPE_3_M_12_x: ["AP.collEnvModelPort.staticObjects_3.objShape_m_12.x"],
            self.Columns.STATICOBJECTSHAPE_3_M_13_x: ["AP.collEnvModelPort.staticObjects_3.objShape_m_13.x"],
            self.Columns.STATICOBJECTSHAPE_3_M_14_x: ["AP.collEnvModelPort.staticObjects_3.objShape_m_14.x"],
            self.Columns.STATICOBJECTSHAPE_3_M_15_x: ["AP.collEnvModelPort.staticObjects_3.objShape_m_15.x"],
            self.Columns.STATICOBJECTSHAPE_3_M_0_y: ["AP.collEnvModelPort.staticObjects_3.objShape_m_0.y"],
            self.Columns.STATICOBJECTSHAPE_3_M_1_y: ["AP.collEnvModelPort.staticObjects_3.objShape_m_1.y"],
            self.Columns.STATICOBJECTSHAPE_3_M_2_y: ["AP.collEnvModelPort.staticObjects_3.objShape_m_2.y"],
            self.Columns.STATICOBJECTSHAPE_3_M_3_y: ["AP.collEnvModelPort.staticObjects_3.objShape_m_3.y"],
            self.Columns.STATICOBJECTSHAPE_3_M_4_y: ["AP.collEnvModelPort.staticObjects_3.objShape_m_4.y"],
            self.Columns.STATICOBJECTSHAPE_3_M_5_y: ["AP.collEnvModelPort.staticObjects_3.objShape_m_5.y"],
            self.Columns.STATICOBJECTSHAPE_3_M_6_y: ["AP.collEnvModelPort.staticObjects_3.objShape_m_6.y"],
            self.Columns.STATICOBJECTSHAPE_3_M_7_y: ["AP.collEnvModelPort.staticObjects_3.objShape_m_7.y"],
            self.Columns.STATICOBJECTSHAPE_3_M_8_y: ["AP.collEnvModelPort.staticObjects_3.objShape_m_8.y"],
            self.Columns.STATICOBJECTSHAPE_3_M_9_y: ["AP.collEnvModelPort.staticObjects_3.objShape_m_9.y"],
            self.Columns.STATICOBJECTSHAPE_3_M_10_y: ["AP.collEnvModelPort.staticObjects_3.objShape_m_10.y"],
            self.Columns.STATICOBJECTSHAPE_3_M_11_y: ["AP.collEnvModelPort.staticObjects_3.objShape_m_11.y"],
            self.Columns.STATICOBJECTSHAPE_3_M_12_y: ["AP.collEnvModelPort.staticObjects_3.objShape_m_12.y"],
            self.Columns.STATICOBJECTSHAPE_3_M_13_y: ["AP.collEnvModelPort.staticObjects_3.objShape_m_13.y"],
            self.Columns.STATICOBJECTSHAPE_3_M_14_y: ["AP.collEnvModelPort.staticObjects_3.objShape_m_14.y"],
            self.Columns.STATICOBJECTSHAPE_3_M_15_y: ["AP.collEnvModelPort.staticObjects_3.objShape_m_15.y"],
            ######
            self.Columns.NUMBERVALIDSTATICOBJECTSINWRLDCRD: ["AP.envModelPort.numberOfStaticObjects_u8"],
            self.Columns.STATICOBJECT_2_OBJSHAPE_M_ARRAY_0_X: [
                "GT.envModelPort.staticObjects._2_.objShape_m.array._%_.x_dir"
            ],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_0_x: ["AP.envModelPort.staticObjects_0.objShape_m_0.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_1_x: ["AP.envModelPort.staticObjects_0.objShape_m_1.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_2_x: ["AP.envModelPort.staticObjects_0.objShape_m_2.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_3_x: ["AP.envModelPort.staticObjects_0.objShape_m_3.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_4_x: ["AP.envModelPort.staticObjects_0.objShape_m_4.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_5_x: ["AP.envModelPort.staticObjects_0.objShape_m_5.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_6_x: ["AP.envModelPort.staticObjects_0.objShape_m_6.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_7_x: ["AP.envModelPort.staticObjects_0.objShape_m_7.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_8_x: ["AP.envModelPort.staticObjects_0.objShape_m_8.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_9_x: ["AP.envModelPort.staticObjects_0.objShape_m_9.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_10_x: ["AP.envModelPort.staticObjects_0.objShape_m_10.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_11_x: ["AP.envModelPort.staticObjects_0.objShape_m_11.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_12_x: ["AP.envModelPort.staticObjects_0.objShape_m_12.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_13_x: ["AP.envModelPort.staticObjects_0.objShape_m_13.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_14_x: ["AP.envModelPort.staticObjects_0.objShape_m_14.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_15_x: ["AP.envModelPort.staticObjects_0.objShape_m_15.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_0_y: ["AP.envModelPort.staticObjects_0.objShape_m_0.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_1_y: ["AP.envModelPort.staticObjects_0.objShape_m_1.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_2_y: ["AP.envModelPort.staticObjects_0.objShape_m_2.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_3_y: ["AP.envModelPort.staticObjects_0.objShape_m_3.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_4_y: ["AP.envModelPort.staticObjects_0.objShape_m_4.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_5_y: ["AP.envModelPort.staticObjects_0.objShape_m_5.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_6_y: ["AP.envModelPort.staticObjects_0.objShape_m_6.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_7_y: ["AP.envModelPort.staticObjects_0.objShape_m_7.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_8_y: ["AP.envModelPort.staticObjects_0.objShape_m_8.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_9_y: ["AP.envModelPort.staticObjects_0.objShape_m_9.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_10_y: ["AP.envModelPort.staticObjects_0.objShape_m_10.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_11_y: ["AP.envModelPort.staticObjects_0.objShape_m_11.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_12_y: ["AP.envModelPort.staticObjects_0.objShape_m_12.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_13_y: ["AP.envModelPort.staticObjects_0.objShape_m_13.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_14_y: ["AP.envModelPort.staticObjects_0.objShape_m_14.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_0_M_15_y: ["AP.envModelPort.staticObjects_0.objShape_m_15.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_0_x: ["AP.envModelPort.staticObjects_1.objShape_m_0.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_1_x: ["AP.envModelPort.staticObjects_1.objShape_m_1.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_2_x: ["AP.envModelPort.staticObjects_1.objShape_m_2.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_3_x: ["AP.envModelPort.staticObjects_1.objShape_m_3.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_4_x: ["AP.envModelPort.staticObjects_1.objShape_m_4.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_5_x: ["AP.envModelPort.staticObjects_1.objShape_m_5.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_6_x: ["AP.envModelPort.staticObjects_1.objShape_m_6.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_7_x: ["AP.envModelPort.staticObjects_1.objShape_m_7.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_8_x: ["AP.envModelPort.staticObjects_1.objShape_m_8.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_9_x: ["AP.envModelPort.staticObjects_1.objShape_m_9.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_10_x: ["AP.envModelPort.staticObjects_1.objShape_m_10.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_11_x: ["AP.envModelPort.staticObjects_1.objShape_m_11.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_12_x: ["AP.envModelPort.staticObjects_1.objShape_m_12.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_13_x: ["AP.envModelPort.staticObjects_1.objShape_m_13.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_14_x: ["AP.envModelPort.staticObjects_1.objShape_m_14.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_15_x: ["AP.envModelPort.staticObjects_1.objShape_m_15.x"],
            self.Columns.STATICOBJECT_2_OBJSHAPE_M_ARRAY_0_Y: [
                "GT.envModelPort.staticObjects._2_.objShape_m.array._%_.y_dir"
            ],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_0_y: ["AP.envModelPort.staticObjects_1.objShape_m_0.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_1_y: ["AP.envModelPort.staticObjects_1.objShape_m_1.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_2_y: ["AP.envModelPort.staticObjects_1.objShape_m_2.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_3_y: ["AP.envModelPort.staticObjects_1.objShape_m_3.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_4_y: ["AP.envModelPort.staticObjects_1.objShape_m_4.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_5_y: ["AP.envModelPort.staticObjects_1.objShape_m_5.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_6_y: ["AP.envModelPort.staticObjects_1.objShape_m_6.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_7_y: ["AP.envModelPort.staticObjects_1.objShape_m_7.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_8_y: ["AP.envModelPort.staticObjects_1.objShape_m_8.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_9_y: ["AP.envModelPort.staticObjects_1.objShape_m_9.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_10_y: ["AP.envModelPort.staticObjects_1.objShape_m_10.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_11_y: ["AP.envModelPort.staticObjects_1.objShape_m_11.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_12_y: ["AP.envModelPort.staticObjects_1.objShape_m_12.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_13_y: ["AP.envModelPort.staticObjects_1.objShape_m_13.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_14_y: ["AP.envModelPort.staticObjects_1.objShape_m_14.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_1_M_15_y: ["AP.envModelPort.staticObjects_1.objShape_m_15.y"],
            ######
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_0_x: ["AP.envModelPort.staticObjects_2.objShape_m_0.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_1_x: ["AP.envModelPort.staticObjects_2.objShape_m_1.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_2_x: ["AP.envModelPort.staticObjects_2.objShape_m_2.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_3_x: ["AP.envModelPort.staticObjects_2.objShape_m_3.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_4_x: ["AP.envModelPort.staticObjects_2.objShape_m_4.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_5_x: ["AP.envModelPort.staticObjects_2.objShape_m_5.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_6_x: ["AP.envModelPort.staticObjects_2.objShape_m_6.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_7_x: ["AP.envModelPort.staticObjects_2.objShape_m_7.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_8_x: ["AP.envModelPort.staticObjects_2.objShape_m_8.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_9_x: ["AP.envModelPort.staticObjects_2.objShape_m_9.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_10_x: ["AP.envModelPort.staticObjects_2.objShape_m_10.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_11_x: ["AP.envModelPort.staticObjects_2.objShape_m_11.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_12_x: ["AP.envModelPort.staticObjects_2.objShape_m_12.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_13_x: ["AP.envModelPort.staticObjects_2.objShape_m_13.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_14_x: ["AP.envModelPort.staticObjects_2.objShape_m_14.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_15_x: ["AP.envModelPort.staticObjects_2.objShape_m_15.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_0_y: ["AP.envModelPort.staticObjects_2.objShape_m_0.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_1_y: ["AP.envModelPort.staticObjects_2.objShape_m_1.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_2_y: ["AP.envModelPort.staticObjects_2.objShape_m_2.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_3_y: ["AP.envModelPort.staticObjects_2.objShape_m_3.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_4_y: ["AP.envModelPort.staticObjects_2.objShape_m_4.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_5_y: ["AP.envModelPort.staticObjects_2.objShape_m_5.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_6_y: ["AP.envModelPort.staticObjects_2.objShape_m_6.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_7_y: ["AP.envModelPort.staticObjects_2.objShape_m_7.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_8_y: ["AP.envModelPort.staticObjects_2.objShape_m_8.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_9_y: ["AP.envModelPort.staticObjects_2.objShape_m_9.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_10_y: ["AP.envModelPort.staticObjects_2.objShape_m_10.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_11_y: ["AP.envModelPort.staticObjects_2.objShape_m_11.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_12_y: ["AP.envModelPort.staticObjects_2.objShape_m_12.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_13_y: ["AP.envModelPort.staticObjects_2.objShape_m_13.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_14_y: ["AP.envModelPort.staticObjects_2.objShape_m_14.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_2_M_15_y: ["AP.envModelPort.staticObjects_2.objShape_m_15.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_0_x: ["AP.envModelPort.staticObjects_3.objShape_m_0.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_1_x: ["AP.envModelPort.staticObjects_3.objShape_m_1.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_2_x: ["AP.envModelPort.staticObjects_3.objShape_m_2.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_3_x: ["AP.envModelPort.staticObjects_3.objShape_m_3.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_4_x: ["AP.envModelPort.staticObjects_3.objShape_m_4.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_5_x: ["AP.envModelPort.staticObjects_3.objShape_m_5.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_6_x: ["AP.envModelPort.staticObjects_3.objShape_m_6.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_7_x: ["AP.envModelPort.staticObjects_3.objShape_m_7.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_8_x: ["AP.envModelPort.staticObjects_3.objShape_m_8.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_9_x: ["AP.envModelPort.staticObjects_3.objShape_m_9.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_10_x: ["AP.envModelPort.staticObjects_3.objShape_m_10.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_11_x: ["AP.envModelPort.staticObjects_3.objShape_m_11.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_12_x: ["AP.envModelPort.staticObjects_3.objShape_m_12.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_13_x: ["AP.envModelPort.staticObjects_3.objShape_m_13.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_14_x: ["AP.envModelPort.staticObjects_3.objShape_m_14.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_15_x: ["AP.envModelPort.staticObjects_3.objShape_m_15.x"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_0_y: ["AP.envModelPort.staticObjects_3.objShape_m_0.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_1_y: ["AP.envModelPort.staticObjects_3.objShape_m_1.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_2_y: ["AP.envModelPort.staticObjects_3.objShape_m_2.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_3_y: ["AP.envModelPort.staticObjects_3.objShape_m_3.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_4_y: ["AP.envModelPort.staticObjects_3.objShape_m_4.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_5_y: ["AP.envModelPort.staticObjects_3.objShape_m_5.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_6_y: ["AP.envModelPort.staticObjects_3.objShape_m_6.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_7_y: ["AP.envModelPort.staticObjects_3.objShape_m_7.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_8_y: ["AP.envModelPort.staticObjects_3.objShape_m_8.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_9_y: ["AP.envModelPort.staticObjects_3.objShape_m_9.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_10_y: ["AP.envModelPort.staticObjects_3.objShape_m_10.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_11_y: ["AP.envModelPort.staticObjects_3.objShape_m_11.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_12_y: ["AP.envModelPort.staticObjects_3.objShape_m_12.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_13_y: ["AP.envModelPort.staticObjects_3.objShape_m_13.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_14_y: ["AP.envModelPort.staticObjects_3.objShape_m_14.y"],
            self.Columns.STATICOBJECTSHAPEWRLDCRD_3_M_15_y: ["AP.envModelPort.staticObjects_3.objShape_m_15.y"],
            self.Columns.NUMBERVALIDDYNAMICOBJECTSWRLDCRD: ["AP.envModelPort.numberOfDynamicObjects_u8"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_0_0_x: ["AP.envModelPort.dynamicObjects_0.objShape_0.x"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_0_1_x: ["AP.envModelPort.dynamicObjects_0.objShape_1.x"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_0_2_x: ["AP.envModelPort.dynamicObjects_0.objShape_2.x"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_0_3_x: ["AP.envModelPort.dynamicObjects_0.objShape_3.x"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_0_0_y: ["AP.envModelPort.dynamicObjects_0.objShape_0.y"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_0_1_y: ["AP.envModelPort.dynamicObjects_0.objShape_1.y"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_0_2_y: ["AP.envModelPort.dynamicObjects_0.objShape_2.y"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_0_3_y: ["AP.envModelPort.dynamicObjects_0.objShape_3.y"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_1_0_x: ["AP.envModelPort.dynamicObjects_1.objShape_0.x"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_1_1_x: ["AP.envModelPort.dynamicObjects_1.objShape_1.x"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_1_2_x: ["AP.envModelPort.dynamicObjects_1.objShape_2.x"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_1_3_x: ["AP.envModelPort.dynamicObjects_1.objShape_3.x"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_1_0_y: ["AP.envModelPort.dynamicObjects_1.objShape_0.y"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_1_1_y: ["AP.envModelPort.dynamicObjects_1.objShape_1.y"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_1_2_y: ["AP.envModelPort.dynamicObjects_1.objShape_2.y"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_1_3_y: ["AP.envModelPort.dynamicObjects_1.objShape_3.y"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_2_0_x: ["AP.envModelPort.dynamicObjects_2.objShape_0.x"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_2_1_x: ["AP.envModelPort.dynamicObjects_2.objShape_1.x"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_2_2_x: ["AP.envModelPort.dynamicObjects_2.objShape_2.x"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_2_3_x: ["AP.envModelPort.dynamicObjects_2.objShape_3.x"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_2_0_y: ["AP.envModelPort.dynamicObjects_2.objShape_0.y"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_2_1_y: ["AP.envModelPort.dynamicObjects_2.objShape_1.y"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_2_2_y: ["AP.envModelPort.dynamicObjects_2.objShape_2.y"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_2_3_y: ["AP.envModelPort.dynamicObjects_2.objShape_3.y"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_3_0_x: ["AP.envModelPort.dynamicObjects_3.objShape_0.x"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_3_1_x: ["AP.envModelPort.dynamicObjects_3.objShape_1.x"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_3_2_x: ["AP.envModelPort.dynamicObjects_3.objShape_2.x"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_3_3_x: ["AP.envModelPort.dynamicObjects_3.objShape_3.x"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_3_0_y: ["AP.envModelPort.dynamicObjects_3.objShape_0.y"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_3_1_y: ["AP.envModelPort.dynamicObjects_3.objShape_1.y"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_3_2_y: ["AP.envModelPort.dynamicObjects_3.objShape_2.y"],
            self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_3_3_y: ["AP.envModelPort.dynamicObjects_3.objShape_3.y"],
            # self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_1_M_0_x: ["AP.envModelPort.dynamicObjects_1.objShape_m_0.x"],
            # self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_1_M_1_x: ["AP.envModelPort.dynamicObjects_1.objShape_m_1.x"],
            # self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_1_M_2_x: ["AP.envModelPort.dynamicObjects_1.objShape_m_2.x"],
            # self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_1_M_3_x: ["AP.envModelPort.dynamicObjects_1.objShape_m_3.x"],
            # self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_1_M_0_y: ["AP.envModelPort.dynamicObjects_1.objShape_m_0.y"],
            # self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_1_M_1_y: ["AP.envModelPort.dynamicObjects_1.objShape_m_1.y"],
            # self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_1_M_2_y: ["AP.envModelPort.dynamicObjects_1.objShape_m_2.y"],
            # self.Columns.DYNAMICOBJECTSHAPEWRLDCRD_1_M_3_y: ["AP.envModelPort.dynamicObjects_1.objShape_m_3.y"],
            # self.Columns.STATICOBJECT_ACTUALSIZE_0: ["GT.envModelPort.staticObjects._0_.objShape_m.actualSize"],
            # self.Columns.STATICOBJECT_ACTUALSIZE_1: ["GT.envModelPort.staticObjects._1_.objShape_m.actualSize"],
            # self.Columns.STATICOBJECT_ACTUALSIZE_2: ["GT.envModelPort.staticObjects._2_.objShape_m.actualSize"],
            self.Columns.NUMBERVALIDDYNAMICOBJECTS: ["AP.collEnvModelPort.numberOfDynamicObjects_u8"],
            self.Columns.DYNAMICOBJECTSHAPE_0_M_0_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_0.x"],
            self.Columns.DYNAMICOBJECTSHAPE_0_M_1_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_1.x"],
            self.Columns.DYNAMICOBJECTSHAPE_0_M_2_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_2.x"],
            self.Columns.DYNAMICOBJECTSHAPE_0_M_3_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_3.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_4_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_4.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_5_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_5.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_6_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_6.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_7_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_7.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_8_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_8.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_9_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_9.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_10_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_10.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_11_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_11.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_12_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_12.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_13_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_13.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_14_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_14.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_15_x: ["AP.collEnvModelPort.staticObjects_0.objShape_m_15.x"],
            "apstates": ["AP.planningCtrlPort.apStates"],
            self.Columns.DYNAMICOBJECTSHAPE_0_M_0_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_0.y"],
            self.Columns.DYNAMICOBJECTSHAPE_0_M_1_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_1.y"],
            self.Columns.DYNAMICOBJECTSHAPE_0_M_2_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_2.y"],
            self.Columns.DYNAMICOBJECTSHAPE_0_M_3_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_3.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_4_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_4.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_5_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_5.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_6_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_6.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_7_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_7.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_8_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_8.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_9_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_9.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_10_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_10.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_11_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_11.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_12_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_12.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_13_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_13.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_14_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_14.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_0_M_15_y: ["AP.collEnvModelPort.staticObjects_0.objShape_m_15.y"],
            self.Columns.DYNAMICOBJECTSHAPE_1_M_0_x: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_0.x"],
            self.Columns.DYNAMICOBJECTSHAPE_1_M_1_x: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_1.x"],
            self.Columns.DYNAMICOBJECTSHAPE_1_M_2_x: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_2.x"],
            self.Columns.DYNAMICOBJECTSHAPE_1_M_3_x: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_3.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_4_x: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_4.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_5_x: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_5.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_6_x: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_6.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_7_x: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_7.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_8_x: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_8.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_9_x: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_9.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_10_x: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_10.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_11_x: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_11.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_12_x: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_12.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_13_x: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_13.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_14_x: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_14.x"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_15_x: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_15.x"],
            self.Columns.DYNAMICOBJECTSHAPE_1_M_0_y: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_0.y"],
            self.Columns.DYNAMICOBJECTSHAPE_1_M_1_y: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_1.y"],
            self.Columns.DYNAMICOBJECTSHAPE_1_M_2_y: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_2.y"],
            self.Columns.DYNAMICOBJECTSHAPE_1_M_3_y: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_3.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_4_y: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_4.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_5_y: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_5.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_6_y: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_6.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_7_y: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_7.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_8_y: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_8.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_9_y: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_9.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_10_y: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_10.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_11_y: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_11.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_12_y: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_12.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_13_y: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_13.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_14_y: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_14.y"],
            # self.Columns.DYNAMICOBJECTSHAPE_1_M_15_y: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_15.y"],
            self.Columns.DYNAMICOBJECTSHAPE_2_M_0_y: ["AP.collEnvModelPort.dynamicObjects_2.objShape_m_0.y"],
            self.Columns.DYNAMICOBJECTSHAPE_2_M_1_y: ["AP.collEnvModelPort.dynamicObjects_2.objShape_m_1.y"],
            self.Columns.DYNAMICOBJECTSHAPE_2_M_2_y: ["AP.collEnvModelPort.dynamicObjects_2.objShape_m_2.y"],
            self.Columns.DYNAMICOBJECTSHAPE_2_M_3_y: ["AP.collEnvModelPort.dynamicObjects_2.objShape_m_3.y"],
            self.Columns.DYNAMICOBJECTSHAPE_3_M_0_y: ["AP.collEnvModelPort.dynamicObjects_3.objShape_m_0.y"],
            self.Columns.DYNAMICOBJECTSHAPE_3_M_1_y: ["AP.collEnvModelPort.dynamicObjects_3.objShape_m_1.y"],
            self.Columns.DYNAMICOBJECTSHAPE_3_M_2_y: ["AP.collEnvModelPort.dynamicObjects_3.objShape_m_2.y"],
            self.Columns.DYNAMICOBJECTSHAPE_3_M_3_y: ["AP.collEnvModelPort.dynamicObjects_3.objShape_m_3.y"],
            self.Columns.DYNAMICOBJECTSHAPE_1_M_0_x: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_0.x"],
            self.Columns.DYNAMICOBJECTSHAPE_1_M_1_x: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_1.x"],
            self.Columns.DYNAMICOBJECTSHAPE_1_M_2_x: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_2.x"],
            self.Columns.DYNAMICOBJECTSHAPE_1_M_3_x: ["AP.collEnvModelPort.dynamicObjects_1.objShape_m_3.x"],
            self.Columns.DYNAMICOBJECTSHAPE_2_M_0_x: ["AP.collEnvModelPort.dynamicObjects_2.objShape_m_0.x"],
            self.Columns.DYNAMICOBJECTSHAPE_2_M_1_x: ["AP.collEnvModelPort.dynamicObjects_2.objShape_m_1.x"],
            self.Columns.DYNAMICOBJECTSHAPE_2_M_2_x: ["AP.collEnvModelPort.dynamicObjects_2.objShape_m_2.x"],
            self.Columns.DYNAMICOBJECTSHAPE_2_M_3_x: ["AP.collEnvModelPort.dynamicObjects_2.objShape_m_3.x"],
            self.Columns.DYNAMICOBJECTSHAPE_3_M_0_x: ["AP.collEnvModelPort.dynamicObjects_3.objShape_m_0.x"],
            self.Columns.DYNAMICOBJECTSHAPE_3_M_1_x: ["AP.collEnvModelPort.dynamicObjects_3.objShape_m_1.x"],
            self.Columns.DYNAMICOBJECTSHAPE_3_M_2_x: ["AP.collEnvModelPort.dynamicObjects_3.objShape_m_2.x"],
            self.Columns.DYNAMICOBJECTSHAPE_3_M_3_x: ["AP.collEnvModelPort.dynamicObjects_3.objShape_m_3.x"],
            self.Columns.NUMBERPARKINGMARKINGS: ["AP.envModelPort.numberOfParkMarkings_u8"],
            self.Columns.EGOVEHICLEPOSEFORAP_X: ["AP.envModelPort.egoVehiclePoseForAP.pos_x_m"],
            self.Columns.EGOVEHICLEPOSEFORAP_Y: ["AP.envModelPort.egoVehiclePoseForAP.pos_y_m"],
            self.Columns.ODOESTIMATEPOSEFORAP_X: ["AP.odoEstimationPort.xPosition_m"],
            self.Columns.ODOESTIMATEPOSEFORAP_Y: ["AP.odoEstimationPort.yPosition_m"],
            self.Columns.STATICOBJECT_REFOBJID: ["GT.envModelPort.staticObjects._0_.refObjID_nu"],
            self.Columns.STATICOBJECT_EXISTENCEPROB_PERC: ["GT.envModelPort.staticObjects._0_.existenceProb_perc"],
            self.Columns.STATICOBJECT_OBJHEIGHTCLASS: ["GT.envModelPort.staticObjects._0_.objHeightClass_nu"],
            self.Columns.RESETCOUNTER: ["AP.resetOriginRequestPort.resetCounter_nu"],
            self.Columns.RESETORIGIN: ["AP.resetOriginRequestPort.resetOrigin_nu"],
            self.Columns.GT_ENV_NUMBEROFSTATICOBJECTS: ["GT.envModelPort.numberOfStaticObjects_u8"],
            self.Columns.AP_COLLENV_NUMBEROFSTATICOBJECTS: ["AP.collEnvModelPort.numberOfStaticObjects_u8"],
            self.Columns.AP_ENV_NUMBEROFSTATICOBJECTS: ["AP.envModelPort.numberOfStaticObjects_u8"],
            self.Columns.PARKINGSPACEMARKINGS_0_0_x: ["AP.envModelPort.parkingSpaceMarkings_0_0.x"],
            self.Columns.PARKINGSPACEMARKINGS_0_0_y: ["AP.envModelPort.parkingSpaceMarkings_0_0.y"],
            self.Columns.PARKINGSPACEMARKINGS_0_1_x: ["AP.envModelPort.parkingSpaceMarkings_0_1.x"],
            self.Columns.PARKINGSPACEMARKINGS_0_1_y: ["AP.envModelPort.parkingSpaceMarkings_0_1.y"],
            self.Columns.PARKINGSPACEMARKINGS_1_0_x: ["AP.envModelPort.parkingSpaceMarkings_1_0.x"],
            self.Columns.PARKINGSPACEMARKINGS_1_0_y: ["AP.envModelPort.parkingSpaceMarkings_1_0.y"],
            self.Columns.PARKINGSPACEMARKINGS_1_1_x: ["AP.envModelPort.parkingSpaceMarkings_1_1.x"],
            self.Columns.PARKINGSPACEMARKINGS_1_1_y: ["AP.envModelPort.parkingSpaceMarkings_1_1.y"],
            self.Columns.PARKINGSPACEMARKINGS_2_0_x: ["AP.envModelPort.parkingSpaceMarkings_2_0.x"],
            self.Columns.PARKINGSPACEMARKINGS_2_0_y: ["AP.envModelPort.parkingSpaceMarkings_2_0.y"],
            self.Columns.PARKINGSPACEMARKINGS_2_1_x: ["AP.envModelPort.parkingSpaceMarkings_2_1.x"],
            self.Columns.PARKINGSPACEMARKINGS_2_1_y: ["AP.envModelPort.parkingSpaceMarkings_2_1.y"],
            self.Columns.PARKINGSPACEMARKINGS_3_0_x: ["AP.envModelPort.parkingSpaceMarkings_3_0.x"],
            self.Columns.PARKINGSPACEMARKINGS_3_0_y: ["AP.envModelPort.parkingSpaceMarkings_3_0.y"],
            self.Columns.PARKINGSPACEMARKINGS_3_1_x: ["AP.envModelPort.parkingSpaceMarkings_3_1.x"],
            self.Columns.PARKINGSPACEMARKINGS_3_1_y: ["AP.envModelPort.parkingSpaceMarkings_3_1.y"],
            self.Columns.PARKINGSPACEMARKINGS_4_0_x: ["AP.envModelPort.parkingSpaceMarkings_4_0.x"],
            self.Columns.PARKINGSPACEMARKINGS_4_0_y: ["AP.envModelPort.parkingSpaceMarkings_4_0.y"],
            self.Columns.PARKINGSPACEMARKINGS_4_1_x: ["AP.envModelPort.parkingSpaceMarkings_4_1.x"],
            self.Columns.PARKINGSPACEMARKINGS_4_1_y: ["AP.envModelPort.parkingSpaceMarkings_4_1.y"],
            self.Columns.PARKINGSPACEMARKINGS_5_0_x: ["AP.envModelPort.parkingSpaceMarkings_5_0.x"],
            self.Columns.PARKINGSPACEMARKINGS_5_0_y: ["AP.envModelPort.parkingSpaceMarkings_5_0.y"],
            self.Columns.PARKINGSPACEMARKINGS_5_1_x: ["AP.envModelPort.parkingSpaceMarkings_5_1.x"],
            self.Columns.PARKINGSPACEMARKINGS_5_1_y: ["AP.envModelPort.parkingSpaceMarkings_5_1.y"],
            self.Columns.PARKINGSPACEMARKINGS_6_0_x: ["AP.envModelPort.parkingSpaceMarkings_6_0.x"],
            self.Columns.PARKINGSPACEMARKINGS_6_0_y: ["AP.envModelPort.parkingSpaceMarkings_6_0.y"],
            self.Columns.PARKINGSPACEMARKINGS_6_1_x: ["AP.envModelPort.parkingSpaceMarkings_6_1.x"],
            self.Columns.PARKINGSPACEMARKINGS_6_1_y: ["AP.envModelPort.parkingSpaceMarkings_6_1.y"],
            self.Columns.PARKINGSPACEMARKINGS_7_0_x: ["AP.envModelPort.parkingSpaceMarkings_7_0.x"],
            self.Columns.PARKINGSPACEMARKINGS_7_0_y: ["AP.envModelPort.parkingSpaceMarkings_7_0.y"],
            self.Columns.PARKINGSPACEMARKINGS_7_1_x: ["AP.envModelPort.parkingSpaceMarkings_7_1.x"],
            self.Columns.PARKINGSPACEMARKINGS_7_1_y: ["AP.envModelPort.parkingSpaceMarkings_7_1.y"],
            self.Columns.PARKINGSPACEMARKINGS_8_0_x: ["AP.envModelPort.parkingSpaceMarkings_8_0.x"],
            self.Columns.PARKINGSPACEMARKINGS_8_0_y: ["AP.envModelPort.parkingSpaceMarkings_8_0.y"],
            self.Columns.PARKINGSPACEMARKINGS_8_1_x: ["AP.envModelPort.parkingSpaceMarkings_8_1.x"],
            self.Columns.PARKINGSPACEMARKINGS_8_1_y: ["AP.envModelPort.parkingSpaceMarkings_8_1.y"],
            self.Columns.PARKINGSPACEMARKINGS_9_0_x: ["AP.envModelPort.parkingSpaceMarkings_9_0.x"],
            self.Columns.PARKINGSPACEMARKINGS_9_0_y: ["AP.envModelPort.parkingSpaceMarkings_9_0.y"],
            self.Columns.PARKINGSPACEMARKINGS_9_1_x: ["AP.envModelPort.parkingSpaceMarkings_9_1.x"],
            self.Columns.PARKINGSPACEMARKINGS_9_1_y: ["AP.envModelPort.parkingSpaceMarkings_9_1.y"],
            self.Columns.PARKINGSPACEMARKINGS_10_0_x: ["AP.envModelPort.parkingSpaceMarkings_10_0.x"],
            self.Columns.PARKINGSPACEMARKINGS_10_0_y: ["AP.envModelPort.parkingSpaceMarkings_10_0.y"],
            self.Columns.PARKINGSPACEMARKINGS_10_1_x: ["AP.envModelPort.parkingSpaceMarkings_10_1.x"],
            self.Columns.PARKINGSPACEMARKINGS_10_1_y: ["AP.envModelPort.parkingSpaceMarkings_10_1.y"],
            self.Columns.PARKINGSPACEMARKINGS_11_0_x: ["AP.envModelPort.parkingSpaceMarkings_11_0.x"],
            self.Columns.PARKINGSPACEMARKINGS_11_0_y: ["AP.envModelPort.parkingSpaceMarkings_11_0.y"],
            self.Columns.PARKINGSPACEMARKINGS_11_1_x: ["AP.envModelPort.parkingSpaceMarkings_11_1.x"],
            self.Columns.PARKINGSPACEMARKINGS_11_1_y: ["AP.envModelPort.parkingSpaceMarkings_11_1.y"],
            self.Columns.PARKINGSPACEMARKINGS_12_0_x: ["AP.envModelPort.parkingSpaceMarkings_12_0.x"],
            self.Columns.PARKINGSPACEMARKINGS_12_0_y: ["AP.envModelPort.parkingSpaceMarkings_12_0.y"],
            self.Columns.PARKINGSPACEMARKINGS_12_1_x: ["AP.envModelPort.parkingSpaceMarkings_12_1.x"],
            self.Columns.PARKINGSPACEMARKINGS_12_1_y: ["AP.envModelPort.parkingSpaceMarkings_12_1.y"],
            self.Columns.PARKINGSPACEMARKINGS_13_0_x: ["AP.envModelPort.parkingSpaceMarkings_13_0.x"],
            self.Columns.PARKINGSPACEMARKINGS_13_0_y: ["AP.envModelPort.parkingSpaceMarkings_13_0.y"],
            self.Columns.PARKINGSPACEMARKINGS_13_1_x: ["AP.envModelPort.parkingSpaceMarkings_13_1.x"],
            self.Columns.PARKINGSPACEMARKINGS_13_1_y: ["AP.envModelPort.parkingSpaceMarkings_13_1.y"],
            self.Columns.PARKINGSPACEMARKINGS_14_0_x: ["AP.envModelPort.parkingSpaceMarkings_14_0.x"],
            self.Columns.PARKINGSPACEMARKINGS_14_0_y: ["AP.envModelPort.parkingSpaceMarkings_14_0.y"],
            self.Columns.PARKINGSPACEMARKINGS_14_1_x: ["AP.envModelPort.parkingSpaceMarkings_14_1.x"],
            self.Columns.PARKINGSPACEMARKINGS_14_1_y: ["AP.envModelPort.parkingSpaceMarkings_14_1.y"],
            self.Columns.PARKINGSPACEMARKINGS_15_0_x: ["AP.envModelPort.parkingSpaceMarkings_15_0.x"],
            self.Columns.PARKINGSPACEMARKINGS_15_0_y: ["AP.envModelPort.parkingSpaceMarkings_15_0.y"],
            self.Columns.PARKINGSPACEMARKINGS_15_1_x: ["AP.envModelPort.parkingSpaceMarkings_15_1.x"],
            self.Columns.PARKINGSPACEMARKINGS_15_1_y: ["AP.envModelPort.parkingSpaceMarkings_15_1.y"],
            self.Columns.GT_DELIMITERX: ["GT.envModelPort.parkingSpaceMarkings._0_.pos_m.array._%_.x_dir"],
            self.Columns.GT_DELIMITERY: ["GT.envModelPort.parkingSpaceMarkings._0_.pos_m.array._%_.y_dir"],
            self.Columns.GT_DELIMITER_0_X: ["GT.envModelPort.parkingSpaceMarkings._0_.pos_m.array._%_.x_dir"],
            self.Columns.GT_DELIMITER_0_Y: ["GT.envModelPort.parkingSpaceMarkings._0_.pos_m.array._%_.y_dir"],
            self.Columns.GT_DELIMITER_1_X: ["GT.envModelPort.parkingSpaceMarkings._1_.pos_m.array._%_.x_dir"],
            self.Columns.GT_DELIMITER_1_Y: ["GT.envModelPort.parkingSpaceMarkings._1_.pos_m.array._%_.y_dir"],
            self.Columns.GT_DELIMITER_2_X: ["GT.envModelPort.parkingSpaceMarkings._2_.pos_m.array._%_.x_dir"],
            self.Columns.GT_DELIMITER_2_Y: ["GT.envModelPort.parkingSpaceMarkings._2_.pos_m.array._%_.y_dir"],
            self.Columns.GT_DELIMITER_3_X: ["GT.envModelPort.parkingSpaceMarkings._3_.pos_m.array._%_.x_dir"],
            self.Columns.GT_DELIMITER_3_Y: ["GT.envModelPort.parkingSpaceMarkings._3_.pos_m.array._%_.y_dir"],
            self.Columns.GT_DELIMITER_4_X: ["GT.envModelPort.parkingSpaceMarkings._4_.pos_m.array._%_.x_dir"],
            self.Columns.GT_DELIMITER_4_Y: ["GT.envModelPort.parkingSpaceMarkings._4_.pos_m.array._%_.y_dir"],
            # self.Columns.STATICOBJECT_ACTUALSIZE: ["GT.envModelPort.staticObjects._%_.objShape_m.actualSize"],
            # "apstates": ["AP.planningCtrlPort.apStates"],
            self.Columns.STATICOBJECT_HEIGHTCLASS: ["GT.envModelPort.staticObjects._%_.objHeightClass_nu"],
            # self.Columns.SGFOUTPUT_STATICOBJECTVERTICESOUTPUT_0_X: ["sgfOutput.staticObjectVerticesOutput.vertices._0_.x"],
            self.Columns.GT_SLOT_P_X_0: ["GT.envModelPort.parkingBoxes._%_.slotCoordinates.0.x_m"],
            self.Columns.GT_SLOT_P_Y_0: ["GT.envModelPort.parkingBoxes._%_.slotCoordinates.0.y_m"],
            self.Columns.GT_SLOT_P_X_1: ["GT.envModelPort.parkingBoxes._%_.slotCoordinates.1.x_m"],
            self.Columns.GT_SLOT_P_Y_1: ["GT.envModelPort.parkingBoxes._%_.slotCoordinates.1.y_m"],
            self.Columns.GT_SLOT_P_X_2: ["GT.envModelPort.parkingBoxes._%_.slotCoordinates.2.x_m"],
            self.Columns.GT_SLOT_P_Y_2: ["GT.envModelPort.parkingBoxes._%_.slotCoordinates.2.y_m"],
            self.Columns.GT_SLOT_P_X_3: ["GT.envModelPort.parkingBoxes._%_.slotCoordinates.3.x_m"],
            self.Columns.GT_SLOT_P_Y_3: ["GT.envModelPort.parkingBoxes._%_.slotCoordinates.3.y_m"],
            self.Columns.GT_MODSLOTS_SLOT_CORNERS_0_x: ["GT.mODSlots._%_.slot_corners._0_.x"],
            self.Columns.GT_MODSLOTS_SLOT_CORNERS_0_y: ["GT.mODSlots._%_.slot_corners._0_.y"],
            self.Columns.GT_MODSLOTS_SLOT_CORNERS_1_x: ["GT.mODSlots._%_.slot_corners._1_.x"],
            self.Columns.GT_MODSLOTS_SLOT_CORNERS_1_y: ["GT.mODSlots._%_.slot_corners._1_.y"],
            self.Columns.GT_MODSLOTS_SLOT_CORNERS_2_x: ["GT.mODSlots._%_.slot_corners._2_.x"],
            self.Columns.GT_MODSLOTS_SLOT_CORNERS_2_y: ["GT.mODSlots._%_.slot_corners._2_.y"],
            self.Columns.GT_MODSLOTS_SLOT_CORNERS_3_x: ["GT.mODSlots._%_.slot_corners._3_.x"],
            self.Columns.GT_MODSLOTS_SLOT_CORNERS_3_y: ["GT.mODSlots._%_.slot_corners._3_.y"],
            ###
            # self.Columns.PARKINGSLOTDETECTIONOUTPUT_SLOTCORNERS_0_X: ["parkingSlotDetectionOutput.parkingSlots_%_.slotCorners._0_.x"],
            # self.Columns.PARKINGSLOTDETECTIONOUTPUT_SLOTCORNERS_0_Y: ["parkingSlotDetectionOutput.parkingSlots_%_.slotCorners._0_.y"],
            # self.Columns.PARKINGSLOTDETECTIONOUTPUT_SLOTCORNERS_1_X: ["parkingSlotDetectionOutput.parkingSlots_%_.slotCorners._1_.x"],
            # self.Columns.PARKINGSLOTDETECTIONOUTPUT_SLOTCORNERS_1_Y: ["parkingSlotDetectionOutput.parkingSlots_%_.slotCorners._1_.y"],
            # self.Columns.PARKINGSLOTDETECTIONOUTPUT_SLOTCORNERS_2_X: ["parkingSlotDetectionOutput.parkingSlots_%_.slotCorners._2_.x"],
            # self.Columns.PARKINGSLOTDETECTIONOUTPUT_SLOTCORNERS_2_Y: ["parkingSlotDetectionOutput.parkingSlots_%_.slotCorners._2_.y"],
            # self.Columns.PARKINGSLOTDETECTIONOUTPUT_SLOTCORNERS_3_X: ["parkingSlotDetectionOutput.parkingSlots_%_.slotCorners._3_.x"],
            # self.Columns.PARKINGSLOTDETECTIONOUTPUT_SLOTCORNERS_3_Y: ["parkingSlotDetectionOutput.parkingSlots_%_.slotCorners._3_.y"],
            ####
            self.Columns.CNNBASEDPARKINGSPACES_PARKINGSLOTS_0_SLOTCORNERS_0_X: [
                "AP.SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_0.x"
            ],
            self.Columns.CNNBASEDPARKINGSPACES_PARKINGSLOTS_0_SLOTCORNERS_0_Y: [
                "AP.SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_0.y"
            ],
            self.Columns.CNNBASEDPARKINGSPACES_PARKINGSLOTS_0_SLOTCORNERS_1_X: [
                "AP.SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_1.x"
            ],
            self.Columns.CNNBASEDPARKINGSPACES_PARKINGSLOTS_0_SLOTCORNERS_1_Y: [
                "AP.SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_1.y"
            ],
            self.Columns.CNNBASEDPARKINGSPACES_PARKINGSLOTS_0_SLOTCORNERS_2_X: [
                "AP.SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_2.x"
            ],
            self.Columns.CNNBASEDPARKINGSPACES_PARKINGSLOTS_0_SLOTCORNERS_2_Y: [
                "AP.SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_2.y"
            ],
            self.Columns.CNNBASEDPARKINGSPACES_PARKINGSLOTS_0_SLOTCORNERS_3_X: [
                "AP.SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_3.x"
            ],
            self.Columns.CNNBASEDPARKINGSPACES_PARKINGSLOTS_0_SLOTCORNERS_3_Y: [
                "AP.SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_3.y"
            ],
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
        # self.environment.testrun.testcase_results
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


class HilClValidationSignals(MDFSignalDefinition):
    """HiL Closed Loop evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        USEER_ACTION = "User_action"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.USEER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
        }


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

    @staticmethod
    def signal_equals(value_list: list, eq_target_value):
        """Return a list of indicies where conditions are met.

        Receive a list as 1st arg, and a target value as 2nd arg.
        Find all indicies where the 1st arg input list value matches the target value.
        Return all such indicies in list format.

        Example: for value_list = [5, 1, 2, 5] and eq_target_value = 5 the result will be [0, 3]

                Args:
                    value_list (list): List of input signal values.
                    eq_target_value (int): Value that will be searched for in the values_list input.

                Returns:
                    list: List of indices where the input list value matches the target value.
        """
        return [i for i, v in enumerate(value_list) if v == eq_target_value]

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

    def AddStatesToEvalString(input_signal, eval_string, input_dict, input_time_signal):
        """
        Function add states of input_signal and time points of events to eval_string.

        Args:
            input_signal (list): List of input signal values.
            eval_string (string): String of evaluation text.
            input_dict (dict): Dictionary of the satets of input_signal.
            input_time_signal (list): List of time.

        """
        states_dict = HilClFuntions.States(input_signal, 0, len(input_signal), 1)
        for key in states_dict:
            actual_value = input_dict.get(states_dict[key])
            actual_number = int(states_dict[key])
            actual_time = input_time_signal[key]

            eval_string += " ".join(f"<br>{actual_value} ({actual_number}) at {actual_time} us".split())

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

    @staticmethod
    def object_generator(obj_size: int, coordinate_list: List[tuple]):
        """
        Generate a 2D geometry with shapely, according to how many points it has.

        Args:
            obj_size (int): how many points was used to describe the object by the system.
            coordinate_list (list[tuple]): the coordinates of the object detected by the system. It has to be
                                           sequential x y coordinate tuples, with a float or integer value for x and y.
            Example:
                first_point = (1.2, 0.3)
                second_point = (1.7, -0.3)
                third_point = (-0.4, 7.3)

                object = object_generator(3, first_point, second_point, third_point)
        """
        if len(coordinate_list) != obj_size:
            raise ValueError(
                f"Error at the input of the object_generator function. The number of points used "
                f"by the system to describe the object: {obj_size} is not equal to the coordinates "
                f"given to the function to calculate the polygons: {len(coordinate_list)}!"
            )

        if obj_size == 1:
            target_object = Point(coordinate_list)
        elif obj_size == 2:
            target_object = LineString(coordinate_list)
        elif obj_size >= 3:
            target_object = Polygon(coordinate_list)
        else:
            target_object = None

        return target_object

    @staticmethod
    def log_exceptions(f):
        """Decorate function 'f' to log exceptions into the log output of the reporting ui for easier debugging.

        Any 'f' function can be decorated, but please note that it was created specifically to decorate the tsf scripts' process() function.
        Error logging -for whatever reason- is absent from the reporting ui's log output window.
        """

        @functools.wraps(f)
        def inner(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception:
                print(f"Exception encountered: {traceback.format_exc()}")

        return inner

    @staticmethod
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

    @staticmethod
    def maneuver_area_check(
        positions_x=None,
        positions_y=None,
        heading_angle=None,
        ego_wheelbase: float = 0,
        ego_length: float = 0,
        ego_rear_overhang: float = 0,
        ego_front_overhang: float = 0,
        ego_width: float = 0,
        left_d: float = 0,
        rear_d: float = 0,
        right_d: float = 0,
        front_d: float = 0,
        parking_pos_x: float = 0,
        parking_pos_y: float = 0,
        parking_heading_angle: float = 0,
        ego_reference_on_bumper: bool = True,
    ):
        """
        Examining if a dynamic object enters the defined static zone.

        Args:
            positions_x (list): List of x coordinates [m] of dynamic object position.
            positions_y (list): List of y coordinates [m] of dynamic object position.
            heading_angle (list): List of heading angle values [rad] of dynamic object position.
            ego_wheelbase (float): Value of the wheelbase of the dynamic object in meters.
                                   Optional, but either ego_wheelbase or ego_length shall be given.
            ego_length (float): Value of the length of the dynamic object in meters.
                                Optional, but either ego_wheelbase or ego_length shall be given.
            ego_rear_overhang (float): Value of the distance between
                                       rear bumper and rear axle of the dynamic object in meters.
            ego_front_overhang (float): Value of the distance between
                                        front bumper and front axle of the dynamic object in meters.
            ego_width (float): Value of the width of the dynamic object in meters.
            left_d (float): Value of left side size of maneuver area based on parking area requirement in meters.
            rear_d (float): Value of rear size of maneuver area based on parking area requirement in meters.
            right_d (float): Value of right side size of maneuver area based on parking area requirement in meters.
            front_d (float): Value of front size of maneuver area based on parking area requirement in meters.
            parking_pos_x (float): X coordinate of the final parking position.
            parking_pos_y (float): Y coordinate of the final parking position.
            parking_heading_angle (list): List of heading angle values [rad] of the final parking position.
            ego_reference_on_bumper (bool): if True, position_x/y points are referring to the middle of rear bumper,
                                            otherwise the middle of rear axle

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

        if ego_reference_on_bumper:
            x_min_offset = 0
            x_max_offset = ego_length
        else:
            x_min_offset = -rear_overhang
            x_max_offset = ego_wheelbase + ego_front_overhang

        maneuvering_area = box(
            parking_pos_x + x_min_offset - rear_d,
            parking_pos_y - ego_width / 2 - right_d,
            parking_pos_x + x_max_offset + front_d,
            parking_pos_y + ego_width / 2 + left_d,
        )
        maneuvering_area = affinity.rotate(
            maneuvering_area, parking_heading_angle, origin=(parking_pos_x, parking_pos_y), use_radians=True
        )

        target_boxes = []
        m_a_multiple = []
        m_a_x, m_a_y = maneuvering_area.exterior.xy
        for i in range(len(result)):
            ego = box(
                positions_x[i] + x_min_offset,
                positions_y[i] - ego_width / 2,
                positions_x[i] + x_max_offset,
                positions_y[i] + ego_width / 2,
            )
            rotated_target = affinity.rotate(
                ego, heading_angle[i], origin=(positions_x[i], positions_y[i]), use_radians=True
            )
            result[i] = difference(rotated_target, maneuvering_area).area == 0
            x_t, y_t = rotated_target.exterior.xy
            target_boxes.append((list(x_t), list(y_t)))
            m_a_multiple.append((list(m_a_x), list(m_a_y)))

        return result, m_a_multiple, target_boxes

    @staticmethod
    def create_slider_graph(
        target_boxes=(),
        wz_polygons=(),
        timestamps=(),
        target_name="EGO",
        wz_name="MANEUVERING AREA",
        target_add_marker=False,
        wz_add_marker=False,
    ):
        """
        Creating a 2D plot for two polygons in the function of time.

        Args:
            target_boxes (list): exterior points of object1 in a list for each measured time instance.
            wz_polygons (list): exterior points of object2 in a list for each measured time instance.
            timestamps (list): Optional, desired timestamps for each measured time instance.
                               If not given, indexes will be used.
            target_name (str): this will be the annotation name of object1 on the final graph.
            wz_name (str): this will be the annotation name of object2 on the final graph.
            target_add_marker (bool): if True, plot-mode of object1 will be "lines+markers", otherwise only "lines"
            wz_add_marker (bool): if True, plot-mode of object2 will be "lines+markers", otherwise only "lines"

        Returns:
            plotly.graph_object: A plot of two dynamic object with a slider
                                 to look for multiple time instances of the scenario.
        """
        plt = go.Figure()

        # reducing number of plots to around 750 --> browsers can handle this much without problem
        if (cut_idx := (len(target_boxes) - 1) // 749) <= 1:
            cut_idx += 1

        target_boxes = list(target_boxes[:-1:cut_idx]) + [target_boxes[-1]]
        wz_polygons = list(wz_polygons[:-1:cut_idx]) + [wz_polygons[-1]]
        timestamps = list(timestamps[:-1:cut_idx]) + [timestamps[-1]]

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
                    name=target_name,
                    # fillcolor='red',
                    line=dict(color="red", width=1),
                    fill="toself",
                    marker=dict(size=10, symbol="x"),
                    mode=f"lines{'+markers' if target_add_marker else ''}",
                    # opacity=0.5
                )
            )

            plt.add_trace(
                go.Scatter(
                    visible=False,
                    x=wz_x,
                    y=wz_y,
                    name=wz_name,
                    # fillcolor='blue',
                    line=dict(color="blue", width=1),
                    fill="toself",
                    marker=dict(size=10, symbol="x"),
                    mode=f"lines{'+markers' if wz_add_marker else ''}",
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
            yaxis=dict(scaleanchor="x"),
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
        IuOdoEstimationPort = "IuOdoEstimationPort_eSigStatus"
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

        self._root = ["AP", "MTA_ADC5"]

        self._properties = [
            (
                self.Columns.MF_VEHICLE_Parameter,
                [
                    ".mfControlConfig.vehicleParams.sSigHeader.eSigStatus",
                    ".MF_TRJCTL_DATA.VehicleParams.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.IuTRJCTLGeneralInputPort,
                [
                    ".trjctlGeneralInputPort.sSigHeader.eSigStatus",
                    ".VDP_DATA.TRJCTLGeneralInputPort.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.IuTrajRequestPort,
                [
                    ".trajRequestPort.sSigHeader.eSigStatus",
                    ".MF_MANAGER_DATA.trajRequestPort.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.MF_SYS_FUNC_Parameter,
                [
                    ".mfControlConfig.sysFuncParams.sSigHeader.eSigStatus",
                    ".MF_TRJCTL_DATA.SysFuncParams.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.IuOdoEstimationPort,
                [
                    ".odoEstimationOutputPort.odoEstimation.sSigHeader.eSigStatus",
                    ".MF_VEDODO_DATA.OdoEstimationOutputPort.odoEstimation.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.MF_FC_TRJCTL_Parameter,
                [
                    ".mfControlConfig.mfcParams.sSigHeader.eSigStatus",
                    ".MF_TRJCTL_DATA.FcTrjctlParams.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.IuLoDMCStatusPort,
                [
                    ".LoDMCStatusPort.sSigHeader.eSigStatus",
                    ".AP_LODMC_DATA.LoDMCStatusPort.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.IuLoCtrlRequestPort,
                [
                    ".loCtrlRequestPort.sSigHeader.eSigStatus",
                    ".MF_MANAGER_DATA.loCtrlRequestPort.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.IuLaDMCStatusPort,
                [
                    ".LaDMCStatusPort.sSigHeader.eSigStatus",
                    ".AP_LODMC_DATA.LaDMCStatusPort.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.IuLaCtrlRequestPort,
                [
                    ".laCtrlRequestPort.sSigHeader.eSigStatus",
                    ".MF_MANAGER_DATA.laCtrlRequestPort.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.IuGearboxCtrlStatusPort,
                [
                    ".gearboxCtrlStatusPort.sSigHeader.eSigStatus",
                    ".VDP_DATA.GearboxCtrlStatusPort.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.IuGearboxCtrlRequestPort,
                [
                    ".IuGearboxCtrlRequestPort.sSigHeader.eSigStatus",
                    ".MF_TRJCTL_DATA.GearboxCtrlRequestPort.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.IuLoDMCCtrlRequestPort,
                [
                    ".LoDMCCtrlRequestPort.sSigHeader.eSigStatus",
                    ".MF_TRJCTL_DATA.LoDMCCtrlRequestPort.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.IuLaDMCCtrlRequestPort,
                [
                    ".IuLaDMCCtrlRequestPort.sSigHeader.eSigStatus",
                    ".MF_TRJCTL_DATA.LaDMCCtrlRequestPort.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.IuMfControlStatusPort,
                [
                    ".mfControlStatusPort.sSigHeader.eSigStatus",
                    ".MF_TRJCTL_DATA.MfControlStatusPort.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.IuDrivingResistancePort,
                [
                    ".DrivingResistancePort.sSigHeader.eSigStatus",
                    ".MF_TRJCTL_DATA.DrivingResistancePort.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.IuTrajCtrlDebugPort,
                [
                    ".IuTrajCtrlDebugPort.sSigHeader.eSigStatus",
                    ".MF_TRJCTL_DATA.TrajCtrlDebugPort.sSigHeader.eSigStatus",
                ],
            ),
        ]


class MoCoSignals(SignalDefinition):
    """Example signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        activateLaCtrl = "activateLaCtrl"
        laDMCCtrlRequest_nu = "laDMCCtrlRequest_nu"
        frontSteerAngReq_rad = "frontSteerAngReq_rad"
        steerAngReqFront_rad = "steerAngReqFront_rad"
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
        steerAngReqRaw_rad = "steerAngReqRaw_rad"
        motionStatus_nu = "motionStatus_nu"
        trajValid_nu = "trajValid_nu"
        numValidCtrlPoints_nu = "numValidCtrlPoints_nu"
        mNumOfReplanCalls = "mNumOfReplanCalls"
        mReplanSuccessful_nu = "mReplanSuccessful_nu"

        xPosition_m = "xPosition_m"
        yPosition_m = "yPosition_m"
        yawAngle_rad = "yawAngle_rad"
        currentDeviation_m = "currentDeviation_m"
        orientationError_rad = "orientationError_rad"
        distance_interface = "distance_interface"
        velocity_interface = "velocity_interface"
        acceleration_interface = "acceleration_interface"
        drivingForwardReq_nu = "drivingForwardReq_nu"
        timestamp = "timestamp"
        lateralControlFinished_nu = "lateralControlFinished_nu"
        lateralPathControlFailed_nu = "lateralPathControlFailed_nu"
        emergencyHoldReq_nu = "emergencyHoldReq_nu"
        vehStandstillSecured_nu = "vehStandstillSecured_nu"
        drivingDirection_nu = "drivingDirection_nu"
        isLastSegment_nu = "isLastSegment_nu"

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
        distanceToStopReq_m_3 = "distanceToStopReq_m_3"
        velocityLimitReq_mps_3 = "velocityLimitReq_mps_3"
        distanceToStopReq_m_4 = "distanceToStopReq_m_4"
        velocityLimitReq_mps_4 = "velocityLimitReq_mps_4"
        distanceToStopReq_m_5 = "distanceToStopReq_m_5"
        velocityLimitReq_mps_5 = "velocityLimitReq_mps_5"
        distanceToStopReq_m_6 = "distanceToStopReq_m_6"
        velocityLimitReq_mps_6= "velocityLimitReq_mps_6"
        distanceToStopReq_m_7 = "distanceToStopReq_m_7"
        velocityLimitReq_mps_7 = "velocityLimitReq_mps_7"
        distanceToStopReq_m_8 = "distanceToStopReq_m_8"
        velocityLimitReq_mps_8 = "velocityLimitReq_mps_8"
        distanceToStopReq_m_9 = "distanceToStopReq_m_9"
        velocityLimitReq_mps_9 = "velocityLimitReq_mps_9"
        distanceToStopReq_m_10 = "distanceToStopReq_m_10"
        velocityLimitReq_mps_10 = "velocityLimitReq_mps_10"
        distanceToStopReq_m_11 = "distanceToStopReq_m_11"
        velocityLimitReq_mps_11 = "velocityLimitReq_mps_11"
        distanceToStopReq_m_12 = "distanceToStopReq_m_12"
        velocityLimitReq_mps_12 = "velocityLimitReq_mps_12"
        distanceToStopReq_m_13 = "distanceToStopReq_m_13"
        velocityLimitReq_mps_13 = "velocityLimitReq_mps_13"
        distanceToStopReq_m_14 = "distanceToStopReq_m_14"
        velocityLimitReq_mps_14 = "velocityLimitReq_mps_14"
        distanceToStopReq_m_15 = "distanceToStopReq_m_15"
        velocityLimitReq_mps_15 = "velocityLimitReq_mps_15"
        distanceToStopReq_m_16 = "distanceToStopReq_m_16"
        velocityLimitReq_mps_16 = "velocityLimitReq_mps_16"
        distanceToStopReq_m_17 = "distanceToStopReq_m_17"
        velocityLimitReq_mps_17 = "velocityLimitReq_mps_17"
        distanceToStopReq_m_18 = "distanceToStopReq_m_18"
        velocityLimitReq_mps_18 = "velocityLimitReq_mps_18"
        distanceToStopReq_m_19 = "distanceToStopReq_m_19"
        velocityLimitReq_mps_19 = "velocityLimitReq_mps_19"
        crvRARReq_1pm_0 = "crvRARReq_1pm_0"
        crvRARReq_1pm_1 = "crvRARReq_1pm_1"
        crvRARReq_1pm_2 = "crvRARReq_1pm_2"
        crvRARReq_1pm_3 = "crvRARReq_1pm_3"
        crvRARReq_1pm_4 = "crvRARReq_1pm_4"
        crvRARReq_1pm_5 = "crvRARReq_1pm_5"
        crvRARReq_1pm_6 = "crvRARReq_1pm_6"
        crvRARReq_1pm_7 = "crvRARReq_1pm_7"
        crvRARReq_1pm_8 = "crvRARReq_1pm_8"
        crvRARReq_1pm_9 = "crvRARReq_1pm_9"
        crvRARReq_1pm_10 = "crvRARReq_1pm_10"
        crvRARReq_1pm_11 = "crvRARReq_1pm_11"
        crvRARReq_1pm_12 = "crvRARReq_1pm_12"
        crvRARReq_1pm_13 = "crvRARReq_1pm_13"
        crvRARReq_1pm_14 = "crvRARReq_1pm_14"
        crvRARReq_1pm_15 = "crvRARReq_1pm_15"
        crvRARReq_1pm_16 = "crvRARReq_1pm_16"
        crvRARReq_1pm_17 = "crvRARReq_1pm_17"
        crvRARReq_1pm_18 = "crvRARReq_1pm_18"
        crvRARReq_1pm_19 = "crvRARReq_1pm_19"

        xTrajRAReq_m_19 = "xTrajRAReq_m_19"
        yTrajRAReq_m_19 = "yTrajRAReq_m_19"
        xTrajRAReq_m_18 = "xTrajRAReq_m_18"
        yTrajRAReq_m_18 = "yTrajRAReq_m_18"
        longiVelocity_mps = "longiVelocity_mps"
        newSegmentStarted_nu = "newSegmentStarted_nu"
        distanceToStopReq_m = "distanceToStopReq_m"
        distanceToStopReqInterExtrapolTraj_m = "distanceToStopReqInterExtrapolTraj_m"
        velocityLimitReq_mps = "velocityLimitReq_mps"
        velocityLimitReqInterpolTraj_mps = "velocityLimitReqInterpolTraj_mps"
        xInterpolTraj_m = "xInterpolTraj_m"
        yInterpolTraj_m = "yInterpolTraj_m"
        trajIntermediateValueRaw_perc = "trajIntermediateValueRaw_perc"
        longitudinalPathControlFailed_nu = "longitudinalPathControlFailed_nu"

        distance_m_0 = "distance_m_0"
        distance_m_1 = "distance_m_1"
        distance_m_2 = "distance_m_2"
        distance_m_3 = "distance_m_3"
        drivingResistance_FL = "drivingResistance_FL"
        drivingResistance_RL = "drivingResistance_RL"
        drivingResistance_RR = "drivingResistance_RR"
        drivingResistance_FR = "drivingResistance_FR"
        drivingResistanceType_0 = "drivingResistanceType_0"
        drivingResistanceType_1 = "drivingResistanceType_1"
        drivingResistanceType_2 = "drivingResistanceType_2"
        drivingResistanceType_3 = "drivingResistanceType_3"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "MTA_ADC5"]

        self._properties = [
            (
                self.Columns.activateLaCtrl,
                [
                    ".laCtrlRequestPort.activateLaCtrl",
                    ".MF_MANAGER_DATA.laCtrlRequestPort.activateLaCtrl",
                ],
            ),
            (
                self.Columns.laDMCCtrlRequest_nu,
                [
                    ".laDMCCtrlRequestPort.laDMCCtrlRequest_nu",
                    ".MF_TRJCTL_DATA.LaDMCCtrlRequestPort.laDMCCtrlRequest_nu",
                ],
            ),
            (
                self.Columns.frontSteerAngReq_rad,
                [
                    ".laDMCCtrlRequestPort.frontSteerAngReq_rad",
                    ".MF_TRJCTL_DATA.LaDMCCtrlRequestPort.frontSteerAngReq_rad",
                ],
            ),
            (
                self.Columns.steerAngReqFront_rad,
                [
                    ".laCtrlRequestPort.steerAngReqFront_rad",
                    ".MF_MANAGER_DATA.laCtrlRequestPort.steerAngReqFront_rad",
                ],
            ),
            (
                self.Columns.activateLoCtrl,
                [
                    ".loCtrlRequestPort.activateLoCtrl",
                    ".MF_MANAGER_DATA.loCtrlRequestPort.activateLoCtrl",
                ],
            ),
            (
                self.Columns.loDMCCtrlRequest_nu,
                [
                    ".LoDMCCtrlRequestPort.loDMCCtrlRequest_nu",
                    ".MF_TRJCTL_DATA.LoDMCCtrlRequestPort.loDMCCtrlRequest_nu",
                ],
            ),
            (
                self.Columns.gearboxCtrlRequest_nu,
                [
                    ".gearBoxCtrlRequestPort.gearboxCtrlRequest_nu",
                    ".MF_TRJCTL_DATA.GearboxCtrlRequestPort.gearboxCtrlRequest_nu",
                ],
            ),
            (
                self.Columns.holdReq_nu,
                [
                    ".LoDMCCtrlRequestPort.holdReq_nu",
                    ".MF_TRJCTL_DATA.LoDMCCtrlRequestPort.holdReq_nu",
                ],
            ),
            (
                self.Columns.maneuveringFinished_nu,
                [
                    ".LoDMCStatusPort.maneuveringFinished_nu",
                    ".AP_LODMC_DATA.LoDMCStatusPort.maneuveringFinished_nu",
                ],
            ),
            (
                self.Columns.gearCur_nu,
                [
                    ".gearboxCtrlStatusPort.gearInformation.gearCur_nu",
                    ".VDP_DATA.GearboxCtrlStatusPort.gearInformation.gearCur_nu",
                ],
            ),
            (
                self.Columns.currentDeviation_m,
                [
                    ".trajCtrlDebugPort.currentDeviation_m",
                    ".MF_TRJCTL_DATA.TrajCtrlDebugPort.currentDeviation_m",
                ],
            ),
            (
                self.Columns.comfortStopRequest,
                [
                    ".loCtrlRequestPort.comfortStopRequest",
                    ".MF_MANAGER_DATA.loCtrlRequestPort.comfortStopRequest",
                ],
            ),
            (
                self.Columns.requestedValue,
                [
                    ".loCtrlRequestPort.distanceToStopReq_m.requestedValue",
                    ".MF_MANAGER_DATA.loCtrlRequestPort.distanceToStopReq_m.requestedValue",
                ],
            ),
            (
                self.Columns.secureInStandstill,
                [
                    ".loCtrlRequestPort.secureInStandstill",
                    ".MF_MANAGER_DATA.loCtrlRequestPort.secureInStandstill",
                ],
            ),
            (
                self.Columns.standstillHoldCur_nu,
                [
                    ".LoDMCStatusPort.standstillHoldCur_nu",
                    ".AP_LODMC_DATA.LoDMCStatusPort.standstillHoldCur_nu",
                ],
            ),
            (
                self.Columns.standstillSecureCur_nu,
                [
                    ".LoDMCStatusPort.standstillSecureCur_nu",
                    ".AP_LODMC_DATA.LoDMCStatusPort.standstillSecureCur_nu",
                ],
            ),
            (
                self.Columns.loCtrlRequestType,
                [
                    ".loCtrlRequestPort.loCtrlRequestType",
                    ".MF_MANAGER_DATA.loCtrlRequestPort.loCtrlRequestType",
                ],
            ),
            (
                self.Columns.laCtrlRequestType,
                [
                    ".laCtrlRequestPort.laCtrlRequestType",
                    ".MF_MANAGER_DATA.laCtrlRequestPort.laCtrlRequestType",
                ],
            ),
            (
                self.Columns.steerAngFrontAxle_rad,
                [
                    ".odoEstimationOutputPort.odoEstimation.steerAngFrontAxle_rad",
                    ".MF_VEDODO_DATA.OdoEstimationOutputPort.odoEstimation.steerAngFrontAxle_rad",
                ],
            ),
            (
                self.Columns.steerAngReqRaw_rad,
                [
                    ".trajCtrlDebugPort.steerAngReqRaw_rad",
                    ".MF_TRJCTL_DATA.TrajCtrlDebugPort.steerAngReqRaw_rad",
                ],
            ),
            (
                self.Columns.motionStatus_nu,
                [
                    ".odoEstimationOutputPort.odoEstimation.motionStatus_nu",
                    ".MF_VEDODO_DATA.OdoEstimationOutputPort.odoEstimation.motionStatus_nu",
                ],
            ),
            (
                self.Columns.trajValid_nu,
                [
                    ".trajRequestPort.trajValid_nu",
                    ".MF_MANAGER_DATA.trajRequestPort.trajValid_nu",
                ],
            ),
                (
                self.Columns.numValidCtrlPoints_nu,
                [
                    ".trajRequestPort.numValidCtrlPoints_nu",
                    ".MF_MANAGER_DATA.trajRequestPort.numValidCtrlPoints_nu",
                ],
            ),
            (
                self.Columns.mNumOfReplanCalls,
                [
                    ".trajPlanDebugPort.mNumOfReplanCalls",
                    ".MF_TRJPLA_DATA.trjplaDebugPort.mNumOfReplanCalls",
                ],
            ),
            (
                self.Columns.mReplanSuccessful_nu,
                [
                    ".trajPlanDebugPort.mReplanSuccessful_nu",
                    ".MF_TRJPLA_DATA.trjplaDebugPort.mReplanSuccessful_nu",
                ],
            ),
            (
                self.Columns.numValidCtrlPoints_nu,
                [
                    ".trajRequestPort.numValidCtrlPoints_nu",
                    ".MF_MANAGER_DATA.trajRequestPort.numValidCtrlPoints_nu",
                ],
            ),
            (
                self.Columns.mNumOfReplanCalls,
                [
                    ".trajPlanDebugPort.mNumOfReplanCalls",
                    ".MF_TRJPLA_DATA.trjplaDebugPort.mNumOfReplanCalls",
                ],
            ),
            (
                self.Columns.mReplanSuccessful_nu,
                [
                    ".trajPlanDebugPort.mReplanSuccessful_nu",
                    ".MF_TRJPLA_DATA.trjplaDebugPort.mReplanSuccessful_nu",
                ],
            ),
            (
                self.Columns.xPosition_m,
                [
                    ".odoEstimationOutputPort.odoEstimation.xPosition_m",
                    ".MF_VEDODO_DATA.OdoEstimationOutputPort.odoEstimation.xPosition_m",
                ],
            ),
            (
                self.Columns.yPosition_m,
                [
                    ".odoEstimationOutputPort.odoEstimation.yPosition_m",
                    ".MF_VEDODO_DATA.OdoEstimationOutputPort.odoEstimation.yPosition_m",
                ],
            ),
            (
                self.Columns.yawAngle_rad,
                [
                    ".odoEstimationOutputPort.odoEstimation.yawAngle_rad",
                    ".MF_VEDODO_DATA.OdoEstimationOutputPort.odoEstimation.yawAngle_rad",
                ],
            ),
            (
                self.Columns.orientationError_rad,
                [
                    ".trajCtrlDebugPort.orientationError_rad",
                    ".MF_TRJCTL_DATA.TrajCtrlDebugPort.orientationError_rad",
                ],
            ),
            (
                self.Columns.distance_interface,
                [
                    ".loCtrlRequestPort.distanceToStopReq_m.drivingDirRequest",
                    ".MF_MANAGER_DATA.loCtrlRequestPort.distanceToStopReq_m.drivingDirRequest",
                ],
            ),
            (
                self.Columns.velocity_interface,
                [
                    ".loCtrlRequestPort.velocityReq_mps.drivingDirRequest",
                    ".MF_MANAGER_DATA.loCtrlRequestPort.velocityReq_mps.drivingDirRequest",
                ],
            ),
            (
                self.Columns.acceleration_interface,
                [
                    ".loCtrlRequestPort.accelerationReq_mps2.drivingDirRequest",
                    ".MF_MANAGER_DATA.loCtrlRequestPort.accelerationReq_mps2.drivingDirRequest",
                ],
            ),
            (
                self.Columns.drivingForwardReq_nu,
                [
                    ".trajRequestPort.drivingForwardReq_nu",
                    ".MF_MANAGER_DATA.trajRequestPort.drivingForwardReq_nu",
                ],
            ),
            (
                self.Columns.timestamp,
                [
                    ".odoInputPort.odoSigFcanPort.vehDynamics.timestamp_us",
                    ".MF_VEDODO_DATA.OdoEstimationOutputPort.odoEstimation.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.xTrajRAReq_m_0,
                [
                    ".trajRequestPort.plannedTraj_0.xTrajRAReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[0].xTrajRAReq_m",
                ],
            ),
            (
                self.Columns.yTrajRAReq_m_0,
                [
                    ".trajRequestPort.plannedTraj_0.yTrajRAReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[0].yTrajRAReq_m",
                ],
            ),
            (
                self.Columns.yawReq_rad_0,
                [
                    ".trajRequestPort.plannedTraj_0.yawReq_rad",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[0].yawReq_rad",
                ],
            ),
            (
                self.Columns.crvRAReq_1pm,
                [
                    ".plannedTrajDrivenPoint.crvRAReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[0].crvRAReq_1pm",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_0,
                [
                    ".trajRequestPort.plannedTraj_0.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[0].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_0,
                [
                    ".trajRequestPort.plannedTraj_0.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[0].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.xTrajRAReq_m_1,
                [
                    ".trajRequestPort.plannedTraj_1.xTrajRAReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[1].xTrajRAReq_m",
                ],
            ),
            (
                self.Columns.yTrajRAReq_m_1,
                [
                    ".trajRequestPort.plannedTraj_1.yTrajRAReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[1].yTrajRAReq_m",
                ],
            ),
            (
                self.Columns.yawReq_rad_1,
                [
                    ".trajRequestPort.plannedTraj_1.yawReq_rad",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[1].yawReq_rad",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_1,
                [
                    ".trajRequestPort.plannedTraj_1.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[1].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_1,
                [
                    ".trajRequestPort.plannedTraj_1.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[1].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.xTrajRAReq_m_2,
                [
                    ".trajRequestPort.plannedTraj_2.xTrajRAReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[2].xTrajRAReq_m",
                ],
            ),
            (
                self.Columns.yTrajRAReq_m_2,
                [
                    ".trajRequestPort.plannedTraj_2.yTrajRAReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[2].yTrajRAReq_m",
                ],
            ),
            (
                self.Columns.yawReq_rad_2,
                [
                    ".trajRequestPort.plannedTraj_2.yawReq_rad",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[2].yawReq_rad",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_2,
                [
                    ".trajRequestPort.plannedTraj_2.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[2].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_2,
                [
                    ".trajRequestPort.plannedTraj_2.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[2].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_3,
                [
                    ".trajRequestPort.plannedTraj_3.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[3].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_3,
                [
                    ".trajRequestPort.plannedTraj_3.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[3].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_4,
                [
                    ".trajRequestPort.plannedTraj_4.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[4].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_4,
                [
                    ".trajRequestPort.plannedTraj_4.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[4].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_5,
                [
                    ".trajRequestPort.plannedTraj_5.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[5].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_5,
                [
                    ".trajRequestPort.plannedTraj_5.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[5].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_6,
                [
                    ".trajRequestPort.plannedTraj_6.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[6].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_6,
                [
                    ".trajRequestPort.plannedTraj_6.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[6].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_7,
                [
                    ".trajRequestPort.plannedTraj_7.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[7].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_7,
                [
                    ".trajRequestPort.plannedTraj_7.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[7].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_8,
                [
                    ".trajRequestPort.plannedTraj_8.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[8].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_8,
                [
                    ".trajRequestPort.plannedTraj_8.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[8].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_9,
                [
                    ".trajRequestPort.plannedTraj_9.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[9].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_9,
                [
                    ".trajRequestPort.plannedTraj_9.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[9].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_10,
                [
                    ".trajRequestPort.plannedTraj_10.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[10].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_10,
                [
                    ".trajRequestPort.plannedTraj_10.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[10].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_11,
                [
                    ".trajRequestPort.plannedTraj_11.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[11].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_11,
                [
                    ".trajRequestPort.plannedTraj_11.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[11].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_12,
                [
                    ".trajRequestPort.plannedTraj_12.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[12].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_12,
                [
                    ".trajRequestPort.plannedTraj_12.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[12].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_13,
                [
                    ".trajRequestPort.plannedTraj_13.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[13].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_13,
                [
                    ".trajRequestPort.plannedTraj_13.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[13].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_14,
                [
                    ".trajRequestPort.plannedTraj_14.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[14].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_14,
                [
                    ".trajRequestPort.plannedTraj_14.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[14].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_11,
                [
                    ".trajRequestPort.plannedTraj_11.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[11].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_11,
                [
                    ".trajRequestPort.plannedTraj_11.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[11].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_15,
                [
                    ".trajRequestPort.plannedTraj_15.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[15].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_15,
                [
                    ".trajRequestPort.plannedTraj_15.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[15].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_16,
                [
                    ".trajRequestPort.plannedTraj_16.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[16].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_16,
                [
                    ".trajRequestPort.plannedTraj_16.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[16].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_17,
                [
                    ".trajRequestPort.plannedTraj_17.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[17].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_17,
                [
                    ".trajRequestPort.plannedTraj_17.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[17].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_18,
                [
                    ".trajRequestPort.plannedTraj_18.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[18].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_18,
                [
                    ".trajRequestPort.plannedTraj_18.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[18].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m_19,
                [
                    ".trajRequestPort.plannedTraj_19.distanceToStopReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[19].distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps_19,
                [
                    ".trajRequestPort.plannedTraj_19.velocityLimitReq_mps",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[19].velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.crvRARReq_1pm_0,
                [
                    ".trajRequestPort.plannedTraj_0.crvRARReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[0].crvRARReq_1pm",
                ],
            ),
            (
                self.Columns.crvRARReq_1pm_1,
                [
                    ".trajRequestPort.plannedTraj_1.crvRARReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[1].crvRARReq_1pm",
                ],
            ),
            (
                self.Columns.crvRARReq_1pm_2,
                [
                    ".trajRequestPort.plannedTraj_2.crvRARReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[2].crvRARReq_1pm",
                ],
            ),
            (
                self.Columns.crvRARReq_1pm_3,
                [
                    ".trajRequestPort.plannedTraj_3.crvRARReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[3].crvRARReq_1pm",
                ],
            ),
            (
                self.Columns.crvRARReq_1pm_4,
                [
                    ".trajRequestPort.plannedTraj_4.crvRARReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[4].crvRARReq_1pm",
                ],
            ),
            (
                self.Columns.crvRARReq_1pm_5,
                [
                    ".trajRequestPort.plannedTraj_5.crvRARReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[5].crvRARReq_1pm",
                ],
            ),
            (
                self.Columns.crvRARReq_1pm_6,
                [
                    ".trajRequestPort.plannedTraj_6.crvRARReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[6].crvRARReq_1pm",
                ],
            ),
            (
                self.Columns.crvRARReq_1pm_7,
                [
                    ".trajRequestPort.plannedTraj_7.crvRARReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[7].crvRARReq_1pm",
                ],
            ),
            (
                self.Columns.crvRARReq_1pm_8,
                [
                    ".trajRequestPort.plannedTraj_8.crvRARReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[8].crvRARReq_1pm",
                ],
            ),
            (
                self.Columns.crvRARReq_1pm_9,
                [
                    ".trajRequestPort.plannedTraj_9.crvRARReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[9].crvRARReq_1pm",
                ],
            ),
            (
                self.Columns.crvRARReq_1pm_10,
                [
                    ".trajRequestPort.plannedTraj_10.crvRARReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[10].crvRARReq_1pm",
                ],
            ),
            (
                self.Columns.crvRARReq_1pm_11,
                [
                    ".trajRequestPort.plannedTraj_11.crvRARReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[11].crvRARReq_1pm",
                ],
            ),
            (
                self.Columns.crvRARReq_1pm_12,
                [
                    ".trajRequestPort.plannedTraj_12.crvRARReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[12].crvRARReq_1pm",
                ],
            ),
            (
                self.Columns.crvRARReq_1pm_13,
                [
                    ".trajRequestPort.plannedTraj_13.crvRARReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[13].crvRARReq_1pm",
                ],
            ),
            (
                self.Columns.crvRARReq_1pm_14,
                [
                    ".trajRequestPort.plannedTraj_14.crvRARReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[14].crvRARReq_1pm",
                ],
            ),
            (
                self.Columns.crvRARReq_1pm_15,
                [
                    ".trajRequestPort.plannedTraj_15.crvRARReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[15].crvRARReq_1pm",
                ],
            ),
            (
                self.Columns.crvRARReq_1pm_16,
                [
                    ".trajRequestPort.plannedTraj_16.crvRARReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[16].crvRARReq_1pm",
                ],
            ),
            (
                self.Columns.crvRARReq_1pm_17,
                [
                    ".trajRequestPort.plannedTraj_17.crvRARReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[17].crvRARReq_1pm",
                ],
            ),
            (
                self.Columns.crvRARReq_1pm_18,
                [
                    ".trajRequestPort.plannedTraj_18.crvRARReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[18].crvRARReq_1pm",
                ],
            ),
            (
                self.Columns.crvRARReq_1pm_19,
                [
                    ".trajRequestPort.plannedTraj_19.crvRARReq_1pm",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[19].crvRARReq_1pm",
                ],
            ),
            (
                self.Columns.lateralControlFinished_nu,
                [
                    ".mfControlStatusPort.lateralControlFinished_nu",
                    ".MF_TRJCTL_DATA.MfControlStatusPort.lateralControlFinished_nu",
                ],
            ),
            (
                self.Columns.lateralPathControlFailed_nu,
                [
                    ".mfControlStatusPort.lateralPathControlFailed_nu",
                    ".MF_TRJCTL_DATA.MfControlStatusPort.lateralPathControlFailed_nu",
                ],
            ),
            (
                self.Columns.emergencyHoldReq_nu,
                [
                    ".LoDMCCtrlRequestPort.emergencyHoldReq_nu",
                    ".MF_TRJCTL_DATA.loDMCCtrlRequestPort.emergencyHoldReq_nu",
                ],
            ),
            (
                self.Columns.vehStandstillSecured_nu,
                [
                    ".mfControlStatusPort.vehStandstillSecured_nu",
                    ".MF_TRJCTL_DATA.MfControlStatusPort.vehStandstillSecured_nu",
                ],
            ),
            (
                self.Columns.drivingDirection_nu,
                [
                    ".odoEstimationOutputPort.odoEstimation.drivingDirection_nu",
                    ".MF_VEDODO_DATA.OdoEstimationOutputPort.odoEstimation.drivingDirection_nu",
                ],
            ),
                (
                self.Columns.isLastSegment_nu,
                [
                    ".trajRequestPort.isLastSegment_nu",
                    ".MF_MANAGER_DATA.trajRequestPort.isLastSegment_nu",
                ],
            ),

            (
                self.Columns.longiVelocity_mps,
                [
                    ".odoEstimationOutputPort.odoEstimation.longiVelocity_mps",
                    ".MF_VEDODO_DATA.OdoEstimationOutputPort.odoEstimation.longiVelocity_mps",
                ],
            ),
            (
                self.Columns.newSegmentStarted_nu,
                [
                    ".trajRequestPort.newSegmentStarted_nu",
                    ".MF_MANAGER_DATA.trajRequestPort.newSegmentStarted_nu",
                ],
            ),
            (
                self.Columns.distanceToStopReq_m,
                [
                    ".LoDMCCtrlRequestPort.distanceToStopReq_m",
                    ".MF_TRJCTL_DATA.LoDMCCtrlRequestPort.distanceToStopReq_m",
                ],
            ),
            (
                self.Columns.distanceToStopReqInterExtrapolTraj_m,
                [
                    ".trajCtrlDebugPort.distanceToStopReqInterExtrapolTraj_m",
                    ".MF_TRJCTL_DATA.TrajCtrlDebugPort.distanceToStopReqInterExtrapolTraj_m",
                ],
            ),
            (
                self.Columns.velocityLimitReq_mps,
                [
                    ".LoDMCCtrlRequestPort.velocityLimitReq_mps",
                    ".MF_TRJCTL_DATA.LoDMCCtrlRequestPort.velocityLimitReq_mps",
                ],
            ),
            (
                self.Columns.velocityLimitReqInterpolTraj_mps,
                [
                    ".trajCtrlDebugPort.velocityLimitReqInterpolTraj_mps",
                    ".MF_TRJCTL_DATA.TrajCtrlDebugPort.velocityLimitReqInterpolTraj_mps",
                ],
            ),
            (
                self.Columns.xInterpolTraj_m,
                [
                    ".trajCtrlDebugPort.xInterpolTraj_m",
                    ".MF_TRJCTL_DATA.TrajCtrlDebugPort.xInterpolTraj_m",
                ],
            ),
            (
                self.Columns.yInterpolTraj_m,
                [
                    ".trajCtrlDebugPort.yInterpolTraj_m",
                    ".MF_TRJCTL_DATA.TrajCtrlDebugPort.yInterpolTraj_m",
                ],
            ),
            (
                self.Columns.trajIntermediateValueRaw_perc,
                [
                    ".trajCtrlDebugPort.trajIntermediateValueRaw_perc",
                    ".MF_TRJCTL_DATA.TrajCtrlDebugPort.trajIntermediateValueRaw_perc",
                ],
            ),
            (
                self.Columns.longitudinalPathControlFailed_nu,
                [
                    ".mfControlStatusPort.longitudinalPathControlFailed_nu",
                    # Not present in rec extractor
                    ".MF_TRJCTL_DATA.MfControlStatusPort.longitudinalPathControlFailed_nu",
                ],
            ),
            (
                self.Columns.xTrajRAReq_m_19,
                [
                    ".trajRequestPort.plannedTraj_19.xTrajRAReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[19].xTrajRAReq_m",
                ],
            ),
            (
                self.Columns.yTrajRAReq_m_19,
                [
                    ".trajRequestPort.plannedTraj_19.yTrajRAReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[19].yTrajRAReq_m",
                ],
            ),
            (
                self.Columns.xTrajRAReq_m_18,
                [
                    ".trajRequestPort.plannedTraj_18.xTrajRAReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[18].xTrajRAReq_m",
                ],
            ),
            (
                self.Columns.yTrajRAReq_m_18,
                [
                    ".trajRequestPort.plannedTraj_18.yTrajRAReq_m",
                    ".MF_MANAGER_DATA.trajRequestPort.plannedTraj[18].yTrajRAReq_m",
                ],
            ),
            (
                self.Columns.distance_m_0,
                [
                    ".trajRequestPort.drivingResistance_0.distance_m",
                    ".MF_MANAGER_DATA.trajRequestPort.drivingResistance_0.distance_m",
                ],
            ),
            (
                self.Columns.distance_m_1,
                [
                    ".trajRequestPort.drivingResistance_1.distance_m",
                    ".MF_MANAGER_DATA.trajRequestPort.drivingResistance_1.distance_m",
                ],
            ),
            (
                self.Columns.distance_m_2,
                [
                    ".trajRequestPort.drivingResistance_2.distance_m",
                    ".MF_MANAGER_DATA.trajRequestPort.drivingResistance_2.distance_m",
                ],
            ),
            (
                self.Columns.distance_m_3,
                [
                    ".trajRequestPort.drivingResistance_3.distance_m",
                    ".MF_MANAGER_DATA.trajRequestPort.drivingResistance_3.distance_m",
                ],
            ),
            (
                self.Columns.drivingResistance_FL,
                [
                    ".DrivingResistancePort.distanceFL",
                    ".MF_TRJCTL_DATA.DrivingResistancePort.drivingResistance_FL.distance_m",
                ],
            ),
            (
                self.Columns.drivingResistance_RL,
                [
                    ".DrivingResistancePort.distanceRL",
                    ".MF_TRJCTL_DATA.DrivingResistancePort.drivingResistance_RL.distance_m",
                ],
            ),
            (
                self.Columns.drivingResistance_RR,
                [
                    ".DrivingResistancePort.distanceRR",
                    ".MF_TRJCTL_DATA.DrivingResistancePort.drivingResistance_RR.distance_m",
                ],
            ),
            (
                self.Columns.drivingResistance_FR,
                [
                    ".DrivingResistancePort.distanceFR",
                    ".MF_TRJCTL_DATA.DrivingResistancePort.drivingResistance_FR.distance_m",
                ],
            ),
            (
                self.Columns.drivingResistanceType_0,
                [
                    ".trajRequestPort.drivingResistance_0.type_nu",
                    ".MF_MANAGER_DATA.trajRequestPort.drivingResistance_0.type_nu",
                ],
            ),
            (
                self.Columns.drivingResistanceType_1,
                [
                    ".trajRequestPort.drivingResistance_1.type_nu",
                    ".MF_MANAGER_DATA.trajRequestPort.drivingResistance_1.type_nu",
                ],
            ),
            (
                self.Columns.drivingResistanceType_2,
                [
                    ".trajRequestPort.drivingResistance_2.type_nu",
                    ".MF_MANAGER_DATA.trajRequestPort.drivingResistance_2.type_nu",
                ],
            ),
            (
                self.Columns.drivingResistanceType_3,
                [
                    ".trajRequestPort.drivingResistance_3.type_nu",
                    ".MF_MANAGER_DATA.trajRequestPort.drivingResistance_3.type_nu",
                ],
            ),
        ]


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
        # self.environment.testrun.testcase_results
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
    Example of application:
    df["status"] = screen_nu.apply(lambda x: fh.get_status_label(x, constants.RootCauseAnalysis))

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


def get_parking_type_from_file_path(file_path):
    """Define the dictionary mapping use case IDs to parking types"""
    parking_type_dict = {
        "AP_UC_001": "Parallel",
        "AP_UC_002": "Parallel",
        "AP_UC_011": "Parallel",
        "AP_UC_003": "Parallel",
        "AP_UC_004": "Parallel",
        "AP_UC_005": "Parallel",
        "AP_UC_006": "Parallel",
        "AP_UC_007": "Parallel",
        "AP_UC_008": "Parallel",
        "AP_UC_009": "Parallel",
        "AP_UC_010": "Parallel",
        "AP_UC_012": "Parallel",
        "AP_UC_013": "Parallel",
        "AP_UC_014": "Parallel",
        "AP_UC_015": "Parallel",
        "AP_UC_016": "Parallel",
        "AP_UC_017": "Parallel",
        "AP_UC_018": "Perpendicular",
        "AP_UC_019": "Perpendicular",
        "AP_UC_020_01": "Perpendicular_backward",
        "AP_UC_020_02": "Perpendicular_forward",
        "AP_UC_021": "Perpendicular",
        "AP_UC_022": "Perpendicular",
        "AP_UC_023": "Perpendicular",
        "AP_UC_059": "Perpendicular",
        "AP_UC_024": "Perpendicular",
        "AP_UC_025": "Perpendicular",
        "AP_UC_026": "Perpendicular",
        "AP_UC_027": "Perpendicular",
        "AP_UC_028": "Perpendicular",
        "AP_UC_029": "Perpendicular",
        "AP_UC_031": "Perpendicular",
        "AP_UC_032": "Perpendicular",
        "AP_UC_033": "Perpendicular",
        "AP_UC_034": "Perpendicular",
        "AP_UC_035": "Perpendicular",
        "AP_UC_036": "Perpendicular",
        "AP_UC_037": "Perpendicular",
        "AP_UC_068": "Perpendicular",
        "AP_UC_069": "Perpendicular",
        "AP_UC_038": "Angular",
        "AP_UC_070": "Angular",
        "AP_UC_039": "Angular",
        "AP_UC_71": "Angular",
        "AP_UC_040": "Angular",
        "AP_UC_041": "Angular",
        "AP_UC_044": "Angular",
        "AP_UC_060": "Angular",
        "AP_UC_061": "Angular",
        "AP_UC_100": "Unknown",
        "AP_UC_101": "Unknown",
        "AP_UC_102": "Unknown",
        "AP_UC_103": "Unknown",
        "AP_UC_104": "Unknown",
        "AP_UC_105": "Unknown",
        "AP_UC_106": "Unknown",
        "AP_UC_045": "Unknown",
        "AP_UC_046": "Unknown",
        "AP_UC_047": "Unknown",
        "AP_UC_048": "Unknown",
        "AP_UC_049": "Unknown",
        "AP_UC_050": "Unknown",
        "AP_UC_051": "Unknown",
        "AP_UC_052": "Unknown",
        "AP_UC_053": "Unknown",
        "AP_UC_054": "Unknown",
        "AP_UC_055": "Unknown",
        "AP_UC_056": "Unknown",
        "AP_UC_057": "Unknown",
        "AP_UC_058": "Unknown",
    }

    # Use a regular expression to find the use case ID in the file path
    match = re.search(r"AP_UC_\d+", file_path)
    if match:
        usecase_id = match.group()
        if usecase_id == "AP_UC_020":
            # Perform a supplementary search to determine if it is "AP_UC_020_01" or "AP_UC_020_02"
            sup_match = re.search(r"AP_UC_020_\d{2}", file_path)
            if sup_match:
                usecase_id = sup_match.group()
            else:
                return "Unknown"
    else:
        return "Unknown"
    # Regular expression patterns to identify backward and forward parking
    backward_pattern = re.compile(r"AP_UC_(018|025|070|71|102|104|106)")
    forward_pattern = re.compile(r"AP_UC_(019|026|038|039|101|103|105)")
    park_type = parking_type_dict.get(usecase_id, "Unknown")
    if backward_pattern.match(usecase_id):
        park_type += " backward"
    elif forward_pattern.match(usecase_id):
        park_type += " forward"

    # Return the parking type if the use case ID is found in the dictionary, else return "Unknown"
    return park_type


def get_time_intervals_with_indices(cycle_counter, threshold=1):
    """
    Identify time intervals and their indices in non-continuous cycle counter data.

    :param cycle_counter: List of cycle counter values (assumed to be sorted).
    :param threshold: Difference threshold to identify gaps in the cycle counter.
    :return: List of time intervals, each represented as a dictionary with 'start', 'end', 'start_index', and 'end_index'.
    """
    if not cycle_counter:
        return []

    intervals = []
    start = cycle_counter[0]
    start_index = 0
    previous = cycle_counter[0]

    for i, current in enumerate(cycle_counter[1:], start=1):
        if current - previous > threshold:
            intervals.append({"start": start, "end": previous, "start_index": start_index, "end_index": i - 1})
            start = current
            start_index = i
        previous = current

    intervals.append({"start": start, "end": previous, "start_index": start_index, "end_index": len(cycle_counter) - 1})
    return intervals


def create_rects(time_intervals, final_df):
    """
    Returns:
    list of dict: List of rectangles represented as dictionaries with 'x_min', 'x_max', 'y_min', and 'y_max' keys.
    """
    rects = []

    # Check if 'storeRequest' and 'MP_mapID' exist in final_df
    if "storeRequest" in final_df.columns:
        y_min_signal = final_df["storeRequest"].min()
    else:
        # Use an alternative signal or default value if 'storeRequest' is not present
        y_min_signal = final_df["alternativeSignal"].min() if "alternativeSignal" in final_df.columns else 0

    if "MP_mapID" in final_df.columns:
        y_max_signal = final_df["MP_mapID"].max()
    else:
        # Use an alternative signal or default value if 'MP_mapID' is not present
        y_max_signal = final_df["mapDataFileSystemStatus"].max() if "mapRecordingStatus" in final_df.columns else 255

    for interval in time_intervals:
        rect = {
            "x_min": interval["start"],
            "x_max": interval["end"],
            "y_min": y_min_signal,
            "y_max": y_max_signal,
        }
        rects.append(rect)

    return rects


def create_config(data_pairs, annotation_text, rects=None):
    """Returns: dict: Configuration dictionary."""
    if rects is None:
        rects = []  # Default to an empty list if no rectangles are provided

    config = {
        "data_pairs": data_pairs,
        "rects": rects,
        "annotation": {
            "text": annotation_text,
            "font_size": 15,
            "font_color": "Black",
        },
        "layout": {
            "xaxis_title": "uiCycleCounter",
            "yaxis_title": "State transition",
        },
    }
    return config


def create_plot(data, plot_titles, plots, remarks, config, final_data=None):
    """
    Create a plot using the provided data and optional configuration.

    Parameters:
        - data: DataFrame containing the main data to plot.
        - plot_titles: List to append plot titles.
        - plots: List to append plot figures.
        - remarks: List to append remarks.
        - config: Optional dictionary containing configuration settings with keys:
            - 'data_pairs': List of tuples, each containing (x_data, y_data, name, marker_color)
            - 'rects': List of dictionaries for rectangle settings with keys 'x_min', 'x_max', 'y_min', 'y_max'
            - 'annotation': Dictionary for annotation settings with keys 'text', 'font_size', 'font_color'
            - 'layout': Dictionary for layout settings with keys 'xaxis_title', 'yaxis_title'
        - final_data: Optional DataFrame for final data to plot; if not provided, only main data will be plotted.
    """

    def add_trace(fig, x, y, name, marker_color=None):
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines+markers",
                line_shape="hv",
                name=name,
                marker=dict(color=marker_color) if marker_color else None,
            )
        )

    # Add initial elements to plot_titles, plots, and remarks
    plot_titles.append("")
    plots.append("")
    remarks.append("")

    fig = go.Figure()

    # Add traces based on config data pairs
    for x, y, name, marker_color in config["data_pairs"]:
        add_trace(fig, data[x], data[y], name, marker_color)
        if final_data is not None:
            add_trace(fig, final_data[x], final_data[y], f"{name}_state_change", "green")

    # Determine rectangles and annotations positions based on config
    rects = config["rects"]
    annotation = config["annotation"]
    layout = config["layout"]

    # Add rectangles
    for rect in rects:
        fig.add_shape(
            type="rect",
            x0=rect["x_min"],
            y0=rect["y_min"],
            x1=rect["x_max"],
            y1=rect["y_max"],
            line=dict(color="RoyalBlue"),
            fillcolor="red" if "failed" in annotation["text"] else "green",
            opacity=0.3,
        )

    # Add annotations to each rectangle
    for rect in rects:
        fig.add_annotation(
            x=(rect["x_min"] + rect["x_max"]) / 2,
            y=(rect["y_min"] + rect["y_max"]) / 2,
            text=annotation["text"],
            showarrow=False,
            font=dict(size=annotation["font_size"], color=annotation["font_color"]),
            align="center",
        )

    # Update layout
    fig.update_layout(xaxis_title=layout["xaxis_title"], yaxis_title=layout["yaxis_title"])

    # Append figure to plots
    plots.append(fig)
    return plots


def update_plots(data, plot_titles, plots, remarks, data_pairs):
    """Updates plot titles, plots, and remarks based on the provided data pairs."""

    def add_trace(fig, x, y, name, marker_color=None):
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines+markers",
                line_shape="hv",
                name=name,
                marker=dict(color=marker_color) if marker_color else None,
            )
        )

    # Add initial elements to plot_titles, plots, and remarks
    plot_titles.append("")
    plots.append("")
    remarks.append("")

    fig = go.Figure()

    for x, y, name, marker_color in data_pairs:
        add_trace(fig, data[x], data[y], name, marker_color)

    plots.append(fig)
    return plots


def update_results(result, test_result, plots, plot_titles, remarks):
    """Update result details with test results, plots, plot titles, and remarks."""
    result_df = {
        fc.TEST_RESULT: [test_result],
    }
    result.details["Additional_results"] = result_df
    for plot in plots:
        if "plotly.graph_objs._figure.Figure" in str(type(plot)):
            result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        else:
            result.details["Plots"].append(plot)
    for plot_title in plot_titles:
        result.details["Plot_titles"].append(plot_title)
    for remark in remarks:
        result.details["Remarks"].append(remark)
