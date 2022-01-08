#! /bin/bash
cd $(dirname ${BASH_SOURCE})
source venv/bin/activate
python3 application.py >> logs/app.log 2>&1
