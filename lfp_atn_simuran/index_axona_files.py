import re

import numpy as np
import simuran
import typer
from simuran.loaders.nc_loader import NCLoader


def main(path_to_files: str, output_path: str) -> None:
    simuran.index_ephys_files(
        start_dir=path_to_files,
        loader=NCLoader(system="Axona", loader_kwargs={"pos_extension": ".pos"}),
        output_path=output_path,
        overwrite=True,
        post_process_fn=clean_data,
    )


def get_rat_name(s):
    # '''Get rat name from filename'''
    names_part = ["Su", "Ca", "LR", "CS", "CR", "LS"]
    temp = s.split("_")
    for name in temp:
        for parts in names_part:
            if parts in name:
                return name


def get_rat_name_folder(s):
    """Get rat name from folder"""
    names_part = ["Su", "Ca", "LR", "CS", "CR", "LS"]
    temp = s.split("/")
    for name in temp:
        for part in names_part:
            if part in name:
                return name


def decode_name(rat_name):
    """Function to decode rat names based on the order of the names"""
    res = []
    regex_dict = {
        "Canula": "^(Can)",
        "Ca1": "(Ca)",
        "lesion": "(L)",
        "Control": "(CC)|(CR)|(CS)",
        "Ret": "(Ret)|(R)",
        "Sub": "(Sub)|(S)",
    }
    for code in regex_dict:
        if re.search(regex_dict[code], rat_name):
            rat_name = re.sub(regex_dict[code], "", rat_name)
            res.append(code)
    n = re.findall("\d$", rat_name)
    if len(n) > 0:
        res.append(n[0])
    return res


def decode_name_folder(rat_name):
    """Function to decode rat names based on the order of the names"""
    res = []
    regex_dict = {
        "Canula": "^(Can)",
        "Ca1": "(Ca)",
        "lesion": "(L)",
        "Control": "(CC)|(CR)|(CS)",
        "Ret": "(Ret)|(R)",
        "Sub": "(Sub)|(S)",
    }
    for code in regex_dict:
        if re.search(regex_dict[code], rat_name):
            rat_name = re.sub(regex_dict[code], "", rat_name)
            res.append(code)
    n = re.findall("\d$", rat_name)
    if len(n) > 0:
        res.append(n[0])
    return res


def get_treatment(s):
    """Get the type of treatment from filename"""
    temp = re.split("_|\.", s.lower())
    if "saline" in temp:
        return "control"
    elif "muscimol" in temp or "musc" in temp:
        return "muscimol"


def get_treatment_folder(s):
    """Get the type of maze from folder
    not considering controls
    """
    temp = re.split("_|\.", s.lower())
    if "saline" in temp or "sham" in temp:
        return "control"
    elif "muscimol" in temp or "musc" in temp:
        return "muscimol"


def get_sleep_awake(s):
    """Get the if animal is sleeping from filename"""
    temp = re.split("_|\.", s.lower())
    if "sleep" in temp:
        return 1
    return 0


def get_sleep_awake_folder(s):
    """Get the if animal is sleeping from folder"""
    temp = re.split("_|\.|\ |\/", s.lower())
    if "sleep" in temp or "sleeping" in temp:
        return 1
    return 0


def get_habituation(s):
    """Get the type of maze from filename"""
    temp = re.split("_|\.|\ |\/", s.lower())
    names_part = ["habituation", "hab", "hab1", "hab2", "hab3", "hab4"]
    for name in temp:
        for parts in names_part:
            if parts in name:
                return 1
    return 0


def get_habituation_folder(s):
    """Get the type of maze from folder"""
    names_part = ["habituation", "hab", "hab1", "hab2", "hab3", "hab4", "hab5"]
    temp = s.split("/")
    for name in temp:
        for parts in names_part:
            if parts in name:
                return 1
    return 0


def n_channels(s):
    """Get the number of channels from filename"""
    temp = re.split("_|\.", s.lower())
    if "C64" in temp:
        return 64
    return 32


def get_light_dark(s):
    """Get the if animal is sleeping from filename"""
    temp = re.split("_|\.", s.lower())
    if "light" in temp:
        return 1
    elif "dark" in temp:
        return 0
    return np.nan


def get_light_dark_folder(s):
    """Get the type of maze from filename"""
    temp = s.split("/")
    if "light" in temp:
        return 1
    elif "dark" in temp:
        return 0

    return np.nan


def get_maze(s):
    """Get the type of maze from filename"""
    temp = re.split("_|\.", s.lower())
    if "smallsq" in temp:
        return "small_sq"

    elif "bigsq" in temp or "big" in temp or "big_sq" in temp:
        return "big_sq"

    elif "smallsqdownup" in temp and "up" in temp:
        return "smallsqdownup_up"

    elif "smallsqdownup" in temp and "down" in temp:
        return "smallsqdownup_down"

    elif "small sq" in temp and "screen":
        return "small_sq"

    elif "btm" in temp:
        return "btm"

    elif "noborders" in temp:
        return "noborders"

    elif "movespatcue" in temp or "spacue" in temp:
        return "movespatcue"

    elif "bigsq1wall" in temp:
        return "bigsq1wall"

    elif (
        "maze" in temp
        and "+" in temp
        or "+maze" in temp
        or "t" in temp
        and "maze" in temp
    ):
        return "tmaze"

    elif "mazedown" in temp:
        return "mazedown"

    else:
        return np.nan


def get_maze_from_folder(s):
    """Get the type of maze from filename"""
    temp = re.split("_|\.|\ |\/", s.lower())

    if (
        "smallsq" in temp
        or "small" in temp
        or "smallsqrest" in temp
        or "smallsw" in temp
        or "smallaq" in temp
    ):
        return "small_sq"

    elif "bigsq" in temp or "big" in temp or "big_sq" in temp:
        return "big_sq"

    elif "smallsqdownup" in temp and "up" in temp:
        return "smallsqdownup_up"

    elif "smallsqdownup" in temp and "down" in temp:
        return "smallsqdownup_down"

    elif "smallsqdown" in temp and "down" in temp:
        return "smallsqdownup_down"

    elif "small sq" in temp and "screen":
        return "small_sq"

    elif "btm" in temp:
        return "btm"

    elif "movespatcue" in temp:
        return "movespatcue"

    elif "bigsq1wall" in temp:
        return "bigsq1wall"

    elif "screening" in temp or "screen" in temp:
        return "screening"

    elif "small" in temp and "change" in temp:
        return "small_sq"

    elif "spat" in temp or "spatial" in temp:
        return "spatial_cues"

    elif (
        "maze" in temp
        and "+" in temp
        or "+maze" in temp
        or "t" in temp
        and "maze" in temp
    ):
        return "tmaze"

    elif "wb" in temp:
        return "wb_task"

    elif "donut" in temp:
        return "donut"

    elif "move" in temp and "walls" in temp:
        return "move_walls"

    elif "smallsqresting" in temp:
        return "small_sq"

    elif "one" in temp and "wall":
        return "bigsq1wall"

    elif "two" in temp and "walls":
        return "bigsq2walls"

    elif "sleep" in temp or "sleeps" in temp:
        return "sleep"

    else:
        return np.nan


def clean_config_files(s):
    """Remove config SET files"""
    try:
        return int(s)
    except:
        return np.nan


def clean_setup_files(s):
    names_part = ["setup"]
    temp = s.split("/")
    for name in temp:
        for part in names_part:
            if part in name:
                return np.nan
    return s


def get_date_from_files(fold, file):
    """Get date from the set file"""
    try:
        with open(fold + "/" + file + ".set") as f:
            date = f.readline()[-12:].strip()
            return date

    except:
        return np.nan


def get_missing_dates(s):
    """Get missing dates from filename"""
    temp = s.split("_")
    return temp[0]


def convert_datetime(dt):
    """convert datetime string to datetime object"""
    try:
        return datetime.datetime.strptime(dt, "%d %b %Y %H:%M:%S")
    except:
        return np.nan


def update_maze(s):
    if "Control" in s:
        return "Control"
    if "lesion" in s:
        return "lesion"


def animal_to_mapping(s):
    cl_13 = "CL-SR_1-3.py"
    cl_46 = "CL-SR_4-6.py"
    d = {
        "CSubRet1": cl_13,
        "CSubRet2": cl_13,
        "CSubRet3": cl_13,
        "CSubRet4": cl_46,
        "CSubRet5": cl_46,
        "CSR6": cl_46,
    }

    return d.get(s, "NOT_EXIST")


def clean_data(df, **kwargs):
    """
    Sequency of cleaning dataframe

    Parameters:
    df (pandas dataframe): Dataframe with all data
    Returns:
    dataframe: Cleaned dataframe

    """
    df["recording_name"] = df.filename.apply(lambda x: x[:-4])
    # Rat name
    df["rat"] = df.recording_name.apply(get_rat_name)
    df["name_folder"] = df.directory.apply(get_rat_name_folder)
    df["rat"] = df["rat"].combine_first(df["name_folder"])
    df.drop("name_folder", axis=1, inplace=True)
    # number of channels
    df["n_channels"] = df.filename.apply(n_channels)
    # sleep experiment
    df["sleep"] = df.filename.apply(get_sleep_awake)
    df["sleep_folder"] = df.filename.apply(get_sleep_awake_folder)
    df["sleep"] = df["sleep"].combine_first(df["sleep_folder"])
    df.drop("sleep_folder", axis=1, inplace=True)
    # get mazes
    df["maze"] = df.filename.apply(get_maze)
    df["maze_folder"] = df.directory.apply(get_maze_from_folder)
    df["maze"] = df["maze"].combine_first(df["maze_folder"])
    df.drop("maze_folder", axis=1, inplace=True)
    # get habituation
    df["habituation"] = df.filename.apply(get_habituation)
    df["habituation_folder"] = df.filename.apply(get_habituation_folder)
    df["habituation"] = df["habituation"].combine_first(df["habituation_folder"])
    df.drop("habituation_folder", axis=1, inplace=True)
    # Get treatment
    df["treatment"] = df.filename.apply(get_treatment)
    df["treatment_folder"] = df.filename.apply(get_treatment_folder)
    df["treatment"] = df["treatment"].combine_first(df["treatment_folder"])
    df.drop("treatment_folder", axis=1, inplace=True)
    # Get duration
    df["duration"] = df.duration.apply(clean_config_files)
    df.dropna(subset=["duration"], inplace=True)
    # light or dark
    df["light"] = df.filename.apply(get_light_dark)
    df["light"] = df["light"].fillna(11)
    # Cleaning
    df["directory"] = df.directory.apply(clean_setup_files)
    df.dropna(subset=["directory"], inplace=True)
    # Combine datetime
    # Dates from file
    fold_file = df[["directory", "recording_name"]].values
    df["date"] = [get_date_from_files(fold, file) for fold, file in fold_file]
    df.loc[df.date.isnull(), "date"] = df.loc[df.date.isnull(), "recording_name"].apply(
        get_missing_dates
    )
    df["date_time"] = df["date"] + " " + df["time"]
    df["date_time"] = df["date_time"].apply(convert_datetime)
    df.drop(["date", "time"], inplace=True, axis=1)
    df["name_dec"] = df.rat.apply(decode_name)
    df.drop("recording_name", axis=1, inplace=True)
    df.loc[df.treatment.isnull(), "treatment"] = df.loc[
        df.treatment.isnull()
    ].name_dec.apply(update_maze)
    df.drop("name_dec", axis=1, inplace=True)

    df["mapping"] = df.rat.apply(animal_to_mapping)

    return df


if __name__ == "__main__":
    typer.run(main)
