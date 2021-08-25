import os

import simuran
from skm_pyutils.py_path import get_all_files_in_dir
from skm_pyutils.py_table import list_to_df, df_to_file, df_from_file

def main(start_dir, map_file):

    # def sorting_fn(x):
    #     in_dir = start_dir
    #     comp = x.source_file[len(in_dir) + 2 :]
    #     return comp

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

    here = os.path.abspath(os.path.dirname(__file__))
    out_loc = os.path.join(here, "..", "cell_lists", "musc_cells_grab.csv")
    # cells_to_analyse = container.select_cells()
    if not os.path.exists(out_loc):
        cells_to_analyse = simuran.dir_to_table(start_dir)
    else:
        cells_to_analyse = df_from_file(out_loc)

    # Fill in the mappings
    mapping_dict = {
        "CanCSCa1": "CanCSCa",
        "CanCSR7": "CanCSR",
        "CanCSR8": "CanCSR",
    }
    def mapping_from_row(row):
        animal_name = row["Directory"][len(start_dir+os.sep):].split("_")[0]
        return mapping_dict[animal_name]

    cells_to_analyse["Mapping"] = cells_to_analyse.apply(mapping_from_row, axis=1)

    df_to_file(cells_to_analyse, out_loc)

if __name__ == "__main__":
    main_start_dir = (
        r"D:\SubRet_recordings_imaging\muscimol_data"
    )
    main_map_file = "CanCSR.py"

    main(main_start_dir, main_map_file)
