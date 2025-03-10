# LFP Anterior Thalamus Lesion

## Installation

```Bash
git clone https://github.com/seankmartin/SIMURAN
cd SIMURAN
pip install -e .
cd ..
git clone https://github.com/seankmartin/NeuroChaT
cd NeuroChaT
pip install -e .
cd ..
git clone https://github.com/seankmartin/PythonUtils
cd PythonUtils
pip install -e .
cd ..
git clone https://github.com/seankmartin/lfp_atn
cd lfp_atn
pip install -e .
cd ..
```

## Running the code

```bash

echo "Use this to run specific results."
doit list

echo "Use this to run everything."
doit
```

## Data considered

### Open field recordings

Recordings were selected to be balanced for each animal (same number).
Generally habituation recordings were excluded where possible, and if included, late habituation sessions were used, as the wires are moved less at this point.

Control:

1. CSR1 - all small square recordings (not habituation) (6 days)
2. CSR2 - all small square recordings (not habituation) (6 days)
3. CSR3 - all small square recordings (not habituation) (6 days)
4. CSR4 - all small square recordings and big square (3 days, 6 records)
5. CSR5 - all small square recordings and big square (3 days, 6 records)
6. CSR6 - all small square recordings and late habituation (6 days)

Lesion:

1. LSR1 - all small square recordings (not habituation) (6 days)
2. LSR3 - all small square recordings (not habituation) (6 days)
3. LSR4 - all small square recordings and some habituation(5 days, 6 records)
4. LSR5 - all small square recordings and some habituation (5 days, 6 records)
5. LSR6 - all small square recordings (habituation only) (6 days)

## Note

1. TODO list the parameters of the usual FIR filter used.
2. Delta is considered to be in the range 1.5 - 4 Hz.
3. Theta is considered to be in the range 6 - 10 Hz.

## Analysis

See `lfp_atn_simuran/multi_runs`

## Papers

- Z-score LFP is common and found in many papers.
- Power spectrum is a common analysis.
- T-maze coherence is from a youtube video, check Matheus mails.

## TODO

- Check if PS.norm.range.power == ps.range.power / ps.power
