import logging
from copy import deepcopy
from math import floor, ceil
import os

from neurochat.nc_utils import butter_filter
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from skm_pyutils.py_table import list_to_df
from skm_pyutils.py_plot import UnicodeGrabber
import simuran
import pandas as pd

from lfp_atn_simuran.analysis.lfp_clean import LFPClean


# 3. Compare theta and speed
def speed_vs_amp(self, lfp_signal, low_f, high_f, filter_kwargs=None, **kwargs):
    lim = kwargs.get("range", [0, self.get_duration()])
    samples_per_sec = kwargs.get("samplesPerSec", 10)
    do_once = True

    if filter_kwargs is None:
        filter_kwargs = {}
    try:
        lfp_signal = lfp_signal.filter(low_f, high_f, **filter_kwargs)
    except BaseException:
        lfp_signal = deepcopy(lfp_signal)
        _filt = [10, low_f, high_f, "bandpass"]
        lfp_signal._set_samples(
            butter_filter(
                lfp_signal.get_samples(), lfp_signal.get_sampling_rate(), *_filt
            )
        )

    # Calculate the LFP power
    skip_rate = int(self.get_sampling_rate() / samples_per_sec)
    slicer = slice(skip_rate, -skip_rate, skip_rate)
    index_to_grab = np.logical_and(self.get_time() >= lim[0], self.get_time() <= lim[1])
    time_to_use = self.get_time()[index_to_grab][slicer]
    speed = self.get_speed()[index_to_grab][slicer]

    lfp_amplitudes = np.zeros_like(time_to_use)
    lfp_samples = lfp_signal.get_samples()
    if hasattr(lfp_samples, "unit"):
        import astropy.units as u

        lfp_samples = lfp_samples.to(u.uV).value
    else:
        lfp_samples = lfp_samples * 1000

    for i, t in enumerate(time_to_use):
        diff = 1 / (2 * samples_per_sec)
        low_sample = floor((t - diff) * lfp_signal.get_sampling_rate())
        high_sample = ceil((t + diff) * lfp_signal.get_sampling_rate())
        if high_sample < len(lfp_samples):
            lfp_amplitudes[i] = np.mean(
                np.abs(lfp_samples[low_sample : high_sample + 1])
            )
        elif do_once:
            logging.warning(
                "Position data ({}s) is longer than EEG data ({}s)".format(
                    time_to_use[-1], len(lfp_samples) / lfp_signal.get_sampling_rate()
                )
            )
            do_once = False

    # binsize = kwargs.get("binsize", 2)
    # min_speed, max_speed = kwargs.get("range", [0, 40])

    # max_speed = min(max_speed, np.ceil(speed.max() / binsize) * binsize)
    # min_speed = max(min_speed, np.floor(speed.min() / binsize) * binsize)
    # bins = np.arange(min_speed, max_speed, binsize)

    # visit_time = np.histogram(speed, bins)[0]
    # speedInd = np.digitize(speed, bins) - 1

    # visit_time = visit_time / samples_per_sec
    # binned_lfp = [np.sum(lfp_amplitudes[speedInd == i]) for i in range(len(bins) - 1)]
    # rate = np.array(binned_lfp) / visit_time

    pd_df = list_to_df(
        [speed, lfp_amplitudes], transpose=True, headers=["Speed", "LFP amplitude"]
    )
    pd_df = pd_df[pd_df["Speed"] <= 40]
    pd_df["Speed"] = np.around(pd_df["Speed"])

    return pd_df


def speed_lfp_amp(
    recording,
    figures,
    base_dir,
    clean_method="avg",
    fmin=5,
    fmax=12,
    speed_sr=10,
    **kwargs,
):
    clean_kwargs = kwargs.get("clean_kwargs", {})
    lc = LFPClean(method=clean_method, visualise=False)
    signals_grouped_by_region = lc.clean(
        recording.signals, 0.5, 100, method_kwargs=clean_kwargs
    )["signals"]
    fmt = kwargs.get("image_format", "png")

    # Single values
    spatial = recording.spatial.underlying
    simuran.set_plot_style()
    results = {}
    skip_rate = int(spatial.get_sampling_rate() / speed_sr)
    slicer = slice(skip_rate, -skip_rate, skip_rate)
    speed = spatial.get_speed()[slicer]
    results["mean_speed"] = np.mean(speed)
    results["duration"] = spatial.get_duration()
    results["distance"] = results["mean_speed"] * results["duration"]

    basename = recording.get_name_for_save(base_dir)

    # Figures
    simuran.set_plot_style()
    for name, signal in signals_grouped_by_region.items():
        lfp_signal = signal

        # Speed vs LFP power
        pd_df = speed_vs_amp(spatial, lfp_signal, fmin, fmax, samplesPerSec=speed_sr)

        results[f"{name}_df"] = pd_df

        fig, ax = plt.subplots()
        sns.lineplot(data=pd_df, x="Speed", y="LFP amplitude", ax=ax)
        simuran.despine()
        fname = basename + "_speed_theta_{}".format(name)
        speed_amp_fig = simuran.SimuranFigure(
            fig, filename=fname, done=True, format=fmt, dpi=400
        )
        figures.append(speed_amp_fig)

    return results


def define_recording_group(base_dir, main_dir):
    dirs = base_dir[len(main_dir + os.sep) :].split(os.sep)
    dir_to_check = dirs[0]
    if dir_to_check.startswith("CS"):
        group = "Control"
    elif dir_to_check.startswith("LS"):
        group = "Lesion"
    else:
        group = "Undefined"

    number = int(dir_to_check.split("_")[0][-1])
    return group, number


def combine_results(info, extra_info, **kwargs):
    """This uses the pickle output from SIMURAN."""
    simuran.set_plot_style()
    data_animal_list, fname_animal_list = info
    out_dir, name = extra_info
    os.makedirs(out_dir, exist_ok=True)

    n_ctrl_animals = 0
    n_lesion_animals = 0
    df_lists = []
    for item_list, fname_list in zip(data_animal_list, fname_animal_list):
        r_ctrl = 0
        r_les = 0
        for item_dict, fname in zip(item_list, fname_list):
            item_dict = item_dict["speed_lfp_amp"]
            data_set, number = define_recording_group(
                os.path.dirname(fname), kwargs["cfg_base_dir"]
            )

            # if number >= 4:
            #     continue

            # Skip LSR7 if present
            if number == 7:
                continue

            if data_set == "Control":
                r_ctrl += 1
            else:
                r_les += 1

            for r in ["SUB", "RSC"]:
                id_ = item_dict[r + "_df"]
                id_["Group"] = data_set
                id_["region"] = r
                id_["number"] = number
                df_lists.append(id_)

            # ic(
            #     fname,
            #     data_set,
            #     number,
            #     item_dict["mean_speed"],
            #     len(item_dict["RSC_df"]),
            # )
        n_ctrl_animals += r_ctrl / len(fname_list)
        n_lesion_animals += r_les / len(fname_list)

    print(f"{n_ctrl_animals} CTRL animals, {n_lesion_animals} Lesion animals")

    df = pd.concat(df_lists, ignore_index=True)
    df.replace("Control", f"Control (ATN,   N = {int(n_ctrl_animals)})", inplace=True)
    df.replace("Lesion", f"Lesion  (ATNx, N = {int(n_lesion_animals)})", inplace=True)

    print("Saving plots to {}".format(os.path.join(out_dir, "summary")))

    control_df = df[df["Group"] == f"Lesion  (ATNx, N = {int(n_lesion_animals)})"]
    sub_df = control_df[control_df["region"] == "RSC"]
    print(sub_df.groupby("Speed").mean())
    for ci, oname in zip([95, None], ["_ci", ""]):
        sns.lineplot(
            data=df[df["region"] == "SUB"],
            x="Speed",
            y="LFP amplitude",
            style="Group",
            hue="Group",
            ci=ci,
            estimator=np.median,
            # estimator="mean",
        )
        simuran.despine()
        plt.xlabel("Speed (cm / s)")
        plt.ylabel("Amplitude ({}V)".format(UnicodeGrabber.get("micro")))
        plt.title("Subicular LFP power (median)")

        os.makedirs(os.path.join(out_dir, "summary"), exist_ok=True)
        plt.savefig(
            os.path.join(
                out_dir, "summary", name + "--sub--speed--theta{}.png".format(oname)
            ),
            dpi=400,
        )

        plt.close("all")

        sns.lineplot(
            data=df[df["region"] == "RSC"],
            x="Speed",
            y="LFP amplitude",
            style="Group",
            hue="Group",
            ci=ci,
            estimator=np.median,
            # estimator="mean",
        )
        simuran.despine()
        plt.xlabel("Speed (cm / s)")
        plt.ylabel("Amplitude ({}V)".format(UnicodeGrabber.get("micro")))
        plt.title("Retrosplenial LFP power (median)")

        plt.savefig(
            os.path.join(
                out_dir, "summary", name + "--rsc--speed--theta{}.png".format(oname)
            ),
            dpi=400,
        )

        plt.close("all")
