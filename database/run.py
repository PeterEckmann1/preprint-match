import os
import requests
import time


for i in range(0, 2000, 10):
    string = '#!/bin/bash\n#SBATCH --job-name="database"\n#SBATCH --output="/home/peter251/database/' + str(i).zfill(6) + '.out"\n#SBATCH --mem=10G\n#SBATCH --partition=shared\n#SBATCH --nodes=1\n#SBATCH --ntasks-per-node=1\n#SBATCH --export=ALL\n#SBATCH -t 10:00:00\nmodule load python\npython3 -u main.py ' + str(i) + ' ' + str(i + 10)
    file = open('jobfile', 'w')
    file.write(string)
    file.close()

    os.system('sbatch jobfile')