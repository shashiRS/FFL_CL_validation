"""pose helper module for CEM"""

import math
import typing

from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import RelativeMotion


class FtPoseHelper:
    """Helper class for pose transformations."""

    @staticmethod
    def transform_point(point: typing.Tuple[float, float], relative_motion: RelativeMotion):
        """Transform a point based on relative motion."""
        x_t = point[0] + relative_motion.longitudinal_translation
        y_t = point[1] + relative_motion.lateral_translation

        x = x_t * math.cos(relative_motion.yaw_rotation) - y_t * math.sin(relative_motion.yaw_rotation)
        y = x_t * math.sin(relative_motion.yaw_rotation) + y_t * math.cos(relative_motion.yaw_rotation)

        return x, y

    @staticmethod
    def transform_vector(vector: typing.Tuple[float, float], relative_motion: RelativeMotion):
        """Transform a vector based on relative motion."""
        # This is a 0 order approximation if we want more accurate result we can consider the rotation of the ego
        #  coordinate, the change in the ego velocity
        # and the angular velocity coss product with the TP and ego center distance
        return vector
