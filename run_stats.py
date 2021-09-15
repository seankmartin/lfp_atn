"""
Grab the output CSV files and run stats on them.

See lfp_atn_simuran/jasp_stats for equivalent JASP tests.
"""
import os
from skm_pyutils.py_table import df_from_file
from skm_pyutils.py_stats import mwu, corr
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

    corr(
        control_df["SUB_theta_rel"],
        control_df["results_speed_lfp_amp_mean_speed"],
        fmt_kwargs=t1_kwargs,
        do_plot=True,
        method="spearman",
    )

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

    corr(
        lesion_df["SUB_theta_rel"],
        lesion_df["results_speed_lfp_amp_mean_speed"],
        fmt_kwargs=t2_kwargs,
        do_plot=True,
        method="spearman",
    )


def ibi_stats(overall_kwargs):
    return
    pt("Open field speed IBI")
    df, control_df, lesion_df = get_df(
        "spike_ibi--CTRL_Lesion_cells_filled_recording_speed_ibi_results.csv"
    )

    # Remove instances of no bursting
    col_name = "Number of bursts"
    control_df = control_df[control_df[col_name].fillna(0) > 1]
    lesion_df = lesion_df[lesion_df[col_name].fillna(0) > 1]

    t1_kwargs = {
        **overall_kwargs,
        **{"value": "theta coherence (unitless)"},
    }

    corr(
        control_df["SUB_theta_rel"],
        control_df["results_speed_lfp_amp_mean_speed"],
        t1_kwargs,
    )

    t2_kwargs = {
        **overall_kwargs,
        **{"value": "theta coherence (unitless)"},
    }

    corr(
        lesion_df["SUB_theta_rel"],
        lesion_df["results_speed_lfp_amp_mean_speed"],
        t2_kwargs,
    )


def main(show_quartiles=False):
    overall_kwargs_ttest = {
        "show_quartiles": show_quartiles,
        "group1": "control",
        "group2": "ATNx",
    }

    overall_kwargs_corr = {
        "show_quartiles": show_quartiles,
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

    # 6.


if __name__ == "__main__":
    main(True)
