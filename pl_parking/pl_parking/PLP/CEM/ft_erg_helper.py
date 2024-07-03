"""erg helper module for CEM"""

import typing
from dataclasses import dataclass

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from pl_parking.PLP.CEM.constants import ConstantsCem, GroundTruthCarMaker
from pl_parking.PLP.CEM.ft_pcl_helper import FtPclHelper


@dataclass(frozen=True)
class PMDLinePoint:
    """Dataclass representing a point in a PMD line."""

    x: float
    y: float


@dataclass(frozen=True)
class PCLPoint:
    """Dataclass representing a point in PCL."""

    x: float
    y: float

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


@dataclass(frozen=True)
class PCLDelimiter:
    """Dataclass representing a delimiter in PCL."""

    delimiter_id: int
    delimiter_type: int
    start_point: PMDLinePoint
    end_point: PMDLinePoint
    confidence_percent: float


class TranslationRotation:
    """Class handling translation and rotation operations."""

    @staticmethod
    def rotate_translate(point, new_origin, angle):
        """Rotate and translate a point around a new origin by a given angle."""
        ox, oy = new_origin
        px, py = point
        x_p = np.cos(angle) * (px - ox) + np.sin(angle) * (py - oy)
        y_p = np.cos(angle) * (py - oy) - np.sin(angle) * (px - ox)
        return x_p, y_p

    @staticmethod
    def rotate_x(point, angle, origin=(0, 0)):
        """Angle in radian"""
        ox, oy = origin
        px, py = point
        return np.cos(angle) * (px - ox) + np.sin(angle) * (py - oy)

    @staticmethod
    def rotate_y(point, angle, origin=(0, 0)):
        """Angle in radian"""
        ox, oy = origin
        px, py = point
        return np.sin(angle) * (px - ox) - np.cos(angle) * (py - oy)

    @staticmethod
    def rotate_translate_x_offset(point: PCLPoint, new_origin: list, angle: float):
        """Angle in radians"""
        ox, oy = new_origin
        px, py = point.x, point.y
        x_p = np.cos(angle) * (px - ox) + np.sin(angle) * (py - oy)
        y_p = np.cos(angle) * (py - oy) - np.sin(angle) * (px - ox)
        return x_p - GroundTruthCarMaker.REAR_BUMPER_TO_REAR_AXIS_DIST, y_p

    def pcl_coordinates(self, pcl_delimiter: PCLDelimiter, origin: list, angle: float):
        """Calculate PCL coordinates for a given PCL delimiter.

        Args:
            pcl_delimiter (PCLDelimiter): The PCL delimiter.
            origin (list): The origin point for rotation and translation.
            angle (float): The angle of rotation.

        Returns:
            PCLDelimiter: The PCL delimiter with translated and rotated coordinates.
        """
        start_point = self.rotate_translate_x_offset(pcl_delimiter.line_start, origin, angle)
        end_point = self.rotate_translate_x_offset(pcl_delimiter.line_end, origin, angle)

        return PCLDelimiter(
            pcl_delimiter.id,
            pcl_delimiter.delimiter_type,
            PCLPoint(start_point[0], start_point[1]),
            PCLPoint(end_point[0], end_point[1]),
            pcl_delimiter.line_probability,
        )

    def update_position(self, pcl_array: list, ego_position: list, ego_angle: float) -> typing.List[PCLDelimiter]:
        """Update positions of PCL (Park Cluster Location) array relative to ego position and angle.

        Args:
            pcl_array (list): List of PCL delimiters.
            ego_position (list): Ego vehicle position coordinates.
            ego_angle (float): Ego vehicle angle.

        Returns:
            typing.List[PCLDelimiter]: Updated list of PCL delimiters.
        """
        pcl_position: typing.List[PCLDelimiter] = []
        for pcl in pcl_array:
            pcl_updated = self.pcl_coordinates(pcl, ego_position, ego_angle)
            closes_point = FtPclHelper.get_closest_point(pcl_updated)
            if not (
                abs(closes_point.x) > ConstantsCem.AP_G_DES_MAP_RANGE_M / 2
                or abs(closes_point.y) > ConstantsCem.AP_G_DES_MAP_RANGE_M / 2
            ):
                pcl_position.append(pcl_updated)

        return pcl_position


class ErgPlots:
    """Plots from .erg files."""

    @staticmethod
    def plot_pcl_output_gt(pcl_output_df: pd.DataFrame, gt_df: pd.DataFrame, ego_position: pd.DataFrame):
        """Generate plot comparing PCL output with ground truth and return the figure."""
        # Filter empty and duplicated data
        pcl_output_df = pcl_output_df.drop_duplicates(subset="numPclDelimiters_timestamp")
        pcl_output_df = pcl_output_df.loc[:, (pcl_output_df != 0).any(axis=0)]
        # Merge x,y columns
        x_columns = [col for col in pcl_output_df.columns if "P0_x" in col or "P1_x" in col]
        y_columns = [col for col in pcl_output_df.columns if "P0_y" in col or "P1_y" in col]
        out_df = pd.DataFrame()
        for x_column, y_column in zip(x_columns, y_columns):
            out_df[f"{x_column},{y_column}_updated"] = pcl_output_df[[x_column, y_column]].apply(tuple, axis=1)
        out_df["timestamp"] = pcl_output_df["numPclDelimiters_timestamp"]
        out_df_melted = pd.melt(
            out_df, id_vars=["timestamp"], value_vars=out_df.columns, var_name="var", value_name="tupla"
        )
        out_df_melted[["x", "y"]] = pd.DataFrame(out_df_melted["tupla"].tolist(), index=out_df_melted.index)
        out_df_melted = out_df_melted[["timestamp", "x", "y"]]

        # Filter empty and needed data
        gt_df = gt_df.loc[:, gt_df.columns.str.endswith(("lineStartX", "lineEndX", "lineStartY", "lineEndY"))]
        gt_df = gt_df.loc[:, (gt_df != 0).all(axis=0)]
        x_columns = [col for col in gt_df.columns if col.endswith(("lineStartX", "lineEndX"))]
        y_columns = [col for col in gt_df.columns if col.endswith(("lineStartY", "lineEndY"))]
        gt_df = gt_df.loc[gt_df.index.repeat(len(ego_position))]
        gt_df.index = ego_position.index
        gt_df["timestamp"] = ego_position["timestamp"]
        pose_gt_df = pd.concat([ego_position, gt_df], axis=1)

        for x_col, y_col in zip(x_columns, y_columns):
            gt_df[f"{x_col},{y_col}_updated"] = pose_gt_df.apply(
                lambda value, x_col=x_col, y_col=y_col: TranslationRotation.rotate_translate(
                    [value[x_col], value[y_col]], [value["Fr1_x"], value["Fr1_y"]], value["yaw"]
                ),
                axis=1,
            )

        columns = [column for column in gt_df.columns if column.endswith("_updated")]
        gt_df_melted = pd.melt(gt_df, id_vars=["timestamp"], value_vars=columns, var_name="var", value_name="tupla")
        gt_df_melted[["x", "y"]] = pd.DataFrame(gt_df_melted["tupla"].tolist(), index=gt_df_melted.index)
        gt_df_melted = gt_df_melted[["timestamp", "x", "y"]]
        gt_df_melted["x"] -= GroundTruthCarMaker.REAR_BUMPER_TO_REAR_AXIS_DIST

        # Concat GT and Output DFs
        out_df_melted["Dataset"] = "PCL Output"
        gt_df_melted["Dataset"] = "GT"
        df_combined = pd.concat([gt_df_melted, out_df_melted], ignore_index=True)

        # Plot data
        fig = px.scatter(df_combined, x="x", y="y", color="Dataset", animation_frame="timestamp")
        x_range = [min(df_combined["x"]) - 1, max(df_combined["x"] + 1)]
        y_range = [min(df_combined["y"]) - 1, max(df_combined["y"] + 1)]
        fig.update_layout(xaxis_range=x_range, yaxis_range=y_range)

        return fig

    @staticmethod
    def plot_ego_trajectory(ego_position: pd.DataFrame):
        """Plot ego vehicle trajectory and return the figure."""
        # Polygon
        # ego_position['Fr1_y'] += GroundTruthCarMaker.REAR_BUMPER_TO_REAR_AXIS_DIST
        ego_position["pos_x0"] = ego_position["Fr1_x"] + TranslationRotation.rotate_x(
            [-GroundTruthCarMaker.REAR_BUMPER_TO_REAR_AXIS_DIST, GroundTruthCarMaker.CAR_WIDTH / 2], ego_position["yaw"]
        )
        ego_position["pos_y0"] = ego_position["Fr1_y"] + TranslationRotation.rotate_y(
            [-GroundTruthCarMaker.REAR_BUMPER_TO_REAR_AXIS_DIST, GroundTruthCarMaker.CAR_WIDTH / 2], ego_position["yaw"]
        )
        ego_position["pos_x1"] = ego_position["Fr1_x"] + TranslationRotation.rotate_x(
            [GroundTruthCarMaker.REAR_AXIS_TO_FRONT_DIST, GroundTruthCarMaker.CAR_WIDTH / 2], ego_position["yaw"]
        )
        ego_position["pos_y1"] = ego_position["Fr1_y"] + TranslationRotation.rotate_y(
            [GroundTruthCarMaker.REAR_AXIS_TO_FRONT_DIST, GroundTruthCarMaker.CAR_WIDTH / 2], ego_position["yaw"]
        )
        ego_position["pos_x2"] = ego_position["Fr1_x"] + TranslationRotation.rotate_x(
            [-GroundTruthCarMaker.REAR_BUMPER_TO_REAR_AXIS_DIST, -GroundTruthCarMaker.CAR_WIDTH / 2],
            ego_position["yaw"],
        )
        ego_position["pos_y2"] = ego_position["Fr1_y"] + TranslationRotation.rotate_y(
            [-GroundTruthCarMaker.REAR_BUMPER_TO_REAR_AXIS_DIST, -GroundTruthCarMaker.CAR_WIDTH / 2],
            ego_position["yaw"],
        )
        ego_position["pos_x3"] = ego_position["Fr1_x"] + TranslationRotation.rotate_x(
            [GroundTruthCarMaker.REAR_AXIS_TO_FRONT_DIST, -GroundTruthCarMaker.CAR_WIDTH / 2], ego_position["yaw"]
        )
        ego_position["pos_y3"] = ego_position["Fr1_y"] + TranslationRotation.rotate_y(
            [GroundTruthCarMaker.REAR_AXIS_TO_FRONT_DIST, -GroundTruthCarMaker.CAR_WIDTH / 2], ego_position["yaw"]
        )
        ego_position["pos_x0_"] = ego_position["pos_x0"]
        ego_position["pos_y0_"] = ego_position["pos_y0"]

        polygon_df_x = ego_position[["pos_x0", "pos_x1", "pos_x3", "pos_x2", "pos_x0_", "timestamp"]].melt(
            id_vars="timestamp", var_name="var", value_name="x"
        )
        polygon_df_y = ego_position[["pos_y0", "pos_y1", "pos_y3", "pos_y2", "pos_y0_", "timestamp"]].melt(
            id_vars="timestamp", var_name="var", value_name="y"
        )
        polygon_df = pd.concat([polygon_df_x, polygon_df_y["y"]], axis=1)
        polygon_df = polygon_df[["timestamp", "x", "y"]]

        # Plot data
        fig = px.line(polygon_df, x="x", y="y", color_discrete_sequence=["red"], animation_frame="timestamp")
        x_range = [min(polygon_df["x"]) - 1, max(polygon_df["x"] + 1)]
        y_range = [min(polygon_df["y"]) - 1, max(polygon_df["y"] + 1)]
        fig.update_layout(xaxis_range=x_range, yaxis_range=y_range)

        return fig

    @staticmethod
    def plot_pcl_static_gt(gt_df: pd.DataFrame, ego_position_df: pd.DataFrame):
        """Plot static PCL with ground truth."""
        # Gt df with ego_df dimension
        gt_df = gt_df.loc[:, gt_df.columns.str.endswith(("lineStartX", "lineEndX", "lineStartY", "lineEndY"))]
        gt_df = gt_df.loc[:, (gt_df != 0).all(axis=0)]
        x_columns = [col for col in gt_df.columns if col.endswith(("lineStartX", "lineEndX"))]
        y_columns = [col for col in gt_df.columns if col.endswith(("lineStartY", "lineEndY"))]
        gt_df = gt_df.loc[gt_df.index.repeat(len(ego_position_df))]
        gt_df.index = ego_position_df.index
        gt_df["timestamp"] = ego_position_df["timestamp"]
        # Stack x and y values
        df_x = (
            gt_df[x_columns + ["timestamp"]]
            .melt(id_vars="timestamp", var_name="var", value_name="x")
            .sort_values(["timestamp", "var"])
        )
        duplicated_rows = df_x.iloc[1::2].copy()
        df_x = pd.concat([df_x, duplicated_rows]).sort_values(["timestamp", "var"])
        df_y = (
            gt_df[y_columns + ["timestamp"]]
            .melt(id_vars="timestamp", var_name="var", value_name="y")
            .sort_values(["timestamp", "var"])
        )
        duplicated_rows = df_y.iloc[1::2].copy()
        df_y = pd.concat([df_y, duplicated_rows]).sort_values(["timestamp", "var"])
        x_y_df = pd.concat([df_x, df_y["y"]], axis=1)
        x_y_df["line_id"] = x_y_df["var"].apply(lambda x: x.split(".")[0])
        # Plot df
        fig = px.line(x_y_df, x="x", y="y", color="line_id", animation_frame="timestamp")
        return fig

    def plot_ego_pcl_gt(self, ego_position: pd.DataFrame, gt_df: pd.DataFrame):
        """Plot ego vehicle trajectory, static PCL, and ground truth together.

        Args:
            ego_position (pd.DataFrame): DataFrame containing ego vehicle position data.
            gt_df (pd.DataFrame): DataFrame containing ground truth data.

        Returns:
            go.Figure: Figure containing combined plots.
        """
        ego_fig = self.plot_ego_trajectory(ego_position)
        pcl_fig = self.plot_pcl_static_gt(gt_df, ego_position)
        frames = [
            go.Frame(data=f.data + ego_fig.frames[i].data + pcl_fig.frames[i].data, name=f.name)
            for i, f in enumerate(ego_fig.frames)
        ]
        fig_all = go.Figure(data=frames[0].data, frames=frames, layout=pcl_fig.layout)
        return fig_all
