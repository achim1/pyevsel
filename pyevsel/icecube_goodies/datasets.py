"""
Export a single dictionary holding nfiles
information per each dataset
"""

# livetime of some datasets
IC79GS_LIVETIME = 26723588.380711164
IC79BS_LIVETIME = 2899974
IC86BS_LIVETIME = 739.59*3600
IC86GS_LIVETIME = 7236.03*3600
ic79ltime = IC79BS_LIVETIME + IC79GS_LIVETIME
ic86ltime = IC86BS_LIVETIME + IC86GS_LIVETIME


nue_ds79 = {
6461 : 2000,
6725:  10000
}

nue_ds86 = {
9250: 10000
}

nue_ds_fast = {
6725:  10000
}

numu_ds79 = {
6726: 10000,
6454: 500
}

numu_ds86 = {
9095: 10000
}
numu_ds_fast = {
6726: 10000
}

nutau_ds79 = {
8962: 500
}

nutau_ds86 = {
10099: 500
}

nutau_ds_fast = {
8962: 500
}

mu_ds79 = {
6514: 99802,
9086: 76673,
9505: 100000,
9654: 100000,
9493: 99663,
9106: 99999
}

mu_ds86 = {
#ic86
10309: 10000,
10282: 19997,
10651: 19994,
10784: 19714,
10899: 19882,
10475: 19435
}

mu_ds_fast = {
6514: 99802
}

mucc_ds79 = {
6451: 100000,
6939: 10000,
7260: 30000
}

analysis_datasets = {
#nue
6461 : 2000,
6725:  10000,
9095: 10000,
#numu
9095: 10000,
6726: 10000,
6454: 500,
#nutau
8962: 500,
10099: 500,
#mu
6514: 99802,
#9622: 100000,
#6451: 100000,
9086: 76673,
9505: 100000,
9654: 100000,
9493: 99663,
9106: 99999,
#ic86
10309: 10000,
10282: 19997,
10651: 19994,
10784: 19714,
10899: 19882,
10475: 19435,
#mu-cc
6451: 100000,
6939: 10000,
7260: 30000
}


datasets = {
6461 : 2000,
6725:  10000,
6726: 10000,
6454: 500,
8962: 500,
6462: 9970,
7785: 10000,
7693: 1000,
7694: 1000,
6514: 99802,
6451: 100000,
9106: 99999,
9493: 99663,
9654: 100000,
7260: 30000,
6939: 10000,
9086: 76673,
9505: 100000,
#ic86
10036: 2511,
10282: 19997,
10475: 19435,
10784: 19714,
10651: 19994,
9255: 100000,
10661: 19994,
10309: 10000,
9622: 100000,
9527: 13485,
10281: 9657,
9485: 2700,
9036: 100000,
10899: 19882,
9250: 10000,
9095: 10000,
10099: 500
}

ic79ds_id = nue_ds79.keys() +\
            numu_ds79.keys() +\
            nutau_ds79.keys() +\
            mu_ds79.keys() +\
            mucc_ds79.keys() +\
            [1000,1200]

ic86ds_id = nue_ds86.keys() +\
            numu_ds86.keys() +\
            nutau_ds86.keys() +\
            mu_ds86.keys() +\
            [2000,2200]


