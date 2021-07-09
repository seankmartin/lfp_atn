import os
from site import addsitedir
from math import floor, ceil

import simuran
import pandas as pd
import matplotlib.pyplot as plt
import astropy.units as u
from neurochat.nc_lfp import NLfp
import numpy as np
from scipy.signal import coherence
from skm_pyutils.py_table import list_to_df
import seaborn as sns

try:
    from lfp_atn_simuran.analysis.lfp_clean import LFPClean
    from lfp_atn_simuran.analysis.plot_coherence import plot_recording_coherence
    from lfp_atn_simuran.analysis.frequency_analysis import powers
    from lfp_atn_simuran.analysis.parse_cfg import parse_cfg_info

    do_analysis = True
except ImportError:
    do_analysis = False

lib_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
addsitedir(lib_folder)
from lib.plots import plot_pos_over_time

here = os.path.dirname(os.path.abspath(__file__))


def main(excel_location, base_dir):
    df = pd.read_excel(excel_location)
    cfg = parse_cfg_info()
    delta_min = cfg["delta_min"]
    delta_max = cfg["delta_max"]
    theta_min = cfg["theta_min"]
    theta_max = cfg["theta_max"]
    clean_method = cfg["clean_method"]
    clean_kwargs = cfg["clean_kwargs"]
    window_sec = 1
    fmin, fmax = 1, 40

    ituples = df.itertuples()
    num_rows = len(df)

    no_pass = False
    if "passed" not in df.columns:
        print("Please add passed as a column to the df.")
        no_pass = True

    results = []
    coherence_df_list = []
    for j in range(num_rows // 2):
        row1 = next(ituples)
        row2 = next(ituples)
        recording_location = os.path.join(base_dir, row1.location)
        recording_location = recording_location.replace("--", os.sep)
        param_file = os.path.join(here, "..", "recording_mappings", row1.mapping)

        recording = simuran.Recording(
            param_file=param_file, base_file=recording_location
        )
        spatial = recording.spatial.underlying
        lfp_clean = LFPClean(method=clean_method, visualise=False)
        sig_dict = lfp_clean.clean(
            recording, min_f=fmin, max_f=fmax, method_kwargs=clean_kwargs
        )["signals"]

        x = np.array(sig_dict["SUB"].samples.to(u.mV))
        y = np.array(sig_dict["RSC"].samples.to(u.mV))
        fs = sig_dict["SUB"].sampling_rate
        f, Cxy = coherence(x, y, fs, nperseg=2 * fmax)
        f = f[np.nonzero((f >= fmin) & (f <= fmax))]
        Cxy = Cxy[np.nonzero((f >= fmin) & (f <= fmax))]

        max_theta_coherence_ = max(
            Cxy[np.nonzero((f >= theta_min) & (f <= theta_max))]
        )
        max_delta_coherence_ = max(
            Cxy[np.nonzero((f >= delta_min) & (f <= delta_max))]
        )

        fig, ax = plt.subplots()
        for r in (row1, row2):
            # end or choice could be used
            # t1, t2 = r.start, r.end
            t1, t2 = r.start, r.choice
            t3 = r.end
            lfpt1, lfpt2 = int(floor(t1 * 250)), int(ceil(t2 * 250))

            st1, st2 = int(floor(t1 * 50)), int(ceil(t3 * 50))
            x_time = spatial.get_pos_x()[st1:st2]
            y_time = spatial.get_pos_y()[st1:st2]
            c_end = int(floor(t2 * 50))
            spat_c = (spatial.get_pos_x()[c_end], spatial.get_pos_y()[c_end])

            if r.test == "first":
                c = "k"
            else:
                c = "r"

            ax.plot(x_time, y_time, c=c, label=r.test)
            ax.plot(spat_c[0], spat_c[1], c="b", marker="x", label="decision")
            ax.plot(x_time[0], y_time[0], c="b", marker="o", label="start")
            ax.plot(x_time[-1], y_time[-1], c="b", marker=".", label="end")

            res_dict = {}
            for region, signal in sig_dict.items():
                lfp = NLfp()
                lfp.set_channel_id(signal.channel)
                lfp._timestamp = np.array(signal.timestamps[lfpt1:lfpt2].to(u.s))
                lfp._samples = np.array(signal.samples[lfpt1:lfpt2].to(u.mV))
                lfp._record_info["Sampling rate"] = signal.sampling_rate
                delta_power = lfp.bandpower(
                    [delta_min, delta_max], window_sec=window_sec, band_total=True
                )
                theta_power = lfp.bandpower(
                    [theta_min, theta_max], window_sec=window_sec, band_total=True
                )
                res_dict["{}_delta".format(region)] = delta_power["relative_power"]
                res_dict["{}_theta".format(region)] = theta_power["relative_power"]

            res_list = [r.location, r.session, r.animal, r.test]
            res_list += [
                res_dict["SUB_delta"],
                res_dict["SUB_theta"],
                res_dict["RSC_delta"],
                res_dict["RSC_theta"],
            ]
            results.append(res_list)
            name = os.path.splitext(r.location)[0]

            x = np.array(sig_dict["SUB"].samples[lfpt1:lfpt2].to(u.mV))
            y = np.array(sig_dict["RSC"].samples[lfpt1:lfpt2].to(u.mV))
            fs = sig_dict["SUB"].sampling_rate

            f, Cxy = coherence(x, y, fs, nperseg=2 * fmax)
            f = f[np.nonzero((f >= fmin) & (f <= fmax))]
            Cxy = Cxy[np.nonzero((f >= fmin) & (f <= fmax))]

            max_theta_coherence = max(
                Cxy[np.nonzero((f >= theta_min) & (f <= theta_max))]
            )
            max_delta_coherence = max(
                Cxy[np.nonzero((f >= delta_min) & (f <= delta_max))]
            )

            fig2, ax2 = plt.subplots(3, 1)
            ax2[0].plot(f, Cxy, c="k")
            ax2[1].plot([i / 250 for i in range(len(x))], x, c="k")
            ax2[2].plot([i / 250 for i in range(len(y))], y, c="k")
            base_dir_new = os.path.dirname(excel_location)
            fig2.savefig(
                os.path.join(
                    base_dir_new,
                    "coherence_{}_{}_{}.png".format(row1.location, r.session, r.test),
                )
            )
            plt.close(fig2)
            res_list += [max_theta_coherence, max_delta_coherence]
            res_list += [max_theta_coherence_, max_delta_coherence_]

            if no_pass is False:
                group = (
                    "Control" if r.animal.lower().startswith("c") else "Lesion (ATNx)"
                )
                for f_, cxy_ in zip(f, Cxy):
                    coherence_df_list.append((f_, cxy_, r.passed, group))

        ax.invert_yaxis()
        ax.legend()
        base_dir_new = os.path.dirname(excel_location)
        figname = os.path.join(base_dir_new, name) + "_tmaze.png"
        fig.savefig(figname, dpi=400)
        plt.close(fig)

    headers = [
        "location",
        "session",
        "animal",
        "test",
        "SUB_delta",
        "SUB_theta",
        "RSC_delta",
        "RSC_theta",
        "Theta_coherence",
        "Delta_coherence",
        "Full_theta_coherence",
        "Full_delta_coherence",
    ]

    df = pd.DataFrame(results, columns=headers)

    split = os.path.splitext(excel_location)
    out_name = split[0] + "_results" + split[1]
    df.to_excel(out_name, index=False)

    if no_pass is False:
        headers = ["Frequency (Hz)", "Coherence", "Choice", "Group"]
        df = list_to_df(coherence_df_list, headers=headers)

        sns.lineplot(
            data=df, x="Frequency (Hz)", y="Coherence", hue="Group", style="Choice"
        )
        plt.savefig(os.path.join(os.path.dirname(excel_location), "coherence"))


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    main_output_location = os.path.join(here, "results")

    base_dir = r"D:\SubRet_recordings_imaging"
    xls_location = os.path.join(main_output_location, "tmaze-times.xlsx")

    main(xls_location, base_dir)