"""Frame Evaluation module for SPP"""

import logging
from typing import Dict, List

import matplotlib.pyplot as plt
from shapely.geometry import Polygon

from pl_parking.PLP.CV.SPP.constants import SppKPI

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class EvalFrame:
    """Data class representing SPP frame evaluation."""

    DEFAULT_POLYGON_RESULTS = {
        "Recording": "Unknown",
        "Timestamp": None,
        "Percentage_Coverage": -1,
        "Percentage_Extralap": -1,
        "Percentage_Underlap": -1,
    }

    DEFAULT_POLYLINE_RESULTS = {
        "Recording": "Unknown",
        "Timestamp": None,
        "Boundary_Type": "Unknown",
        "Classification": SppKPI.UNCLASSIFIED.name,
    }

    def __init__(self, recording=None, gt=None, sim=None, timestamp=None):
        """Initialize object attributes."""
        self.recording = recording
        self.ground_truth_data = gt
        self.simulation_data = sim
        self.timestamp = timestamp

    @property
    def gt_available(self) -> bool:
        """Validation of ground truth data."""
        return self.ground_truth_data is not None

    @property
    def sim_available(self) -> bool:
        """Validation of simulated data."""
        return self.simulation_data is not None

    @property
    def valid(self) -> bool:
        """Validation of a frame."""
        return self.gt_available and self.sim_available

    def plot_polygons(self, timestamp):
        """Plot of GT and SIM Polygons"""
        sim_polygons = self.simulation_data.drivable_area
        gt_polygons = self.ground_truth_data.drivable_area

        for polygon in sim_polygons:
            # get the coordinates of simulated polygon
            sim_polygon_coords = polygon.points

            # discard the z-coordinate and return a list of tuples representing the corresponding 2D points
            sim_polygon_coords_xy = [(x, y) for x, y, _ in sim_polygon_coords]

            # Create a Polygon from the SIM polygon coordinates
            sim_polygon = Polygon(sim_polygon_coords_xy)
            sim_polygon_fixed = self.fix_invalid_polygon(sim_polygon)

            # Extract x, y coordinates for plotting
            x_sim_polygon, y_sim_polygon = sim_polygon.exterior.xy

            plt.plot(x_sim_polygon, y_sim_polygon, label="SIM Polygon", color="red")

            if sim_polygon_fixed.geom_type == "Polygon":
                x_sim_polygon_fixed, y_sim_polygon_fixed = sim_polygon_fixed.exterior.xy
                plt.plot(x_sim_polygon_fixed, y_sim_polygon_fixed, label="SIM Polygon Fixed", color="black")
            elif sim_polygon_fixed.geom_type == "MultiPolygon":
                for poly in sim_polygon_fixed.geoms:
                    x_poly, y_poly = poly.exterior.xy
                    plt.plot(x_poly, y_poly, label="SIM Polygon Fixed", color="black")

        for polygon in gt_polygons:
            # get the coordinates of Gt polygon
            gt_polygon_coords = polygon.points

            # discard the z-coordinate and return a list of tuples representing the corresponding 2D points
            gt_polygon_coords_xy = [(x, y) for x, y, _ in gt_polygon_coords]

            # Create a Polygon from the GT polygon coordinates
            gt_polygon = Polygon(gt_polygon_coords_xy)

            # Extract x, y coordinates for plotting
            x_gt_polygon, y_gt_polygon = gt_polygon.exterior.xy

            plt.plot(x_gt_polygon, y_gt_polygon, label="GT", color="green")

        plt.xlabel("X")
        plt.ylabel("Y")
        plt.title(f"Plot of GT and SIM Polygons at {timestamp}")
        plt.grid(True)

        # Place the legend outside the plot
        plt.legend(loc="upper left", bbox_to_anchor=(1, 1))

        # Show the plot and keep the window open
        plt.show(block=True)

    def evaluate_frame_polygons(self, timestamp) -> List[Dict]:
        """Evaluation of polygons."""
        # self.plot_polygons(timestamp)
        data = []
        total_gts_area = 0
        total_overlap_area = 0
        total_extralap_area = 0
        total_underlap_area = 0

        frame_result = self.DEFAULT_POLYGON_RESULTS.copy()
        frame_result["Recording"] = self.recording
        frame_result["Timestamp"] = self.timestamp

        gt_polygons = self.ground_truth_data.drivable_area
        sim_polygons = self.simulation_data.drivable_area

        for gt_polygon in gt_polygons:
            gt_polygon_area, overlap_area, underlap_area = self.evaluate_gt_polygons(gt_polygon, sim_polygons)
            total_gts_area += gt_polygon_area
            total_overlap_area += overlap_area
            total_underlap_area += underlap_area

        for sim_polygon in sim_polygons:
            extralap_area = self.evaluate_sim_polygons(sim_polygon, gt_polygons)
            total_extralap_area += extralap_area

        # Calculate the percentage of overlapping areas
        percentage_coverage = (total_overlap_area / total_gts_area) * 100 if total_gts_area > 0 else 0
        frame_result["Percentage_Coverage"] = percentage_coverage

        # Calculate the percentage of underlapping areas
        percentage_underlap = (total_underlap_area / total_gts_area) * 100 if total_gts_area > 0 else 0
        frame_result["Percentage_Underlap"] = percentage_underlap

        # Calculate the percentage of extralapping areas
        percentage_extralap = (total_extralap_area / total_gts_area) * 100 if total_gts_area > 0 else 0
        frame_result["Percentage_Extralap"] = percentage_extralap

        data.append(frame_result)

        return data

    def evaluate_gt_polygons(self, gt_polygon, sim_polygons):
        """Evaluation of a GT polygon compared to SIM polygons."""
        if len(sim_polygons) > 0:
            gt_polygon = self.get_polygon(gt_polygon)
            sim_polygons = [self.get_polygon(sim_polygon) for sim_polygon in sim_polygons]

            gt_polygon_area, overlap_area, gt_underlap = self.get_gt_underlap(gt_polygon, sim_polygons)

            return gt_polygon_area, overlap_area, gt_underlap

    def evaluate_sim_polygons(self, sim_polygon, gt_polygons):
        """Evaluation of a SIM polygon compared to GT polygons."""
        if len(gt_polygons) > 0:
            sim_polygon = self.get_polygon(sim_polygon)
            gt_polygons = [self.get_polygon(gt_polygon) for gt_polygon in gt_polygons]

            sim_extralap = self.get_sim_extralap(sim_polygon, gt_polygons)

            return sim_extralap

    @staticmethod
    def overlapping_area(polygon1, polygon2):
        """Compute the overlapping area between two polygons"""
        intersection = polygon1.intersection(polygon2)
        return intersection.area

    @staticmethod
    def get_polygon(polygon):
        """Create a polygon based on input coordinates"""
        polygon_coords = polygon.points

        if polygon_coords is not None:
            # discard the z - coordinate and return a list of tuples representing the corresponding 2D points
            polygon_coords_xy = [(x, y) for x, y, _ in polygon_coords]

            return Polygon(polygon_coords_xy)
        else:
            return None

    @staticmethod
    def fix_invalid_polygon(polygon):
        """Function to fix invalid polygon using the buffer(0) trick"""
        if not polygon.is_valid:
            polygon = polygon.buffer(0)  # Attempt to fix the polygon
            if not polygon.is_valid:
                return None  # Return None if the polygon cannot be fixed

        return polygon

    def get_gt_underlap(self, gt_polygon, sim_polygons):
        """Compute area, overlap area and underlap area of a GT polygon"""
        overlap_area = 0

        # Fix the GT polygon
        gt_polygon = self.fix_invalid_polygon(gt_polygon)
        if gt_polygon is None:
            raise ValueError("GT polygon is invalid and could not be fixed.")

        # Compute the area of GT polygon
        gt_polygon_area = gt_polygon.area

        for _, sim_polygon in enumerate(sim_polygons):
            # Fix the SIM polygon
            sim_polygon = self.fix_invalid_polygon(sim_polygon)
            if sim_polygon is None:
                continue  # Skip if polygon cannot be fixed

            # Compute the overlapping area
            current_overlap_area = self.overlapping_area(gt_polygon, sim_polygon)
            overlap_area += current_overlap_area

        gt_underlap = gt_polygon_area - overlap_area

        return gt_polygon_area, overlap_area, gt_underlap

    def get_sim_extralap(self, sim_polygon, gt_polygons):
        """Compute extralap area of a SIM polygon"""
        overlap_area = 0
        current_overlap_area = 0

        # Fix the SIM polygon
        sim_polygon = self.fix_invalid_polygon(sim_polygon)
        if sim_polygon is None:
            raise ValueError("SIM polygon is invalid and could not be fixed.")

        # Compute the area of SIM polygon
        sim_polygon_area = sim_polygon.area

        for _, gt_polygon in enumerate(gt_polygons):
            # Fix the GT polygon
            gt_polygon = self.fix_invalid_polygon(gt_polygon)
            if gt_polygon is None:
                continue  # Skip if polygon cannot be fixed

            # Compute the overlapping area
            current_overlap_area = self.overlapping_area(gt_polygon, sim_polygon)
            overlap_area += overlap_area

        sim_extralap = sim_polygon_area - current_overlap_area

        return sim_extralap
