import os
import yaml

# File path for the template YAML
TEMPLATE_PATH = "./examples/workflow_template.yaml"


def load_yaml(path):
    """Load and return the YAML content from the given path."""
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading YAML file: {e}")
        return None


def save_yaml(data, path):
    """Save the given data to a YAML file at the specified path."""
    try:
        with open(path, "w") as f:
            yaml.dump(data, f, sort_keys=False)
        return True
    except Exception as e:
        print(f"Error saving YAML file: {e}")
        return False


def prompt(prompt_text, default):
    """
    Prompt the user with a message that includes a default value.
    If the user input is empty, return the default value.
    """
    user_input = input(f"{prompt_text} (default: {default}): ")
    return user_input if user_input else str(default)


def update_input_block(block):
    """
    Update the 'input.rhd2000' section of a YAML block.
    Prompts the user for input file path and optional digital/analog channels.
    """
    new_input = prompt("Enter path and filter spec for input files", "")
    block["input.rhd2000"]["sessions"] = [new_input]

    # Build aux_channels dictionary based on user input.
    aux_channels = {}

    include_dig_in = prompt("Include digital inputs? (y/n)", "y")
    if include_dig_in.lower() in ("y", "yes"):
        digital_str = prompt("Enter digital input indices (comma separated)", "")
        if digital_str.strip():
            aux_channels["digital_in"] = [int(x.strip()) for x in digital_str.split(",") if x.strip().isdigit()]

    include_ana_in = prompt("Include analog inputs? (y/n)", "y")
    if include_ana_in.lower() in ("y", "yes"):
        analog_str = prompt("Enter analog input indices (comma separated)", "")
        if analog_str.strip():
            aux_channels["analog_in"] = [int(x.strip()) for x in analog_str.split(",") if x.strip().isdigit()]

    # If aux channels were provided, add them to the block
    if aux_channels:
        block["input.rhd2000"]["aux_channels"] = aux_channels
    else:
        block["input.rhd2000"]["aux_channels"] = "[]"


def update_checkpoint_block(block, output_dir):
    """
    Update the 'checkpoint' section of a YAML block.
    Adjusts the file path based on the provided output directory.
    """
    default_final_name = "final.h5"
    current_file = block["checkpoint"].get("file", "")
    file_name = os.path.basename(current_file) if current_file else default_final_name

    if file_name == default_final_name:
        new_final_name = prompt("Enter name for final checkpoint file", default_final_name)
        new_file = os.path.join(output_dir, new_final_name)
    else:
        new_file = os.path.join(output_dir, file_name)

    block["checkpoint"]["file"] = new_file


def main():
    # Load the template YAML file.
    data = load_yaml(TEMPLATE_PATH)
    if data is None:
        return

    # Ask for output file path and output directory.
    output_yaml_path = prompt("Where should the new YAML file be saved?", "updated_workflow.yaml")
    output_dir = prompt("Enter path to output files", "")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Process each block in the YAML file.
    for block in data:
        if "input.rhd2000" in block:
            update_input_block(block)
        if "checkpoint" in block and isinstance(block["checkpoint"], dict):
            update_checkpoint_block(block, output_dir)

    # Save the updated YAML.
    if save_yaml(data, output_yaml_path):
        print(f"Updated YAML saved to {output_yaml_path}")
    else:
        print("Failed to save updated YAML file.")


if __name__ == "__main__":
    main()