import cv2
import glob
import os
import sys

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:", __file__, "<imgdir>")
        sys.exit(1)

    imgdir = sys.argv[1]
    if not os.path.exists(imgdir):
        print("ERROR: image directory does not exist:", imgdir, file=sys.stderr)
        sys.exit(1)

    for img in glob.glob(os.path.join(imgdir, '*.bmp')):
        print(img)

        i = cv2.imread(img)
        font = cv2.FONT_HERSHEY_SIMPLEX
        i = cv2.putText(i, os.path.split(img)[1], (20, 50), font,
                        1.0, (255,255,255), 2)

        outpath = os.path.join(os.path.split(img)[0], "label", os.path.split(img)[1])

        os.makedirs(os.path.split(outpath)[0], exist_ok=True)

        cv2.imwrite(outpath, i)

# EOF
