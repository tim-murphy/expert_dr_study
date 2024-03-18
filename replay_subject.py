import os
import sys

from replay_file import replay_from_file

from winsound import Beep as beep

# NOTE: this must be the same order as Gazepoint Analysis, otherwise we'll put
#       the wrong data on the wrong image.
ALL_FILES = [
    "007-0028-000_1140x848.bmp",
    "007-0055-000_1140x848.bmp",
    "007-0142-000_1140x848.bmp",
    "007-0323-000_1140x848.bmp",
    "007-1774-100_1140x848.bmp",
    "007-2252-100_1140x848.bmp",
    "007-2469-100_1140x848.bmp",
    "007-2477-100_1140x848.bmp",
    "007-2840-100_1140x848.bmp",
    "007-4250-200_1140x848.bmp",
    "007-4850-300_1140x848.bmp",
    "007-5457-300_1140x848.bmp",
    "007-6320-400_1140x848.bmp",
    "007-6573-400_1140x848.bmp",
    "007-7146-400_1140x848.bmp",
    "007-7235-400_1140x848.bmp",
    "20170502092649506_1140x848.bmp",
    "20170518171333730_1140x848.bmp",
    "20170519153000176_1140x848.bmp",
    "20170521094743135_1140x848.bmp",
    "007-0051-000_1140x848.bmp",
    "007-0079-000_1140x848.bmp",
    "007-0321-000_1140x848.bmp",
    "007-1811-100_1140x848.bmp",
    "007-2403-100_1140x848.bmp",
    "007-2705-100_1140x848.bmp",
    "007-2763-100_1140x848.bmp",
    "007-2841-100_1140x848.bmp",
    "007-4290-200_1140x848.bmp",
    "007-4991-300_1140x848.bmp",
    "007-6520-400_1140x848.bmp",
    "007-7017-400_1140x848.bmp",
    "007-7175-400_1140x848.bmp",
    "007-7265-400_1140x848.bmp",
    "20170228231807286_1140x848.bmp",
    "20170511224838938_1140x848.bmp",
    "20170512231007763_1140x848.bmp",
    "20170525111826224_1140x848.bmp",
    "20170609154552424_1140x848.bmp",
    "20170622080837660_1140x848.bmp"
]

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage:", __file__, "<subject_data_dir> <dataset=(tracking|thinkaloud)>")
        sys.exit(1)

    ### subject data error checking ###
    datadir = sys.argv[1]

    if not os.path.exists(datadir):
        print("ERROR: subject data directory does not exist!", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(datadir):
        print("ERROR: subject data path is not a directory!", file=sys.stderr)
        sys.exit(1)

    ### dataset error checking ###
    dataset = sys.argv[2]

    if dataset not in ("tracking", "thinkaloud"):
        print("ERROR: invalid dataset:", dataset, file=sys.stderr)
        sys.exit(1)

    ### processing starts here ###
    for img in ALL_FILES:
        img_path = os.path.join(datadir, dataset, img + ".processed.txt")
        if not os.path.exists(img_path):
            print("!!! skip file:", img)
        else:
            print("===", img, "===")
            replay_from_file(img_path)
            beep(500, 500) # beep when finished

# EOF
