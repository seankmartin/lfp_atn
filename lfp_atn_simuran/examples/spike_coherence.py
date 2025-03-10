import os

import simuran
import matplotlib.pyplot as plt

try:
    from lfp_atn_simuran.Scripts.spike_lfp import nc_sfc

    do_analysis = True
except ImportError:
    do_analysis = False


def recording_info():
    def setup_signals():
        """Set up the signals (such as eeg or lfp)."""
        # The total number of signals in the recording
        num_signals = 32

        # What brain region each signal was recorded from
        regions = ["SUB"] * 2 + ["RSC"] * 2 + ["SUB"] * 28

        # If the wires were bundled, or any other kind of grouping existed
        # If no grouping, groups = [i for i in range(num_signals)]
        groups = ["LFP", "LFP", "LFP", "LFP"]
        for i in range(2, 9):
            groups.append(i)
            groups.append(i)
            groups.append(i)
            groups.append(i)

        # The sampling rate in Hz of each signal
        sampling_rate = [250] * num_signals
        channel_type = ["eeg"] * num_signals

        # This just passes the information on
        output_dict = {
            "num_signals": num_signals,
            "region": regions,
            "group": groups,
            "sampling_rate": sampling_rate,
            "channel_type": channel_type,
        }

        return output_dict

    def setup_units():
        """Set up the single unit data."""
        # The number of tetrodes, probes, etc - any kind of grouping
        num_groups = 8

        # The region that each group belongs to
        regions = ["SUB"] * num_groups

        # A group number for each group, for example the tetrode number
        groups = [1, 2, 3, 4, 9, 10, 11, 12]

        output_dict = {
            "num_groups": num_groups,
            "region": regions,
            "group": groups,
        }

        return output_dict

    def setup_spatial():
        """Set up the spatial data."""
        arena_size = "default"

        output_dict = {
            "arena_size": arena_size,
        }
        return output_dict

    def setup_loader():
        """
        Set up the loader and keyword arguments for the loader.

        See also
        --------
        simuran.loaders.loader_list.py

        """
        # The type of loader to use, see simuran.loaders.loader_list.py for options
        # For now nc_loader is the most common option
        # loader = "params_only"
        loader = "nc_loader"

        # Keyword arguments to pass to the loader.
        loader_kwargs = {
            "system": "Axona",
            "pos_extension": ".txt",
        }

        output_dict = {
            "loader": loader,
            "loader_kwargs": loader_kwargs,
        }

        return output_dict

    load_params = setup_loader()

    mapping = {
        "signals": setup_signals(),
        "units": setup_units(),
        "spatial": setup_spatial(),
        "loader": load_params["loader"],
        "loader_kwargs": load_params["loader_kwargs"],
    }
    return mapping


def analyse_recording(recording, output_location):
    """

    Parameters
    ----------
    recording : simuran.recording.Recording

    """
    lfp_signal = recording.signals[0].underlying
    units = recording.units
    available_units = recording.get_available_units()
    for l in available_units:
        group, avail_units = l
        if len(avail_units) > 0:
            group_to_use = recording.units.group_by_property("group", group)[1][0]
            break
    unit = recording.units[group_to_use].underlying
    unit.set_unit_no(avail_units[0])
    spike_times = unit.get_unit_stamp()

    figs, data = nc_sfc(lfp_signal, spike_times)

    for i, f in enumerate(figs):
        f.savefig(os.path.join(output_location, f"out_{i}.png"), dpi=300)
        plt.close(f)


def main(set_file_location, output_location, do_analysis=False, min_f=0.5, max_f=30):
    """Create a single recording for analysis."""
    recording = simuran.Recording(params=recording_info(), base_file=set_file_location)
    if not do_analysis:
        return recording

    else:
        os.makedirs(output_location, exist_ok=True)

        analyse_recording(
            recording,
            output_location,
        )


if __name__ == "__main__":
    main_set_file_location = r"D:\SubRet_recordings_imaging\LSubRet5\recording\Small sq up_small sq down\01122017\S1_small sq up\01122017_smallsqdownup_up_1_1.set"
    here = os.path.dirname(os.path.abspath(__file__))
    main_output_location = os.path.join(here, "results")

    main(main_set_file_location, main_output_location, True)
