import unittest
from scipy.io import wavfile
import numpy
import pysptk
import os
from os.path import join
import sys

cwd = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(cwd, '..'))

import ttsserver.espp.analysis as alysis
filename = os.path.join(cwd, "data/tmp.wav")
fs, x = wavfile.read(filename)
chunk_size = 1024


class TestAnalysis(unittest.TestCase):

    def test_pitch_detect(self):
        self.assertIsNotNone(alysis.pitch_detect(x, fs, chunk_size))

    def test_zero_crossing_rate_blocks(self):
        self.assertIsNotNone(
            alysis.zero_crossing_rate_blocks(
                x, chunk_size, fs))

    def test_root_mealysis_square(self):
        self.assertIsNotNone(alysis.root_mean_square(x, chunk_size, fs))

    def test_starting_info(self):
        self.assertIsNotNone(
            alysis.starting_info(
                x, alysis.pitch_detect(
                    x, fs, chunk_size), fs, chunk_size))


if __name__ == '__main__':
    unittest.main()
