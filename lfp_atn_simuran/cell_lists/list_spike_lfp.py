import os

import simuran

from lfp_atn_simuran.analysis.spike_lfp import recording_spike_lfp, combine_results
from lfp_atn_simuran.analysis.parse_cfg import parse_cfg_info

here = os.path.dirname(os.path.abspath(__file__))
herename = os.path.splitext(os.path.basename(__file__))[0]


def main():
    cfg = parse_cfg_info()
    out_dir = os.path.abspath(os.path.join(here, "..", "sim_results", herename))
    os.makedirs(out_dir, exist_ok=True)
    cell_list = os.path.join(here, "CTRL_Lesion_cells_filled_eeg.xlsx")
    headers = ["STA_SUB", "SFC_SUB", "STA_RSC", "SFC_RSC", "Time", "Frequency"]
    simuran.analyse_cell_list(
        cell_list,
        recording_spike_lfp,
        headers,
        combine_results,
        out_dir,
        fn_kwargs=cfg,
    )


if __name__ == "__main__":
    main()