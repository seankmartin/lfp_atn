configfile: "snakemake_config.yaml"

rule preprocess_data:
    output:
        "results/axona_file_index.csv"
    shell:
        "python lfp_atn_simuran/index_axona_files.py {config[data_directory]} {config[file_index_path]}"


rule test:
    output:
        "results/blah.py"
    input:
        "results/axona_file_index.csv"
    shell:
        r"python E:\Repos\SIMURAN\simuran\main\main_from_template.py lfp_atn_simuran\batch_params\CSR1-openfield.py lfp_atn_simuran\configs\default.py lfp_atn_simuran\functions\fn_spectra.py --data-filterpath lfp_atn_simuran\table_params\CSR1.yaml"
