# Copyright (c) 2013-2019 Hanson Robotics, Ltd. 
import scipy
from scipy.io import wavfile
from scipy.fftpack import rfft, irfft, fftfreq
import numpy
import pysptk
import warnings
warnings.filterwarnings('ignore')
import preprocess as prep


def data_blocks(x, chunk_size):
    num_blocks = int(numpy.ceil(len(x) / chunk_size))
    x = numpy.resize(x, (num_blocks, chunk_size))
    x = numpy.array(x)
    # Blocks of Data by Windowing Through Chunk Size
    return x


def pitch_detect(sndarray, fs, chunk_size):
    """
    pitch_detect(sndarray,fs, chunk_size)

                        pitch_detect computes the fundamental frequency/pitches of blocks/ of Chunks
                Parameters:sndarray - Discrete Data
                                   fs -Sampling frequency
                                   chunk_size
                Returns f0
    """
    new_sndarray = numpy.asarray(numpy.float64(sndarray))
    f0 = pysptk.swipe(numpy.asarray(new_sndarray), fs,
                      chunk_size, 65, 500, 0.001, 1)

    return f0


def zero_crossing_rate_blocks(wavedata, chunk_size, fs):
    """
    zero_crossing_rate_blocks(wavedata,chunk_size,fs)
                    This module computes the zero crossing rate of blocks.
                    It is important in classifying/detecting the voiced and unvoiced region
                    if the zcr is smaller then it is categorized as voiced
                    if the zcr is greater then it is categorized as unvoiced

            Parameter: wavedata - Discrete Data;same as 'x'
                               chunk_size
                               fs - Sampling Frequency
            Returns: zero_crossing_rate_obj - Object containing zcr in seconds and TimeStamps for the zcr

    See:https://www.asee.org/documents/zones/zone1/2008/student/ASEE12008_0044_paper.pdf
    """
    num_blocks = int(numpy.ceil(len(wavedata) / chunk_size))
    time_stamps = (numpy.arange(0, num_blocks - 1) * (chunk_size / float(fs)))
    zero_crossing_rate = []
    for i in range(0, num_blocks - 1):
        start = i * chunk_size
        stop = numpy.min([(start + chunk_size - 1), len(wavedata)])
        zero_crossing = 0.5 * \
            numpy.mean(numpy.abs(numpy.diff(numpy.sign(wavedata[start:stop]))))
        zero_crossing_rate.append(zero_crossing)

    zero_crossing_rate_obj = {
        "zero_crossing_rate_TS": zero_crossing_rate,
        "ts": time_stamps}
    return zero_crossing_rate_obj


def root_mean_square(x, chunk_size, fs):
    """
    root_mean_square(x,chunk_size,fs)
                    root_mean_square computes the root mean square of the blocks and is
                    important for categorizing inflection/pitch-bending samples
            Parameters: x
                                    chunk_size
                                    fs
            Returns		rms-root mean square
    """
    num_blocks = int(numpy.ceil(len(x) / chunk_size))
    timestamps = (numpy.arange(0, num_blocks - 1) * (chunk_size / float(fs)))
    rms = []
    for i in range(0, num_blocks - 1):
        start = i * chunk_size
        stop = numpy.min([(start + chunk_size - 1), len(x)])
        rms_seg = numpy.sqrt(numpy.mean(x[start:stop]**2))
        rms.append(rms_seg)

    return numpy.nan_to_num(numpy.asarray(rms))


def spectral_centroid(wavedata, chunk_size, fs):
    magnitude_spectrum = prep.stft(x, chunk_size)
    timebins, freqbins = numpy.shape(magnitude_spectrum)
    time_stamps = (numpy.arange(0, timebins - 1) * (timebins / float(fs)))

    spectral_centroid = []
    for t in range(timebins - 1):
        power_spectrum = numpy. abs(magnitude_spectrum[t])**2
        sc_t = numpy.sum(power_spectrum * numpy.arange(1,
                                                       freqbins + 1)) / numpy.sum(power_spectrum)
        spectral_centroid.append(sc_t)
    spectral_centroid = numpy.asarray(spectral_centroid)
    spectral_centroid = numpy.nan_to_num(spectral_centroid)
    return spectral_centroid, numpy.asarray(time_stamps)


def unvoiced_starting_pts(
        x, fs, f0, voiced_unvoiced_starting_info_object, chunk_size):
    # register unvoiced signal starting points
    zero_crossing_rate_array = zero_crossing_rate_blocks(x, chunk_size, fs)
    for i in range(0, len(zero_crossing_rate_array["zero_crossing_rate_TS"])):
        if zero_crossing_rate_array["zero_crossing_rate_TS"][i] >= numpy.mean(
                zero_crossing_rate_array["zero_crossing_rate_TS"]):
            voiced_unvoiced_starting_info_object["unvoicedStart"].append(
                zero_crossing_rate_array["ts"][i])
            voiced_unvoiced_starting_info_object["USamp"].append(i)


def voiced_starting_pts(
        x, fs, f0, voiced_unvoiced_starting_info_object, chunk_size):
    # register voiced signal starting points
    zero_crossing_rate_array = zero_crossing_rate_blocks(x, chunk_size, fs)
    for i in range(0, len(zero_crossing_rate_array["zero_crossing_rate_TS"])):
        if zero_crossing_rate_array["zero_crossing_rate_TS"][i] <= numpy.mean(
                zero_crossing_rate_array["zero_crossing_rate_TS"]):
            voiced_unvoiced_starting_info_object["voicedStart"].append(
                zero_crossing_rate_array["ts"][i])
            voiced_unvoiced_starting_info_object["VSamp"].append(i)


def voiced_regions(x, f0, voiced_unvoiced_starting_info_object, chunk_size):
    x = data_blocks(x, chunk_size)
    voiced_regions = []
    for i in range(0, len(
            voiced_unvoiced_starting_info_object["voicedStart"])):
        voiced_regions.append(
            x[voiced_unvoiced_starting_info_object['VSamp'][i]])
    voiced_regions = numpy.abs(voiced_regions)
    # Voiced Regions
    return voiced_regions


def unvoiced_regions(x, f0, voiced_unvoiced_starting_info_object, chunk_size):
    x = data_blocks(x, chunk_size)
    unvoiced_regions = []
    for i in range(0, len(
            voiced_unvoiced_starting_info_object["unvoicedStart"])):
        unvoiced_regions.append(
            x[voiced_unvoiced_starting_info_object['USamp'][i]])
    unvoiced_regions = numpy.abs(unvoiced_regions)
    return unvoiced_regions


def starting_info(x, f0, fs, chunk_size):
    """
    starting_info(x,f0,fs,chunk_size)
                    starting_info specifies the voiced and unvoiced starting points.
                    It also contains the samples of the voiced and unvoiced samples.
                    It will help,mainly,to get the voiced_samples.
            Parameter:	x- Discrete Data
                                    f0- Fundamental Frequency
                                    fs- Sampling Frequency
                                    chunk_size

            Returns:	voiced_unvoiced_starting_info_object- Contains object of the
                                    unvoicedStart,VoicedStart,unvoicedSamples('USamp') and voicedSamples(VSamp)
    """
    voiced_unvoiced_starting_info_object = {
        "unvoicedStart": [],
        "voicedStart": [],
        "USamp": [],
        "VSamp": []}
    unvoiced_starting_pts(
        x,
        fs,
        f0,
        voiced_unvoiced_starting_info_object,
        chunk_size)
    voiced_starting_pts(
        x,
        fs,
        f0,
        voiced_unvoiced_starting_info_object,
        chunk_size)
    # Starting Info of Voiced/Unvoiced Regions
    return voiced_unvoiced_starting_info_object
