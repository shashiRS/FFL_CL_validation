"""LOC MAP Test Cases"""

import logging
import math
import os
import tempfile
from pathlib import Path

import pandas as pd
from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import TestCase, TestStep, register_signals, testcase_definition, teststep_definition, verifies
from tsf.core.utilities import debug

import pl_parking.common_constants as fc
import pl_parking.PLP.LOC.MAP.constants as fh
from pl_parking.common_ft_helper import (
    MfCustomTestcaseReport,
    MfCustomTeststepReport,
    build_html_table,
    rep,
)
from pl_parking.PLP.LOC.common_ft_helper import (
    MAP_Signals,
    MAPEventStateChecker,
    create_config,
    create_plot,
    create_rects,
    get_time_intervals_with_indices,
    update_results,
)
from pl_parking.PLP.LOC.MAP.constants import StateChange

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "SIGNAL_DATA"
loc_signal = MAP_Signals()


def latlon_to_utm(latitude, longitude):
    """
    Convert geographic coordinates (latitude, longitude) to UTM (Universal Transverse Mercator) coordinates.

    Parameters:
    latitude (float): Latitude in decimal degrees.
    longitude (float): Longitude in decimal degrees.

    Returns:
    tuple: A tuple containing:
        - easting (float): The UTM easting in meters.
        - northing (float): The UTM northing in meters.
        - zone_number (int): The UTM zone number.
    """
    # Constants for the WGS84 ellipsoid
    a = 6378137.0  # Semi-major axis of the Earth in meters
    f = 1 / 298.257223563  # Flattening
    e2 = f * (2 - f)  # Eccentricity squared

    k0 = 0.9996  # Scale factor at the central meridian
    # Calculate UTM zone number
    zone_number = int((longitude + 180) / 6) + 1

    # Calculate the central meridian of the UTM zone in radians
    central_meridian = math.radians((zone_number - 1) * 6 - 180 + 3)

    # Convert latitude and longitude to radians
    lat_rad = math.radians(latitude)
    lon_rad = math.radians(longitude)

    # Radius of curvature in the prime vertical (N)
    N = a / math.sqrt(1 - e2 * math.sin(lat_rad) ** 2)

    # Meridional arc (M) — Simplified for the sake of this example
    T = math.tan(lat_rad) ** 2
    C = e2 * math.cos(lat_rad) ** 2 / (1 - e2)
    A = math.cos(lat_rad) * (lon_rad - central_meridian)

    M = a * (
        (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256) * lat_rad
        - (3 * e2 / 8 + 3 * e2**2 / 32 + 45 * e2**3 / 1024) * math.sin(2 * lat_rad)
        + (15 * e2**2 / 256 + 45 * e2**3 / 1024) * math.sin(4 * lat_rad)
        - (35 * e2**3 / 3072) * math.sin(6 * lat_rad)
    )

    # Calculate easting (x)
    easting = k0 * N * (A + (1 - T + C) * A**3 / 6 + (5 - 18 * T + T**2 + 72 * C - 58 * e2) * A**5 / 120)
    easting += 500000  # Adding the false easting

    # Calculate northing (y)
    northing = k0 * (
        M
        + N
        * math.tan(lat_rad)
        * (A**2 / 2 + (5 - T + 9 * C + 4 * C**2) * A**4 / 24 + (61 - 58 * T + T**2 + 600 * C - 330 * e2) * A**6 / 720)
    )

    # If the point is in the Southern Hemisphere, add 10,000,000 to the northing value
    if latitude < 0:
        northing += 10000000

    return easting, northing, zone_number


def build_signal_summary(pre_condition_result, test_result, x, y, zone_number, hemisphere):
    """Will build signal summary"""
    return pd.DataFrame(
        {
            "Signal_Evaluation": {
                "1": f"{loc_signal.get_complete_signal_name(MAP_Signals.Columns.MAP_ID)}, "
                f"{loc_signal.get_complete_signal_name(MAP_Signals.Columns.STORE_REQUEST)}, "
                f"{loc_signal.get_complete_signal_name(MAP_Signals.Columns.MAP_RECORDING_STATUS)}, "
                f"{loc_signal.get_complete_signal_name(MAP_Signals.Columns.MAP_DATA_FILE_SYSTEM_DATA)}",
                "2": f"{loc_signal.get_complete_signal_name(MAP_Signals.Columns.MAP_ORIGIN_HEMISPHERE)}, "
                f"{loc_signal.get_complete_signal_name(MAP_Signals.Columns.MAP_ORIGIN_X)}, "
                f"{loc_signal.get_complete_signal_name(MAP_Signals.Columns.MAP_ORIGIN_Y)}, "
                f"{loc_signal.get_complete_signal_name(MAP_Signals.Columns.MAP_ORIGIN_ZONE)}",
            },
            "Result": {
                "1": f"and {MAP_Signals.Columns.MAP_ID} == same as previous cycle "
                f"and {MAP_Signals.Columns.STORE_REQUEST} == {fh.TRUE} "
                f"and {MAP_Signals.Columns.MAP_RECORDING_STATUS} == {StateChange.ONGOING}(ongoing) "
                f"and {MAP_Signals.Columns.MAP_DATA_FILE_SYSTEM_DATA} == {StateChange.ONGOING}(ongoing) "
                "which indicates a received store request.",
                "2": f"{MAP_Signals.Columns.MAP_ORIGIN_HEMISPHERE} == {hemisphere} "
                f"{MAP_Signals.Columns.MAP_ORIGIN_X} == {x} "
                f"{MAP_Signals.Columns.MAP_ORIGIN_Y} == {y} "
                f"{MAP_Signals.Columns.MAP_ORIGIN_ZONE} == {zone_number} "
                "created and provided a georeferenced map.",
            },
            "Verdict": {"1": f"{pre_condition_result}", "2": f"{test_result}"},
        }
    )


@teststep_definition(
    step_number=1,
    name="SWRT_LOC_MAP_GeoReferenceMap_Creation ",
    description="This test step confirms that when <MappingAndLocalizationLowSpeed>  received a store map request,"
    " and it has a valid trajectory of global positions and a valid fused map,"
    " it shall create and provide a Georeferenced map.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MAP_Signals)
class TestStepFtLOCOutputMAPGeoReferenceMapCreation(TestStep):
    """Transitions from the ERROR state,
    when continue event received, map shall move from error state to error state
    """

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # Define variables
        test_result = fc.NOT_ASSESSED
        pre_condition_result = fc.NOT_ASSESSED
        data = pd.DataFrame()
        plot_titles, plots, remarks = rep([], 3)
        signal_details = {}

        # Load signals

        data = pd.DataFrame(self.readers[SIGNAL_DATA])
        data.reset_index(drop=True, inplace=True)
        Required_signals = [
            "uiCycleCounter",
            "MP_mapID",
            "mapRecordingStatus",
            "mapDataFileSystemStatus",
            "mapOrigin.hemisphere",
            "mapOrigin.x",
            "mapOrigin.y",
            "mapOrigin.zone",
            "storeRequest",
        ]
        data = data[Required_signals]
        matching_indices = []
        # Check if data has been provided to continue with the validation
        result_data = []
        checker = MAPEventStateChecker(data)
        """Evaluation part"""
        # which indicate map is in saving state
        for index in range(len(data) - 1):
            previous_index = index - 1
            next_index = index + 1
            if (
                checker.isStoreEvent(index, previous_index)
                and checker.isInMappingState(index)
                and checker.isInSavingState(next_index)
            ):
                # If all conditions are met, store the index
                matching_indices.append(index + 1)
                pre_condition_result = fc.PASS
        pre_condition_result = fc.PASS if pre_condition_result == fc.PASS else fc.FAIL
        # TODO get details of gps location from the person who share the recording
        # convert gps location to UTS co -ordinates

        # Example GPS coordinates (latitude and longitude)
        latitude = 37.7749
        longitude = -122.4194
        x, y, zone_number = latlon_to_utm(latitude, longitude)

        # Determine the hemisphere
        # hemisphere = +1 for Northern, hemisphere = −1 for Southern
        hemisphere = 1 if latitude >= 0 else -1

        for index in matching_indices:
            if (
                data.at[index + 1, "mapOrigin.hemisphere"] == hemisphere
                and data.at[index + 1, "mapOrigin.x"] == x
                and data.at[index + 1, "mapOrigin.y"] == y
                and data.at[index + 1, "mapOrigin.zone"] == zone_number
            ):
                result_data.extend(data.iloc[index : index + 2])

        final_df = pd.DataFrame(result_data)
        test_result = fc.FAIL if final_df.empty else fc.PASS

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
            remark = "Created and provided a Georeferenced map."
        else:
            self.result.measured_result = FALSE
            final_df = data
            remark = "Test failed, georeferenced map not updated."
        signal_details = build_signal_summary(pre_condition_result, test_result, x, y, zone_number, hemisphere)
        signal_summary = build_html_table(signal_details, remark)
        plot_titles.append("")
        annotation_text = (
            "Georeferenced map" if self.result.measured_result is TRUE else "georeferenced map not updated"
        )
        plots.append(signal_summary)
        remarks.append(remark)
        time_intervals = get_time_intervals_with_indices(final_df["uiCycleCounter"].tolist(), threshold=1)
        rects = create_rects(time_intervals, final_df)
        config = create_config(Required_signals, rects=rects, annotation_text=annotation_text)
        plots = create_plot(data, plot_titles, plots, remarks, config, final_df)
        update_results(self.result, test_result, plots, plot_titles, remarks)


@verifies(
    "88383",
    "https://jazz.conti.de/qm4/web/console/LIB_L3_SW_TM/_ufIY0DRKEe-YwuveGcgWRQ#action=com.ibm.rqm.planning.home."
    "actionDispatcher&subAction=viewTestCase&id=88383",
)
@testcase_definition(
    name="SWRT_LOC_MAP_GeoReferenceMap_Creation ",
    description="This test ensure when <MappingAndLocalizationLowSpeed>  received a store map request, "
    "and it has a valid trajectory of global positions and a valid fused map,"
    " it shall create and provide a georeferenced map.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI"
    "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_aJSjYDLREe-Om-dBJsz4EQ&vvc.configuration"
    "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fcm%2Fchangeset%2F_te6KgT7VEe-moNw0sxuQRA&componentURI"
    "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F"
    "_wxtVgiowEe-t3Zp5B0W8XQ",
)
class FtLOCOutputMAPGeoReferenceMapCreation(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtLOCOutputMAPGeoReferenceMapCreation]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.
    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.
    This is only meant to jump start testcase debugging.
    """
    debug(
        FtLOCOutputMAPGeoReferenceMapCreation,
        os.path.join(fh.DEBUG_ROOT_FOLDER, fh.BSIG_PATH),
        temp_dir=temp_dir,
        open_explorer=open_explorer,
        kpi_report=False,
        dev_report=True,
        project_name="PAR230",
    )
    _log.debug("All done.")


if __name__ == "__main__":
    working_directory = Path(tempfile.mkdtemp("_loc"))

    data_folder = working_directory / "data"
    out_folder = working_directory / "out"

    main(temp_dir=out_folder, open_explorer=True)
