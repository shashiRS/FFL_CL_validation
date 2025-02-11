"""This helper contains info for UI Manager."""

import plotly.graph_objects as go

import pl_parking.common_constants as fc
import pl_parking.PLP.MF.constants as constants
from pl_parking.PLP.MF.constants import PlotlyTemplate

x_coords_front = [
    -79,
    -261,
    -478,
    -659,
    -451,
    -412,
    -323,
    -290,
    -79,
    -261,
    -323,
    -412,
    -478,
    -460,
    -591,
    -540,
    -440,
    -367,
    -296,
    -200,
    -150,
    -277,
    -367,
    -460,
    -478,
    -367,
    -367,
    -367,
    -367,
]  # ,-478,-412]
y_coords_front = [
    -128,
    -4,
    -4,
    -128,
    -240,
    -215,
    -215,
    -240,
    -128,
    -4,
    -215,
    -215,
    -4,
    -60,
    -165,
    -192,
    -125,
    -125,
    -125,
    -192,
    -165,
    -60,
    -60,
    -60,
    -4,
    -4,
    -60,
    -125,
    -215,
]  # ,-4,-215]
x_coords_rear = [-x for x in x_coords_front]
y_coords_rear = [-x for x in y_coords_front]
# x_coords_backc = [-x for x in x_coords_back]
# y_coords_backc = [x-500 for x in y_coords_back]
car_x = [-431, -431, -412, -323, -300, -300]
car_y = [-400, -260, -235, -235, -260, -400]

sector_dict_front = {
    3: {
        3: {
            "x": [-290, -323, -296, -200],
            "y": [-240, -215, -125, -192],
            "name": "Sector 3, critical 3",
            "fill": "rgba(255, 0, 0, 0.5)",
        },
        2: {
            "x": [-150, -277, -296, -200],
            "y": [-165, -60, -125, -192],
            "name": "Sector 3, critical 2",
            "fill": "rgba(255, 255, 0, 0.5)",
        },
        1: {
            "x": [-150, -277, -261, -79],
            "y": [-165, -60, -4, -128],
            "name": "Sector 3, critical 1",
            "fill": "rgba(0, 255, 0, 0.5)",
        },
        0: {
            "x": [-670, -740, -550, -480],
            "y": [-110, -70, 100, 10],
            "name": "Sector 0, critical 0",
            "fill": "rgba(128, 128,  128, 0.5)",
        },
    },
    2: {
        3: {
            "x": [-367, -323, -296, -367],
            "y": [-215, -215, -125, -125],
            "name": "Sector 2, critical 3",
            "fill": "rgba(255, 0, 0, 0.5)",
        },
        2: {
            "x": [-367, -277, -296, -367],
            "y": [-60, -60, -125, -125],
            "name": "Sector 2, critical 2",
            "fill": "rgba(255, 255, 0, 0.5)",
        },
        1: {
            "x": [-367, -367, -277, -261],
            "y": [-4, -60, -60, -4],
            "name": "Sector 2, critical 1",
            "fill": "rgba(0, 255, 0, 0.5)",
        },
        0: {
            "x": [-670, -740, -550, -480],
            "y": [-110, -70, 100, 10],
            "name": "Sector 0, critical 0",
            "fill": "rgba(128, 128,  128, 0.5)",
        },
    },
    1: {
        3: {
            "x": [-367, -412, -440, -367],
            "y": [-215, -215, -125, -125],
            "name": "Sector 1, critical 3",
            "fill": "rgba(255, 0, 0, 0.5)",
        },
        2: {
            "x": [-367, -460, -440, -367],
            "y": [-60, -60, -125, -125],
            "name": "Sector 1, critical 2",
            "fill": "rgba(255, 255, 0, 0.5)",
        },
        1: {
            "x": [-367, -367, -460, -478],
            "y": [-4, -60, -60, -4],
            "name": "Sector 1, critical 1",
            "fill": "rgba(0, 255, 0, 0.5)",
        },
        0: {
            "x": [-670, -740, -550, -480],
            "y": [-110, -70, 100, 10],
            "name": "Sector 0, critical 0",
            "fill": "rgba(128, 128,  128, 0.5)",
        },
    },
    0: {
        3: {
            "x": [-451, -412, -440, -540],
            "y": [-240, -215, -125, -192],
            "name": "Sector 0, critical 3",
            "fill": "rgba(255, 0, 0, 0.5)",
        },
        2: {
            "x": [-591, -460, -440, -540],
            "y": [-165, -60, -125, -192],
            "name": "Sector 0, critical 2",
            "fill": "rgba(255, 255, 0, 0.5)",
        },
        1: {
            "x": [-591, -460, -478, -659],
            "y": [-165, -60, -4, -128],
            "name": "Sector 0, critical 1",
            "fill": "rgba(0, 255, 0, 0.5)",
        },
        0: {
            "x": [-670, -740, -550, -480],
            "y": [-110, -70, 100, 10],
            "name": "Sector 0, critical 0",
            "fill": "rgba(128, 128,  128, 0.5)",
        },
    },
}
sector_dict_rear = {
    11: {
        3: {
            "x": [-x for x in sector_dict_front[3][3]["x"]],
            "y": [-x for x in sector_dict_front[3][3]["y"]],
            "name": "Sector 11, critical 3",
            "fill": sector_dict_front[3][3]["fill"],
        },
        2: {
            "x": [-x for x in sector_dict_front[3][2]["x"]],
            "y": [-x for x in sector_dict_front[3][2]["y"]],
            "name": "Sector 11, critical 2",
            "fill": sector_dict_front[3][2]["fill"],
        },
        1: {
            "x": [-x for x in sector_dict_front[3][1]["x"]],
            "y": [-x for x in sector_dict_front[3][1]["y"]],
            "name": "Sector 11, critical 1",
            "fill": sector_dict_front[3][1]["fill"],
        },
    },
    10: {
        3: {
            "x": [-x for x in sector_dict_front[2][3]["x"]],
            "y": [-x for x in sector_dict_front[2][3]["y"]],
            "name": "Sector 10, critical 3",
            "fill": sector_dict_front[2][3]["fill"],
        },
        2: {
            "x": [-x for x in sector_dict_front[2][2]["x"]],
            "y": [-x for x in sector_dict_front[2][2]["y"]],
            "name": "Sector 10, critical 2",
            "fill": sector_dict_front[2][2]["fill"],
        },
        1: {
            "x": [-x for x in sector_dict_front[2][1]["x"]],
            "y": [-x for x in sector_dict_front[2][1]["y"]],
            "name": "Sector 10, critical 1",
            "fill": sector_dict_front[2][1]["fill"],
        },
    },
    9: {
        3: {
            "x": [-x for x in sector_dict_front[1][3]["x"]],
            "y": [-x for x in sector_dict_front[1][3]["y"]],
            "name": "Sector 9, critical 3",
            "fill": sector_dict_front[1][3]["fill"],
        },
        2: {
            "x": [-x for x in sector_dict_front[1][2]["x"]],
            "y": [-x for x in sector_dict_front[1][2]["y"]],
            "name": "Sector 9, critical 2",
            "fill": sector_dict_front[1][2]["fill"],
        },
        1: {
            "x": [-x for x in sector_dict_front[1][1]["x"]],
            "y": [-x for x in sector_dict_front[1][1]["y"]],
            "name": "Sector 9, critical 1",
            "fill": sector_dict_front[1][1]["fill"],
        },
    },
    8: {
        3: {
            "x": [-x for x in sector_dict_front[0][3]["x"]],
            "y": [-x for x in sector_dict_front[0][3]["y"]],
            "name": "Sector 8, critical 3",
            "fill": sector_dict_front[0][3]["fill"],
        },
        2: {
            "x": [-x for x in sector_dict_front[0][2]["x"]],
            "y": [-x for x in sector_dict_front[0][2]["y"]],
            "name": "Sector 8, critical 2",
            "fill": sector_dict_front[0][2]["fill"],
        },
        1: {
            "x": [-x for x in sector_dict_front[0][1]["x"]],
            "y": [-x for x in sector_dict_front[0][1]["y"]],
            "name": "Sector 8, critical 1",
            "fill": sector_dict_front[0][1]["fill"],
        },
    },
}


def plotter_helper(time, signals, columns, signal_paths):
    """Add traces to a figure in order to plot it."""
    fig = go.Figure()
    for column in columns:
        fig.add_trace(go.Scatter(x=time, y=signals[column], mode="lines", name=signal_paths[column]))
    fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[us]")
    fig.update_layout(PlotlyTemplate.lgt_tmplt)
    return fig


pdw_sector_length = constants.SilCl.PDWConstants.PDWSectorLength


class PDWSectorDistance:
    """Helper for PDW measurements"""

    def sector_evaluation(smallest_dist_f: list, critical_level_f: list, type_of_sector: list):
        """
        This function evaluate_signals takes smallest_dist_f (an array with 4 signals of smallest_distance for each front)
        and critical_level_f (an array with 4 signals of critical for each front) as parameters. It then iterates over each front,
        checks if the critical level (a mask that checks if an object was detected) is non-zero, and evaluates accordingly.
        Finally, it returns a dictionary signal_summary where each segment of front is associated with its evaluation string.
        """
        signal_summary = {}
        verdict = []

        for idx, (smallest_dist, critical_level) in enumerate(zip(smallest_dist_f, critical_level_f)):
            critical_level_mask = any(critical_level)  # Checking if any value in the array is non-zero
            if critical_level_mask:
                smallest_dist_front1 = min(smallest_dist)
                for i, element in enumerate(smallest_dist):
                    if element == smallest_dist_front1:
                        idx_crit = i
                        break
                verdict.append(True)
                sector_slice = 0
                smallest_dist_front = round(min(smallest_dist), 3)
                if smallest_dist_front <= pdw_sector_length.SLICE_LENGTH:
                    sector_slice = 1
                elif (
                    smallest_dist_front <= (pdw_sector_length.SLICE_LENGTH * 2)
                    and smallest_dist_front >= pdw_sector_length.SLICE_LENGTH
                ):
                    sector_slice = 2
                elif smallest_dist_front <= (pdw_sector_length.SLICE_LENGTH * 3) and smallest_dist_front >= (
                    pdw_sector_length.SLICE_LENGTH * 2
                ):
                    sector_slice = 3
                elif smallest_dist_front <= (pdw_sector_length.SLICE_LENGTH * 4) and smallest_dist_front >= (
                    pdw_sector_length.SLICE_LENGTH * 3
                ):
                    sector_slice = 4
                elif smallest_dist_front <= (pdw_sector_length.SLICE_LENGTH * 5) and smallest_dist_front >= (
                    pdw_sector_length.SLICE_LENGTH * 4
                ):
                    sector_slice = 5
                elif smallest_dist_front <= (pdw_sector_length.SLICE_LENGTH * 6) and smallest_dist_front >= (
                    pdw_sector_length.SLICE_LENGTH * 5
                ):
                    sector_slice = 6
                elif smallest_dist_front <= (pdw_sector_length.SLICE_LENGTH * 7) and smallest_dist_front >= (
                    pdw_sector_length.SLICE_LENGTH * 6
                ):
                    sector_slice = 7
                elif smallest_dist_front <= (pdw_sector_length.SLICE_LENGTH * 8) and smallest_dist_front >= (
                    pdw_sector_length.SLICE_LENGTH * 7
                ):
                    sector_slice = 8
                elif smallest_dist_front <= pdw_sector_length.PDW_SECTOR_LENGTH and smallest_dist_front >= (
                    pdw_sector_length.SLICE_LENGTH * 8
                ):
                    sector_slice = 9
                evaluation = f"The criticality level = {critical_level_f[idx].iat[idx_crit]} in slice {sector_slice} with smallest distance detected towards object {smallest_dist_front} m."
            else:
                verdict.append(False)
                evaluation = "No object detected."

            signal_summary[f"{type_of_sector[idx]}"] = evaluation
        return signal_summary, verdict

    def all_sector_evaluation(
        smallest_dist_f: list,
        critical_level_f: list,
        type_of_sector: list,
        # obstacle_dist_f: list,
        # obstacle_signals_f: list,
    ):
        """
        This function evaluate_signals takes smallest_dist_f (an array with 4 signals of smallest_distance for each front)
        and critical_level_f (an array with 4 signals of critical for each front) as parameters. It then iterates over each front,
        checks if the critical level (a mask that checks if an object was detected) is non-zero, and evaluates accordingly.
        Finally, it returns a dictionary signal_summary where each segment of front is associated with its evaluation string.
        """
        signal_summary = {}
        hmi_flag = None
        verdict = []
        input_timestamp = None
        for idx, (smallest_dist, critical_level) in enumerate(zip(smallest_dist_f, critical_level_f)):

            critical_level_mask = any(critical_level)  # Checking if any value in the array is non-zero
            if critical_level_mask:
                smallest_dist_front1 = min(smallest_dist)
                if smallest_dist_front1 == 0:
                    smallest_dist_front1 = min(smallest_dist[smallest_dist != 0])
                    hmi_flag = True
                    input_timestamp = smallest_dist[smallest_dist != 0].index[0]
                for i, element in enumerate(smallest_dist):
                    if element == smallest_dist_front1:
                        idx_crit = i
                        input_timestamp = idx_crit
                        break
                verdict.append(True)
                smallest_dist_front = round(min(smallest_dist), 3)
                if hmi_flag:
                    smallest_dist_front = round(min(smallest_dist[smallest_dist != 0]), 3)
                # obstacle_dist_front = round(min(obstacle_dist), 3)
                sector_slice = 0
                if smallest_dist_front <= pdw_sector_length.SLICE_LENGTH:
                    sector_slice = 1
                elif (
                    smallest_dist_front <= (pdw_sector_length.SLICE_LENGTH * 2)
                    and smallest_dist_front >= pdw_sector_length.SLICE_LENGTH
                ):
                    sector_slice = 2
                elif smallest_dist_front <= (pdw_sector_length.SLICE_LENGTH * 3) and smallest_dist_front >= (
                    pdw_sector_length.SLICE_LENGTH * 2
                ):
                    sector_slice = 3
                elif smallest_dist_front <= (pdw_sector_length.SLICE_LENGTH * 4) and smallest_dist_front >= (
                    pdw_sector_length.SLICE_LENGTH * 3
                ):
                    sector_slice = 4
                elif smallest_dist_front <= (pdw_sector_length.SLICE_LENGTH * 5) and smallest_dist_front >= (
                    pdw_sector_length.SLICE_LENGTH * 4
                ):
                    sector_slice = 5
                elif smallest_dist_front <= (pdw_sector_length.SLICE_LENGTH * 6) and smallest_dist_front >= (
                    pdw_sector_length.SLICE_LENGTH * 5
                ):
                    sector_slice = 6
                elif smallest_dist_front <= (pdw_sector_length.SLICE_LENGTH * 7) and smallest_dist_front >= (
                    pdw_sector_length.SLICE_LENGTH * 6
                ):
                    sector_slice = 7
                elif smallest_dist_front <= (pdw_sector_length.SLICE_LENGTH * 8) and smallest_dist_front >= (
                    pdw_sector_length.SLICE_LENGTH * 7
                ):
                    sector_slice = 8
                elif smallest_dist_front <= pdw_sector_length.PDW_SECTOR_LENGTH and smallest_dist_front >= (
                    pdw_sector_length.SLICE_LENGTH * 8
                ):
                    sector_slice = 9
                # evaluation1 = f"The criticality level = {critical_level_f[idx].iat[idx_crit]} in SLICE {sector_slice} with smallest distance detected towards object {smallest_dist_front} m."
                evaluation1 = f"Criticality = {critical_level_f[idx].iat[idx_crit]}, SLICE = {sector_slice}, at distance {smallest_dist_front} m."
                # evaluation1 = {"crit_level" : critical_level_f[idx].iat[idx_crit],
            # "distance" : smallest_dist_front,
            # "slice" : sector_slice,}
            # evaluation2 = f"The criticality level = {critical_level_f[idx].iat[idx_crit]} in SLICE {sector_slice} with smallest distance detected towards object {obstacle_dist_front} m."
            else:
                verdict.append(False)
                evaluation1 = "Criticality = N/a, SLICE = N/a, at distance N/a m."
            #     evaluation1 =  {
            # "crit_level" : 'N/a',
            # "distance" : 'N/a',
            # "slice" : 'N/a',
            #  }
            # evaluation2 = "No object detected."

            signal_summary[f"{type_of_sector[idx]}"] = evaluation1
            # signal_summary[f"{obstacle_signals_f[idx]}"] = evaluation2
        return signal_summary, verdict, input_timestamp


all_sector_evaluation = PDWSectorDistance.all_sector_evaluation
sector_evaluation = PDWSectorDistance.sector_evaluation


def get_result_color(result):
    """Method to give a signal status with verdict and color."""
    color_dict = {
        False: "#dc3545",
        True: "#28a745",
        fc.FAIL: "#dc3545",
        fc.PASS: "#28a745",
        "NOT ASSESSED": "#818589",
        fc.NOT_ASSESSED: "#818589",
    }
    text_dict = {
        False: "FAILED",
        True: "PASSED",
        fc.FAIL: "FAILED",
        fc.PASS: "PASSED",
        "NOT ASSESSED": "NOT ASSESSED",
        fc.NOT_ASSESSED: "NOT ASSESSED",
    }

    return (
        f'<span align="center" style="width: 100%; height: 100%; display: block;background-color: {color_dict[result]}'
        f' ; color : #ffffff">{text_dict[result]}</span>'
    )
