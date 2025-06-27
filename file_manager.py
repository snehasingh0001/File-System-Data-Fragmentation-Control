from disk import Disk

disk = Disk()
allocation_before_defrag = {}

def allocate_file(file_name, file_size):
    success = disk.allocate(file_name, file_size)
    if success:
        allocation_before_defrag[file_name] = disk.files[file_name].copy()
        return True, disk.files[file_name]
    else:
        return False, []

def get_disk_state():
    return disk.get_state()

def defragment():
    global allocation_before_defrag
    score_before = disk.fragmentation_score()
    before_allocations = allocation_before_defrag.copy()

    disk.defragment_disk()

    score_after = disk.fragmentation_score()
    after_allocations = disk.files.copy()

    # Clear before allocations after defrag
    allocation_before_defrag = {}

    return {
        "disk_state": disk.get_state(),
        "score_before": score_before,
        "score_after": score_after,
        "allocations_before": before_allocations,
        "allocations_after": after_allocations
    }
def allocate_multiple_files(file_infos):
    """
    file_infos: list of tuples -> [(file_name1, size1), (file_name2, size2), ...]
    """
    results = {}
    for file_name, size in file_infos:
        success = disk.allocate(file_name, size)
        if success:
            allocation_before_defrag[file_name] = disk.files[file_name].copy()
            results[file_name] = {
                "success": True,
                "blocks": disk.files[file_name]
            }
        else:
            results[file_name] = {
                "success": False,
                "blocks": []
            }
    return results