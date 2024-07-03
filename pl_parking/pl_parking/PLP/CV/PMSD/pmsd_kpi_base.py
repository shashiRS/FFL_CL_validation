"""PMSD KPI helper"""

import json
from pathlib import Path

import drawsvg as draw
import numpy as np

from pl_parking.PLP.CV.PMSD.association import GeoPoint, GtLine, LineBoundary, VehicleLine, VehiclePoint
from pl_parking.PLP.CV.PMSD.gps_utils import GPS_utils


class Pmsd_Kpi_Base:
    """PMSD KPI helper"""

    @staticmethod
    def plot_lines(
        trans_gt_lines: list[VehicleLine], trans_pred_lines: list[VehicleLine], frame_num, prefix, boundary=False
    ):
        """Line plot"""
        scale = 10

        def to_grid(p: VehiclePoint) -> np.ndarray:
            return (np.array((*p,)) * scale).astype(np.int32)

        d = draw.Drawing(100 * scale, 80 * scale, origin="center", style="background: black")
        for line in trans_gt_lines:
            if boundary:
                corners = LineBoundary.for_line(line).corners
                d.append(draw.Lines(*[item for row in corners for item in to_grid(row)], close=True, stroke="white"))
            pt1, pt2 = to_grid(line.start), to_grid(line.end)
            d.append(draw.Lines(*pt1, *pt2, close=False, stroke="yellow"))

        for line in trans_pred_lines:
            pt1, pt2 = to_grid(line.start), to_grid(line.end)
            d.append(draw.Lines(*pt1, *pt2, close=False, stroke="red"))

        d.append(draw.Circle(0, 0, 5, stroke="green"))
        d.append(draw.Lines(0, 0, 5, 0, stroke="green"))

        Path(f"video/svgs/{prefix}").mkdir(exist_ok=True)
        # d.save_png(f'{frame_num}.png')
        d.save_svg(f"video/svgs/{prefix}/{frame_num}.svg")

    @staticmethod
    def get_gt_lines(gps: GPS_utils):
        """Get GT lines"""

        def distance(x: list[GtLine]):
            return np.linalg.norm(gps.geo2enu(**x[0].start.__dict__))

        min_gt_lines = None
        for location in ["MRing", "Frankfurt"]:
            gt_lines = json.load((Path(__file__).parent / f"{location}_place.json").open("r"))["lines"]
            gt_lines = [GtLine(GeoPoint(**i["start"]), GeoPoint(**i["end"])) for i in gt_lines]
            if min_gt_lines is None and distance(gt_lines) < 500:
                min_gt_lines = gt_lines
            elif distance(gt_lines) < distance(min_gt_lines):
                min_gt_lines = gt_lines
        return min_gt_lines

    @staticmethod
    def get_gps(lazy_reader):
        """Get GPS data"""
        gps_data = list(
            zip(*[lazy_reader[f"RT-Range Processor.Hunter.Position.{pre}itude"] for pre in ["Lat", "Long", "Alt"]])
        )

        yaws = lazy_reader["RT-Range Processor.Hunter.Angles.Heading"]
        return gps_data, yaws
