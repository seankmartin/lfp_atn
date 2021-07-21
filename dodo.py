# For use with Python doit.
import os

from simuran.main.doit import create_task
from skm_pyutils.py_config import read_cfg
from skm_pyutils.py_path import get_all_files_in_dir
from doit.tools import title_with_actions
from doit.task import clean_targets

here = os.path.dirname(os.path.abspath(__file__))
cfg = read_cfg(os.path.join(here, "dodo.cfg"), verbose=False)
num_workers = cfg.get("DEFAULT", "num_workers")
dirname = cfg.get("DEFAULT", "dirname")
main_cfg_path = cfg.get("DEFAULT", "cfg_path")
kwargs = {
    "num_workers": num_workers,
    "dirname": dirname,
    "cfg_path": main_cfg_path,
}


def task_list_openfield():
    return create_task(
        os.path.join(here, "lfp_atn_simuran", "multi_runs", "run_openfield.py"),
        ["fn_list_recordings.py"],
        reason="List the recordings that are analysed in openfield.",
        **kwargs
    )


def task_coherence():
    return create_task(
        os.path.join(here, "lfp_atn_simuran", "multi_runs", "run_coherence.py"),
        ["plot_coherence.py"],
        reason="Analyse coherence between SUB and RSC in the openfield data.",
        **kwargs,
    )


def task_lfp_plot():
    return create_task(
        os.path.join(here, "lfp_atn_simuran", "multi_runs", "run_lfp_plot.py"),
        ["plot_lfp_eg.py"],
        reason="Plot first 100s of each recording in openfield for LFP inspection.",
        **kwargs,
    )


def task_lfp_power():
    return create_task(
        os.path.join(here, "lfp_atn_simuran", "multi_runs", "run_spectra.py"),
        ["simuran_theta_power.py"],
        reason="Power analysis within the openfield in SUB and RSC.",
        **kwargs,
    )


def task_lfp_rate():
    return create_task(
        os.path.join(here, "lfp_atn_simuran", "multi_runs", "run_lfp_rate.py"),
        ["simuran_lfp_rate.py"],
        reason="Rate maps of LFP (like a firing map, but with LFP amplitude).",
        **kwargs,
    )


def task_lfp_speed():
    return create_task(
        os.path.join(here, "lfp_atn_simuran", "multi_runs", "run_speed_theta.py"),
        ["speed_lfp.py"],
        reason="Relation of LFP power and speed in openfield.",
        **kwargs,
    )


def task_speed_ibi():
    base_ = os.path.join(here, "lfp_atn_simuran", "cell_lists")
    dependencies = [
        os.path.join(base_, "CTRL_Lesion_cells_filled.xlsx"),
        os.path.join(base_, "list_spike_ibi.py"),
    ]
    dir_ = os.path.join(here, "lfp_atn_simuran", "sim_results", "list_spike_ibi")
    if os.path.exists(dir_):
        targets = get_all_files_in_dir(dir_, return_absolute=True)
    else:
        targets = []

    location = os.path.abspath(os.path.join(base_, "list_spike_ibi.py"))
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

def task_spike_lfp():
    base_ = os.path.join(here, "lfp_atn_simuran", "cell_lists")
    dependencies = [
        os.path.join(base_, "CTRL_Lesion_cells_filled.xlsx"),
        os.path.join(base_, "list_spike_lfp.py"),
    ]
    dir_ = os.path.join(here, "lfp_atn_simuran", "sim_results", "list_spike_lfp")
    if os.path.exists(dir_):
        targets = get_all_files_in_dir(dir_, return_absolute=True)
    else:
        targets = []

    location = os.path.abspath(os.path.join(base_, "list_spike_lfp.py"))
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