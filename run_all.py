from time import time
from tqdm import tqdm
from subprocess import run

tasks_to_run = [
    "doit list_openfield",
    "doit coherence",
    "doit lfp_power",
    "doit lfp_speed",
    "doit muscimol_sta",
    "doit speed_ibi",
    "doit spike_lfp",
    "doit summarise_results"
]

start_time = time()
for t in tqdm(tasks_to_run):
    print("Running {}".format(t))
    run(t)

end_time = time() - start_time

print("Finished running in {:.2f} minutes".format(end_time / 60.0))