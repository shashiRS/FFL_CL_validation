"""ws helper module for CEM"""

from pl_parking.PLP.CEM.inputs.input_CemPclReader import PCLDelimiter, PCLPoint


class FtWsHelper:
    """Helper class for WS operations."""

    @staticmethod
    def get_ws_from_json_gt(gt_data):
        """Get WS from JSON ground truth data."""
        line_gt_output = dict()
        lines_all_ts = gt_data["WheelStopper"]["StreamData"]

        for _, lines in enumerate(lines_all_ts):
            ts_lines = lines["Timestamp"]
            line_gt_output[ts_lines] = list()

            for line in lines["TimedObjectData"]:
                line_out = PCLDelimiter(
                    0,
                    2,
                    PCLPoint(
                        line["StaticObject"]["pointContainer"]["points"][0][0],
                        line["StaticObject"]["pointContainer"]["points"][0][1],
                    ),
                    PCLPoint(
                        line["StaticObject"]["pointContainer"]["points"][1][0],
                        line["StaticObject"]["pointContainer"]["points"][1][1],
                    ),
                    100,
                )
                line_gt_output[ts_lines].append(line_out)

        return line_gt_output
