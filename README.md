# expert_data

[![DOI](https://zenodo.org/badge/773595597.svg)](https://zenodo.org/doi/10.5281/zenodo.12695625)

Scripts in this repo are to perform any post-processing (invalidate data during
zoom and pan, etc) and upload to Gazepoint Analysis for, well, analysis.

Before loading any data, create two Gazepoint Analysis projects to replay the
data to: `tracking` for eye tracking only, and `thinkaloud` for eye tracking
and thinkaloud audio. Load all images into the media list with timeout of 0.

Steps to run for each subject:
1. `postprocess_subject.py <datadir> <outdir>/<subject_id>`.
2. Open Gazepoint Analysis `tracking` project.
3. `replay_subject.py <outdir>/<subject_id> tracking`.
4. Click `Start Record` on Gazepoint analysis and follow prompts from the
   replay_subject.py script, ensuring the image being replayed matches the
   image on Gazepoint Analysis.
5. Repeat steps 2-4 for thinkalound instead of tracking.
6. For thinkalound data, convert sound to mp3 format and copy into the Gazepoint
   Analysis results directory (instructions coming soon).
