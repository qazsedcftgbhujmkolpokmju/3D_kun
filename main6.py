import os
import subprocess

folder = r"C:\Users\Administrator\Downloads\vectorizer"
folder_out = r"C:\Users\Administrator\Downloads\vectorizer\out"
i = 0
for file in os.listdir(folder):
        if file.endswith('.svg'):
            file = os.path.join(folder, file)
            with open(r"C:\Users\Administrator\Downloads\vectorizer\out\tmp.txt", "w") as f:
                f.write(str(i) + "\n" + file + "\n" + folder_out)
            i += 1
            result = subprocess.run(["python", r"D:\ProgramData\PycharmProjects\pythonProject4\main4.py"], capture_output=True, text=True)
            print(result.stdout)
