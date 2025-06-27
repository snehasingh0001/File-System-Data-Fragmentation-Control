from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
import zipfile
import random
import shutil

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# Constants
TOTAL_BLOCKS = 100
BLOCK_SIZE_KB = 1
DISK_CAPACITY_KB = TOTAL_BLOCKS * BLOCK_SIZE_KB
UPLOAD_FOLDER = 'uploads'
EXTRACT_FOLDER = 'extracted'
REPORTS_FOLDER = 'reports'
COMPRESSED_FOLDER = 'compressed'

# Global state
ALLOCATION_STATE = ['Free'] * TOTAL_BLOCKS
ALLOCATED_PATHS = {}
OVERSIZE_PATH = None

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACT_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)
os.makedirs(COMPRESSED_FOLDER, exist_ok=True)

# Utility Functions
def get_file_size_kb(path):
    if not os.path.exists(path):
        return 0
    if os.path.isdir(path):
        total_size = 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return round(total_size / 1024, 2)
    else:
        return round(os.path.getsize(path) / 1024, 2)

def calculate_fragmentation(block_indexes):
    if len(block_indexes) <= 1:
        return 0.0
    fragments = 1
    for i in range(1, len(block_indexes)):
        if block_indexes[i] != block_indexes[i - 1] + 1:
            fragments += 1
    return 1 - (1 / fragments)

def update_utilization():
    used = sum(1 for b in ALLOCATION_STATE if b != 'Free')
    return round((used / TOTAL_BLOCKS) * 100, 2)

# Routes
@app.route('/')
def index():
    return render_template("index.html",
        utilization_percent=update_utilization(),
        disk_state=ALLOCATION_STATE,
        allocated_paths=ALLOCATED_PATHS,
        oversize_path=OVERSIZE_PATH,
        defrag_report_available=os.path.exists(os.path.join(REPORTS_FOLDER, "defrag_report.txt"))
    )

@app.route('/upload_zip', methods=['POST'])
def upload_zip():
    file = request.files['zip_file']
    if file and file.filename.endswith('.zip'):
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(EXTRACT_FOLDER)
        flash("ZIP uploaded and extracted successfully.")
    else:
        flash("Invalid file. Please upload a ZIP file.")
    return redirect(url_for('index'))

@app.route('/allocate_path', methods=['POST'])
def allocate_path():
    global OVERSIZE_PATH
    path = request.form.get('file_path')
    if not path:
        flash("Please enter a valid file or folder path.")
        return redirect(url_for('index'))

    size_kb = get_file_size_kb(path)
    if size_kb > DISK_CAPACITY_KB:
        OVERSIZE_PATH = path
        flash(f"File '{path}' is too large to allocate ({size_kb} KB).")
        return redirect(url_for('index'))

    size_in_blocks = random.randint(2, 8)
    free_indexes = [i for i, b in enumerate(ALLOCATION_STATE) if b == 'Free']

    if len(free_indexes) < size_in_blocks:
        flash("Not enough space to allocate.")
        return redirect(url_for('index'))

    selected_blocks = sorted(random.sample(free_indexes, size_in_blocks))
    for i in selected_blocks:
        ALLOCATION_STATE[i] = path

    fragmentation_score = calculate_fragmentation(selected_blocks)
    ALLOCATED_PATHS[path] = {
        'blocks_allocated': size_in_blocks,
        'block_indexes': selected_blocks,
        'fragmentation_score': fragmentation_score
    }

    OVERSIZE_PATH = None
    flash(f"Allocated path '{path}' using {size_in_blocks} blocks.")
    return redirect(url_for('index'))

@app.route('/simulate_random', methods=['POST'])
def simulate_random():
    path = f"File_{len(ALLOCATED_PATHS) + 1}"
    return allocate_random_file(path)

def allocate_random_file(path):
    size_in_blocks = random.randint(2, 8)
    free_indexes = [i for i, b in enumerate(ALLOCATION_STATE) if b == 'Free']

    if len(free_indexes) < size_in_blocks:
        flash("Not enough space to simulate allocation.")
        return redirect(url_for('index'))

    selected_blocks = sorted(random.sample(free_indexes, size_in_blocks))
    for i in selected_blocks:
        ALLOCATION_STATE[i] = path

    fragmentation_score = calculate_fragmentation(selected_blocks)
    ALLOCATED_PATHS[path] = {
        'blocks_allocated': size_in_blocks,
        'block_indexes': selected_blocks,
        'fragmentation_score': fragmentation_score
    }

    flash(f"Simulated random allocation for '{path}' using {size_in_blocks} blocks.")
    return redirect(url_for('index'))

@app.route('/compress', methods=['POST'], endpoint='compress')
def compress_and_download():
    path = request.form.get('original_path')
    if not path or not os.path.exists(path):
        flash("Original file/folder not found.")
        return redirect(url_for('index'))

    base_name = os.path.basename(path).replace(" ", "_")
    compressed_path = os.path.join(COMPRESSED_FOLDER, base_name)

    try:
        if os.path.isdir(path):
            # Compress the directory
            shutil.make_archive(compressed_path, 'zip', path)
            zip_file = f"{compressed_path}.zip"
        else:
            # Compress a single file
            zip_file = f"{compressed_path}.zip"
            with zipfile.ZipFile(zip_file, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(path, arcname=os.path.basename(path))

        flash(f"Compressed and ready to download: {os.path.basename(zip_file)}")
        return send_file(zip_file, as_attachment=True)

    except Exception as e:
        flash(f"Compression failed: {e}")
        return redirect(url_for('index'))


@app.route('/defragment', methods=['POST'])
def defragment():
    global ALLOCATION_STATE
    new_state = ['Free'] * TOTAL_BLOCKS
    new_allocations = {}
    current_index = 0
    report_lines = []

    for path, info in ALLOCATED_PATHS.items():
        block_count = info['blocks_allocated']
        new_blocks = list(range(current_index, current_index + block_count))
        for i in new_blocks:
            new_state[i] = path
        new_fragmentation = calculate_fragmentation(new_blocks)
        new_allocations[path] = {
            'blocks_allocated': block_count,
            'block_indexes': new_blocks,
            'fragmentation_score': new_fragmentation
        }
        report_lines.append(f"{path}: {block_count} blocks moved to {new_blocks}")
        current_index += block_count

    ALLOCATION_STATE = new_state
    ALLOCATED_PATHS.clear()
    ALLOCATED_PATHS.update(new_allocations)

    with open(os.path.join(REPORTS_FOLDER, "defrag_report.txt"), "w") as report_file:
        report_file.write("\n".join(report_lines))

    flash("Disk defragmented successfully.")
    return redirect(url_for('index'))

@app.route('/download_report')
def download_report():
    return send_file(os.path.join(REPORTS_FOLDER, "defrag_report.txt"), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)