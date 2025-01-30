import os
import shutil

def move_profile_photos(photo_base_dir, target_base_dir):
    for i in range(1, 16):
        subfolder = f"{i:03}"
        os.makedirs(os.path.join(target_base_dir, subfolder), exist_ok=True)

    for folder in os.listdir(photo_base_dir):
        folder_path = os.path.join(photo_base_dir, folder)

        if os.path.isdir(folder_path):
            image_filename = f"{folder}.jpg"
            image_path = os.path.join(folder_path, image_filename)

            if os.path.exists(image_path):
                parts = folder.split('-')
                if len(parts) >= 3:
                    department_code = parts[1]

                    if department_code.isdigit() and 1 <= int(department_code) <= 15:
                        target_folder = os.path.join(target_base_dir, f"{int(department_code):03}")
                        target_path = os.path.join(target_folder, image_filename)
                        shutil.move(image_path, target_path)
                        print(f"Moved {image_filename} to {target_path}")
                    else:
                        print(f"Skipping {folder} - Invalid department code {department_code}")
                else:
                    print(f"Skipping {folder} - Invalid format")

if __name__ == "__main__":
    photo_base_dir = r"/Velammal-Engineering-College-Backend/static/temp_photos/"
    target_base_dir = r"/Velammal-Engineering-College-Backend/static/images/profile_photos/"
    move_profile_photos(photo_base_dir, target_base_dir)
