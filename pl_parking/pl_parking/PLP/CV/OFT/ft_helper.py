"""Helper file for OFT test cases"""

from tsf.io.signals import SignalDefinition


class OFTSignals(SignalDefinition):
    """OFT signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        NUMFLOWS_FRONT = "num_flows_front"
        AGE_FRONT = "age_front"
        XIMGPREVIOUS_FRONT = "xImgPrevious_front"
        YIMGPREVIOUS_FRONT = "yImgPrevious_front"
        XIMGCURRENT_FRONT = "xImgCurrent_front"
        YIMGCURRENT_FRONT = "yImgCurrent_front"
        FEATUREID_FRONT = "featureId_front"

        NUMFLOWS_LEFT = "num_flows_left"
        AGE_LEFT = "age_left"
        XIMGPREVIOUS_LEFT = "xImgPrevious_left"
        YIMGPREVIOUS_LEFT = "yImgPrevious_left"
        XIMGCURRENT_LEFT = "xImgCurrent_left"
        YIMGCURRENT_LEFT = "yImgCurrent_left"
        FEATUREID_LEFT = "featureId_left"

        NUMFLOWS_REAR = "num_flows_rear"
        AGE_REAR = "age_rear"
        XIMGPREVIOUS_REAR = "xImgPrevious_rear"
        YIMGPREVIOUS_REAR = "yImgPrevious_rear"
        XIMGCURRENT_REAR = "xImgCurrent_rear"
        YIMGCURRENT_REAR = "yImgCurrent_rear"
        FEATUREID_REAR = "featureId_rear"

        NUMFLOWS_RIGHT = "num_flows_right"
        AGE_RIGHT = "age_right"
        XIMGPREVIOUS_RIGHT = "xImgPrevious_right"
        YIMGPREVIOUS_RIGHT = "yImgPrevious_right"
        XIMGCURRENT_RIGHT = "xImgCurrent_right"
        YIMGCURRENT_RIGHT = "yImgCurrent_right"
        FEATUREID_RIGHT = "featureId_right"

    def get_properties(self):
        """Get signals names."""
        signals_dict = dict()

        signals_dict[self.Columns.NUMFLOWS_FRONT] = ".OFT_FC_DATA.pOftBasicTracks.uiNrOfPointCloudFlows"
        signals_dict[self.Columns.NUMFLOWS_LEFT] = ".OFT_LSC_DATA.pOftBasicTracks.uiNrOfPointCloudFlows"
        signals_dict[self.Columns.NUMFLOWS_REAR] = ".OFT_RC_DATA.pOftBasicTracks.uiNrOfPointCloudFlows"
        signals_dict[self.Columns.NUMFLOWS_RIGHT] = ".OFT_RSC_DATA.pOftBasicTracks.uiNrOfPointCloudFlows"
        signals_dict[self.Columns.AGE_FRONT] = ".OFT_FC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].age"
        signals_dict[self.Columns.AGE_LEFT] = ".OFT_LSC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].age"
        signals_dict[self.Columns.AGE_REAR] = ".OFT_RC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].age"
        signals_dict[self.Columns.AGE_RIGHT] = ".OFT_RSC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].age"
        signals_dict[self.Columns.XIMGPREVIOUS_FRONT] = (
            ".OFT_FC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].xImgPrevious"
        )
        signals_dict[self.Columns.XIMGPREVIOUS_LEFT] = (
            ".OFT_LSC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].xImgPrevious"
        )
        signals_dict[self.Columns.XIMGPREVIOUS_REAR] = (
            ".OFT_RC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].xImgPrevious"
        )
        signals_dict[self.Columns.XIMGPREVIOUS_RIGHT] = (
            ".OFT_RSC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].xImgPrevious"
        )
        signals_dict[self.Columns.YIMGPREVIOUS_FRONT] = (
            ".OFT_FC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].yImgPrevious"
        )
        signals_dict[self.Columns.YIMGPREVIOUS_LEFT] = (
            ".OFT_LSC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].yImgPrevious"
        )
        signals_dict[self.Columns.YIMGPREVIOUS_REAR] = (
            ".OFT_RC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].yImgPrevious"
        )
        signals_dict[self.Columns.YIMGPREVIOUS_RIGHT] = (
            ".OFT_RSC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].yImgPrevious"
        )
        signals_dict[self.Columns.XIMGCURRENT_FRONT] = (
            ".OFT_FC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].xImgCurrent"
        )
        signals_dict[self.Columns.XIMGCURRENT_LEFT] = (
            ".OFT_LSC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].xImgCurrent"
        )
        signals_dict[self.Columns.XIMGCURRENT_REAR] = (
            ".OFT_RC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].xImgCurrent"
        )
        signals_dict[self.Columns.XIMGCURRENT_RIGHT] = (
            ".OFT_RSC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].xImgCurrent"
        )
        signals_dict[self.Columns.YIMGCURRENT_FRONT] = (
            ".OFT_FC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].yImgCurrent"
        )
        signals_dict[self.Columns.YIMGCURRENT_LEFT] = (
            ".OFT_LSC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].yImgCurrent"
        )
        signals_dict[self.Columns.YIMGCURRENT_REAR] = (
            ".OFT_RC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].yImgCurrent"
        )
        signals_dict[self.Columns.YIMGCURRENT_RIGHT] = (
            ".OFT_RSC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].yImgCurrent"
        )
        signals_dict[self.Columns.FEATUREID_FRONT] = ".OFT_FC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].featureId"
        signals_dict[self.Columns.FEATUREID_LEFT] = ".OFT_LSC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].featureId"
        signals_dict[self.Columns.FEATUREID_REAR] = ".OFT_RC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].featureId"
        signals_dict[self.Columns.FEATUREID_RIGHT] = ".OFT_RSC_DATA.pOftBasicTracks.pointCloudFlowFeatures[%].featureId"

        return signals_dict

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "ADC5xx_Device", "M7board.EM_Thread", "CarPC.EM_Thread", "SIM VFB", "MTA_ADC5"]

        self._properties = self.get_properties()
