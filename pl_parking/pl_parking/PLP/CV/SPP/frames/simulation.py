"""Simulation Frame module for SPP"""

import logging

from ..constants import SppPolygon, SppSemantics
from .frame import Frame

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class SimulationFrame(Frame):
    """Class representing a single simulation camera frame for evaluation"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # list to store polylines
        self.obstacles_polylines = []

        # lists to store objects on specific class type
        self.drivable_area = []
        self.curb_objects = []
        self.static_objects = []
        self.dynamic_objects = []

    def load(
        self,
        sim_df=None,
        polylines_timestamp=None,
        polylines_number_of_polygons=None,
        polylines_vertex_start_index=None,
        polylines_num_vertices=None,
        vertex_x=None,
        vertex_y=None,
        vertex_z=None,
        boundary_type=None,
    ):
        """Load all data for a frame from the Bsig file
        :param sim_df
        :param polylines_timestamp
        :param boundary_type
        :param polylines_number_of_polygons
        :param polylines_vertex_start_index
        :param polylines_num_vertices
        :param vertex_x
        :param vertex_y
        :param vertex_z
        :return: whether the loading was successfully or not
        """
        self.objects_loaded = True

        sim_frame_data = sim_df[sim_df[polylines_timestamp] == self.timestamp]

        self.objects_loaded = (
            self.load_objects(
                sim_frame_data,
                polylines_number_of_polygons,
                polylines_vertex_start_index,
                polylines_num_vertices,
                vertex_x,
                vertex_y,
                vertex_z,
                boundary_type,
            )
            and self.objects_loaded
        )

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
        else:
            self.objects_loaded = False

        return self.objects_loaded

    def load_objects(
        self,
        sim_frame_data,
        polylines_number_of_polygons,
        polylines_vertex_start_index,
        polylines_num_vertices,
        vertex_x,
        vertex_y,
        vertex_z,
        boundary_type,
    ):
        """Load measured objects by class type"""
        sim_meas = SimMeasurements(sim_frame_data)

        sim_meas.load_sim_values(
            polylines_number_of_polygons,
            polylines_vertex_start_index,
            polylines_num_vertices,
            vertex_x,
            vertex_y,
            vertex_z,
            boundary_type,
        )
        sim_meas.add_objects(self)

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
        """Add a drivable area object to a list"""
        self.drivable_area.append(object_label)

    def add_static_object(self, object_label):
        """Add a static object to a list"""
        self.static_objects.append(object_label)

    def add_dynamic_object(self, object_label):
        """Add a dynamic object to a list"""
        self.dynamic_objects.append(object_label)

    def add_curb_object(self, object_label):
        """Add a curb object to a list"""
        self.curb_objects.append(object_label)


class SimMeasurements:
    """Class representing measurements from SIM"""

    def __init__(self, sim_frame_data=None):
        self.frame_measured_objects = sim_frame_data
        self.loaded_measurements = []

    def load_sim_values(
        self,
        polylines_number_of_polygons,
        polylines_vertex_start_index,
        polylines_num_vertices,
        vertex_x,
        vertex_y,
        vertex_z,
        boundary_type,
    ):
        """Get simulated values from bsig file"""
        frame_measured_objects = self.frame_measured_objects
        number_of_polygons = frame_measured_objects[polylines_number_of_polygons].iloc[0]

        if boundary_type == SppSemantics.DRIVABLE_AREA.name:
            for i in range(0, number_of_polygons):
                polygon_vertex_start_index = frame_measured_objects[polylines_vertex_start_index + str(i)].iloc[0]
                polygon_number_of_vertices = frame_measured_objects[polylines_num_vertices + str(i)].iloc[0]
                polygon_vertex_end_index = polygon_vertex_start_index + polygon_number_of_vertices

                sim_object = SimDrivableArea(SppSemantics.DRIVABLE_AREA.name)
                sim_object.load_from_bsig(
                    frame_measured_objects,
                    polygon_vertex_start_index,
                    polygon_vertex_end_index,
                    vertex_x,
                    vertex_y,
                    vertex_z,
                )

                if len(sim_object.points) < SppPolygon.SPP_MIN_NUMBER_PTS_POLYGON:
                    continue
                self.loaded_measurements.append(sim_object)

    def add_objects(self, frame):
        """Store each object type in a dedicated list"""
        for measured_object in self.loaded_measurements:
            if isinstance(measured_object, SimDrivableArea):
                frame.add_drivable_area(measured_object)
            elif isinstance(measured_object, SimStaticObject):
                frame.add_static_object(measured_object)
            elif isinstance(measured_object, SimDynamicObject):
                frame.add_dynamic_object(measured_object)
            elif isinstance(measured_object, SimCurbObject):
                frame.add_curb_object(measured_object)


class SimObject:
    """Class representing a simulated object"""

    def __init__(self, semantic=None):
        self.semantic = semantic
        self.points = []

    def load_from_bsig(
        self, frame_measured_objects, vertex_start_index, vertex_end_index, vertex_x, vertex_y, vertex_z
    ):
        """Extract vertices of each polyline from a start_index to an end_index. Each vertex will be a tuple.
        Return a list of vertices.
        """
        for coord_idx in range(vertex_start_index, vertex_end_index):
            x = frame_measured_objects[vertex_x + str(coord_idx)].iloc[0]
            y = frame_measured_objects[vertex_y + str(coord_idx)].iloc[0]
            z = frame_measured_objects[vertex_z + str(coord_idx)].iloc[0]

            self.points.append((x, y, z))


class SimDrivableArea(SimObject):
    """Class representing a measured drivable area object"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SimStaticObject(SimObject):
    """Class representing a measured static object"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SimDynamicObject(SimObject):
    """Class representing a measured dynamic object"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SimCurbObject(SimObject):
    """Class representing a measured curb object"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
