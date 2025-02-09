import torch


class Hypergrad:
    """Implicit differentiation for auxiliary parameters.
    This implementation follows the Algs. in "Optimizing Millions of Hyperparameters by Implicit Differentiation"
    (https://arxiv.org/pdf/1911.02590.pdf), with small differences.

    """

    def __init__(self, learning_rate=.1, truncate_iter=3):
        self.learning_rate = learning_rate
        self.truncate_iter = truncate_iter

    # algo 2 in ho
    def grad(self, loss_val, grad_train, aux_params, shared_params):
        """Calculates the gradients w.r.t \phi dloss_aux/dphi, see paper for details

        :param loss_val:
        :param loss_train:
        :param aux_params:
        :param params:
        :return:
        """
        # dL_val_dw
        # v1
        dloss_val_dparams = torch.autograd.grad(
            loss_val,
            shared_params,
            retain_graph=True,
            allow_unused=True
        )
        
        v2 = self._approx_inverse_hvp(dloss_val_dparams, grad_train, shared_params)

        v3 = torch.autograd.grad(
            grad_train,
            aux_params,
            grad_outputs=v2,
            allow_unused=True
        )
        # assume the dL_val_d_lambda is always zero

        return list(-g for g in v3)

    def _approx_inverse_hvp(self, dloss_val_dparams, grad_train, shared_params):
        """

        :param dloss_val_dparams: dL_val/dW
        :param dloss_train_dparams: dL_train/dW
        :param params: weights W
        :return: dl_val/dW * dW/dphi
        """
        p = v = dloss_val_dparams

        for _ in range(self.truncate_iter):
            grad = torch.autograd.grad(
                    grad_train,
                    shared_params,
                    grad_outputs=v,
                    retain_graph=True,
                    allow_unused=True
                )
            #print("dloss_train_dparams:",dloss_train_dparams)
            grad = [g * self.learning_rate for g in grad]  # scale: this a is key for convergence
            v = [curr_v - curr_g for (curr_v, curr_g) in zip(v, grad)]
            # note: different than the pseudo code in the paper
            p = [curr_p + curr_v for (curr_p, curr_v) in zip(p, v)]

        return list(pp for pp in p)
