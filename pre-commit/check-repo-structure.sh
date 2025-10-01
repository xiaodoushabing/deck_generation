#!/bin/bash

# Function to handle file checks
# $1: path to check
# $2: expected file type:
    # 'f': must be a file
    # 'd': must be a directory
    # 'd_nonempty': must be a non-empty directory
    # 'folder_pattern': special check for folder with naming patterns
    # 'file_or_folder': special check for entry that can be file or folder

REQUIRED_PATHS=(
    "./r_folder|folder_pattern"
    "./requirements.txt|f"
    "./src|d_nonempty"
    "./tests|d"
    "dep_script|file_or_folder"
)

OPTIONAL_PATHS=(
    "./.gitignore|f"
    "./pre-commit|d"
)

# Define folder-to-files mapping
declare -A FOLDER_FILES
FOLDER_FILES["./r_folder"]="r_file_1.py r_file_2.py r_file_3.py r_file_4.py"
# Extend here for additional folders:
# FOLDER_FILES["./r_folder_project2"]="r_file_10.py r_file_11.py r_file_12.py"

# Define file-or-folder mapping
declare -A FILE_OR_FOLDER
FILE_OR_FOLDER["dep_script"]="./dep_script.py|f ./dep_script|d"

check_path() {
    local path="$1"
    local type="$2"

    case "$type" in
        f)
            if [ ! -f "$path" ]; then
                echo "STRUCTURE VIOLATION: Required file not found: $path."
                return 1
            fi
            ;;
        d)
            if [ ! -d "$path" ]; then
                echo "STRUCTURE VIOLATION: Required directory not found: $path"
                return 1
            fi
            ;;
        d_nonempty)
            if [ ! -d "$path" ] || [ -z "$(ls -A "$path")" ]; then
                echo "STRUCTURE VIOLATION: Required directory is missing or empty: $path."
                return 1
            fi
            ;;
        folder_pattern)
            check_folder_pattern_structure "$path"|| return 1
            ;;
        file_or_folder)
            check_file_or_folder_exists "$path" || return 1
            ;;
        *)
            echo "Unknown type defined: $type for path $path."
            return 1
            ;;
    esac
    return 0
}

# Check folder pattern structure
# The r_ means that these files are required.
# Change the r_file* and r_folder* to match your folder naming convention
check_folder_pattern_structure() {
    local path="$1"
    local all_folders=("$path"*)
    local required_files="${FOLDER_FILES[$path]}"
    local exit_status=0

    # Filter to only actual directories first
    local matching_folders=()
    for item in "${all_folders[@]}"; do
        if [ -d "$item" ]; then
            matching_folders+=("$item")
        fi
    done

    if [ "${#matching_folders[@]}" -lt 1 ]; then
        echo "STRUCTURE VIOLATION: No directories found matching pattern: $path*"
        return 1
    fi

    # If only one folder exists, it must be named as "$path"
    if [ "${#matching_folders[@]}" -eq 1 ] && [ "${matching_folders[0]}" != "$path" ]; then
        echo "STRUCTURE VIOLATION: Folder must be named as $path if only one folder exists."
        return 1
    fi


    if [ -n "$required_files" ]; then
        read -ra files <<< "$required_files"
    fi

    # Now check required files in each valid folder
    for folder in "${matching_folders[@]}"; do
        for file in "${files[@]}"; do
            if [ ! -f "$folder/$file" ]; then
                echo "STRUCTURE VIOLATION: Required file not found: $folder/$file"
                exit_status=1
            fi
        done
    done

    return $exit_status
}

# Check file or folder exists
check_file_or_folder_exists() {
    local path="$1"
    local options="${FILE_OR_FOLDER[$path]}"

    if [ -z "$options" ]; then
        echo "SCRIPT CONFIG ERROR: Missing FILE_OR_FOLDER configuration for: $path. Update FILE_OR_FOLDER array in script"
        return 1
    fi

    read -ra paths <<< "$options"

    for option in "${paths[@]}"; do
        IFS='|' read -r option type <<< "$option"
        if [ -z "$option" ]; then
            echo "SCRIPT CONFIG ERROR: Empty option found in FILE_OR_FOLDER mapping for: $path"
            return 1
        fi
        # Check if the option is a file or directory based on type
        if [ -z "$type" ]; then
            echo "SCRIPT CONFIG ERROR: Missing type for option in FILE_OR_FOLDER mapping for: $path"
            return 1
        fi
        if [ -"$type" "$option" ]; then
            return 0 # Found at least one valid option
        fi
    done

    echo "STRUCTURE VIOLATION: None of the following found: $options"
    return 1
}


echo "Verifying repository structure..."

EXIT_CODE=0

# Check required paths
for item in "${REQUIRED_PATHS[@]}"; do
    IFS='|' read -r file_path file_type <<< "$item"
    check_path "$file_path" "$file_type" || EXIT_CODE=1
done

# # Check optional paths (don't affect exit code)
# echo "Checking optional paths..."
# for item in "${OPTIONAL_PATHS[@]}"; do
#     IFS='|' read -r file_path file_type <<< "$item"
#     if ! check_path "$file_path" "$file_type"; then
#         echo "INFO: Optional item missing: $file_path"
#     fi
# done

exit $EXIT_CODE