# -*- coding: utf-8 -*-

# Mount google drive files
from google.colab import drive
drive.mount("/content/drive", force_remount=True)

# Install packages
!pip install git+https://github.com/seankmartin/NeuroChaT -q
!pip install git+https://github.com/seankmartin/PythonUtils -q
!pip install git+https://github.com/seankmartin/SIMURAN -q
!pip install git+https://github.com/seankmartin/lfp_atn -q
!pip install mne -q
!pip install fooof -q

# Import libraries
import os
import csv

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from tqdm.notebook import tqdm
import simuran
from lfp_atn_simuran.Scripts.frequency_analysis import powers
from fooof import FOOOFGroup

# Configuration
path_dir = "/content/drive/My Drive/NeuroScience/ATN_CA1"
temp_storage_location = "/content/drive/My Drive/NeuroScience/Temp"
index_location = os.path.join(temp_storage_location, "index.csv")
mapping_params_location = os.path.join(temp_storage_location, "mapping.py")
os.makedirs(os.path.dirname(index_location), exist_ok=True)

nc_loader_kwargs = {
    "system": "Axona",
    "pos_extension": ".pos"
}

clean_kwargs = {
    "pick_property": "group",
    "channels": ["LFP"],
}

all_params = {
    # Cleaning params
    "clean_method": "pick_zscore",
    "clean_kwargs": clean_kwargs,
    
    # Filtering params
    "fmin": 1,
    "fmax": 100,
    "theta_min": 6,
    "theta_max": 10,
    "delta_min": 1.5,
    "delta_max": 4,
    "fmax_plot": 40,

    # Plotting params
    "psd_scale": "decibels",
    "image_format": "png",

    # Path setup
    "cfg_base_dir" : "/content/drive/My Drive/NeuroScience/ATN_CA1",

    # STA
    "number_of_shuffles_sta": 5
}

# Write out the mapping file

def setup_signals():
    """Set up the signals (such as eeg or lfp)."""

    # The total number of signals in the recording
    num_signals = 32

    # What brain region each signal was recorded from
    regions = ["CA1"] * 32

    # If the wires were bundled, or any other kind of grouping existed
    # If no grouping, grouping = [i for in range(num_signals)]
    groups = ["LFP", "LFP"] + [i for i in range(num_signals - 2)]

    # The sampling rate in Hz of each signal
    sampling_rate = [250] * num_signals

    # This just passes the information on
    output_dict = {
        "num_signals": num_signals,
        "region": regions,
        "group": groups,
        "sampling_rate": sampling_rate,
    }

    return output_dict


def setup_units():
    """Set up the single unit data."""
    # The number of tetrodes, probes, etc - any kind of grouping
    num_groups = 8

    # The region that each group belongs to
    regions = ["CA1"] * num_groups

    # A group number for each group, for example the tetrode number
    groups = [1, 2, 3, 4, 9, 10, 11, 12]

    output_dict = {
        "num_groups": num_groups,
        "region": regions,
        "group": groups,
    }

    return output_dict


def setup_spatial():
    """Set up the spatial data."""

    output_dict = {
        "arena_size": "default",
    }
    return output_dict


def setup_loader():
    """
    Set up the loader and keyword arguments for the loader.

    See also
    --------
    simuran.loaders.loader_list.py

    """
    # The type of loader to use, see simuran.loaders.loader_list.py for options
    loader = "nc_loader"

    output_dict = {
        "loader": loader,
        "loader_kwargs": nc_loader_kwargs,
    }

    return output_dict


load_params = setup_loader()
mapping = {
    "signals": setup_signals(),
    "units": setup_units(),
    "spatial": setup_spatial(),
    "loader": load_params["loader"],
    "loader_kwargs": load_params["loader_kwargs"],
}

ph = simuran.ParamHandler(params=mapping)
ph.write(mapping_params_location)

# Index the files if not already done
overwrite = False

def add_mapping_to_df(input_df, **kwargs):
    input_df["Mapping"] = [os.path.basename(mapping_params_location)] * len(input_df)
    return input_df

files_df = simuran.index_ephys_files(
    path_dir,
    loader_name="neurochat",
    out_loc=index_location,
    post_process_fn=add_mapping_to_df,
    overwrite=overwrite,
    post_process_kwargs=None,
    loader_kwargs=nc_loader_kwargs,
)

# Inspect the files_df
files_df

# Parse the recording information
rc = simuran.recording_container_from_df(
    files_df,
    base_dir=path_dir,
    param_dir=temp_storage_location
    )

from skm_pyutils.py_log import get_default_log_loc

log_loc = get_default_log_loc("test.log")
print(log_loc)

# Analyse each recording in the container
ah = simuran.AnalysisHandler(handle_errors=True)
sm_figures = []

fn_kwargs = all_params

for r in rc:
    for i in range(len(r.signals)):
        r.signals[i].load()
    fn_args = [r, path_dir, sm_figures]
    ah.add_fn(powers, *fn_args, **fn_kwargs)

ah.run_all_fns(pbar="notebook")

# Save the analysis results
print(ah)
simuran.save_figures(sm_figures, temp_storage_location, verbose=True)
ah.save_results(os.path.join(temp_storage_location, "results.csv"))

class UnicodeGrabber(object):
    """This is a fully static class to get unicode chars for plotting."""
    char_dict = {
        "micro": u"\u00B5",
        "pow2": u"\u00B2",
    }

    @staticmethod
    def get_chars():
        return list(UnicodeGrabber.char_dict.keys())

    @staticmethod
    def get(char, default=""):
        return UnicodeGrabber.char_dict.get(char, default)

# Combine the results

# First, extract the frequencies and powers
with open(os.path.join(temp_storage_location, "results.csv"), "r") as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',', quotechar="'")
    welch_freqs = []
    welch_powers = []
    freq_end = 199
    power_end = 2 * freq_end
    max_pxxs = []
    for row in csvreader:
        if row[0] == "CA1 welch":
            values = row[1:]
            freqs = values[:freq_end]
            freqs = np.array([float(f[1:]) for f in freqs])
            powers = values[freq_end:power_end]
            powers = np.array([float(f[1:]) for f in powers])
            welch_freqs.append(freqs)
            welch_powers.append(powers)
        elif row[0] == "CA1 max f":
            val = float(row[1])
            max_pxxs.append(val)
in_list = [np.array(welch_freqs).flatten(), np.array(welch_powers).flatten()]

# Then combine these into a pandas df as
# F, P
df = pd.DataFrame(in_list).T
df.columns = ["frequency", "power"]
df.to_csv(os.path.join(temp_storage_location, "power_results.csv"), index=False)
print(df.head())

## Then use seaborn to produce a summary plot
scale = all_params["psd_scale"]
simuran.set_plot_style()
plt.close("all")
for ci, oname in zip([95, None], ["_ci", ""]):
    out_loc = os.path.join(temp_storage_location, f"ca1_power_final{oname}.pdf")

    sns.lineplot(
            data=df,
            x="frequency",
            y="power",
            ci=ci,
            estimator=np.median,
        )
    plt.xlabel("Frequency (Hz)")
    plt.xlim(0, all_params["fmax_plot"])
    plt.ylim(-25, 0)
    if scale == "volts":
        micro = UnicodeGrabber.get("micro")
        pow2 = UnicodeGrabber.get("pow2")
        plt.ylabel(f"PSD ({micro}V{pow2} / Hz)")
    elif scale == "decibels":
        plt.ylabel("PSD (dB)")
    else:
        raise ValueError("Unsupported scale {}".format(scale))
    plt.title("CA1 LFP power (median)")
    simuran.despine()

    plt.savefig(out_loc, dpi=400,)
    plt.show()
    print(f"Figure saved to {out_loc}")
    plt.close("all")

# Fooof plots
peaks_data = []
fg = FOOOFGroup(
    peak_width_limits=[1.0, 8.0],
    max_n_peaks=2,
    min_peak_height=0.1,
    peak_threshold=2.0,
    aperiodic_mode="fixed",
)

fooof_arr_s = np.array(welch_powers)
for i in range(len(fooof_arr_s)):
    fooof_arr_s[i] = (np.power(10.0, (fooof_arr_s[i] / 10.0)) * max_pxxs[i])

fooof_arr_f = np.array(welch_freqs)
fg.fit(fooof_arr_f[0], fooof_arr_s, [0.5, 40], progress="tqdm.notebook")

peaks = fg.get_params("peak_params", 0)[:, 0]

for p in peaks:
    peaks_data.append([p, "Control", "CA1"])

peaks_df = pd.DataFrame.from_records(peaks_data, columns=["Peak frequency", "Group", "Region"])

fig, ax = plt.subplots()
sns.histplot(
    data=peaks_df,
    x="Peak frequency",
    # element="step",
    ax=ax,
)
simuran.despine()
out_name = os.path.join(temp_storage_location, "ca1_peaks_fooof.pdf")
fig.savefig(out_name, dpi=400)
plt.close(fig)

# To see errors, use this
!ln -s /root/.skm_python /root/skm_python