from disk import DiskBlock

def defragment(disk):
    print("Starting defragmentation...")
    new_blocks = []
    for block in disk.blocks:
        if block.occupied:
            new_blocks.append(block)
    free_blocks = [DiskBlock(i) for i in range(len(disk.blocks) - len(new_blocks))]
    disk.blocks = new_blocks + free_blocks
    # Reassign block IDs after defragmentation
    for i, block in enumerate(disk.blocks):
        block.block_id = i
    print("Defragmentation completed.")