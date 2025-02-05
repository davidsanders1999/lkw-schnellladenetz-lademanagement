import os
import shutil

def main():
    path = os.path.join(os.path.dirname(__file__), "data")
    
    
    for root, dirs, files in os.walk(path):
        for file in files:
            if not file.endswith('.csv'):
                continue
            file_path = os.path.join(root, file)
            os.remove(file_path)

if __name__ == "__main__":
    main()