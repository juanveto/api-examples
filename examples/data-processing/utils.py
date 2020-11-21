def setup_fs(s3, key="", secret="", endpoint="", cert=""):
    """Given a boolean specifying whether to use local disk or S3, setup filesystem
    """

    if s3:
        import s3fs

        if "amazonaws" in endpoint:
            fs = s3fs.S3FileSystem(key=key, secret=secret)
        elif cert != "":
            fs = s3fs.S3FileSystem(key=key, secret=secret, client_kwargs={"endpoint_url": endpoint, "verify": cert})
        else:
            fs = s3fs.S3FileSystem(key=key, secret=secret, client_kwargs={"endpoint_url": endpoint},)

    else:
        from pathlib import Path
        import canedge_browser

        base_path = Path(__file__).parent
        fs = canedge_browser.LocalFileSystem(base_path=base_path)

    return fs


def custom_sig(df, signal1, signal2, function, new_signal):
    """Helper function for calculating a new signal based on two signals and a function.
    Returns a dataframe with the new signal name and physical values
    """
    import pandas as pd

    try:
        s1 = df[df["Signal"] == signal1]["Physical Value"].rename(signal1)
        s2 = df[df["Signal"] == signal2]["Physical Value"].rename(signal2)

        df_new_sig = pd.merge_ordered(s1, s2, on="TimeStamp", fill_method="ffill",).set_index("TimeStamp")

        df_new_sig = df_new_sig.apply(lambda x: function(x[0], x[1]), axis=1).dropna().rename("Physical Value").to_frame()

        df_new_sig["Signal"] = new_signal

        return df_new_sig

    except:
        print(f"Warning: Custom signal {new_signal} not created\n")
        return pd.DataFrame()


class MultiFrameDecoder:
    """BETA class for handling transport protocol data. For each response ID, identify
    sequences of subsequent frames and combine the relevant parts of the data payloads
    into a single payload with the response ID as the ID. The original raw dataframe is
    then cleansed of the original response ID sequence frames. Instead, the new concatenated
    frames are inserted. Further, the class supports DBC decoding of the resulting modified raw data

    :param df_raw:                      dataframe of raw CAN data from the mdf_iter module
    :param res_id_list_hex:             list of transport protocol 'response CAN IDs' to process
    :param SINGLE_FRAME_MASK:           mask used in matching single frames
    :param FIRST_FRAME_MASK:            mask used in matching first frames
    :param CONSEQ_FRAME_MASK:           mask used in matching consequtive frames
    :param SINGLE_FRAME:                frame type reflecting a single frame response
    :param FIRST_FRAME:                 frame type reflecting the first frame in a multi frame response
    :param CONSEQ_FRAME:                frame type reflecting a consequtive frame in a multi frame response
    :param first_frame_payload_start:   the combined payload will start at this byte in the FIRST_FRAME
    :param bam_id_hex:                  used in e.g. J1939, this marks the initial BAM message ID in HEX
    """

    def __init__(self, df_raw, res_id_list_hex):
        self.df_raw = df_raw
        self.res_id_list_hex = res_id_list_hex
        self.res_id_list = [int(res_id, 16) for res_id in self.res_id_list_hex]

        return

    def construct_new_tp_frame(self, base_frame, payload_concatenated, can_id):
        new_frame = base_frame
        new_frame.at["DataBytes"] = payload_concatenated
        new_frame.at["DLC"] = 0
        new_frame.at["DataLength"] = len(payload_concatenated)

        if can_id:
            new_frame.at["ID"] = can_id

        return new_frame

    def combine_tp_frames(
        self,
        SINGLE_FRAME_MASK,
        FIRST_FRAME_MASK,
        CONSEQ_FRAME_MASK,
        SINGLE_FRAME,
        FIRST_FRAME,
        CONSEQ_FRAME,
        first_frame_payload_start,
        conseq_frame_payload_start,
        bam_id_hex="",
    ):
        import pandas as pd

        df_raw_combined = pd.DataFrame()

        for channel, df_raw in self.df_raw.groupby("BusChannel"):

            for res_id in self.res_id_list:
                # filter raw data for response ID and extract a 'base frame'
                if bam_id_hex == "":
                    bam_id = 0
                else:
                    bam_id = int(bam_id_hex, 16)

                df_raw_filter = self.df_raw[self.df_raw["ID"].isin([res_id, bam_id])]

                if df_raw_filter.empty:
                    continue

                base_frame = df_raw_filter.iloc[0]

                frame_list = []
                frame_timestamp_list = []
                payload_concatenated = []
                can_id = None

                # iterate through rows in filtered dataframe
                for index, row in df_raw_filter.iterrows():
                    payload = row["DataBytes"]
                    first_byte = payload[0]
                    row_id = row["ID"]

                    # if single frame, save frame directly (excl. 1st byte)
                    if first_byte & SINGLE_FRAME_MASK == SINGLE_FRAME:
                        new_frame = self.construct_new_tp_frame(base_frame, payload[1:])
                        frame_list.append(new_frame.values.tolist())
                        frame_timestamp_list.append(index)

                    # if first frame, save info from prior multi frame response sequence,
                    # then initialize a new sequence incl. the first frame payload
                    elif (first_byte & FIRST_FRAME_MASK == FIRST_FRAME & bam_id == "") or (bam_id == row_id):
                        # create a new frame using information from previous iterations
                        if len(payload_concatenated) > 0:
                            new_frame = self.construct_new_tp_frame(base_frame, payload_concatenated, can_id)
                            frame_list.append(new_frame.values.tolist())
                            frame_timestamp_list.append(frame_timestamp)

                        # reset and start on next frame
                        payload_concatenated = []
                        frame_timestamp = index

                        # for J1939 BAM, extract PGN and convert to 29 bit CAN ID for use in baseframe
                        if bam_id_hex != "":
                            pgn_hex = "".join("{:02x}".format(x) for x in reversed(payload[5:8]))
                            pgn = int(pgn_hex, 16)
                            can_id = (6 << 26) | (pgn << 8) | 254

                        for byte in payload[first_frame_payload_start:]:
                            payload_concatenated.append(byte)

                    # if consequtive frame, extend payload with payload excl. 1st byte
                    elif first_byte & CONSEQ_FRAME_MASK == CONSEQ_FRAME:
                        for byte in payload[conseq_frame_payload_start:]:
                            payload_concatenated.append(byte)

                df_raw_tp = pd.DataFrame(frame_list, columns=base_frame.index, index=frame_timestamp_list)
                df_raw_excl_tp = self.df_raw[~self.df_raw["ID"].isin(self.res_id_list)]
                df_raw_combined = df_raw_excl_tp.append(df_raw_tp)
                df_raw_combined.index.name = "TimeStamp"

            df_raw_combined = df_raw_combined.sort_index()

            return df_raw_combined

    def decode_tp_data(self, df_raw_combined, df_decoder):
        import pandas as pd

        df_phys_list = []
        # to process data with variable payload lengths for the same ID
        # it needs to be processed group-by-group based on the data length:
        df_grouped = df_raw_combined.groupby("DataLength")
        df_phys = pd.DataFrame()
        for length, group in df_grouped:
            df_phys_group = df_decoder.decode_frame(group)
            df_phys = df_phys.append(df_phys_group)

        df_phys = df_phys.sort_index()
        return df_phys

    def combine_tp_frames_uds(self):

        SINGLE_FRAME_MASK = 0xFF
        FIRST_FRAME_MASK = 0xF0
        CONSEQ_FRAME_MASK = 0xF0
        SINGLE_FRAME = 0x00
        FIRST_FRAME = 0x10
        CONSEQ_FRAME = 0x20
        first_frame_payload_start = 2
        conseq_frame_payload_start = 1

        return self.combine_tp_frames(
            SINGLE_FRAME_MASK,
            FIRST_FRAME_MASK,
            CONSEQ_FRAME_MASK,
            SINGLE_FRAME,
            FIRST_FRAME,
            CONSEQ_FRAME,
            first_frame_payload_start,
            conseq_frame_payload_start,
        )

    def combine_tp_frames_nmea(self):

        SINGLE_FRAME_MASK = 0xFF
        FIRST_FRAME_MASK = 0x0F
        CONSEQ_FRAME_MASK = 0x00
        SINGLE_FRAME = 0xFF
        FIRST_FRAME = 0x00
        CONSEQ_FRAME = 0x00
        first_frame_payload_start = 0
        conseq_frame_payload_start = 1

        return self.combine_tp_frames(
            SINGLE_FRAME_MASK,
            FIRST_FRAME_MASK,
            CONSEQ_FRAME_MASK,
            SINGLE_FRAME,
            FIRST_FRAME,
            CONSEQ_FRAME,
            first_frame_payload_start,
            conseq_frame_payload_start,
        )

    def combine_tp_frames_j1939(self, bam_id_hex):

        SINGLE_FRAME_MASK = 0xFF
        FIRST_FRAME_MASK = 0xFF
        CONSEQ_FRAME_MASK = 0x00
        SINGLE_FRAME = 0xFF
        FIRST_FRAME = 0x20
        CONSEQ_FRAME = 0x00
        first_frame_payload_start = 8
        conseq_frame_payload_start = 1

        return self.combine_tp_frames(
            SINGLE_FRAME_MASK,
            FIRST_FRAME_MASK,
            CONSEQ_FRAME_MASK,
            SINGLE_FRAME,
            FIRST_FRAME,
            CONSEQ_FRAME,
            first_frame_payload_start,
            conseq_frame_payload_start,
            bam_id_hex,
        )
