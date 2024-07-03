"""This helper contains info for pdw plot with sectors."""

import plotly.graph_objects as go

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


def plotter_helper(time, signals, columns):
    """Add traces to a figure in order to plot it."""
    fig = go.Figure()
    for column in columns:
        fig.add_trace(go.Scatter(x=time, y=signals[column], mode="lines", name=column))
    fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[us]")
    fig.update_layout(PlotlyTemplate.lgt_tmplt)
    return fig
