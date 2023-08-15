import os
import subprocess

folder = r"..." # 根目录
folder_out = r"...\out"
i = 0
for file in os.listdir(folder):
        if file.endswith('.svg'):
            file = os.path.join(folder, file)
            with open(r"...\out\tmp.txt", "w") as f:
                f.write(str(i) + "\n" + file + "\n" + folder_out)
            i += 1
            result = subprocess.run(["python", r"svg-3D.py"], capture_output=True, text=True)
            print(result.stdout)
