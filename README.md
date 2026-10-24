# HR-leave-assistant


### 1. Create a virtual environment

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Conda alternative:

```bash
conda create -n mcp-llm-connect python=3.11 -y
conda activate mcp-llm-connect
```


### 3. Configure environment variables

```bash
cp .env.sample .env
```

### 4. Install requirements.txt


pip install -r requirements.txt


If using Docker, restart the container after editing `.env`:

```bash
docker compose down
docker compose up --build
```



### `Connection refused` or `Could not connect`

The server is not running or the port is different. Verify:

```bash
curl http://localhost:8000/health
```


Push the Docker image in DockerHub

Docker loging

>>> docker login

Create a TAG

>>> docker tag containerising_mcp_llm_connect-hr-mcp-server:latest:latest rajeshthakur1/containerising_mcp_llm_connect-hr-mcp-server:latest

Push the image in Docker Hub

>>> docker push rajeshthakur1/containerising_mcp_llm_connect-hr-mcp-server:latest
