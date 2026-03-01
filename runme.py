import subprocess
import time
import requests

DOCKER_COMPOSE_FILE = "docker-compose.yml"  # path to your compose file
NGROK_API = "http://localhost:4040/api/tunnels"

def start_docker_compose():
    print("[+] Starting Docker Compose...")
    cmd = ["docker", "compose", "-f", DOCKER_COMPOSE_FILE, "up", "--build", "-d"]
    subprocess.run(cmd, check=True)
    print("[+] Docker Compose started in detached mode.")
    print("\t[1] Started Ngrok.")
    print("\t[2] Started RASA.")
    print("\t[3] Started Backend.")
    print("\t[4] Started Redis.")
    print("\t[4] Started postgres.")

def get_ngrok_url():
    while True:
        try:
            resp = requests.get(NGROK_API).json()
            tunnels = resp.get("tunnels", [])
            if tunnels:
                public_url = tunnels[0].get("public_url")
                if public_url:
                    return public_url
        except Exception:
            pass
        time.sleep(1)

if __name__ == "__main__":
    start_docker_compose()
    url = get_ngrok_url()
    print(f"\nNgrok public URL: {url}/sms")
    print("Paste this URL in twilio whatsapp sandbox settings")
