"""
PS5 File Renamer
Automatically renames PS5 video clips and screenshots with standardized naming.
"""
import os
import json
import time
import re
import logging
from pathlib import Path
from typing import List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# Constants
IGNORED_FILES = frozenset([
    ".",
    "..",
    ".DS_Store",
    "_scanned.json",
    "_originals.json"
])
SCANNED_JSON = "_scanned.json"
ORIGINALS_JSON = "_originals.json"
MAX_FILENAME_ATTEMPTS = 1000


class PS5FileRenamer:
    """Handles renaming of PS5 video clips and screenshots."""
    
    def __init__(self, root_paths: List[str] = None):
        """
        Initialize the renamer.
        
        Args:
            root_paths: List of root paths to check. Defaults to standard PS5 structure.
        """
        self.root_paths = root_paths or ["./PS5/CREATE", "./CREATE"]
        self.scan_dirs = self._find_scan_directories()
    
    def _find_scan_directories(self) -> List[Path]:
        """
        Find the correct root directory and return scan paths.
        
        Returns:
            List of Path objects for video and screenshot directories.
        """
        for root in self.root_paths:
            root_path = Path(root)
            vid_dir = root_path / "Video Clips"
            pic_dir = root_path / "Screenshots"
            
            # Check if at least one of the directories exists
            if vid_dir.is_dir() or pic_dir.is_dir():
                logger.info(f"Found root directory: {root}")
                return [vid_dir, pic_dir]
        
        # If nothing found, return default paths (will show error later)
        logger.warning("Warning: Could not find PS5 or CREATE directories")
        return [Path("./PS5/CREATE/Video Clips"), Path("./PS5/CREATE/Screenshots")]
    
    @staticmethod
    def _load_json_file(file_path: Path) -> List[str]:
        """
        Load a JSON file and return its contents as a list.
        
        Args:
            file_path: Path to the JSON file.
            
        Returns:
            List of strings from the JSON file, or empty list if file doesn't exist.
        """
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading {file_path}: {e}")
            return []
    
    @staticmethod
    def _save_json_file(file_path: Path, data: List[str]) -> None:
        """
        Save data to a JSON file.
        
        Args:
            file_path: Path to save the JSON file.
            data: List of strings to save.
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            logger.error(f"Error writing {file_path}: {e}")
    
    @staticmethod
    def _natural_sort_key(s: str) -> List:
        """
        Generate a natural sorting key for strings with numbers.
        
        Args:
            s: String to generate key for.
            
        Returns:
            List suitable for sorting.
        """
        return [int(text) if text.isdigit() else text.lower() 
                for text in re.split(r'([0-9]+)', s)]
    
    @staticmethod
    def _clean_directory_name(name: str) -> str:
        """
        Clean directory name to only alphanumeric characters and spaces.
        
        Args:
            name: Directory name to clean.
            
        Returns:
            Cleaned directory name with hyphens instead of spaces.
        """
        cleaned = re.sub(r'[^A-Za-z0-9 ]', '', name)
        return cleaned.replace(" ", "-")
    
    def _find_available_filename(self, directory: Path, base_name: str, 
                                 extension: str, start_index: int = 0) -> Tuple[str, int]:
        """
        Find an available filename with sequential numbering.
        
        Args:
            directory: Directory to check for existing files.
            base_name: Base name for the file.
            extension: File extension including the dot.
            start_index: Starting index for numbering.
            
        Returns:
            Tuple of (new_filename, counter_used).
        """
        for i in range(start_index, MAX_FILENAME_ATTEMPTS):
            new_name = f"{base_name}-{str(i).zfill(3)}{extension}"
            if not (directory / new_name).exists():
                return new_name, i
        
        # Fallback if we somehow hit the limit
        return f"{base_name}-999{extension}", 999
    
    def _process_directory(self, scan_dir: Path, dir_name: str) -> None:
        """
        Process a single game directory.
        
        Args:
            scan_dir: Parent scan directory (Video Clips or Screenshots).
            dir_name: Name of the game directory to process.
        """
        dir_path = scan_dir / dir_name
        
        # Load tracking files
        prev_scanned = self._load_json_file(dir_path / SCANNED_JSON)
        prev_originals = self._load_json_file(dir_path / ORIGINALS_JSON)
        
        logger.info(f"Scanning {dir_path}")
        time.sleep(1)
        
        if not dir_path.is_dir():
            logger.error("ERROR: Not a directory")
            return
        
        try:
            # Get and sort files
            files = [f for f in os.listdir(dir_path) if f not in IGNORED_FILES]
            files.sort(key=self._natural_sort_key)
        except OSError as e:
            logger.error(f"Error reading directory {dir_path}: {e}")
            return
        
        counter = 0
        processed_files = []
        processed_originals = []
        dir_cleaned = self._clean_directory_name(dir_name)
        
        for filename in files:
            file_path = dir_path / filename
            
            # Skip if already processed
            if filename in prev_scanned:
                logger.info(f"Previously Processed: {filename}")
                continue
            
            # Delete if it's an original file
            if filename in prev_originals:
                logger.info(f"DELETE: {filename}")
                try:
                    file_path.unlink()
                except OSError as e:
                    logger.error(f"Error deleting {filename}: {e}")
                continue
            
            # Process new files
            if file_path.is_file() and not filename.endswith('.db'):
                extension = file_path.suffix
                
                # Generate new filename
                new_name, counter = self._find_available_filename(
                    dir_path, dir_cleaned, extension, counter
                )
                new_path = dir_path / new_name
                
                # Rename the file
                try:
                    file_path.rename(new_path)
                    processed_originals.append(filename)
                    processed_files.extend([filename, new_name])
                    logger.info(f"ADDING: {new_name}")
                    counter += 1
                except OSError as e:
                    logger.error(f"Error renaming {filename}: {e}")
        
        # Save updated tracking files
        self._save_json_file(
            dir_path / SCANNED_JSON,
            prev_scanned + processed_files
        )
        self._save_json_file(
            dir_path / ORIGINALS_JSON,
            prev_originals + processed_originals
        )
    
    def run(self) -> None:
        """Execute the main renaming process."""
        for scan_dir in self.scan_dirs:
            if not scan_dir.is_dir():
                logger.warning(f"{scan_dir} not found!")
                continue
            
            try:
                # Get list of game directories
                directories = [d for d in os.listdir(scan_dir) 
                             if d not in IGNORED_FILES]
                directories.sort(key=self._natural_sort_key)
            except OSError as e:
                logger.error(f"Error reading directory {scan_dir}: {e}")
                continue
            
            for dir_name in directories:
                self._process_directory(scan_dir, dir_name)
        
        logger.info("[COMPLETED]")

def main():
    """Main entry point for the script."""
    try:
        renamer = PS5FileRenamer()
        renamer.run()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        # Wait for user input before closing
        print("\n" + "="*50)
        input("Press ENTER to exit...")

if __name__ == "__main__":
    main()
