"""simuran_batch_params.py describes behaviour for recursing through directories."""

import os
from lfp_atn_simuran.analysis.speed_ibi import (
    recording_speed_ibi,
    recording_ibi_headings,
    combine_results
)

# The magic string __dirname__, is replaced by a directory name that is passed through command line
dirname = "__dirname__"
# The magic string __thisdirname__ is also available, which is replaced by the directory that this file is in.
this_dirname = "__thisdirname__"

# The path to the cell list location
cell_list_path = os.path.abspath(
    os.path.join(this_dirname, "..", "cell_lists", "CTRL_Lesion_cells_filled.xlsx")
)

# The function to run on each recording in the cell list
# This is required
fn_to_run = recording_speed_ibi

# The function to run after analysing the cell lists
# This can be left as None
after_fn = combine_results

# out_dir can be left as None to automatically name
out_dir = os.path.abspath(
    os.path.join(this_dirname, "..", "sim_results", "spike_ibi")
)

# Arguments to pass into fn_to_run
fn_args = [out_dir, dirname]

# Keyword arguments to pass into fn_to_run
# By default these are added to the config file chosen
fn_kwargs = {}

# Headers for the output
headers = recording_ibi_headings()

params = {
    "cell_list_path": cell_list_path,
    "function_to_run": fn_to_run,
    "after_fn": after_fn,
    "headers": headers,
    "out_dir": out_dir,
    "fn_args": fn_args,
    "fn_kwargs": fn_kwargs,
}