"""Helper file for GDR test cases."""

from tsf.io.signals import SignalDefinition

MAX_NUMBER_POINTS = 6000


class GDRSignals(SignalDefinition):
    """MF signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        ID_FRONT = "id_front"
        X_FRONT = "x_m_front"
        Y_FRONT = "y_m_front"
        Z_FRONT = "z_m_front"
        NUM_POINTS_FRONT = "num_points_front"

        ID_LEFT = "id_left"
        X_LEFT = "x_m_left"
        Y_LEFT = "y_m_left"
        Z_LEFT = "z_m_left"
        NUM_POINTS_LEFT = "num_points_left"

        ID_REAR = "id_rear"
        X_REAR = "x_m_rear"
        Y_REAR = "y_m_rear"
        Z_REAR = "z_m_rear"
        NUM_POINTS_REAR = "num_points_rear"

        ID_RIGHT = "id_right"
        X_RIGHT = "x_m_right"
        Y_RIGHT = "y_m_right"
        Z_RIGHT = "z_m_right"
        NUM_POINTS_RIGHT = "num_points_right"

    def get_properties(self):
        """Get signals names."""
        signal_dict = {
            self.Columns.NUM_POINTS_FRONT: ".GDR_FC_DATA.gdrPointList.numPoints",
            self.Columns.NUM_POINTS_LEFT: ".GDR_LSC_DATA.gdrPointList.numPoints",
            self.Columns.NUM_POINTS_REAR: ".GDR_RC_DATA.gdrPointList.numPoints",
            self.Columns.NUM_POINTS_RIGHT: ".GDR_RSC_DATA.gdrPointList.numPoints",
            self.Columns.ID_FRONT: ".GDR_FC_DATA.gdrPointList.pointList[%].id",
            self.Columns.X_FRONT: ".GDR_FC_DATA.gdrPointList.pointList[%].x_m",
            self.Columns.Y_FRONT: ".GDR_FC_DATA.gdrPointList.pointList[%].y_m",
            self.Columns.Z_FRONT: ".GDR_FC_DATA.gdrPointList.pointList[%].z_m",
            self.Columns.ID_LEFT: ".GDR_LSC_DATA.gdrPointList.pointList[%].id",
            self.Columns.X_LEFT: ".GDR_LSC_DATA.gdrPointList.pointList[%].x_m",
            self.Columns.Y_LEFT: ".GDR_LSC_DATA.gdrPointList.pointList[%].y_m",
            self.Columns.Z_LEFT: ".GDR_LSC_DATA.gdrPointList.pointList[%].z_m",
            self.Columns.ID_REAR: ".GDR_RC_DATA.gdrPointList.pointList[%].id",
            self.Columns.X_REAR: ".GDR_RC_DATA.gdrPointList.pointList[%].x_m",
            self.Columns.Y_REAR: ".GDR_RC_DATA.gdrPointList.pointList[%].y_m",
            self.Columns.Z_REAR: ".GDR_RC_DATA.gdrPointList.pointList[%].z_m",
            self.Columns.ID_RIGHT: ".GDR_RSC_DATA.gdrPointList.pointList[%].id",
            self.Columns.X_RIGHT: ".GDR_RSC_DATA.gdrPointList.pointList[%].x_m",
            self.Columns.Y_RIGHT: ".GDR_RSC_DATA.gdrPointList.pointList[%].y_m",
            self.Columns.Z_RIGHT: ".GDR_RSC_DATA.gdrPointList.pointList[%].z_m",
        }
        return signal_dict

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "ADC5xx_Device", "M7board.EM_Thread", "CarPC.EM_Thread", "SIM VFB", "MTA_ADC5"]

        self._properties = self.get_properties()
