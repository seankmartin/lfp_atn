from copy import deepcopy

import simuran
import numpy as np
import pandas as pd

from lfp_atn_simuran.analysis.lfp_clean import LFPClean
from skm_pyutils.py_table import list_to_df
from skm_pyutils.py_plot import UnicodeGrabber

import matplotlib.pyplot as plt


def recording_spike_lfp(recording, clean_method="avg", **kwargs):
    clean_kwargs = kwargs.get("clean_kwargs", {})
    lc = LFPClean(method=clean_method, visualise=False)
    fmin = 0
    fmax = 100
    for i in range(len(recording.signals)):
        recording.signals[i].load()
    signals_grouped_by_region = lc.clean(
        recording.signals, fmin, fmax, method_kwargs=clean_kwargs
    )["signals"]

    simuran.set_plot_style()
    fmt = kwargs.get("image_format", "png")

    sub_sig = signals_grouped_by_region["SUB"]
    rsc_sig = signals_grouped_by_region["RSC"]

    # SFC here
    nc_sig = sub_sig.to_neurochat()
    nc_sig2 = rsc_sig.to_neurochat()

    NUM_RESULTS = 6

    output = {}
    # To avoid overwriting what has been set to analyse
    all_analyse = deepcopy(recording.get_set_units())

    # Unit contains probe/tetrode info, to_analyse are list of cells
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
        available_units = unit.underlying.get_unit_list()

        for cell in to_analyse:
            name_for_save = out_str_start + "_" + str(cell)
            output[name_for_save] = [np.nan] * NUM_RESULTS

            # Check to see if this data is ok
            if no_data_loaded:
                continue
            if cell not in available_units:
                continue

            unit.underlying.set_unit_no(cell)
            # Do analysis on that unit
            spike_train = unit.underlying.get_unit_stamp()

            g_data = nc_sig.plv(spike_train, mode="bs", fwin=[0, 20])
            sta = g_data["STAm"]
            sfc = g_data["SFCm"]
            g_data = nc_sig2.plv(spike_train, mode="bs", fwin=[0, 20])
            sta_rsc = g_data["STAm"]
            sfc_rsc = g_data["SFCm"]
            t = g_data["t"]
            f = g_data["f"]

            output[name_for_save] = [sta, sfc, sta_rsc, sfc_rsc, t, f]
            unit.underlying.reset_results()

    return output


def combine_results(info, extra):
    import os
    import simuran
    import seaborn as sns
    from lfp_atn_simuran.analysis.parse_cfg import parse_cfg_info

    cfg = parse_cfg_info()
    base_dir = cfg.get("cfg_base_dir")
    img_format = cfg.get("image_format")

    out_dir, filename = extra
    base, ext = os.path.splitext(os.path.basename(filename))

    here = os.path.dirname(os.path.abspath(__file__))
    cell_list_location = os.path.join(
        here, "..", "cell_lists", "CTRL_Lesion_cells_filled_eeg.xlsx"
    )
    df = pd.read_excel(cell_list_location)

    for out_region in ["sub", "rsc"]:
        new_list1 = []
        new_list2 = []
        for row in info.itertuples():
            dir_ = row.Directory[len(base_dir + os.sep) :]
            group = dir_[0]
            animal_name = dir_.split(os.sep)[0].split("_")[0]
            number = int(animal_name[-1])

            if group == "C":
                group = "Control"
            elif group == "L":
                group = "ATNx (Lesion)"
            else:
                raise ValueError("unsupported group {}".format(group))
            if out_region == "sub":
                sta = row.STA_SUB
                sfc = row.SFC_SUB
            else:
                sta = row.STA_RSC
                sfc = row.SFC_RSC
            t = row.Time
            f = row.Frequency

            spatial = (
                df[
                    (df["Filename"] == row.Filename)
                    & (df["Group"] == row.Group)
                    & (df["Unit"] == row.Unit)
                ]["class"]
                .values.flatten()[0]
                .split("_")[0]
            )
            if group == "ATNx (Lesion)" and spatial == "S":
                raise RuntimeError("Incorrect parsing")

            for i in range(len(sta)):
                new_list1.append([group, float(sta[i]), float(t[i]), spatial])
            for i in range(len(sfc)):
                new_list2.append([group, float(sfc[i]) / 100, float(f[i]), spatial])

        headers1 = ["Group", "STA", "Time (s)", "Spatial"]
        headers2 = ["Group", "SFC", "Frequency (Hz)", "Spatial"]
        df1 = list_to_df(new_list1, headers=headers1)
        df2 = list_to_df(new_list2, headers=headers2)

        simuran.set_plot_style()

        fig, ax = plt.subplots()
        sns.lineplot(
            data=df1, x="Time (s)", y="STA", ax=ax, style="Group", hue="Spatial"
        )
        mc = UnicodeGrabber.get("micro")
        ax.set_ylabel(f"Spike triggered average {mc}V")
        name = f"average_sta_{out_region}"
        fig.savefig(os.path.join(out_dir, name + "." + img_format))
        plt.close(fig)

        fig, ax = plt.subplots()
        sns.lineplot(
            data=df2, x="Frequency (Hz)", y="SFC", ax=ax, style="Group", hue="Spatial"
        )
        ax.set_ylabel("Spike field coherence")
        name = f"average_sfc_{out_region}"
        fig.savefig(os.path.join(out_dir, name + "." + img_format))
        plt.close(fig)

        out_fname = os.path.join(out_dir, base + f"__sta_{out_region}" + ext)
        df1.to_excel(out_fname, index=False)
        out_fname = os.path.join(out_dir, base + f"__sfc_{out_region}" + ext)
        df2.to_excel(out_fname, index=False)
