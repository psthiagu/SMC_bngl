#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 3 11:37:30 2020

@author: ?
""" 
import numpy as np

class HypothesisTester(object):
    """Test a hypothesis about a property based on random samples.

    The test is posed as follows. The null hypothesis H0 is that
    P_{satisfied} >= prob, and the alternative hypothesis is that
    P_{satisfied} < prob. The parameter alpha and beta define the

    Parameters
    -----------
    prob : float
        The probability threshold for the hypothesis. Between 0 and 1.
    alpha : float
        The Type-I error limit specified for deciding between the alternative
        hypotheses. Between 0 and 1.
    beta : float
        The Type-II error limit specified for deciding between the alternative
        hypotheses. Between 0 and 1.
    delta : float
        The indifference parameter, which defines an interval around `prob` in
        both directions inside which it is acceptable to conclude either of the
        alternative hypotheses.
    """
    def __init__(self, prob, alpha, beta, delta):
        self.prob = prob
        self.alpha = alpha
        self.beta = beta
        self.delta = delta
        self.logA = np.log((1 - self.beta) / self.alpha)
        self.logB = np.log(self.beta / (1 - self.alpha))

    def get_logq(self, samples):
        """Return the logarithm of the test ratio given a set of samples.

        This function is typically not used from outside but can be useful
        for tracking and plotting how the value of the test ratio changes as
        samples are collected.

        Parameters
        ----------
        samples : list[bool]
            A list of True/False values corresponding to the satisfaction of
            a property in a series of random samples.

        Returns
        -------
        logq : float
            The test ratio calculated given the samples and test parameters.
        """
        ps = len([s for s in samples if s])
        ns = len(samples) - ps
        term1 = ps * np.log(self.prob - self.delta)
        term2 = ns * np.log(1 - (self.prob - self.delta))
        term3 = ps * np.log(self.prob + self.delta)
        term4 = ns * np.log(1 - (self.prob + self.delta))
        logq = term1 + term2 - term3 - term4
        return logq

    def test(self, samples):
        """Return the result of the hypothesis test or None if not decidable.

        Parameters
        ----------
        samples : list[bool]
            A list of True/False values corresponding to the satisfaction of
            a property in a series of random samples.

        Returns
        -------
        result : 0, 1 or None
            The result of the hypothesis test with 0 corresponding to the
            null hypothesis, 1 corresponding to the alternative hypothesis.
            If the test cannot yet be decided with the given set of samples,
            None is returned.
        """
        logq = self.get_logq(samples)
        if logq <= self.logB:
            return 0
        elif logq >= self.logA:
            return 1
        else:
            return None
