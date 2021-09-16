"""
Grab the output CSV files and run stats on them.

See lfp_atn_simuran/jasp_stats for equivalent JASP tests.
"""
import os
from skm_pyutils.py_table import df_from_file
from skm_pyutils.py_stats import mwu, corr, wilcoxon
import matplotlib.pyplot as plt

here = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(here, "lfp_atn_simuran", "sim_results")
summary_location = os.path.join(results_dir, "merged_results")
plot_dir = os.path.join(results_dir, "merged_results", "stats_plots")
os.makedirs(plot_dir, exist_ok=True)


def pt(title, n_dashes=20, start="\n"):
    str_ = "-" * n_dashes + title + "-" * n_dashes
    print(start + str_)


def get_df(filename, describe=False):
    full_fname = os.path.join(summary_location, filename)
    df = df_from_file(full_fname)
    if describe:
        print("Processing {}".format(filename))
        print("Overall")
        print(df.describe())

    try:
        control_df = df[df["Condition"] == "Control"]
        lesion_df = df[df["Condition"] == "Lesion"]
    except KeyError:
        return df

    if describe:
        print("Processing {}".format(filename))
        print("Overall")
        print(df.describe())
        print("Control")
        print(control_df.describe())

        print("Lesion")
        print(lesion_df.describe())

    return df, control_df, lesion_df

def get_musc_df(filename, describe=False):
    full_fname = os.path.join(summary_location, filename)
    df = df_from_file(full_fname)
    if describe:
        print("Processing {}".format(filename))
        print("Overall")
        print(df.describe())

    def process_condition(row):
        to_check = row["Spatial"]
        if "before" in to_check or "next" in to_check:
            return "Control"
        else:
            return "Muscimol"

    df["group"] = df.apply(lambda row: process_condition(row), axis=1)

    try:
        control_df = df[df["group"] == "Control"]
        lesion_df = df[df["group"] == "Muscimol"]
    except KeyError:
        return df

    if describe:
        print("Processing {}".format(filename))
        print("Overall")
        print(df.describe())
        print("Control")
        print(control_df.describe())

        print("Lesion")
        print(lesion_df.describe())

    return df, control_df, lesion_df


def process_fig(res, name):
    fig = res["figure"]
    fig.savefig(os.path.join(plot_dir, name), dpi=400)
    plt.close(fig)


def power_stats(overall_kwargs):
    pt("Open field power", start="")
    df, control_df, lesion_df = get_df("fn_spectra--merge--fn_spectra.csv")

    t1_kwargs = {
        **overall_kwargs,
        **{"value": "subicular relative theta powers (unitless)"},
    }
    res = mwu(
        control_df["SUB_theta_rel"], lesion_df["SUB_theta_rel"], t1_kwargs, do_plot=True
    )
    process_fig(res, "sub_theta_openfield.pdf")

    t2_kwargs = {
        **overall_kwargs,
        **{"value": "retrospenial relative theta powers (unitless)"},
    }
    res = mwu(
        control_df["RSC_theta_rel"], lesion_df["RSC_theta_rel"], t2_kwargs, do_plot=True
    )
    process_fig(res, "rsc_theta_openfield.pdf")


def coherence_stats(overall_kwargs):
    pt("Open field coherence")
    df, control_df, lesion_df = get_df("fn_coherence--merge--fn_coherence.csv")

    t1_kwargs = {
        **overall_kwargs,
        **{"value": "theta coherence (unitless)"},
    }
    res = mwu(
        control_df["Theta_Coherence"],
        lesion_df["Theta_Coherence"],
        t1_kwargs,
        do_plot=True,
    )
    process_fig(res, "theta_coherence_openfield.pdf")

    t2_kwargs = {
        **overall_kwargs,
        **{"value": "delta coherence (unitless)"},
    }
    res = mwu(
        control_df["Delta_Coherence"],
        lesion_df["Delta_Coherence"],
        t2_kwargs,
        do_plot=True,
    )
    process_fig(res, "delta_coherence_openfield.pdf")


def speed_stats(overall_kwargs):
    pt("Open field Speed LFP power relationship")
    df, control_df, lesion_df = get_df("merged_speed.csv")

    t1_kwargs = {
        **overall_kwargs,
        **{
            "group": "in control",
            "value1": "mean speed (cm/s)",
            "value2": "relative subicular theta power (unitless)",
            "trim": True,
            "offset": 0,
        },
    }
    res = corr(
        control_df["SUB_theta_rel"],
        control_df["results_speed_lfp_amp_mean_speed"],
        fmt_kwargs=t1_kwargs,
        do_plot=True,
        method="spearman",
    )
    process_fig(res, "control_speed_corr.pdf")

    t2_kwargs = {
        **overall_kwargs,
        **{
            "group": "in ATNx",
            "value1": "mean speed (cm/s)",
            "value2": "relative subicular theta power (unitless)",
            "trim": True,
            "offset": 0,
        },
    }
    res = corr(
        lesion_df["SUB_theta_rel"],
        lesion_df["results_speed_lfp_amp_mean_speed"],
        fmt_kwargs=t2_kwargs,
        do_plot=True,
        method="spearman",
    )
    process_fig(res, "lesion_speed_corr.pdf")


def ibi_stats(overall_kwargs):
    pt("Open field speed IBI")
    df, control_df, lesion_df = get_df(
        "spike_ibi--CTRL_Lesion_cells_filled_recording_speed_ibi_results.csv"
    )

    # Remove instances of no bursting
    col_name = "Number of bursts"
    control_df = control_df[control_df[col_name].fillna(0) > 1]
    lesion_df = lesion_df[lesion_df[col_name].fillna(0) > 1]

    speed_name = "Mean IBI Speed"
    speed_name = "Mean speed"

    t1_kwargs = {
        **overall_kwargs,
        **{
            "group": "in control",
            "value1": "mean speed (cm/s)",
            "value2": "median IBI (s)",
            "trim": True,
            "offset": 0,
        },
    }
    res = corr(
        control_df[speed_name],
        control_df["Median IBI"],
        t1_kwargs,
        do_plot=True,
        method="spearman",
    )
    process_fig(res, "control_ibi_corr.pdf")

    t2_kwargs = {
        **overall_kwargs,
        **{
            "group": "in ATNx",
            "value1": "mean speed (cm/s)",
            "value2": "median IBI (s)",
            "trim": True,
            "offset": 0,
        },
    }
    res = corr(
        lesion_df[speed_name],
        lesion_df["Median IBI"],
        t2_kwargs,
        do_plot=True,
        method="spearman",
    )
    process_fig(res, "lesion_ibi_corr.pdf")


def spike_lfp_stats(overall_kwargs):
    pt("Spike LFP openfield")
    df, control_df, lesion_df = get_df(
        "spike_lfp--CTRL_Lesion_cells_filled_eeg_recording_spike_lfp_results.csv"
    )
    control_nspatial_spikes = control_df[control_df["Spatial"] == "NS"]

    t1_kwargs = {
        **overall_kwargs,
        **{
            "value": "subicular theta spike field coherence for non-spatially tuned cells (percent)"
        },
    }

    res = mwu(
        control_nspatial_spikes["Theta_SFC_SUB"],
        lesion_df["Theta_SFC_SUB"],
        t1_kwargs,
        do_plot=True,
    )
    process_fig(res, "sub_sfc.pdf")

    t2_kwargs = {
        **overall_kwargs,
        **{
            "value": "retrospenial theta spike field coherence for non-spatially tuned cells (percent)"
        },
    }

    res = mwu(
        control_nspatial_spikes["Theta_RSC_SUB"],
        lesion_df["Theta_RSC_SUB"],
        t2_kwargs,
        do_plot=True,
    )
    process_fig(res, "rsc_sfc.pdf")

    t3_kwargs = {
        **overall_kwargs,
        **{"value": "subicular theta phase (degrees)"},
    }

    res = mwu(
        control_nspatial_spikes["Mean_Phase_SUB"],
        lesion_df["Mean_Phase_SUB"],
        t3_kwargs,
        do_plot=True,
    )
    process_fig(res, "sub_phase.pdf")

    t4_kwargs = {
        **overall_kwargs,
        **{"value": "retrospenial theta phase (degrees)"},
    }

    res = mwu(
        control_nspatial_spikes["Mean_Phase_RSC"],
        lesion_df["Mean_Phase_RSC"],
        t4_kwargs,
        do_plot=True,
    )
    process_fig(res, "rsc_phase.pdf")


def tmaze_stats(overall_kwargs):
    df, control_df, lesion_df = get_df("tmaze--tmaze-times_results.csv")
    bit_to_get = (control_df["part"] == "choice") & (
        control_df["trial"] == "choice_correct"
    )
    control_choice = control_df[bit_to_get]

    bit_to_get = (lesion_df["part"] == "choice") & (
        lesion_df["trial"] == "choice_correct"
    )
    lesion_choice = lesion_df[bit_to_get]

    t1_kwargs = {
        **overall_kwargs,
        **{
            "value": "subicular to retronspenial LFP theta coherence during correct trials"
        },
    }

    res = mwu(
        control_choice["Theta_coherence"],
        lesion_choice["Theta_coherence"],
        t1_kwargs,
        do_plot=True,
    )
    process_fig(res, "t-maze_coherence_correct.pdf")

    t1a_kwargs = {
        **overall_kwargs,
        **{"value": "subicular LFP theta power during correct trials"},
    }

    res = mwu(
        control_choice["SUB_theta"],
        lesion_choice["SUB_theta"],
        t1a_kwargs,
        do_plot=True,
    )
    process_fig(res, "t-maze_subpower_correct.pdf")

    bit_to_get = (control_df["part"] == "choice") & (
        control_df["trial"] == "choice_errors"
    )
    control_choice = control_df[bit_to_get]

    bit_to_get = (lesion_df["part"] == "choice") & (
        lesion_df["trial"] == "choice_errors"
    )
    lesion_choice = lesion_df[bit_to_get]

    t2_kwargs = {
        **overall_kwargs,
        **{
            "value": "subicular to retronspenial LFP theta coherence during incorrect trials"
        },
    }

    res = mwu(
        control_choice["Theta_coherence"],
        lesion_choice["Theta_coherence"],
        t2_kwargs,
        do_plot=True,
    )
    process_fig(res, "t-maze_coherence_incorrect.pdf")

    t2a_kwargs = {
        **overall_kwargs,
        **{"value": "subicular LFP theta power during incorrect trials"},
    }

    res = mwu(
        control_choice["SUB_theta"],
        lesion_choice["SUB_theta"],
        t2a_kwargs,
        do_plot=True,
    )
    process_fig(res, "t-maze_subpower_incorrect.pdf")

    bit_to_get = (control_df["part"] == "choice") & (
        control_df["trial"] == "choice_correct"
    )
    control_choice1 = control_df[bit_to_get]

    bit_to_get = (control_df["part"] == "choice") & (
        control_df["trial"] == "choice_errors"
    )
    control_choice2 = control_df[bit_to_get]

    t3_kwargs = (
        {
            "value": "subicular to retronspenial LFP theta coherence during choice trials in control",
            "group1": "correct",
            "group2": "incorrect",
            "show_quartiles": overall_kwargs["show_quartiles"],
        },
    )

    res = wilcoxon(
        control_choice1["Theta_coherence"],
        control_choice2["Theta_coherence"],
        t3_kwargs,
        do_plot=True,
    )
    process_fig(res, "t-maze_coherence_ctrl.pdf")

    bit_to_get = (lesion_df["part"] == "choice") & (
        lesion_df["trial"] == "choice_correct"
    )
    lesion_choice1 = lesion_df[bit_to_get]

    bit_to_get = (lesion_df["part"] == "choice") & (
        lesion_df["trial"] == "choice_errors"
    )
    lesion_choice2 = lesion_df[bit_to_get]

    t4_kwargs = (
        {
            "value": "subicular to retronspenial LFP theta coherence during choice trials in ATNx",
            "group1": "correct",
            "group2": "incorrect",
            "show_quartiles": overall_kwargs["show_quartiles"],
        },
    )

    res = wilcoxon(
        lesion_choice1["Theta_coherence"],
        lesion_choice2["Theta_coherence"],
        t4_kwargs,
        do_plot=True,
    )
    process_fig(res, "t-maze_coherence_lesion.pdf")


def muscimol_stats(overall_kwargs):
    pt("Spike LFP muscimol")
    df, control_df, lesion_df = get_df(
        "spike_lfp--CTRL_Lesion_cells_filled_eeg_recording_spike_lfp_results.csv"
    )

    t1_kwargs = {
        **overall_kwargs,
        **{
            "value": "subicular theta spike field coherence (percent)"
        },
    }

    res = mwu(
        control_df["Theta_SFC_SUB"],
        lesion_df["Theta_SFC_SUB"],
        t1_kwargs,
        do_plot=True,
    )
    process_fig(res, "sub_sfc_musc.pdf")

    t2_kwargs = {
        **overall_kwargs,
        **{
            "value": "retrospenial theta spike field coherence (percent)"
        },
    }

    res = mwu(
        control_df["Theta_RSC_SUB"],
        lesion_df["Theta_RSC_SUB"],
        t2_kwargs,
        do_plot=True,
    )
    process_fig(res, "rsc_sfc_musc.pdf")

    t3_kwargs = {
        **overall_kwargs,
        **{"value": "subicular theta phase (degrees)"},
    }

    res = mwu(
        control_df["Mean_Phase_SUB"],
        lesion_df["Mean_Phase_SUB"],
        t3_kwargs,
        do_plot=True,
    )
    process_fig(res, "sub_phase_musc.pdf")

    t4_kwargs = {
        **overall_kwargs,
        **{"value": "retrospenial theta phase (degrees)"},
    }

    res = mwu(
        control_df["Mean_Phase_RSC"],
        lesion_df["Mean_Phase_RSC"],
        t4_kwargs,
        do_plot=True,
    )
    process_fig(res, "rsc_phase_musc.pdf")


def main(show_quartiles=False):
    overall_kwargs_ttest = {
        "show_quartiles": show_quartiles,
        "group1": "control",
        "group2": "ATNx",
    }

    overall_kwargs_corr = {
        "show_quartiles": show_quartiles,
    }

    overall_kwargs_musc = {
        "show_quartiles": show_quartiles,
        "group1": "before muscimol",
        "group2": "after muscimol",
    }

    # 1. Power overall
    power_stats(overall_kwargs_ttest)

    # 2. Coherence in the open-field
    coherence_stats(overall_kwargs_ttest)

    # 3. Speed to LFP power relationship
    speed_stats(overall_kwargs_corr)

    # 4. Speed to IBI
    ibi_stats(overall_kwargs_corr)

    # 5. STA in openfield
    spike_lfp_stats(overall_kwargs_ttest)

    # 6. T-maze
    tmaze_stats(overall_kwargs_ttest)

    #7. Muscimol stats
    muscimol_stats(overall_kwargs_musc)


if __name__ == "__main__":
    main(True)
