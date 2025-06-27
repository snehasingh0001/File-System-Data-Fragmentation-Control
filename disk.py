class Disk:
    def _init_(self, size=100):
        self.size = size
        self.blocks = ['Free'] * size
        self.files = {}  
    def allocate(self, file_name, file_size):
        free_blocks = [i for i, block in enumerate(self.blocks) if block == 'Free']
        if len(free_blocks) < file_size:
            return False

        allocated_blocks = free_blocks[:file_size]
        for block in allocated_blocks:
            self.blocks[block] = file_name
        self.files[file_name] = allocated_blocks
        return True

    def defragment_disk(self):
        new_blocks = ['Free'] * self.size
        current_index = 0
        new_files = {}
        for file_name, blocks in self.files.items():
            length = len(blocks)
            new_files[file_name] = list(range(current_index, current_index + length))
            for i in range(length):
                new_blocks[current_index + i] = file_name
            current_index += length
        self.blocks = new_blocks
        self.files = new_files

    def get_state(self):
        return self.blocks

    def fragmentation_score(self):
        fragmented_files = 0
        for blocks in self.files.values():
            if len(blocks) <= 1:
                continue
            sorted_blocks = sorted(blocks)
            for i in range(len(sorted_blocks) - 1):
                if sorted_blocks[i] + 1 != sorted_blocks[i + 1]:
                    fragmented_files += 1
                    break
        return fragmented_files