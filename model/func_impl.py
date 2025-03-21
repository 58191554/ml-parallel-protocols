import numpy as np
from mpi4py import MPI


def get_info(
    comm,
    rank: int,
    mp_size: int,
    dp_size: int,
    is_fc1: bool,
    is_megatron_mp: bool,
    in_dim: int,
    out_dim: int,
):
    """The function that prepare necessary information for parallel training.

    Parameters
    ----------
        comm : Communicator
            the global mpi communicator

        rank : int
            the corresponding rank of the process

        mp_size : int
            Model Parallel size

        dp_size : int
            Data Parallel size

        is_fc1 : int
            A boolean indicating whether the current layer is the first layer or not

        is_megatron_mp : boolean
            A boolean indicating whether we are using Megatron-style Model Parallel or not

        in_dim : int
            An integer corresponds to the original input feature dimension

        out_dim : int
            An integer corresponds to the original output feature dimension

    Returns
    -------
        mp_idx : int
            An integer corresponds to model parallel communication index

        dp_idx : int
            An integer corresponds to data parallel communication index

        mp_comm : Communicator
            The Model Parallel communicator after split

        dp_comm : Communicator
            The Data Parallel communicator after split

        part_in_dim : int
            An integer corresponds to the input feature dimension after specific parallelism

        part_out_dim : int
            An integer corresponds to the output feature dimension after specific parallelism
    """

    # Get the mp_idx, dp_idx from rank, mp_size and dp_size (you may not need to use all three of them)
    mp_idx = rank % mp_size
    dp_idx = rank // mp_size

    # Get the model/data parallel communication groups
    # the model/data parallel communication group is required to apply mpi operations within the scope of the group
    # Hint: try to figure out the relationship between the mp_idx, dp_idx with the mp/dp communication group
    #       and use the comm.Split() function to get the corresponding group.

    mp_comm = comm.Split(color=dp_idx, key=rank)
    dp_comm = comm.Split(color=mp_idx, key=rank)

    # Derive the part_in_dim and part_out_dim depend on is_fc1 and is_megatron_mp

    if is_fc1:
        part_in_dim = in_dim
        part_out_dim = out_dim // mp_size
    else:
        if is_megatron_mp:
            part_in_dim = in_dim // mp_size
            part_out_dim = out_dim
        else:
            part_in_dim = in_dim
            part_out_dim = out_dim // mp_size
    
    return mp_idx, dp_idx, mp_comm, dp_comm, part_in_dim, part_out_dim


def naive_collect_forward_input(
    x: np.ndarray,
    mp_comm,
    mp_size: int,
):
    """The function for collecting layer fc2's inputs across different nodes with naive model parallelism

    Parameters
    ----------
        x : np.ndarray
            layer input for a single node of shape (batch_size, part_in_dim)

        mp_comm : Communicator
            The Model Parallel communicator

        mp_size : int
            Model Parallel size

    Returns
    -------
        collected_x : np.ndarray
            collected layer inputs across different nodes of shape (batch_size, in_dim)

    """
    # Note: you may want to ensure that the source variable and destination variable in your mpi func call should
    #       have the same data type, otherwise you will not collect the correct value.

    # Hint: Try to figure out the way MPI calls deal with the destination memory layout for 2d matrix transfer, this might
    #       might not align with your expected layout. In order to get the correct layout, you may wish to use some NumPy
    #       functions (np.split and np.concatenate might be helpful).

    gathered = mp_comm.allgather(x)
    collected_x = np.concatenate(gathered, axis=1)
    return collected_x


def naive_collect_forward_output(
    out: np.ndarray,
    mp_comm,
    mp_size: int,
):
    """The function for collecting layer fc2's outputs across different nodes with naive model parallelism

    Parameters
    ----------
        out : np.ndarray
            layer output for a single node of shape (batch_size, part_out_dim)

        mp_comm : Communicator
            The Model Parallel communicator

        mp_size : int
            Model Parallel size

    Returns
    -------
        collected_out : np.ndarray
            collected layer outputs across different nodes of shape (batch_size, out_dim)

    """

    gathered = mp_comm.allgather(out)
    collected_out = np.concatenate(gathered, axis=1)
    return collected_out

def megatron_collect_forward_input(
    x: np.ndarray,
    mp_comm,
    mp_size: int,
):
    """The function for collecting layer fc2's inputs across different nodes with megatron-style model parallelism

    Parameters
    ----------
        x : np.ndarray
            layer input for a single node of shape (batch_size, part_in_dim)

        mp_comm : Communicator
            The Model Parallel communicator

        mp_size : int
            Model Parallel size

    Returns
    -------
        collected_x : np.ndarray
            collected layer inputs across different nodes of shape (batch_size, in_dim)

    """

    """TODO: Your code here"""

    # Hint: you don't need all the input parameters to get the collected_x
    return x

def megatron_collect_forward_output(
    out: np.ndarray,
    mp_comm,
    mp_size: int,
):
    """The function for collecting layer fc2's outputs across different nodes with megatron-style model parallelism

    Parameters
    ----------
        out : np.ndarray
            layer output for a single node of shape (batch_size, part_out_dim)

        mp_comm : Communicator
            The Model Parallel communicator

        mp_size : int
            Model Parallel size

    Returns
    -------
        collected_out : np.ndarray
            collected layer outputs across different nodes of shape (batch_size, out_dim)

    """
    # Hint: try to work through a toy forward example for megatron-style model parallel to figure out the
    #       the communication functions that you might need
    collected_out = np.empty_like(out)
    mp_comm.Allreduce(out, collected_out, op=MPI.SUM)
    return collected_out

def naive_collect_backward_output(
    output_grad: np.ndarray,
    mp_group_idx: int,
    mp_size: int,
):
    """The function for collecting layer fc2's output_grad across different nodes with naive model parallelism

    Parameters
    ----------
        output_grad : np.ndarray
            layer output_grad for a single node of shape (batch_size, out_dim)

        mp_group_idx : int
            The Model Parallel group idx

        mp_size : int
            Model Parallel size

    Returns
    -------
        collected_output_grad : np.ndarray
            collected layer output_grad across different nodes of shape (batch_size, part_out_dim)

    """
    # Hint: you might want to use np.split to get the collected_output_grad for each MP node
    parts = np.split(output_grad, mp_size, axis=1)
    collected_output_grad = parts[mp_group_idx]
    return collected_output_grad

def naive_collect_backward_x(
    grad_x: np.ndarray,
    mp_comm,
    mp_size: int,
):
    """The function for collecting layer fc2's grad_x across different nodes with naive model parallelism

    Parameters
    ----------
        grad_x : np.ndarray
            layer backward grad_x for a single node of shape (batch_size, in_dim)

        mp_comm : Communicator
            The Model Parallel communicator

        mp_size : int
            Model Parallel size

    Returns
    -------
        collected_grad_x : np.ndarray
            collected layer backward grad_x across different nodes of shape (batch_size, part_in_dim)

    """
    # Hint 1: The communication pattern for this function can be seen as the reverse of its forward
    #         , so you might to check the naive_collect_forward_output() impl.

    # Hint 2: You might want to use reduce_scatter
    # ensure grad_x is contiguous memory layout
    grad_x = np.ascontiguousarray(grad_x)
    batch_size, in_dim = grad_x.shape
    part_in_dim = in_dim // mp_size

    # transpose grad_x: shape becomes (in_dim, batch_size)
    trans_grad_x = grad_x.T.copy()  # ensure new array is contiguous

    # 准备接收缓冲区：每个节点接收 part_in_dim * batch_size 个元素
    recv_buf = np.empty(part_in_dim * batch_size, dtype=grad_x.dtype)

    # use Reduce_scatter to sum the transposed flattened data and scatter to each node
    mp_comm.Reduce_scatter([trans_grad_x.flatten(), MPI.DOUBLE],
                           [recv_buf, MPI.DOUBLE],
                           op=MPI.SUM)

    # reshape the received data: shape becomes (part_in_dim, batch_size), then transpose to (batch_size, part_in_dim)
    collected_grad_x = np.reshape(recv_buf, (part_in_dim, batch_size)).T
    return collected_grad_x

def megatron_collect_backward_output(
    output_grad: np.ndarray,
    mp_group_idx: int,
    mp_size: int,
):
    """The function for collecting layer fc2's output_grad across different nodes with megatron-style model parallelism

    Parameters
    ----------
        output_grad : np.ndarray
            layer output_grad for a single node of shape (batch_size, out_dim)

        mp_group_idx : int
            The Model Parallel group idx

        mp_size : int
            Model Parallel size

    Returns
    -------
        collected_output_grad : np.ndarray
            collected layer output_grad across different nodes of shape (batch_size, part_out_dim)

    """
    # Hint: your implementation should be within one line of code
    return output_grad


def megatron_collect_backward_x(
    grad_x: np.ndarray,
    mp_comm,
    mp_size: int,
):
    """The function for collecting layer fc2's grad_x across different nodes with megatron-style model parallelism

    Parameters
    ----------
        grad_x : np.ndarray
            layer backward grad_x for a single node of shape (batch_size, in_dim)

        mp_comm : Communicator
            The Model Parallel communicator

        mp_size : int
            Model Parallel size

    Returns
    -------
        collected_grad_x : np.ndarray
            collected layer backward grad_x across different nodes of shape (batch_size, part_in_dim)

    """
    # Hint: your implementation should be within one line of code
    return grad_x


def collect_weight_grad(
    grad_w: np.ndarray,
    grad_b: np.ndarray,
    dp_comm,
):
    """The function for collecting weight gradients across data parallel nodes

    Parameters
    ----------
        grad_w : np.ndarray
            gradients value for fc weight on a single node of shape (in_dim, out_dim)

        grad_b : np.ndarray
            gradients value for fc bias on a single node of shape (1, out_dim)

        dp_comm : Communicator
            The Data Parallel communicator

    Returns
    -------
        collected_grad_w : np.ndarray
            collected gradients value of shape (in_dim, out_dim) for fc weight across different nodes

        collected_grad_b : np.ndarray
            collected gradients value of shape (1, out_dim) for fc bias across different nodes

    """
    # Hint: Think about how you might want to aggregate the gradients from different nodes in data parallel training
    collected_grad_w = np.empty_like(grad_w)
    collected_grad_b = np.empty_like(grad_b)
    
    dp_comm.Allreduce(grad_w, collected_grad_w, op=MPI.SUM)
    dp_comm.Allreduce(grad_b, collected_grad_b, op=MPI.SUM)
    
    return collected_grad_w, collected_grad_b