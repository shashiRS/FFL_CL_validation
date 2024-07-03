"""Endpoints to discover testcases."""

import importlib
import inspect
import logging
import os
import pkgutil
import sys

from tsf.core.parameterized_testcase import ParameterizedTestCase
from tsf.core.testcase import TestCase, Statistics
from tsf.core.report import CustomReportOverview
from os.path import join, dirname, abspath

from pydantic import BaseModel

_log = logging.getLogger(__file__)


class _OrmBaseModel(BaseModel):
    """Base for all models."""

    # model_config = ConfigDict(from_attributes=True)

    class Config:
        """Enable ORM mode."""

        from_attributes = True  # v2
        orm_mode = True  # v1


class TestcaseDefinition(_OrmBaseModel):
    """Model for a testcase definition."""

    class_name: str


def normalize_str(c: str, join_char="_"):
    c = c.lower()
    return join_char.join(c.split(" "))


def _check_testcase_teststep(module_name, import_errors):
    """Import the given module and inspect for (parametrized) testcases and teststeps."""
    discovered_testcases_tsf = []
    discovered_testcases_trc = []
    discovered_statistics_plugin = []
    discovered_custom_overview_plugin = []

    def handle_exception(exception):
        msg_lst = [f"Failed to scan: {module_name}."]
        msg_lst.append(f"Error: {str(exception)}.")
        import_errors.append("".join(msg_lst))

    try:
        m = importlib.import_module(module_name)
    except ImportError as ex:
        handle_exception(ex)
    except Exception as ex:
        handle_exception(ex)
    except SystemExit as ex:
        handle_exception(ex)
    except BaseException as ex:
        handle_exception(ex)

    _log.debug(f"Checked module '{m.__name__}' ({os.path.abspath(m.__file__)})")
    for name, member in inspect.getmembers(m):
        # Only iterate over classes implmented in that particular module
        if inspect.isclass(member) and member.__module__.startswith(module_name):
            if member.__module__.startswith("tsf."):
                # not interested in resources
                continue

            if issubclass(member, ParameterizedTestCase):
                # for parameter_set in member.parameter_sets:
                #     spec_tag = parameter_set.spec_tag
                #     # self.__add_teststcase(module_name, member, spec_tag)
                class_name = module_name + "." + name
                # TestcaseCache().testcases.append(model.TestcaseDefinition(class_name=class_name))
                discovered_testcases_tsf.append(TestcaseDefinition(class_name=class_name).class_name)

            elif issubclass(member, TestCase):
                # spec_tag = member.spec_tag
                # self.__add_teststcase(module_name, member, spec_tag)
                class_name = module_name + "." + name
                # TestcaseCache().testcases.append(model.TestcaseDefinition(class_name=class_name))
                discovered_testcases_tsf.append(TestcaseDefinition(class_name=class_name).class_name)

            elif hasattr(member, "test_cluster_name"):
                class_name = module_name + "." + name
                discovered_testcases_trc.append(TestcaseDefinition(class_name=class_name).class_name)

            elif issubclass(member, Statistics):
                class_name = module_name + "." + name
                discovered_statistics_plugin.append(TestcaseDefinition(class_name=class_name).class_name)

            elif issubclass(member, CustomReportOverview):
                class_name = module_name + "." + name
                discovered_custom_overview_plugin.append(TestcaseDefinition(class_name=class_name).class_name)

    return (
        discovered_testcases_tsf,
        discovered_testcases_trc,
        discovered_statistics_plugin,
        discovered_custom_overview_plugin,
    )


def scan_environment(workspace_path):
    """Scan the python environment for TSF (parametrized) testcases."""
    discovered_testcases_tsf = []
    discovered_testcases_trc = []
    discovered_statistics_plugin = []
    discovered_custom_overview_plugin = []
    import_errors = []

    components = os.listdir(workspace_path)

    for component in components:
        if os.path.isdir(os.path.join(workspace_path, component)) and component != "Trcruntime":
            try:
                m = importlib.import_module(component)
            except ImportError:
                continue

            for mi in pkgutil.walk_packages(m.__path__, m.__name__ + "."):
                try:
                    tsf_tests, trc_tests, statistics_overview, custom_overview = _check_testcase_teststep(
                        mi.name, import_errors
                    )

                    discovered_testcases_tsf.extend(tsf_tests)
                    discovered_testcases_trc.extend(trc_tests)
                    discovered_statistics_plugin.extend(statistics_overview)
                    discovered_custom_overview_plugin.extend(custom_overview)

                except Exception as ex:
                    print(f"Failed to scan: {mi.name}. {ex}")
                except SystemExit as ex:
                    print(f"Failed to scan: {mi.name}. {ex}")
                except BaseException as ex:
                    print(f"Failed to scan: {mi.name}. {ex}")

    # return [discovered_testcases_tsf, discovered_testcases_trc, discovered_statistics_plugin, discovered_custom_overview_plugin], import_errors
    return [discovered_testcases_tsf]


print(scan_environment(sys.argv[1]))
