"""File used to store all helper functions used in MOCO kpis"""

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
        if (row["secureInStandstill"] and row["calculated_standstill"]) or (
            row["gearCur_nu"] == constants.HilCl.Gear.GEAR_P and row['comfortStopRequest'] and
            row["calculated_standstill"]
        ) or (
            row["gearCur_nu"] == constants.HilCl.Gear.GEAR_P and
            row["loCtrlRequestType"] == constants.MoCo.Parameter.LOCTRL_EMERGENCY_STOP
        ):
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


def check_hold_request_due_to_steer_angle(vehicle_standstill, not_close_to_requested, angle_static):
    """
    Check if a hold request should be made due to the steer angle conditions.

    :param vehicle_standstill: Boolean indicating if the vehicle is in standstill.
    :param not_close_to_requested: Determine when the current steer angle is/are close to requested
    :param angle_static: Determine when the angle close to static is triggered
    :return: 'LodmcHoldReq.ON' if the vehicle is in standstill and the steer angle is not close, else 'LodmcHoldReq.OFF'
    """
    if vehicle_standstill and not_close_to_requested:
        return constants.MoCo.LoDMCHoldRequestType.LODMC_HOLD_REQ_ON
    elif vehicle_standstill and not not_close_to_requested and angle_static == 1:
        return constants.MoCo.LoDMCHoldRequestType.LODMC_HOLD_REQ_OFF
    elif vehicle_standstill and not_close_to_requested and angle_static == 0:
        return constants.MoCo.LoDMCHoldRequestType.LODMC_HOLD_REQ_ON
    else:
        return constants.MoCo.LoDMCHoldRequestType.LODMC_HOLD_REQ_OFF


def check_veh_secured_standstill(vehicle_standstill, not_close_to_requested, angle_static):
    """
    Check for lateral vehicle secured standstill due to the steer angle conditions.

    :param vehicle_standstill: Boolean indicating if the vehicle is in standstill.
    :param not_close_to_requested: Determine when the current steer angle is/are close to requested
    :param angle_static: Determine when the angle close to static
    :return: 'TRUE' if the vehicle is in secured standstill, else 'FALSE'
    """
    if vehicle_standstill and not not_close_to_requested and angle_static == 1:
        return constants.MoCo.Parameter.TRUE
    else:
        return constants.MoCo.Parameter.FALSE


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
    # calculate the difference in the front wheel angle between each measurement
    df["angle_diff"] = df["frontSteerAngReq_rad"].diff()
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
    df["steer_angle_close_to_static"] = (
        abs(df["steer_angle_velocity"]) < constants.MoCo.Parameter.AP_C_PC_MIN_STEER_VEL_RADPS
    )
    df["steer_angle_close_to_static"] = df["steer_angle_close_to_static"].map({True: 1, False: 0})
    df["angle_close_to_static_triggered"] = df["steer_angle_close_to_static"].diff()
    df["angle_close_to_static_triggered"].fillna(0, inplace=True)

    return df


def get_steer_angle_not_close_to_static_trigger(df):
    """
    Calculates the differences between current and past steer angle not close to static state in order to get when
    the trigger from False to True is happening
    :param df: df with measurements needed to determine the steer angle close to static
    :return: df with new columns where steer angle not close to static condition met and when the trigger from
    False to True should happen
    """
    df["steer_angle_not_close_to_static"] = (
        abs(df["steer_angle_velocity"]) >= constants.MoCo.Parameter.AP_C_PC_MIN_STEER_VEL_RADPS
    )
    df["steer_angle_not_close_to_static"] = df["steer_angle_not_close_to_static"].map({True: 1, False: 0})
    df["steer_angle_not_close_to_static"] = df["steer_angle_not_close_to_static"].diff()
    df["steer_angle_not_close_to_static"].fillna(0, inplace=True)

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
    df["calculated_comfortable_standstill_check"] = df["calculated_comfortable_standstill"].astype(bool)
    if df["calculated_comfortable_standstill_check"].any():
        # # identify consecutive blocks of True
        df["block"] = (
            df["calculated_comfortable_standstill"] != df["calculated_comfortable_standstill"].shift(1)
        ).cumsum()
        active_periods = df[(df["calculated_comfortable_standstill"].astype(int)) == 1]
        df["calculated_comfortable_standstill_updated"] = df["calculated_comfortable_standstill"]
        # Checking start timestamp and end timestamp for each active block
        start_end_times = []
        for _, group in active_periods.groupby("block"):
            start_end_times.append((group["timestamp"].iloc[0], group["timestamp"].iloc[-1]))
        # Checking delta duration between two consecutive active blocks
        for i in range(1, len(start_end_times)):
            previous_end_time = start_end_times[i - 1][1]
            current_start_time = start_end_times[i][0]
            delta = current_start_time - previous_end_time
            # Consider delta time gap less than or equal to 0.1 sec
            if delta <= 100_000_000:
                df.loc[
                    (df.timestamp > previous_end_time) & (df.timestamp < current_start_time),
                    "calculated_comfortable_standstill_updated",
                ] = True
        # identify consecutive blocks with addition of delta gap.
        df["calculated_block"] = (
            df["calculated_comfortable_standstill_updated"] != df["calculated_comfortable_standstill_updated"].shift(1)
        ).cumsum()
        active_periods_updated = df[(df["calculated_comfortable_standstill_updated"].astype(int)) == 1]

        # calculate the duration for each active block
        durations = active_periods_updated.groupby("calculated_block").apply(
            lambda x: (
                (x["timestamp"].max() - x["timestamp"].min())
                if (x["timestamp"].max()) != (x["timestamp"].min())
                else 1_000_000_000
            )
        )
        # mapping the active blocks durations
        df["comfortable_active_time"] = df["calculated_block"].map(durations)
        df["comfortable_active_time"] = df["comfortable_active_time"].fillna(0)
        # convert from microseconds to seconds
        df["comfortable_active_time"] = df["comfortable_active_time"] / 1_000_000_000
    else:
        df["comfortable_active_time"] = 0

    return df


def calculate_additional_front_steer_angle_request_delta(df):
    """
    Calculate additional front steer angle request delta (=compensate tire deformation).
    Parameters:
        df: A pandas dataframe with the data.
    Returns:
        A dataframe with an extra column with target value .
    """
    # df["laCtrlRequestType"] == constants.MoCo.LaCtrlRequestType.LACTRL_COMF_ANGLE_ADJUSTMENT
    steer_angle_delta = df.apply(lambda x: (x["steerAngReqFront_rad"] - x["steerAngFrontAxle_rad"]), axis=1)
    df["steer_angle_delta"] = df["laCtrlRequestType"].map(steer_angle_delta)
    df["steer_angle_delta"] = df["steer_angle_delta"].fillna(0)

    # Calculate additional front steer angle request fraction
    df["additional_front_steer_angle_request_fraction"] = (
        df["steer_angle_delta"] * constants.MoCo.Parameter.AP_C_COMP_TIRE_DEF_FACTOR_NU
    )

    # Target value calculation
    target_value = df.apply(
        lambda x: (x["steerAngReqFront_rad"] + x["additional_front_steer_angle_request_fraction"]), axis=1
    )
    df["target_value"] = df["additional_front_steer_angle_request_fraction"].map(target_value)
    df["target_value"] = df["target_value"].fillna(0)

    return df


def calculate_distance_to_stop(df, loCtrlRequestType_param):
    """Calculate the new requested distance to stop based on the current distance,
    vehicle velocity, and the rate limit based on the maximum of vehicle velocity
    and minimum parking velocity.
    Parameters:
    - df: A pandas Series (representing a df of the DataFrame).
    Returns:
    - newDistanceToStopReq_m: The updated distance to stop (in meters).
    """
    df["time_diff"] = df["timestamp"].diff()
    df["sample_time"] = df["time_diff"] / 1000000000
    min_parking_velocity = constants.MoCo.Parameter.AP_C_MIN_PARKING_VEL_MPS

    # Check for changes from False to True to determine activation cycle
    df["activateLoCtrlChanged"] = df["activateLoCtrl"].diff()
    df["statusChange"] = df["activateLoCtrlChanged"] == 1

    # Calculate the maximum change rate
    df["max_change_rate"] = np.maximum(np.abs(df["longiVelocity_mps"]), min_parking_velocity)
    df["newSegmentStarted_nu"] = df["newSegmentStarted_nu"].astype(bool)

    if loCtrlRequestType_param == 1:
        df = check_phase_1_wheel_stopper_approaching_feature(df, loCtrlRequestType_param)
        df = check_phase_2_and_3_wheel_stopper_approaching_feature(df)
        df["input_distance"] = df["calculated_distanceToStopReq_m"]
    else:
        df["input_distance"] = df["input_distanceToStopReq_m"]

    df["newDistanceToStopReq_m"] = 0

    previous_distance = 0
    for index, row in df.iterrows():
        if row["activateLoCtrl"] == 1 and row["loCtrlRequestType"] == loCtrlRequestType_param:
            requested_distance = row["input_distance"]
            # Check for exceptions to bypass ramp-up
            if row["statusChange"] or row["newSegmentStarted_nu"] or row["calculated_standstill"]:
                # Allow a direct jump to the requested distance
                actual_distance = requested_distance
            else:
                # Ramp up the distance gradually, considering the velocity limit
                max_possible_increase = previous_distance + (row["max_change_rate"] * row["sample_time"])

                # The distance can only increase up to the requested limit, but no more than the ramp-up
                if max_possible_increase < requested_distance:
                    actual_distance = max_possible_increase
                else:
                    actual_distance = requested_distance

            # Update the DataFrame with the actual distance at this time step
            df.at[index, "newDistanceToStopReq_m"] = actual_distance

            # Store the current actual distance as the previous distance for the next iteration
            previous_distance = actual_distance
        else:
            df.at[index, "newDistanceToStopReq_m"] = 0

    # Check calculated output distance to stop value (newDistanceToStopReq_m) is within [0, {AP_C_MAX_DIST_TO_STOP_M}].
    # Apply the conditions to update the column
    max_limit = constants.MoCo.Parameter.AP_C_MAX_DIST_TO_STOP_M
    df["newDistanceToStopReq_m"] = df["newDistanceToStopReq_m"].apply(
        lambda x: 0 if x < 0 else (max_limit if x > max_limit else x)
    )

    df["delta"] = df["distanceToStopReq_m"].diff() / df["sample_time"]
    # Update distance_grad based on conditional logic
    df["distance_grad_mps"] = df.apply(
        lambda row: (
            0  # Set distance_grad to 0 if statusChange or other flags are set
            if row["statusChange"] or row["newSegmentStarted_nu"] or row["calculated_standstill"]
            else (
                row["delta"]  # Calculate delta only if activateLoCtrl and loCtrlRequestType match
                if row["activateLoCtrl"] and row["loCtrlRequestType"] == loCtrlRequestType_param
                else 0  # Otherwise set distance_grad to 0
            )
        ),
        axis=1,
    )
    return df


def check_velocity_ramp_up(df):
    """Check exceptions for velocity request ramp up and calculate new velocity"""
    df = adjust_velocity_based_on_wheel_stopper(df)
    acceleration_limit = constants.MoCo.Parameter.AP_C_VL_VEL_RAMP_LIMIT_MPS2
    df["time_diff"] = df["timestamp"].diff()
    df["sample_time"] = df["time_diff"] / 1000000000

    shift_ts = constants.MoCo.Parameter.AP_C_PC_VELO_PREVIEW_TIME_S * 1000000000

    df["condition"] = (df["activateLoCtrl"].astype(bool)) & (
        df["loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_BY_TRAJECTORY
    )

    df["StatusChanged"] = (df["newSegmentStarted_nu"].astype(int)).diff()
    df["isNewSegmentChanged"] = df["StatusChanged"] == 1

    # Filter the DataFrame where condition is True and newSegmentStarted_nu is True
    filtered_df = df[df["condition"] & df["isNewSegmentChanged"]]

    # Initialize the mask column in the DataFrame to False for all rows
    df["mask"] = False  # Initialize mask as a column of False values
    # Iterate over each row in the filtered DataFrame
    for _, row in filtered_df.iterrows():
        # Calculate the timestamp offset for each row
        timestamp = row["timestamp"]
        timestamp_offset = timestamp - shift_ts

        # Check if the condition is True for the timestamp_offset
        # We need to ensure that `timestamp_offset` falls within the valid range
        condition_offset_met = df.loc[df["timestamp"] == timestamp_offset, "condition"].any()

        # If the condition is True at the timestamp_offset, fill the values
        if condition_offset_met:
            # Find the range of rows that fall between timestamp_offset and timestamp
            df.loc[(df["timestamp"] >= timestamp_offset) & (df["timestamp"] <= timestamp), "mask"] = True

    df["previewedVelocity_mps"] = df["velocityFromPathPoints"]
    df.loc[df["mask"], "previewedVelocity_mps"] = df["calculated_inputVelocity_mps"]

    # Handle NaN values caused by the shift (e.g., in the last few rows)
    df["previewedVelocity_mps"].ffill(inplace=True)

    # Check for changes from False to True to determine activation cycle
    df["activateLoCtrlChanged"] = df["activateLoCtrl"].diff()
    df["statusChange"] = df["activateLoCtrlChanged"] == 1

    df["newSegmentStarted_nu"] = df["newSegmentStarted_nu"].astype(bool)
    df["calculated_velocityLimit"] = 0

    # "Verify that the component is in standstill"
    df["calculated_standstill"] = df.apply(
        lambda row: is_vehicle_in_standstill(
            row["standstillHoldCur_nu"], row["standstillSecureCur_nu"], row["motionStatus_nu"]
        ),
        axis=1,
    )

    previous_velocity = 0
    for index, row in df.iterrows():
        # Get the requested velocity limit at this time step
        if (
            row["activateLoCtrl"] == 1
            and row["loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_BY_TRAJECTORY
        ):
            requested_velocity = row["previewedVelocity_mps"]

            # Check for exceptions to bypass ramp-up
            if row["statusChange"] or row["newSegmentStarted_nu"] or row["calculated_standstill"]:
                # Allow a direct jump to the requested velocity
                actual_velocity = requested_velocity
            else:
                # Ramp up the velocity gradually, considering the acceleration limit
                max_possible_increase = previous_velocity + (acceleration_limit * row["sample_time"])

                # The velocity can only increase up to the requested limit, but no faster than the ramp-up
                if max_possible_increase < requested_velocity:
                    actual_velocity = max_possible_increase
                else:
                    actual_velocity = requested_velocity

            # Update the DataFrame with the actual velocity at this time step
            df.at[index, "calculated_velocityLimit"] = actual_velocity

            # Store the current actual velocity as the previous velocity for the next iteration
            previous_velocity = actual_velocity
        else:
            df.at[index, "calculated_velocityLimit"] = 0

    ##Check for if any wheel is closer to wheelstopper then calculated velocity (calculated_velocityLimit) should be set to upper velocity limit
    upper_vel_limit = constants.MoCo.Parameter.AP_C_WFC_WS_VEL_LIMIT_MPS
    df.loc[
        (df["check_if_any_wheel_closer"]),
        "calculated_velocityLimit",
    ] = upper_vel_limit

    return df


def check_preview_distance(df):
    """Calculate the preview distance dynamically based on velocity at each time step"""
    df["velocityFromPathPoints"] = 0
    df["calculated_inputVelocity_mps"] = 0
    df["current_idx"] = 0
    df["calculated_idx"] = 0
    path_points = constants.MoCo.Parameter.AP_M_MAX_NUM_TRAJ_CTRL_POINTS

    for index, row in df.iterrows():
        df.loc[index, "current_idx"] = int(row["currentTrajectoryIndex_nu"])
        current_idx = int(row["currentTrajectoryIndex_nu"])
        col1 = f"distanceToStopReq_m_{current_idx}"
        col2 = f"distanceToStopReq_m_{current_idx + 1}"
        col3 = f"velocityLimitReq_mps_{current_idx}"
        col4 = f"velocityLimitReq_mps_{current_idx + 1}"
        df.loc[index, "calculated_inputVelocity_mps"] = row[col3] + (
            (row[col4] - row[col3]) * row["trajIntermediateValueRaw_perc"]
        )

        # Calculate the interpolated distanceToStopReq and velocityLimitReq_mps for each row
        row["ego_position"] = row[col1] + ((row[col2] - row[col1]) * row["trajIntermediateValueRaw_perc"])

        row["preview_distance"] = abs(row["longiVelocity_mps"]) * constants.MoCo.Parameter.AP_C_PC_VELO_PREVIEW_TIME_S
        row["actual_preview_distance"] = row["ego_position"] - row["preview_distance"]

        # Initialize a flag to track if a valid path point is selected
        valid_path_point_found = False

        for i in range(path_points - 1):
            col5 = f"distanceToStopReq_m_{i}"
            if row[col5] <= abs(row["actual_preview_distance"]):
                col6 = f"velocityLimitReq_mps_{i}"
                if i > 0:  # Check to ensure i-1 is valid
                    col7 = f"velocityLimitReq_mps_{i - 1}"
                else:
                    col7 = f"velocityLimitReq_mps_{i}"

                df.loc[index, "calculated_idx"] = i
                df.loc[index, "velocityFromPathPoints"] = row[col7] + (
                    (row[col6] - row[col7]) * row["trajIntermediateValueRaw_perc"]
                )
                # Flag that a valid path point was found and break out of the loop
                valid_path_point_found = True
                break
        # If no valid path point is found, assign a default value to 'velocityFromPathPoints'
        if not valid_path_point_found:
            df.loc[index, "velocityFromPathPoints"] = 0  # or some other default value
    return df


def check_active_replan(df):
    """Check mReplanSuccessful_nu and mNumOfReplanCalls activation for velocity comparison"""
    # Filter the DataFrame based on the conditions
    df["condition"] = (df["activateLoCtrl"].astype(bool)) & (
        df["loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_BY_TRAJECTORY
    )

    df_check = df[df["condition"] & ((df["mReplanSuccessful_nu"] == 1) & (df["mNumOfReplanCalls"] > 0))]
    # Define the shift in timestamps (preview time in nanoseconds)
    shift_ts = constants.MoCo.Parameter.AP_C_PC_VELO_PREVIEW_TIME_S * 1000000000

    # Get the timestamp(s) from the filtered DataFrame
    df["checkReplan"] = False
    for _, row in df_check.iterrows():
        # Calculate the timestamp offset for each row
        timestamp1 = row["timestamp"]
        timestamp_offset1 = timestamp1 - shift_ts

        condition_offset_met1 = df.loc[df["timestamp"] == timestamp_offset1, "condition"].any()

        # If the condition is True at the timestamp_offset, fill the values
        if condition_offset_met1:
            # Find the range of rows that fall between timestamp_offset and timestamp
            df.loc[(df["timestamp"] >= timestamp_offset1) & (df["timestamp"] <= timestamp1), "checkReplan"] = True
    return df


def calculate_distance_before_first_path_point(row):
    """Calculate distance between orthogonal projection point on extrapolated distance and First path point"""
    # Condition check: if trajIntermediateValueRaw_perc <0. calculate the distance
    if row["trajIntermediateValueRaw_perc"] < 0:
        # Calculate difference between two distanceToStopReq values
        diff_distanceToStopReq = row["distanceToStopReq_m_1"] - row["distanceToStopReq_m_0"]
        distance_m = diff_distanceToStopReq * (row["trajIntermediateValueRaw_perc"])
        return distance_m
    else:
        return 0


def calculate_distance_behind_last_path_point(row):
    """Calculate distance between orthogonal projection point on extrapolated distance and last path point"""
    # Condition check: if trajIntermediateValueRaw_perc >1. calculate the distance
    if row["trajIntermediateValueRaw_perc"] > 1:
        # Calculate difference between two distanceToStopReq values
        path_points = constants.MoCo.Parameter.AP_M_MAX_NUM_TRAJ_CTRL_POINTS
        # Example: when numValidCtrlPoints_nu is 3, then this means the first two distanceToStopReq_m show values and the third one can be 0,
        # So need to consider (["numValidCtrlPoints_nu"] - 1) for distanceToStopReq_m for valid column
        row["ValidCtrlPoints"] = row["numValidCtrlPoints_nu"] - 1
        x1 = min(int(row["ValidCtrlPoints"]), (path_points - 1))
        x2 = min(int(row["ValidCtrlPoints"] - 1), (path_points - 2))
        col1 = f"distanceToStopReq_m_{x1}"
        col2 = f"distanceToStopReq_m_{x2}"

        row["diff_distanceToStopReq"] = row[col1] - row[col2]
        # substracted 1 from trajIntermediateValueRaw_perc as it is outside trajectory
        distance_m = row["diff_distanceToStopReq"] * (row["trajIntermediateValueRaw_perc"] - 1)
        return abs(distance_m)
    else:
        return 0


def calculating_driving_resistance(df):
    """Calculating driving resistance and transformation to the wheel individual driving resistance if not MFMDrivingResistanceType.MFM_NONE(0)"""
    df["reduce_resistance_distance"] = df.apply(
        lambda x: (x["distanceToStopReq_m_0"] - x["distanceToStopReqInterExtrapolTraj_m"]), axis=1
    )

    df["calculated_driving_resistance_FL"] = df.apply(
        lambda x: (x["distance_m_0"] - x["reduce_resistance_distance"]), axis=1
    )
    df["calculated_drivingResistance_FL"] = 0
    df.loc[
        (df["drivingResistanceType_0"] != constants.MoCo.MFMDrivingResistanceType.MFM_NONE),
        "calculated_drivingResistance_FL",
    ] = df["calculated_driving_resistance_FL"]

    df["calculated_driving_resistance_RL"] = df.apply(
        lambda x: (x["distance_m_1"] - x["reduce_resistance_distance"]), axis=1
    )
    df["calculated_drivingResistance_RL"] = 0
    df.loc[
        (df["drivingResistanceType_1"] != constants.MoCo.MFMDrivingResistanceType.MFM_NONE),
        "calculated_drivingResistance_RL",
    ] = df["calculated_driving_resistance_RL"]

    df["calculated_driving_resistance_RR"] = df.apply(
        lambda x: (x["distance_m_2"] - x["reduce_resistance_distance"]), axis=1
    )
    df["calculated_drivingResistance_RR"] = 0
    df.loc[
        (df["drivingResistanceType_2"] != constants.MoCo.MFMDrivingResistanceType.MFM_NONE),
        "calculated_drivingResistance_RR",
    ] = df["calculated_driving_resistance_RR"]

    df["calculated_driving_resistance_FR"] = df.apply(
        lambda x: (x["distance_m_3"] - x["reduce_resistance_distance"]), axis=1
    )
    df["calculated_drivingResistance_FR"] = 0
    df.loc[
        (df["drivingResistanceType_3"] != constants.MoCo.MFMDrivingResistanceType.MFM_NONE),
        "calculated_drivingResistance_FR",
    ] = df["calculated_driving_resistance_FR"]

    return df


def check_curvature_step(df):
    """Identifing curvature steps and determine the previewed velocity based on curvature steps."""
    df = check_preview_distance(df)
    df = check_velocity_ramp_up(df)
    df["condition"] = (df["activateLoCtrl"].astype(bool)) & (
        df["loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_BY_TRAJECTORY
    )
    df["calculated_previewedVelocity_mps"] = df["calculated_velocityLimit"]
    df["condition_curvature"] = False
    df["condition"] = False
    df["curvature_step"] = 0
    signal_names = constants.MoCo.Parameter.AP_M_MAX_NUM_TRAJ_CTRL_POINTS

    for _, row in df.iterrows():
        for i in range(signal_names - 1):
            if i >= row["current_idx"] and i < row["calculated_idx"]:
                # Calculate the distance between two consecutive planned path points
                col1 = f"distanceToStopReq_m_{i}"
                col2 = f"distanceToStopReq_m_{i + 1}"
                row[f"distanceBetweenPoints_m_{i}"] = abs(row[col1] - row[col2])

                col3 = "longiVelocity_mps"
                col4 = f"velocityLimitReq_mps_{i}"
                row[f"calculated_min_velocity_{i}"] = min(abs(row[col3]), row[col4])

                # Calculate the curvature threshold using the provided constant values
                if row[f"calculated_min_velocity_{i}"] > 0:
                    row[f"curvatureThreshold_1pm_{i}"] = (
                        constants.MoCo.Parameter.AP_V_MAX_STEER_ANG_VEL_RADPS * row[f"distanceBetweenPoints_m_{i}"]
                    ) / (constants.MoCo.Parameter.AP_V_WHEELBASE_M * row[f"calculated_min_velocity_{i}"])
                else:
                    row[f"curvatureThreshold_1pm_{i}"] = 0

                # Calculate the change in curvature between consecutive points
                col5 = f"crvRARReq_1pm_{i}"
                col6 = f"crvRARReq_1pm_{i + 1}"
                row[f"curvatureChange_{i}"] = abs(row[col5] - row[col6])

                # Identify curvature steps based on the calculated change and threshold
                row[f"curvature_step_{i}"] = row[f"curvatureChange_{i}"] > row[f"curvatureThreshold_1pm_{i}"]

                # Calculate minimum velocity limit of the used path points for preview
                col7 = f"velocityLimitReq_mps_{i}"
                col8 = f"velocityLimitReq_mps_{i+1}"
                row[f"Min_velocity{i}"] = min(row[col7], row[col8])

                # Apply condition for curvature_step and set previewedVelocity_mps to calculated_min_velocity where the curvature condition is True
                if row["condition"] and row[f"curvature_step_{i}"]:
                    row["condition_curvature"] = True

                if row["condition_curvature"]:
                    row["calculated_previewedVelocity_mps"] = row[f"Min_velocity{i}"]
                    row["curvature_step"] = 1
    return df


def calculate_interpolated_curvature(df):
    """Calculate Linear interpolated curvature value (trajRequestPort.plannedTraj[].crvRAReq_1pm) at position on path."""
    # Initialize the "interpolated_curvature" column if not already in the DataFrame
    if "interpolated_curvature" not in df.columns:
        df["interpolated_curvature"] = 0

    # Loop through each row and apply the conditions
    for index, row in df.iterrows():
        if row["trajIntermediateValueRaw_perc"] < 0:
            df.at[index, "interpolated_curvature"] = row["crvRARReq_1pm_0"]
        elif row["trajIntermediateValueRaw_perc"] > 1:
            df.at[index, "interpolated_curvature"] = row["crvRARReq_1pm_19"]
        else:
            row["interpolated_curvature"] = 0
    return df


def calculate_upper_velocity_limit_max_lat_acc(df):
    """Calculating upper velocity limit and update the vehicle's velocity limit based on maximum lateral acceleration and curvature of the path."""
    df = calculate_interpolated_curvature(df)
    max_abs_vel_lat_acc = constants.MoCo.Parameter.AP_G_MAX_AVG_LAT_ACCEL_MPS2

    # Calculate the upper velocity limit
    df["upper_velocity_limit"] = np.sqrt(np.abs(max_abs_vel_lat_acc / df["interpolated_curvature"]))

    condition = (
        (df["activateLoCtrl"] == 1)
        & (df["activateLaCtrl"] == 1)
        & (df["laCtrlRequestType"] == constants.MoCo.LaCtrlRequestType.LACTRL_BY_TRAJECTORY)
        & (df["upper_velocity_limit"] < df["calculated_velocityLimit"])
    )
    df["calculated_velocity"] = df["calculated_velocityLimit"]
    df.loc[condition, "calculated_velocity"] = df["upper_velocity_limit"]
    return df


def calculate_upper_velocity_limit_max_lat_yaw_rate(df):
    """Calculating upper velocity limit and update the vehicle's velocity limit based on maximum absolute lateral vehicle yaw rate
    {AP_G_MAX_AVG_YAW_RATE_RADPS} at rear axle center is not exceeded based on the interpolated curvature of path.
    """
    df = calculate_interpolated_curvature(df)

    max_abs_lat_yaw_rate = constants.MoCo.Parameter.AP_G_MAX_AVG_YAW_RATE_RADPS

    # Calculate the upper velocity limit
    df["upper_velocity_limit"] = np.abs(max_abs_lat_yaw_rate / df["interpolated_curvature"])

    condition = (
        (df["activateLoCtrl"] == 1)
        & (df["activateLaCtrl"] == 1)
        & (df["laCtrlRequestType"] == constants.MoCo.LaCtrlRequestType.LACTRL_BY_TRAJECTORY)
        & (df["upper_velocity_limit"] < df["calculated_velocity"])
    )
    df["calculated_velocityLimitReq_mps"] = df["calculated_velocity"]
    df.loc[condition, "calculated_velocityLimitReq_mps"] = df["upper_velocity_limit"]
    return df


def adjust_velocity_based_on_wheel_stopper(df):
    """Calculating driving resistance and if any wheel is closer (<) than {AP_C_WFC_WS_VEL_DIST_THRESH_M} to a wheel stopper,
    the velocity limit shall be limited to upper limit {AP_C_WFC_WS_VEL_LIMIT_MPS} .
    """
    df = calculating_driving_resistance(df)
    threshold = constants.MoCo.Parameter.AP_C_WFC_WS_VEL_DIST_THRESH_M

    df["check_if_any_wheel_closer"] = (
        (df["activateLoCtrl"] == 1)
        & (df["loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_BY_TRAJECTORY)
        & (
            (
                (df["calculated_driving_resistance_FL"] < threshold)
                & (df["drivingResistanceType_0"] == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER)
            )
            | (
                (df["calculated_driving_resistance_RL"] < threshold)
                & (df["drivingResistanceType_1"] == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER)
            )
            | (
                (df["calculated_driving_resistance_RR"] < threshold)
                & (df["drivingResistanceType_2"] == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER)
            )
            | (
                (df["calculated_driving_resistance_FR"] < threshold)
                & (df["drivingResistanceType_3"] == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER)
            )
        )
    )
    return df


def check_phase_1_wheel_stopper_approaching_feature(df, loCtrlRequestType_param):
    """Checking phase1 wheel stopper approaching feature"""
    # Phase 1: Approaching phase (adjusting distance to stop)
    df = calculating_driving_resistance(df)
    threshold = constants.MoCo.Parameter.AP_C_WFC_OVERSHOOT_DIST_THRES_M

    # Create the 'check_if_any_wheel_closer_to_stopper' column for comparison to check if any of the columns is less
    # .than or equal to  the threshold
    df["check_if_any_wheel_closer_to_stopper"] = (
        (df["activateLoCtrl"] == 1)
        & (df["loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_BY_TRAJECTORY)
        & (
            (
                (df["calculated_driving_resistance_FL"] <= threshold)
                & (df["drivingResistanceType_0"] == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER)
            )
            | (
                (df["calculated_driving_resistance_RL"] <= threshold)
                & (df["drivingResistanceType_1"] == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER)
            )
            | (
                (df["calculated_driving_resistance_RR"] <= threshold)
                & (df["drivingResistanceType_2"] == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER)
            )
            | (
                (df["calculated_driving_resistance_FR"] <= threshold)
                & (df["drivingResistanceType_3"] == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER)
            )
        )
    )
    # Logical check for driving resistance type
    df["resistance_FL"] = np.inf
    df["resistance_RL"] = np.inf
    df["resistance_RR"] = np.inf
    df["resistance_FR"] = np.inf

    df.loc[
        df["drivingResistanceType_0"] == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER, "resistance_FL"
    ] = df["calculated_driving_resistance_FL"]
    df.loc[
        df["drivingResistanceType_1"] == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER, "resistance_RL"
    ] = df["calculated_driving_resistance_RL"]
    df.loc[
        df["drivingResistanceType_2"] == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER, "resistance_RR"
    ] = df["calculated_driving_resistance_RR"]
    df.loc[
        df["drivingResistanceType_3"] == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER, "resistance_FR"
    ] = df["calculated_driving_resistance_FR"]

    common_index = df.index
    df_resistance_aligned = df[["resistance_FL", "resistance_RL", "resistance_RR", "resistance_FR"]].reindex(
        common_index
    )
    # Find the minimum of the valid resistances
    df["shortest_distance_to_wheel_stopper"] = df_resistance_aligned.min(axis=1).fillna(0)
    # Check if any wheel is intended to touch the wheel stopper
    df["increase_distance_to_stop"] = (
        df["input_distanceToStopReq_m"] + constants.MoCo.Parameter.AP_C_WFC_OVERSHOOT_LENGTH_M
    )

    df["intended_touched_wheel_stopper"] = False
    df.loc[
        (
            (df["activateLoCtrl"] == 1)
            & (df["loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_BY_TRAJECTORY)
            & (df["increase_distance_to_stop"] >= df["shortest_distance_to_wheel_stopper"])
            & (
                (df["drivingResistanceType_0"] == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER)
                | (df["drivingResistanceType_1"] == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER)
                | (df["drivingResistanceType_2"] == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER)
                | (df["drivingResistanceType_3"] == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER)
            )
        ),
        "intended_touched_wheel_stopper",
    ] = True

    df["check_phase1_conditions"] = (df["check_if_any_wheel_closer_to_stopper"]) & (
        df["intended_touched_wheel_stopper"]
    )

    df["calculated_distanceToStopReq_m"] = 0
    df.loc[
        (df["activateLoCtrl"] == 1)
        & (df["loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_BY_TRAJECTORY),
        "calculated_distanceToStopReq_m",
    ] = df["input_distanceToStopReq_m"]
    df.loc[(df["check_phase1_conditions"]), "calculated_distanceToStopReq_m"] = df["increase_distance_to_stop"]

    df["check_phase_1_Result"] = False
    df.loc[
        df["check_phase1_conditions"] & (df["calculated_distanceToStopReq_m"] == df["increase_distance_to_stop"]),
        "check_phase_1_Result",
    ] = True

    return df


def check_phase_2_and_3_wheel_stopper_approaching_feature(df):
    """Checking phase 2 and 3 wheel stopper approaching feature"""
    dist_threshold = constants.MoCo.Parameter.AP_C_WFC_VDY_DIST_THRES_M

    # Create the 'check_if_any_wheel_closer_to_stopper' column for comparison to check if any of the columns is less than or equal to  the threshold
    df["wheel_closer_to_wheel_stopper"] = (
        (df["activateLoCtrl"] == 1)
        & (df["loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_BY_TRAJECTORY)
        & (
            (
                (df["calculated_driving_resistance_FL"] < dist_threshold)
                & (df["drivingResistanceType_0"] == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER)
            )
            | (
                (df["calculated_driving_resistance_RL"] < dist_threshold)
                & (df["drivingResistanceType_1"] == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER)
            )
            | (
                (df["calculated_driving_resistance_RR"] < dist_threshold)
                & (df["drivingResistanceType_2"] == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER)
            )
            | (
                (df["calculated_driving_resistance_FR"] < dist_threshold)
                & (df["drivingResistanceType_3"] == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER)
            )
        )
    )
    ##Need to remember the last value before undefined and then check for the other direction.
    # Initialize 'previous_drivingDirectionValue_nu' column to None
    df["previous_drivingDirectionValue_nu"] = None

    # Variable to keep track of the last valid (non-zero) drivingDirection_nu
    last_valid_value = 0

    # Loop through each row and apply the conditions
    for index, row in df.iterrows():
        if row["drivingDirection_nu"] == 0:
            # If drivingDirection_nu is 0, use the last valid value
            df.at[index, "previous_drivingDirectionValue_nu"] = last_valid_value
        else:
            # If drivingDirection_nu is non-zero, update the last valid value
            df.at[index, "previous_drivingDirectionValue_nu"] = row["drivingDirection_nu"]
            last_valid_value = row["drivingDirection_nu"]

    df["isStatusChanged"] = df["previous_drivingDirectionValue_nu"].diff()
    df["isDrivingDirectionChanged"] = (df["isStatusChanged"] == -1) | (df["isStatusChanged"] == 1)

    # Calculating passed distance of current stroke
    df["initial_distance_to_stop"] = 0  # To store the initial distance of the stroke
    df["passed_distance_of_current_stroke"] = 0  # To store the passed distance

    # Initialize the variable to keep track of the initial distance to stop
    initial_distance = None

    for idx in range(len(df)):
        row = df.iloc[idx]

        # Add the new condition to check for activateLoCtrl and loCtrlRequestType
        if (row["activateLoCtrl"] == 1) and (
            row["loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_BY_TRAJECTORY
        ):

            # Detect the start of a new stroke (based on the flags)
            if row["newSegmentStarted_nu"] or (
                idx > 0 and row["drivingForwardReq_nu"] != df.iloc[idx - 1, df.columns.get_loc("drivingForwardReq_nu")]
            ):
                initial_distance = row["input_distanceToStopReq_m"]  # Set the initial distance to stop

            # Assign the initial distance to the corresponding cycle using iloc
            df.iloc[idx, df.columns.get_loc("initial_distance_to_stop")] = initial_distance

            # Calculate the passed distance of the current stroke
            if initial_distance is not None:
                passed_distance = initial_distance - row["input_distanceToStopReq_m"]
                df.iloc[idx, df.columns.get_loc("passed_distance_of_current_stroke")] = passed_distance

    df["detect_touched_wheel_stopper"] = False
    df.loc[
        (
            df["wheel_closer_to_wheel_stopper"]
            & df["isDrivingDirectionChanged"]
            & (df["passed_distance_of_current_stroke"] > constants.MoCo.Parameter.AP_C_WFC_VDY_DRIVE_OFF_THRES_M)
            & (df["activateLoCtrl"] == 1)
            & (df["loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_BY_TRAJECTORY)
        ),
        "detect_touched_wheel_stopper",
    ] = True  # Detect touching

    # Phase 3: Stopping (set distance to stop to 0)
    for idx in range(len(df)):
        # Select the current row
        row = df.iloc[idx]

        # Check if the vehicle has touched the wheel stopper
        if row["detect_touched_wheel_stopper"]:
            # Set the distanceToStopReq_m to 0 after touching the stopper
            df.iloc[idx, df.columns.get_loc("calculated_distanceToStopReq_m")] = 0

        # Ensure that once the stopper is touched, the vehicle holds at distanceToStopReq_m = 0
        if idx > 0 and df.iloc[idx - 1, df.columns.get_loc("detect_touched_wheel_stopper")]:
            df.iloc[idx, df.columns.get_loc("calculated_distanceToStopReq_m")] = 0

    # Resetting condition for new control request
    distance_zero_active = False
    # Find the first occurrence of 'detect_touched_wheel_stopper' == True
    matching_rows = df[df["detect_touched_wheel_stopper"]]

    # Check if there are any True values
    if not matching_rows.empty:
        # If True values are found, get the index of the first occurrence
        start_timestamp = matching_rows.index.min()
        start_index = df.index.get_loc(start_timestamp)
        df.loc[start_index:, "check_reset_condition"] = (
            (df.loc[start_index:, "activateLoCtrl"] == 1)
            & (df.loc[start_index:, "loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_BY_TRAJECTORY)
            & (
                (
                    df.loc[start_index:, "drivingResistanceType_0"]
                    == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER
                )
                | (
                    df.loc[start_index:, "drivingResistanceType_1"]
                    == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER
                )
                | (
                    df.loc[start_index:, "drivingResistanceType_2"]
                    == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER
                )
                | (
                    df.loc[start_index:, "drivingResistanceType_3"]
                    == constants.MoCo.MFMDrivingResistanceType.MFM_WHEEL_STOPPER
                )
            )
        ) & (
            (df.loc[start_index:, "newSegmentStarted_nu"].astype(bool))
            | (
                df.loc[start_index:, "shortest_distance_to_wheel_stopper"].fillna(0)
                >= constants.MoCo.Parameter.AP_C_WFC_VDY_DIST_THRES_M
            )
        )
        # Loop over the DataFrame starting from 'start_index'
        for i in range(start_index, len(df)):
            if df.iloc[i]["detect_touched_wheel_stopper"] and not distance_zero_active:
                distance_zero_active = True

            if distance_zero_active:
                df.iloc[i, df.columns.get_loc("calculated_distanceToStopReq_m")] = 0

            if df.iloc[i]["check_reset_condition"]:
                distance_zero_active = False
                df.iloc[i, df.columns.get_loc("calculated_distanceToStopReq_m")] = df.loc[
                    i, "input_distanceToStopReq_m"
                ]
                df.iloc[i, df.columns.get_loc("detect_touched_wheel_stopper")] = ~df.loc[
                    i, "detect_touched_wheel_stopper"
                ]
    else:
        pass

    df["check_phase_2_Result"] = False
    df.loc[df["detect_touched_wheel_stopper"] & (df["calculated_distanceToStopReq_m"] == 0), "check_phase_2_Result"] = (
        True
    )
    return df
