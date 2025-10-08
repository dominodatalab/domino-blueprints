source venv/bin/activate
venv\Scripts\activate
pip install mlflow==2.18.0 dominodatalab pandas scikit-learn PyJWT

python3 run_experiment_and_register_model.py --domino_host_name "marcdo77364.cs.domino.tech" \
                                            --domino_project_owner "wadkars" \
                                            --domino_project_name "ddl-end-to-end-demo" \
                                            --domino_experiment_name "sw-external-ddl-end-to-end-demo" \
                                            --domino_run_name "external-run" \
                                            --domino_model_name "sw-external-ddl-end-to-end-demo"
