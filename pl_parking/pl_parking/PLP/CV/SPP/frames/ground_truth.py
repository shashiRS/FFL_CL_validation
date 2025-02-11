"""Ground Truth Frame module for SPP"""

import logging

from ..constants import SppPolygon, SppSemantics
from ..constants import SppPolylines as Polylines
from .frame import Frame

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class GroundTruthFrame(Frame):
    """Class representing a single ground truth camera frame for evaluation"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # list to store polylines
        self.obstacles_polylines = []

        # lists to store objects of specific class type
        self.drivable_area = []
        self.curb_objects = []
        self.static_objects = []
        self.dynamic_objects = []

    def load(self, gt_camera_data=None, boundary_type=None):
        """Load data for a frame from the Json file
        :param gt_camera_data
        :param boundary_type
        :return: whether the loading was successfully or not
        """
        self.objects_loaded = True

        gt_frame_data = gt_camera_data[gt_camera_data["gt_spp_timestamp"] == self.timestamp]

        if not gt_frame_data.empty:  # already checked, do I need it?
            self.objects_loaded = self.load_objects(gt_frame_data, boundary_type) and self.objects_loaded

            if self.objects_loaded:
                try:
                    if len(self.static_objects) > 0:
                        self.add_to_obstacles_polylines(self.static_objects)
                except Exception as e:
                    self.static_objects = ()
                    _log.warning(f"No static objects! {e}")

                try:
                    if len(self.dynamic_objects) > 0:
                        self.add_to_obstacles_polylines(self.dynamic_objects)
                except Exception as e:
                    self.dynamic_objects = ()
                    _log.warning(f"No dynamic objects! {e}")

                try:
                    if len(self.curb_objects) > 0:
                        self.add_to_obstacles_polylines(self.curb_objects)
                except Exception as e:
                    self.curb_objects = ()
                    _log.warning(f"No curb objects! {e}")

        return self.objects_loaded

    def load_objects(self, gt_frame_data, boundary_type):
        """Load objects by class type"""
        gt_meas = GtMeasurements(gt_frame_data)

        gt_meas.load_gt_values(boundary_type)
        gt_meas.add_objects(self)

        if boundary_type == SppSemantics.DRIVABLE_AREA.name and len(self.drivable_area) == 0:
            return False
        elif (
            boundary_type is None
            and len(self.curb_objects) == 0
            and len(self.static_objects) == 0
            and len(self.dynamic_objects) == 0
        ):
            return False

        return True

    def add_to_obstacles_polylines(self, obstacles):
        """Add obstacles to a list regardless of semantics"""
        for obstacle in obstacles:
            self.obstacles_polylines.append({obstacle.semantic: obstacle.points})

    def add_drivable_area(self, object_label):
        """Add a drivable area objects to a list"""
        self.drivable_area.append(object_label)

    def add_static_object(self, object_label):
        """Add a static objects to a list"""
        self.static_objects.append(object_label)

    def add_dynamic_object(self, object_label):
        """Add a dynamic objects to a list"""
        self.dynamic_objects.append(object_label)

    def add_curb_object(self, object_label):
        """Add a curb objects to a list"""
        self.curb_objects.append(object_label)


class GtMeasurements:
    """Class representing measurements from GT"""

    def __init__(self, gt_frame_data=None):
        self.frame_labeled_objects = gt_frame_data
        self.loaded_labels = []

    def load_gt_values(self, boundary_type):
        """Extract vertices of each polyline from start_index to end_index"""
        frame_labeled_objects = self.frame_labeled_objects
        number_of_polygons = int(
            frame_labeled_objects.iat[0, frame_labeled_objects.columns.get_loc("gt_no_of_polygons")]
        )
        number_of_polylines = int(
            frame_labeled_objects.iat[0, frame_labeled_objects.columns.get_loc("gt_no_of_polylines")]
        )

        if boundary_type == SppSemantics.DRIVABLE_AREA.name:
            if number_of_polygons > 0:
                for i in range(0, number_of_polygons):

                    polyline_vertex_start_index = int(
                        frame_labeled_objects.iat[
                            0, frame_labeled_objects.columns.get_loc("gt_vertex_start_index_" + str(i))
                        ]
                    )
                    polyline_number_of_vertices = int(
                        frame_labeled_objects.iat[0, frame_labeled_objects.columns.get_loc("gt_num_vertices_" + str(i))]
                    )
                    polyline_vertex_end_index = polyline_vertex_start_index + polyline_number_of_vertices

                    polyline_semantic = frame_labeled_objects.iat[
                        0, frame_labeled_objects.columns.get_loc("gt_semantic_" + str(i))
                    ]

                    if polyline_semantic == SppSemantics.DRIVABLE_AREA.name:
                        labeled_object = GtDrivableArea(polyline_semantic)
                        labeled_object.load_points(
                            frame_labeled_objects, polyline_vertex_start_index, polyline_vertex_end_index
                        )

                        if len(labeled_object.points) < SppPolygon.SPP_MIN_NUMBER_PTS_POLYGON:
                            continue
                        self.loaded_labels.append(labeled_object)
        else:
            if number_of_polygons > 0 and number_of_polylines > 0:
                for i in range(0, number_of_polygons + number_of_polylines):
                    polyline_vertex_start_index = int(
                        frame_labeled_objects.iat[
                            0, frame_labeled_objects.columns.get_loc("gt_vertex_start_index_" + str(i))
                        ]
                    )
                    polyline_number_of_vertices = int(
                        frame_labeled_objects.iat[0, frame_labeled_objects.columns.get_loc("gt_num_vertices_" + str(i))]
                    )
                    polyline_vertex_end_index = polyline_vertex_start_index + polyline_number_of_vertices

                    polyline_semantic = frame_labeled_objects.iat[
                        0, frame_labeled_objects.columns.get_loc("gt_semantic_" + str(i))
                    ]

                    if polyline_semantic == SppSemantics.STATIC_OBSTACLE.name:
                        labeled_object = GtStaticObject(polyline_semantic)
                        labeled_object.load_points(
                            frame_labeled_objects, polyline_vertex_start_index, polyline_vertex_end_index
                        )

                        if len(labeled_object.points) < Polylines.SPP_MIN_NUMBER_PTS_POLYLINE:
                            continue
                        self.loaded_labels.append(labeled_object)

                    elif polyline_semantic == SppSemantics.DYNAMIC_OBSTACLE.name:
                        labeled_object = GtDynamicObject(polyline_semantic)
                        labeled_object.load_points(
                            frame_labeled_objects, polyline_vertex_start_index, polyline_vertex_end_index
                        )

                        if len(labeled_object.points) < Polylines.SPP_MIN_NUMBER_PTS_POLYLINE:
                            continue
                        self.loaded_labels.append(labeled_object)

                    elif polyline_semantic == SppSemantics.CURB.name:
                        labeled_object = GtCurbObject(polyline_semantic)
                        labeled_object.load_points(
                            frame_labeled_objects, polyline_vertex_start_index, polyline_vertex_end_index
                        )

                        if len(labeled_object.points) < Polylines.SPP_MIN_NUMBER_PTS_POLYLINE:
                            continue
                        self.loaded_labels.append(labeled_object)

    def add_objects(self, frame):
        """Store each object type in a dedicated list"""
        for labeled_object in self.loaded_labels:
            if isinstance(labeled_object, GtDrivableArea):
                frame.add_drivable_area(labeled_object)
            elif isinstance(labeled_object, GtStaticObject):
                frame.add_static_object(labeled_object)
            elif isinstance(labeled_object, GtDynamicObject):
                frame.add_dynamic_object(labeled_object)
            elif isinstance(labeled_object, GtCurbObject):
                frame.add_curb_object(labeled_object)


class GtObject:
    """Class representing a GT object"""

    def __init__(self, semantic=None):
        self.semantic = semantic
        self.points = []

    def load_points(self, frame_labeled_objects, vertex_start_index, vertex_end_index):
        """Extract vertices of each polyline from a start_index to an end_index. Each vertex will be a tuple.
        Return a list of vertices.
        """
        for coord_idx in range(vertex_start_index, vertex_end_index):
            x = frame_labeled_objects.iat[0, frame_labeled_objects.columns.get_loc("gt_vertex_x_" + str(coord_idx))]
            y = frame_labeled_objects.iat[0, frame_labeled_objects.columns.get_loc("gt_vertex_y_" + str(coord_idx))]
            z = frame_labeled_objects.iat[0, frame_labeled_objects.columns.get_loc("gt_vertex_z_" + str(coord_idx))]

            self.points.append((x, y, z))


class GtDrivableArea(GtObject):
    """Class representing a drivable area object"""

    def __init__(self, *args, **kwargs):
        """Initialize object attributes."""
        super().__init__(*args, **kwargs)


class GtStaticObject(GtObject):
    """Class representing a static object"""

    def __init__(self, *args, **kwargs):
        """Initialize object attributes."""
        super().__init__(*args, **kwargs)


class GtDynamicObject(GtObject):
    """Class representing a Dynamic object"""

    def __init__(self, *args, **kwargs):
        """Initialize object attributes."""
        super().__init__(*args, **kwargs)


class GtCurbObject(GtObject):
    """Class representing a Curb object"""

    def __init__(self, *args, **kwargs):
        """Initialize object attributes."""
        super().__init__(*args, **kwargs)
