import numpy as np


def split_data(
    x_train,
    y_train,
    mp_size,
    dp_size,
    rank,
):
    """The function for splitting the dataset uniformly across data parallel groups

    Parameters
    ----------
        x_train : np.ndarray float32
            the input feature of MNIST dataset in numpy array of shape (data_num, feature_dim)

        y_train : np.ndarray int32
            the label of MNIST dataset in numpy array of shape (data_num,)

        mp_size : int
            Model Parallel size

        dp_size : int
            Data Parallel size

        rank : int
            the corresponding rank of the process

    Returns
    -------
        split_x_train : np.ndarray float32
            the split input feature of MNIST dataset in numpy array of shape (data_num/dp_size, feature_dim)

        split_y_train : np.ndarray int32
            the split label of MNIST dataset in numpy array of shape (data_num/dp_size, )

    Note
    ----
        please split the data uniformly across data parallel groups and
        do not shuffle the index as we will shuffle them later
    """

    """TODO: Your code here"""

    # Try to get the correct start_idx and end_idx from dp_size, mp_size and rank and return
    # the corresponding data
    dp_group_id = rank // mp_size
    data_num = x_train.shape[0]
    chunk_size = data_num // dp_size
    start_idx = dp_group_id * chunk_size
    end_idx = start_idx + chunk_size

    split_x_train = x_train[start_idx:end_idx]
    split_y_train = y_train[start_idx:end_idx]

    return split_x_train, split_y_train