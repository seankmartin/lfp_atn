"""
Grab the output CSV files and run stats on them.

See lfp_atn_simuran/jasp_stats for equivalent JASP tests.
"""
import os
from skm_pyutils.py_table import df_from_file
from skm_pyutils.py_stats import mwu

here = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(here, "lfp_atn_simuran", "sim_results")
summary_location = os.path.join(results_dir, "merged_results")


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


def main(show_quartiles=False):
    
    # 1. Power overall
    df, control_df, lesion_df = get_df("fn_spectra--merge--fn_spectra.csv")

    overall_kwargs = {
        "show_quartiles": show_quartiles,
        "group1": "control",
        "group2": "ATNx",
    }
    t1_kwargs = {
        **overall_kwargs,
        **{"value": "subicular relative theta powers (unitless)"},
    }
    res = mwu(control_df["SUB_theta_rel"], lesion_df["SUB_theta_rel"], t1_kwargs)
    t2_kwargs = {
        **overall_kwargs,
        **{"value": "retrospenial relative theta powers (unitless)"},
    }
    res = mwu(control_df["RSC_theta_rel"], lesion_df["RSC_theta_rel"], t2_kwargs)


if __name__ == "__main__":
    main()
