"""PCE helper scripts"""

import logging

import pandas as pd
from tsf.io.signals import SignalDefinition

import pl_parking.PLP.CV.PCE.constants as ct

# from tsf.core.testcase import PreProcessor
# from pl_parking.PLP.CV.PCE.constants import SensorSource
# from tsf.core.results import DATA_NOK
# from pl_parking.PLP.CV.SPP.frames.frame import Frame

_log = logging.getLogger(__name__)

Empty_Dataframe = pd.DataFrame(columns=["timestamp", "bsig_index", "label_present"]).set_index("timestamp")


class PCESignals(SignalDefinition):
    """MF signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        BASE_CTRL_OPMODE_LSC = "Base_ctrl_opmode_lsc"
        BASE_CTRL_OPMODE_FC = "Base_ctrl_opmode_fc"
        BASE_CTRL_OPMODE_RSC = "Base_ctrl_opmode_rsc"
        BASE_CTRL_OPMODE_RC = "Base_ctrl_opmode_rc"
        CHIPSY_SIG_STATUS_LSC = "ChipsY_Sigstatus_lsc"
        CHIPSUV_SIG_STATUS_LSC = "ChipsUV_Sigstatus_lsc"
        CHIPSY_SIG_STATUS_RSC = "ChipsY_Sigstatus_rsc"
        CHIPSUV_SIG_STATUS_RSC = "ChipsUV_Sigstatus_rsc"
        CHIPSY_SIG_STATUS_RC = "ChipsY_Sigstatus_rc"
        CHIPSUV_SIG_STATUS_RC = "ChipsUV_Sigstatus_rc"
        CHIPSY_SIG_STATUS_FC = "ChipsY_Sigstatus_fc"
        CHIPSUV_SIG_STATUS_FC = "ChipsUV_Sigstatus_fc"
        DTCT_RESULTS_SIGSTATUS_LSC = "detection_results_sig_status_lsc"
        DTCT_RESULTS_SIGSTATUS_FC = "detection_results_sig_status_fc"
        DTCT_RESULTS_SIGSTATUS_RSC = "detection_results_sig_status_rsc"
        DTCT_RESULTS_SIGSTATUS_RC = "detection_results_sig_status_rc"
        CHIPSY_FOCALX_LSC = "Chipsy_focalx_lsc"
        CHIPSUV_FOCALX_LSC = "Chipsuv_focalx_lsc"
        CHIPSY_FOCALY_LSC = "Chipsy_focaly_lsc"
        CHIPSUV_FOCALY_LSC = "Chipsuv_focaly_lsc"
        CHIPSY_CENTERX_LSC = "Chipsy_Centerx_lsc"
        CHIPSUV_CENTERX_LSC = "Chipsuv_Centerx_lsc"
        CHIPSY_CENTERY_LSC = "Chipsy_Centery_lsc"
        CHIPSUV_CENTERY_LSC = "Chipsuv_Centery_lsc"
        CHIPSY_CAMERATYPE_LSC = "Chipsy_CameraType_lsc"
        CHIPSUV_CAMERATYPE_LSC = "Chipsuv_CameraType_lsc"
        DETECTION_RESULTS_FOCALX_LSC = "Detection_Results_FOCALX_lsc"
        DETECTION_RESULTS_FOCALY_LSC = "Detection_Results_FOCALY_lsc"
        DETECTION_RESULTS_CENTERX_LSC = "Detection_Results_CenterX_lsc"
        DETECTION_RESULTS_CENTERY_LSC = "Detection_Results_CenterY_lsc"
        DETECTION_RESULTS_CAMERATYPE_LSC = "Detection_Results_CameraType_lsc"
        SEMSEG_FOCALX_LSC = "SemSeg_FOCALX_lsc"
        SEMSEG_FOCALY_LSC = "SemSeg_FOCALY_lsc"
        SEMSEG_CENTERX_LSC = "SemSeg_CenterX_lsc"
        SEMSEG_CENTERY_LSC = "SemSeg_CenterY_lsc"
        SEMSEG_CAMERATYPE_LSC = "SemSeg_CameraType_lsc"
        CHIPSY_FOCALX_RSC = "Chipsy_focalx_rsc"
        CHIPSUV_FOCALX_RSC = "Chipsuv_focalx_rsc"
        CHIPSY_FOCALY_RSC = "Chipsy_focaly_rsc"
        CHIPSUV_FOCALY_RSC = "Chipsuv_focaly_rsc"
        CHIPSY_CENTERX_RSC = "Chipsy_Centerx_rsc"
        CHIPSUV_CENTERX_RSC = "Chipsuv_Centerx_rsc"
        CHIPSY_CENTERY_RSC = "Chipsy_Centery_rsc"
        CHIPSUV_CENTERY_RSC = "Chipsuv_Centery_rsc"
        CHIPSY_CAMERATYPE_RSC = "Chipsy_CameraType_rsc"
        CHIPSUV_CAMERATYPE_RSC = "Chipsuv_CameraType_rsc"
        DETECTION_RESULTS_FOCALX_RSC = "Detection_Results_FOCALX_rsc"
        DETECTION_RESULTS_FOCALY_RSC = "Detection_Results_FOCALY_rsc"
        DETECTION_RESULTS_CENTERX_RSC = "Detection_Results_CenterX_rsc"
        DETECTION_RESULTS_CENTERY_RSC = "Detection_Results_CenterY_rsc"
        DETECTION_RESULTS_CAMERATYPE_RSC = "Detection_Results_CameraType_rsc"
        SEMSEG_FOCALX_RSC = "SemSeg_FOCALX_rsc"
        SEMSEG_FOCALY_RSC = "SemSeg_FOCALY_rsc"
        SEMSEG_CENTERX_RSC = "SemSeg_CenterX_rsc"
        SEMSEG_CENTERY_RSC = "SemSeg_CenterY_rsc"
        SEMSEG_CAMERATYPE_RSC = "SemSeg_CameraType_rsc"
        CHIPSY_FOCALX_RC = "Chipsy_focalx_rc"
        CHIPSUV_FOCALX_RC = "Chipsuv_focalx_rc"
        CHIPSY_FOCALY_RC = "Chipsy_focaly_rc"
        CHIPSUV_FOCALY_RC = "Chipsuv_focaly_rc"
        CHIPSY_CENTERX_RC = "Chipsy_Centerx_rc"
        CHIPSUV_CENTERX_RC = "Chipsuv_Centerx_rc"
        CHIPSY_CENTERY_RC = "Chipsy_Centery_rc"
        CHIPSUV_CENTERY_RC = "Chipsuv_Centery_rc"
        CHIPSY_CAMERATYPE_RC = "Chipsy_CameraType_rc"
        CHIPSUV_CAMERATYPE_RC = "Chipsuv_CameraType_rc"
        DETECTION_RESULTS_FOCALX_RC = "Detection_Results_FOCALX_rc"
        DETECTION_RESULTS_FOCALY_RC = "Detection_Results_FOCALY_rc"
        DETECTION_RESULTS_CENTERX_RC = "Detection_Results_CenterX_rc"
        DETECTION_RESULTS_CENTERY_RC = "Detection_Results_CenterY_rc"
        DETECTION_RESULTS_CAMERATYPE_RC = "Detection_Results_CameraType_rc"
        SEMSEG_FOCALX_RC = "SemSeg_FOCALX_rc"
        SEMSEG_FOCALY_RC = "SemSeg_FOCALY_rc"
        SEMSEG_CENTERX_RC = "SemSeg_CenterX_rc"
        SEMSEG_CENTERY_RC = "SemSeg_CenterY_rc"
        SEMSEG_CAMERATYPE_RC = "SemSeg_CameraType_rc"
        CHIPSY_FOCALX_FC = "Chipsy_focalx_fc"
        CHIPSUV_FOCALX_FC = "Chipsuv_focalx_fc"
        CHIPSY_FOCALY_FC = "Chipsy_focaly_fc"
        CHIPSUV_FOCALY_FC = "Chipsuv_focaly_fc"
        CHIPSY_CENTERX_FC = "Chipsy_Centerx_fc"
        CHIPSUV_CENTERX_FC = "Chipsuv_Centerx_fc"
        CHIPSY_CENTERY_FC = "Chipsy_Centery_fc"
        CHIPSUV_CENTERY_FC = "Chipsuv_Centery_fc"
        CHIPSY_CAMERATYPE_FC = "Chipsy_CameraType_fc"
        CHIPSUV_CAMERATYPE_FC = "Chipsuv_CameraType_fc"
        DETECTION_RESULTS_FOCALX_FC = "Detection_Results_FOCALX_fc"
        DETECTION_RESULTS_FOCALY_FC = "Detection_Results_FOCALY_fc"
        DETECTION_RESULTS_CENTERX_FC = "Detection_Results_CenterX_fc"
        DETECTION_RESULTS_CENTERY_FC = "Detection_Results_CenterY_fc"
        DETECTION_RESULTS_CAMERATYPE_FC = "Detection_Results_CameraType_fc"
        SEMSEG_FOCALX_FC = "SemSeg_FOCALX_fc"
        SEMSEG_FOCALY_FC = "SemSeg_FOCALY_fc"
        SEMSEG_CENTERX_FC = "SemSeg_CenterX_fc"
        SEMSEG_CENTERY_FC = "SemSeg_CenterY_fc"
        SEMSEG_CAMERATYPE_FC = "SemSeg_CameraType_fc"
        NUM_CUBOID_DETECTIONS_FC = "num_cuboid_detections_fc"
        NUM_CUBOID_DETECTIONS_RC = "num_cuboid_detections_rc"
        NUM_CUBOID_DETECTIONS_RSC = "num_cuboid_detections_rsc"
        NUM_CUBOID_DETECTIONS_LSC = "num_cuboid_detections_lsc"
        CUBOID_KEY_POINTS_X_FC = "cuboid_detections_key_points_x_of_fc_det_"
        CUBOID_KEY_POINTS_Y_FC = "cuboid_detections_key_points_y_of_fc_det_"
        CUBOID_KEY_POINTS_X_RC = "cuboid_detections_key_points_x_of_rc_det_"
        CUBOID_KEY_POINTS_Y_RC = "cuboid_detections_key_points_y_of_rc_det_"
        CUBOID_KEY_POINTS_X_RSC = "cuboid_detections_key_points_x_of_rsc_det_"
        CUBOID_KEY_POINTS_Y_RSC = "cuboid_detections_key_points_y_of_rsc_det_"
        CUBOID_KEY_POINTS_X_LSC = "cuboid_detections_key_points_x_of_lsc_det_"
        CUBOID_KEY_POINTS_Y_LSC = "cuboid_detections_key_points_y_of_lsc_det_"
        CUBOID_SUB_CLASS_CONFIDENCE_FC = "cuboid_detections_subclass_confidence_of_fc_det_"
        CUBOID_SUB_CLASS_CONFIDENCE_RC = "cuboid_detections_subclass_confidence_of_rc_det_"
        CUBOID_SUB_CLASS_CONFIDENCE_RSC = "cuboid_detections_subclass_confidence_of_rsc_det_"
        CUBOID_SUB_CLASS_CONFIDENCE_LSC = "cuboid_detections_subclass_confidence_of_lsc_det_"
        CUBOID_SUB_CLASS_ID_FC = "cuboid_detections_subclass_id_of_fc_det_"
        CUBOID_SUB_CLASS_ID_RC = "cuboid_detections_subclass_id_of_rc_det_"
        CUBOID_SUB_CLASS_ID_RSC = "cuboid_detections_subclass_id_of_rsc_det_"
        CUBOID_SUB_CLASS_ID_LSC = "cuboid_detections_subclass_id_of_lsc_det_"
        NUM_BOUNDING_BOX_DETECTIONS_FC = "num_bounding_box_detections_fc"
        NUM_BOUNDING_BOX_DETECTIONS_RC = "num_bounding_box_detections_rc"
        NUM_BOUNDING_BOX_DETECTIONS_RSC = "num_bounding_box_detections_rsc"
        NUM_BOUNDING_BOX_DETECTIONS_LSC = "num_bounding_box_detections_lsc"
        BOUNDING_BOX_KEY_POINTS_X_FC = "bounding_box_detections_key_points_x_of_fc_det_"
        BOUNDING_BOX_KEY_POINTS_Y_FC = "bounding_box_detections_key_points_y_of_fc_det_"
        BOUNDING_BOX_KEY_POINTS_Y_RC = "bounding_box_detections_key_points_y_of_rc_det_"
        BOUNDING_BOX_KEY_POINTS_X_RC = "bounding_box_detections_key_points_x_of_rc_det_"
        BOUNDING_BOX_KEY_POINTS_X_RSC = "bounding_box_detections_key_points_x_of_rsc_det_"
        BOUNDING_BOX_KEY_POINTS_Y_RSC = "bounding_box_detections_key_points_y_of_rsc_det_"
        BOUNDING_BOX_KEY_POINTS_X_LSC = "bounding_box_detections_key_points_x_of_lsc_det_"
        BOUNDING_BOX_KEY_POINTS_Y_LSC = "bounding_box_detections_key_points_y_of_lsc_det_"
        BOUNDING_BOX_SUB_CLASS_CONFIDENCE_FC = "bounding_box_detections_subclass_confidence_of_fc_det_"
        BOUNDING_BOX_SUB_CLASS_CONFIDENCE_RC = "bounding_box_detections_subclass_confidence_of_rc_det_"
        BOUNDING_BOX_SUB_CLASS_CONFIDENCE_RSC = "bounding_box_detections_subclass_confidence_of_rsc_det_"
        BOUNDING_BOX_SUB_CLASS_CONFIDENCE_LSC = "bounding_box_detections_subclass_confidence_of_lsc_det_"
        BOUNDING_BOX_SUB_CLASS_ID_FC = "bounding_box_detections_subclass_id_of_fc_det_"
        BOUNDING_BOX_SUB_CLASS_ID_RC = "bounding_box_detections_subclass_id_of_rc_det_"
        BOUNDING_BOX_SUB_CLASS_ID_RSC = "bounding_box_detections_subclass_id_of_rsc_det_"
        BOUNDING_BOX_SUB_CLASS_ID_LSC = "bounding_box_detections_subclass_id_of_lsc_det_"
        NUM_PARKING_SLOT_DETECTIONS_FC = "num_parking_slot_detections_fc"
        NUM_PARKING_SLOT_DETECTIONS_RC = "num_parking_slot_detections_rc"
        NUM_PARKING_SLOT_DETECTIONS_RSC = "num_parking_slot_detections_rsc"
        NUM_PARKING_SLOT_DETECTIONS_LSC = "num_parking_slot_detections_lsc"
        PARKING_SLOT_KEY_POINTS_X_FC = "parking_slot_key_points_x_of_fc_det_"
        PARKING_SLOT_KEY_POINTS_Y_FC = "parking_slot_key_points_y_of_fc_det_"
        PARKING_SLOT_KEY_POINTS_X_RC = "parking_slot_key_points_x_of_rc_det_"
        PARKING_SLOT_KEY_POINTS_Y_RC = "parking_slot_key_points_y_of_rc_det_"
        PARKING_SLOT_KEY_POINTS_X_RSC = "parking_slot_key_points_x_of_rsc_det_"
        PARKING_SLOT_KEY_POINTS_Y_RSC = "parking_slot_key_points_y_of_rsc_det_"
        PARKING_SLOT_KEY_POINTS_X_LSC = "parking_slot_key_points_x_of_lsc_det_"
        PARKING_SLOT_KEY_POINTS_Y_LSC = "parking_slot_key_points_y_of_lsc_det_"
        PARKING_SLOT_SUB_CLASS_CONFIDENCE_FC = "parking_slot_subclass_confidence_of_fc_det_"
        PARKING_SLOT_SUB_CLASS_CONFIDENCE_RC = "parking_slot_subclass_confidence_of_rc_det_"
        PARKING_SLOT_SUB_CLASS_CONFIDENCE_RSC = "parking_slot_subclass_confidence_of_rsc_det_"
        PARKING_SLOT_SUB_CLASS_CONFIDENCE_LSC = "parking_slot_subclass_confidence_of_lsc_det_"
        PARKING_OCCLUSION_CONFIDENCE_FC = "parking_occlusion_confidence_fc_det_"
        PARKING_ORIENTATION_CONFIDENCE_FC = "parking_orientation_confidence_fc_det_"
        PARKING_OCCLUSION_CONFIDENCE_RC = "parking_occlusion_confidence_rc_det_"
        PARKING_ORIENTATION_CONFIDENCE_RC = "parking_orientation_confidence_rc_det_"
        PARKING_OCCLUSION_CONFIDENCE_RSC = "parking_occlusion_confidence_rsc_det_"
        PARKING_ORIENTATION_CONFIDENCE_RSC = "parking_orientation_confidence_rsc_det_"
        PARKING_OCCLUSION_CONFIDENCE_LSC = "parking_occlusion_confidence_lsc_det_"
        PARKING_ORIENTATION_CONFIDENCE_LSC = "parking_orientation_confidence_lsc_det_"
        PARKING_SLOT_SUB_CLASS_ID_FC = "parking_slot_subclass_id_of_fc_det_"
        PARKING_SLOT_SUB_CLASS_ID_RC = "parking_slot_subclass_id_of_rc_det_"
        PARKING_SLOT_SUB_CLASS_ID_RSC = "parking_slot_subclass_id_of_rsc_det_"
        PARKING_SLOT_SUB_CLASS_ID_LSC = "parking_slot_subclass_id_of_lsc_det_"
        NUM_RESULTS_FC = "number_of_results"
        NUM_RESULTS_RC = "number_of_results_rc"
        NUM_RESULTS_RSC = "number_of_results_rsc"
        NUM_RESULTS_LSC = "number_of_results_lsc"
        BASE_CTRL_TIMESTAMP_FC = "base_ctrl_timestamp_fc"
        BASE_CTRL_TIMESTAMP_RC = "base_ctrl_timestamp_rc"
        BASE_CTRL_TIMESTAMP_LSC = "base_ctrl_timestamp_lsc"
        BASE_CTRL_TIMESTAMP_RSC = "base_ctrl_timestamp_rsc"
        DETECTION_RESULTS_TIMESTAMP_FC = "detection_results_timestamp_fc"
        DETECTION_RESULTS_TIMESTAMP_RC = "detection_results_timestamp_rc"
        DETECTION_RESULTS_TIMESTAMP_RSC = "detection_results_timestamp_rsc"
        DETECTION_RESULTS_TIMESTAMP_LSC = "detection_results_timestamp_lsc"
        SEMSEG_TIMESTAMP_FC = "semseg_timestamp_fc"
        SEMSEG_TIMESTAMP_RC = "semseg_timestamp_rc"
        SEMSEG_TIMESTAMP_RSC = "semseg_timestamp_rsc"
        SEMSEG_TIMESTAMP_LSC = "semseg_timestamp_lsc"
        ODDYP1_TIMESTAMP_FC = "data_input_yp1_timestamp_fc"
        ODDUVP1_TIMESTAMP_FC = "data_input_uvp1_timestamp_fc"
        ODDYP1_TIMESTAMP_RC = "data_input_yp1_timestamp_rc"
        ODDUVP1_TIMESTAMP_RC = "data_input_uvp1_timestamp_rc"
        ODDYP1_TIMESTAMP_RSC = "data_input_yp1_timestamp_rsc"
        ODDUVP1_TIMESTAMP_RSC = "data_input_uvp1_timestamp_rsc"
        ODDYP1_TIMESTAMP_LSC = "data_input_yp1_timestamp_lsc"
        ODDUVP1_TIMESTAMP_LSC = "data_input_uvp1_timestamp_lsc"
        SEMSEG_SIGSTATUS_LSC = "semseg_sig_status_lsc"
        SEMSEG_SIGSTATUS_FC = "semseg_sig_status_fc"
        SEMSEG_SIGSTATUS_RSC = "semseg_sig_status_rsc"
        SEMSEG_SIGSTATUS_RC = "semseg_sig_status_rc"
        ALGO_SIGSTATE_FC = "algo_sigstate_fc"
        ALGO_COMPSTATE_FC = "algo_compstate_fc"
        ALGO_SIGSTATE_RC = "algo_sigstate_rc"
        ALGO_COMPSTATE_RC = "algo_compstate_rc"
        ALGO_SIGSTATE_RSC = "algo_sigstate_rsc"
        ALGO_COMPSTATE_RSC = "algo_compstate_rsc"
        ALGO_SIGSTATE_LSC = "algo_sigstate_lsc"
        ALGO_COMPSTATE_LSC = "algo_compstate_lsc"
        DETECTION_RESULTS_SENSORSOURCE_FC = "detection_results_sensorsource_fc"
        DETECTION_RESULTS_SENSORSOURCE_RC = "detection_results_sensorsource_rc"
        DETECTION_RESULTS_SENSORSOURCE_RSC = "detection_results_sensorsource_rsc"
        DETECTION_RESULTS_SENSORSOURCE_LSC = "detection_results_sensorsource_lsc"
        SEMSEG_SENSORSOURCE_FC = "semseg_sensorsource_fc"
        SEMSEG_SENSORSOURCE_RC = "semseg_sensorsource_rc"
        SEMSEG_SENSORSOURCE_RSC = "semseg_sensorsource_rsc"
        SEMSEG_SENSORSOURCE_LSC = "semseg_sensorsource_lsc"
        ODDYP1_SENSORSOURCE_FC = "data_input_yp1_sensorsource_fc"
        ODDUVP1_SENSORSOURCE_FC = "data_input_uv1_sensorsource_fc"
        ODDYP1_SENSORSOURCE_RC = "data_input_yp1_sensorsource_rc"
        ODDUVP1_SENSORSOURCE_RC = "data_input_uv1_sensorsource_rc"
        ODDYP1_SENSORSOURCE_RSC = "data_input_yp1_sensorsource_rsc"
        ODDUVP1_SENSORSOURCE_RSC = "data_input_uv1_sensorsource_rsc"
        ODDYP1_SENSORSOURCE_LSC = "data_input_yp1_sensorsource_lsc"
        ODDUVP1_SENSORSOURCE_LSC = "data_input_uv1_sensorsource_lsc"
        PARAMETERS_SENSORSOURCE_FC = "data_input_parameters_sensorsource_fc"
        PARAMETERS_SENSORSOURCE_RC = "data_input_parameters_sensorsource_rc"
        PARAMETERS_SENSORSOURCE_RSC = "data_input_parameters_sensorsource_rsc"
        PARAMETERS_SENSORSOURCE_LSC = "data_input_parameters_sensorsource_lsc"
        SEMSEG_MEASUREMENTCOUNTER_RSC = "semseg_measurement_counter_rsc"
        SEMSEG_MEASUREMENTCOUNTER_FC = "semseg_measurement_counter_fc"
        SEMSEG_MEASUREMENTCOUNTER_RC = "semseg_measurement_counter_rc"
        SEMSEG_MEASUREMENTCOUNTER_LSC = "semseg_measurement_counter_lsc"
        BASE_CTRL_MEASUREMENTCOUNTER_RC = "base_ctrl_measurement_counter_rc"
        BASE_CTRL_MEASUREMENTCOUNTER_LSC = "base_ctrl_measurement_counter_lsc"
        BASE_CTRL_MEASUREMENTCOUNTER_RSC = "base_ctrl_measurement_counter_rsc"
        BASE_CTRL_MEASUREMENTCOUNTER_FC = "base_ctrl_measurement_counter_fc"
        DETECTION_RESULTS_MEASUREMENTCOUNTER_FC = "detection_results_measurement_counter_fc"
        DETECTION_RESULTS_MEASUREMENTCOUNTER_RC = "detection_results_measurement_counter_rc"
        DETECTION_RESULTS_MEASUREMENTCOUNTER_LSC = "detection_results_measurement_counter_lsc"
        DETECTION_RESULTS_MEASUREMENTCOUNTER_RSC = "detection_results_measurement_counter_rsc"
        CHIPSY_TIMESTAMP_FC = "ChipsY_Timestamp_fc"
        CHIPSUV_TIMESTAMP_FC = "ChipsUV_Timestamp_fc"
        CHIPSY_TIMESTAMP_RC = "ChipsY_Timestamp_rc"
        CHIPSUV_TIMESTAMP_RC = "ChipsUV_Timestamp_rc"
        CHIPSY_TIMESTAMP_RSC = "ChipsY_Timestamp_rsc"
        CHIPSUV_TIMESTAMP_RSC = "ChipsUV_Timestamp_rsc"
        CHIPSY_TIMESTAMP_LSC = "ChipsY_Timestamp_lsc"
        CHIPSUV_TIMESTAMP_LSC = "ChipsUV_Timestamp_lsc"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()
        self._root = ["MTA_ADC5", "AP"]
        self._properties = self.get_properties()

    def get_properties(self):
        """Generate a string of signals to be read."""
        signal_dict = {
            # signal name has to be updated after having R4 recordings
            self.Columns.MTS_TS: "MTS.Package.TimeStamp",
            self.Columns.BASE_CTRL_OPMODE_LSC: ".GRAPPA_LSC_DATA.syncRef.m_baseCtrlData.eOpMode",
            self.Columns.BASE_CTRL_OPMODE_FC: ".GRAPPA_FC_DATA.syncRef.m_baseCtrlData.eOpMode",
            self.Columns.BASE_CTRL_OPMODE_RSC: ".GRAPPA_RSC_DATA.syncRef.m_baseCtrlData.eOpMode",
            self.Columns.BASE_CTRL_OPMODE_RC: ".GRAPPA_RC_DATA.syncRef.m_baseCtrlData.eOpMode",
            self.Columns.CHIPSY_SIG_STATUS_LSC: ".CHIPS_LSC_IMAGE.ChipsLscCylP1Y.signalHeader.eSigStatus",
            self.Columns.CHIPSUV_SIG_STATUS_LSC: ".CHIPS_LSC_IMAGE.ChipsLscCylP1UV.signalHeader.eSigStatus",
            self.Columns.CHIPSY_SIG_STATUS_RSC: ".CHIPS_RSC_IMAGE.ChipsRscCylP1Y.signalHeader.eSigStatus",
            self.Columns.CHIPSUV_SIG_STATUS_RSC: ".CHIPS_RSC_IMAGE.ChipsRscCylP1UV.signalHeader.eSigStatus",
            self.Columns.CHIPSY_SIG_STATUS_RC: ".CHIPS_RC_IMAGE.ChipsRcCylP1Y.signalHeader.eSigStatus",
            self.Columns.CHIPSUV_SIG_STATUS_RC: ".CHIPS_RC_IMAGE.ChipsRcCylP1UV.signalHeader.eSigStatus",
            self.Columns.CHIPSY_SIG_STATUS_FC: ".CHIPS_FC_IMAGE.ChipsFcCylP1Y.signalHeader.eSigStatus",
            self.Columns.CHIPSUV_SIG_STATUS_FC: ".CHIPS_FC_IMAGE.ChipsFcCylP1UV.signalHeader.eSigStatus",
            self.Columns.DTCT_RESULTS_SIGSTATUS_LSC: ".GRAPPA_LSC_DATA.DetectionResults.sSigHeader.eSigStatus",
            self.Columns.DTCT_RESULTS_SIGSTATUS_FC: ".GRAPPA_FC_DATA.DetectionResults.sSigHeader.eSigStatus",
            self.Columns.DTCT_RESULTS_SIGSTATUS_RSC: ".GRAPPA_RSC_DATA.DetectionResults.sSigHeader.eSigStatus",
            self.Columns.DTCT_RESULTS_SIGSTATUS_RC: ".GRAPPA_RC_DATA.DetectionResults.sSigHeader.eSigStatus",
            self.Columns.CHIPSY_FOCALX_LSC: ".CHIPS_LSC_IMAGE.ChipsLscCylP1Y.imageHeader.intrinsics.focalX",
            self.Columns.CHIPSUV_FOCALX_LSC: ".CHIPS_LSC_IMAGE.ChipsLscCylP1UV.imageHeader.intrinsics.focalX",
            self.Columns.CHIPSY_FOCALY_LSC: ".CHIPS_LSC_IMAGE.ChipsLscCylP1Y.imageHeader.intrinsics.focalY",
            self.Columns.CHIPSUV_FOCALY_LSC: ".CHIPS_LSC_IMAGE.ChipsLscCylP1UV.imageHeader.intrinsics.focalY",
            self.Columns.CHIPSY_CENTERX_LSC: ".CHIPS_LSC_IMAGE.ChipsLscCylP1Y.imageHeader.intrinsics.centerX",
            self.Columns.CHIPSUV_CENTERX_LSC: ".CHIPS_LSC_IMAGE.ChipsLscCylP1UV.imageHeader.intrinsics.centerX",
            self.Columns.CHIPSY_CENTERY_LSC: ".CHIPS_LSC_IMAGE.ChipsLscCylP1Y.imageHeader.intrinsics.centerY",
            self.Columns.CHIPSUV_CENTERY_LSC: ".CHIPS_LSC_IMAGE.ChipsLscCylP1UV.imageHeader.intrinsics.centerY",
            self.Columns.CHIPSY_CAMERATYPE_LSC: ".CHIPS_LSC_IMAGE.ChipsLscCylP1Y.imageHeader.intrinsics.cameraType",
            self.Columns.CHIPSUV_CAMERATYPE_LSC: ".CHIPS_LSC_IMAGE.ChipsLscCylP1UV.imageHeader.intrinsics.cameraType",
            self.Columns.DETECTION_RESULTS_FOCALX_LSC: ".GRAPPA_LSC_DATA.DetectionResults.sReferenceImageIntrinsics.focalX",
            self.Columns.DETECTION_RESULTS_FOCALY_LSC: ".GRAPPA_LSC_DATA.DetectionResults.sReferenceImageIntrinsics.focalY",
            self.Columns.DETECTION_RESULTS_CENTERX_LSC: ".GRAPPA_LSC_DATA.DetectionResults.sReferenceImageIntrinsics.centerX",
            self.Columns.DETECTION_RESULTS_CENTERY_LSC: ".GRAPPA_LSC_DATA.DetectionResults.sReferenceImageIntrinsics.centerY",
            self.Columns.DETECTION_RESULTS_CAMERATYPE_LSC: ".GRAPPA_LSC_DATA.DetectionResults.sReferenceImageIntrinsics.cameraType",
            self.Columns.SEMSEG_FOCALX_LSC: ".GRAPPA_LSC_IMAGE.GrappaSemSegLscImage.imageHeader.intrinsics.focalX",
            self.Columns.SEMSEG_FOCALY_LSC: ".GRAPPA_LSC_IMAGE.GrappaSemSegLscImage.imageHeader.intrinsics.focalY",
            self.Columns.SEMSEG_CENTERX_LSC: ".GRAPPA_LSC_IMAGE.GrappaSemSegLscImage.imageHeader.intrinsics.centerX",
            self.Columns.SEMSEG_CENTERY_LSC: ".GRAPPA_LSC_IMAGE.GrappaSemSegLscImage.imageHeader.intrinsics.centerY",
            self.Columns.SEMSEG_CAMERATYPE_LSC: ".GRAPPA_LSC_IMAGE.GrappaSemSegLscImage.imageHeader.intrinsics.cameraType",
            self.Columns.CHIPSY_FOCALX_RSC: ".CHIPS_RSC_IMAGE.ChipsRscCylP1Y.imageHeader.intrinsics.focalX",
            self.Columns.CHIPSUV_FOCALX_RSC: ".CHIPS_RSC_IMAGE.ChipsRscCylP1UV.imageHeader.intrinsics.focalX",
            self.Columns.CHIPSY_FOCALY_RSC: ".CHIPS_RSC_IMAGE.ChipsRscCylP1Y.imageHeader.intrinsics.focalY",
            self.Columns.CHIPSUV_FOCALY_RSC: ".CHIPS_RSC_IMAGE.ChipsRscCylP1UV.imageHeader.intrinsics.focalY",
            self.Columns.CHIPSY_CENTERX_RSC: ".CHIPS_RSC_IMAGE.ChipsRscCylP1Y.imageHeader.intrinsics.centerX",
            self.Columns.CHIPSUV_CENTERX_RSC: ".CHIPS_RSC_IMAGE.ChipsRscCylP1UV.imageHeader.intrinsics.centerX",
            self.Columns.CHIPSY_CENTERY_RSC: ".CHIPS_RSC_IMAGE.ChipsRscCylP1Y.imageHeader.intrinsics.centerY",
            self.Columns.CHIPSUV_CENTERY_RSC: ".CHIPS_RSC_IMAGE.ChipsRscCylP1UV.imageHeader.intrinsics.centerY",
            self.Columns.CHIPSY_CAMERATYPE_RSC: ".CHIPS_RSC_IMAGE.ChipsRscCylP1Y.imageHeader.intrinsics.cameraType",
            self.Columns.CHIPSUV_CAMERATYPE_RSC: ".CHIPS_RSC_IMAGE.ChipsRscCylP1UV.imageHeader.intrinsics.cameraType",
            self.Columns.DETECTION_RESULTS_FOCALX_RSC: ".GRAPPA_RSC_DATA.DetectionResults.sReferenceImageIntrinsics.focalX",
            self.Columns.DETECTION_RESULTS_FOCALY_RSC: ".GRAPPA_RSC_DATA.DetectionResults.sReferenceImageIntrinsics.focalY",
            self.Columns.DETECTION_RESULTS_CENTERX_RSC: ".GRAPPA_RSC_DATA.DetectionResults.sReferenceImageIntrinsics.centerX",
            self.Columns.DETECTION_RESULTS_CENTERY_RSC: ".GRAPPA_RSC_DATA.DetectionResults.sReferenceImageIntrinsics.centerY",
            self.Columns.DETECTION_RESULTS_CAMERATYPE_RSC: ".GRAPPA_RSC_DATA.DetectionResults.sReferenceImageIntrinsics.cameraType",
            self.Columns.SEMSEG_FOCALX_RSC: ".GRAPPA_RSC_IMAGE.GrappaSemSegRscImage.imageHeader.intrinsics.focalX",
            self.Columns.SEMSEG_FOCALY_RSC: ".GRAPPA_RSC_IMAGE.GrappaSemSegRscImage.imageHeader.intrinsics.focalY",
            self.Columns.SEMSEG_CENTERX_RSC: ".GRAPPA_RSC_IMAGE.GrappaSemSegRscImage.imageHeader.intrinsics.centerX",
            self.Columns.SEMSEG_CENTERY_RSC: ".GRAPPA_RSC_IMAGE.GrappaSemSegRscImage.imageHeader.intrinsics.centerY",
            self.Columns.SEMSEG_CAMERATYPE_RSC: ".GRAPPA_RSC_IMAGE.GrappaSemSegRscImage.imageHeader.intrinsics.cameraType",
            self.Columns.CHIPSY_FOCALX_RC: ".CHIPS_RC_IMAGE.ChipsRcCylP1Y.imageHeader.intrinsics.focalX",
            self.Columns.CHIPSUV_FOCALX_RC: ".CHIPS_RC_IMAGE.ChipsRcCylP1UV.imageHeader.intrinsics.focalX",
            self.Columns.CHIPSY_FOCALY_RC: ".CHIPS_RC_IMAGE.ChipsRcCylP1Y.imageHeader.intrinsics.focalY",
            self.Columns.CHIPSUV_FOCALY_RC: ".CHIPS_RC_IMAGE.ChipsRcCylP1UV.imageHeader.intrinsics.focalY",
            self.Columns.CHIPSY_CENTERX_RC: ".CHIPS_RC_IMAGE.ChipsRcCylP1Y.imageHeader.intrinsics.centerX",
            self.Columns.CHIPSUV_CENTERX_RC: ".CHIPS_RC_IMAGE.ChipsRcCylP1UV.imageHeader.intrinsics.centerX",
            self.Columns.CHIPSY_CENTERY_RC: ".CHIPS_RC_IMAGE.ChipsRcCylP1Y.imageHeader.intrinsics.centerY",
            self.Columns.CHIPSUV_CENTERY_RC: ".CHIPS_RC_IMAGE.ChipsRcCylP1UV.imageHeader.intrinsics.centerY",
            self.Columns.CHIPSY_CAMERATYPE_RC: ".CHIPS_RC_IMAGE.ChipsRcCylP1Y.imageHeader.intrinsics.cameraType",
            self.Columns.CHIPSUV_CAMERATYPE_RC: ".CHIPS_RC_IMAGE.ChipsRcCylP1UV.imageHeader.intrinsics.cameraType",
            self.Columns.DETECTION_RESULTS_FOCALX_RC: ".GRAPPA_RC_DATA.DetectionResults.sReferenceImageIntrinsics.focalX",
            self.Columns.DETECTION_RESULTS_FOCALY_RC: ".GRAPPA_RC_DATA.DetectionResults.sReferenceImageIntrinsics.focalY",
            self.Columns.DETECTION_RESULTS_CENTERX_RC: ".GRAPPA_RC_DATA.DetectionResults.sReferenceImageIntrinsics.centerX",
            self.Columns.DETECTION_RESULTS_CENTERY_RC: ".GRAPPA_RC_DATA.DetectionResults.sReferenceImageIntrinsics.centerY",
            self.Columns.DETECTION_RESULTS_CAMERATYPE_RC: ".GRAPPA_RC_DATA.DetectionResults.sReferenceImageIntrinsics.cameraType",
            self.Columns.SEMSEG_FOCALX_RC: ".GRAPPA_RC_IMAGE.GrappaSemSegRcImage.imageHeader.intrinsics.focalX",
            self.Columns.SEMSEG_FOCALY_RC: ".GRAPPA_RC_IMAGE.GrappaSemSegRcImage.imageHeader.intrinsics.focalY",
            self.Columns.SEMSEG_CENTERX_RC: ".GRAPPA_RC_IMAGE.GrappaSemSegRcImage.imageHeader.intrinsics.centerX",
            self.Columns.SEMSEG_CENTERY_RC: ".GRAPPA_RC_IMAGE.GrappaSemSegRcImage.imageHeader.intrinsics.centerY",
            self.Columns.SEMSEG_CAMERATYPE_RC: ".GRAPPA_RC_IMAGE.GrappaSemSegRcImage.imageHeader.intrinsics.cameraType",
            self.Columns.CHIPSY_FOCALX_FC: ".CHIPS_FC_IMAGE.ChipsFcCylP1Y.imageHeader.intrinsics.focalX",
            self.Columns.CHIPSUV_FOCALX_FC: ".CHIPS_FC_IMAGE.ChipsFcCylP1UV.imageHeader.intrinsics.focalX",
            self.Columns.CHIPSY_FOCALY_FC: ".CHIPS_FC_IMAGE.ChipsFcCylP1Y.imageHeader.intrinsics.focalY",
            self.Columns.CHIPSUV_FOCALY_FC: ".CHIPS_FC_IMAGE.ChipsFcCylP1UV.imageHeader.intrinsics.focalY",
            self.Columns.CHIPSY_CENTERX_FC: ".CHIPS_FC_IMAGE.ChipsFcCylP1Y.imageHeader.intrinsics.centerX",
            self.Columns.CHIPSUV_CENTERX_FC: ".CHIPS_FC_IMAGE.ChipsFcCylP1UV.imageHeader.intrinsics.centerX",
            self.Columns.CHIPSY_CENTERY_FC: ".CHIPS_FC_IMAGE.ChipsFcCylP1Y.imageHeader.intrinsics.centerY",
            self.Columns.CHIPSUV_CENTERY_FC: ".CHIPS_FC_IMAGE.ChipsFcCylP1UV.imageHeader.intrinsics.centerY",
            self.Columns.CHIPSY_CAMERATYPE_FC: ".CHIPS_FC_IMAGE.ChipsFcCylP1Y.imageHeader.intrinsics.cameraType",
            self.Columns.CHIPSUV_CAMERATYPE_FC: ".CHIPS_FC_IMAGE.ChipsFcCylP1UV.imageHeader.intrinsics.cameraType",
            self.Columns.DETECTION_RESULTS_FOCALX_FC: ".GRAPPA_FC_DATA.DetectionResults.sReferenceImageIntrinsics.focalX",
            self.Columns.DETECTION_RESULTS_FOCALY_FC: ".GRAPPA_FC_DATA.DetectionResults.sReferenceImageIntrinsics.focalY",
            self.Columns.DETECTION_RESULTS_CENTERX_FC: ".GRAPPA_FC_DATA.DetectionResults.sReferenceImageIntrinsics.centerX",
            self.Columns.DETECTION_RESULTS_CENTERY_FC: ".GRAPPA_FC_DATA.DetectionResults.sReferenceImageIntrinsics.centerY",
            self.Columns.DETECTION_RESULTS_CAMERATYPE_FC: ".GRAPPA_FC_DATA.DetectionResults.sReferenceImageIntrinsics.cameraType",
            self.Columns.SEMSEG_FOCALX_FC: ".GRAPPA_FC_IMAGE.GrappaSemSegFcImage.imageHeader.intrinsics.focalX",
            self.Columns.SEMSEG_FOCALY_FC: ".GRAPPA_FC_IMAGE.GrappaSemSegFcImage.imageHeader.intrinsics.focalY",
            self.Columns.SEMSEG_CENTERX_FC: ".GRAPPA_FC_IMAGE.GrappaSemSegFcImage.imageHeader.intrinsics.centerX",
            self.Columns.SEMSEG_CENTERY_FC: ".GRAPPA_FC_IMAGE.GrappaSemSegFcImage.imageHeader.intrinsics.centerY",
            self.Columns.SEMSEG_CAMERATYPE_FC: ".GRAPPA_FC_IMAGE.GrappaSemSegFcImage.imageHeader.intrinsics.cameraType",
            self.Columns.NUM_CUBOID_DETECTIONS_FC: ".GRAPPA_FC_DATA.DetectionResults.numCuboidDetections",
            self.Columns.NUM_CUBOID_DETECTIONS_RC: ".GRAPPA_RC_DATA.DetectionResults.numCuboidDetections",
            self.Columns.NUM_CUBOID_DETECTIONS_RSC: ".GRAPPA_RSC_DATA.DetectionResults.numCuboidDetections",
            self.Columns.NUM_CUBOID_DETECTIONS_LSC: ".GRAPPA_LSC_DATA.DetectionResults.numCuboidDetections",
            self.Columns.NUM_BOUNDING_BOX_DETECTIONS_FC: ".GRAPPA_FC_DATA.DetectionResults.numBoundingBoxDetections",
            self.Columns.NUM_BOUNDING_BOX_DETECTIONS_RC: ".GRAPPA_RC_DATA.DetectionResults.numBoundingBoxDetections",
            self.Columns.NUM_BOUNDING_BOX_DETECTIONS_RSC: ".GRAPPA_RSC_DATA.DetectionResults.numBoundingBoxDetections",
            self.Columns.NUM_BOUNDING_BOX_DETECTIONS_LSC: ".GRAPPA_LSC_DATA.DetectionResults.numBoundingBoxDetections",
            self.Columns.NUM_PARKING_SLOT_DETECTIONS_FC: ".GRAPPA_FC_DATA.DetectionResults.numPolynomialDetections",
            self.Columns.NUM_PARKING_SLOT_DETECTIONS_RC: ".GRAPPA_RC_DATA.DetectionResults.numPolynomialDetections",
            self.Columns.NUM_PARKING_SLOT_DETECTIONS_RSC: ".GRAPPA_RSC_DATA.DetectionResults.numPolynomialDetections",
            self.Columns.NUM_PARKING_SLOT_DETECTIONS_LSC: ".GRAPPA_LSC_DATA.DetectionResults.numPolynomialDetections",
            self.Columns.NUM_RESULTS_FC: ".GRAPPA_FC_DATA.DetectionResults.uiNumResults",
            self.Columns.NUM_RESULTS_RC: ".GRAPPA_RC_DATA.DetectionResults.uiNumResults",
            self.Columns.NUM_RESULTS_RSC: ".GRAPPA_RSC_DATA.DetectionResults.uiNumResults",
            self.Columns.NUM_RESULTS_LSC: ".GRAPPA_LSC_DATA.DetectionResults.uiNumResults",
            self.Columns.BASE_CTRL_TIMESTAMP_FC: ".GRAPPA_FC_DATA.syncRef.m_baseCtrlData.sSigHeader.uiTimeStamp",
            self.Columns.BASE_CTRL_TIMESTAMP_RC: ".GRAPPA_RC_DATA.syncRef.m_baseCtrlData.sSigHeader.uiTimeStamp",
            self.Columns.BASE_CTRL_TIMESTAMP_RSC: ".GRAPPA_RSC_DATA.syncRef.m_baseCtrlData.sSigHeader.uiTimeStamp",
            self.Columns.BASE_CTRL_TIMESTAMP_LSC: ".GRAPPA_LSC_DATA.syncRef.m_baseCtrlData.sSigHeader.uiTimeStamp",
            self.Columns.DETECTION_RESULTS_TIMESTAMP_RC: ".GRAPPA_RC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
            self.Columns.DETECTION_RESULTS_TIMESTAMP_FC: ".GRAPPA_FC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
            self.Columns.DETECTION_RESULTS_TIMESTAMP_RSC: ".GRAPPA_RSC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
            self.Columns.DETECTION_RESULTS_TIMESTAMP_LSC: ".GRAPPA_LSC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
            self.Columns.SEMSEG_TIMESTAMP_FC: ".GRAPPA_FC_IMAGE.GrappaSemSegFcImage.signalHeader.uiTimeStamp",
            self.Columns.SEMSEG_TIMESTAMP_RC: ".GRAPPA_RC_IMAGE.GrappaSemSegRcImage.signalHeader.uiTimeStamp",
            self.Columns.SEMSEG_TIMESTAMP_RSC: ".GRAPPA_RSC_IMAGE.GrappaSemSegRscImage.signalHeader.uiTimeStamp",
            self.Columns.SEMSEG_TIMESTAMP_LSC: ".GRAPPA_LSC_IMAGE.GrappaSemSegLscImage.signalHeader.uiTimeStamp",
            self.Columns.ODDYP1_TIMESTAMP_FC: ".CHIPS_FC_CYL_DATA.pOddCylYP1Image.signalHeader.uiTimeStamp",
            self.Columns.ODDUVP1_TIMESTAMP_FC: ".CHIPS_FC_CYL_DATA.pOddCylUVP1Image.signalHeader.uiTimeStamp",
            self.Columns.ODDYP1_TIMESTAMP_RC: ".CHIPS_RC_CYL_DATA.pOddCylYP1Image.signalHeader.uiTimeStamp",
            self.Columns.ODDUVP1_TIMESTAMP_RC: ".CHIPS_RC_CYL_DATA.pOddCylUVP1Image.signalHeader.uiTimeStamp",
            self.Columns.ODDYP1_TIMESTAMP_RSC: ".CHIPS_RSC_CYL_DATA.pOddCylYP1Image.signalHeader.uiTimeStamp",
            self.Columns.ODDUVP1_TIMESTAMP_RSC: ".CHIPS_RSC_CYL_DATA.pOddCylUVP1Image.signalHeader.uiTimeStamp",
            self.Columns.ODDYP1_TIMESTAMP_LSC: ".CHIPS_LSC_CYL_DATA.pOddCylYP1Image.signalHeader.uiTimeStamp",
            self.Columns.ODDUVP1_TIMESTAMP_LSC: ".CHIPS_LSC_CYL_DATA.pOddCylUVP1Image.signalHeader.uiTimeStamp",
            self.Columns.SEMSEG_SIGSTATUS_LSC: ".GRAPPA_LSC_IMAGE.GrappaSemSegLscImage.signalHeader.eSigStatus",
            self.Columns.SEMSEG_SIGSTATUS_FC: ".GRAPPA_FC_IMAGE.GrappaSemSegFcImage.signalHeader.eSigStatus",
            self.Columns.SEMSEG_SIGSTATUS_RSC: ".GRAPPA_RSC_IMAGE.GrappaSemSegRscImage.signalHeader.eSigStatus",
            self.Columns.SEMSEG_SIGSTATUS_RC: ".GRAPPA_RC_IMAGE.GrappaSemSegRcImage.signalHeader.eSigStatus",
            self.Columns.ALGO_SIGSTATE_FC: ".GRAPPA_FC_DATA.m_algoCompState.sSigHeader.eSigStatus",
            self.Columns.ALGO_COMPSTATE_FC: ".GRAPPA_FC_DATA.m_algoCompState.eCompState",
            self.Columns.ALGO_SIGSTATE_RC: ".GRAPPA_RC_DATA.m_algoCompState.sSigHeader.eSigStatus",
            self.Columns.ALGO_COMPSTATE_RC: ".GRAPPA_RC_DATA.m_algoCompState.eCompState",
            self.Columns.ALGO_SIGSTATE_LSC: ".GRAPPA_LSC_DATA.m_algoCompState.sSigHeader.eSigStatus",
            self.Columns.ALGO_COMPSTATE_LSC: ".GRAPPA_LSC_DATA.m_algoCompState.eCompState",
            self.Columns.ALGO_SIGSTATE_RSC: ".GRAPPA_RSC_DATA.m_algoCompState.sSigHeader.eSigStatus",
            self.Columns.ALGO_COMPSTATE_RSC: ".GRAPPA_RSC_DATA.m_algoCompState.eCompState",
            self.Columns.DETECTION_RESULTS_SENSORSOURCE_FC: ".GRAPPA_FC_DATA.DetectionResults.eSensorSource",
            self.Columns.DETECTION_RESULTS_SENSORSOURCE_RC: ".GRAPPA_RC_DATA.DetectionResults.eSensorSource",
            self.Columns.DETECTION_RESULTS_SENSORSOURCE_RSC: ".GRAPPA_RSC_DATA.DetectionResults.eSensorSource",
            self.Columns.DETECTION_RESULTS_SENSORSOURCE_LSC: ".GRAPPA_LSC_DATA.DetectionResults.eSensorSource",
            self.Columns.SEMSEG_SENSORSOURCE_FC: ".GRAPPA_FC_DATA.GrappaSemSegFcImage.signalHeader.eSensorSource",
            self.Columns.SEMSEG_SENSORSOURCE_RC: ".GRAPPA_RC_DATA.GrappaSemSegRcImage.signalHeader.eSensorSource",
            self.Columns.SEMSEG_SENSORSOURCE_RSC: ".GRAPPA_RSC_DATA.GrappaSemSegRscImage.signalHeader.eSensorSource",
            self.Columns.SEMSEG_SENSORSOURCE_LSC: ".GRAPPA_LSC_DATA.GrappaSemSegLscImage.signalHeader.eSensorSource",
            self.Columns.ODDYP1_SENSORSOURCE_FC: ".GRAPPA_FC_DATA.OddYP1Image.signalHeader.sensorSource",
            self.Columns.ODDUVP1_SENSORSOURCE_FC: ".GRAPPA_FC_DATA.OddUVP1Image.signalHeader.sensorSource",
            self.Columns.ODDYP1_SENSORSOURCE_RC: ".GRAPPA_RC_DATA.OddYP1Image.signalHeader.sensorSource",
            self.Columns.ODDUVP1_SENSORSOURCE_RC: ".GRAPPA_RC_DATA.OddUVP1Image.signalHeader.sensorSource",
            self.Columns.ODDYP1_SENSORSOURCE_RSC: ".GRAPPA_RSC_DATA.OddYP1Image.signalHeader.sensorSource",
            self.Columns.ODDUVP1_SENSORSOURCE_RSC: ".GRAPPA_RSC_DATA.OddUVP1Image.signalHeader.sensorSource",
            self.Columns.ODDYP1_SENSORSOURCE_LSC: ".GRAPPA_LSC_DATA.OddYP1Image.signalHeader.sensorSource",
            self.Columns.ODDUVP1_SENSORSOURCE_LSC: ".GRAPPA_LSC_DATA.OddUVP1Image.signalHeader.sensorSource",
            self.Columns.PARAMETERS_SENSORSOURCE_FC: ".GRAPPA_FC_DATA.Parameters.eSensorSource",
            self.Columns.PARAMETERS_SENSORSOURCE_RC: ".GRAPPA_RC_DATA.Parameters.eSensorSource",
            self.Columns.PARAMETERS_SENSORSOURCE_RSC: ".GRAPPA_RSC_DATA.Parameters.eSensorSource",
            self.Columns.PARAMETERS_SENSORSOURCE_LSC: ".GRAPPA_LSC_DATA.Parameters.eSensorSource",
            self.Columns.SEMSEG_MEASUREMENTCOUNTER_FC: ".GRAPPA_FC_IMAGE.GrappaSemSegFcImage.signalHeader.uiMeasurementCounter",
            self.Columns.SEMSEG_MEASUREMENTCOUNTER_RC: ".GRAPPA_RC_IMAGE.GrappaSemSegRcImage.signalHeader.uiMeasurementCounter",
            self.Columns.SEMSEG_MEASUREMENTCOUNTER_RSC: ".GRAPPA_RSC_IMAGE.GrappaSemSegRscImage.signalHeader.uiMeasurementCounter",
            self.Columns.SEMSEG_MEASUREMENTCOUNTER_LSC: ".GRAPPA_LSC_IMAGE.GrappaSemSegLscImage.signalHeader.uiMeasurementCounter",
            self.Columns.BASE_CTRL_MEASUREMENTCOUNTER_FC: ".GRAPPA_FC_DATA.syncRef.m_baseCtrlData.sSigHeader.uiMeasurementCounter",
            self.Columns.BASE_CTRL_MEASUREMENTCOUNTER_RC: ".GRAPPA_RC_DATA.syncRef.m_baseCtrlData.sSigHeader.uiMeasurementCounter",
            self.Columns.BASE_CTRL_MEASUREMENTCOUNTER_RSC: ".GRAPPA_RSC_DATA.syncRef.m_baseCtrlData.sSigHeader.uiMeasurementCounter",
            self.Columns.BASE_CTRL_MEASUREMENTCOUNTER_LSC: ".GRAPPA_LSC_DATA.syncRef.m_baseCtrlData.sSigHeader.uiMeasurementCounter",
            self.Columns.DETECTION_RESULTS_MEASUREMENTCOUNTER_FC: ".GRAPPA_FC_DATA.DetectionResults.sSigHeader.uiMeasurementCounter",
            self.Columns.DETECTION_RESULTS_MEASUREMENTCOUNTER_RC: ".GRAPPA_RC_DATA.DetectionResults.sSigHeader.uiMeasurementCounter",
            self.Columns.DETECTION_RESULTS_MEASUREMENTCOUNTER_RSC: ".GRAPPA_RSC_DATA.DetectionResults.sSigHeader.uiMeasurementCounter",
            self.Columns.DETECTION_RESULTS_MEASUREMENTCOUNTER_LSC: ".GRAPPA_LSC_DATA.DetectionResults.sSigHeader.uiMeasurementCounter",
            self.Columns.CHIPSY_TIMESTAMP_RSC: ".CHIPS_RSC_IMAGE.ChipsRscCylP1Y.signalHeader.uiTimeStamp",
            self.Columns.CHIPSUV_TIMESTAMP_RSC: ".CHIPS_RSC_IMAGE.ChipsRscCylP1UV.signalHeader.uiTimeStamp",
            self.Columns.CHIPSY_TIMESTAMP_LSC: ".CHIPS_LSC_IMAGE.ChipsLscCylP1Y.signalHeader.uiTimeStamp",
            self.Columns.CHIPSUV_TIMESTAMP_LSC: ".CHIPS_LSC_IMAGE.ChipsLscCylP1UV.signalHeader.uiTimeStamp",
            self.Columns.CHIPSY_TIMESTAMP_RC: ".CHIPS_RC_IMAGE.ChipsRcCylP1Y.signalHeader.uiTimeStamp",
            self.Columns.CHIPSUV_TIMESTAMP_RC: ".CHIPS_RC_IMAGE.ChipsRcCylP1UV.signalHeader.uiTimeStamp",
            self.Columns.CHIPSY_TIMESTAMP_FC: ".CHIPS_FC_IMAGE.ChipsFcCylP1Y.signalHeader.uiTimeStamp",
            self.Columns.CHIPSUV_TIMESTAMP_FC: ".CHIPS_FC_IMAGE.ChipsFcCylP1UV.signalHeader.uiTimeStamp",
        }
        for idx in range(0, ct.grappa_constants.GRAPPA_MAX_NUMBER_OF_SPECIFIC_DETECTIONS):
            for key in range(0, 8):
                signal_dict[self.Columns.CUBOID_KEY_POINTS_X_FC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_FC_DATA.DetectionResults.aCuboidDetections[{idx}].aKeyPoints[{key}].x"
                )
                signal_dict[self.Columns.CUBOID_KEY_POINTS_Y_FC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_FC_DATA.DetectionResults.aCuboidDetections[{idx}].aKeyPoints[{key}].y"
                )
                signal_dict[self.Columns.CUBOID_KEY_POINTS_X_RSC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_RSC_DATA.DetectionResults.aCuboidDetections[{idx}].aKeyPoints[{key}].x"
                )
                signal_dict[self.Columns.CUBOID_KEY_POINTS_Y_RSC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_RSC_DATA.DetectionResults.aCuboidDetections[{idx}].aKeyPoints[{key}].y"
                )
                signal_dict[self.Columns.CUBOID_KEY_POINTS_X_RC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_RC_DATA.DetectionResults.aCuboidDetections[{idx}].aKeyPoints[{key}].x"
                )
                signal_dict[self.Columns.CUBOID_KEY_POINTS_Y_RC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_RC_DATA.DetectionResults.aCuboidDetections[{idx}].aKeyPoints[{key}].y"
                )
                signal_dict[self.Columns.CUBOID_KEY_POINTS_X_LSC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_LSC_DATA.DetectionResults.aCuboidDetections[{idx}].aKeyPoints[{key}].x"
                )
                signal_dict[self.Columns.CUBOID_KEY_POINTS_Y_LSC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_LSC_DATA.DetectionResults.aCuboidDetections[{idx}].aKeyPoints[{key}].y"
                )
            for key in range(0, 2):
                signal_dict[self.Columns.BOUNDING_BOX_KEY_POINTS_X_FC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_FC_DATA.DetectionResults.aBoundingBoxDetections[{idx}].aKeyPoints[{key}].x"
                )
                signal_dict[self.Columns.BOUNDING_BOX_KEY_POINTS_Y_FC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_FC_DATA.DetectionResults.aBoundingBoxDetections[{idx}].aKeyPoints[{key}].y"
                )
                signal_dict[self.Columns.BOUNDING_BOX_KEY_POINTS_X_RC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_RC_DATA.DetectionResults.aBoundingBoxDetections[{idx}].aKeyPoints[{key}].x"
                )
                signal_dict[self.Columns.BOUNDING_BOX_KEY_POINTS_Y_RC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_RC_DATA.DetectionResults.aBoundingBoxDetections[{idx}].aKeyPoints[{key}].y"
                )
                signal_dict[self.Columns.BOUNDING_BOX_KEY_POINTS_X_RSC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_RSC_DATA.DetectionResults.aBoundingBoxDetections[{idx}].aKeyPoints[{key}].x"
                )
                signal_dict[self.Columns.BOUNDING_BOX_KEY_POINTS_Y_RSC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_RSC_DATA.DetectionResults.aBoundingBoxDetections[{idx}].aKeyPoints[{key}].y"
                )
                signal_dict[self.Columns.BOUNDING_BOX_KEY_POINTS_X_LSC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_LSC_DATA.DetectionResults.aBoundingBoxDetections[{idx}].aKeyPoints[{key}].x"
                )
                signal_dict[self.Columns.BOUNDING_BOX_KEY_POINTS_Y_LSC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_LSC_DATA.DetectionResults.aBoundingBoxDetections[{idx}].aKeyPoints[{key}].y"
                )
            for key in range(0, 4):
                signal_dict[self.Columns.PARKING_SLOT_KEY_POINTS_X_FC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_FC_DATA.DetectionResults.aPolynomialDetections[{idx}].aKeyPoints[{key}].x"
                )
                signal_dict[self.Columns.PARKING_SLOT_KEY_POINTS_Y_FC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_FC_DATA.DetectionResults.aPolynomialDetections[{idx}].aKeyPoints[{key}].y"
                )
                signal_dict[self.Columns.PARKING_SLOT_KEY_POINTS_X_RC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_RC_DATA.DetectionResults.aPolynomialDetections[{idx}].aKeyPoints[{key}].x"
                )
                signal_dict[self.Columns.PARKING_SLOT_KEY_POINTS_Y_RC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_RC_DATA.DetectionResults.aPolynomialDetections[{idx}].aKeyPoints[{key}].y"
                )
                signal_dict[self.Columns.PARKING_SLOT_KEY_POINTS_X_RSC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_RSC_DATA.DetectionResults.aPolynomialDetections[{idx}].aKeyPoints[{key}].x"
                )
                signal_dict[self.Columns.PARKING_SLOT_KEY_POINTS_Y_RSC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_RSC_DATA.DetectionResults.aPolynomialDetections[{idx}].aKeyPoints[{key}].y"
                )
                signal_dict[self.Columns.PARKING_SLOT_KEY_POINTS_X_LSC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_LSC_DATA.DetectionResults.aPolynomialDetections[{idx}].aKeyPoints[{key}].x"
                )
                signal_dict[self.Columns.PARKING_SLOT_KEY_POINTS_Y_LSC + str(idx) + "_keypoint_" + str(key)] = (
                    f".GRAPPA_LSC_DATA.DetectionResults.aPolynomialDetections[{idx}].aKeyPoints[{key}].y"
                )
            signal_dict[self.Columns.CUBOID_SUB_CLASS_ID_FC + str(idx)] = (
                f".GRAPPA_FC_DATA.DetectionResults.aCuboidDetections[{idx}].eSubClassId"
            )
            signal_dict[self.Columns.CUBOID_SUB_CLASS_ID_RC + str(idx)] = (
                f".GRAPPA_RC_DATA.DetectionResults.aCuboidDetections[{idx}].eSubClassId"
            )
            signal_dict[self.Columns.CUBOID_SUB_CLASS_ID_RSC + str(idx)] = (
                f".GRAPPA_RSC_DATA.DetectionResults.aCuboidDetections[{idx}].eSubClassId"
            )
            signal_dict[self.Columns.CUBOID_SUB_CLASS_ID_LSC + str(idx)] = (
                f".GRAPPA_LSC_DATA.DetectionResults.aCuboidDetections[{idx}].eSubClassId"
            )
            signal_dict[self.Columns.CUBOID_SUB_CLASS_CONFIDENCE_FC + str(idx)] = (
                f".GRAPPA_FC_DATA.DetectionResults.aCuboidDetections[{idx}].aSubClassConfidences"
            )
            signal_dict[self.Columns.CUBOID_SUB_CLASS_CONFIDENCE_RC + str(idx)] = (
                f".GRAPPA_RC_DATA.DetectionResults.aCuboidDetections[{idx}].aSubClassConfidences"
            )
            signal_dict[self.Columns.CUBOID_SUB_CLASS_CONFIDENCE_RSC + str(idx)] = (
                f".GRAPPA_RSC_DATA.DetectionResults.aCuboidDetections[{idx}].aSubClassConfidences"
            )
            signal_dict[self.Columns.CUBOID_SUB_CLASS_CONFIDENCE_LSC + str(idx)] = (
                f".GRAPPA_LSC_DATA.DetectionResults.aCuboidDetections[{idx}].aSubClassConfidences"
            )
            signal_dict[self.Columns.BOUNDING_BOX_SUB_CLASS_ID_FC + str(idx)] = (
                f".GRAPPA_FC_DATA.DetectionResults.aBoundingBoxDetections[{idx}].eSubClassId"
            )
            signal_dict[self.Columns.BOUNDING_BOX_SUB_CLASS_ID_RC + str(idx)] = (
                f".GRAPPA_RC_DATA.DetectionResults.aBoundingBoxDetections[{idx}].eSubClassId"
            )
            signal_dict[self.Columns.BOUNDING_BOX_SUB_CLASS_ID_RSC + str(idx)] = (
                f".GRAPPA_RSC_DATA.DetectionResults.aBoundingBoxDetections[{idx}].eSubClassId"
            )
            signal_dict[self.Columns.BOUNDING_BOX_SUB_CLASS_ID_LSC + str(idx)] = (
                f".GRAPPA_LSC_DATA.DetectionResults.aBoundingBoxDetections[{idx}].eSubClassId"
            )
            signal_dict[self.Columns.BOUNDING_BOX_SUB_CLASS_CONFIDENCE_FC + str(idx)] = (
                f".GRAPPA_FC_DATA.DetectionResults.aBoundingBoxDetections[{idx}].aSubClassConfidences"
            )
            signal_dict[self.Columns.BOUNDING_BOX_SUB_CLASS_CONFIDENCE_RC + str(idx)] = (
                f".GRAPPA_RC_DATA.DetectionResults.aBoundingBoxDetections[{idx}].aSubClassConfidences"
            )
            signal_dict[self.Columns.BOUNDING_BOX_SUB_CLASS_CONFIDENCE_RSC + str(idx)] = (
                f".GRAPPA_RSC_DATA.DetectionResults.aBoundingBoxDetections[{idx}].aSubClassConfidences"
            )
            signal_dict[self.Columns.BOUNDING_BOX_SUB_CLASS_CONFIDENCE_LSC + str(idx)] = (
                f".GRAPPA_LSC_DATA.DetectionResults.aBoundingBoxDetections[{idx}].aSubClassConfidences"
            )
            signal_dict[self.Columns.PARKING_SLOT_SUB_CLASS_ID_FC + str(idx)] = (
                f".GRAPPA_FC_DATA.DetectionResults.aPolynomialDetections[{idx}].eSubClassId"
            )
            signal_dict[self.Columns.PARKING_SLOT_SUB_CLASS_ID_RC + str(idx)] = (
                f".GRAPPA_RC_DATA.DetectionResults.aPolynomialDetections[{idx}].eSubClassId"
            )
            signal_dict[self.Columns.PARKING_SLOT_SUB_CLASS_ID_RSC + str(idx)] = (
                f".GRAPPA_RSC_DATA.DetectionResults.aPolynomialDetections[{idx}].eSubClassId"
            )
            signal_dict[self.Columns.PARKING_SLOT_SUB_CLASS_ID_LSC + str(idx)] = (
                f".GRAPPA_LSC_DATA.DetectionResults.aPolynomialDetections[{idx}].eSubClassId"
            )
            signal_dict[self.Columns.PARKING_SLOT_SUB_CLASS_CONFIDENCE_FC + str(idx)] = (
                f".GRAPPA_FC_DATA.DetectionResults.aPolynomialDetections[{idx}].aSubClassConfidences"
            )
            signal_dict[self.Columns.PARKING_SLOT_SUB_CLASS_CONFIDENCE_RC + str(idx)] = (
                f".GRAPPA_RC_DATA.DetectionResults.aPolynomialDetections[{idx}].aSubClassConfidences"
            )
            signal_dict[self.Columns.PARKING_SLOT_SUB_CLASS_CONFIDENCE_RSC + str(idx)] = (
                f".GRAPPA_RSC_DATA.DetectionResults.aPolynomialDetections[{idx}].aSubClassConfidences"
            )
            signal_dict[self.Columns.PARKING_SLOT_SUB_CLASS_CONFIDENCE_LSC + str(idx)] = (
                f".GRAPPA_LSC_DATA.DetectionResults.aPolynomialDetections[{idx}].aSubClassConfidences"
            )
            signal_dict[self.Columns.PARKING_OCCLUSION_CONFIDENCE_FC + str(idx)] = (
                f".GRAPPA_FC_DATA.DetectionResults.aPolynomialDetections[{idx}].aOcclusionValues"
            )
            signal_dict[self.Columns.PARKING_OCCLUSION_CONFIDENCE_RC + str(idx)] = (
                f".GRAPPA_RC_DATA.DetectionResults.aPolynomialDetections[{idx}].aOcclusionValues"
            )
            signal_dict[self.Columns.PARKING_OCCLUSION_CONFIDENCE_RSC + str(idx)] = (
                f".GRAPPA_RSC_DATA.DetectionResults.aPolynomialDetections[{idx}].aOcclusionValues"
            )
            signal_dict[self.Columns.PARKING_OCCLUSION_CONFIDENCE_LSC + str(idx)] = (
                f".GRAPPA_LSC_DATA.DetectionResults.aPolynomialDetections[{idx}].aOcclusionValues"
            )
            signal_dict[self.Columns.PARKING_ORIENTATION_CONFIDENCE_FC + str(idx)] = (
                f".GRAPPA_FC_DATA.DetectionResults.aPolynomialDetections[{idx}].aOrientationConfidences"
            )
            signal_dict[self.Columns.PARKING_ORIENTATION_CONFIDENCE_RC + str(idx)] = (
                f".GRAPPA_RC_DATA.DetectionResults.aPolynomialDetections[{idx}].aOrientationConfidences"
            )
            signal_dict[self.Columns.PARKING_ORIENTATION_CONFIDENCE_RSC + str(idx)] = (
                f".GRAPPA_RSC_DATA.DetectionResults.aPolynomialDetections[{idx}].aOrientationConfidences"
            )
            signal_dict[self.Columns.PARKING_ORIENTATION_CONFIDENCE_LSC + str(idx)] = (
                f".GRAPPA_LSC_DATA.DetectionResults.aPolynomialDetections[{idx}].aOrientationConfidences"
            )
        return signal_dict


def check_validity_of_cuboid_keypoints(df, camera, eval_frame):
    """Checks Validity of cuboid keypoints"""
    dict_list_keypoints = []
    dict_obj_keypoints = {}
    dict_det_keypoints = {}
    dict_list_Timestamps = []
    for _, row in df.iterrows():
        num_cuboid_detection = int(row[f"num_cuboid_detections_{camera}"])
        timestamp = int(row[f"detection_results_timestamp_{camera}"])
        if timestamp in eval_frame.valid_timestamps_in_camera[camera]:
            for det in range(0, num_cuboid_detection):
                if eval_frame.valid_detections_in_camera[camera][f"{timestamp}_{det}"]:
                    dict_det_keypoints[f"frame{timestamp}_det{det}"] = True
                    for keypoint in range(0, 8):  # cuboid detections have 8 keypoints
                        keypoints_cuboid_x = row[
                            f"cuboid_detections_key_points_x_of_{camera}_det_{det}_keypoint_{keypoint}"
                        ]
                        keypoints_cuboid_y = row[
                            f"cuboid_detections_key_points_y_of_{camera}_det_{det}_keypoint_{keypoint}"
                        ]
                        if keypoints_cuboid_x > 0 and keypoints_cuboid_y > 0:
                            dict_obj_keypoints[f"frame{timestamp}_det{det}_keypoint{keypoint}"] = True
                        else:
                            dict_obj_keypoints[f"frame{timestamp}_det{det}_keypoint{keypoint}"] = False
                            dict_list_Timestamps.append(timestamp)
                            dict_det_keypoints[f"frame{timestamp}_det{det}"] = False
            dict_list_Timestamps = list(dict.fromkeys(dict_list_Timestamps))
    dict_list_keypoints.append(dict_obj_keypoints)

    if any(ele is True for ele in dict_det_keypoints.values()):
        validity_of_keypoints = True
    else:
        validity_of_keypoints = False

    return validity_of_keypoints, dict_list_Timestamps, dict_det_keypoints


def check_cuboid_subclass_confidence(df, camera, eval_frame, dict_list_keypoints, test):
    """Checks Validity of Cuboid Subclass Confidence"""
    # captures validity of subclass confidence of each detected cuboid
    dict_obj_subclass_confidence = {}
    dict_det_subclass_confidence = {}
    dict_list_subclass_timestamps = []
    for _, row in df.iterrows():
        num_cuboid_detection = int(row[f"num_cuboid_detections_{camera}"])
        timestamp = int(row[f"detection_results_timestamp_{camera}"])
        if timestamp in eval_frame.valid_timestamps_in_camera[camera]:
            for det in range(0, num_cuboid_detection):
                dict_det_subclass_confidence[f"frame{timestamp}_det{det}"] = True
                if (eval_frame.valid_detections_in_camera[camera][f"{timestamp}_{det}"]) is True:
                    if dict_list_keypoints[f"frame{timestamp}_det{det}"] is True:
                        for conf in range(0, 3):  # cuboid detections have 3 subclasses
                            subclass_conf = row[f"cuboid_detections_subclass_confidence_of_{camera}_det_{det}", conf]
                            if subclass_conf >= 0 and subclass_conf <= 1:
                                dict_obj_subclass_confidence[f"frame{timestamp}_det{det}_conf_{conf}"] = True
                            else:
                                dict_obj_subclass_confidence[f"frame{timestamp}_det{det}_conf_{conf}"] = False
                                dict_list_subclass_timestamps.append(timestamp)
                                dict_det_subclass_confidence[f"frame{timestamp}_det{det}"] = False
            dict_list_subclass_timestamps = list(dict.fromkeys(dict_list_subclass_timestamps))
    if test == "subclass":
        if any(ele is True for ele in dict_det_subclass_confidence.values()):
            validity_of_subclass = True
        else:
            validity_of_subclass = False
    else:
        if all(ele is True for ele in dict_det_subclass_confidence.values()):
            validity_of_subclass = True
        else:
            validity_of_subclass = False
    return validity_of_subclass, dict_list_subclass_timestamps, dict_det_subclass_confidence


def valid_cuboid_subclass(df, cam, eval_frame, dict_list_keypoints, dict_det_subclass_confidence):
    """Checks for the valid cuboid subclass"""
    invalid_subclass_timestamps = []
    dict_obj_subclass = {}
    for _, row in df.iterrows():
        # num_cuboid_detection = int(row[ft.PCESignals.Columns.NUM_CUBOID_DETECTIONS])
        num_cuboid_detection = int(row[f"num_cuboid_detections_{cam}"])
        timestamp = int(row[f"detection_results_timestamp_{cam}"])
        if timestamp in eval_frame.valid_timestamps_in_camera[cam]:
            # checks whether the component has provided the most confident subclass
            for det in range(0, num_cuboid_detection):
                if (eval_frame.valid_detections_in_camera[cam][f"{timestamp}_{det}"]) is True:
                    if (
                        dict_list_keypoints[f"frame{timestamp}_det{det}"] is True
                        and dict_det_subclass_confidence[f"frame{timestamp}_det{det}"] is True
                    ):
                        # holds the subclass confidences for all the cuboid detection
                        dict_sub_class_conf = {}
                        # holds the subclass confidence for all the classes of each detection
                        sub_class_conf_frame = []
                        for conf in range(0, 3):
                            subclass_conf = row[f"cuboid_detections_subclass_confidence_of_{cam}_det_{det}", conf]
                            dict_sub_class_conf[f"timestamp{timestamp}_det{det}_conf{conf}"] = subclass_conf
                            sub_class_conf_frame.append(subclass_conf)
                        # maximum of subclass confidences
                        cuboid_subclass_max_confidence = max(dict_sub_class_conf.values())
                        cuboid_subclass_id = sub_class_conf_frame.index(cuboid_subclass_max_confidence)
                        # check if most confident subclass id is assigned to the detection.
                        if cuboid_subclass_id == int(row[f"cuboid_detections_subclass_id_of_{cam}_det_{det}"]):
                            # if most confident subclass is provided
                            dict_obj_subclass[f"obj_{timestamp}_det_{det}"] = True
                        else:
                            # if most confident subclass is not provided
                            dict_obj_subclass[f"obj_{timestamp}_det_{det}"] = False
                            invalid_subclass_timestamps.append(timestamp)
            invalid_subclass_timestamps = list(dict.fromkeys(invalid_subclass_timestamps))

    return dict_obj_subclass, invalid_subclass_timestamps


def valid_bounding_box_subclass(df, cam, eval_frame, dict_list_keypoints, dict_det_subclass_confidence):
    """Checks for the valid bounding box subclass"""
    invalid_subclass_timestamps = []
    dict_obj_subclass = {}
    for _, row in df.iterrows():
        # num_cuboid_detection = int(row[ft.PCESignals.Columns.NUM_CUBOID_DETECTIONS])
        num_bounding_box_detection = int(row[f"num_bounding_box_detections_{cam}"])
        timestamp = int(row[f"detection_results_timestamp_{cam}"])
        if timestamp in eval_frame.valid_timestamps_in_camera[cam]:
            # checks whether the component has provided the most confident subclass
            for det in range(0, num_bounding_box_detection):
                if (eval_frame.valid_detections_in_camera[cam][f"{timestamp}_{det}"]) is True:
                    if (
                        dict_list_keypoints[f"frame{timestamp}_det{det}"] is True
                        and dict_det_subclass_confidence[f"frame{timestamp}_det{det}"] is True
                    ):
                        # holds the subclass confidences for all the cuboid detection
                        dict_sub_class_conf = {}
                        # holds the subclass confidence for all the classes of each detection
                        sub_class_conf_frame = []
                        for conf in range(0, 6):
                            subclass_conf = row[f"bounding_box_detections_subclass_confidence_of_{cam}_det_{det}", conf]
                            dict_sub_class_conf[f"timestamp{timestamp}_det{det}_conf{conf}"] = subclass_conf
                            sub_class_conf_frame.append(subclass_conf)
                        # maximum of subclass confidences
                        bounding_subclass_max_confidence = max(dict_sub_class_conf.values())
                        bounding_box_subclass_id = sub_class_conf_frame.index(bounding_subclass_max_confidence)
                        # check if most confident subclass id is assigned to the detection.
                        if bounding_box_subclass_id == int(
                            row[f"bounding_box_detections_subclass_id_of_{cam}_det_{det}"]
                        ):
                            # if most confident subclass is provided
                            dict_obj_subclass[f"obj_{timestamp}_det_{det}"] = True
                        else:
                            # if most confident subclass is not provided
                            dict_obj_subclass[f"obj_{timestamp}_det_{det}"] = False
                            invalid_subclass_timestamps.append(timestamp)
            invalid_subclass_timestamps = list(dict.fromkeys(invalid_subclass_timestamps))

    return dict_obj_subclass, invalid_subclass_timestamps


def valid_poly_subclass(df, cam, eval_frame, dict_list_keypoints, dict_det_subclass_confidence):
    """Checks for the valid poly subclass"""
    invalid_subclass_timestamps = []
    dict_obj_subclass = {}
    for _, row in df.iterrows():
        num_parking_slot_detection = int(row[f"num_parking_slot_detections_{cam}"])
        timestamp = int(row[f"detection_results_timestamp_{cam}"])
        if timestamp in eval_frame.valid_timestamps_in_camera[cam]:
            # checks whether the component has provided the most confident subclass
            for det in range(0, num_parking_slot_detection):
                if (eval_frame.valid_detections_in_camera[cam][f"{timestamp}_{det}"]) is True:
                    if (
                        dict_list_keypoints[f"frame{timestamp}_det{det}"] is True
                        and dict_det_subclass_confidence[f"frame{timestamp}_det{det}"] is True
                    ):
                        dict_sub_class_conf = {}  # holds the subclass confidences for all the parking slot detection
                        list_sub_class_conf_each_frame = []
                        for conf in range(0, 3):
                            subclass_conf = row[f"parking_slot_subclass_confidence_of_{cam}_det_{det}", conf]
                            dict_sub_class_conf[f"timestamp{timestamp}_det{det}_conf{conf}"] = subclass_conf
                            list_sub_class_conf_each_frame.append(subclass_conf)
                        # maximum of subclass confidences
                        maximum_subclass_confidence = max(dict_sub_class_conf.values())
                        # index of maximum confidence subclass
                        parking_slot_subclass_id = list_sub_class_conf_each_frame.index(maximum_subclass_confidence)
                        # compares the subclass with the actual subclass
                        if parking_slot_subclass_id == int(row[f"parking_slot_subclass_id_of_{cam}_det_{det}"]):
                            # if most confident subclass is provided
                            dict_obj_subclass[f"obj_{timestamp}_det_{det}"] = True
                        else:
                            # if most confident subclass is provided
                            dict_obj_subclass[f"obj_{timestamp}_det_{det}"] = False
                            invalid_subclass_timestamps.append(timestamp)
            invalid_subclass_timestamps = list(dict.fromkeys(invalid_subclass_timestamps))

    return dict_obj_subclass, invalid_subclass_timestamps


def check_validity_of_bounding_box_keypoints(df, camera, eval_frame):
    """Checks Validity of bounding box keypoints"""
    dict_list_keypoints = []
    dict_obj_keypoints = {}
    dict_det_keypoints = {}
    dict_list_Timestamps = []
    for _, row in df.iterrows():
        num_bounding_box_detection = int(row[f"num_bounding_box_detections_{camera}"])
        timestamp = int(row[f"detection_results_timestamp_{camera}"])
        if timestamp in eval_frame.valid_timestamps_in_camera[camera]:
            for det in range(0, num_bounding_box_detection):
                if eval_frame.valid_detections_in_camera[camera][f"{timestamp}_{det}"]:
                    dict_det_keypoints[f"frame{timestamp}_det{det}"] = True
                    for keypoint in range(0, 2):  # bounding box detections have 2 keypoints
                        keypoints_bounding_box_x = row[
                            f"bounding_box_detections_key_points_x_of_{camera}_det_{det}_keypoint_{keypoint}"
                        ]
                        keypoints_bounding_box_y = row[
                            f"bounding_box_detections_key_points_y_of_{camera}_det_{det}_keypoint_{keypoint}"
                        ]
                        if keypoints_bounding_box_x > 0 and keypoints_bounding_box_y > 0:
                            dict_obj_keypoints[f"frame{timestamp}_det{det}_keypoint{keypoint}"] = True
                        else:
                            dict_obj_keypoints[f"frame{timestamp}_det{det}_keypoint{keypoint}"] = False
                            dict_list_Timestamps.append(timestamp)
                            dict_det_keypoints[f"frame{timestamp}_det{det}"] = False
            dict_list_Timestamps = list(dict.fromkeys(dict_list_Timestamps))
    dict_list_keypoints.append(dict_obj_keypoints)

    if any(ele is True for ele in dict_det_keypoints.values()):
        validity_of_keypoints = True
    else:
        validity_of_keypoints = False

    return validity_of_keypoints, dict_list_Timestamps, dict_det_keypoints


def check_bounding_box_subclass_confidence(df, camera, eval_frame, dict_list_keypoints, test_type):
    """Checks Validity of bounding box Subclass Confidence"""
    # captures validity of subclass confidence of each detected bounding box
    dict_list_subclass_timestamps = []
    dict_obj_subclass_confidence = {}
    dict_det_subclass_confidence = {}
    for _, row in df.iterrows():
        num_bounding_box_detection = int(row[f"num_bounding_box_detections_{camera}"])
        timestamp = int(row[f"detection_results_timestamp_{camera}"])
        if timestamp in eval_frame.valid_timestamps_in_camera[camera]:
            for det in range(0, int(num_bounding_box_detection)):
                if (eval_frame.valid_detections_in_camera[camera][f"{timestamp}_{det}"]) is True:
                    if dict_list_keypoints[f"frame{timestamp}_det{det}"] is True:
                        dict_det_subclass_confidence[f"frame{timestamp}_det{det}"] = True
                        for conf in range(0, 6):
                            subclass_conf = row[
                                f"bounding_box_detections_subclass_confidence_of_{camera}_det_{det}", conf
                            ]
                            if subclass_conf >= 0 and subclass_conf <= 1:  # bounding box detections have 6 subclasses
                                dict_obj_subclass_confidence[f"frame{timestamp}_det{det}_conf_{conf}"] = True
                            else:
                                dict_obj_subclass_confidence[f"frame{timestamp}_det{det}_conf_{conf}"] = False
                                dict_det_subclass_confidence[f"frame{timestamp}_det{det}"] = False
                                dict_list_subclass_timestamps.append(timestamp)
            dict_list_subclass_timestamps = list(dict.fromkeys(dict_list_subclass_timestamps))
    if test_type == "subclass":
        if any(ele is True for ele in dict_det_subclass_confidence.values()):
            validity_of_subclass = True
        else:
            validity_of_subclass = False
    else:
        if all(ele is True for ele in dict_det_subclass_confidence.values()):
            validity_of_subclass = True
        else:
            validity_of_subclass = False

    return validity_of_subclass, dict_list_subclass_timestamps, dict_det_subclass_confidence


def check_validity_of_parking_slot_keypoints(df, camera, eval_frame):
    """Checks Validity of parking slot keypoints"""
    dict_list_keypoints = []
    dict_obj_keypoints = {}
    dict_det_keypoints = {}
    dict_list_Timestamps = []
    for _, row in df.iterrows():
        num_parking_slot_detection = int(row[f"num_parking_slot_detections_{camera}"])
        timestamp = int(row[f"detection_results_timestamp_{camera}"])
        if timestamp in eval_frame.valid_timestamps_in_camera[camera]:
            for det in range(0, num_parking_slot_detection):
                if eval_frame.valid_detections_in_camera[camera][f"{timestamp}_{det}"]:
                    dict_det_keypoints[f"frame{timestamp}_det{det}"] = True
                    for keypoint in range(0, 4):  # parking slot detections have 4 keypoints
                        keypoints_parking_x = row[
                            f"parking_slot_key_points_x_of_{camera}_det_{det}_keypoint_{keypoint}"
                        ]
                        keypoints_parking_y = row[
                            f"parking_slot_key_points_y_of_{camera}_det_{det}_keypoint_{keypoint}"
                        ]
                        if keypoints_parking_x > 0 and keypoints_parking_y > 0:
                            dict_obj_keypoints[f"frame{timestamp}_det{det}_keypoint{keypoint}"] = True
                        else:
                            dict_obj_keypoints[f"frame{timestamp}_det{det}_keypoint{keypoint}"] = False
                            dict_list_Timestamps.append(timestamp)
                            dict_det_keypoints[f"frame{timestamp}_det{det}"] = False
            dict_list_Timestamps = list(dict.fromkeys(dict_list_Timestamps))
    dict_list_keypoints.append(dict_obj_keypoints)

    if any(ele is True for ele in dict_det_keypoints.values()):
        validity_of_keypoints = True
    else:
        validity_of_keypoints = False

    return validity_of_keypoints, dict_list_Timestamps, dict_det_keypoints


def check_parking_slot_orientation_confidence(df, camera, eval_frame, dict_list_keypoints):
    """Checks Validity of bounding box Subclass Confidence"""
    # captures validity of orientation confidence of each detected parking slot
    dict_obj_orientation_confidence = {}
    invalid_orientation_conf_timestamps = []
    for _, row in df.iterrows():
        num_parking_slot_detection = int(row[f"num_parking_slot_detections_{camera}"])
        timestamp = int(row[f"detection_results_timestamp_{camera}"])
        if timestamp in eval_frame.valid_timestamps_in_camera[camera]:
            for det in range(0, num_parking_slot_detection):
                if eval_frame.valid_detections_in_camera[camera][f"{timestamp}_{det}"]:
                    if dict_list_keypoints[f"frame{timestamp}_det{det}"] is True:
                        for conf in range(0, 3):
                            orientation_conf = row[f"parking_orientation_confidence_{camera}_det_{det}", conf]
                            if orientation_conf >= 0 and orientation_conf <= 1:
                                dict_obj_orientation_confidence[f"obj_{timestamp}_det_{det}"] = True
                            else:
                                dict_obj_orientation_confidence[f"obj_{timestamp}_det_{det}"] = False
                                invalid_orientation_conf_timestamps.append(timestamp)
    invalid_orientation_conf_timestamps = list(dict.fromkeys(invalid_orientation_conf_timestamps))

    if all(ele is True for ele in dict_obj_orientation_confidence.values()):
        valid_orientation_confidence = True
    else:
        valid_orientation_confidence = False

    return valid_orientation_confidence, invalid_orientation_conf_timestamps


def check_parking_slot_occlusion_confidence(df, camera, eval_frame, dict_list_keypoints):
    """Checks Validity of bounding box Subclass Confidence"""
    # captures validity of visbility confidence of each detected parking slot
    invalid_occlusion_conf_timestamps = []
    dict_obj_visibility_confidence = {}
    for _, row in df.iterrows():
        num_parking_slot_detection = int(row[f"num_parking_slot_detections_{camera}"])
        timestamp = int(row[f"detection_results_timestamp_{camera}"])
        if timestamp in eval_frame.valid_timestamps_in_camera[camera]:
            for det in range(0, num_parking_slot_detection):
                if eval_frame.valid_detections_in_camera[camera][f"{timestamp}_{det}"]:
                    if dict_list_keypoints[f"frame{timestamp}_det{det}"] is True:
                        for conf in range(0, 4):
                            visibility_conf = row[f"parking_occlusion_confidence_{camera}_det_{det}", conf]
                            if visibility_conf >= 0 and visibility_conf <= 1:
                                dict_obj_visibility_confidence[f"obj_{timestamp}_det_{det}"] = True
                            else:
                                dict_obj_visibility_confidence[f"obj_{timestamp}_det_{det}"] = False
                                invalid_occlusion_conf_timestamps.append(timestamp)
    invalid_occlusion_conf_timestamps = list(dict.fromkeys(invalid_occlusion_conf_timestamps))

    if all(ele is True for ele in dict_obj_visibility_confidence.values()):
        valid_occlusion_confidence = True
    else:
        valid_occlusion_confidence = False

    return valid_occlusion_confidence, invalid_occlusion_conf_timestamps


def check_parking_slot_subclass_confidence(df, camera, eval_frame, dict_list_keypoints, test_type):
    """Checks Validity of parking slot Subclass Confidence"""
    # captures validity of subclass confidence of each detected parking slot
    dict_obj_subclass_confidence = {}
    dict_det_subclass_confidence = {}
    invalid_subclass_conf_timestamps = []
    for _, row in df.iterrows():
        num_parking_slot_detection = int(row[f"num_parking_slot_detections_{camera}"])
        timestamp = int(row[f"detection_results_timestamp_{camera}"])
        if timestamp in eval_frame.valid_timestamps_in_camera[camera]:
            # checks the validity of subclass confidence of each detected parking slot
            for det in range(0, num_parking_slot_detection):
                dict_det_subclass_confidence[f"frame{timestamp}_det{det}"] = True
                if (eval_frame.valid_detections_in_camera[camera][f"{timestamp}_{det}"]) is True:
                    if dict_list_keypoints[f"frame{timestamp}_det{det}"] is True:
                        for conf in range(0, 3):
                            subclass_conf = row[f"parking_slot_subclass_confidence_of_{camera}_det_{det}", conf]
                            if subclass_conf >= 0 and subclass_conf <= 1:
                                dict_obj_subclass_confidence[f"frame{timestamp}_det{det}_conf_{conf}"] = True
                            else:
                                dict_obj_subclass_confidence[f"frame{timestamp}_det{det}_conf_{conf}"] = False
                                invalid_subclass_conf_timestamps.append(timestamp)
                                dict_det_subclass_confidence[f"frame{timestamp}_det{det}"] = False
    invalid_subclass_conf_timestamps = list(dict.fromkeys(invalid_subclass_conf_timestamps))
    if test_type == "subclass":
        if any(ele is True for ele in dict_det_subclass_confidence.values()):
            validity_of_subclass = True
        else:
            validity_of_subclass = False
    else:
        if all(ele is True for ele in dict_det_subclass_confidence.values()):
            validity_of_subclass = True
        else:
            validity_of_subclass = False

    return validity_of_subclass, invalid_subclass_conf_timestamps, dict_det_subclass_confidence


def check_data_input_sensor_source_information_fc(df):
    """Checks Validity of FC sensor source information of data inputs"""
    # captures the sensor source information of data inputs
    valid_sensor_source_fc = []
    for _, row in df.iterrows():
        #  Read sensor source information from its relevant data inputs.
        data_input_yp1_sensorsource_fc = int(row[PCESignals.Columns.ODDYP1_SENSORSOURCE_FC])
        data_input_uvp1_sensorsource_fc = int(row[PCESignals.Columns.ODDUVP1_SENSORSOURCE_FC])
        data_input_parameters_sensorsource_fc = int(row[PCESignals.Columns.PARAMETERS_SENSORSOURCE_FC])
        # checks the validity of sensor source information of data inputs
        if data_input_yp1_sensorsource_fc == data_input_uvp1_sensorsource_fc == data_input_parameters_sensorsource_fc:
            valid_sensor_source_fc.append(True)
        else:
            valid_sensor_source_fc.append(False)
    if all(valid_sensor_source_fc):
        return True
    else:
        return False


def check_data_input_sensor_source_information_rc(df):
    """Checks Validity of RC sensor source information of data inputs"""
    # captures the sensor source information of data inputs
    valid_sensor_source_rc = []
    for _, row in df.iterrows():
        #  Read sensor source information from its relevant data inputs.
        data_input_yp1_sensorsource_rc = int(row[PCESignals.Columns.ODDYP1_SENSORSOURCE_RC])
        data_input_uvp1_sensorsource_rc = int(row[PCESignals.Columns.ODDUVP1_SENSORSOURCE_RC])
        data_input_parameters_sensorsource_rc = int(row[PCESignals.Columns.PARAMETERS_SENSORSOURCE_RC])
        # checks the validity of sensor source information of data inputs
        if data_input_yp1_sensorsource_rc == data_input_uvp1_sensorsource_rc == data_input_parameters_sensorsource_rc:
            valid_sensor_source_rc.append(True)
        else:
            valid_sensor_source_rc.append(False)
    if all(valid_sensor_source_rc):
        return True
    else:
        return False


def check_data_input_sensor_source_information_rsc(df):
    """Checks Validity of RSC sensor source information of data inputs"""
    # captures the sensor source information of data inputs
    valid_sensor_source_rsc = []
    for _, row in df.iterrows():
        #  Read sensor source information from its relevant data inputs.
        data_input_yp1_sensorsource_rsc = int(row[PCESignals.Columns.ODDYP1_SENSORSOURCE_RSC])
        data_input_uvp1_sensorsource_rsc = int(row[PCESignals.Columns.ODDUVP1_SENSORSOURCE_RSC])
        data_input_parameters_sensorsource_rsc = int(row[PCESignals.Columns.PARAMETERS_SENSORSOURCE_RSC])
        # checks the validity of sensor source information of data inputs
        if (
            data_input_yp1_sensorsource_rsc
            == data_input_uvp1_sensorsource_rsc
            == data_input_parameters_sensorsource_rsc
        ):
            valid_sensor_source_rsc.append(True)
        else:
            valid_sensor_source_rsc.append(False)
    if all(valid_sensor_source_rsc):
        return True
    else:
        return False


def check_data_input_sensor_source_information_lsc(df):
    """Checks Validity of LSC sensor source information of data inputs"""
    # captures the sensor source information of data inputs
    valid_sensor_source_lsc = []
    for _, row in df.iterrows():
        #  Read sensor source information from its relevant data inputs.
        data_input_yp1_sensorsource_lsc = int(row[PCESignals.Columns.ODDYP1_SENSORSOURCE_LSC])
        data_input_uvp1_sensorsource_lsc = int(row[PCESignals.Columns.ODDUVP1_SENSORSOURCE_LSC])
        data_input_parameters_sensorsource_lsc = int(row[PCESignals.Columns.PARAMETERS_SENSORSOURCE_LSC])
        # checks the validity of sensor source information of data inputs
        if (
            data_input_yp1_sensorsource_lsc
            == data_input_uvp1_sensorsource_lsc
            == data_input_parameters_sensorsource_lsc
        ):
            valid_sensor_source_lsc.append(True)
        else:
            valid_sensor_source_lsc.append(False)
    if all(valid_sensor_source_lsc):
        return True
    else:
        return False


def check_data_input_timestamp(df, camera):
    """Checks Validity of timestamp of data inputs"""
    # Checks Validity of timestamp of data inputs
    df_chips_input = df.assign(NE=df[f"ChipsY_Timestamp_{camera}"] == df[f"ChipsUV_Timestamp_{camera}"])
    # add another column to df_chips_input with validity using valid_status
    valid_status = {False: "InValid", True: "Valid"}
    df_chips_input["validity"] = df_chips_input["NE"].replace(valid_status)
    # Filter the df for Invalid data(where the ChipsY_Timestamp != ChipsUV_Timestamp)
    df_chips_invalid = df_chips_input[(df_chips_input["validity"] == "InValid")]

    return df_chips_invalid


def check_detection_results_timestamp(df, camera):
    """Checks if data output(det_result) timestamps is matched to data inputs(Chips data)"""
    df_od_timestamps = df[["mts_ts", f"detection_results_timestamp_{camera}", f"ChipsY_Timestamp_{camera}"]].assign(
        NE=df[f"detection_results_timestamp_{camera}"] == df[f"ChipsY_Timestamp_{camera}"]
    )
    # add another column to df_chips_input with validity using valid_status
    valid_status = {False: "InValid", True: "Valid"}
    df_od_timestamps["validity"] = df_od_timestamps["NE"].replace(valid_status)
    # Filter the df for Invalid data(where the detection_results_timestamp != ChipsY_Timestamp)
    df_invalid_od_timestamps = df_od_timestamps[(df_od_timestamps["validity"] == "InValid")]

    return df_invalid_od_timestamps


def check_semseg_results_timestamp(df, camera):
    """Checks if data output(semseg) timestamps is matched to data inputs(Chips data)"""
    df_semseg_timestamps = df[["mts_ts", f"semseg_timestamp_{camera}", f"ChipsY_Timestamp_{camera}"]].assign(
        NE=df[f"semseg_timestamp_{camera}"] == df[f"ChipsY_Timestamp_{camera}"]
    )
    # add another column to df_chips_input with validity using valid_status
    valid_status = {False: "InValid", True: "Valid"}
    df_semseg_timestamps["validity"] = df_semseg_timestamps["NE"].replace(valid_status)
    # Filter the df for Invalid data(where the semseg_timestamp != ChipsY_Timestamp)
    df_invalid_sem_timestamps = df_semseg_timestamps[(df_semseg_timestamps["validity"] == "InValid")]

    return df_invalid_sem_timestamps


def check_required_signals(dict_signal_check, df):
    """Checks the availabilty of the signals"""
    signal_availability = True
    list_of_missing_signals = []

    for signal in dict_signal_check:
        if signal not in df:
            signal_availability = False
            list_of_missing_signals.append(signal)
    return signal_availability, list_of_missing_signals


def signals_to_be_plotted(df, camera, output_type):
    """List the signal to plot"""
    if output_type == "semseg":
        df_filtered = df[
            [
                f"semseg_sig_status_{camera}",
                f"Chipsy_focalx_{camera}",
                f"Chipsuv_focalx_{camera}",
                f"Chipsy_focaly_{camera}",
                f"Chipsuv_focaly_{camera}",
                f"Chipsy_Centerx_{camera}",
                f"Chipsuv_Centerx_{camera}",
                f"Chipsy_Centery_{camera}",
                f"Chipsuv_Centery_{camera}",
                f"Chipsy_CameraType_{camera}",
                f"Chipsuv_CameraType_{camera}",
                f"SemSeg_FOCALX_{camera}",
                f"SemSeg_FOCALY_{camera}",
                f"SemSeg_CenterX_{camera}",
                f"SemSeg_CenterY_{camera}",
                f"SemSeg_CameraType_{camera}",
                f"ChipsY_Sigstatus_{camera}",
                f"ChipsUV_Sigstatus_{camera}",
                f"Base_ctrl_opmode_{camera}",
            ]
        ]
    else:
        df_filtered = df[
            [
                f"detection_results_sig_status_{camera}",
                f"Chipsy_focalx_{camera}",
                f"Chipsuv_focalx_{camera}",
                f"Chipsy_focaly_{camera}",
                f"Chipsuv_focaly_{camera}",
                f"Chipsy_Centerx_{camera}",
                f"Chipsuv_Centerx_{camera}",
                f"Chipsy_Centery_{camera}",
                f"Chipsuv_Centery_{camera}",
                f"Chipsy_CameraType_{camera}",
                f"Chipsuv_CameraType_{camera}",
                f"Detection_Results_FOCALX_{camera}",
                f"Detection_Results_FOCALY_{camera}",
                f"Detection_Results_CenterX_{camera}",
                f"Detection_Results_CenterY_{camera}",
                f"Detection_Results_CameraType_{camera}",
                f"ChipsY_Sigstatus_{camera}",
                f"ChipsUV_Sigstatus_{camera}",
                f"Base_ctrl_opmode_{camera}",
            ]
        ]
    return df_filtered
