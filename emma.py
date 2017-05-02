#!/usr/bin/python3
# ----------------------------------------------------
# Electromagnetic Mining Array (EMMA)
# Copyright 2017, Pieter Robyns
# ----------------------------------------------------

from ops import *
from debug import DEBUG
from time import sleep
from emma_worker import app
from celery import group
import numpy as np
import matplotlib.pyplot as plt
import sys
import argparse
import configparser
import emutils
import emio

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Electromagnetic Mining Array (EMMA)')  # ['align','attack','filter','save']
    parser.add_argument('actions', type=str, choices=ops.keys(), help='Action to perform', nargs='+')
    parser.add_argument('inpath', type=str, help='Input path where the trace sets are located')
    parser.add_argument('--inform', dest='inform', type=str, choices=['cw','sigmf','gnuradio'], default='cw', help='Input format to use when loading')
    parser.add_argument('--outform', dest='outform', type=str, choices=['cw','sigmf','gnuradio'], default='sigmf', help='Output format to use when saving')
    parser.add_argument('--outpath', '-O', dest='outpath', type=str, default='./export/', help='Output path to use when saving')
    parser.add_argument('--num-cores', dest='num_cores', type=int, default=4, help='Number of CPU cores')
    args, unknown = parser.parse_known_args()
    print(emutils.BANNER)

    try:
        # Get a list of filenames depending on the format
        trace_set_paths = emio.get_trace_paths(args.inpath, args.inform)

        # Worker-specific configuration
        window = Window(begin=1600, end=14000)
        conf = argparse.Namespace(
            reference_trace=emio.get_trace_set(trace_set_paths[0], args.inform)[0][window.begin:window.end],
            window=window,
            **args.__dict__
        )

        jobs = []
        for part in emutils.partition(trace_set_paths, int(len(trace_set_paths) / args.num_cores)):
            jobs.append(work.s(part, conf))

        result = group(jobs)()
        print(result.get())
    except KeyboardInterrupt:
        pass

    # Clean up
    print("Cleaning up")
    app.backend.cleanup()
