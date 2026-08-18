import os
import re
import subprocess
import glob
import shutil

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    flutter_dir = os.path.join(root_dir, "curago_field_app")
    pubspec_path = os.path.join(flutter_dir, "pubspec.yaml")
    static_dir = os.path.join(root_dir, "backend", "static")

    if not os.path.exists(static_dir):
        os.makedirs(static_dir)

    # 1. Read and bump version
    with open(pubspec_path, "r") as f:
        content = f.read()

    version_match = re.search(r'^version:\s*(\d+\.\d+\.\d+)\+(\d+)', content, re.MULTILINE)
    if not version_match:
        print("Could not find version in pubspec.yaml")
        return

    base_version = version_match.group(1)
    build_num = int(version_match.group(2))
    new_build_num = build_num + 1
    new_version_str = f"version: {base_version}+{new_build_num}"

    new_content = re.sub(r'^version:\s*(\d+\.\d+\.\d+)\+(\d+)', new_version_str, content, flags=re.MULTILINE)

    with open(pubspec_path, "w") as f:
        f.write(new_content)
    
    print(f"Bumped version to {base_version}+{new_build_num}")

    # 2. Build APK
    print("Building APK...")
    subprocess.run(["flutter", "build", "apk"], cwd=flutter_dir, check=True)

    # 3. Clean old APKs
    old_apks = glob.glob(os.path.join(static_dir, "*.apk"))
    for apk in old_apks:
        os.remove(apk)
        print(f"Removed old APK: {apk}")

    # 4. Copy new APK
    source_apk = os.path.join(flutter_dir, "build", "app", "outputs", "flutter-apk", "app-release.apk")
    target_apk = os.path.join(static_dir, f"Curago_Field_App_v{base_version}_{new_build_num}.apk")
    shutil.copy2(source_apk, target_apk)
    print(f"Copied new APK to: {target_apk}")

    # 5. Git commit
    print("Committing changes...")
    subprocess.run(["git", "add", pubspec_path, static_dir], cwd=root_dir)
    subprocess.run(["git", "commit", "-m", f"chore: release APK v{base_version}+{new_build_num}"], cwd=root_dir)
    subprocess.run(["git", "push", "origin", "master"], cwd=root_dir)
    print("Successfully released and pushed new APK!")

if __name__ == "__main__":
    main()
