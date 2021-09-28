import dodo
import os
import shutil
import csv

from skm_pyutils.py_table import df_from_file, df_to_file
from skm_pyutils.py_pdf import pdf_cat
from skm_pyutils.py_config import read_cfg

here = os.path.dirname(os.path.abspath(__file__))
output_location = os.path.join(here, "results.txt")
out_file = open(output_location, "w")
results_dir = os.path.join(here, "lfp_atn_simuran", "sim_results")
summary_location = os.path.join(results_dir, "summary")


def out(msg):
    print(msg)
    out_file.write(msg + "\n")


def describe_task(task_name, info_dict, all_files):
    out(f"{task_name}")
    task_info = dodo.__dict__[task_name]()

    if "dfs" not in info_dict:
        dfs = []
        for f in task_info["file_dep"]:
            if os.path.basename(f).startswith("fn_"):
                dfs.append(os.path.splitext(os.path.basename(f))[0])
        dfs = [os.path.join(results_dir, name, f"merge--{name}.csv") for name in dfs]
    else:
        dfs = info_dict["dfs"]

    if "reason" not in info_dict:
        try:
            reason_str = task_info["doc"].split("--reason ")[-1].split('"')[1]
        except IndexError:
            reason_str = "Unknown reason"
    else:
        reason_str = info_dict["reason"]
    out(f"\tPurpose -- {reason_str}")

    if len(dfs) > 0:
        out("\tMain dataframes")
    for df_loc in dfs:
        out(f"\t\t{df_loc}")
        df = df_from_file(df_loc)
        headers = df.columns.values
        out("\t\tHeaders")
        for h in headers:
            out(f"\t\t\t{h}")
        all_files.append(df_loc)
    if "figs" in info_dict.keys():
        out("\tMain figures")
        for fig_loc in info_dict["figs"]:
            out(f"\t\t{fig_loc}")
            all_files.append(fig_loc)


def main():
    print(
        "Will save summary information to {} and print it also".format(output_location)
    )

    all_tasks = [d for d in dodo.__dict__.keys() if d.startswith("task")]

    id_ = {}

    ## Coherence in open field
    fig_list = [
        os.path.join(summary_location, "run_coherence.pdf"),
        os.path.join(summary_location, "run_coherence_ci.pdf"),
    ]
    df_list = [
        os.path.join(results_dir, "fn_coherence", "merge--fn_coherence.csv"),
    ]
    id_["task_coherence"] = {"figs": fig_list, "dfs": df_list}

    ## LFP power results in openfield
    fig_list = [
        os.path.join(summary_location, "run_spectra--foof--RSCcombined.pdf"),
        os.path.join(summary_location, "run_spectra--foof--SUBcombined.pdf"),
        os.path.join(summary_location, "run_spectra--rsc--power.pdf"),
        os.path.join(summary_location, "run_spectra--rsc--power_ci.pdf"),
        os.path.join(summary_location, "run_spectra--sub--power.pdf"),
        os.path.join(summary_location, "run_spectra--sub--power_ci.pdf"),
        os.path.join(results_dir, "saved", "ca1_power_final.pdf"),
        os.path.join(results_dir, "saved", "ca1_power_final_ci.pdf"),
    ]
    df_list = [
        os.path.join(results_dir, "fn_spectra", "merge--fn_spectra.csv"),
        os.path.join(results_dir, "saved", "ca1_power_results.csv"),
    ]
    id_["task_lfp_power"] = {"figs": fig_list, "dfs": df_list}

    ## Speed to LFP power relationship
    fig_list = [
        os.path.join(summary_location, "run_speed_theta--sub--speed--theta_ci.pdf"),
        os.path.join(summary_location, "run_speed_theta--rsc--speed--theta_ci.pdf"),
    ]
    df_list = [
        os.path.join(results_dir, "fn_speed_theta", "merge--fn_speed_theta.csv"),
    ]
    id_["task_lfp_speed"] = {"figs": fig_list}

    ## Speed IBI
    df_list = [
        os.path.join(
            results_dir,
            "spike_ibi",
            "CTRL_Lesion_cells_filled_recording_speed_ibi_results.csv",
        )
    ]
    fig_list = [os.path.join(summary_location, "Speed_IBI_Median.pdf")]
    id_["task_speed_ibi"] = {"figs": fig_list, "dfs": df_list}

    ## Spike LFP
    df_list = [
        os.path.join(
            results_dir,
            "spike_lfp",
            "CTRL_Lesion_cells_filled_eeg_recording_spike_lfp_results.csv",
        ),
        os.path.join(
            results_dir,
            "spike_lfp",
            "CTRL_Lesion_cells_filled_eeg__sfc_sub.csv",
        ),
    ]
    fig_list = [
        os.path.join(results_dir, "spike_lfp", "average_sfc_sub.pdf"),
        os.path.join(results_dir, "spike_lfp", "average_sfc_shuffled_sub.pdf"),
        os.path.join(results_dir, "spike_lfp", "average_sta_sub.pdf"),
        os.path.join(results_dir, "spike_lfp", "average_sfc_rsc.pdf"),
    ]
    id_["task_spike_lfp"] = {"figs": fig_list, "dfs": df_list}

    ## Tmaze
    df_list = [
        os.path.join(results_dir, "tmaze", "tmaze-times_results.csv"),
        os.path.join(results_dir, "tmaze", "coherence_full.csv"),
    ]
    fig_list = [
        os.path.join(results_dir, "tmaze", "Control--coherence_ci.pdf"),
        os.path.join(results_dir, "tmaze", "Control--coherence.pdf"),
        os.path.join(results_dir, "tmaze", "Control--power_ci.pdf"),
        os.path.join(results_dir, "tmaze", "Lesion (ATNx)--coherence_ci.pdf"),
        os.path.join(results_dir, "tmaze", "Lesion (ATNx)--coherence.pdf"),
        os.path.join(results_dir, "tmaze", "Lesion (ATNx)--power_ci.pdf"),
        os.path.join(results_dir, "tmaze", "bar--coherence.pdf"),
        os.path.join(results_dir, "tmaze", "choice_coherence_ci.pdf"),
        os.path.join(results_dir, "tmaze", "bar--coherence--delta.pdf"),
        os.path.join(results_dir, "tmaze", "choice_power_ci.pdf"),
    ]
    tmaze_dict = {
        "reason": "T-maze coherence around decision time.",
        "figs": fig_list,
        "dfs": df_list,
    }
    id_["task_tmaze"] = tmaze_dict

    ## Muscimol
    df_list = [
        os.path.join(
            results_dir,
            "spike_lfp_musc",
            "musc_cells_grab_recording_spike_lfp_results.csv",
        ),
        os.path.join(
            results_dir,
            "spike_lfp_musc",
            "musc_cells_grab__sfc_sub.csv",
        ),
    ]
    fig_list = [
        os.path.join(results_dir, "spike_lfp_musc", "average_sfc_sub.pdf"),
        os.path.join(results_dir, "spike_lfp_musc", "average_sfc_rsc.pdf"),
    ]
    musc_dict = {
        "figs": fig_list,
        "dfs": df_list,
    }
    id_["task_muscimol_sta"] = musc_dict

    all_files = []
    for task in all_tasks:
        describe_task(task, id_.get(task, {}), all_files)
    out_file.close()

    out_loc_merge = os.path.join(results_dir, "merged_results")
    os.makedirs(out_loc_merge, exist_ok=True)
    pdf_files = [fname for fname in all_files if os.path.splitext(fname)[-1] == ".pdf"]

    pdf_merge_loc = os.path.join(out_loc_merge, "merged_results.pdf")
    pdf_cat(pdf_files, pdf_merge_loc)

    here = os.path.dirname(os.path.abspath(__file__))
    cfg = read_cfg(os.path.join(here, "dodo.cfg"), verbose=False)
    dirname = cfg.get("DEFAULT", "dirname")
    for f in all_files:
        base_part = os.path.dirname(f)[len(results_dir + os.sep) :].replace(
            os.sep, "--"
        )
        out_loc_merge_file = os.path.join(
            out_loc_merge, base_part + "--" + os.path.basename(f)
        )
        if os.path.splitext(out_loc_merge_file)[-1] == ".csv":
            out_str = ""
            with open(f, "r") as file:
                csvreader = csv.reader(file, delimiter=",", quotechar='"')
                for i, row in enumerate(csvreader):
                    if i == 0:
                        l1 = row
                        out_str += ",".join(row) + ",Condition" + "\n"
                    elif len(row) == 0:
                        continue
                    elif row[0] == "Average" or row[0] == "Std" or row == l1:
                        continue
                    else:
                        fpath = row[0]
                        if "tmaze" in os.path.basename(f):
                            fpath_without_base = fpath
                        else:
                            fpath_without_base = fpath[len(dirname + os.sep) :]
                        if fpath_without_base.startswith("C"):
                            condition = "Control"
                        elif fpath_without_base.startswith("L"):
                            condition = "Lesion"
                        elif fpath_without_base.startswith("m"):
                            condition = "Muscimol"
                        else:
                            condition = "Unkown"

                        for j in range(len(row)):
                            if row[j].startswith("["):
                                row[j] = "Removed"
                        out_str += ",".join(row) + f",{condition}\n"

            with open(out_loc_merge_file, "w") as file:
                file.write(out_str[:-1])
        else:
            shutil.copy(f, out_loc_merge_file)

    f1 = os.path.join(out_loc_merge, "fn_spectra--merge--fn_spectra.csv")
    f2 = os.path.join(out_loc_merge, "fn_speed_theta--merge--fn_speed_theta.csv")

    df1 = df_from_file(f1).drop(["Condition"], axis=1)
    df2 = df_from_file(f2)

    merged_df = df1.merge(df2, on=["Recording_directory", "Recording_name"])
    df_to_file(merged_df, os.path.join(out_loc_merge, "merged_speed.csv"))


if __name__ == "__main__":
    main()
