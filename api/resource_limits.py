
import platform


# Maximum worker address space: 384 MiB
MAX_MEMORY_MB = 384

# CPU time limits (not wall-clock time)
CPU_SOFT_LIMIT = 20
CPU_HARD_LIMIT = 22


def apply_resource_limits():
    """Apply resource limits to a Linux conversion worker."""

    # Keep local macOS and Windows development unchanged
    if platform.system() != "Linux":
        return False

    import resource

    memory_bytes = MAX_MEMORY_MB * 1024 * 1024

    # Do not exceed any existing system-imposed hard limit
    _, memory_hard = resource.getrlimit(
        resource.RLIMIT_AS
    )

    if memory_hard == resource.RLIM_INFINITY:
        memory_limit = memory_bytes
    else:
        memory_limit = min(memory_bytes, memory_hard)

    # Limit the process's virtual address space
    resource.setrlimit(
        resource.RLIMIT_AS,
        (memory_limit, memory_limit)
    )

    # Check existing CPU limits
    _, cpu_hard = resource.getrlimit(
        resource.RLIMIT_CPU
    )

    if cpu_hard == resource.RLIM_INFINITY:
        soft_limit = CPU_SOFT_LIMIT
        hard_limit = CPU_HARD_LIMIT
    else:
        hard_limit = min(CPU_HARD_LIMIT, cpu_hard)
        soft_limit = min(CPU_SOFT_LIMIT, hard_limit)

    # Limit CPU seconds used by this worker
    resource.setrlimit(
        resource.RLIMIT_CPU,
        (soft_limit, hard_limit)
    )

    return True
