#!/usr/bin/env bash

if [[ -e /usr/bin/hr ]]; then
    hr cmd pip2_install flask sox>=1.2.9 pysptk>=0.1.4 numpy scipy colorlog
fi
