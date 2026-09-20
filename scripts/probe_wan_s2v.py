from gradio_client import Client

SPACE = "Wan-AI/Wan2.2-S2V"
print(f"PROBE_START space={SPACE}")
client = Client(SPACE, verbose=True)
print("CLIENT_CONNECTED")
try:
    info = client.view_api(all_endpoints=True)
    print("VIEW_API_RETURN:", info)
except TypeError:
    info = client.view_api()
    print("VIEW_API_RETURN:", info)
print("PROBE_OK")
