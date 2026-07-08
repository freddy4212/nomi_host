# NOMI Containerized Deployment

Make sure Podman is installed and your default machine environment has been configured.

## Deployment Steps
1. Change into `nomi_host/_deployment`.

2. Create `config.yaml` under `nomi_host/_deployment` and fill in the API key and model name.

```
llm:
  api_key: "YOUR_GEMINI_API_KEY"
  model_name: "models/gemini-3-flash-preview"
```

3. Edit `deployment.yaml` and update the paths at the bottom of the configuration to point to `/path/to/config.yaml` and `/path/to/database/init-db.sql` with real paths.

```
  volumes:
  - name: init-db-volume
    hostPath:
      path: /path/to/nomi_host/_deployment/database/init-db.sql (replace this with the real path)
      type: File
  - name: config-volume
    hostPath:
      path: /path/to/nomi_host/_deployment/config.yaml (replace this with the real path)
      type: File
  - name: nomi-data-pvc
    persistentVolumeClaim:
      claimName: nomi-data
```

4. Build the backend image.

```
podman build -t nomi-backend:v1 -f ./backend/Dockerfile ../
```

5. Build the frontend image.

```
podman build -t nomi-frontend:v1 -f .//frontend/Dockerfile ../
```

6. Run the deployment.

```
podman kube play ./deployment.yaml
```

7. Restart the pod.

```
podman pod restart nomi
```

## Launch and Run

After confirming that Podman Machine is running, execute:

```
podman pod restart nomi
```

Then open the following URL in your browser:

```
localhost:5173
```

## Updating the Application

If the code is updated in the future, re-pull the source code and then:

1. Rebuild the images and bump the frontend or backend tag to v2, for example:

```
podman build -t nomi-backend:v2 -f ./backend/Dockerfile ../
```

2. Edit `deployment.yaml` and update the frontend or backend image tag to v2, for example:

```
  - name: nomi-backend
    image: localhost/nomi-backend:v2
```

3. Redeploy.

```
podman kube down deployment.yaml
podman kube play deployment.yaml
```
