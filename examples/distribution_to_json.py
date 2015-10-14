#!/usr/bin/env python

# Copyright (c) 2015, Ecole Polytechnique Federale de Lausanne, Blue Brain Project
# All rights reserved.
#
# This file is part of NeuroM <https://github.com/BlueBrain/NeuroM>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#     3. Neither the name of the copyright holder nor the names of
#        its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

'''Extract a distribution for the selected feature of the population of neurons among
   the exponential, normal and uniform distribution, according to the minimum ks distance.
   '''

from neurom import ezy
from scipy import stats
import numpy as np
import argparse
import json
from collections import OrderedDict


def parse_args():
    '''Parse command line arguments'''
    parser = argparse.ArgumentParser(
        description='Morphology fit distribution extractor',
        epilog='Note: Outputs json of the optimal distribution \
                and corresponding parameters.')

    parser.add_argument('datapath',
                        help='Path to morphology data file or directory')

    parser.add_argument('feature',
                        help='Feature available for the ezy.neuron')

    return parser.parse_args()


def distribution_fit(data, distribution='norm'):
    '''Calculates and returns the parameters of a distribution'''
    return getattr(stats, distribution).fit(data)


def distribution_error(data, distribution='norm'):
    '''Calculates and returns the distance of a fitted distribution
       from the initial data.
    '''
    params = distribution_fit(data, distribution=distribution)
    return stats.kstest(data, distribution, params)[0]


def test_multiple_distr(data):
    '''Runs the distribution fit for multiple distributions and returns
       the optimal distribution along with the corresponding parameters.
    '''
    distr_to_check = ['norm', 'expon', 'uniform']

    fit_data = {d: distribution_fit(data, d) for d in distr_to_check}

    fit_error = {distribution_error(data, d): d for d in distr_to_check}

    optimal = fit_error.values()[np.argmax(fit_error.iterkeys())]

    return optimal, fit_data[optimal]


def extract_data(data_path, feature):
    '''Loads a list of neurons, extracts feature
       and transforms the fitted distribution in the correct format.
       Returns the optimal distribution, corresponding parameters,
       minimun and maximum values.
    '''
    population = ezy.load_neurons(data_path)

    feature_data = [getattr(n, 'get_' + feature)() for n in population]

    results = {}

    try:
        opt_fit = test_multiple_distr(feature_data)
    except ValueError:
        from itertools import chain
        feature_data = list(chain(*feature_data))
        opt_fit = test_multiple_distr(feature_data)

    results["type"] = opt_fit[0]
    results["params"] = opt_fit[1]
    results["min"] = np.min(feature_data)
    results["max"] = np.max(feature_data)

    return results


def transform_distribution(data):
    '''Transform optimal distribution data into correct format
       based on the distribution type.
    '''
    data_dict = OrderedDict()

    if data["type"] == 'norm':
        data_dict.update({"type": "normal"})
        data_dict.update({"mu": data["params"][0]})
        data_dict.update({"sigma": data["params"][1]})

    elif data["type"] == 'expon':
        data_dict.update({"type": "exponential"})
        data_dict.update({"lambda": data["params"][1]})

    elif data["type"] == 'uniform':
        data_dict.update({"type": "uniform"})

    data_dict.update({"min": data["min"]})
    data_dict.update({"max": data["max"]})
    data_dict.update({"description": "Random text"})

    return data_dict


if __name__ == '__main__':
    args = parse_args()

    d_path = args.datapath

    feat = args.feature

    _result = transform_distribution(extract_data(d_path, feat))

    print json.dumps(_result, indent=2, separators=(',', ': '))
