from ttsbase import TTSBase
from visemes import BaseVisemes

class Numb_Visemes(BaseVisemes):
    # Mapping is approx. May need tunning
    # All phonemes are from cereproc documentation
    # https://www.cereproc.com/files/CereVoiceCloudGuide.pdf
    default_visemes_map = {
        'A-I': ['A','AA','AI','AU','AE','AH','AW','AX','AY','EY',],
        'E': ['E','E@','EI','II','IY','EI', 'EH',],
        'F-V': ['F','V'],
        'Q-W': ['W'],
        'L': ['@', '@@', 'I', 'I@','IH','L', 'R', 'Y', 'R'],
        'C-D-G-K-N-S-TH': ['CH','D','DH','G','H','HH','JH','K','N','NG','S','SH','T','TH','Z','ZH','DX','ER',],
        'M': ['B','M','P'],
        'O': ['O','OI','OO','OU','AO','OW','OY',],
        'U': ['U','U@','UH','UU','UW'],
        'Sil': ['SIL']
    }


class NumbTTS(TTSBase):

    def get_visemes(self, phonemes):
        visemes = []
        for ph in phonemes:
            v = self.get_viseme(ph)
            if v is not None:
                visemes.append(v)
        logger.debug("Get visemes {}".format(visemes))
        return visemes

    def do_tts(self, tts_data):
        text = tts_data.text
        fname = '{}.wav'.format(os.path.join(self.output_dir, text.strip()))
        if os.path.isfile(fname):
            shutil.copy(fname, tts_data.wavout)
            try:
                tts_data.phonemes = self.get_phonemes(fname)
            except Exception as ex:
                logger.error(traceback.format_exc())
                tts_data.phonemes = []

    def get_phonemes(self, fname):
        timing = '{}.yaml'.format(os.path.splitext(fname)[0])
        if os.path.isfile(timing):
            with open(timing) as f:
                phonemes = yaml.load(f)
            logger.info("Get timing info from file")
        else:
            phonemes = [
                {'type': 'phoneme', 'name': phoneme[0],
                    'start': phoneme[1], 'end': phoneme[2]}
                    for phoneme in audio2phoneme(fname)]
            with open(timing, 'w') as f:
                yaml.dump(phonemes, f)
            logger.info("Write timing info to file")
        return phonemes
