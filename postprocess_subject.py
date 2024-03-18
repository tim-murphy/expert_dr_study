# post-process all data for a given subject

import glob
import os
import sys

from append_grades import append_grades
from postprocessing import process_data_file

DATASETS = ('tracking', 'thinkaloud')

def postprocess_subject(datadir, outdir):
    if not os.path.exists(datadir):
        print("ERROR: data directory does not exist:", datadir, file=sys.stderr)
        sys.exit(1)

    # output directory
    if os.path.exists(outdir):
        # careful, we already have data!!
        overwrite = None
        while overwrite not in ('y', 'n'):
            print("WARN:", outdir)
            print("WARN: outdir already exists! Overwrite? [y/n]: ", end='')
            overwrite = input().lower()
            if len(overwrite) > 0:
                overwrite = overwrite[0]

        if overwrite == 'n':
            print("Not overwriting data. Goodbye.")
            sys.exit(1)

        # if we get here, we've agreed to overwrite.
        print("Overwriting data. I hope you know what you're doing...")
    else:
        os.mkdir(outdir)

    for dataset in DATASETS:
        print("===", dataset, "===")

        datapath = os.path.join(datadir, dataset)
        if not os.path.exists(datapath):
            print("WARN: dataset does not exist:", dataset)
            continue

        outdir_dataset = os.path.join(outdir, dataset)
        if not os.path.exists(outdir_dataset):
            os.mkdir(outdir_dataset)

        # get all of the data for this subject
        for dat in glob.glob(os.path.join(datapath, '*.bmp.txt')):
            print(os.path.split(dat)[1], "...", sep='', end='')
            process_data_file(dat, outdir_dataset)
            print("done")

    # add the grades to the master file
    append_grades(outdir)

    print("All done, have a nice day :)")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage:", __file__, "<datadir> <outdir>")
        sys.exit(1)

    # data directory
    datadir = sys.argv[1]
    outdir = sys.argv[2]

    postprocess_subject(datadir, outdir)

# EOF
