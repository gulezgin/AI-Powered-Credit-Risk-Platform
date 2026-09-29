"""One-shot pipeline: generate synthetic data -> train & calibrate models ->
seed the database. Run this once before starting the API/dashboard."""
from src.data import generate_synthetic_data
from src.db import seed
from src.models import train


def main():
    print("=== 1/3 Generating synthetic bank data ===")
    generate_synthetic_data.main()

    print("\n=== 2/3 Training & calibrating models ===")
    train.train_synthetic()

    print("\n=== 3/3 Seeding database ===")
    seed.seed()

    print("\nPipeline complete. Start the API with:\n  uvicorn api.main:app --reload")
    print("Start the dashboard with:\n  streamlit run dashboard/Home.py")


if __name__ == "__main__":
    main()
