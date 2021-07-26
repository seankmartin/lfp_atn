from copy import deepcopy
import os
import logging
from math import floor, ceil

import matplotlib.pyplot as plt
import numpy as np
import simuran
import scipy.stats
import seaborn as sns
from skm_pyutils.py_table import list_to_df


# 1. Compare speed and firing rate
def speed_firing(self, spike_train, **kwargs):
    graph_results = self.speed(spike_train, **kwargs)
    ax = kwargs.get("ax", None)

    results = {}
    results["lin_fit_r"] = self.get_results()["Speed Pears R"]
    results["lin_fit_p"] = self.get_results()["Speed Pears P"]

    bins = np.array([int(b) for b in graph_results["bins"]])
    rate = np.array([float(r) for r in graph_results["rate"]])

    if ax is None:
        fig, ax = plt.subplots()

    df = list_to_df([bins, rate], transpose=True, headers=["Speed", "Firing rate"])

    sns.lineplot(data=df, x="Speed", y="Firing rate", ax=ax)
    ax.set_title("Speed vs Firing rate")
    ax.set_xlabel("Speed (cm / s)")
    ax.set_ylabel("Firing rate (spike / s)")

    return results, ax


# 2. Compare speed and interburst interval
def calc_ibi(spike_train, speed, speed_sr, burst_thresh=5):
    unitStamp = spike_train
    isi = 1000 * np.diff(unitStamp)

    burst_start = []
    burst_end = []
    burst_duration = []
    spikesInBurst = []
    bursting_isi = []
    num_burst = 0
    ibi = []
    k = 0
    ibi_speeds = []
    while k < isi.size:
        if isi[k] <= burst_thresh:
            burst_start.append(k)
            spikesInBurst.append(2)
            bursting_isi.append(isi[k])
            burst_duration.append(isi[k])
            m = k + 1
            while m < isi.size and isi[m] <= burst_thresh:
                spikesInBurst[num_burst] += 1
                bursting_isi.append(isi[m])
                burst_duration[num_burst] += isi[m]
                m += 1
            # to compensate for the span of the last spike
            burst_duration[num_burst] += 1
            burst_end.append(m)
            k = m + 1
            num_burst += 1
        else:
            k += 1

    if num_burst:
        for j in range(0, num_burst - 1):
            time_end = unitStamp[burst_start[j + 1]]
            time_start = unitStamp[burst_end[j]]
            ibi.append(time_end - time_start)
            speed_time_idx1 = int(floor(time_start * speed_sr))
            speed_time_idx2 = int(ceil(time_end * speed_sr))
            burst_speed = speed[speed_time_idx1:speed_time_idx2]
            avg_speed = np.mean(burst_speed)
            ibi_speeds.append(avg_speed)

        # ibi in sec, burst_duration in ms
    else:
        # TODO test this
        simuran.log.warning("No burst detected")
        return None, None
    ibi = np.array(ibi) / 1000

    return ibi, np.array(ibi_speeds)


def speed_ibi(self, spike_train, **kwargs):
    samples_per_sec = kwargs.get("samplesPerSec", 10)
    binsize = kwargs.get("binsize", 1)
    min_speed, max_speed = kwargs.get("range", [0, 40])
    ax = kwargs.get("ax", None)

    speed = self.get_speed()
    max_speed = min(max_speed, np.ceil(speed.max() / binsize) * binsize)
    min_speed = max(min_speed, np.floor(speed.min() / binsize) * binsize)
    bins = np.arange(min_speed, max_speed, binsize)

    ibi, ibi_speeds = calc_ibi(spike_train, speed, samples_per_sec)
    if ibi is None:
        return None, None, np.nan, np.nan, 0
    elif len(ibi) < 10:
        return None, None, np.nan, np.nan, 0
    spear_r, spear_p = scipy.stats.spearmanr(ibi_speeds, ibi)

    pd_df = list_to_df([ibi_speeds, ibi], transpose=True, headers=["Speed", "IBI"])
    pd_df = pd_df[pd_df["Speed"] <= 40]
    pd_df["Speed"] = np.around(pd_df["Speed"]).astype(int)

    if ax is None:
        _, ax = plt.subplots()
    sns.lineplot(data=pd_df, x="Speed", y="IBI", ci=None, ax=ax)
    ax.set_ylabel("IBI (s)")
    ax.set_xlabel("Speed (cm / s)")
    ax.set_title("Speed vs IBI")

    return pd_df, ax, spear_r, spear_p, len(ibi) + 1


def recording_ibi_headings():
    return [
        "IBI R",
        "IBI P",
        "Number of bursts",
        "Speed R",
        "Speed P",
        "Mean speed",
        "Mean firing rate",
    ]


# TODO add average IBI to this to comp avg speed and avg IBI
def recording_speed_ibi(recording, out_dir, base_dir, **kwargs):
    """This is performed per cell in the recording."""
    # How many results expected in a row?
    NUM_RESULTS = len(recording_ibi_headings())
    img_format = kwargs.get("img_format", ".png")

    simuran.set_plot_style()

    output = {}
    # To avoid overwriting what has been set to analyse
    all_analyse = deepcopy(recording.get_set_units())

    # Unit contains probe/tetrode info, to_analyse are list of cells
    spatial_error = False
    try:
        recording.spatial.load()
    except BaseException:
        print(
            "WARNING: Unable to load spatial information for {}".format(
                recording.source_file
            )
        )
        spatial_error = True

    spatial = recording.spatial.underlying
    for unit, to_analyse in zip(recording.units, all_analyse):

        # Two cases for empty list of cells
        if to_analyse is None:
            continue
        if len(to_analyse) == 0:
            continue

        unit.load()
        # Loading can overwrite units_to_use, so reset these after load
        unit.units_to_use = to_analyse
        out_str_start = str(unit.group)
        no_data_loaded = unit.underlying is None
        if not no_data_loaded:
            available_units = unit.underlying.get_unit_list()

        for cell in to_analyse:
            name_for_save = out_str_start + "_" + str(cell)
            output[name_for_save] = [np.nan] * NUM_RESULTS

            if spatial_error:
                continue
            # Check to see if this data is ok
            if no_data_loaded:
                continue
            if cell not in available_units:
                continue

            op = [np.nan] * NUM_RESULTS
            fig, axes = plt.subplots(2, 1)
            unit.underlying.set_unit_no(cell)
            spike_train = unit.underlying.get_unit_stamp()
            ibi_df, ibi_ax, sr, sp, nb = speed_ibi(spatial, spike_train, ax=axes[0])
            op[0] = sr
            op[1] = sp
            op[2] = nb

            res, speed_ax = speed_firing(spatial, spike_train, ax=axes[1], binsize=2)

            op[3] = res["lin_fit_r"]
            op[4] = res["lin_fit_p"]
            op[5] = np.mean(np.array(spatial.get_speed()))
            op[6] = len(spike_train) / unit.underlying.get_duration()

            simuran.despine()
            plt.tight_layout()
            out_name_end = recording.get_name_for_save(base_dir)
            out_name_end += "_T{}_SS{}".format(out_str_start, str(cell))
            out_name = os.path.join(out_dir, out_name_end) + img_format
            # TODO test this
            simuran.print("Saving plot to {}".format(out_name))
            fig.savefig(out_name, dpi=400)
            plt.close(fig)

            output[name_for_save] = op
            # Do analysis on that unit
            unit.underlying.reset_results()

    return output

# TODO integrate this function
def vis_speed_ibi(df, out_dir=None):
    simuran.set_plot_style()

    fig, ax = plt.subplots()
    sns.scatterplot(
        data=df, x="Mean speed", y="IBI R", hue="State", style="State", ax=ax
    )

    simuran.despine()

    fig.savefig("Speed_IBI.png")


if __name__ == "__main__":
    import pandas as pd
    
    location = r"E:\Repos\lfp_atn\lfp_atn_simuran\sim_results\list_spike_ibi\CTRL_Lesion_cells_filled_spike_ibi_and_locking_results.xlsx"

    df = pd.read_excel(location)
    vis_speed_ibi(df)
