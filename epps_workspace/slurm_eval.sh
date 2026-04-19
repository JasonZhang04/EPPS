#!/bin/bash
#SBATCH --job-name=epps_evaluation
#SBATCH --output=logs/epps_eval_%j.out
#SBATCH --error=logs/epps_eval_%j.err
#SBATCH --time=12:00:00
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G

echo "Starting EPPS Evaluation Pipeline on SLURM..."
source activate virtualhome 

# Run hybrid synthesis to generate testing dataset
python -m src.data_gen.dataset_compiler

# Run primary evaluation engine
python -m src.eval.evaluator

echo "Evaluation Pipeline Completed."
