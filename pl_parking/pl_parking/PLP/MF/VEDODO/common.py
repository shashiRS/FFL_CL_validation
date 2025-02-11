"""Here keeping commonly used methods to avoid duplicate code"""

import logging
import math

import numpy as np
import plotly.graph_objects as go

from pl_parking.PLP.MF.constants import PlotlyTemplate


def calculate_odo_error(x_gt, y_gt, psi_gt, psi_odo, x_odo, y_odo):
    """Calculates relative longitudinal and lateral error"""
    x_get_len = len(x_gt)
    abs_err_long_m = np.zeros(x_get_len)
    abs_err_lat_m = np.zeros(x_get_len)
    driven_dist_arr_m = np.zeros(x_get_len)
    rel_err_long_perc = np.zeros(x_get_len)
    rel_err_lat_perc = np.zeros(x_get_len)
    p_gt_ll = 0
    driven_dist_m = 0.0

    if len(x_gt) == len(y_gt) == len(psi_gt) == len(x_odo) == len(y_odo) == len(psi_odo):
        for idx in range(len(x_gt)):
            if not x_gt[idx] or not x_odo[idx]:
                rel_err_long_perc[idx] = 0
                rel_err_lat_perc[idx] = 0
                abs_err_long_m[idx] = 0
                abs_err_lat_m[idx] = 0
                continue

            p_gt = [
                [
                    x_gt[idx],
                ],
                [
                    y_gt[idx],
                ],
            ]
            p_odo = [
                [
                    x_odo[idx],
                ],
                [
                    y_odo[idx],
                ],
            ]

            # calculate orthogonal point - Lotpunkt
            arr = np.matrix(
                np.array(
                    [[math.cos(psi_gt[idx]), -math.sin(psi_gt[idx])], [math.sin(psi_gt[idx]), math.cos(psi_gt[idx])]]
                )
            )

            x = np.matmul(np.linalg.inv(arr), np.subtract(p_odo, p_gt))
            lp = p_gt + np.multiply(x[0], [[math.cos(psi_gt[idx])], [math.sin(psi_gt[idx])]])

            # absolute error
            abs_err_long_m[idx] = np.linalg.norm(np.subtract(lp, p_gt))
            abs_err_lat_m[idx] = np.linalg.norm(np.subtract(lp, p_odo))

            # driven distance
            if x_gt[idx] > 0:
                driven_dist_m = driven_dist_m + np.linalg.norm(np.subtract(p_gt, p_gt_ll))
                driven_dist_arr_m[idx] = driven_dist_m

            p_gt_ll = p_gt

            # relative error
            if driven_dist_m != 0.0:
                rel_err_long_perc[idx] = abs_err_long_m[idx] / driven_dist_m * 100.0
                rel_err_lat_perc[idx] = abs_err_lat_m[idx] / driven_dist_m * 100.0
            else:
                rel_err_long_perc[idx] = 0.0
                rel_err_lat_perc[idx] = 0.0

    else:
        logging.warning("Array dimensions do not match for CalcOdoError!")
    return abs_err_long_m, abs_err_lat_m, driven_dist_arr_m, rel_err_long_perc, rel_err_lat_perc


def get_relative_positional_error_per_meter(gt, estimated, time):
    """Calculates relative longitudinal and lateral position error with GT and Estimate data"""
    relative_error_per_meter = {"error": [], "time": []}
    current_dist = 0
    reference_dist = 0
    for d_est, d_gt, t in zip(estimated, gt, time):
        if not np.isnan(d_est):
            if d_est and d_gt:
                current_dist += d_est
                reference_dist += d_gt
                if current_dist >= 1:  # check for 1 meter chunks
                    diff_dist = abs(reference_dist - current_dist)
                    relative_error_per_meter["error"].append(diff_dist)
                    relative_error_per_meter["time"].append(t)
                    current_dist = 0
                    reference_dist = 0
    return relative_error_per_meter


def plot_graphs_threshold(
    ap_time, deviation_list, deviate_error_list_name, threshold, threshold_name, x_axis, y_axis, error_mode="lines"
):
    """Method to plot graphs for threshold value comparison in report"""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=ap_time,
            y=[
                threshold,
            ]
            * len(ap_time),
            mode="lines",
            name=threshold_name,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=ap_time,
            y=deviation_list,
            mode=error_mode,
            name=deviate_error_list_name,
        )
    )
    fig.layout = go.Layout(
        yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title=x_axis, yaxis_title=y_axis
    )
    fig.update_layout(PlotlyTemplate.lgt_tmplt)
    fig.add_annotation(
        dict(
            font=dict(color="black", size=12),
            x=0,
            y=-0.12,
            showarrow=False,
            text=f"{deviate_error_list_name}  vs {threshold_name}",
            textangle=0,
            xanchor="left",
            xref="paper",
            yref="paper",
        )
    )
    return fig


def plot_graphs(ap_time, est_sig, est_sig_name, gt_sig, gt_sig_name, x_axis, y_axis):
    """Method to plot graphs for estimate vs ground truth in report"""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=ap_time,
            y=est_sig,
            mode="lines",
            name=est_sig_name,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=ap_time,
            y=gt_sig,
            mode="lines",
            name=gt_sig_name,
        )
    )
    fig.layout = go.Layout(
        yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title=x_axis, yaxis_title=y_axis
    )
    fig.update_layout(PlotlyTemplate.lgt_tmplt)
    fig.add_annotation(
        dict(
            font=dict(color="black", size=12),
            x=0,
            y=-0.12,
            showarrow=False,
            text=f"{gt_sig_name} vs {est_sig_name}",
            textangle=0,
            xanchor="left",
            xref="paper",
            yref="paper",
        )
    )
    return fig


def plot_graphs_time(est_time, est_sig, est_sig_name, gt_time, gt_sig, gt_sig_name, x_axis, y_axis):
    """Method to plot graphs for estimate vs ground truth in report"""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=est_time,
            y=est_sig,
            mode="lines",
            name=est_sig_name,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=gt_time,
            y=gt_sig,
            mode="lines",
            name=gt_sig_name,
        )
    )
    fig.layout = go.Layout(
        yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title=x_axis, yaxis_title=y_axis
    )
    fig.update_layout(PlotlyTemplate.lgt_tmplt)
    fig.add_annotation(
        dict(
            font=dict(color="black", size=12),
            x=0,
            y=-0.12,
            showarrow=False,
            text=f"{gt_sig_name} vs {est_sig_name}",
            textangle=0,
            xanchor="left",
            xref="paper",
            yref="paper",
        )
    )
    return fig


def plot_graphs_signgle_signal(ap_time, sig, sig_name, title, x_axis, y_axis):
    """Method to plot graphs for singke signals plot in report"""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=ap_time,
            y=sig,
            mode="lines",
            name=sig_name,
        )
    )

    fig.layout = go.Layout(
        yaxis=dict(tickformat="14"),
        xaxis=dict(tickformat="14"),
        xaxis_title=x_axis,
        yaxis_title=y_axis,
        showlegend=True,
    )
    fig.update_layout(PlotlyTemplate.lgt_tmplt)
    fig.add_annotation(
        dict(
            font=dict(color="black", size=12),
            x=0,
            y=-0.12,
            showarrow=False,
            text=title,
            textangle=0,
            xanchor="left",
            xref="paper",
            yref="paper",
        )
    )
    return fig


def plot_graphs_two_threshold(
    ap_time,
    deviation_list,
    deviate_error_list_name,
    threshold1,
    threshold1_name,
    threshold2,
    threshold2_name,
    title,
    x_axis,
    y_axis,
):
    """Method to plot graphs for threshold value comparison in report"""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=ap_time,
            y=[
                threshold1,
            ]
            * len(ap_time),
            mode="lines",
            name=threshold1_name,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=ap_time,
            y=[
                threshold2,
            ]
            * len(ap_time),
            mode="lines",
            name=threshold2_name,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=ap_time,
            y=deviation_list,
            mode="lines",
            name=deviate_error_list_name,
        )
    )
    fig.layout = go.Layout(
        yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title=x_axis, yaxis_title=y_axis
    )
    fig.update_layout(PlotlyTemplate.lgt_tmplt)
    fig.add_annotation(
        dict(
            font=dict(color="black", size=12),
            x=0,
            y=-0.12,
            showarrow=False,
            text=title,
            textangle=0,
            xanchor="left",
            xref="paper",
            yref="paper",
        )
    )
    return fig


def max_consecutive_number(lst, number):
    """
    To find the maximum length of consecutive matching number in a given data-list
    :param lst: data list
    :param number: matching number
    :return: Variable to store the maximum length of consecutive number
    """
    max_len = 0
    current_len = 0  # Variable to store the current length of consecutive number

    for num in lst:
        if num == number:
            current_len += 1  # Increment the current length if the number is matching
        else:
            max_len = max(max_len, current_len)  # Update the max length if necessary
            current_len = 0  # Reset current length when a 0 is encountered

    # After the loop, we need to check once more in case the longest streak ends at the last element
    max_len = max(max_len, current_len)

    return max_len
