import os
import subprocess
import sys
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def check_and_install_zipnn():
    try:
        import zipnn
    except ImportError:
        print("zipnn not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "zipnn"])
        import zipnn


def decompress_file(input_file, delete=False, force=False, hf_cache=False,):
    import zipnn

    if not input_file.endswith(".znn"):
        raise ValueError("Input file does not have the '.znn' suffix")

    if os.path.exists(input_file):
        if delete and not hf_cache:
            print(f"Deleting {input_file}...")
            os.remove(input_file)
        else:
            decompressed_path = input_file[:-4]
            if not force and os.path.exists(decompressed_path):

                user_input = (
                    input(f"{decompressed_path} already exists; overwrite (y/n)? ").strip().lower()
                )

                if user_input not in ("yes", "y"):
                    print(f"Skipping {input_file}...")
                    return
            print(f"Decompressing {input_file}...")

            output_file = input_file[:-4]
            zpn = zipnn.ZipNN(is_streaming=True)

            with open(input_file, "rb") as infile, open(output_file, "wb") as outfile:
                d_data = b""
                chunk = infile.read()
                d_data += zpn.decompress(chunk)
                outfile.write(d_data)
                print(f"Decompressed {input_file} to {output_file}")

            if hf_cache:
                # If the file is in the Hugging Face cache, fix the symlinks
                print("Reorganizing Hugging Face cache...")
                try:
                    snapshot_path = os.path.dirname(input_file)
                    blob_name = os.path.join(snapshot_path, os.readlink(input_file))
                    os.rename(output_file, blob_name)
                    os.symlink(blob_name, output_file)
                    
                    print("To delete the original compressed file, run the script with the --delete flag.")
                    if os.path.exists(input_file) and delete:
                        os.remove(input_file)
                except Exception as e:
                    raise Exception(f"Error reorganizing Hugging Face cache: {e}")

    else:
        print(f"Error: The file {input_file} does not exist.")


if __name__ == "__main__":
    check_and_install_zipnn()

    parser = argparse.ArgumentParser(description="Enter a file path to decompress.")
    parser.add_argument("input_file", type=str, help="Specify the path to the file to decompress.")
    parser.add_argument(
        "--delete",
        action="store_true",
        help="A flag that triggers deletion of a single compressed file instead of decompression",
    )
    parser.add_argument(
        "--force", action="store_true", help="A flag that forces overwriting when decompressing."
    )
    parser.add_argument(
        "--hf_cache",
        action="store_true",
        help="A flag that indicates if the file is in the Hugging Face cache.",
    )
    args = parser.parse_args()
    optional_kwargs = {}
    if args.delete:
        optional_kwargs["delete"] = args.delete
    if args.force:
        optional_kwargs["force"] = args.force
    if args.hf_cache:
        optional_kwargs["hf_cache"] = args.hf_cache

    decompress_file(args.input_file, **optional_kwargs)
