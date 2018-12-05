# MeRLA
Monophonic melody generation with reinforcement learning

## Setup
Running this program requires the installation of the python-midi toolkit, which can be found [here](https://github.com/vishnubob/python-midi).

## Running MeRLA
Inside main.py, there are several variables that can be changed. The input chord progressions can be modified near the bottom of the file (there are examples for formatting). The output csv file name and the number of simulations can be modified as parameters to the 'run_experiment' function. The 'SURVEY' boolean at the top of the file can be used to generate three types of melodies (MeRLA with tension, MeRLA without tension, and random) for comparison. If 'SURVEY' is false, only one melody will be generated for each chord progression.

The main.py script can then be run with 

```sh
python2.7 main.py
```

##
Copyright © 2018 Joshua Klag
