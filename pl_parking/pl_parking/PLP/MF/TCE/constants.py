"""In constants.py file contains the signal names"""

from dataclasses import dataclass


@dataclass
class CarMakerUrl:
    """This class contains Carmaker recordings signals URLs"""

    time: str = "Time"
    tceDebugPortTs: str = "AP.tceDebugPort.sSigHeader.uiTimeStamp"
    tceEstimatePortTs: str = "AP.tceEstimationPort.sSigHeader.uiTimeStamp"
    estTyreCircFL: str = "AP.tceEstimationPort.tireCircFL_m"
    refTyreCircFL: str = "AP.tceDebugPort.tireCircInternalFL_m"
    estTyreCircFR: str = "AP.tceEstimationPort.tireCircFR_m"
    refTyreCircFR: str = "AP.tceDebugPort.tireCircInternalFR_m"
    estTyreCircRL: str = "AP.tceEstimationPort.tireCircRL_m"
    refTyreCircRL: str = "AP.tceDebugPort.tireCircInternalRL_m"
    estTyreCircRR: str = "AP.tceEstimationPort.tireCircRR_m"
    refTyreCircRR: str = "AP.tceDebugPort.tireCircInternalRR_m"
    estTyreCircStdvFL: str = "AP.tceEstimationPort.tireCircStdvFL_m"
    estTyreCircStdvFR: str = "AP.tceEstimationPort.tireCircStdvFR_m"
    estTyreCircStdvRL: str = "AP.tceEstimationPort.tireCircStdvRL_m"
    estTyreCircStdvRR: str = "AP.tceEstimationPort.tireCircStdvRR_m"
    estRearTrackWidth: str = "AP.tceEstimationPort.rearTrackWidth_m"
    estRearTrackWidthStdv: str = "AP.tceEstimationPort.rearTrackWidthStdv_m"
    estRearTrackWidthValid: str = "AP.tceEstimationPort.rearTrackWidthValid"
    estTyreCircFLValid: str = "AP.tceEstimationPort.tireCircFLValid"
    estTyreCircFRValid: str = "AP.tceEstimationPort.tireCircFRValid"
    estTyreCircRLValid: str = "AP.tceEstimationPort.tireCircRLValid"
    estTyreCircRRValid: str = "AP.tceEstimationPort.tireCircRRValid"
    tireCircFL_0p1: str = "AP.tcePersDataPort.tireCircFL_0p1mm"
    tireCircFR_0p1: str = "AP.tcePersDataPort.tireCircFR_0p1mm"
    tireCircRL_0p1: str = "AP.tcePersDataPort.tireCircRL_0p1mm"
    tireCircRR_0p1: str = "AP.tcePersDataPort.tireCircRR_0p1mm"
    tireCircStdvFL_0p1: str = "AP.tcePersDataPort.tireCircStdvFL_0p1mm"
    tireCircStdvFR_0p1: str = "AP.tcePersDataPort.tireCircStdvFR_0p1mm"
    tireCircStdvRL_0p1: str = "AP.tcePersDataPort.tireCircStdvRL_0p1mm"
    tireCircStdvRR_0p1: str = "AP.tcePersDataPort.tireCircStdvRR_0p1mm"
    positionDOP: str = "odoGpsPort.gpsData.positionDOP"


@dataclass
class UnitConversion:
    """This class contains unit conversion formulas"""

    microsecondsToSeconds: float = 1 / 1_000_000
    kphToMps: float = 1 / 3.6
    mpsToKph: float = 3.6
    millisecondsToSeconds: float = 1 / 1000


@dataclass
class TceConstantValues:
    """This class contains TCE Constant values"""

    TCE_MIN_TYRE_CIRCUMFERENCE_M: float = 2.01488
    TCE_MAX_TYRE_CIRCUMFERENCE_M: float = 2.09712
    TCE_TYRE_RANGE = [TCE_MIN_TYRE_CIRCUMFERENCE_M, TCE_MAX_TYRE_CIRCUMFERENCE_M]
    TCE_MIN_TYRE_CIRCUMFERENCE_STDV_M: float = 0
    TCE_MAX_TYRE_CIRCUMFERENCE_STDV_M: float = 0.01
    TCE_TYRE_STDV_RANGE = [TCE_MIN_TYRE_CIRCUMFERENCE_STDV_M, TCE_MAX_TYRE_CIRCUMFERENCE_STDV_M]
    TCE_MIN_TYRE_CIRCUMFERENCE_PERS_DATA_MM: float = 2014.88
    TCE_MAX_TYRE_CIRCUMFERENCE_PERS_DATA_MM: float = 2097.12
    TCE_TYRE_PERS_DATA_RANGE = [TCE_MIN_TYRE_CIRCUMFERENCE_PERS_DATA_MM, TCE_MAX_TYRE_CIRCUMFERENCE_PERS_DATA_MM]
    TCE_MIN_TYRE_CIRCUMFERENCE_PERS_DATA_STDV_MM: float = 0.0
    TCE_MAX_TYRE_CIRCUMFERENCE_PERS_DATA_STDV_MM: float = 0.01
    TCE_TYRE_PERS_DATA_STDV_RANGE = [
        TCE_MIN_TYRE_CIRCUMFERENCE_PERS_DATA_STDV_MM,
        TCE_MAX_TYRE_CIRCUMFERENCE_PERS_DATA_STDV_MM,
    ]
    TCE_TYRE_CIRCUMFERENCE_FR_M: float = 2.032
    TCE_TYRE_CIRCUMFERENCE_RE_M: float = 2.032
