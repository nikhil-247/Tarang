.PHONY: install test data train infer api docker

install:
	python -m pip install -r requirements.txt

test:
	pytest -q

data:
	python scripts/generate_dataset.py --rows 2500 --output data/network_events.csv

train:
	python scripts/train.py --input data/network_events.csv --model-dir artifacts

infer:
	python scripts/infer.py --input data/network_events.csv --model-dir artifacts --output reports/predictions.csv

api:
	PYTHONPATH=src uvicorn tarang.api:app --host 0.0.0.0 --port 8000

docker:
	docker build -t tarang-threat-detection .
