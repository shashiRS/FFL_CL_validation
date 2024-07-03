"""Here keeping commonly used methods to avoid duplicate code"""

import logging
import math

import numpy as np


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


def get_relative_positional_error_per_meter(gt_y, y_estimated):
    """Calculates relative longitudinal and lateral position error with GT and Estimate data"""
    relative_error_per_meter_list = list()
    current_dist = 0
    reference_dist = 0
    for d_est, d_gt in zip(y_estimated, gt_y):
        if not np.isnan(d_est):
            if d_est and d_gt:
                current_dist += d_est
                reference_dist += d_gt
                if current_dist >= 1:  # check for 1 meter chunks
                    diff_dist = abs(reference_dist - current_dist)
                    relative_error_per_meter_list.append(diff_dist)
                    current_dist = 0
                    reference_dist = 0
                else:
                    relative_error_per_meter_list.append(0)
            else:
                relative_error_per_meter_list.append(0)
    return relative_error_per_meter_list
