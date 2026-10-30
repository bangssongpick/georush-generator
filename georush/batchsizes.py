"""How many videos one run may make. One place for the command line, the window and the pipelines."""

# v1.3.5: up to 20 Shorts per run (was 1/3/5/10). 20 is just under one week of Shorts at 3 a day (21),
# which is also the window in which no flag repeats.
SHORTS_BATCH_SIZES = (1, 2, 3, 5, 10, 20)
LONGFORM_BATCH_SIZES = (1, 2, 3)
