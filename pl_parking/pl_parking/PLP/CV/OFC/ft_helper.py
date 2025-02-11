"""Helper file for OFC test cases"""

import ctypes

import numpy as np
from tsf.io.signals import SignalDefinition


def decode_flows(img_h, img_w, flow_map_data, flow_map_data_offset):
    """Function used to decode the flow map and transform it into an optical flow array"""
    flat_dim = int(img_h) * int(img_w)
    flow_map_raw = np.zeros(flat_dim, dtype=np.uint32)

    ctypes_flows = (ctypes.c_uint32 * len(flow_map_data))(*flow_map_data)
    ctypes.memmove(flow_map_raw.ctypes.data, ctypes.byref(ctypes_flows, flow_map_data_offset), flow_map_raw.nbytes)

    flow_map = flow_map_raw.reshape((int(img_h), int(img_w)))
    # horiz, vert, conf
    raw_tda4_uvc = np.zeros((int(img_h), int(img_w), 3), dtype=np.float64)
    raw_tda4_uvc[..., 0] = ((flow_map >> 16) & 0xFFFF).astype(">i2") / 16.0
    raw_tda4_uvc[..., 1] = ((((flow_map << 16).astype(">i4")) >> 20).astype(">i4") & 0xFFFF).astype(">i2") / 16.0
    raw_tda4_uvc[..., 2] = flow_map & 0x0F

    return raw_tda4_uvc


class OFCSignals(SignalDefinition):
    """OFC signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        IMAGE_HEIGHT = "image_height"
        IMAGE_WIDTH = "image_width"
        FLOWMAPDATA_FORWARD_FRONT = "flowMapData_forward_front"
        FLOWMAPDATAOFFSET_FORWARD_FRONT = "flowMapDataOffset_forward_front"
        FLOWMAPDATA_BACKWARD_FRONT = "flowMapData_backward_front"
        FLOWMAPDATAOFFSET_BACKWARD_FRONT = "flowMapDataOffset_backward_front"

        FLOWMAPDATA_FORWARD_LEFT = "flowMapData_forward_left"
        FLOWMAPDATAOFFSET_FORWARD_LEFT = "flowMapDataOffset_forward_left"
        FLOWMAPDATA_BACKWARD_LEFT = "flowMapData_backward_left"
        FLOWMAPDATAOFFSET_BACKWARD_LEFT = "flowMapDataOffset_backward_left"

        FLOWMAPDATA_FORWARD_REAR = "flowMapData_forward_rear"
        FLOWMAPDATAOFFSET_FORWARD_REAR = "flowMapDataOffset_forward_rear"
        FLOWMAPDATA_BACKWARD_REAR = "flowMapData_backward_rear"
        FLOWMAPDATAOFFSET_BACKWARD_REAR = "flowMapDataOffset_backward_rear"

        FLOWMAPDATA_FORWARD_RIGHT = "flowMapData_forward_right"
        FLOWMAPDATAOFFSET_FORWARD_RIGHT = "flowMapDataOffset_forward_right"
        FLOWMAPDATA_BACKWARD_RIGHT = "flowMapData_backward_right"
        FLOWMAPDATAOFFSET_BACKWARD_RIGHT = "flowMapDataOffset_backward_right"

    def get_properties(self):
        """Get signals names."""
        signal_dict = dict()

        signal_dict[self.Columns.FLOWMAPDATA_FORWARD_FRONT] = ".OFC_FC_IMAGE.OfcFlowImageFc.forwardFlows.flowMapData"
        signal_dict[self.Columns.FLOWMAPDATAOFFSET_FORWARD_FRONT] = (
            ".OFC_FC_IMAGE.OfcFlowImageFc.forwardFlows.flowMapDataOffset"
        )
        signal_dict[self.Columns.FLOWMAPDATA_BACKWARD_FRONT] = ".OFC_FC_IMAGE.OfcFlowImageFc.backwardFlows.flowMapData"
        signal_dict[self.Columns.FLOWMAPDATAOFFSET_BACKWARD_FRONT] = (
            ".OFC_FC_IMAGE.OfcFlowImageFc.backwardFlows.flowMapDataOffset"
        )
        signal_dict[self.Columns.IMAGE_HEIGHT] = ".OFC_FC_IMAGE.OfcFlowImageFc.forwardFlows.imageHeader.height"
        signal_dict[self.Columns.IMAGE_WIDTH] = ".OFC_FC_IMAGE.OfcFlowImageFc.forwardFlows.imageHeader.width"

        signal_dict[self.Columns.FLOWMAPDATA_FORWARD_LEFT] = ".OFC_LSC_IMAGE.OfcFlowImageLsc.forwardFlows.flowMapData"
        signal_dict[self.Columns.FLOWMAPDATAOFFSET_FORWARD_LEFT] = (
            ".OFC_LSC_IMAGE.OfcFlowImageLsc.forwardFlows.flowMapDataOffset"
        )
        signal_dict[self.Columns.FLOWMAPDATA_BACKWARD_LEFT] = ".OFC_LSC_IMAGE.OfcFlowImageLsc.backwardFlows.flowMapData"
        signal_dict[self.Columns.FLOWMAPDATAOFFSET_BACKWARD_LEFT] = (
            ".OFC_LSC_IMAGE.OfcFlowImageLsc.backwardFlows.flowMapDataOffset"
        )

        signal_dict[self.Columns.FLOWMAPDATA_FORWARD_REAR] = ".OFC_RC_IMAGE.OfcFlowImageRc.forwardFlows.flowMapData"
        signal_dict[self.Columns.FLOWMAPDATAOFFSET_FORWARD_REAR] = (
            ".OFC_RC_IMAGE.OfcFlowImageRc.forwardFlows.flowMapDataOffset"
        )
        signal_dict[self.Columns.FLOWMAPDATA_BACKWARD_REAR] = ".OFC_RC_IMAGE.OfcFlowImageRc.backwardFlows.flowMapData"
        signal_dict[self.Columns.FLOWMAPDATAOFFSET_BACKWARD_REAR] = (
            ".OFC_RC_IMAGE.OfcFlowImageRc.backwardFlows.flowMapDataOffset"
        )

        signal_dict[self.Columns.FLOWMAPDATA_FORWARD_RIGHT] = ".OFC_RSC_IMAGE.OfcFlowImageRsc.forwardFlows.flowMapData"
        signal_dict[self.Columns.FLOWMAPDATAOFFSET_FORWARD_RIGHT] = (
            ".OFC_RSC_IMAGE.OfcFlowImageRsc.forwardFlows.flowMapDataOffset"
        )
        signal_dict[self.Columns.FLOWMAPDATA_BACKWARD_RIGHT] = (
            ".OFC_RSC_IMAGE.OfcFlowImageRsc.backwardFlows.flowMapData"
        )
        signal_dict[self.Columns.FLOWMAPDATAOFFSET_BACKWARD_RIGHT] = (
            ".OFC_RSC_IMAGE.OfcFlowImageRsc.backwardFlows.flowMapDataOffset"
        )

        return signal_dict

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = [
            "AP",
            "ADC5xx_Device",
            "M7board.EM_Thread",
            "CarPC.EM_Thread",
            "SIM VFB",
            "MTA_ADC5",
        ]

        self._properties = self.get_properties()
