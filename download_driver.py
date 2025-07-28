import os
import platform
import subprocess
import shutil
from pathlib import Path
import requests
from zipfile import ZipFile
from typing import Optional, Tuple

def get_chrome_version() -> Optional[str]:
    system = platform.system()
    
    try:
        if system == "Darwin":  # macOS
            process = subprocess.Popen(
                ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'],
                stdout=subprocess.PIPE
            )
            version = process.communicate()[0].decode('UTF-8').replace('Google Chrome ', '').strip()
        elif system == "Windows":
            process = subprocess.Popen(
                ['reg', 'query', 'HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon', '/v', 'version'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            output = process.communicate()[0].decode('UTF-8')
            version = output.strip().split()[-1]
        else:
            print("Unsupported operating system")
            return None
            
        print(f"Full Chrome version: {version}")  # Debug print
        return version
    except Exception as e:
        print(f"Error getting Chrome version: {e}")
        return None

def get_system_info() -> Tuple[str, str]:
    system = platform.system()
    machine = platform.machine().lower()
    
    if system == "Darwin":  # macOS
        platform_name = "mac"
        if machine == "x86_64":
            arch = "x64"
        elif machine == "arm64":
            arch = "arm64"
        else:
            raise SystemError(f"Unsupported Mac architecture: {machine}")
    elif system == "Windows":
        platform_name = "win"
        if machine == "amd64" or machine == "x86_64":
            arch = "x64"
        else:
            raise SystemError(f"Unsupported Windows architecture: {machine}")
    else:
        raise SystemError(f"Unsupported operating system: {system}")
        
    return platform_name, arch

def get_platform_download_name(platform_name: str, arch: str) -> str:
    if platform_name == "win":
        return f"{platform_name}64"
    else:  # mac
        return f"{platform_name}-{arch}"

def find_matching_driver_version(versions_data: dict, chrome_version: str, platform_name: str, arch: str) -> Optional[dict]:
    chrome_major_version = chrome_version.split('.')[0]
    platform_download_name = get_platform_download_name(platform_name, arch)
    
    print(f"Looking for ChromeDriver versions matching platform: {platform_download_name}")  # Debug print

    matching_versions = [
        v for v in versions_data['versions']
        if v['version'].split('.')[0] == chrome_major_version
        and 'chromedriver' in v['downloads']
        and any(d['platform'] == platform_download_name for d in v['downloads']['chromedriver'])
    ]
    
    if not matching_versions:
        # If no exact major version match, try finding the closest available version
        all_major_versions = [
            int(v['version'].split('.')[0]) 
            for v in versions_data['versions']
            if 'chromedriver' in v['downloads']
            and any(d['platform'] == platform_download_name for d in v['downloads']['chromedriver'])
        ]
        
        if not all_major_versions:
            return None
            
        target_version = int(chrome_major_version)
        closest_version = min(all_major_versions, key=lambda x: abs(x - target_version))
        
        matching_versions = [
            v for v in versions_data['versions']
            if v['version'].split('.')[0] == str(closest_version)
            and 'chromedriver' in v['downloads']
            and any(d['platform'] == platform_download_name for d in v['downloads']['chromedriver'])
        ]
        
        if matching_versions:
            print(f"No exact version match found. Using closest major version: {closest_version}")
    
    if matching_versions:
        return sorted(matching_versions, key=lambda x: [int(i) for i in x['version'].split('.')])[-1]
    
    return None


def download_chromedriver(chrome_version: str, platform_name: str, arch: str) -> bool:
    base_url = "https://googlechromelabs.github.io/chrome-for-testing"
    known_versions_url = f"{base_url}/known-good-versions-with-downloads.json"
    
    try:
        response = requests.get(known_versions_url)
        response.raise_for_status()
        versions_data = response.json()
        
        matching_version = find_matching_driver_version(versions_data, chrome_version, platform_name, arch)
        
        if not matching_version:
            print(f"No compatible ChromeDriver version found for Chrome {chrome_version}")
            return False
            
        print(f"Found matching ChromeDriver version: {matching_version['version']}")

        platform_download_name = get_platform_download_name(platform_name, arch)
        download_info = next(
            (d for d in matching_version['downloads']['chromedriver'] if d['platform'] == platform_download_name),
            None
        )
        if not download_info:
            print(f"No ChromeDriver download found for {platform_download_name}")
            return False
            
        download_url = download_info['url']

        driver_dir = Path("./chromedriver")
        driver_dir.mkdir(exist_ok=True)

        # Clean up existing ChromeDriver files
        chromedriver_name = "chromedriver.exe" if platform_name == "win" else "chromedriver"
        existing_driver = driver_dir / chromedriver_name
        if existing_driver.exists():
            print(f"Removing existing ChromeDriver: {existing_driver}")
            existing_driver.unlink()

        print(f"Downloading ChromeDriver from {download_url}")
        response = requests.get(download_url)
        response.raise_for_status()
        
        zip_path = driver_dir / "chromedriver.zip"
        with open(zip_path, 'wb') as f:
            f.write(response.content)
            
        with ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(driver_dir)

        # Find the extracted chromedriver executable
        extracted_driver = next(driver_dir.rglob(chromedriver_name))
        final_driver_path = driver_dir / chromedriver_name
        
        # Move to final location
        shutil.move(str(extracted_driver), str(final_driver_path))
        
        # Clean up zip file and any extracted directories
        zip_path.unlink()
        for item in driver_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
                
        # Make executable on Unix-like systems
        if platform_name != "win":
            os.chmod(final_driver_path, 0o755)
            
        print(f"ChromeDriver successfully installed to {final_driver_path}")
        return True
        
    except Exception as e:
        print(f"Error downloading ChromeDriver: {e}")
        return False

def main():
    try:
        chrome_version = get_chrome_version()
        if not chrome_version:
            print("Could not determine Chrome version")
            return
            
        platform_name, arch = get_system_info()
        print(f"Detected system: {platform_name} ({arch})")
        print(f"Chrome version: {chrome_version}")
        
        success = download_chromedriver(chrome_version, platform_name, arch)
        if not success:
            print("Failed to set up ChromeDriver")
            return
            
    except Exception as e:
        print(f"Error during setup: {e}")
        return

if __name__ == "__main__":
    main()