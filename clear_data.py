import os
import shutil
import logging
logging.basicConfig(filename='logs.log', level=logging.DEBUG, format='%(asctime)s; %(levelname)s; %(message)s')

def main():
    logging.info('Start: Clear Data')
    path = os.path.join(os.path.dirname(__file__), "data")
    
    
    for root, dirs, files in os.walk(path):
        for file in files:
            if not file.endswith('.csv'):
                continue
            file_path = os.path.join(root, file)
            os.remove(file_path)

if __name__ == "__main__":
    main()