from contextlib import contextmanager

import torch
from torch import nn
from torch.nn import functional as F

_REQUIRES_GRAD_ATTR = '_original_requires_grad'

__all__ = [
    'original_requires_grad',
    'record_original_requires_grad',
    'restore_original_requires_grad',
    'disable_param_grad',
    'im2col_2d',
    'add_value_to_diagonal'
]


def original_requires_grad(module, param_name):
    param = getattr(module, param_name, None)
    return param is not None and getattr(param, _REQUIRES_GRAD_ATTR)


def record_original_requires_grad(param):
    setattr(param, _REQUIRES_GRAD_ATTR, param.requires_grad)


def restore_original_requires_grad(param):
    param.requires_grad = getattr(
        param, _REQUIRES_GRAD_ATTR, param.requires_grad
    )


@contextmanager
def disable_param_grad(model):

    for param in model.parameters():
        record_original_requires_grad(param)
        param.requires_grad = False

    yield
    for param in model.parameters():
        restore_original_requires_grad(param)


def im2col_2d(x: torch.Tensor, conv2d: nn.Module):
    assert x.ndimension() == 4  # n x c x h_in x w_in
    assert isinstance(conv2d, (nn.Conv2d, nn.ConvTranspose2d))

    # n x c(k_h)(k_w) x (h_out)(w_out)
    Mx = F.unfold(
        x,
        conv2d.kernel_size,
        dilation=conv2d.dilation,
        padding=conv2d.padding,
        stride=conv2d.stride
    )

    return Mx


def add_value_to_diagonal(x: torch.Tensor, value):
    if x.is_cuda:
        indices = torch.cuda.LongTensor([[i, i] for i in range(x.shape[0])])
    else:
        indices = torch.LongTensor([[i, i] for i in range(x.shape[0])])
    values = x.new_ones(x.shape[0]).mul(value)
    return x.index_put(tuple(indices.t()), values, accumulate=True)
