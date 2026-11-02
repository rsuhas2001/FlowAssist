run:
	python run.py

test:
	python -m pytest -q

seed:
	python data/generate_data.py
