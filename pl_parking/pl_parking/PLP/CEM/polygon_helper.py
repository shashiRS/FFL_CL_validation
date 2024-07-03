"""Polygon helper module for CEM"""

import numpy as np


def rotate_right(v):
    """Rotates a vector `v` to the right."""
    return np.array([v[1], -v[0]])


def is_polygon_convex_counterclockwise(vertex_list, err_threshold=10e-4):
    """
    Decide if the polygon is convex without self-intersections and that its vertices
    listed in counterclockwise order.
    """
    for i, _ in enumerate(vertex_list):
        v1 = vertex_list[i]
        v2 = vertex_list[(i + 1) % len(vertex_list)]
        # print("v1", v1)
        # print("v2", v2)

        normal = rotate_right(v2 - v1)
        # Normalize so that the error threshold has equal effect no matter the length of the edge.
        normal = normal / np.linalg.norm(normal)
        # print("normal", normal)

        for j in range(len(vertex_list) - 2):
            v_other = vertex_list[(i + 2 + j) % len(vertex_list)]
            # print("v_other", v_other)
            vec_to_other = v_other - v1
            # print(i, j, vec_to_other)
            vec_to_other = vec_to_other / np.linalg.norm(vec_to_other)
            # print(vec_to_other)
            if np.dot(normal, vec_to_other) > err_threshold:
                return False

    return True


def is_polygon_convex(vertex_list, err_threshold=10e-4):
    """Checks if a polygon defined by `vertex_list` is convex with a given error threshold."""
    return is_polygon_convex_counterclockwise(vertex_list) or is_polygon_convex_counterclockwise(vertex_list[::-1])


def is_vertex_order_counterclockwise_assuming_convex(vertex_list, err_threshold=10e-4):
    """
    Checks if the vertices in `vertex_list` are ordered counterclockwise
    assuming convexity with a given error threshold.
    """
    for i, _ in enumerate(vertex_list):
        v1 = vertex_list[i]
        v2 = vertex_list[(i + 1) % len(vertex_list)]
        v3 = vertex_list[(i + 2) % len(vertex_list)]

        normal = rotate_right(v2 - v1)
        # Normalize so that the error threshold has equal effect no matter the length of the edge.
        normal = normal / np.linalg.norm(normal)
        if np.dot(normal, v3 - v2) > err_threshold:
            return False
    return True


def project_to_line_as_parameter(x, v1, v2):
    """
    Return the real number t such that the projection of x
    onto the line v1v2 is v1 + t*(v2-v1).
    """
    # Solve for (v1 + t*(v2-v1) - x) * (v2-v1) = 0
    return np.dot(x - v1, v2 - v1) / np.dot(v2 - v1, v2 - v1)


def dist_of_point_from_edge(p, v1, v2):
    """Return the distance of a point and an edge in the plane."""
    t = project_to_line_as_parameter(p, v1, v2)
    if t < 0:
        return np.linalg.norm(p - v1)
    elif t > 1:
        return np.linalg.norm(p - v2)
    else:
        return np.linalg.norm(p - (v1 + t * (v2 - v1)))


def is_inside_polygon(p, vertex_list):
    """
    Decide if the point p is inside a polygon in the plane.

    The vertices of the polygon are assumed to be in counterclockwise order.
    """
    for i, _ in enumerate(vertex_list):
        v1 = vertex_list[i]
        v2 = vertex_list[(i + 1) % len(vertex_list)]

        normal = rotate_right(v2 - v1)
        # Normalize so that the error threshold has equal effect no matter the length of the edge.
        normal = normal / np.linalg.norm(normal)

        if np.dot(normal, p - v1) > 0:
            return False

    return True


def dist_of_point_from_polygon(p, vertex_list):
    """
    Return the distance of a point from a (filled) polygon in the plane.

    The vertices of the polygon are assumed to be in counterclockwise order.

    The polygon being filled means that if the point is inside the polygon,
    then the distance is zero.
    """
    if is_inside_polygon(p, vertex_list):
        return 0.0

    return min(
        dist_of_point_from_edge(p, vertex_list[i], vertex_list[(i + 1) % len(vertex_list)])
        for i in range(len(vertex_list))
    )
