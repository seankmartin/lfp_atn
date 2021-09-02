import os
from math import floor, ceil
from pprint import pprint
import csv

import simuran
import pandas as pd
import matplotlib.pyplot as plt
import astropy.units as u
from neurochat.nc_lfp import NLfp
import numpy as np
from scipy.signal import coherence
from skm_pyutils.py_table import list_to_df, df_from_file, df_to_file
import seaborn as sns
import mne

try:
    from lfp_atn_simuran.analysis.lfp_clean import LFPClean
    from lfp_atn_simuran.analysis.plot_coherence import plot_recording_coherence
    from lfp_atn_simuran.analysis.frequency_analysis import powers

    do_analysis = True
except ImportError:
    do_analysis = False

from neuronal.decoding import LFPDecoder

here = os.path.dirname(os.path.abspath(__file__))


def decoding(lfp_array, groups, labels, base_dir):

    for group in ["Control", "Lesion (ATNx)"]:
        sfreq = 250
        ch_types = ["eeg", "eeg"]
        ch_names = ["SUB", "RSC"]

        correct_groups = groups == group
        info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)
        # Can use 0 here on idx 2 to only have SUB
        lfp_to_use = lfp_array[correct_groups, :, :]
        mne_epochs = mne.EpochsArray(lfp_to_use, info)
        labels_ = labels[correct_groups]

        decoder = LFPDecoder(
            labels=labels_,
            mne_epochs=mne_epochs,
            cv_params={"n_splits": 100},
            feature_params={"step": 25},
        )
        out = decoder.decode()

        print(decoder.decoding_accuracy(out[2], out[1]))

        print("\n----------Cross Validation-------------")

        decoder.cross_val_decode(shuffle=True)
        pprint(decoder.cross_val_result)
        pprint(decoder.confidence_interval_estimate("accuracy"))

        random_search = decoder.hyper_param_search(verbose=True, set_params=False)
        print("Best params:", random_search.best_params_)

        decoder.visualise_features(output_folder=base_dir, name=f"_{group}")


def main(
    excel_location,
    base_dir,
    plot_individual_sessions,
    do_coherence=True,
    do_decoding=True,
    overwrite=False,
):

    # Setup
    df = df_from_file(excel_location)
    cfg = simuran.parse_config()
    delta_min = cfg["delta_min"]
    delta_max = cfg["delta_max"]
    theta_min = cfg["theta_min"]
    theta_max = cfg["theta_max"]
    clean_method = cfg["clean_method"]
    clean_kwargs = cfg["clean_kwargs"]
    window_sec = 0.5
    fmin, fmax = 1, 20

    # Don't analyse more than 6 seconds
    max_len = 6

    ituples = df.itertuples()
    num_rows = len(df)

    no_pass = False
    if "passed" not in df.columns:
        print("Please add passed as a column to the df.")
        no_pass = True

    results = []
    coherence_df_list = []

    base_dir_new = os.path.dirname(excel_location)
    decoding_loc = os.path.join(base_dir_new, "lfp_decoding.csv")
    lfp_len = 500
    hf = lfp_len // 2
    new_lfp = np.zeros(shape=(num_rows // 2, 2, lfp_len))
    groups = []
    choices = []
    oname_coherence = os.path.join(
        here, "..", "sim_results", "tmaze", "coherence_full.csv"
    )
    os.makedirs(os.path.dirname(oname_coherence), exist_ok=True)
    skip = (
        (os.path.exists(decoding_loc))
        and (not overwrite)
        and (os.path.exists(oname_coherence))
    )
    if skip:
        with open(decoding_loc, "r") as f:
            csvreader = csv.reader(f, delimiter=",")
            for i, row in enumerate(csvreader):
                groups.append(row[0])
                choices.append(row[1])
                vals = row[2:]
                new_lfp[i, 0] = np.array([float(v) for v in vals[:lfp_len]])
                new_lfp[i, 1] = np.array(
                    [float(v) for v in vals[lfp_len : 2 * (lfp_len)]]
                )
        coherence_df = df_from_file(oname_coherence)

    ## Extract LFP, do coherence, and plot
    if not skip:
        for j in range(num_rows // 2):
            row1 = next(ituples)
            row2 = next(ituples)
            recording_location = os.path.join(base_dir, row1.location)
            recording_location = recording_location.replace("--", os.sep)
            param_file = os.path.join(here, "..", "recording_mappings", row1.mapping)

            recording = simuran.Recording(
                param_file=param_file, base_file=recording_location, load=False
            )
            lfp_clean = LFPClean(method=clean_method, visualise=False)
            recording.signals.load()
            sig_dict = lfp_clean.clean(
                recording, min_f=fmin, max_f=fmax, method_kwargs=clean_kwargs
            )["signals"]

            x = np.array(sig_dict["SUB"].samples.to(u.mV))
            duration = len(x) / 250
            y = np.array(sig_dict["RSC"].samples.to(u.mV))
            fs = sig_dict["SUB"].sampling_rate

            if do_coherence:
                recording.spatial.load()
                spatial = recording.spatial.underlying
                f, Cxy = coherence(x, y, fs, nperseg=window_sec * 250)
                f = f[np.nonzero((f >= fmin) & (f <= fmax))]
                Cxy = Cxy[np.nonzero((f >= fmin) & (f <= fmax))]

                theta_co = Cxy[np.nonzero((f >= theta_min) & (f <= theta_max))]
                delta_co = Cxy[np.nonzero((f >= delta_min) & (f <= delta_max))]
                max_theta_coherence_ = np.amax(theta_co)
                max_delta_coherence_ = np.amax(delta_co)

            if plot_individual_sessions:
                fig, ax = plt.subplots()

            # Loop over the two parts of a trial
            # TODO decide if this should just be for the first/final part of the trial
            for k_, r in enumerate((row1, row2)):
                # end or choice could be used
                # t1, t2 = r.start, r.end
                t1, t2 = r.start, r.choice
                t3 = r.end
                if t3 > duration:
                    raise RuntimeError(
                        "Last time {} greater than duration {}".format(t3, duration)
                    )
                lfpt1, lfpt2 = int(floor(t1 * 250)), int(ceil(t2 * 250))
                if (lfpt2 - lfpt1) > (max_len * 250):
                    lfpt2 = lfpt1 + (max_len * 250)
                # Make sure have at least 1 second
                if (lfpt2 - lfpt1) < 250:
                    lfpt2 = lfpt1 + 250

                if plot_individual_sessions:
                    if r.test == "first":
                        c = "k"
                    else:
                        c = "r"

                    st1, st2 = int(floor(t1 * 50)), int(ceil(t3 * 50))
                    x_time = spatial.get_pos_x()[st1:st2]
                    y_time = spatial.get_pos_y()[st1:st2]
                    c_end = int(floor(t2 * 50))
                    spat_c = (spatial.get_pos_x()[c_end], spatial.get_pos_y()[c_end])
                    ax.plot(x_time, y_time, c=c, label=r.test)
                    ax.plot(spat_c[0], spat_c[1], c="b", marker="x", label="decision")
                    ax.plot(x_time[0], y_time[0], c="b", marker="o", label="start")
                    ax.plot(x_time[-1], y_time[-1], c="b", marker=".", label="end")

                if do_coherence:
                    res_dict = {}
                    # Power
                    for region, signal in sig_dict.items():
                        lfp = NLfp()
                        lfp.set_channel_id(signal.channel)
                        lfp._timestamp = np.array(
                            signal.timestamps[lfpt1:lfpt2].to(u.s)
                        )
                        lfp._samples = np.array(signal.samples[lfpt1:lfpt2].to(u.mV))
                        lfp._record_info["Sampling rate"] = signal.sampling_rate
                        delta_power = lfp.bandpower(
                            [delta_min, delta_max],
                            window_sec=window_sec,
                            band_total=True,
                        )
                        theta_power = lfp.bandpower(
                            [theta_min, theta_max],
                            window_sec=window_sec,
                            band_total=True,
                        )
                        res_dict["{}_delta".format(region)] = delta_power[
                            "relative_power"
                        ]
                        res_dict["{}_theta".format(region)] = theta_power[
                            "relative_power"
                        ]

                    res_list = [
                        r.location,
                        r.session,
                        r.animal,
                        r.test,
                        r.passed.strip(),
                    ]
                    res_list += [
                        res_dict["SUB_delta"],
                        res_dict["SUB_theta"],
                        res_dict["RSC_delta"],
                        res_dict["RSC_theta"],
                    ]

                    # Coherence
                    name = os.path.splitext(r.location)[0]

                    sub_s = sig_dict["SUB"]
                    rsc_s = sig_dict["RSC"]
                    x = np.array(sub_s.samples[lfpt1:lfpt2].to(u.mV))
                    y = np.array(rsc_s.samples[lfpt1:lfpt2].to(u.mV))

                    fs = sig_dict["SUB"].sampling_rate

                    f, Cxy = coherence(x, y, fs, nperseg=window_sec * 250)
                    f = f[np.nonzero((f >= fmin) & (f <= fmax))]
                    Cxy = Cxy[np.nonzero((f >= fmin) & (f <= fmax))]

                    theta_co = Cxy[np.nonzero((f == 10.0))]
                    delta_co = Cxy[np.nonzero((f >= delta_min) & (f <= delta_max))]
                    max_theta_coherence = np.amax(theta_co)
                    max_delta_coherence = np.amax(delta_co)

                    if plot_individual_sessions:
                        fig2, ax2 = plt.subplots(3, 1)
                        ax2[0].plot(f, Cxy, c="k")
                        ax2[1].plot([i / 250 for i in range(len(x))], x, c="k")
                        ax2[2].plot([i / 250 for i in range(len(y))], y, c="k")
                        base_dir_new = os.path.dirname(excel_location)
                        fig2.savefig(
                            os.path.join(
                                base_dir_new,
                                "coherence_{}_{}_{}.png".format(
                                    row1.location, r.session, r.test
                                ),
                            )
                        )
                        plt.close(fig2)

                    res_list += [max_theta_coherence, max_delta_coherence]
                    res_list += [max_theta_coherence_, max_delta_coherence_]
                    results.append(res_list)

                if no_pass is False:
                    group = (
                        "Control"
                        if r.animal.lower().startswith("c")
                        else "Lesion (ATNx)"
                    )
                    if do_coherence:
                        for f_, cxy_ in zip(f, Cxy):
                            coherence_df_list.append(
                                (f_, cxy_, r.passed.strip(), group, r.test, r.session)
                            )

                # For decoding
                if do_decoding:
                    sub_s = sig_dict["SUB"].filter(theta_min, theta_max)
                    rsc_s = sig_dict["RSC"].filter(theta_min, theta_max)
                    x = np.array(sub_s.samples[lfpt1:lfpt2].to(u.mV))
                    y = np.array(rsc_s.samples[lfpt1:lfpt2].to(u.mV))

                    new_lfp[j, 0, k_ * hf : (k_ + 1) * hf] = np.abs(x[-hf:])
                    new_lfp[j, 1, k_ * hf : (k_ + 1) * hf] = np.abs(y[-hf:])

            if do_decoding:
                groups.append(group)
                choices.append(str(r.passed).strip())

            if plot_individual_sessions:
                ax.invert_yaxis()
                ax.legend()
                base_dir_new = os.path.dirname(excel_location)
                figname = os.path.join(base_dir_new, name) + "_tmaze.png"
                fig.savefig(figname, dpi=400)
                plt.close(fig)

    if do_coherence and not skip:
        # Save the results
        headers = [
            "location",
            "session",
            "animal",
            "test",
            "choice",
            "SUB_delta",
            "SUB_theta",
            "RSC_delta",
            "RSC_theta",
            "Theta_coherence",
            "Delta_coherence",
            "Full_theta_coherence",
            "Full_delta_coherence",
        ]

        res_df = pd.DataFrame(results, columns=headers)

        split = os.path.splitext(os.path.basename(excel_location))
        out_name = os.path.join(
            here, "..", "sim_results", "tmaze", split[0] + "_results" + split[1]
        )
        df_to_file(res_df, out_name, index=False)

        # Plot difference between pass and fail trials
        headers = ["Frequency (Hz)", "Coherence", "Passed", "Group", "Test", "Session"]
        coherence_df = list_to_df(coherence_df_list, headers=headers)

        df_to_file(coherence_df, oname_coherence, index=False)

    if do_coherence or skip:
        # coherence_df = coherence_df[coherence_df["Test"] == "second"]
        simuran.set_plot_style()
        sns.lineplot(
            data=coherence_df,
            x="Frequency (Hz)",
            y="Coherence",
            hue="Group",
            style="Passed",
            ci=None,
            estimator=np.median,
        )
        plt.ylim(0, 1)
        simuran.despine()
        plt.savefig(
            os.path.join(here, "..", "sim_results", "tmaze", "coherence.pdf"), dpi=400
        )
        plt.close("all")

        sns.lineplot(
            data=coherence_df,
            x="Frequency (Hz)",
            y="Coherence",
            hue="Group",
            style="Passed",
            ci=95,
            estimator=np.median,
        )
        plt.ylim(0, 1)
        simuran.despine()
        plt.savefig(
            os.path.join(here, "..", "sim_results", "tmaze", "coherence_ci.pdf"),
            dpi=400,
        )
        plt.close("all")

    # Try to decode pass and fail trials.
    if not os.path.exists(decoding_loc) or overwrite:
        with open(decoding_loc, "w") as f:
            for i in range(len(groups)):
                line = ""
                line += f"{groups[i]},"
                line += f"{choices[i]},"
                for v in new_lfp[i, 0]:
                    line += f"{v},"
                for v in new_lfp[i, 1]:
                    line += f"{v},"
                line = line[:-1] + "\n"
                f.write(line)

    if do_decoding:
        groups = np.array(groups)
        labels = np.array(choices)
        decoding(new_lfp, groups, labels, base_dir_new)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    main_output_location = os.path.join(here, "results")

    main_base_dir = r"D:\SubRet_recordings_imaging"
    main_xls_location = os.path.join(main_output_location, "tmaze-times.xlsx")

    cfg_path = os.path.abspath(os.path.join(here, "..", "configs", "default.py"))
    simuran.set_config_path(cfg_path)

    main_plot_individual_sessions = False
    main_do_coherence = True
    main_do_decoding = False

    main_overwrite = True
    main(
        main_xls_location,
        main_base_dir,
        main_plot_individual_sessions,
        main_do_coherence,
        main_do_decoding,
        main_overwrite,
    )
