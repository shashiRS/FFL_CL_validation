"""File used to store all helper functions used in MOCO kpis"""

import math

import numpy as np
import pandas as pd
import yaml

import pl_parking.PLP.MF.constants as constants


def read_data_from_multiples_trajectories(observed_signals, csv_file):
    """Function used to collect data from multiple trajectories"""
    with open(observed_signals) as file:
        signals_data = yaml.safe_load(file)

    columns_to_include = {}

    for rule in signals_data["signals"]:
        signal_pattern = rule["signal"]
        rename_to = rule["rename"]

        for idx in range(constants.MoCo.Parameter.AP_M_MAX_NUM_TRAJ_CTRL_POINTS):
            signal_name = signal_pattern.replace("{id}", str(idx))
            new_name = f"{rename_to}_{idx}"
            columns_to_include[signal_name] = new_name

    df = pd.read_csv(csv_file)
    df_filtered = df[list(columns_to_include.keys())]
    df_filtered.rename(columns=columns_to_include, inplace=True)

    return df_filtered


def get_requested_driving_direction(row):
    """

    Get the requested driving direction defined by the longitudinal operation modes.

    :param row:  A pandas Series representing a row in a DataFrame. This row contains the necessary signals
                 get the requested driving direction, such a 'loCtrlRequestType', 'distance_interface', etc.
    :return: A int representing the requested driving direction.

    """
    if row["loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_BY_TRAJECTORY:
        if row["drivingForwardReq_nu"]:
            requested_driving_direction = constants.MoCo.RequestedDrivingDir.FORWARD
        else:
            requested_driving_direction = constants.MoCo.RequestedDrivingDir.BACKWARD

    if (
        row["loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_BY_DISTANCE
        or row["loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_BY_DISTANCE_VELOCITY
    ):
        requested_driving_direction = row["distance_interface"]

    if (
        row["loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_BY_VELOCITY
        or row["loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_VELOCITY_LIMITATION
    ):
        requested_driving_direction = row["velocity_interface"]

    if row["loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_BY_ACCELERATION:
        requested_driving_direction = row["acceleration_interface"]

    return requested_driving_direction


def evaluate_target_gear(row):
    """
    Determine the target gear based on various control signals within a given row.

    This function evaluates multiple conditions related to the vehicle's longitudinal
    and lateral control requests to decide the target gear for the vehicle. The
    target gear is determined based on the status of the vehicle's standstill,
    comfort stop requests, emergency stop requests, requested driving direction, and the validity
    of the trajectory path.

    :param row:  A pandas Series representing a row in a DataFrame. This row contains the necessary signals
                 to evaluate the target gear, such a 'activateLoCtrl', 'secureInStandstill', etc.
    :return: A enum representing the target gear, which can be 'Parking', 'Neutral', etc. based on the evaluation
             of input signal.
    """
    if row["activateLoCtrl"]:
        if row["secureInStandstill"] and row["calculated_standstill"]:
            return constants.HilCl.Gear.GEAR_P
        elif (row["comfortStopRequest"] and row["calculated_standstill"]) or (
            row["loCtrlRequestType"] == constants.MoCo.Parameter.LOCTRL_EMERGENCY_STOP
        ):
            return constants.HilCl.Gear.GEAR_N
        elif get_requested_driving_direction(row) == constants.MoCo.RequestedDrivingDir.FORWARD:
            return constants.HilCl.Gear.GEAR_D
        elif get_requested_driving_direction(row) == constants.MoCo.RequestedDrivingDir.BACKWARD:
            return constants.HilCl.Gear.GEAR_R
        else:
            return constants.HilCl.Gear.GEAR_N
    else:
        if not row["trajValid_nu"]:
            return constants.HilCl.Gear.GEAR_NOT_DEFINED


def check_comfort_stop_request(comfort_stop_req):
    """

    :param comfort_stop_req:
    :return:
    """
    return (
        constants.MoCo.LoDMCHoldRequestType.LODMC_HOLD_REQ_ON
        if comfort_stop_req
        else constants.MoCo.LoDMCHoldRequestType.LODMC_HOLD_REQ_OFF
    )


def is_vehicle_in_standstill(standstill_hold_cur_nu, standstill_secure_cur_nu, motion_state_nu):
    """
    Determine if the vehicle is in standstill based on LoDMC indications and vehicle odometry.

    :param standstill_hold_cur_nu: Boolean indicating if the vehicle is held in standstill by LoDMC
    :param standstill_secure_cur_nu: Boolean indicating if the vehicle is secured in standstill by LoDMC.
    :param motion_state_nu: Determined motion state
    :return:
    """
    if (standstill_hold_cur_nu or standstill_secure_cur_nu) and (
        motion_state_nu == constants.MoCo.MotionState.ODO_STANDSTILL
    ):
        return True
    else:
        return False


def is_not_close_to_requested(current_angle, requested_angle, first_steer_accur_rad):
    """
    Check if the current steer angle is close to the requested steer angle.

    :param current_angle:
    :param requested_angle:
    :param first_steer_accur_rad: The accuracy threshold for considering angle as 'close'
    :return: Boolean indicating if the current angle is close to the requested angle
    """
    return abs(current_angle - requested_angle) > first_steer_accur_rad


def is_steer_angle_close_to_static(steer_angle_velocity, min_steer_vel_rad):
    """
    Check if the current steer angle is close to static based on the steer angle velocity.

    :param steer_angle_velocity: The velocity of the steer angle.
    :param min_steer_vel_rad: The minimum threshold for the steer angle velocity to be considered close to static.
    :return: Boolean indicating if the steer angle velocity is close to static.
    """
    return abs(steer_angle_velocity) <= min_steer_vel_rad


def check_hold_request_due_to_steer_angle(vehicle_standstill, close_to_requested, angle_not_static):
    """
    Check if a hold request should be made due to the steer angle conditions.

    :param vehicle_standstill: Boolean indicating if the vehicle is in standstill.
    :param close_to_requested: Determine when the current steer angle is/are close to requested
    :param angle_not_static: Determine when the angle close to static is triggered
    :return: 'LodmcHoldReq.ON' if the vehicle is in standstill and the steer angle is not close, else 'LodmcHoldReq.OFF'
    """
    if vehicle_standstill and not close_to_requested:
        return constants.MoCo.LoDMCHoldRequestType.LODMC_HOLD_REQ_ON
    elif angle_not_static == 1:
        return constants.MoCo.LoDMCHoldRequestType.LODMC_HOLD_REQ_OFF
    else:
        return np.nan


def calculate_steer_angle_velocity(df):
    """
    Calculate the steering angle velocity for each row in the Dataframe.
    The steer angle velocity is determined as difference between current front wheel angle and the saved front wheel
    angle during last cycle (@satisfied_by{SWD_MFCINP_SetLastFrontWheelAngle_v001}). The result is divided by the sample
    time.
    :param df: A dataframe containing the columns 'timestamp' and 'current_front_wheel_angle'
    :return: The original DataFrame with an additional column 'steer_angle_velocity'
    """
    # calculate the time interval (sample_time) between each measurement in seconds
    df["sample_time"] = df["timestamp"].diff()
    # calculate de difference in the front wheel angle between each measurement
    df["angle_diff"] = df["steerAngFrontAxle_rad"].diff()

    # calculate the steering angle velocity
    df["steer_angle_velocity"] = df["angle_diff"] / (df["sample_time"] / 1000000000)
    # handle NaN values for the first row
    df["steer_angle_velocity"].fillna(0, inplace=True)

    return df


def front_SteerAngle_Req_radsec(df):
    """
    Calculating front steer angle velocity request in radian/second
    :param df: A dataframe containing the columns 'timestamp' and 'frontSteerAngReq_rad'
    :return: The original DataFrame with an additional column 'frontSteerAngReq_rad/sec'
    """
    # calculate the time interval (sample_time) between each measurement in seconds
    df["sample_time"] = df["timestamp"].diff()
    # calculate de difference in the front wheel angle between each measurement
    df["angle_diff"] = df["frontSteerAngReq_rad_at_wheels"].diff()

    df["frontSteerAngReq_rad_sec"] = df["angle_diff"] / (df["sample_time"] / 1000000000)
    df["frontSteerAngReq_rad_sec"].fillna(0, inplace=True)

    return df


def get_ego_position(row):
    """
    Calculate ego position based on the x and y coordinates.

    :param row: A series containing the columns 'xPosition_m' 'yPosition_m'.
    :return: A dictionary with the pos X  pos Y of the vehicle.
    """
    return {"x_position": row["xPosition_m"], "y_position": row["yPosition_m"]}


def get_planned_path(df):
    """
    Calculate the planned path from the DataFrame columns.

     Parameters:
     df (pd.DataFrame): A DataFrame containing columns for each trajectory control point,
                        like 'plannedTraj_x_m', 'plannedTraj_y_m', 'plannedTraj_yaw_rad', etc.
     Returns:
     list: A list of dictionaries, each representing a path_point in the planned path.
    """
    path_points = []
    for _, row in df.iterrows():
        path_point = {
            "x_traj_req_m": row["xTrajRAReq_m_0"],
            "y_traj_req_m": row["yTrajRAReq_m_0"],
            "yaw_angle_rad": row["yawReq_rad_0"],
            "curvature_1_p_m": row["crvRAReq_1pm"],
            "distance_to_stop_m": row["distanceToStopReq_m_0"],
            "velocity_limit_m_p_s": row["velocityLimitReq_mps_0"],
        }
        path_points.append(path_point)

    return path_points


def closest_point_on_line_segment(point, line_start, line_end):
    """
    Find the closest point on a line segment to a given point.

    Parameters:
        point: Tuple (x,y) representing the vehicle position.
        line_start: Tuple (x,y) representing the start of the line segment.
        line_end: Tuple (x,y) representing the end of the line segment.

    Returns:
        Tuple (x,y) of the nearest point on the line segment.

    """
    line_vec = np.array(line_end) - np.array(line_start)
    point_vec = np.array(point) - np.array(line_start)

    line_len = np.dot(line_vec, line_vec)
    if line_len == 0.0:
        return line_start

    t = max(0, min(1, np.dot(point_vec, line_vec) / line_len))

    closest_point = np.array(line_start) + t * line_vec
    return tuple(closest_point)


def get_orthogonal_projection_point(ego_position, planned_path):
    """
    Calculate the orthogonal projection point of the ego position onto the planned path.

    Parameters:
    ego_position (tuple): The (x, y) coordinates of the ego position.
    planned_path (list): A list of path points, each a dictionary with 'position' as a key.

    Returns:
    (float, float): The coordinates of the orthogonal projection point.
    """
    car_position = (ego_position["x_position"], ego_position["y_position"])
    closest_point = None
    min_distance = float("inf")

    for i in range(len(planned_path) - 1):
        line_start = (planned_path[i]["x_traj_req_m"], planned_path[i]["y_traj_req_m"])
        line_end = (planned_path[i + 1]["x_traj_req_m"], planned_path[i + 1]["y_traj_req_m"])

        current_closest = closest_point_on_line_segment(car_position, line_start, line_end)
        current_distance = np.linalg.norm(np.array(car_position) - np.array(current_closest))

        if current_distance < min_distance:
            min_distance = current_distance
            closest_point = current_closest

    return closest_point


def calculate_lateral_deviation(ego_position, orthogonal_projection_point):
    """
    Calculate the lateral deviation of the ego from the planned path.

    Parameters:
    ego_position (tuple): The (x, y) coordinates of the ego position.
    orthogonal_projection_point (tuple): The (x, y) coordinates of the orthogonal projection point on the path.

    Returns:
    float: The lateral deviation from the path in the same units as the positions.
    """
    car_position = (ego_position["x_position"], ego_position["x_position"])
    deviation_vector = np.array(car_position) - np.array(orthogonal_projection_point)
    lateral_deviation = np.linalg.norm(deviation_vector)

    return lateral_deviation


def calculate_orientation_deviation_from_path(
    ego_yaw_angle: float, planned_path: list, orthogonal_projection_point: tuple
) -> float:
    """
    Calculates the orientation deviation from path as the angular difference between the yaw_angle_rad of the
    planned path at the orthogonal projection point and the ego's yaw angle.

    Parameters:
        ego_yaw_angle: the car's yaw angle
        planned_path: List of dictionaries, each representing a path point
        orthogonal_projection_point: The orthogonal projection point coordinates

    Return:
        The calculated orientation deviation from path.

    """
    # find the closest path point to the orthogonal projection point
    closest_path_point = min(
        planned_path,
        key=lambda point: np.linalg.norm(
            np.array([point["x_traj_req_m"], point["y_traj_req_m"]]) - np.array(orthogonal_projection_point)
        ),
    )
    path_yaw_angle = closest_path_point["yaw_angle_rad"]

    # calculate the orientation deviation from path
    orientation_deviation_from_path = path_yaw_angle - ego_yaw_angle

    return orientation_deviation_from_path


def check_target_gear(dataframe):
    """Function used to check the target gear"""
    df = dataframe

    parking_cond = df.loc[
        (df["calculated_target_gear"] == constants.HilCl.Gear.GEAR_P)
        & (df["calculated_target_gear"] != df["gearCur_nu"])
    ]

    neutral_cond = df.loc[
        (df["calculated_target_gear"] == constants.HilCl.Gear.GEAR_N)
        & (df["calculated_target_gear"] != df["gearCur_nu"])
    ]

    drive_cond = df.loc[
        (df["calculated_target_gear"] == constants.HilCl.Gear.GEAR_D)
        & (df["calculated_target_gear"] != df["gearCur_nu"])
    ]

    reverse_cond = df.loc[
        (df["calculated_target_gear"] == constants.HilCl.Gear.GEAR_R)
        & (df["calculated_target_gear"] != df["gearCur_nu"])
    ]

    not_defined_cond = df.loc[
        (df["calculated_target_gear"] == constants.HilCl.Gear.GEAR_NOT_DEFINED)
        & (df["calculated_target_gear"] != df["gearCur_nu"])
    ]

    if (
        not parking_cond.empty
        or not neutral_cond.empty
        or not drive_cond.empty
        or not reverse_cond.empty
        or not not_defined_cond.empty
    ):

        return True
    else:
        return False


def get_steer_angle_close_to_static_trigger(df):
    """
    Calculates the differences between current and past steer angle close to static state in order to get when
    the trigger from False to True is happening
    :param df: df with measurements needed to determine the steer angle close to static
    :return: df with new columns where steer angle close to static condition met and when the trigger from
    False to True should happen
    """
    df["steer_angle_close_to_static"] = df["steer_angle_velocity"] <= constants.MoCo.Parameter.MIN_STEER_VEL_RADPS
    df["steer_angle_close_to_static"] = df["steer_angle_close_to_static"].map({True: 1, False: 0})
    df["angle_close_to_static_triggered"] = df["steer_angle_close_to_static"].diff()
    df["angle_close_to_static_triggered"].fillna(0, inplace=True)

    return df


def get_hold_request_current_state(df):
    """
    Determine when the hold request should mantain their state based on ON/OFF triggers previously calculated and
    defined in dataframe for those that are not nan value

    :param df: df with calculated hold request following test conditions
    :return: df with calculated hold request state for whole measurement
    """
    df["calculated_hold_req_nu"].values[0] = 0
    for i in range(1, len(df)):
        if math.isnan(df["calculated_hold_req_nu"].values[i]):
            df["calculated_hold_req_nu"].values[i] = df["calculated_hold_req_nu"].values[i - 1]

    return df


def count_e_signal_status_signal(dataframe):
    """Check if the eSigstatus is valid (== 1)"""
    filtered_columns = [col for col in dataframe.columns if "eSigStatus" in col]

    return filtered_columns


def calculate_comfortable_standstill_steering_duration(df):
    """
    Calculate the duration that comfortable standstill was active.

    Parameters:
        df: A pandas dataframe with the data to calculate the duration

    Returns:
        A dataframe with an extra column with the duration for which comfortable standstill was active from the
        first occurrence to just before it deactivate.

    """
    # identify consecutive blocks of True
    df["block"] = (df["calculated_comfortable_standstill"] != df["calculated_comfortable_standstill"].shift(1)).cumsum()

    active_periods = df[int(df["calculated_comfortable_standstill"]) == 1]
    # calculate the duration for each active block
    durations = active_periods.groupby("block").apply(lambda x: (x["ts"].max() - x["ts"].min()))

    # mapping the active blocks durations
    df["comfortable_active_time"] = df["block"].map(durations)
    df["comfortable_active_time"] = df["comfortable_active_time"].fillna(0)
    # convert from microseconds to seconds
    df["comfortable_active_time"] = df["comfortable_active_time"] / 1_000_000

    return df
