.PHONY: setup run dashboard atlas benchmark gpu clean run-quick run-deep run-gpu run-multifield run-reaction

setup:
	python -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip
	. .venv/bin/activate && pip install -r requirements.txt
	. .venv/bin/activate && python -m pytest -q tests/test_backend.py

run:
	. .venv/bin/activate && python -m physics_ai.main_loop

run-quick:
	. .venv/bin/activate && python -m physics_ai.main_loop --config configs/run_quick.yaml

run-deep:
	. .venv/bin/activate && python -m physics_ai.main_loop --config configs/run_deep.yaml

run-gpu:
	. .venv/bin/activate && PHYSICS_AI_CUDA=1 python -m physics_ai.main_loop --config configs/run_gpu.yaml

run-multifield:
	. .venv/bin/activate && python -m physics_ai.main_loop --config configs/run_multifield.yaml

run-reaction:
	. .venv/bin/activate && python -m physics_ai.main_loop --config configs/run_reaction.yaml

dashboard:
	. .venv/bin/activate && streamlit run physics_ai/live_dashboard.py -- --run-dir experiments

atlas:
	. .venv/bin/activate && bash scripts/run_lab_pipeline.sh

benchmark:
	. .venv/bin/activate && python -m physics_ai.benchmark_runner --mode wave --batch 64 --size 64 --steps 80

gpu:
	. .venv/bin/activate && PHYSICS_AI_CUDA=1 python -m physics_ai.main_loop --dynamics-type wave

clean:
	rm -rf .venv experiments benchmarks
