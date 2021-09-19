# For use with Python doit.
import os

from simuran.main.doit import create_task, create_list_task
from skm_pyutils.py_config import read_cfg
from doit.tools import title_with_actions
from doit.task import clean_targets

here = os.path.dirname(os.path.abspath(__file__))
cfg = read_cfg(os.path.join(here, "dodo.cfg"), verbose=False)
num_workers = cfg.getint("DEFAULT", "num_workers")
dirname = cfg.get("DEFAULT", "dirname")
main_cfg_path = cfg.get("DEFAULT", "cfg_path")
overwrite = cfg.getboolean("DEFAULT", "overwrite")
save = cfg.getboolean("DEFAULT", "save")
kwargs = {
    "num_workers": num_workers,
    "dirname": dirname,
    "cfg_path": main_cfg_path,
    "overwrite": overwrite,
    "save": save,
}


def task_list_openfield():
    return create_task(
        os.path.join(here, "lfp_atn_simuran", "multi_runs", "run_openfield.py"),
        ["fn_list_recordings.py", "lfp_clean.py"],
        reason="List the recordings that are analysed in openfield.",
        **kwargs,
    )


def task_coherence():
    return create_task(
        os.path.join(here, "lfp_atn_simuran", "multi_runs", "run_coherence.py"),
        ["fn_coherence.py", "lfp_clean.py"],
        reason="Analyse coherence between SUB and RSC in the openfield data.",
        **kwargs,
    )


# def task_lfp_plot():
#     return create_task(
#         os.path.join(here, "lfp_atn_simuran", "multi_runs", "run_lfp_plot.py"),
#         ["fn_plot_lfp.py", "lfp_clean.py"],
#         reason="Plot first 100s of each recording in openfield for LFP inspection.",
#         **kwargs,
#     )


def task_lfp_power():
    return create_task(
        os.path.join(here, "lfp_atn_simuran", "multi_runs", "run_spectra.py"),
        ["fn_spectra.py", "lfp_clean.py"],
        reason="Power analysis within the openfield in SUB and RSC.",
        **kwargs,
    )


# def task_lfp_rate():
#     return create_task(
#         os.path.join(here, "lfp_atn_simuran", "multi_runs", "run_lfp_rate.py"),
#         ["fn_lfp_rate.py", "lfp_clean.py"],
#         reason="Rate maps of LFP (like a firing map, but with LFP amplitude).",
#         **kwargs,
#     )


def task_lfp_speed():
    return create_task(
        os.path.join(here, "lfp_atn_simuran", "multi_runs", "run_speed_theta.py"),
        ["fn_speed_theta.py", "lfp_clean.py"],
        reason="Relation of LFP power and speed in openfield.",
        **kwargs,
    )


def task_speed_ibi():
    return create_list_task(
        os.path.join(here, "lfp_atn_simuran", "multi_runs", "run_speed_ibi.py"),
        ["speed_ibi.py"],
        reason="Speed to IBI and firing rate relationship.",
        **kwargs,
    )


def task_spike_lfp():
    return create_list_task(
        os.path.join(here, "lfp_atn_simuran", "multi_runs", "run_spike_lfp.py"),
        ["spike_lfp.py", "lfp_clean.py"],
        reason="Spike to LFP relationship.",
        **kwargs,
    )


def task_tmaze():
    base_ = os.path.join(here, "lfp_atn_simuran", "tmaze")
    dependencies = [
        os.path.join(base_, "results", "tmaze-times.xlsx"),
        os.path.join(base_, "tmaze_analyse.py"),
    ]
    targets = [os.path.join(base_, "results", "tmaze-times_results.xlsx")]

    location = os.path.abspath(os.path.join(base_, "tmaze_analyse.py"))
    action = f"python {location}"

    return {
        "file_dep": dependencies,
        "targets": targets,
        "actions": [action],
        "clean": [clean_targets],
        "title": title_with_actions,
        "verbosity": 0,
        "doc": action,
    }


def task_muscimol_sta():
    return create_list_task(
        os.path.join(
            here, "lfp_atn_simuran", "multi_runs", "run_spike_lfp_muscimol.py"
        ),
        ["spike_lfp.py", "lfp_clean.py"],
        reason="Spike to LFP relationship in muscimol data.",
        **kwargs,
    )


def task_summarise_results():
    base_ = here
    dependencies = [
        os.path.join(base_, "summarise_results.py"),
    ]
    targets = [os.path.join(here, "results.txt")]

    location = os.path.abspath(os.path.join(base_, "summarise_results.py"))
    action = f"python {location}"

    return {
        "file_dep": dependencies,
        "targets": targets,
        "actions": [action],
        "clean": [clean_targets],
        "title": title_with_actions,
        "verbosity": 0,
        "doc": action,
    }


def task_stats():
    base_ = here
    dependencies = [
        os.path.join(base_, "summarise_results.py"),
        os.path.join(base_, "run_stats.py"),
    ]
    targets = []

    location = os.path.abspath(os.path.join(base_, "run_stats.py"))
    action = f"python {location}"

    return {
        "file_dep": dependencies,
        "targets": targets,
        "actions": [action],
        "clean": [clean_targets],
        "title": title_with_actions,
        "verbosity": 0,
        "doc": action,
    }