#!/usr/bin/env bash

if [[ -e /usr/bin/hr ]]; then
    hr cmd pip2_install numpy scipy
    hr cmd pip2_install flask sox>=1.2.9 colorlog pinyin==0.2.5 pyyaml
    hr cmd pip2_install pysptk==0.1.4
fi
