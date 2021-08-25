import os

import simuran
from skm_pyutils.py_path import get_all_files_in_dir
from skm_pyutils.py_table import list_to_df

def main(start_dir, map_file):

    # def sorting_fn(x):
    #     in_dir = start_dir
    #     comp = x.source_file[len(in_dir) + 2 :]
    #     return comp

    # here = os.path.abspath(os.path.dirname(__file__))
    # mapping_dir = os.path.join(here, "..", "recording_mappings")

    # df = simuran.index_ephys_files(
    #     start_dir,
    #     loader_name="nc_loader",
    #     loader_kwargs={"system": "Axona", "pos_extension": ".pos"},
    # )
    # df["mapping"] = [map_file] * len(df)
    # container = simuran.recording_container_from_df(
    #     df, base_dir=start_dir, param_dir=mapping_dir
    # )
    # container.sort(sorting_fn)
    # container.print_units(f=os.path.join(start_dir, "full_cell_list.txt"))

    # cells_to_analyse = container.select_cells()
    cells_to_analyse = simuran.dir_to_table(start_dir)
    cells_to_analyse.to_csv(os.path.join(start_dir, "musc_cells_grab.csv"))

if __name__ == "__main__":
    main_start_dir = (
        r"D:\SubRet_recordings_imaging\muscimol_data"
    )
    main_map_file = "CanCSR.py"

    main(main_start_dir, main_map_file)
