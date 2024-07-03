import importlib
import json as j5
from datetime import datetime
from hashlib import md5
from os import remove
from os.path import dirname, splitext, exists
from pathlib import Path
from tsf.core._internals.debugging_support import Bootstrap
from tsf.core._internals.signal_registry import Assignment
from tsf.db.connect import DatabaseConnector, ScopedConnectionProvider
from tsf.db.processing_input import ProcessingInputSet
from tsf.testbench import report
from tsf.testbench import runner
from tsf.testbench import trc_classic_runner
import sys
import os


def create_database(payload, tmp_folder):
    try:

        sqlite_path = os.path.join(tmp_folder, "tsf.sqlite")
        # delete database if it already exists
        if exists(sqlite_path):
            remove(sqlite_path)
        Bootstrap.debugging_sqlite_db(sqlite_path, sync_globals=False)

        input_sets = []
        cp = ScopedConnectionProvider(sqlite=sqlite_path)
        with DatabaseConnector(cp) as dbc:
            # for name in components:
            # dbc.results.add_component("examples")

            project_name = payload["project"]
            if not dbc.global_data.get_project(project_name):
                dbc.global_data.add_project(project_name, "-", "-")
                dbc.processing_inputs.create_input_set(url=f"/{project_name}")

            all_entries = []
            entries_mapping = {}
            for entry in payload["tableData"]:
                c_input = dbc.processing_inputs.create_input(Path(entry["bsig"]))
                all_entries.append(c_input)
                for test_path in entry["functionalTest"]:
                    if test_path not in entries_mapping:
                        entries_mapping[test_path] = []
                    entries_mapping[test_path].append(c_input)

            # ToDo - temporary code to create an input set with all files until multiple inputs sets are usable
            hash = md5(",".join([entry.file_path for entry in all_entries]).encode("utf-8")).hexdigest()
            temp_url = f"/{project_name}/example-{hash}"
            ips = dbc.processing_inputs.get_input_set(url=temp_url)
            if ips and not ips.is_deleted:
                input_sets.append(temp_url)
            else:
                dbc.processing_inputs.create_input_set(temp_url, all_entries)
                input_sets.append(temp_url)

            assignments = {}
            for test_path in entries_mapping:
                entries = entries_mapping[test_path]
                hash = md5(",".join([entry.file_path for entry in entries]).encode("utf-8")).hexdigest()
                url = f"/{project_name}/example-{hash}"
                ips = dbc.processing_inputs.get_input_set(url=url)
                if ips and not ips.is_deleted:
                    assignments[test_path] = [url]
                else:
                    dbc.processing_inputs.create_input_set(url, entries)
                    assignments[test_path] = [url]
            dbc.commit()
    except Exception as err:
        raise Exception(str(err))

    return assignments, input_sets, sqlite_path


def main():
    log_level_arg = []
    log_level_map = {
        "Warning": [],
        "Info": ["-v"],
        "Debug": ["-vv"],
    }

    json_path = sys.argv[1]
    # read config file
    with open(json_path, "r") as fp:
        try:
            data = j5.load(fp)
        except runner.json.JSONDecodeError as ex:
            msg = (
                f"Could not load config json '{json_path}': {ex}. If you are using JSON5 feature make sure to"
                " insall json5."
            )
            runner.json._log.fatal(msg)
            raise runner.json.TsfException(msg)

    tmp_path = dirname(json_path)
    functional_tab_data = data["fun"]
    general_settings = data["General"]
    report_path = functional_tab_data["reportPath"] + "/tsf_report" + datetime.now().strftime("_%m_%d_%Y_%H_%M")
    str_project_name = functional_tab_data["project"]
    str_test_type = functional_tab_data["testType"]
    str_log_level = general_settings.get("logLevel", "Warning")
    use_multiprocessing = general_settings.get("useMultiprocessing", False)
    if "report_prefix" in data and data["report_prefix"]:
        report_path = functional_tab_data["reportPath"] + "/tsf_report_" + str(data["report_prefix"])
    dict_assignments, input_sets, sqlite_path = create_database(functional_tab_data, tmp_path)

    inputs = []
    inputs_object = {}
    # make inputs directory list
    for input in functional_tab_data["tableData"]:
        path_info = input["bsig"]
        # unpacking the tuple
        file_name, extension = splitext(path_info)
        directory = dirname(path_info)
        if extension not in inputs_object:
            inputs_object[extension] = set()

        if directory not in inputs_object[extension]:
            inputs.append(
                {
                    "directory": directory,
                    "file_prefix": "",
                    "file_suffix": "",
                    "extension": extension,
                    "mount_point": None,
                }
            )
            inputs_object[extension].add(directory)

    testcases = []
    inputSets = []
    for key in dict_assignments:
        testcases.append(key)
        inputSets.extend(dict_assignments[key])
    runnerSpecPath = os.path.join(tmp_path, "runner_specification.json")
    # not used currently, intended for use when multiple input sets are accepted
    # inputSets = list(set(inputSets))
    test_run_text = "Debug " + datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    if "regressiontype" in list(functional_tab_data.keys()):
        test_run_text = functional_tab_data["regressiontype"] + " " + datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    software_version = "Example SW"
    if "variant" in list(functional_tab_data.keys()):
        software_version = functional_tab_data["variant"]

    runner_json = {
        "project": str_project_name,
        "subject_under_test": {"name": software_version, "test_discipline": "debug"},
        "testrun": test_run_text,
        "assignments": dict_assignments,
        "processing_input_sets": input_sets,
        "testcases": testcases,
        "input": inputs,
        "temp_dir": report_path,
        "open_explorer": general_settings["openReport"],
    }

    if "statistics" in functional_tab_data["selectedPlugins"] and functional_tab_data["usePlugins"]:
        runner_json["statistics"] = functional_tab_data["selectedPlugins"]["statistics"]
    if "overviews" in functional_tab_data["selectedPlugins"] and functional_tab_data["usePlugins"]:
        runner_json["custom_overviews"] = functional_tab_data["selectedPlugins"]["overviews"]

    json_object = j5.dumps(runner_json, indent=4)
    with open(runnerSpecPath, "w") as runner_file:
        runner_file.write(json_object)

    if str_log_level in log_level_map:
        log_level_arg = log_level_map[str_log_level]

    runner_args = [runnerSpecPath, "--check-inputs", "--clean-dir", "--sqlite", sqlite_path, "-r", *log_level_arg]
    report_args = [
        report_path + "/report",
        "-s",
        report_path + "/run_spec.json",
        "-i",
        report_path,
        "-d",
        "--sqlite",
        sqlite_path,
        "--redo-all",
        *log_level_arg,
    ]
    if use_multiprocessing:
        runner_args.append("--multiprocessing")
    # import test case classes and update assignments
    for tc_name in dict_assignments:
        p, m = tc_name.rsplit(".", 1)
        mod = importlib.import_module(p)
        met = getattr(mod, m)

        if not isinstance(dict_assignments[tc_name], list):
            dict_assignments[tc_name] = [dict_assignments[tc_name]]
        for input_set in dict_assignments[tc_name]:
            assignment = Assignment(ProcessingInputSet, input_set, str_project_name)
            # Attach only, to not mess up the heap and break e.g. unit test which share the heap

            met.assignments = []
            met.assignments.append(assignment)

    # call runner
    if str_test_type == "tsf":
        runner.main(runner_args)
    else:
        trc_classic_runner.main(*runner_args)

    report.main(report_args)


if __name__ == "__main__":
    main()
