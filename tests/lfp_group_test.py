import os
import simuran
from pprint import pprint

# Import from my files
from lfp_atn_simuran.Scripts.frequency_analysis import grouped_powers, powers
from lfp_atn_simuran.Scripts.lfp_clean import LFPClean
from default_recording import load_recording


def main(set_file_location, output_location):
    lc = LFPClean(method="avg", visualise=True, show_vis=True)
    recording = load_recording(set_file_location)
    # fig = lc.compare_methods(("avg", "avg_raw"), recording, 1, 100)
    results = lc.clean(recording, min_f=1, max_f=100)
    results["fig"].savefig(output_location[:-4] + ".png", dpi=300)
    analysis_handler = simuran.AnalysisHandler()
    # analysis_handler.add_fn(grouped_powers, recording, min_f=1, max_f=100, win_len=2)
    analysis_handler.add_fn(powers, recording, min_f=1, max_f=100, win_len=2)
    analysis_handler.run_all_fns()
    analysis_handler.save_results(output_location=output_location)


if __name__ == "__main__":
    # Establish data paths
    main_set_file_location = os.path.join(
        "D:\\",
        "SubRet_recordings_imaging",
        os.path.normpath(
            "LSubRet5/recording/Small sq up_small sq down/01122017/S1_small sq up/01122017_smallsqdownup_up_1_1.set"
        ),
    )
    main_output_location = "compare_results.csv"
    main(main_set_file_location, main_output_location)
