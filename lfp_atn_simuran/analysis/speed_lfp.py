import logging
from copy import deepcopy
from math import floor, ceil
from collections import OrderedDict

from neurochat.nc_utils import butter_filter
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from skm_pyutils.py_table import list_to_df
import simuran

# 1. Compare speed and firing rate
def speed_firing(self, spike_train, **kwargs):
    graph_results = self.speed(spike_train, **kwargs)

    results = {}
    results["lin_fit_r"] = self.get_results()["Speed Pears R"]
    results["lin_fit_p"] = self.get_results()["Speed Pears P"]
    results["lin_speed"] = graph_results["bins"]
    results["lin_rate"] = graph_results["rate"]

    return results


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
            speed_time_idx1 = int(time_start * speed_sr)
            speed_time_idx2 = int(time_end * speed_sr)
            burst_speed = speed[speed_time_idx1:speed_time_idx2]
            avg_speed = np.mean(burst_speed)
            ibi_speeds.append(avg_speed)

        # ibi in sec, burst_duration in ms
    else:
        logging.warning("No burst detected")
    ibi = 1000 * np.array(ibi)

    return ibi, np.array(ibi_speeds)


def speed_ibi(self, spike_train, **kwargs):
    samples_per_sec = kwargs.get("samplesPerSec", 10)
    binsize = kwargs.get("binsize", 1)
    min_speed, max_speed = kwargs.get("range", [0, 40])

    speed = self.get_speed()
    max_speed = min(max_speed, np.ceil(speed.max() / binsize) * binsize)
    min_speed = max(min_speed, np.floor(speed.min() / binsize) * binsize)
    bins = np.arange(min_speed, max_speed, binsize)

    ibi, ibi_speeds = calc_ibi(spike_train, speed, samples_per_sec)
    return ibi, ibi_speeds


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
    binsize = kwargs.get("binsize", 2)
    min_speed, max_speed = kwargs.get("range", [0, 40])

    max_speed = min(max_speed, np.ceil(speed.max() / binsize) * binsize)
    min_speed = max(min_speed, np.floor(speed.min() / binsize) * binsize)
    bins = np.arange(min_speed, max_speed, binsize)

    visit_time = np.histogram(speed, bins)[0]
    speedInd = np.digitize(speed, bins) - 1

    # visit_time = visit_time / samples_per_sec

    lfp_amplitudes = np.zeros_like(time_to_use)
    lfp_samples = lfp_signal.get_samples()
    if hasattr(lfp_samples, "unit"):
        import astropy.units as u

        lfp_samples = lfp_samples.to(u.uV).value
    else:
        lfp_samples = lfp_samples * 1000

    for i, t in enumerate(time_to_use):
        low_sample = floor((t - 0.05) * lfp_signal.get_sampling_rate())
        high_sample = ceil((t + 0.05) * lfp_signal.get_sampling_rate())
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

    # binned_lfp = [np.sum(lfp_amplitudes[speedInd == i]) for i in range(len(bins) - 1)]
    # rate = np.array(binned_lfp) / visit_time

    pd_df = list_to_df(
        [speed, lfp_amplitudes], transpose=True, headers=["Speed", "LFP amplitude"]
    )
    pd_df = pd_df[pd_df["Speed"] <= 40]
    pd_df["Speed"] = np.around(pd_df["Speed"])

    return pd_df


def main(spatial, lfp_signal, spike_train, binsize=1, speed_sr=10):
    """Perform speed to lfp calculations."""
    # This bit can be performed without spike info
    simuran.set_plot_style()
    results = {}
    skip_rate = int(spatial.get_sampling_rate() / speed_sr)
    slicer = slice(skip_rate, -skip_rate, skip_rate)
    speed = spatial.get_speed()[slicer]
    results["mean_speed"] = np.mean(speed)
    results["duration"] = spatial.get_duration()
    results["distance"] = results["mean_speed"] * results["duration"]

    # Speed vs LFP power
    pd_df = speed_vs_amp(
        spatial, lfp_signal, 5, 12, binsize=binsize, samplesPerSec=speed_sr
    )

    fig, ax = plt.subplots()
    sns.lineplot(data=pd_df, x="Speed", y="LFP amplitude", ax=ax)
    # TODO fill filename
    simuran.despine()
    speed_amp_fig = simuran.SimuranFigure(fig, filename=None, done=True)
    return results, speed_amp_fig

    # This part requires spike info

    # Speed vs firing rate
    data = spatial.speed(spike_train, binsize=binsize, samplesPerSec=speed_sr)
    r, b = data["rate"], data["bins"]
    b1, r1 = speed_firing(spatial, spike_train, speed_sr)

    pd_df = list_to_df([b1, r1], transpose=True, headers=["Speed", "Firing rate"])
    pd_df = pd_df[pd_df["Speed"] <= 40]
    pd_df = pd_df[pd_df["Firing rate"] < 20]
    pd_df["Speed"] = np.around(pd_df["Speed"])

    fig, axes = plt.subplots(2, 1)
    sns.lineplot(x=b, y=r, ax=axes[0])
    # sns.scatterplot(x=b1, y=r1, ax=axes[1])
    sns.lineplot(data=pd_df, x="Speed", y="Firing rate", ax=axes[1])
    fig.savefig("speed_frate.png", dpi=400)
    plt.close(fig)

    # Speed vs IBI
    r, b = speed_ibi(spatial, spike_train, samplesPerSec=speed_sr)
    fig, ax = plt.subplots()

    sns.scatterplot(x=b, y=r, ax=ax)
    fig.savefig("speed_ibi.png", dpi=400)
    plt.close(fig)
