clean_kwargs = {
    "pick_property": "group",
    "channels": ["LFP"],
}

params = {
    # Cleaning params
    "clean_method": "pick",
    "clean_kwargs": clean_kwargs,
    
    # Filtering params
    "fmin": 1,
    "fmax": 100,
    "theta_min": 6,
    "theta_max": 12,
    "delta_min": 1.5,
    "delta_max": 4,

    # Plotting params
    "psd_scale": "decibels",
    "image_format": "png",

    # Path setup
    "cfg_base_dir" : r"D:\SubRet_recordings_imaging"
}