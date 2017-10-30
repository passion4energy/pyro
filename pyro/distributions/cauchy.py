import numbers

import numpy as np
import scipy.stats as spr
import torch
from torch.autograd import Variable

from pyro.distributions.distribution import Distribution


class Cauchy(Distribution):
    """
    Cauchy (a.k.a. Lorentz) distribution.

    This is a continuous distribution which is roughly the ratio of two
    Gaussians if the second Gaussian is zero mean. The distribution is over
    tensors that have the same shape as the parameters `mu`and `gamma`, which
    in turn must have the same shape as each other.

    This is often used in conjunction with `torch.nn.Softplus` to ensure the
    `gamma` parameter is positive.

    :param torch.autograd.Variable mu: Location parameter.
    :param torch.autograd.Variable gamma: Scale parameter. Should be positive.
    """

    def __init__(self, mu, gamma, batch_size=None, *args, **kwargs):
        self.mu = mu
        self.gamma = gamma
        if mu.size() != gamma.size():
            raise ValueError("Expected mu.size() == gamma.size(), but got {} vs {}"
                             .format(mu.size(), gamma.size()))
        if mu.dim() == 1 and batch_size is not None:
            self.mu = mu.expand(batch_size, mu.size(0))
            self.gamma = gamma.expand(batch_size, gamma.size(0))
        super(Cauchy, self).__init__(*args, **kwargs)

    def batch_shape(self, x=None):
        event_dim = 1
        mu = self.mu
        if x is not None and x.size() != mu.size():
            mu = self.mu.expand_as(x)
        return mu.size()[:-event_dim]

    def event_shape(self):
        event_dim = 1
        return self.mu.size()[-event_dim:]

    def shape(self, x=None):
        return self.batch_shape(x) + self.event_shape()

    def sample(self):
        np_sample = spr.cauchy.rvs(self.mu.data.cpu().numpy(),
                                   self.gamma.data.cpu().numpy())
        if isinstance(np_sample, numbers.Number):
            np_sample = [np_sample]
        sample = Variable(torch.Tensor(np_sample).type_as(self.mu.data))
        return sample

    def batch_log_pdf(self, x):
        # expand to patch size of input
        mu = self.mu.expand(self.shape(x))
        gamma = self.gamma.expand(self.shape(x))
        x_0 = torch.pow((x - mu)/gamma, 2)
        px = np.pi * gamma * (1 + x_0)
        log_pdf = -1 * torch.sum(torch.log(px), -1)
        batch_log_pdf_shape = self.batch_shape(x) + (1,)
        return log_pdf.contiguous().view(batch_log_pdf_shape)

    def analytic_mean(self):
        raise ValueError("Cauchy has no defined mean")

    def analytic_var(self):
        raise ValueError("Cauchy has no defined variance")
