from lfp_atn_simuran.analysis.lfp_clean import LFPClean
from simuran import EegArray, Eeg, SimuranFigure

import numpy as np
import matplotlib.pyplot as plt

np.random.seed(42)

mean_noise = 0
target_noise_watts = 10
sig_len_seconds = 10
fs = 250
sig_len = fs * sig_len_seconds
n_channels = 4

noise = np.random.normal(mean_noise, np.sqrt(target_noise_watts), sig_len)

evenly_spaced = np.arange(0, sig_len_seconds, 1 / fs)
samples_arr = evenly_spaced * fs

delta_hz = 3
theta_hz = 8
fast_hz = 16
delta_wave = np.sin(evenly_spaced * delta_hz * 2 * np.pi)
theta_wave = np.sin(evenly_spaced * theta_hz * 2 * np.pi)
cosine_wave = np.cos(evenly_spaced * delta_wave * 2 * np.pi)

sig1 = Eeg(delta_wave + theta_wave + noise, fs)
sig1.region = "Main"
sig1.channel = 1
sig2 = Eeg(delta_wave + theta_wave, fs)
sig2.region = "Main"
sig2.channel = 2
sig3 = Eeg(delta_wave + theta_wave + cosine_wave + noise, fs)
sig3.region = "Alt"
sig3.channel = 3
sig4 = Eeg(delta_wave + theta_wave + cosine_wave, fs)
sig4.region = "Alt"
sig4.channel = 4
eegs = EegArray()
eegs.set_container([sig1, sig2, sig3, sig4])

lfp_clean = LFPClean(method="ica", visualise=True, show_vis=False)

method_kwargs = dict(manual_ica=False)
res = lfp_clean.clean(eegs, min_f=1, max_f=20, method_kwargs=method_kwargs)

fig = res["fig"]
figs = res["ica_figs"]

fig.savefig("ica_res_auto.pdf", dpi=400)
figs[0].savefig("ica_exclude_auto.pdf", dpi=400)
figs[1].savefig("ica_recon_auto.pdf", dpi=400)
plt.close("all")

lfp_clean = LFPClean(method="ica", visualise=True, show_vis=False)
method_kwargs = dict(manual_ica=True)
res = lfp_clean.clean(eegs, min_f=1, max_f=20, method_kwargs=method_kwargs)
fig = res["fig"]
figs = res["ica_figs"]

fig.savefig("ica_res_manual.pdf", dpi=400)
figs[0].savefig("ica_exclude_manual.pdf", dpi=400)
figs[1].savefig("ica_recon_manual.pdf", dpi=400)
